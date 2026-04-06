"""Rust crate/super/self import resolver."""

from __future__ import annotations

from pathlib import PurePosixPath


class RustResolver:
    """Resolve Rust use-path imports (crate::, super::, self::).

    Args:
        suffix_index: Mapping from suffix keys to file path lists.
        crate_root: Root directory of the crate (e.g. "/src").
    """

    def __init__(
        self,
        suffix_index: dict[str, list[str]],
        crate_root: str = "",
    ) -> None:
        self._index = suffix_index
        self._crate_root = crate_root.rstrip("/")

    def resolve(self, import_spec: str, current_file: str) -> str | None:
        """Resolve a Rust use-path to a file path.

        Args:
            import_spec: Rust import path (e.g. "crate::handlers").
            current_file: Path of the file containing the use statement.

        Returns:
            Resolved file path or None if unresolvable.
        """
        if import_spec.startswith("crate::"):
            return self._resolve_crate(import_spec[7:])
        if import_spec.startswith("super::"):
            return self._resolve_super(import_spec[7:], current_file)
        if import_spec.startswith("self::"):
            return self._resolve_self(import_spec[6:], current_file)
        return None

    def _resolve_crate(self, remainder: str) -> str | None:
        """Resolve crate:: path from crate root."""
        segments = remainder.split("::")
        first = segments[0]

        # Try direct file: {crate_root}/{first}.rs
        candidate = f"{self._crate_root}/{first}.rs"
        if self._exists(candidate):
            return candidate

        # Try directory with mod.rs: {crate_root}/{first}/mod.rs
        mod_candidate = f"{self._crate_root}/{first}/mod.rs"
        if self._exists(mod_candidate):
            return mod_candidate

        return None

    def _resolve_super(self, remainder: str, current_file: str) -> str | None:
        """Resolve super:: path from parent of current file's directory."""
        current_dir = PurePosixPath(current_file).parent
        parent_dir = current_dir.parent
        first = remainder.split("::")[0]

        candidate = f"{parent_dir}/{first}.rs"
        if self._exists(candidate):
            return candidate

        return None

    def _resolve_self(self, remainder: str, current_file: str) -> str | None:
        """Resolve self:: path from current module directory."""
        current_dir = PurePosixPath(current_file).parent
        first = remainder.split("::")[0]

        candidate = f"{current_dir}/{first}.rs"
        if self._exists(candidate):
            return candidate

        return None

    def _exists(self, path: str) -> bool:
        """Check if a path exists in the suffix index values."""
        for paths in self._index.values():
            if path in paths:
                return True
        return False
