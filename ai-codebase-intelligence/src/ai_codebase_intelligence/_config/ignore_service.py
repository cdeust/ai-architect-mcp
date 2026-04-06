from __future__ import annotations

from ..config.ignore_service import (
    DEFAULT_IGNORE_LIST,
    IGNORED_EXTENSIONS,
    IGNORED_FILES,
)

DEFAULT_IGNORE_DIRS: frozenset[str] = DEFAULT_IGNORE_LIST | frozenset({
    "DerivedData",
})

MAX_FILE_SIZE_BYTES: int = 1_000_000


def should_ignore_dir(name: str) -> bool:
    """Check if a directory name should be ignored.

    Args:
        name: The directory name (not full path).

    Returns:
        True if the directory should be ignored.
    """
    if name in DEFAULT_IGNORE_DIRS:
        return True
    if name.startswith("."):
        return True
    return False


def should_ignore_file(filename: str) -> bool:
    """Check if a file should be ignored based on name and extension.

    Args:
        filename: The filename (not full path).

    Returns:
        True if the file should be ignored.
    """
    if filename in IGNORED_FILES:
        return True

    lower = filename.lower()

    # Check compound extensions first (.min.js, .min.css)
    last_dot = lower.rfind(".")
    if last_dot != -1:
        second_last_dot = lower.rfind(".", 0, last_dot)
        if second_last_dot != -1:
            compound_ext = lower[second_last_dot:]
            if compound_ext in IGNORED_EXTENSIONS:
                return True

        ext = lower[last_dot:]
        if ext in IGNORED_EXTENSIONS:
            return True

    return False


__all__ = [
    "DEFAULT_IGNORE_DIRS",
    "IGNORED_EXTENSIONS",
    "IGNORED_FILES",
    "MAX_FILE_SIZE_BYTES",
    "should_ignore_dir",
    "should_ignore_file",
]
