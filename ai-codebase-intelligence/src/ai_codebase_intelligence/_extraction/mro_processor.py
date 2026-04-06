"""Method Resolution Order (MRO) computation.

Implements C3 linearization for Python (multiple inheritance) and
simple DFS traversal for single-inheritance languages (Java, Swift,
TypeScript, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage

_C3_LANGUAGES = frozenset({SupportedLanguage.PYTHON})


@dataclass(frozen=True, slots=True)
class MROEntry:
    """A single entry in a computed MRO chain.

    Args:
        class_name: The name of the class.
        class_id: The identifier for the class (defaults to class_name).
        depth: The distance from the starting class (0 = self).
    """

    class_name: str
    class_id: str
    depth: int


def compute_mro(
    class_name: str,
    class_id: str,
    inheritance_graph: dict[str, list[str]],
    language: SupportedLanguage,
) -> list[MROEntry]:
    """Compute the method resolution order for a class.

    For Python, uses C3 linearization. For all other languages, uses
    a simple DFS traversal (single-inheritance assumption).

    Args:
        class_name: The starting class name.
        class_id: The starting class identifier.
        inheritance_graph: Mapping from class name to list of parent
            class names.
        language: The source language.

    Returns:
        Ordered list of MROEntry from self to most distant ancestor.
    """
    if language in _C3_LANGUAGES:
        return _c3_linearize(class_name, class_id, inheritance_graph)
    return _dfs_mro(class_name, class_id, inheritance_graph)


def _c3_linearize(
    class_name: str,
    class_id: str,
    graph: dict[str, list[str]],
) -> list[MROEntry]:
    """Compute C3 linearization for multiple-inheritance languages.

    Args:
        class_name: The starting class name.
        class_id: The starting class identifier.
        graph: Inheritance graph (class -> parents).

    Returns:
        C3-linearized MRO list.
    """
    cache: dict[str, list[str]] = {}
    order = _c3_compute(class_name, graph, cache)
    return [
        MROEntry(
            class_name=name,
            class_id=class_id if name == class_name else name,
            depth=i,
        )
        for i, name in enumerate(order)
    ]


def _c3_compute(
    cls: str,
    graph: dict[str, list[str]],
    cache: dict[str, list[str]],
) -> list[str]:
    """Recursive C3 merge step.

    Args:
        cls: Current class name.
        graph: Inheritance graph.
        cache: Memoization cache.

    Returns:
        Linearized list of class names.
    """
    if cls in cache:
        return cache[cls]

    parents = graph.get(cls, [])
    if not parents:
        cache[cls] = [cls]
        return [cls]

    parent_mros = [_c3_compute(p, graph, cache) for p in parents]
    merged = _c3_merge([cls], parent_mros + [list(parents)])
    cache[cls] = merged
    return merged


def _c3_merge(
    current: list[str],
    sequences: list[list[str]],
) -> list[str]:
    """Merge step of C3 linearization.

    Args:
        current: The result list built so far (starts with [cls]).
        sequences: The parent MROs plus the direct parents list.

    Returns:
        The merged linearization.
    """
    result = list(current)
    seqs = [list(s) for s in sequences if s]

    while seqs:
        candidate = None
        for seq in seqs:
            head = seq[0]
            in_tail = any(head in s[1:] for s in seqs)
            if not in_tail:
                candidate = head
                break

        if candidate is None:
            # Fallback: take the first head (inconsistent hierarchy)
            candidate = seqs[0][0]

        if candidate not in result:
            result.append(candidate)

        seqs = [
            [x for x in s if x != candidate]
            for s in seqs
        ]
        seqs = [s for s in seqs if s]

    return result


def _dfs_mro(
    class_name: str,
    class_id: str,
    graph: dict[str, list[str]],
) -> list[MROEntry]:
    """Simple DFS traversal for single-inheritance languages.

    Args:
        class_name: The starting class name.
        class_id: The starting class identifier.
        graph: Inheritance graph.

    Returns:
        DFS-ordered MRO list.
    """
    result: list[MROEntry] = []
    visited: set[str] = set()
    _dfs_visit(class_name, class_id, graph, 0, visited, result)
    return result


def _dfs_visit(
    cls: str,
    root_id: str,
    graph: dict[str, list[str]],
    depth: int,
    visited: set[str],
    out: list[MROEntry],
) -> None:
    """DFS visit step.

    Args:
        cls: Current class name.
        root_id: The root class identifier (for the starting entry).
        graph: Inheritance graph.
        depth: Current depth.
        visited: Already-visited set to prevent cycles.
        out: Accumulator list.
    """
    if cls in visited:
        return
    visited.add(cls)

    out.append(
        MROEntry(
            class_name=cls,
            class_id=root_id if depth == 0 else cls,
            depth=depth,
        )
    )

    for parent in graph.get(cls, []):
        _dfs_visit(parent, root_id, graph, depth + 1, visited, out)
