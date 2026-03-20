"""Augmentation engine — 1:1 port of gitnexus core/augmentation/engine.js."""
from __future__ import annotations

import os
from typing import Any

from ...storage.repo_manager import list_registered_repos


def _find_repo_for_cwd(cwd: str) -> dict[str, str] | None:
    try:
        entries = list_registered_repos(validate=True)
        resolved = os.path.abspath(cwd)
        best_match = None
        best_len = 0
        for entry in entries:
            repo_resolved = os.path.abspath(entry["path"])
            matched = False
            if resolved == repo_resolved:
                matched = True
            elif resolved.startswith(repo_resolved + os.sep):
                matched = True
            elif repo_resolved.startswith(resolved + os.sep):
                matched = True
            if matched and len(repo_resolved) > best_len:
                best_match = entry
                best_len = len(repo_resolved)
        if not best_match:
            return None
        return {
            "name": best_match["name"],
            "storagePath": best_match.get("storagePath", ""),
            "kuzuPath": os.path.join(best_match.get("storagePath", ""), "kuzu"),
        }
    except Exception:
        return None


def augment(pattern: str, cwd: str = "") -> str:
    if not pattern or len(pattern) < 3:
        return ""
    work_dir = cwd or os.getcwd()
    try:
        repo = _find_repo_for_cwd(work_dir)
        if not repo:
            return ""

        from ...mcp.kuzu_pool import init_kuzu, execute_query

        repo_id = repo["name"].lower()
        init_kuzu(repo_id, repo["kuzuPath"])

        # BM25 search
        escaped = pattern.replace("'", "''")
        tables = [("File", "file_fts"), ("Function", "function_fts"), ("Class", "class_fts"),
                  ("Method", "method_fts"), ("Interface", "interface_fts")]
        bm25_results: list[dict[str, Any]] = []
        for table, index in tables:
            try:
                rows = execute_query(repo_id,
                    f"CALL QUERY_FTS_INDEX('{table}', '{index}', '{escaped}', conjunctive := false) "
                    f"YIELD node, score RETURN node.filePath AS fp, score ORDER BY score DESC LIMIT 10")
                for row in rows:
                    bm25_results.append({"filePath": row.get("fp", ""), "score": row.get("score", 0)})
            except Exception:
                pass

        if not bm25_results:
            return ""

        # Map to symbols
        symbol_matches: list[dict[str, Any]] = []
        first_word = pattern.replace("'", "''").split()[0] if pattern.split() else pattern
        for result in bm25_results[:5]:
            esc_fp = result["filePath"].replace("'", "''")
            try:
                symbols = execute_query(repo_id,
                    f"MATCH (n) WHERE n.filePath = '{esc_fp}' AND n.name CONTAINS '{first_word}' "
                    f"RETURN n.id AS id, n.name AS name, n.filePath AS filePath LIMIT 3")
                for sym in symbols:
                    symbol_matches.append({
                        "nodeId": sym.get("id", ""), "name": sym.get("name", ""),
                        "filePath": sym.get("filePath", ""), "score": result["score"],
                    })
            except Exception:
                pass

        if not symbol_matches:
            return ""

        # Enrich top matches
        enriched: list[dict[str, Any]] = []
        seen: set[str] = set()
        for sym in symbol_matches[:5]:
            nid = sym["nodeId"]
            if nid in seen:
                continue
            seen.add(nid)
            esc_id = nid.replace("'", "''")

            callers: list[str] = []
            try:
                rows = execute_query(repo_id,
                    f"MATCH (caller)-[:CodeRelation {{type: 'CALLS'}}]->(n {{id: '{esc_id}'}}) "
                    f"RETURN caller.name AS name LIMIT 3")
                callers = [r.get("name", "") for r in rows if r.get("name")]
            except Exception:
                pass

            callees: list[str] = []
            try:
                rows = execute_query(repo_id,
                    f"MATCH (n {{id: '{esc_id}'}})-[:CodeRelation {{type: 'CALLS'}}]->(callee) "
                    f"RETURN callee.name AS name LIMIT 3")
                callees = [r.get("name", "") for r in rows if r.get("name")]
            except Exception:
                pass

            processes: list[str] = []
            try:
                rows = execute_query(repo_id,
                    f"MATCH (n {{id: '{esc_id}'}})-[r:CodeRelation {{type: 'STEP_IN_PROCESS'}}]->(p:Process) "
                    f"RETURN p.heuristicLabel AS label, r.step AS step, p.stepCount AS stepCount")
                for r in rows:
                    label = r.get("label", "")
                    step = r.get("step", 0)
                    sc = r.get("stepCount", 0)
                    if label:
                        processes.append(f"{label} (step {step}/{sc})")
            except Exception:
                pass

            enriched.append({
                "name": sym["name"], "filePath": sym["filePath"],
                "callers": callers, "callees": callees, "processes": processes,
            })

        if not enriched:
            return ""

        lines = [f"[CodebaseIntelligence] {len(enriched)} related symbols found:", ""]
        for item in enriched:
            lines.append(f"{item['name']} ({item['filePath']})")
            if item["callers"]:
                lines.append(f"  Called by: {', '.join(item['callers'])}")
            if item["callees"]:
                lines.append(f"  Calls: {', '.join(item['callees'])}")
            if item["processes"]:
                lines.append(f"  Flows: {', '.join(item['processes'])}")
            lines.append("")
        return "\n".join(lines).strip()
    except Exception:
        return ""
