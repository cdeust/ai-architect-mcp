"""Rename tool — 1:1 port of gitnexus LocalBackend.rename()."""
from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from .local_backend_context import context_tool


async def rename_tool(backend: Any, repo: dict[str, Any], params: dict[str, Any]) -> Any:
    await backend.ensure_initialized(repo["id"])
    new_name = params.get("new_name", "")
    file_path = params.get("file_path")
    dry_run = params.get("dry_run", True)

    if not params.get("symbol_name") and not params.get("symbol_uid"):
        return {"error": "Either symbol_name or symbol_uid is required."}

    lookup = await context_tool(backend, repo, {
        "name": params.get("symbol_name"), "uid": params.get("symbol_uid"), "file_path": file_path,
    })
    if lookup.get("status") == "ambiguous":
        return lookup
    if lookup.get("error"):
        return lookup

    sym = lookup["symbol"]
    old_name = sym["name"]
    if old_name == new_name:
        return {"error": "New name is the same as the current name."}

    repo_path = repo["repoPath"]
    changes: dict[str, dict[str, Any]] = {}

    def add_edit(fp: str, line: int, old_text: str, new_text: str, confidence: str) -> None:
        if fp not in changes:
            changes[fp] = {"file_path": fp, "edits": []}
        changes[fp]["edits"].append({"line": line, "old_text": old_text, "new_text": new_text, "confidence": confidence})

    def assert_safe(fp: str) -> str:
        full = os.path.abspath(os.path.join(repo_path, fp))
        if not full.startswith(os.path.abspath(repo_path)):
            raise ValueError(f"Path traversal blocked: {fp}")
        return full

    escaped_old = re.escape(old_name)
    pattern = re.compile(rf"\b{escaped_old}\b")

    # Definition edit
    graph_edits = 0
    if sym.get("filePath") and sym.get("startLine"):
        try:
            full = assert_safe(sym["filePath"])
            with open(full, encoding="utf-8") as f:
                lines = f.read().split("\n")
            idx = sym["startLine"] - 1
            if 0 <= idx < len(lines) and old_name in lines[idx]:
                add_edit(sym["filePath"], sym["startLine"], lines[idx].strip(), pattern.sub(new_name, lines[idx]).strip(), "graph")
                graph_edits += 1
        except Exception:
            pass

    # Incoming refs
    all_incoming = []
    for cat in ("calls", "imports", "extends", "implements"):
        all_incoming.extend(lookup.get("incoming", {}).get(cat, []))

    graph_files: set[str] = {sym.get("filePath", "")}
    for ref in all_incoming:
        fp = ref.get("filePath")
        if not fp:
            continue
        graph_files.add(fp)
        try:
            full = assert_safe(fp)
            with open(full, encoding="utf-8") as f:
                lines = f.read().split("\n")
            for i, line in enumerate(lines):
                if old_name in line:
                    add_edit(fp, i + 1, line.strip(), pattern.sub(new_name, line).strip(), "graph")
                    graph_edits += 1
                    break
        except Exception:
            pass

    # Text search for refs graph might have missed
    text_edits = 0
    try:
        result = subprocess.run(
            ["rg", "-l", "--type-add", "code:*.{ts,tsx,js,jsx,py,go,rs,java,c,h,cpp,cc,cs,php,swift,kt}",
             "-t", "code", rf"\b{old_name}\b", "."],
            cwd=repo_path, capture_output=True, text=True, timeout=5,
        )
        rg_files = [f for f in result.stdout.strip().split("\n") if f]
        for rg_file in rg_files:
            norm = rg_file.replace("\\", "/").lstrip("./")
            if norm in graph_files:
                continue
            try:
                full = assert_safe(norm)
                with open(full, encoding="utf-8") as f:
                    lines = f.read().split("\n")
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        add_edit(norm, i + 1, line.strip(), pattern.sub(new_name, line).strip(), "text_search")
                        text_edits += 1
            except Exception:
                pass
    except Exception:
        pass

    all_changes = list(changes.values())
    total_edits = sum(len(c["edits"]) for c in all_changes)

    if not dry_run:
        for change in all_changes:
            try:
                full = assert_safe(change["file_path"])
                with open(full, encoding="utf-8") as f:
                    content = f.read()
                content = pattern.sub(new_name, content)
                with open(full, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass

    return {
        "status": "success", "old_name": old_name, "new_name": new_name,
        "files_affected": len(all_changes), "total_edits": total_edits,
        "graph_edits": graph_edits, "text_search_edits": text_edits,
        "changes": all_changes, "applied": not dry_run,
    }
