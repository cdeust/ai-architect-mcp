"""Pipeline orchestrator."""
from __future__ import annotations

import logging
from typing import Any, Callable

from ..._models.graph_types import (
    GraphNode, GraphRelationship, NodeLabel, RelationshipType,
)
from ..graph.graph import create_knowledge_graph, KnowledgeGraph
from .structure_processor import process_structure
from .parsing_processor_seq import process_parsing
from .import_processor import process_imports
from .call_processor_main import process_calls
from .heritage_processor import process_heritage
from .community_processor import process_communities
from .process_processor import process_processes
from .symbol_table import create_symbol_table
from .ast_cache import create_ast_cache
from .filesystem_walker import walk_repository_paths, read_file_contents
from .utils import get_language_from_filename
from ..tree_sitter.parser_loader import is_language_available
from ...storage.git import is_git_repo

CHUNK_BYTE_BUDGET = 20 * 1024 * 1024  # 20MB
AST_CACHE_CAP = 50


def run_pipeline_from_repo(
    repo_path: str,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    graph = create_knowledge_graph()
    symbol_table = create_symbol_table()
    ast_cache = create_ast_cache(AST_CACHE_CAP)
    import_map: dict[str, set[str]] = {}

    def progress(data: dict[str, Any]) -> None:
        if on_progress:
            on_progress(data)

    # Phase 1: Scan
    progress({"phase": "extracting", "percent": 0, "message": "Scanning repository..."})
    scanned = walk_repository_paths(repo_path)
    total_files = len(scanned)
    progress({"phase": "extracting", "percent": 15, "message": "Repository scanned"})

    # Phase 2: Structure
    progress({"phase": "structure", "percent": 15, "message": "Analyzing project structure..."})
    all_paths = [f["path"] for f in scanned]
    process_structure(graph, all_paths)
    progress({"phase": "structure", "percent": 20, "message": "Project structure analyzed"})

    # Phase 3+4: Chunked read + parse
    parseable = [
        f for f in scanned
        if get_language_from_filename(f["path"]) is not None
        and is_language_available(get_language_from_filename(f["path"]) or "")
    ]
    total_parseable = len(parseable)

    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    current_bytes = 0
    for f in parseable:
        if current_chunk and current_bytes + f["size"] > CHUNK_BYTE_BUDGET:
            chunks.append(current_chunk)
            current_chunk = []
            current_bytes = 0
        current_chunk.append(f["path"])
        current_bytes += f["size"]
    if current_chunk:
        chunks.append(current_chunk)

    progress({"phase": "parsing", "percent": 20,
              "message": f"Parsing {total_parseable} files in {len(chunks)} chunks..."})

    files_parsed = 0
    for chunk_idx, chunk_paths in enumerate(chunks):
        contents = read_file_contents(repo_path, chunk_paths)
        chunk_files = [
            {"path": p, "content": contents[p]}
            for p in chunk_paths if p in contents
        ]

        max_chunk = max(len(c) for c in chunks) if chunks else AST_CACHE_CAP
        ast_cache = create_ast_cache(max_chunk)

        # Each phase is wrapped so one bad file (encoding glitch,
        # tree-sitter edge case, etc.) cannot kill the whole index.
        # The graph is preserved up to the point of failure for the
        # remaining chunks.
        try:
            process_parsing(graph, chunk_files, symbol_table, ast_cache)
        except (UnicodeDecodeError, ValueError, RuntimeError) as exc:
            logging.warning("parsing chunk %d failed: %s", chunk_idx, exc)
        try:
            process_imports(graph, chunk_files, ast_cache, import_map, repo_root=repo_path, all_paths=all_paths)
        except (UnicodeDecodeError, ValueError, RuntimeError) as exc:
            logging.warning("imports chunk %d failed: %s", chunk_idx, exc)
        try:
            process_calls(graph, chunk_files, ast_cache, symbol_table, import_map)
        except (UnicodeDecodeError, ValueError, RuntimeError) as exc:
            logging.warning("calls chunk %d failed: %s", chunk_idx, exc)
        try:
            process_heritage(graph, chunk_files, ast_cache, symbol_table)
        except (UnicodeDecodeError, ValueError, RuntimeError) as exc:
            logging.warning("heritage chunk %d failed: %s", chunk_idx, exc)

        files_parsed += len(chunk_files)
        pct = 20 + int((files_parsed / max(total_parseable, 1)) * 62)
        progress({"phase": "parsing", "percent": pct,
                  "message": f"Parsed chunk {chunk_idx + 1}/{len(chunks)}"})

        ast_cache.clear()

    # Phase 5: Communities
    progress({"phase": "communities", "percent": 82, "message": "Detecting code communities..."})
    community_result = process_communities(graph)

    for comm in community_result["communities"]:
        graph.add_node(GraphNode(
            id=comm["id"], label=NodeLabel.COMMUNITY,
            name=comm["label"],
            properties={
                "heuristicLabel": comm["heuristicLabel"],
                "cohesion": comm["cohesion"],
                "symbolCount": comm["symbolCount"],
            },
        ))

    for m in community_result["memberships"]:
        graph.add_relationship(GraphRelationship(
            source_id=m["nodeId"], target_id=m["communityId"],
            relationship_type=RelationshipType.MEMBER_OF,
            confidence=1.0,
            properties={"reason": "leiden-algorithm"},
        ))

    # Phase 6: Processes
    progress({"phase": "processes", "percent": 94, "message": "Detecting execution flows..."})

    symbol_count = sum(1 for n in graph.iter_nodes() if n.label != NodeLabel.FILE)
    dynamic_max = max(20, min(300, round(symbol_count / 10)))

    process_result = process_processes(
        graph, community_result["memberships"],
        config={"maxProcesses": dynamic_max, "minSteps": 3},
    )

    for proc in process_result["processes"]:
        graph.add_node(GraphNode(
            id=proc["id"], label=NodeLabel.PROCESS,
            name=proc["label"],
            properties={
                "heuristicLabel": proc["heuristicLabel"],
                "processType": proc["processType"],
                "stepCount": proc["stepCount"],
                "communities": proc["communities"],
                "entryPointId": proc["entryPointId"],
                "terminalId": proc["terminalId"],
            },
        ))

    for step in process_result["steps"]:
        graph.add_relationship(GraphRelationship(
            source_id=step["nodeId"], target_id=step["processId"],
            relationship_type=RelationshipType.STEP_IN_PROCESS,
            confidence=1.0,
            properties={"reason": "trace-detection", "step": step["step"]},
        ))

    # Phase 7: Git analytics (ownership, co-change) — conditional on git repo
    git_analytics_result: dict[str, Any] | None = None
    if is_git_repo(repo_path):
        progress({"phase": "git_analytics", "percent": 96,
                  "message": "Analyzing git history (ownership, co-change)..."})
        from .ownership_processor import process_ownership
        from .cochange_processor import process_cochange

        git_analytics_result = {}
        ownership_result = process_ownership(graph, repo_path)
        git_analytics_result["ownership"] = ownership_result["stats"]
        cochange_result = process_cochange(graph, repo_path)
        git_analytics_result["cochange"] = cochange_result["stats"]

    progress({
        "phase": "complete", "percent": 100,
        "message": f"Graph complete! {community_result['stats']['totalCommunities']} communities, "
                   f"{process_result['stats']['totalProcesses']} processes detected.",
    })

    return {
        "graph": graph,
        "repoPath": repo_path,
        "totalFileCount": total_files,
        "communityResult": community_result,
        "processResult": process_result,
        "gitAnalyticsResult": git_analytics_result,
    }
