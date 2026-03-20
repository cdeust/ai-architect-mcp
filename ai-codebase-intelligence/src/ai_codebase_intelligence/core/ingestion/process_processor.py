"""Process detection — 1:1 port of gitnexus process-processor.js."""
from __future__ import annotations

import re
from collections import deque
from typing import Any, Callable

from ..graph.graph import KnowledgeGraph
from .entry_point_scoring import calculate_entry_point_score, is_test_file

MAX_TRACE_DEPTH = 10
MAX_BRANCHING = 4
MAX_PROCESSES = 75
MIN_STEPS = 3
MIN_TRACE_CONFIDENCE = 0.5


def process_processes(
    knowledge_graph: KnowledgeGraph,
    memberships: list[dict[str, str]],
    on_progress: Callable[[str, int], None] | None = None,
    config: dict[str, int] | None = None,
) -> dict[str, Any]:
    cfg = {
        "maxTraceDepth": MAX_TRACE_DEPTH,
        "maxBranching": MAX_BRANCHING,
        "maxProcesses": MAX_PROCESSES,
        "minSteps": MIN_STEPS,
        **(config or {}),
    }

    if on_progress:
        on_progress("Finding entry points...", 0)

    membership_map: dict[str, str] = {}
    for m in memberships:
        membership_map[m["nodeId"]] = m["communityId"]

    calls_edges = _build_calls_graph(knowledge_graph)
    reverse_calls = _build_reverse_calls_graph(knowledge_graph)
    node_map: dict[str, dict[str, Any]] = {}
    for n in knowledge_graph.iter_nodes():
        node_map[n["id"]] = n

    entry_points = _find_entry_points(knowledge_graph, reverse_calls, calls_edges)

    if on_progress:
        on_progress(f"Found {len(entry_points)} entry points, tracing flows...", 20)

    all_traces: list[list[str]] = []
    for i, entry_id in enumerate(entry_points):
        if len(all_traces) >= cfg["maxProcesses"] * 2:
            break
        traces = _trace_from_entry_point(entry_id, calls_edges, cfg)
        for t in traces:
            if len(t) >= cfg["minSteps"]:
                all_traces.append(t)

    if on_progress:
        on_progress(f"Found {len(all_traces)} traces, deduplicating...", 60)

    unique = _deduplicate_traces(all_traces)
    endpoint_deduped = _deduplicate_by_endpoints(unique)

    limited = sorted(endpoint_deduped, key=len, reverse=True)[:cfg["maxProcesses"]]

    if on_progress:
        on_progress(f"Creating {len(limited)} process nodes...", 80)

    processes: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []

    for idx, trace in enumerate(limited):
        entry_id = trace[0]
        terminal_id = trace[-1]
        comms = list({membership_map[nid] for nid in trace if nid in membership_map})
        process_type = "cross_community" if len(comms) > 1 else "intra_community"

        entry_node = node_map.get(entry_id, {})
        terminal_node = node_map.get(terminal_id, {})
        entry_name = entry_node.get("properties", {}).get("name", "Unknown")
        terminal_name = terminal_node.get("properties", {}).get("name", "Unknown")
        label = f"{_capitalize(entry_name)} -> {_capitalize(terminal_name)}"
        pid = f"proc_{idx}_{_sanitize_id(entry_name)}"

        processes.append({
            "id": pid, "label": label, "heuristicLabel": label,
            "processType": process_type, "stepCount": len(trace),
            "communities": comms, "entryPointId": entry_id,
            "terminalId": terminal_id, "trace": trace,
        })

        for step_idx, nid in enumerate(trace):
            steps.append({"nodeId": nid, "processId": pid, "step": step_idx + 1})

    if on_progress:
        on_progress("Process detection complete!", 100)

    cross = sum(1 for p in processes if p["processType"] == "cross_community")
    avg = (sum(p["stepCount"] for p in processes) / len(processes)) if processes else 0

    return {
        "processes": processes,
        "steps": steps,
        "stats": {
            "totalProcesses": len(processes),
            "crossCommunityCount": cross,
            "avgStepCount": round(avg, 1),
            "entryPointsFound": len(entry_points),
        },
    }


def _build_calls_graph(graph: KnowledgeGraph) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {}
    for rel in graph.iter_relationships():
        if rel.get("type") == "CALLS" and rel.get("confidence", 1.0) >= MIN_TRACE_CONFIDENCE:
            adj.setdefault(rel["sourceId"], []).append(rel["targetId"])
    return adj


def _build_reverse_calls_graph(graph: KnowledgeGraph) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {}
    for rel in graph.iter_relationships():
        if rel.get("type") == "CALLS" and rel.get("confidence", 1.0) >= MIN_TRACE_CONFIDENCE:
            adj.setdefault(rel["targetId"], []).append(rel["sourceId"])
    return adj


def _find_entry_points(
    graph: KnowledgeGraph,
    reverse_calls: dict[str, list[str]],
    calls_edges: dict[str, list[str]],
) -> list[str]:
    symbol_types = {"Function", "Method"}
    candidates: list[dict[str, Any]] = []

    for node in graph.iter_nodes():
        if node.get("label") not in symbol_types:
            continue
        props = node.get("properties", {})
        fp = props.get("filePath", "")
        if is_test_file(fp):
            continue

        callers = reverse_calls.get(node["id"], [])
        callees = calls_edges.get(node["id"], [])
        if not callees:
            continue

        result = calculate_entry_point_score(
            props.get("name", ""),
            props.get("language", "javascript"),
            props.get("isExported", False),
            len(callers), len(callees), fp,
        )

        score = result["score"]
        ast_mult = props.get("astFrameworkMultiplier", 1.0)
        if ast_mult > 1.0:
            score *= ast_mult

        if score > 0:
            candidates.append({"id": node["id"], "score": score})

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return [c["id"] for c in candidates[:200]]


def _trace_from_entry_point(
    entry_id: str,
    calls_edges: dict[str, list[str]],
    config: dict[str, int],
) -> list[list[str]]:
    traces: list[list[str]] = []
    queue: deque[tuple[str, list[str]]] = deque([(entry_id, [entry_id])])

    while queue and len(traces) < config["maxBranching"] * 3:
        current_id, path = queue.popleft()
        callees = calls_edges.get(current_id, [])

        if not callees:
            if len(path) >= config["minSteps"]:
                traces.append(list(path))
        elif len(path) >= config["maxTraceDepth"]:
            if len(path) >= config["minSteps"]:
                traces.append(list(path))
        else:
            limited = callees[:config["maxBranching"]]
            added = False
            for cid in limited:
                if cid not in path:
                    queue.append((cid, path + [cid]))
                    added = True
            if not added and len(path) >= config["minSteps"]:
                traces.append(list(path))

    return traces


def _deduplicate_traces(traces: list[list[str]]) -> list[list[str]]:
    if not traces:
        return []
    sorted_t = sorted(traces, key=len, reverse=True)
    unique: list[list[str]] = []
    for trace in sorted_t:
        key = "->".join(trace)
        is_subset = any("->".join(e) for e in unique if key in "->".join(e))
        if not is_subset:
            unique.append(trace)
    return unique


def _deduplicate_by_endpoints(traces: list[list[str]]) -> list[list[str]]:
    if not traces:
        return []
    by_endpoints: dict[str, list[str]] = {}
    sorted_t = sorted(traces, key=len, reverse=True)
    for trace in sorted_t:
        key = f"{trace[0]}::{trace[-1]}"
        if key not in by_endpoints:
            by_endpoints[key] = trace
    return list(by_endpoints.values())


def _capitalize(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def _sanitize_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", s)[:20].lower()
