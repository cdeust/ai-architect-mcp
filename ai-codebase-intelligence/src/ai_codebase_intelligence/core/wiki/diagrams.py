from __future__ import annotations

import re
from typing import Any

from .prompts import short_path


def _sanitize_mermaid_id(name: str) -> str:
    return "n_" + re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _sanitize_mermaid_label(label: str) -> str:
    return label.replace('"', "'").replace("\r", " ").replace("\n", " ")


def build_call_graph_mermaid(
    module_name: str, edges: list[dict[str, str]], max_nodes: int = 12
) -> str | None:
    if not edges:
        return None

    node_set: dict[str, dict[str, str]] = {}
    for e in edges:
        from_key = f"{e['fromFile']}::{e['fromName']}"
        to_key = f"{e['toFile']}::{e['toName']}"
        if from_key not in node_set:
            node_set[from_key] = {"name": e["fromName"], "file": e["fromFile"]}
        if to_key not in node_set:
            node_set[to_key] = {"name": e["toName"], "file": e["toFile"]}

    if len(node_set) > max_nodes:
        edge_counts: dict[str, int] = {}
        for e in edges:
            fk = f"{e['fromFile']}::{e['fromName']}"
            tk = f"{e['toFile']}::{e['toName']}"
            edge_counts[fk] = edge_counts.get(fk, 0) + 1
            edge_counts[tk] = edge_counts.get(tk, 0) + 1
        top_keys = set(
            k for k, _ in sorted(edge_counts.items(), key=lambda x: -x[1])[:max_nodes]
        )
        node_set = {k: v for k, v in node_set.items() if k in top_keys}

    file_groups: dict[str, list[dict[str, str]]] = {}
    for key, node in node_set.items():
        file_groups.setdefault(node["file"], []).append({"key": key, "name": node["name"]})

    valid_keys = set(node_set.keys())
    lines = ["graph TD"]
    for file, nodes in file_groups.items():
        sub_id = _sanitize_mermaid_id(file)
        lines.append(f'  subgraph {sub_id}["{_sanitize_mermaid_label(short_path(file))}"]')
        for n in nodes:
            nid = _sanitize_mermaid_id(n["key"])
            lines.append(f'    {nid}["{_sanitize_mermaid_label(n["name"])}"]')
        lines.append("  end")

    for e in edges:
        fk = f"{e['fromFile']}::{e['fromName']}"
        tk = f"{e['toFile']}::{e['toName']}"
        if fk in valid_keys and tk in valid_keys:
            lines.append(f"  {_sanitize_mermaid_id(fk)} --> {_sanitize_mermaid_id(tk)}")

    return "\n".join(lines)


def build_sequence_diagram(process: dict[str, Any], max_steps: int = 10) -> str | None:
    steps = process.get("steps", [])
    if len(steps) < 2:
        return None
    steps = steps[:max_steps]

    participant_order: list[str] = []
    participant_set: set[str] = set()
    for s in steps:
        fp = s.get("filePath", "")
        if fp not in participant_set:
            participant_set.add(fp)
            participant_order.append(fp)

    lines = ["sequenceDiagram"]
    for fp in participant_order:
        alias = _sanitize_mermaid_id(fp)
        lines.append(f"  participant {alias} as {_sanitize_mermaid_label(short_path(fp))}")

    for i in range(len(steps) - 1):
        from_id = _sanitize_mermaid_id(steps[i].get("filePath", ""))
        to_id = _sanitize_mermaid_id(steps[i + 1].get("filePath", ""))
        label = _sanitize_mermaid_label(steps[i + 1].get("name", ""))
        if from_id == to_id:
            lines.append(f"  {from_id} ->> {from_id}: {label}")
        else:
            lines.append(f"  {from_id} ->> {to_id}: {label}")

    return "\n".join(lines)


def build_inter_module_diagram(
    edges: list[dict[str, Any]], max_nodes: int = 10
) -> str | None:
    if not edges:
        return None

    module_weight: dict[str, int] = {}
    for e in edges:
        module_weight[e["from"]] = module_weight.get(e["from"], 0) + e.get("count", 1)
        module_weight[e["to"]] = module_weight.get(e["to"], 0) + e.get("count", 1)

    top_modules = set(
        k for k, _ in sorted(module_weight.items(), key=lambda x: -x[1])[:max_nodes]
    )

    filtered = [e for e in edges if e["from"] in top_modules and e["to"] in top_modules]
    if not filtered:
        return None

    lines = ["graph LR"]
    for mod in top_modules:
        nid = _sanitize_mermaid_id(mod)
        lines.append(f'  {nid}["{_sanitize_mermaid_label(mod)}"]')
    for e in filtered:
        fid = _sanitize_mermaid_id(e["from"])
        tid = _sanitize_mermaid_id(e["to"])
        lines.append(f"  {fid} -->|{e.get('count', 1)} calls| {tid}")

    return "\n".join(lines)
