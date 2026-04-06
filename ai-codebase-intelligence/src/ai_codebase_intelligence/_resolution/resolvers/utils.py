"""Suffix-index builder for file path lookup by stem and parent/stem."""

from __future__ import annotations

from pathlib import PurePosixPath


def build_suffix_index(file_paths: list[str]) -> dict[str, list[str]]:
    """Build an index mapping filename suffixes to their full paths.

    For each file path, indexes by:
    - bare stem (e.g. "models")
    - parent/stem (e.g. "src/models")
    - grandparent/parent/stem, etc.

    Args:
        file_paths: List of file paths to index.

    Returns:
        Dict mapping suffix keys to lists of matching paths.
    """
    index: dict[str, list[str]] = {}
    seen_pairs: set[tuple[str, str]] = set()

    for path_str in file_paths:
        p = PurePosixPath(path_str)
        stem = p.stem
        parts = list(p.parent.parts)

        # Build suffix keys from most specific to least
        # stem, parent/stem, grandparent/parent/stem, ...
        keys: list[str] = [stem]
        accumulated = stem
        for part in reversed(parts):
            if part == "/":
                continue
            accumulated = f"{part}/{accumulated}"
            keys.append(accumulated)

        for key in keys:
            pair = (key, path_str)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if key not in index:
                index[key] = []
            index[key].append(path_str)

    return index
