"""Go import resolver with module prefix stripping."""

from __future__ import annotations


class GoResolver:
    """Resolve Go imports by stripping the module prefix.

    Args:
        suffix_index: Mapping from suffix keys to file path lists.
        module_prefix: Go module path prefix (e.g. "github.com/org/repo").
    """

    def __init__(
        self,
        suffix_index: dict[str, list[str]],
        module_prefix: str = "",
    ) -> None:
        self._index = suffix_index
        self._module_prefix = module_prefix

    def resolve(self, import_spec: str, current_file: str) -> str | None:
        """Resolve a Go import path to a file path.

        Args:
            import_spec: Go import path.
            current_file: Path of the importing file (unused for Go).

        Returns:
            Resolved file path or None if external/unresolvable.
        """
        if self._module_prefix:
            if not import_spec.startswith(self._module_prefix):
                return None
            local_path = import_spec[len(self._module_prefix) :].lstrip("/")
        else:
            local_path = import_spec

        return self._lookup(local_path)

    def _lookup(self, key: str) -> str | None:
        """Look up a key in the suffix index."""
        matches = self._index.get(key)
        if matches:
            return matches[0]
        return None
