"""Port interfaces for codebase intelligence infrastructure.

Defines abstract base classes for all external system interactions.
Ingestion, search, and tool logic depend only on these interfaces —
never on concrete adapters (SQLite, tree-sitter, git).

Concrete adapters implement these ports and are injected at the
composition root. Tests inject in-memory doubles.

OBSERVATION: gitnexus coupled graph DB, search, and parsing into
  monolithic modules. Every KuzuDB API change broke the pipeline.
PROBLEM: Tight coupling to KuzuDB caused crashes on extension loading,
  schema migration, and stale directory state across 5+ sessions.
SOLUTION: Hexagonal architecture with port interfaces. Storage,
  search, and parsing are swappable without touching business logic.
JUSTIFICATION: ai-architect MCP uses identical pattern with 8 ports.
  Same team, same project — architectural consistency is mandatory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .._models.graph_types import GraphNode, GraphRelationship
from .._models.graph_models import SearchResult

__all__ = [
    "GraphStoragePort",
    "SearchPort",
    "ParserPort",
]


class GraphStoragePort(ABC):
    """Port for graph persistence and retrieval.

    Stores nodes and relationships. Loads them back into memory.
    Concrete adapters: SQLiteStore (production), InMemoryStore (test).
    """

    @abstractmethod
    def initialize(self) -> None:
        """Create database schema if it doesn't exist."""
        ...

    @abstractmethod
    def store_nodes(self, nodes: list[GraphNode]) -> int:
        """Bulk insert nodes.

        Args:
            nodes: Node models to persist.

        Returns:
            Number of nodes successfully stored.
        """
        ...

    @abstractmethod
    def store_relationships(self, relationships: list[GraphRelationship]) -> int:
        """Bulk insert relationships.

        Args:
            relationships: Relationship models to persist.

        Returns:
            Number of relationships successfully stored.
        """
        ...

    @abstractmethod
    def load_all_nodes(self) -> list[GraphNode]:
        """Load all nodes from storage.

        Returns:
            Complete list of persisted nodes.
        """
        ...

    @abstractmethod
    def load_all_relationships(self) -> list[GraphRelationship]:
        """Load all relationships from storage.

        Returns:
            Complete list of persisted relationships.
        """
        ...

    @abstractmethod
    def get_stats(self) -> dict[str, int]:
        """Get node and relationship counts.

        Returns:
            Dict with 'nodes' and 'edges' counts.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Release database resources."""
        ...


class SearchPort(ABC):
    """Port for full-text search operations.

    Provides keyword search across node names and content.
    Concrete adapters: FTS5Search (production), SimpleSearch (test).
    """

    @abstractmethod
    def index_nodes(self, nodes: list[GraphNode]) -> int:
        """Build or rebuild the search index from nodes.

        Args:
            nodes: Nodes to index.

        Returns:
            Number of nodes indexed.
        """
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Execute a full-text search.

        Args:
            query: Search query string.
            limit: Maximum results.

        Returns:
            Ranked list of search results.
        """
        ...


class ParserPort(ABC):
    """Port for source code parsing.

    Extracts symbols (functions, classes, etc.) from source files.
    Concrete adapter: TreeSitterParser (production).
    """

    @abstractmethod
    def parse_file(
        self, file_path: str, content: str, language: str
    ) -> list[GraphNode]:
        """Parse a single source file and extract symbol nodes.

        Args:
            file_path: Relative path to the source file.
            content: File content as string.
            language: Programming language identifier.

        Returns:
            List of extracted symbol nodes.
        """
        ...

    @abstractmethod
    def extract_calls(
        self, file_path: str, content: str, language: str
    ) -> list[GraphRelationship]:
        """Extract function call relationships from a source file.

        Args:
            file_path: Relative path to the source file.
            content: File content as string.
            language: Programming language identifier.

        Returns:
            List of CALLS relationships.
        """
        ...

    @abstractmethod
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported for parsing.

        Args:
            language: Language identifier.

        Returns:
            True if the language has a parser available.
        """
        ...
