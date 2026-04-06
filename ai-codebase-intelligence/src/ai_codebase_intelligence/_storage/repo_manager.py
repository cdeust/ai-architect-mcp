"""Repository registry — persistent catalog of indexed repositories.

Stores and retrieves RepoMetadata as JSON. The registry file and
database directory are module-level constants that can be patched
in tests.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .._models.pipeline_types import RepoMetadata

logger = logging.getLogger(__name__)

REGISTRY_DIR: Path = Path.home() / ".ai-codebase-intelligence"
REGISTRY_FILE: Path = REGISTRY_DIR / "registry.json"
DB_BASE_DIR: Path = REGISTRY_DIR / "databases"


def load_registry() -> dict[str, RepoMetadata]:
    """Load the repository registry from disk.

    Returns:
        Mapping of repo_path -> RepoMetadata. Empty dict if file
        is missing or corrupted.
    """
    if not REGISTRY_FILE.exists():
        return {}
    try:
        raw = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupted registry at %s — returning empty", REGISTRY_FILE)
        return {}

    result: dict[str, RepoMetadata] = {}
    for path, data in raw.items():
        result[path] = RepoMetadata(**data)
    return result


def save_registry(registry: dict[str, RepoMetadata]) -> None:
    """Persist the registry to disk.

    Args:
        registry: Mapping of repo_path -> RepoMetadata.
    """
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        path: meta.model_dump(mode="json") for path, meta in registry.items()
    }
    REGISTRY_FILE.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )


def register_repo(
    repo_path: str,
    repo_name: str,
    commit_hash: str = "",
) -> RepoMetadata:
    """Register a repository in the catalog.

    Args:
        repo_path: Absolute path to the repository.
        repo_name: Human-readable name.
        commit_hash: Git commit hash at indexing time.

    Returns:
        The created RepoMetadata.
    """
    registry = load_registry()
    meta = RepoMetadata(
        repo_path=repo_path,
        repo_name=repo_name,
        last_commit=commit_hash,
        last_indexed_at=datetime.now(tz=timezone.utc),
    )
    registry[repo_path] = meta
    save_registry(registry)
    return meta


def unregister_repo(repo_path: str) -> bool:
    """Remove a repository from the catalog.

    Args:
        repo_path: Absolute path to the repository.

    Returns:
        True if removed, False if not found.
    """
    registry = load_registry()
    if repo_path not in registry:
        return False
    del registry[repo_path]
    save_registry(registry)

    db_path = DB_BASE_DIR / registry.get(repo_path, RepoMetadata(repo_path=repo_path)).repo_name
    if db_path.exists():
        import shutil
        shutil.rmtree(db_path, ignore_errors=True)

    return True
