"""Tests for the AI context file generator."""

from __future__ import annotations

from ai_codebase_intelligence._tools.context_generator import (
    generate_agents_md,
    generate_claude_md,
)


class TestGenerateAgentsMd:
    """Tests for generate_agents_md."""

    def test_contains_repo_name(self) -> None:
        """AGENTS.md includes the repository name in the title."""
        result = generate_agents_md("my-project", 8)
        assert "my-project" in result

    def test_contains_tool_names(self) -> None:
        """AGENTS.md contains all tool names in the table."""
        result = generate_agents_md("test-repo", 8)
        assert "`analyze`" in result
        assert "`query`" in result
        assert "`context`" in result
        assert "`impact`" in result
        assert "`detect_changes`" in result
        assert "`cypher`" in result
        assert "`rename`" in result
        assert "`list_repos`" in result

    def test_contains_workflow_section(self) -> None:
        """AGENTS.md contains a workflow section."""
        result = generate_agents_md("test-repo", 8)
        assert "## Workflow" in result
        assert "analyze" in result
        assert "query" in result

    def test_contains_boundaries(self) -> None:
        """AGENTS.md contains the three-tier boundaries."""
        result = generate_agents_md("test-repo", 8)
        assert "### Always" in result
        assert "### When Appropriate" in result
        assert "### Never" in result

    def test_contains_self_review_checklist(self) -> None:
        """AGENTS.md contains the self-review checklist."""
        result = generate_agents_md("test-repo", 8)
        assert "## Self-Review Checklist" in result
        assert "- [ ]" in result

    def test_tool_count_caps_at_available(self) -> None:
        """Tool count is capped at the number of available tools."""
        result = generate_agents_md("test-repo", 100)
        assert "## Available Tools (8)" in result

    def test_tool_count_respects_lower_value(self) -> None:
        """Tool count below available only shows that many tools."""
        result = generate_agents_md("test-repo", 3)
        assert "## Available Tools (3)" in result
        # Should only include the first 3 tools
        assert "`analyze`" in result
        assert "`query`" in result
        assert "`context`" in result
        assert "`list_repos`" not in result


class TestGenerateClaudeMd:
    """Tests for generate_claude_md."""

    def test_contains_repo_name(self) -> None:
        """CLAUDE.md includes the repository name."""
        result = generate_claude_md("my-project")
        assert "my-project" in result

    def test_contains_workflow(self) -> None:
        """CLAUDE.md contains the workflow section."""
        result = generate_claude_md("test-repo")
        assert "## Workflow" in result

    def test_contains_quick_reference(self) -> None:
        """CLAUDE.md contains the quick reference section."""
        result = generate_claude_md("test-repo")
        assert "## Quick Reference" in result

    def test_contains_boundaries(self) -> None:
        """CLAUDE.md contains the boundaries section."""
        result = generate_claude_md("test-repo")
        assert "## Boundaries" in result

    def test_contains_self_review(self) -> None:
        """CLAUDE.md contains the self-review checklist."""
        result = generate_claude_md("test-repo")
        assert "## Self-Review Checklist" in result

    def test_mentions_mcp_tools(self) -> None:
        """CLAUDE.md references the MCP tool prefix."""
        result = generate_claude_md("test-repo")
        assert "ai_architect_codebase_" in result
