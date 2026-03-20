from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from ...config.ignore_service import should_ignore_path

READ_CONCURRENCY = 32
MAX_FILE_SIZE = 512 * 1024  # 512KB


def walk_repository_paths(
    repo_path: str,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, Any]]:
    root = Path(repo_path)
    all_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        for fn in filenames:
            rel = os.path.join(rel_dir, fn).replace("\\", "/")
            if rel.startswith("./"):
                rel = rel[2:]
            all_files.append(rel)

    filtered = [f for f in all_files if not should_ignore_path(f)]

    entries: list[dict[str, Any]] = []
    skipped_large = 0
    for i, relative_path in enumerate(filtered):
        full_path = os.path.join(repo_path, relative_path)
        try:
            size = os.path.getsize(full_path)
        except OSError:
            continue
        if size > MAX_FILE_SIZE:
            skipped_large += 1
            continue
        entries.append({"path": relative_path.replace("\\", "/"), "size": size})
        if on_progress is not None:
            on_progress(i + 1, len(filtered), relative_path)

    return entries


def read_file_contents(
    repo_path: str,
    relative_paths: list[str],
) -> dict[str, str]:
    contents: dict[str, str] = {}
    for relative_path in relative_paths:
        full_path = os.path.join(repo_path, relative_path)
        try:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                contents[relative_path] = f.read()
        except OSError:
            pass
    return contents


def walk_repository(
    repo_path: str,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, str]]:
    scanned = walk_repository_paths(repo_path, on_progress)
    paths = [f["path"] for f in scanned]
    contents = read_file_contents(repo_path, paths)
    return [
        {"path": f["path"], "content": contents[f["path"]]}
        for f in scanned
        if f["path"] in contents
    ]
