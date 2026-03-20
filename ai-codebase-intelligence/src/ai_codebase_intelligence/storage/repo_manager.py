from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

GITNEXUS_DIR = ".gitnexus"


def get_storage_path(repo_path: str) -> str:
    return os.path.join(os.path.abspath(repo_path), GITNEXUS_DIR)


def get_storage_paths(repo_path: str) -> dict[str, str]:
    storage_path = get_storage_path(repo_path)
    return {
        "storagePath": storage_path,
        "kuzuPath": os.path.join(storage_path, "kuzu"),
        "metaPath": os.path.join(storage_path, "meta.json"),
    }


def load_meta(storage_path: str) -> dict[str, Any] | None:
    try:
        meta_path = os.path.join(storage_path, "meta.json")
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_meta(storage_path: str, meta: dict[str, Any]) -> None:
    os.makedirs(storage_path, exist_ok=True)
    meta_path = os.path.join(storage_path, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def has_index(repo_path: str) -> bool:
    paths = get_storage_paths(repo_path)
    return os.path.exists(paths["metaPath"])


def load_repo(repo_path: str) -> dict[str, Any] | None:
    paths = get_storage_paths(repo_path)
    meta = load_meta(paths["storagePath"])
    if meta is None:
        return None
    return {
        "repoPath": os.path.abspath(repo_path),
        **paths,
        "meta": meta,
    }


def find_repo(start_path: str) -> dict[str, Any] | None:
    current = os.path.abspath(start_path)
    root = os.path.splitdrive(current)[0] + os.sep
    while current != root:
        repo = load_repo(current)
        if repo is not None:
            return repo
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def add_to_gitignore(repo_path: str) -> None:
    gitignore_path = os.path.join(repo_path, ".gitignore")
    try:
        with open(gitignore_path, encoding="utf-8") as f:
            content = f.read()
        if GITNEXUS_DIR in content:
            return
        new_content = (
            f"{content}{GITNEXUS_DIR}\n"
            if content.endswith("\n")
            else f"{content}\n{GITNEXUS_DIR}\n"
        )
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(f"{GITNEXUS_DIR}\n")


def get_global_dir() -> str:
    return os.path.join(str(Path.home()), ".gitnexus")


def get_global_registry_path() -> str:
    return os.path.join(get_global_dir(), "registry.json")


def read_registry() -> list[dict[str, Any]]:
    try:
        with open(get_global_registry_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_registry(entries: list[dict[str, Any]]) -> None:
    d = get_global_dir()
    os.makedirs(d, exist_ok=True)
    with open(get_global_registry_path(), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def register_repo(repo_path: str, meta: dict[str, Any]) -> None:
    resolved = os.path.abspath(repo_path)
    name = os.path.basename(resolved)
    paths = get_storage_paths(resolved)
    entries = read_registry()

    existing = -1
    for i, e in enumerate(entries):
        if os.path.abspath(e.get("path", "")) == resolved:
            existing = i
            break

    entry: dict[str, Any] = {
        "name": name,
        "path": resolved,
        "storagePath": paths["storagePath"],
        "indexedAt": meta.get("indexedAt", ""),
        "lastCommit": meta.get("lastCommit", ""),
        "stats": meta.get("stats", {}),
    }

    if existing >= 0:
        entries[existing] = entry
    else:
        entries.append(entry)

    _write_registry(entries)


def unregister_repo(repo_path: str) -> None:
    resolved = os.path.abspath(repo_path)
    entries = read_registry()
    filtered = [e for e in entries if os.path.abspath(e.get("path", "")) != resolved]
    _write_registry(filtered)


def list_registered_repos(validate: bool = False) -> list[dict[str, Any]]:
    entries = read_registry()
    if not validate:
        return entries

    valid: list[dict[str, Any]] = []
    for entry in entries:
        meta_path = os.path.join(entry.get("storagePath", ""), "meta.json")
        if os.path.exists(meta_path):
            valid.append(entry)

    if len(valid) != len(entries):
        _write_registry(valid)

    return valid


def get_global_config_path() -> str:
    return os.path.join(get_global_dir(), "config.json")


def load_cli_config() -> dict[str, Any]:
    try:
        with open(get_global_config_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_cli_config(config: dict[str, Any]) -> None:
    d = get_global_dir()
    os.makedirs(d, exist_ok=True)
    config_path = get_global_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    try:
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
