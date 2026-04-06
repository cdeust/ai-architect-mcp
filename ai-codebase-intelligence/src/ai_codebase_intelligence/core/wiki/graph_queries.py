"""Graph queries for wiki generation — 1:1 port of gitnexus core/wiki/graph-queries.js."""
from __future__ import annotations

from typing import Any

from ...mcp.kuzu_pool import init_kuzu, execute_query, close_repo

REPO_ID = "__wiki__"


def init_wiki_db(kuzu_path: str) -> None:
    init_kuzu(REPO_ID, kuzu_path)


def close_wiki_db() -> None:
    close_repo(REPO_ID)


def get_files_with_exports() -> list[dict[str, Any]]:
    rows = execute_query(REPO_ID,
        "MATCH (f:File)-[:CodeRelation {type: 'DEFINES'}]->(n) "
        "WHERE n.isExported = true "
        "RETURN f.filePath AS filePath, n.name AS name, labels(n)[0] AS type "
        "ORDER BY f.filePath")
    file_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        fp = row.get("filePath", "")
        if fp not in file_map:
            file_map[fp] = {"filePath": fp, "symbols": []}
        file_map[fp]["symbols"].append({"name": row.get("name", ""), "type": row.get("type", "")})
    return list(file_map.values())


def get_all_files() -> list[str]:
    rows = execute_query(REPO_ID, "MATCH (f:File) RETURN f.filePath AS filePath ORDER BY f.filePath")
    return [r.get("filePath", "") for r in rows]


def get_inter_file_call_edges() -> list[dict[str, str]]:
    rows = execute_query(REPO_ID,
        "MATCH (a)-[:CodeRelation {type: 'CALLS'}]->(b) "
        "WHERE a.filePath <> b.filePath "
        "RETURN DISTINCT a.filePath AS fromFile, a.name AS fromName, "
        "b.filePath AS toFile, b.name AS toName")
    return [{"fromFile": r.get("fromFile", ""), "fromName": r.get("fromName", ""),
             "toFile": r.get("toFile", ""), "toName": r.get("toName", "")} for r in rows]


def get_intra_module_call_edges(file_paths: list[str]) -> list[dict[str, str]]:
    if not file_paths:
        return []
    fl = ", ".join(f"'{f.replace(chr(39), chr(39)+chr(39))}'" for f in file_paths)
    rows = execute_query(REPO_ID,
        f"MATCH (a)-[:CodeRelation {{type: 'CALLS'}}]->(b) "
        f"WHERE a.filePath IN [{fl}] AND b.filePath IN [{fl}] "
        f"RETURN DISTINCT a.filePath AS fromFile, a.name AS fromName, "
        f"b.filePath AS toFile, b.name AS toName")
    return [{"fromFile": r.get("fromFile", ""), "fromName": r.get("fromName", ""),
             "toFile": r.get("toFile", ""), "toName": r.get("toName", "")} for r in rows]


def get_inter_module_call_edges(file_paths: list[str]) -> dict[str, list[dict[str, str]]]:
    if not file_paths:
        return {"outgoing": [], "incoming": []}
    fl = ", ".join(f"'{f.replace(chr(39), chr(39)+chr(39))}'" for f in file_paths)
    out_rows = execute_query(REPO_ID,
        f"MATCH (a)-[:CodeRelation {{type: 'CALLS'}}]->(b) "
        f"WHERE a.filePath IN [{fl}] AND NOT b.filePath IN [{fl}] "
        f"RETURN DISTINCT a.filePath AS fromFile, a.name AS fromName, "
        f"b.filePath AS toFile, b.name AS toName LIMIT 30")
    in_rows = execute_query(REPO_ID,
        f"MATCH (a)-[:CodeRelation {{type: 'CALLS'}}]->(b) "
        f"WHERE NOT a.filePath IN [{fl}] AND b.filePath IN [{fl}] "
        f"RETURN DISTINCT a.filePath AS fromFile, a.name AS fromName, "
        f"b.filePath AS toFile, b.name AS toName LIMIT 30")
    fmt = lambda rows: [{"fromFile": r.get("fromFile", ""), "fromName": r.get("fromName", ""),
                         "toFile": r.get("toFile", ""), "toName": r.get("toName", "")} for r in rows]
    return {"outgoing": fmt(out_rows), "incoming": fmt(in_rows)}


