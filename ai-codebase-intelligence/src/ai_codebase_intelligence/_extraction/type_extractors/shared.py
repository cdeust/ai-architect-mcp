"""Shared type-string parsing utilities.

Pure functions for extracting type names, nullable wrappers, and
generic type arguments from type annotation strings. Used by all
language-specific type extractors.
"""

from __future__ import annotations

import re


def extract_simple_type_name(qualified: str) -> str:
    """Extract the simple name from a qualified type string.

    Strips namespace prefixes separated by "." or "::".

    Args:
        qualified: A potentially qualified type name
            (e.g. "java.util.List", "std::vector").

    Returns:
        The unqualified simple name (e.g. "List", "vector").
    """
    if "::" in qualified:
        return qualified.rsplit("::", 1)[-1]
    if "." in qualified:
        return qualified.rsplit(".", 1)[-1]
    return qualified


def strip_nullable(type_str: str) -> tuple[str, bool]:
    """Strip nullable wrappers from a type string.

    Handles: Optional[X], X?, ?X patterns.

    Args:
        type_str: The raw type string.

    Returns:
        A tuple of (inner_type, is_optional).
    """
    # Optional[X]
    match = re.match(r"^Optional\[(.+)\]$", type_str)
    if match:
        return match.group(1), True

    # Trailing ?
    if type_str.endswith("?"):
        return type_str[:-1], True

    # Leading ? (TypeScript)
    if type_str.startswith("?"):
        return type_str[1:], True

    return type_str, False


def extract_generic_type_args(type_str: str) -> list[str]:
    """Extract generic type arguments from a type string.

    Handles both square brackets (Python: Dict[str, int]) and angle
    brackets (Java/TS: Map<K, V>). Respects nested brackets.

    Args:
        type_str: The type string potentially containing generics.

    Returns:
        A list of type argument strings, or empty list if no generics.
    """
    # Find the opening bracket
    for open_char, close_char in [("[", "]"), ("<", ">")]:
        start = type_str.find(open_char)
        if start == -1:
            continue

        # Find the matching closing bracket
        end = _find_matching_close(type_str, start, open_char, close_char)
        if end == -1:
            continue

        inner = type_str[start + 1 : end]
        return _split_top_level(inner, open_char, close_char)

    return []


def _find_matching_close(
    text: str,
    start: int,
    open_char: str,
    close_char: str,
) -> int:
    """Find the matching closing bracket.

    Args:
        text: The full string.
        start: Index of the opening bracket.
        open_char: The opening bracket character.
        close_char: The closing bracket character.

    Returns:
        Index of the matching closing bracket, or -1.
    """
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return i
    return -1


def _split_top_level(
    inner: str,
    open_char: str,
    close_char: str,
) -> list[str]:
    """Split generic arguments at top-level commas only.

    Args:
        inner: The string inside the outermost brackets.
        open_char: The opening bracket character.
        close_char: The closing bracket character.

    Returns:
        List of trimmed argument strings.
    """
    parts: list[str] = []
    depth = 0
    current: list[str] = []

    for ch in inner:
        if ch in (open_char, "<", "["):
            depth += 1
            current.append(ch)
        elif ch in (close_char, ">", "]"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)

    remainder = "".join(current).strip()
    if remainder:
        parts.append(remainder)

    return parts
