"""Wiki generation MCP tool — expose existing WikiGenerator via MCP."""

from __future__ import annotations

import json
import os

from .._app import mcp
from ..mcp.local.local_backend import LocalBackend

_backend: LocalBackend | None = None


def _get_backend() -> LocalBackend:
    global _backend
    if _backend is None:
        _backend = LocalBackend()
    return _backend


@mcp.tool(
    name="ai_architect_codebase_wiki",
    description=(
        "Generate LLM-powered documentation wiki for an indexed repository. "
        "Creates module-by-module docs with call graphs, sequence diagrams, "
        "and inter-module dependency maps. Requires an LLM API key."
    ),
)
async def tool_wiki(
    repo: str = "",
    model: str = "",
    force: bool = False,
) -> str:
    """Generate or update repository wiki documentation.

    Args:
        repo: Repository name. Omit if only one indexed.
        model: LLM model to use (default: from config/env).
        force: Regenerate even if wiki is up-to-date.
    """
    backend = _get_backend()
    await backend.init()
    repo_handle = await backend.resolve_repo(repo or None)

    from ..core.wiki.generator import WikiGenerator
    from ..core.wiki.llm_client import resolve_llm_config

    llm_config = resolve_llm_config({"model": model} if model else None)
    wiki_gen = WikiGenerator(
        repo_path=repo_handle["repoPath"],
        storage_path=repo_handle["storagePath"],
        kuzu_path=repo_handle["kuzuPath"],
        llm_config=llm_config,
        options={"force": force},
    )

    result = wiki_gen.run()
    wiki_path = os.path.join(repo_handle["storagePath"], "wiki")

    output = {
        "pagesGenerated": result.get("pagesGenerated", 0),
        "mode": result.get("mode", "unknown"),
        "wikiPath": wiki_path,
        "failedModules": result.get("failedModules", []),
    }

    hint = "\n\n---\n**Next:** Browse the wiki at the wikiPath above."
    return json.dumps(output, indent=2) + hint
