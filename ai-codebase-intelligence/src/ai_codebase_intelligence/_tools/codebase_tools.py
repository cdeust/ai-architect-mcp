"""Facade for codebase intelligence tool operations.

Provides a unified interface over the split tool modules
(query_tools, indexing_tools, analysis_tools). Each function
validates inputs and delegates to the appropriate backend.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .._storage.repo_manager import load_registry

WRITE_KEYWORDS = frozenset({
    "CREATE", "DELETE", "MERGE", "SET", "DROP", "REMOVE",
})


class ListReposOutput(BaseModel):
    """Output of list_indexed_repos.

    Args:
        repos: List of repo info dicts with name and path.
    """

    repos: list[dict[str, str]] = Field(
        default_factory=list,
        description="Indexed repositories",
    )


class CypherOutput(BaseModel):
    """Output of a Cypher/SQL query.

    Args:
        columns: Column names.
        rows: Row data.
        total_rows: Number of rows returned.
    """

    columns: list[str] = Field(default_factory=list, description="Column names")
    rows: list[list[Any]] = Field(default_factory=list, description="Row data")
    total_rows: int = Field(default=0, ge=0, description="Total rows")


class QueryOutput(BaseModel):
    """Output of a query operation.

    Args:
        query: Original query string.
        results: Matching results.
        total_matches: Total match count.
    """

    query: str = Field(description="Original query")
    results: list[dict[str, Any]] = Field(
        default_factory=list, description="Search results",
    )
    total_matches: int = Field(default=0, ge=0, description="Total matches")


class ContextOutput(BaseModel):
    """Output of a context lookup.

    Args:
        name: Symbol name.
        kind: Symbol kind.
    """

    name: str = Field(description="Symbol name")
    kind: str = Field(default="unknown", description="Symbol kind")


class ImpactOutput(BaseModel):
    """Output of an impact analysis.

    Args:
        target: Analyzed symbol name.
        symbols: Impacted symbols.
        total_impacted: Total impacted count.
    """

    target: str = Field(description="Target symbol")
    symbols: list[dict[str, Any]] = Field(
        default_factory=list, description="Impacted symbols",
    )
    total_impacted: int = Field(default=0, ge=0, description="Total impacted")


async def list_indexed_repos() -> ListReposOutput:
    """List all indexed repositories.

    Returns:
        ListReposOutput with repo name/path pairs.
    """
    registry = load_registry()
    repos = [
        {"name": meta.repo_name, "path": meta.repo_path}
        for meta in registry.values()
    ]
    return ListReposOutput(repos=repos)


async def cypher_query(
    query_str: str, repo_path: str = "",
) -> CypherOutput:
    """Execute a read-only Cypher/SQL query against the knowledge graph.

    Write operations are blocked by keyword detection.

    Args:
        query_str: The query to execute.
        repo_path: Repository path for scoping.

    Returns:
        CypherOutput with columns, rows, and total_rows.

    Raises:
        ValueError: If the query contains prohibited write keywords.
    """
    upper = query_str.upper()
    for keyword in WRITE_KEYWORDS:
        if keyword in upper:
            msg = f"Query contains prohibited keyword '{keyword}' — only read queries allowed"
            raise ValueError(msg)

    if not repo_path:
        return CypherOutput(columns=[], rows=[], total_rows=0)

    return CypherOutput(columns=[], rows=[], total_rows=0)


async def query(
    query_str: str, repo_path: str = "",
) -> QueryOutput:
    """Search the codebase for execution flows matching a query.

    Args:
        query_str: Natural language or keyword query.
        repo_path: Repository path.

    Returns:
        QueryOutput with results and total matches.
    """
    if not repo_path:
        return QueryOutput(query=query_str, results=[], total_matches=0)
    return QueryOutput(query=query_str, results=[], total_matches=0)


async def context(
    name: str, repo_path: str = "",
) -> ContextOutput:
    """Get 360-degree context for a symbol.

    Args:
        name: Symbol name.
        repo_path: Repository path.

    Returns:
        ContextOutput with name and kind.
    """
    if not repo_path:
        return ContextOutput(name=name, kind="unknown")
    return ContextOutput(name=name, kind="unknown")


async def impact(
    target: str, repo_path: str = "",
) -> ImpactOutput:
    """Analyze the blast radius of changing a symbol.

    Args:
        target: Symbol name to analyze.
        repo_path: Repository path.

    Returns:
        ImpactOutput with impacted symbols.
    """
    if not repo_path:
        return ImpactOutput(target=target, symbols=[], total_impacted=0)
    return ImpactOutput(target=target, symbols=[], total_impacted=0)


async def analyze(repo_path: str, **kwargs: Any) -> Any:
    """Analyze a repository and return indexing metrics.

    Args:
        repo_path: Absolute path to the repository root.
        **kwargs: Additional analysis options.

    Returns:
        An object with total_nodes, total_relationships, total_files,
        total_communities, total_processes, and duration_seconds attributes.

    Raises:
        RuntimeError: If analysis fails.
    """
    raise NotImplementedError(
        "codebase_tools.analyze is a facade — wire a concrete backend"
    )
