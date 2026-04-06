"""Wiki document model and formatting helpers."""
from __future__ import annotations

from dataclasses import dataclass, field

from .graph_queries import DependencyEdge, ModuleNode, SymbolInfo


@dataclass
class WikiSection:
    """A section within a wiki document."""

    title: str
    content: str
    children: list[WikiSection] = field(default_factory=list)


@dataclass
class WikiDocument:
    """Top-level wiki document containing sections."""

    title: str
    sections: list[WikiSection] = field(default_factory=list)


def _format_module_tree(
    modules: list[ModuleNode], indent: int = 0,
) -> str:
    """Format a module tree as indented text.

    Args:
        modules: List of module nodes.
        indent: Current indentation level.

    Returns:
        Text representation of the tree.
    """
    lines: list[str] = []
    prefix = "  " * indent
    for mod in modules:
        lines.append(f"{prefix}- {mod.name}")
        if mod.children:
            lines.append(_format_module_tree(mod.children, indent + 1))
    return "\n".join(lines)


def _format_symbols(symbols: list[SymbolInfo]) -> str:
    """Format a list of symbols as human-readable text.

    Args:
        symbols: List of symbol info objects.

    Returns:
        Formatted text describing the symbols.
    """
    if not symbols:
        return "(no public symbols)"

    lines: list[str] = []
    for sym in symbols:
        visibility = "public" if sym.is_exported else "private"
        sig = f" — {sym.signature}" if sym.signature else ""
        lines.append(f"- [{visibility}] {sym.kind}: {sym.name}{sig}")
    return "\n".join(lines)


def _format_dependencies(deps: list[DependencyEdge]) -> str:
    """Format dependency edges as human-readable text.

    Args:
        deps: List of dependency edges.

    Returns:
        Formatted text describing the dependencies.
    """
    if not deps:
        return "(no external dependencies)"

    lines: list[str] = []
    for dep in deps:
        lines.append(
            f"- {dep.source_module} -> {dep.target_module} "
            f"[{dep.relationship_type} x{dep.count}]"
        )
    return "\n".join(lines)


def _count_modules(modules: list[ModuleNode]) -> int:
    """Recursively count all modules in a tree.

    Args:
        modules: List of module nodes.

    Returns:
        Total count of nodes including children.
    """
    total = 0
    for mod in modules:
        total += 1
        if mod.children:
            total += _count_modules(mod.children)
    return total
