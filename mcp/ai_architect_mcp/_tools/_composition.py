"""Shared composition root and stage context singletons.

Consolidates the factory pattern into a single module. All tool
modules import from here instead of maintaining independent singletons.
"""

from __future__ import annotations

from pathlib import Path

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._config.loader import load_config
from ai_architect_mcp._context.stage_context import StageContext

_root: CompositionRoot | None = None
_context: StageContext | None = None


def get_root() -> CompositionRoot:
    """Get or create the shared composition root.

    Returns:
        The singleton CompositionRoot instance.
    """
    global _root
    if _root is None:
        cfg = load_config()
        _root = CompositionRoot(
            project_root=Path(cfg.adapters.project_root).resolve(),
            repo_path=cfg.adapters.git_repo_path,
            github_repo=cfg.adapters.github_repo or None,
            data_dir=Path(cfg.context.data_dir),
        )
    return _root


def reset_root(new_root: CompositionRoot) -> None:
    """Replace the shared composition root.

    Called by ai_architect_init_pipeline to re-target a new repo.

    Args:
        new_root: The new CompositionRoot to use.
    """
    global _root
    _root = new_root


def get_context() -> StageContext:
    """Get or create the shared stage context.

    Returns:
        The singleton StageContext instance.
    """
    global _context
    if _context is None:
        _context = StageContext()
    return _context


def reset_context(persist_dir: Path | None = None) -> None:
    """Replace the shared stage context.

    Args:
        persist_dir: Optional directory for durable artifact persistence.
    """
    global _context
    from ai_architect_mcp._context.artifact_store import ArtifactStore

    store = ArtifactStore(persist_dir=persist_dir)
    _context = StageContext(store=store)
