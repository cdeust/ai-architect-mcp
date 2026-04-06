"""Import processor — 1:1 port of gitnexus import-processor.js processImports."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

import tree_sitter

from ..._models.graph_types import GraphRelationship, RelationshipType
from ...lib.utils import generate_id
from ...config.supported_languages import SupportedLanguages
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES
from .utils import get_language_from_filename
from ..graph.graph import KnowledgeGraph
from .ast_cache import ASTCache
from .import_resolution import (
    build_suffix_index,
    resolve_import_path,
    suffix_index_get_files_in_dir,
    suffix_resolve,
)

_query_cache: dict[str, object] = {}


def _load_tsconfig_paths(repo_root: str) -> dict[str, Any] | None:
    for filename in ("tsconfig.json", "tsconfig.app.json", "tsconfig.base.json"):
        try:
            path = os.path.join(repo_root, filename)
            with open(path, encoding="utf-8") as f:
                raw = f.read()
            import re
            stripped = re.sub(r"//.*$", "", raw, flags=re.MULTILINE)
            stripped = re.sub(r"/\*[\s\S]*?\*/", "", stripped)
            tsconfig = json.loads(stripped)
            co = tsconfig.get("compilerOptions", {})
            paths = co.get("paths", {})
            base_url = co.get("baseUrl", ".")
            aliases: dict[str, str] = {}
            for pattern, targets in paths.items():
                if not isinstance(targets, list) or not targets:
                    continue
                target = targets[0]
                alias_prefix = pattern[:-1] if pattern.endswith("/*") else pattern
                target_prefix = target[:-1] if target.endswith("/*") else target
                aliases[alias_prefix] = target_prefix
            if aliases:
                return {"aliases": aliases, "baseUrl": base_url}
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _load_go_module_path(repo_root: str) -> dict[str, str] | None:
    try:
        with open(os.path.join(repo_root, "go.mod"), encoding="utf-8") as f:
            content = f.read()
        import re
        m = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
        if m:
            return {"modulePath": m.group(1)}
    except OSError:
        pass
    return None


def _load_swift_package_config(repo_root: str) -> dict[str, Any] | None:
    targets: dict[str, str] = {}
    for source_dir in ("Sources", "Package/Sources", "src"):
        try:
            full = os.path.join(repo_root, source_dir)
            for entry in os.listdir(full):
                if os.path.isdir(os.path.join(full, entry)):
                    targets[entry] = source_dir + "/" + entry
        except OSError:
            continue
    if targets:
        return {"targets": targets}
    return None


def _add_import_edge(
    graph: KnowledgeGraph,
    import_map: dict[str, set[str]],
    file_path: str,
    resolved_path: str,
) -> None:
    source_id = generate_id("File", file_path)
    target_id = generate_id("File", resolved_path)
    graph.add_relationship(GraphRelationship(
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.IMPORTS,
        confidence=1.0,
    ))
    import_map.setdefault(file_path, set()).add(resolved_path)


def process_imports(
    graph: KnowledgeGraph,
    files: list[dict[str, str]],
    ast_cache: ASTCache,
    import_map: dict[str, set[str]],
    on_progress: Callable[[int, int], None] | None = None,
    repo_root: str = "",
    all_paths: list[str] | None = None,
) -> None:
    all_file_list = all_paths if all_paths else [f["path"] for f in files]
    all_file_paths = set(all_file_list)
    resolve_cache: dict[str, str | None] = {}
    normalized_file_list = [p.replace("\\", "/") for p in all_file_list]
    index = build_suffix_index(normalized_file_list, all_file_list)

    effective_root = repo_root or ""
    tsconfig_paths = _load_tsconfig_paths(effective_root) if effective_root else None
    go_module = _load_go_module_path(effective_root) if effective_root else None
    swift_config = _load_swift_package_config(effective_root) if effective_root else None

    for i, file in enumerate(files):
        if on_progress is not None:
            on_progress(i + 1, len(files))

        language = get_language_from_filename(file["path"])
        if language is None:
            continue
        query_str = LANGUAGE_QUERIES.get(language)
        if not query_str:
            continue

        try:
            parser = load_language(language, file["path"])
        except Exception:
            continue

        tree = ast_cache.get(file["path"])
        if tree is None:
            try:
                tree = parser.parse(file["content"].encode("utf-8"))
            except Exception:
                continue
            ast_cache.set(file["path"], tree)

        try:
            cache_key = f"import:{language}"
            if cache_key not in _query_cache:
                _query_cache[cache_key] = parser.language.query(query_str)
            query = _query_cache[cache_key]
            matches = query.matches(tree.root_node)
        except Exception:
            continue

        for _pattern_idx, capture_dict in matches:
            capture_map: dict[str, Any] = {}
            for cname, nodes_list in capture_dict.items():
                if nodes_list:
                    capture_map[cname] = nodes_list[0]

            if "import" not in capture_map:
                continue
            source_node = capture_map.get("import.source")
            if source_node is None:
                continue

            raw = source_node.text.decode("utf-8").strip("'\"<>") if source_node.text else ""

            # Swift: module imports
            if language == SupportedLanguages.Swift and swift_config:
                target_dir = swift_config["targets"].get(raw)
                if target_dir:
                    prefix = target_dir + "/"
                    for fp in all_file_list:
                        if fp.startswith(prefix) and fp.endswith(".swift"):
                            _add_import_edge(graph, import_map, file["path"], fp)
                continue

            # Go: package imports
            if (language == SupportedLanguages.Go and go_module
                    and raw.startswith(go_module["modulePath"])):
                rel_pkg = raw[len(go_module["modulePath"]) + 1:]
                if rel_pkg:
                    pkg_suffix = "/" + rel_pkg + "/"
                    for j, norm in enumerate(normalized_file_list):
                        if (pkg_suffix in norm and norm.endswith(".go")
                                and not norm.endswith("_test.go")):
                            after = norm[norm.index(pkg_suffix) + len(pkg_suffix):]
                            if "/" not in after:
                                _add_import_edge(graph, import_map, file["path"], all_file_list[j])
                continue

            # Standard resolution
            resolved = resolve_import_path(
                file["path"], raw, all_file_paths, all_file_list,
                normalized_file_list, resolve_cache, language,
                tsconfig_paths, index,
            )
            if resolved:
                _add_import_edge(graph, import_map, file["path"], resolved)
