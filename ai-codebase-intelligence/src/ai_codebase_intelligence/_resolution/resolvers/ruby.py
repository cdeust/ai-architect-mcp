"""Ruby require/require_relative resolver."""

from __future__ import annotations

from pathlib import PurePosixPath

_STDLIB_NAMES: frozenset[str] = frozenset({
    "json",
    "yaml",
    "net/http",
    "fileutils",
    "csv",
    "open-uri",
    "set",
    "ostruct",
    "pathname",
    "tempfile",
    "digest",
    "base64",
    "erb",
    "logger",
    "optparse",
    "socket",
    "stringio",
    "time",
    "uri",
    "benchmark",
    "bigdecimal",
    "cgi",
    "date",
    "English",
    "find",
    "io/console",
    "irb",
    "minitest",
    "monitor",
    "mutex_m",
    "net/ftp",
    "net/pop",
    "net/smtp",
    "open3",
    "pp",
    "pstore",
    "readline",
    "resolv",
    "securerandom",
    "shellwords",
    "singleton",
    "syslog",
    "timeout",
    "tmpdir",
    "tsort",
    "webrick",
    "zlib",
})


class RubyResolver:
    """Resolve Ruby require and require_relative imports.

    Args:
        suffix_index: Mapping from suffix keys to file path lists.
    """

    def __init__(self, suffix_index: dict[str, list[str]]) -> None:
        self._index = suffix_index

    def resolve(self, import_spec: str, current_file: str) -> str | None:
        """Resolve a Ruby import to a file path.

        Args:
            import_spec: The require string.
            current_file: Path of the file containing the require.

        Returns:
            Resolved file path or None if stdlib/unresolvable.
        """
        if import_spec.startswith("./"):
            return self._resolve_relative(import_spec, current_file)

        if import_spec in _STDLIB_NAMES:
            return None

        return self._resolve_absolute(import_spec)

    def _resolve_relative(self, spec: str, current_file: str) -> str | None:
        """Resolve require_relative (starts with ./)."""
        current_dir = str(PurePosixPath(current_file).parent)
        bare = spec[2:]
        candidate = f"{current_dir}/{bare}.rb"

        # Check if this exact path exists in the index values
        for paths in self._index.values():
            if candidate in paths:
                return candidate

        # Try suffix-index lookup
        parent = PurePosixPath(current_dir).name
        key = f"{parent}/{bare}"
        matches = self._index.get(key)
        if matches:
            return matches[0]

        return self._index.get(bare, [None])[0]

    def _resolve_absolute(self, spec: str) -> str | None:
        """Resolve absolute require via suffix index."""
        matches = self._index.get(spec)
        if matches:
            return matches[0]
        return None
