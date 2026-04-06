"""Wiki generation orchestrator — async pipeline."""
from __future__ import annotations

import os
from typing import Callable, Awaitable

from .generator import WikiDocument, WikiSection, _format_module_tree, _count_modules
from .graph_queries import GraphStorage, get_module_tree
from .prompts import format_overview_prompt, format_structure_prompt


async def generate_wiki(
    repo_path: str,
    storage: GraphStorage,
    llm_call: Callable[[str], Awaitable[str]],
    project_name: str = "",
) -> WikiDocument:
    """Generate a complete wiki document for a repository.

    Args:
        repo_path: Path to the repository root.
        storage: Graph storage backend with parsed codebase data.
        llm_call: Async function that sends a prompt and returns LLM text.
        project_name: Optional project name override.

    Returns:
        A WikiDocument with all generated sections.
    """
    name = project_name or os.path.basename(repo_path.rstrip("/"))

    modules = await get_module_tree(storage)
    tree_text = _format_module_tree(modules) if modules else "(empty repository)"
    module_count = _count_modules(modules)

    structure_prompt = format_structure_prompt(tree_text)
    structure_content = await llm_call(structure_prompt)

    overview_prompt = format_overview_prompt(
        name, repo_path, tree_text, module_count, 0, "",
    )
    overview_content = await llm_call(overview_prompt)

    sections = [
        WikiSection(title="Overview", content=overview_content),
    ]

    if structure_content:
        sections.append(
            WikiSection(title="Structure", content=structure_content),
        )

    return WikiDocument(title=name, sections=sections)
