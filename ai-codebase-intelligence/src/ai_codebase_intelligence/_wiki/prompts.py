"""Prompt templates for LLM-driven wiki generation."""
from __future__ import annotations


def format_structure_prompt(module_tree_text: str) -> str:
    """Format a prompt for generating wiki structure from a module tree.

    Args:
        module_tree_text: Text representation of the module tree.

    Returns:
        Formatted prompt string.
    """
    return (
        "Given the following module tree, generate a structured wiki outline.\n\n"
        f"Module tree:\n{module_tree_text}\n\n"
        "Organize the documentation into logical sections with clear hierarchy."
    )


def format_detail_prompt(
    module_name: str,
    file_path: str,
    symbols_text: str,
    dependencies_text: str,
) -> str:
    """Format a prompt for generating detailed module documentation.

    Args:
        module_name: Name of the module.
        file_path: Path to the module file.
        symbols_text: Formatted symbols listing.
        dependencies_text: Formatted dependencies listing.

    Returns:
        Formatted prompt string.
    """
    return (
        f"Write detailed documentation for the module **{module_name}** "
        f"located at `{file_path}`.\n\n"
        f"Symbols:\n{symbols_text}\n\n"
        f"Dependencies:\n{dependencies_text}\n\n"
        "Include purpose, key functions, and usage examples."
    )


def format_synthesis_prompt(
    group_name: str, child_docs: str,
) -> str:
    """Format a prompt for synthesizing child documentation into a parent section.

    Args:
        group_name: Name of the parent group.
        child_docs: Concatenated documentation from child sections.

    Returns:
        Formatted prompt string.
    """
    return (
        f"Synthesize documentation for the **{group_name}** group "
        f"from the following sub-sections:\n\n{child_docs}\n\n"
        "Write a cohesive summary that explains how these pieces fit together."
    )


def format_overview_prompt(
    project_name: str,
    repo_path: str,
    section_outline: str,
    module_count: int,
    symbol_count: int,
    languages: str,
) -> str:
    """Format a prompt for generating the project overview.

    Args:
        project_name: Name of the project.
        repo_path: Path to the repository.
        section_outline: Outline of all sections.
        module_count: Total number of modules.
        symbol_count: Total number of symbols.
        languages: Comma-separated language list.

    Returns:
        Formatted prompt string.
    """
    return (
        f"Write an overview for the **{project_name}** project "
        f"at `{repo_path}`.\n\n"
        f"Sections:\n{section_outline}\n\n"
        f"Statistics: {module_count} modules, {symbol_count} symbols. "
        f"Languages: {languages}.\n\n"
        "Include architecture highlights and getting-started guidance."
    )
