"""Language-specific type extractor implementations.

Each function takes a type annotation string and returns a TypeInfo
describing its structure (base type, generics, nullability, array-ness).
"""

from __future__ import annotations

import re

from ai_codebase_intelligence._extraction.type_extractors.shared import (
    extract_generic_type_args,
    extract_simple_type_name,
    strip_nullable,
)
from ai_codebase_intelligence._extraction.type_extractors.type_info import TypeInfo

_PYTHON_ARRAY_TYPES = frozenset(
    {"list", "List", "Sequence", "Tuple", "tuple", "Set", "set", "frozenset"},
)
_TS_ARRAY_TYPES = frozenset({"Array"})
_JAVA_ARRAY_TYPES = frozenset({"List", "ArrayList", "LinkedList", "Set", "HashSet", "Collection"})
_RUST_ARRAY_TYPES = frozenset({"Vec", "VecDeque", "HashSet", "BTreeSet"})


def python_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a Python annotation string.

    Args:
        type_str: A Python type annotation string.

    Returns:
        Parsed TypeInfo.
    """
    # Handle Union[X, None] and X | None
    inner, optional = strip_nullable(type_str)

    # Handle pipe-union with None
    if not optional and "|" in type_str:
        parts = [p.strip() for p in type_str.split("|")]
        non_none = [p for p in parts if p != "None"]
        if len(non_none) < len(parts):
            optional = True
            inner = " | ".join(non_none) if len(non_none) > 1 else non_none[0]

    # Handle Union[X, None]
    if not optional and inner.startswith("Union["):
        args = extract_generic_type_args(inner)
        non_none = [a for a in args if a != "None"]
        if len(non_none) < len(args):
            optional = True
            inner = non_none[0] if len(non_none) == 1 else inner

    generic_args = extract_generic_type_args(inner)
    base = extract_simple_type_name(inner.split("[")[0].split("<")[0])
    is_array = base in _PYTHON_ARRAY_TYPES

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=optional,
        is_array=is_array,
        raw=type_str,
    )


def typescript_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a TypeScript annotation string.

    Args:
        type_str: A TypeScript type annotation string.

    Returns:
        Parsed TypeInfo.
    """
    inner, optional = strip_nullable(type_str)

    # Handle union with null/undefined
    if not optional and "|" in inner:
        parts = [p.strip() for p in inner.split("|")]
        non_null = [p for p in parts if p not in ("null", "undefined")]
        if len(non_null) < len(parts):
            optional = True
            inner = " | ".join(non_null) if len(non_null) > 1 else non_null[0]

    # Handle array suffix: number[]
    if inner.endswith("[]"):
        elem_type = inner[:-2]
        return TypeInfo(
            base="Array",
            generic_args=[elem_type],
            is_optional=optional,
            is_array=True,
            raw=type_str,
        )

    generic_args = extract_generic_type_args(inner)
    base = extract_simple_type_name(inner.split("<")[0].split("[")[0])
    is_array = base in _TS_ARRAY_TYPES

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=optional,
        is_array=is_array,
        raw=type_str,
    )


def swift_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a Swift type string.

    Args:
        type_str: A Swift type annotation string.

    Returns:
        Parsed TypeInfo.
    """
    inner, optional = strip_nullable(type_str)

    # [Type] -> Array<Type>
    if inner.startswith("[") and inner.endswith("]"):
        content = inner[1:-1]
        if ":" in content:
            # [Key: Value] -> Dictionary
            parts = [p.strip() for p in content.split(":", 1)]
            return TypeInfo(
                base="Dictionary",
                generic_args=parts,
                is_optional=optional,
                is_array=False,
                raw=type_str,
            )
        return TypeInfo(
            base="Array",
            generic_args=[content],
            is_optional=optional,
            is_array=True,
            raw=type_str,
        )

    generic_args = extract_generic_type_args(inner)
    base = extract_simple_type_name(inner.split("<")[0])
    is_array = base in ("Array",)

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=optional,
        is_array=is_array,
        raw=type_str,
    )


def go_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a Go type string.

    Args:
        type_str: A Go type string.

    Returns:
        Parsed TypeInfo.
    """
    optional = False

    # Pointer: *T
    if type_str.startswith("*"):
        inner = type_str[1:]
        optional = True
        base = extract_simple_type_name(inner)
        return TypeInfo(
            base=base,
            generic_args=[],
            is_optional=optional,
            is_array=False,
            raw=type_str,
        )

    # Slice: []T
    if type_str.startswith("[]"):
        elem = type_str[2:]
        base = extract_simple_type_name(elem)
        return TypeInfo(
            base=base,
            generic_args=[],
            is_optional=False,
            is_array=True,
            raw=type_str,
        )

    # Map: map[K]V
    match = re.match(r"^map\[(.+?)\](.+)$", type_str)
    if match:
        key_type = match.group(1)
        val_type = match.group(2)
        return TypeInfo(
            base="map",
            generic_args=[key_type, val_type],
            is_optional=False,
            is_array=False,
            raw=type_str,
        )

    base = extract_simple_type_name(type_str)
    return TypeInfo(
        base=base,
        generic_args=[],
        is_optional=False,
        is_array=False,
        raw=type_str,
    )


def rust_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a Rust type string.

    Args:
        type_str: A Rust type string.

    Returns:
        Parsed TypeInfo.
    """
    # Option<T> -> optional
    if type_str.startswith("Option<") and type_str.endswith(">"):
        inner = type_str[7:-1]
        base = extract_simple_type_name(inner)
        return TypeInfo(
            base=base,
            generic_args=[],
            is_optional=True,
            is_array=False,
            raw=type_str,
        )

    generic_args = extract_generic_type_args(type_str)
    base = extract_simple_type_name(type_str.split("<")[0])
    is_array = base in _RUST_ARRAY_TYPES

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=False,
        is_array=is_array,
        raw=type_str,
    )


def jvm_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a Java/Kotlin type string.

    Args:
        type_str: A JVM type annotation string.

    Returns:
        Parsed TypeInfo.
    """
    inner, optional = strip_nullable(type_str)

    generic_args = extract_generic_type_args(inner)
    raw_base = inner.split("<")[0].split("[")[0]
    base = extract_simple_type_name(raw_base)
    is_array = base in _JAVA_ARRAY_TYPES

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=optional,
        is_array=is_array,
        raw=type_str,
    )


def c_cpp_extractor(type_str: str) -> TypeInfo:
    """Extract type info from a C/C++ type string.

    Args:
        type_str: A C/C++ type string.

    Returns:
        Parsed TypeInfo.
    """
    inner = type_str

    # Pointer
    optional = inner.endswith("*")
    if optional:
        inner = inner.rstrip("* ")

    generic_args = extract_generic_type_args(inner)
    base = extract_simple_type_name(inner.split("<")[0])
    is_array = base in ("vector", "array", "list", "deque")

    return TypeInfo(
        base=base,
        generic_args=generic_args,
        is_optional=optional,
        is_array=is_array,
        raw=type_str,
    )
