"""Composition root — factory wiring all adapters to port interfaces.

The ONE place where concrete adapter types are instantiated.
All other code depends only on port interfaces, never on concrete adapters.

OBSERVATION: gitnexus instantiates KuzuDB, FTS, and tree-sitter directly
  in 8+ modules. Swapping storage requires editing every module.
PROBLEM: When KuzuDB broke (v0.11 API changes, extension failures),
  fixes required changes across kuzu-adapter, bm25-index, local-backend,
  all tool implementations, and the pipeline orchestrator.
SOLUTION: Single composition root creates all adapters. Tool code,
  pipeline, and search depend only on GraphStoragePort / SearchPort /
  ParserPort. Swapping SQLite→DuckDB→KuzuDB means changing ONE file.
"""

from __future__ import annotations

import os

from .ports import GraphStoragePort, SearchPort, ParserPort
from .._config.loader import get_config
from .._config.models import CodeIntelligenceConfig


class CompositionRoot:
    """Factory for creating adapter instances.

    Wires concrete adapters to their port interfaces. This is the
    only module that imports concrete adapter classes.

    Args:
        repo_path: Absolute path to the repository being indexed.
        config: Optional config override. Uses global config if None.
    """

    def __init__(
        self,
        repo_path: str = "",
        config: CodeIntelligenceConfig | None = None,
    ) -> None:
        self._repo_path = repo_path
        self._config = config or get_config()

    @property
    def config(self) -> CodeIntelligenceConfig:
        """The active configuration."""
        return self._config

    @property
    def storage_path(self) -> str:
        """Absolute path to the .gitnexus storage directory."""
        return os.path.join(self._repo_path, self._config.storage.storage_dir)

    @property
    def db_path(self) -> str:
        """Absolute path to the SQLite database file."""
        return os.path.join(self.storage_path, self._config.storage.db_filename)

    def create_graph_storage(self) -> GraphStoragePort:
        """Create the graph persistence adapter.

        Production: SQLiteStore backed by a single .db file.

        Returns:
            GraphStoragePort implementation.
        """
        from .sqlite_adapter import SQLiteGraphStorage

        return SQLiteGraphStorage(db_path=self.db_path)

    def create_search(self) -> SearchPort:
        """Create the full-text search adapter.

        Production: FTS5 backed by the same SQLite database.

        Returns:
            SearchPort implementation.
        """
        from .fts5_adapter import FTS5Search

        return FTS5Search(db_path=self.db_path)

    def create_parser(self) -> ParserPort:
        """Create the source code parser adapter.

        Production: tree-sitter 0.23 with per-language grammar packages.

        Returns:
            ParserPort implementation.
        """
        from .tree_sitter_adapter import TreeSitterParser

        return TreeSitterParser(config=self._config.indexing)

    def create_test_storage(self) -> GraphStoragePort:
        """Create an in-memory storage adapter for testing.

        Returns:
            GraphStoragePort backed by Python dicts (no I/O).
        """
        from .in_memory_adapter import InMemoryGraphStorage

        return InMemoryGraphStorage()
