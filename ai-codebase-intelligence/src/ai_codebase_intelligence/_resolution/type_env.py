"""Type environment for scope-aware type resolution.

Binds variable names to types within scope levels (function, class, file)
and resolves them respecting scope priority.
"""

from __future__ import annotations

from collections import defaultdict

VALID_SCOPES = ("function", "class", "file")
SCOPE_PRIORITY = {scope: i for i, scope in enumerate(VALID_SCOPES)}


class TypeEnvironment:
    """Scope-aware type binding and resolution.

    Binds names to types at three scope levels: function, class, file.
    Resolution returns the narrowest matching scope. Also resolves
    'self' to the innermost enclosing class at a given line.
    """

    def __init__(self) -> None:
        self._bindings: dict[
            str, dict[str, dict[str, str]]
        ] = defaultdict(lambda: defaultdict(dict))

    def bind(
        self, name: str, type_name: str, scope: str, file_path: str,
    ) -> None:
        """Bind a name to a type within a scope.

        Args:
            name: Variable/parameter name.
            type_name: The resolved type string.
            scope: One of 'function', 'class', 'file'.
            file_path: Source file where the binding occurs.

        Raises:
            ValueError: If scope is not one of the valid scope levels.
        """
        if scope not in VALID_SCOPES:
            msg = f"Invalid scope '{scope}'. Must be one of {VALID_SCOPES}"
            raise ValueError(msg)
        self._bindings[file_path][scope][name] = type_name

    def resolve_type(
        self, name: str, scope: str, file_path: str,
    ) -> str | None:
        """Resolve a name to its type at the given scope or narrower.

        Returns the binding at the requested scope. If not found at that
        exact scope, falls back to broader scopes (class -> file) but
        never narrows (file scope does not see function bindings).

        Args:
            name: Variable/parameter name.
            scope: The scope level to start resolution at.
            file_path: Source file for the lookup.

        Returns:
            Type string if found, None otherwise.
        """
        file_bindings = self._bindings.get(file_path, {})
        requested_priority = SCOPE_PRIORITY.get(scope, 0)

        # Check from the requested scope outward (broader).
        # function(0) sees function, class, file.
        # class(1) sees class, file.
        # file(2) sees file only.
        for s in VALID_SCOPES:
            if SCOPE_PRIORITY[s] < requested_priority:
                continue
            scope_bindings = file_bindings.get(s, {})
            if name in scope_bindings:
                return scope_bindings[name]

        return None

    def resolve_self(
        self,
        file_path: str,
        line: int,
        classes: dict[str, tuple[int, int]],
    ) -> str | None:
        """Resolve 'self' to the innermost enclosing class at a line.

        Args:
            file_path: Source file path (unused but kept for API consistency).
            line: 1-based line number.
            classes: Mapping of class_name -> (start_line, end_line).

        Returns:
            Class name if inside a class, None otherwise.
        """
        best: str | None = None
        best_span: int = float("inf")  # type: ignore[assignment]

        for cls_name, (start, end) in classes.items():
            if start <= line <= end:
                span = end - start
                if span < best_span:
                    best = cls_name
                    best_span = span

        return best

    def clear(self) -> None:
        """Remove all type bindings."""
        self._bindings.clear()
