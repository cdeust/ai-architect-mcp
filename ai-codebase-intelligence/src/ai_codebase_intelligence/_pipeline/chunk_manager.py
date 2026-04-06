"""Chunk manager — splits file lists into byte-budget-bounded chunks.

Files are grouped into chunks whose total on-disk size stays within
a configurable byte budget. Single files exceeding the budget are
skipped entirely (they cannot fit in any chunk).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_BYTE_BUDGET: int = 20 * 1024 * 1024  # 20 MB


@dataclass
class Chunk:
    """A group of files fitting within a byte budget.

    Args:
        files: Paths of files in this chunk.
        total_bytes: Sum of file sizes in bytes.
    """

    files: list[str] = field(default_factory=list)
    total_bytes: int = 0


def create_chunks(
    files: list[str],
    byte_budget: int = DEFAULT_BYTE_BUDGET,
) -> list[Chunk]:
    """Split *files* into chunks bounded by *byte_budget*.

    Files whose individual size exceeds the budget are skipped.
    Non-existent files are silently ignored.

    Args:
        files: Absolute paths to source files.
        byte_budget: Maximum total bytes per chunk.

    Returns:
        List of Chunk objects, each within the budget.
    """
    if not files:
        return []

    sized: list[tuple[str, int]] = []
    for path in files:
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        if size > byte_budget:
            continue
        sized.append((path, size))

    if not sized:
        return []

    chunks: list[Chunk] = []
    current = Chunk()

    for path, size in sized:
        if current.files and current.total_bytes + size > byte_budget:
            chunks.append(current)
            current = Chunk()
        current.files.append(path)
        current.total_bytes += size

    if current.files:
        chunks.append(current)

    return chunks
