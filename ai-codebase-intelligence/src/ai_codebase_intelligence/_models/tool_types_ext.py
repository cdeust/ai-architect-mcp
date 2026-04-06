"""Extended tool input/output types — rename, scan, and mutation models.

Supplements the core tool types with models for graph mutation
operations like rename-symbol.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RenameInput(BaseModel):
    """Input for the rename-symbol tool.

    Args:
        old_name: Current symbol name.
        new_name: Desired new name.
        repo_path: Repository path (empty = auto-detect).
    """

    old_name: str = Field(description="Current symbol name")
    new_name: str = Field(description="Desired new name")
    repo_path: str = Field(default="", description="Repository path")


class RenameOutput(BaseModel):
    """Output of the rename-symbol tool.

    Args:
        files_affected: Paths of files that were (or would be) modified.
        symbols_renamed: Count of symbol references renamed.
        relationships_updated: Count of graph edges updated.
    """

    files_affected: list[str] = Field(
        default_factory=list,
        description="Files modified by the rename",
    )
    symbols_renamed: int = Field(
        default=0, ge=0,
        description="Number of symbol references renamed",
    )
    relationships_updated: int = Field(
        default=0, ge=0,
        description="Number of graph relationships updated",
    )
