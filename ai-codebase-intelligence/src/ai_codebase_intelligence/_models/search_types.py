"""Search type models — BM25, hybrid search, and request types."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SearchResultKind(str, Enum):
    """Kind of search result."""

    SYMBOL = "symbol"
    PROCESS = "process"
    FILE = "file"


class BM25Result(BaseModel):
    """A single BM25 full-text search result.

    Args:
        node_id: ID of the matched node.
        score: BM25 relevance score.
        matched_field: Which field matched (name, content, etc.).
        snippet: Matching text snippet.
        table_name: Node type table (Function, Class, etc.).
    """

    node_id: str = Field(description="Matched node ID")
    score: float = Field(default=0.0, description="BM25 relevance score")
    matched_field: str = Field(default="", description="Which field matched")
    snippet: str = Field(default="", description="Matching text snippet")
    table_name: str = Field(default="", description="Node type table")


class HybridSearchResult(BaseModel):
    """A hybrid search result combining BM25 + process tracing.

    Args:
        node_id: ID of the matched node.
        name: Symbol name.
        kind: Result kind (symbol, process, file).
        file_path: File containing the symbol.
        rrf_score: Reciprocal Rank Fusion score.
        bm25_score: Raw BM25 score.
        process_score: Score from process participation.
        processes: Process labels this symbol participates in.
        community: Community label.
    """

    node_id: str = Field(description="Matched node ID")
    name: str = Field(default="", description="Symbol name")
    kind: SearchResultKind = Field(description="Result kind")
    file_path: str = Field(default="", description="File path")
    rrf_score: float = Field(default=0.0, description="RRF score")
    bm25_score: float = Field(default=0.0, description="BM25 score")
    process_score: float = Field(default=0.0, description="Process participation score")
    processes: list[str] = Field(default_factory=list, description="Process labels")
    community: str = Field(default="", description="Community label")
    cohesion_score: float = Field(default=0.0, description="Community cohesion score")


class SearchRequest(BaseModel):
    """A search request with parameters.

    Args:
        query: Search query string.
        limit: Maximum results (1-100).
        include_processes: Include process context.
        language_filter: Filter by language.
    """

    query: str = Field(description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")
    include_processes: bool = Field(default=True, description="Include process context")
    language_filter: str | None = Field(default=None, description="Language filter")
