"""Wiki generation phases — pure functions called by WikiGenerator.

Each phase takes the data it needs as arguments instead of mutating
generator state. This keeps generator.py focused on orchestration and
each phase independently testable.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from .diagrams import (
    build_call_graph_mermaid,
    build_inter_module_diagram,
    build_sequence_diagram,
)
from .graph_queries import (
    get_all_processes,
    get_community_file_mapping,
    get_inter_module_call_edges,
    get_inter_module_edges_for_overview,
    get_intra_module_call_edges,
    get_processes_for_files,
)
from .llm_client import call_llm, estimate_tokens
from .prompts import fill_template, format_call_edges, format_processes


def build_module_tree(
    files: list[dict[str, Any]],
    wiki_dir: str,
    llm_config: dict[str, Any],
    on_progress: Any,
) -> list[dict[str, Any]]:
    """Group files into documentation modules via LLM + community signals."""
    snapshot = os.path.join(wiki_dir, "first_module_tree.json")
    try:
        with open(snapshot, encoding="utf-8") as f:
            parsed = json.load(f)
        if isinstance(parsed, list) and parsed:
            return parsed
    except (OSError, json.JSONDecodeError):
        pass

    on_progress("grouping", 12, "Querying graph communities...")
    communities = get_community_file_mapping()

    file_list = "\n".join(
        f"- {f['filePath']}: {', '.join(s['name'] for s in f.get('symbols', []))}"
        for f in files[:200]
    )

    if communities:
        comm_text = "\n".join(
            f"**{c['label']}** ({len(c['files'])} files)" for c in communities[:20]
        )
        prompt = (
            f"Group these files into documentation modules.\n\n"
            f"Communities:\n{comm_text}\n\nFiles:\n{file_list}\n\n"
            "Respond with JSON only."
        )
    else:
        prompt = (
            f"Group these files into documentation modules.\n\n"
            f"Files:\n{file_list}\n\nRespond with JSON only."
        )

    system = (
        "You are a documentation architect. Group files into logical modules. "
        "Respond with JSON mapping module names to file arrays."
    )
    on_progress("grouping", 18, "Asking LLM to group files...")
    result = call_llm(prompt, llm_config, system)
    content = result.get("content", "{}")
    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        return [{
            "name": "All",
            "slug": "all",
            "files": [f["filePath"] for f in files],
            "children": [],
        }]

    grouping = json.loads(m.group(0))
    tree: list[dict[str, Any]] = []
    for name, file_paths in grouping.items():
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        tree.append({
            "name": name,
            "slug": slug,
            "files": file_paths,
            "children": [],
        })

    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(tree, f)
    return tree


def generate_leaf_page(
    node: dict[str, Any],
    wiki_dir: str,
    repo_path: str,
    max_tokens: int,
    llm_config: dict[str, Any],
) -> None:
    """Render a leaf module page (LLM doc + Mermaid diagrams)."""
    files = node.get("files", [])
    intra = get_intra_module_call_edges(files)
    inter = get_inter_module_call_edges(files)
    processes = get_processes_for_files(files, 5)

    source = read_source_snippets(repo_path, files, max_tokens)
    prompt = fill_template(
        "Write documentation for **{{MODULE_NAME}}**.\n\nSource:\n{{SOURCE_CODE}}\n\n"
        "Internal calls: {{INTRA_CALLS}}\nOutgoing: {{OUTGOING_CALLS}}\n"
        "Incoming: {{INCOMING_CALLS}}\nFlows: {{PROCESSES}}",
        {
            "MODULE_NAME": node["name"],
            "SOURCE_CODE": source,
            "INTRA_CALLS": format_call_edges(intra),
            "OUTGOING_CALLS": format_call_edges(inter.get("outgoing", [])),
            "INCOMING_CALLS": format_call_edges(inter.get("incoming", [])),
            "PROCESSES": format_processes(processes),
        },
    )
    result = call_llm(
        prompt, llm_config, "You are a technical documentation writer.",
    )
    content = result.get("content", "")

    call_graph = build_call_graph_mermaid(node["name"], intra)
    if call_graph:
        content += f"\n\n## Call Graph\n\n```mermaid\n{call_graph}\n```\n"
    for proc in processes[:3]:
        seq = build_sequence_diagram(proc)
        if seq:
            content += (
                f"\n\n### {proc.get('label', '')}\n\n```mermaid\n{seq}\n```\n"
            )

    page_path = os.path.join(wiki_dir, f"{node['slug']}.md")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_parent_page(
    node: dict[str, Any],
    wiki_dir: str,
    llm_config: dict[str, Any],
) -> None:
    """Synthesize a parent module page from already-rendered children."""
    children_docs = ""
    for child in node.get("children", []):
        child_path = os.path.join(wiki_dir, f"{child['slug']}.md")
        try:
            with open(child_path, encoding="utf-8") as f:
                doc = f.read()
            summary_end = doc.find("<!-- summary-end -->")
            snippet = doc[:summary_end] if summary_end > 0 else doc[:500]
            children_docs += f"### {child['name']}\n{snippet}\n\n"
        except OSError:
            children_docs += (
                f"### {child['name']}\n(documentation not yet generated)\n\n"
            )

    prompt = (
        f"Write documentation for **{node['name']}** module group.\n\n"
        f"Sub-modules:\n{children_docs}"
    )
    result = call_llm(
        prompt, llm_config,
        "You are a technical documentation writer. Synthesize child docs.",
    )
    page_path = os.path.join(wiki_dir, f"{node['slug']}.md")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(result.get("content", ""))


def generate_overview(
    module_tree: list[dict[str, Any]],
    wiki_dir: str,
    llm_config: dict[str, Any],
) -> None:
    """Render the top-level overview page with cross-module diagrams."""
    all_files_per_module: dict[str, list[str]] = {}
    for node in module_tree:
        all_files_per_module[node["name"]] = node.get("files", [])

    module_edges = get_inter_module_edges_for_overview(all_files_per_module)
    all_procs = get_all_processes(10)

    summaries = ""
    for node in module_tree:
        page_path = os.path.join(wiki_dir, f"{node['slug']}.md")
        try:
            with open(page_path, encoding="utf-8") as f:
                doc = f.read()
            end = doc.find("<!-- summary-end -->")
            summary = doc[:end] if end > 0 else doc[:300]
            summaries += f"**{node['name']}**: {summary.strip()}\n\n"
        except OSError:
            summaries += f"**{node['name']}**: (not yet generated)\n\n"

    edge_text = "\n".join(
        f"{e['from']} -> {e['to']}: {e['count']} calls" for e in module_edges[:20]
    )
    proc_text = format_processes(all_procs[:5])

    prompt = (
        f"Write the overview page for this repository wiki.\n\n"
        f"Module summaries:\n{summaries}\n\n"
        f"Inter-module edges:\n{edge_text}\n\n"
        f"Key flows:\n{proc_text}"
    )
    result = call_llm(
        prompt, llm_config,
        "You are a technical documentation writer. Write the top-level overview.",
    )
    content = result.get("content", "")

    diagram = build_inter_module_diagram(module_edges)
    if diagram:
        content += f"\n\n## Architecture\n\n```mermaid\n{diagram}\n```\n"

    page_path = os.path.join(wiki_dir, "overview.md")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)


def read_source_snippets(
    repo_path: str, file_paths: list[str], max_tokens: int,
) -> str:
    """Concatenate file contents up to a token budget."""
    snippets: list[str] = []
    total = 0
    for fp in file_paths:
        try:
            full = os.path.join(repo_path, fp)
            with open(full, encoding="utf-8", errors="replace") as f:
                content = f.read()
            tokens = estimate_tokens(content)
            if total + tokens > max_tokens:
                break
            snippets.append(f"--- {fp} ---\n{content}")
            total += tokens
        except OSError:
            pass
    return "\n\n".join(snippets) if snippets else "(no source available)"


def flatten_tree(
    tree: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split a module tree into (leaf nodes, parent nodes)."""
    leaves: list[dict[str, Any]] = []
    parents: list[dict[str, Any]] = []
    for node in tree:
        if node.get("children"):
            parents.append(node)
            l, p = flatten_tree(node["children"])
            leaves.extend(l)
            parents.extend(p)
        else:
            leaves.append(node)
    return leaves, parents


def count_modules(tree: list[dict[str, Any]]) -> int:
    """Count nodes in a module tree (recursive)."""
    count = 0
    for node in tree:
        count += 1
        if node.get("children"):
            count += count_modules(node["children"])
    return count
