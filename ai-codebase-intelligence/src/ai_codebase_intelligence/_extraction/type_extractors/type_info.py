"""TypeInfo data model for parsed type annotations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TypeInfo:
    """Parsed type annotation structure.

    Args:
        base: The base type name (unqualified).
        generic_args: Generic type arguments, if any.
        is_optional: Whether the type is nullable/optional.
        is_array: Whether the type represents a collection/array.
        raw: The original type string.
    """

    base: str
    generic_args: list[str] = field(default_factory=list)
    is_optional: bool = False
    is_array: bool = False
    raw: str = ""
