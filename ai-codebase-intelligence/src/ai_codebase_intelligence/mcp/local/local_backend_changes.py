"""Detect changes tool — uses GraphIndex instead of KuzuDB."""
from __future__ import annotations

import subprocess
from typing import Any

from ...core.storage.repo_store import get_index


async def detect_changes_tool(backend: Any, repo: dict[str, Any], params: dict[str, Any]) -> Any:
    await backend.ensure_initialized(repo["id"])
    scope = params.get("scope", "unstaged")

    if scope == "staged":
        diff_args = ["diff", "--staged", "--name-only"]
    elif scope == "all":
        diff_args = ["diff", "HEAD", "--name-only"]
    elif scope == "compare":
        base_ref = params.get("base_ref")
        if not base_ref:
            return {"error": 'base_ref is required for "compare" scope'}
        diff_args = ["diff", base_ref, "--name-only"]
    else:
        diff_args = ["diff", "--name-only"]

    changed_files = params.get("changed_files")
    if not changed_files:
        try:
            result = subprocess.run(
                ["git", *diff_args], cwd=repo["repoPath"],
                capture_output=True, text=True, check=True,
            )
            changed_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception as e:
            return {"error": f"Git diff failed: {e}"}

    if not changed_files:
        return {
            "summary": {"changed_count": 0, "affected_count": 0, "risk_level": "none", "message": "No changes detected."},
            "changed_symbols": [], "affected_processes": [],
        }

    index = get_index(repo["id"])

    changed_symbols: list[dict[str, Any]] = []
    for file in changed_files:
        norm = file.replace("\\", "/")
        nodes = index.find_by_file(norm)
        for node in nodes:
            changed_symbols.append({
                "id": node.id, "name": node.name,
                "type": node.label.value, "filePath": node.file_path,
                "change_type": "Modified",
            })

    affected_processes: dict[str, dict[str, Any]] = {}
    for sym in changed_symbols:
        procs = index.get_processes_for_node(sym["id"])
        for proc in procs:
            pid = proc["id"]
            if pid not in affected_processes:
                affected_processes[pid] = {
                    "id": pid, "name": proc["label"],
                    "step_count": proc["stepCount"], "changed_steps": [],
                }
            affected_processes[pid]["changed_steps"].append({
                "symbol": sym["name"], "step": proc["step"],
            })

    pc = len(affected_processes)
    risk = "low" if pc == 0 else "medium" if pc <= 5 else "high" if pc <= 15 else "critical"

    return {
        "summary": {
            "changed_count": len(changed_symbols), "affected_count": pc,
            "changed_files": len(changed_files), "risk_level": risk,
        },
        "changed_symbols": changed_symbols,
        "affected_processes": list(affected_processes.values()),
    }