def _group_steps(proc_rows: list[dict[str, Any]], step_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps_by_proc: dict[str, list[dict[str, Any]]] = {}
    for s in step_rows:
        pid = s.get("processId", "")
        steps_by_proc.setdefault(pid, []).append({
            "step": s.get("step", 0), "name": s.get("name", ""),
            "filePath": s.get("filePath", ""), "type": s.get("type", ""),
        })
    result = []
    for row in proc_rows:
        pid = row.get("id", "")
        steps = sorted(steps_by_proc.get(pid, []), key=lambda x: x["step"])
        result.append({
            "id": pid, "label": row.get("label", pid),
            "type": row.get("type", "unknown"), "stepCount": row.get("stepCount", 0),
            "steps": steps,
        })
    return result


def get_processes_for_files(file_paths: list[str], limit: int = 5) -> list[dict[str, Any]]:
    if not file_paths:
        return []
    fl = ", ".join(f"'{f.replace(chr(39), chr(39)+chr(39))}'" for f in file_paths)
    proc_rows = execute_query(REPO_ID,
        f"MATCH (s)-[r:CodeRelation {{type: 'STEP_IN_PROCESS'}}]->(p:Process) "
        f"WHERE s.filePath IN [{fl}] "
        f"RETURN DISTINCT p.id AS id, p.heuristicLabel AS label, "
        f"p.processType AS type, p.stepCount AS stepCount "
        f"ORDER BY stepCount DESC LIMIT {limit}")
    if not proc_rows:
        return []
    pids = ", ".join(f"'{r.get('id', '').replace(chr(39), chr(39)+chr(39))}'" for r in proc_rows)
    step_rows = execute_query(REPO_ID,
        f"MATCH (s)-[r:CodeRelation {{type: 'STEP_IN_PROCESS'}}]->(p:Process) "
        f"WHERE p.id IN [{pids}] "
        f"RETURN s.name AS name, s.filePath AS filePath, labels(s)[0] AS type, "
        f"r.step AS step, p.id AS processId ORDER BY p.id, r.step")
    return _group_steps(proc_rows, step_rows)


def get_all_processes(limit: int = 20) -> list[dict[str, Any]]:
    proc_rows = execute_query(REPO_ID,
        f"MATCH (p:Process) RETURN p.id AS id, p.heuristicLabel AS label, "
        f"p.processType AS type, p.stepCount AS stepCount "
        f"ORDER BY stepCount DESC LIMIT {limit}")
    if not proc_rows:
        return []
    pids = ", ".join(f"'{r.get('id', '').replace(chr(39), chr(39)+chr(39))}'" for r in proc_rows)
    step_rows = execute_query(REPO_ID,
        f"MATCH (s)-[r:CodeRelation {{type: 'STEP_IN_PROCESS'}}]->(p:Process) "
        f"WHERE p.id IN [{pids}] "
        f"RETURN s.name AS name, s.filePath AS filePath, labels(s)[0] AS type, "
        f"r.step AS step, p.id AS processId ORDER BY p.id, r.step")
    return _group_steps(proc_rows, step_rows)


def get_inter_module_edges_for_overview(module_files: dict[str, list[str]]) -> list[dict[str, Any]]:
    file_to_mod: dict[str, str] = {}
    for mod, files in module_files.items():
        for f in files:
            file_to_mod[f] = mod
    all_edges = get_inter_file_call_edges()
    counts: dict[str, int] = {}
    for e in all_edges:
        fm = file_to_mod.get(e["fromFile"])
        tm = file_to_mod.get(e["toFile"])
        if fm and tm and fm != tm:
            key = f"{fm}|||{tm}"
            counts[key] = counts.get(key, 0) + 1
    return sorted(
        [{"from": k.split("|||")[0], "to": k.split("|||")[1], "count": v} for k, v in counts.items()],
        key=lambda x: -x["count"],
    )


def get_community_file_mapping() -> list[dict[str, Any]]:
    comm_rows = execute_query(REPO_ID,
        "MATCH (c:Community) RETURN c.id AS id, c.heuristicLabel AS label, "
        "c.keywords AS keywords, c.description AS description, "
        "c.cohesion AS cohesion, c.symbolCount AS symbolCount "
        "ORDER BY c.symbolCount DESC")
    if not comm_rows:
        return []
    member_rows = execute_query(REPO_ID,
        "MATCH (n)-[:CodeRelation {type: 'MEMBER_OF'}]->(c:Community) "
        "WHERE n.filePath IS NOT NULL "
        "RETURN n.filePath AS filePath, c.id AS communityId")

    file_comm: dict[str, dict[str, int]] = {}
    for r in member_rows:
        fp = r.get("filePath", "")
        cid = r.get("communityId", "")
        file_comm.setdefault(fp, {})
        file_comm[fp][cid] = file_comm[fp].get(cid, 0) + 1

    comm_files: dict[str, dict[str, list[str]]] = {}
    for r in comm_rows:
        comm_files[r.get("id", "")] = {"primary": [], "secondary": []}

    for fp, counts in file_comm.items():
        max_c = max(counts, key=lambda k: counts[k])
        if max_c in comm_files:
            comm_files[max_c]["primary"].append(fp)
        for cid in counts:
            if cid != max_c and cid in comm_files:
                comm_files[cid]["secondary"].append(fp)

    results: list[dict[str, Any]] = []
    other_files: list[str] = []
    for r in comm_rows:
        cid = r.get("id", "")
        entry = comm_files.get(cid, {"primary": [], "secondary": []})
        if len(entry["primary"]) < 2:
            other_files.extend(entry["primary"])
            continue
        kw = r.get("keywords", [])
        if isinstance(kw, str):
            kw = [k.strip() for k in kw.split(",")]
        results.append({
            "communityId": cid, "label": r.get("label", cid),
            "keywords": kw if isinstance(kw, list) else [],
            "description": r.get("description", ""),
            "cohesion": r.get("cohesion", 0),
            "symbolCount": r.get("symbolCount", 0),
            "files": entry["primary"], "secondaryFiles": entry["secondary"],
        })
    if other_files:
        results.append({
            "communityId": "__other__", "label": "Other small clusters",
            "keywords": [], "description": "Files from small communities merged",
            "cohesion": 0, "symbolCount": 0,
            "files": other_files, "secondaryFiles": [],
        })
    return results[:30]


def get_inter_community_call_edges() -> list[dict[str, str]]:
    """Get call edges that cross community boundaries."""
    rows = execute_query(REPO_ID,
        "MATCH (a)-[:CodeRelation {type: 'CALLS'}]->(b), "
        "(a)-[:CodeRelation {type: 'MEMBER_OF'}]->(ca:Community), "
        "(b)-[:CodeRelation {type: 'MEMBER_OF'}]->(cb:Community) "
        "WHERE ca.id <> cb.id "
        "RETURN DISTINCT ca.heuristicLabel AS fromComm, "
        "cb.heuristicLabel AS toComm, a.name AS fromName, b.name AS toName "
        "LIMIT 100")
    return rows or []


def get_cross_community_processes(limit: int = 10) -> list[dict[str, Any]]:
    """Get processes that span multiple communities."""
    rows = execute_query(REPO_ID,
        "MATCH (p:Process) WHERE p.processType = 'cross_community' "
        "RETURN p.id AS id, p.heuristicLabel AS label, "
        "p.stepCount AS stepCount, p.communities AS communities "
        f"ORDER BY p.stepCount DESC LIMIT {limit}")
    return rows or []
