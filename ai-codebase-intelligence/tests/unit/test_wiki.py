"""Tests for wiki generation modules (Epic 17)."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._wiki.generator import (
    WikiDocument,
    WikiSection,
    _format_module_tree,
    _format_symbols,
    _format_dependencies,
    _count_modules,
)
from ai_codebase_intelligence._wiki.wiki_orchestrator import generate_wiki
from ai_codebase_intelligence._wiki.graph_queries import (
    ModuleNode,
    SymbolInfo,
    DependencyEdge,
    get_module_tree,
    get_module_symbols,
    get_module_dependencies,
)
from ai_codebase_intelligence._wiki.html_viewer import (
    generate_html,
    _section_id,
)
from ai_codebase_intelligence._wiki.prompts import (
    format_structure_prompt,
    format_detail_prompt,
    format_synthesis_prompt,
    format_overview_prompt,
)
from ai_codebase_intelligence._augmentation.engine import (
    GrepResult,
    GlobResult,
    EnrichedGrepResult,
    EnrichedGlobResult,
    augment_grep_results,
    augment_glob_results,
    MAX_ENRICHMENT_BATCH,
)


# ---- Fixtures ----


class MockGraphStorage:
    """Mock graph storage for testing."""

    def __init__(self, rows: list[dict[str, object]] | None = None) -> None:
        self._rows = rows or []
        self.queries: list[str] = []

    async def initialize(self) -> None:
        pass

    async def store_nodes(self, nodes: list) -> int:
        return 0

    async def store_relationships(self, relationships: list) -> int:
        return 0

    async def query_cypher(
        self, query: str, params: dict[str, object] | None = None
    ) -> list[dict[str, object]]:
        self.queries.append(query)
        return self._rows

    async def get_node(self, node_id: str) -> None:
        return None

    async def get_neighbors(
        self, node_id: str, relationship_type: str | None = None,
        direction: str = "both",
    ) -> list:
        return []

    async def clear(self) -> None:
        pass

    async def node_count(self) -> int:
        return 0

    async def relationship_count(self) -> int:
        return 0


# ---- WikiSection / WikiDocument ----


class TestWikiDataclasses:
    """Tests for WikiSection and WikiDocument creation."""

    def test_section_defaults(self) -> None:
        section = WikiSection(title="Test", content="Body")
        assert section.title == "Test"
        assert section.content == "Body"
        assert section.children == []

    def test_section_with_children(self) -> None:
        child = WikiSection(title="Child", content="Child body")
        parent = WikiSection(
            title="Parent", content="Parent body", children=[child]
        )
        assert len(parent.children) == 1
        assert parent.children[0].title == "Child"

    def test_document_defaults(self) -> None:
        doc = WikiDocument(title="My Project")
        assert doc.title == "My Project"
        assert doc.sections == []

    def test_document_with_sections(self) -> None:
        s1 = WikiSection(title="Intro", content="Hello")
        s2 = WikiSection(title="API", content="Endpoints")
        doc = WikiDocument(title="Proj", sections=[s1, s2])
        assert len(doc.sections) == 2


# ---- HTML Generation ----


class TestHTMLGeneration:
    """Tests for HTML wiki viewer."""

    def test_generate_html_basic(self) -> None:
        doc = WikiDocument(
            title="Test Project",
            sections=[
                WikiSection(title="Overview", content="Hello world"),
            ],
        )
        html_str = generate_html(doc)
        assert "<!DOCTYPE html>" in html_str
        assert "Test Project" in html_str
        assert "Overview" in html_str
        assert "Hello world" in html_str

    def test_generate_html_escapes_special_chars(self) -> None:
        doc = WikiDocument(
            title="<script>alert('xss')</script>",
            sections=[],
        )
        html_str = generate_html(doc)
        assert "<script>alert" not in html_str
        assert "&lt;script&gt;" in html_str

    def test_generate_html_nested_sections(self) -> None:
        child = WikiSection(title="SubSection", content="Details")
        parent = WikiSection(
            title="Main", content="Intro", children=[child]
        )
        doc = WikiDocument(title="Proj", sections=[parent])
        html_str = generate_html(doc)
        assert "SubSection" in html_str
        assert "Details" in html_str

    def test_section_id_generation(self) -> None:
        assert _section_id("Hello World") == "hello-world"
        assert _section_id("API/Routes") == "api-routes"

    def test_generate_html_has_buttons(self) -> None:
        doc = WikiDocument(title="T", sections=[])
        html_str = generate_html(doc)
        assert "Expand All" in html_str
        assert "Collapse All" in html_str

    def test_generate_html_has_css(self) -> None:
        doc = WikiDocument(title="T", sections=[])
        html_str = generate_html(doc)
        assert "<style>" in html_str
        assert "font-family" in html_str


# ---- Graph Queries (mock storage) ----


class TestGraphQueries:
    """Tests for wiki graph query functions."""

    @pytest.mark.asyncio
    async def test_get_module_tree_empty(self) -> None:
        storage = MockGraphStorage(rows=[])
        result = await get_module_tree(storage)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_module_tree_single(self) -> None:
        storage = MockGraphStorage(rows=[
            {
                "parent_id": "folder:src",
                "parent_name": "src",
                "child_id": "file:main.py",
                "child_name": "main.py",
                "file_path": "/repo/src/main.py",
            }
        ])
        result = await get_module_tree(storage)
        assert len(result) == 1
        assert result[0].name == "src"
        assert len(result[0].children) == 1
        assert result[0].children[0].name == "main.py"

    @pytest.mark.asyncio
    async def test_get_module_symbols_empty(self) -> None:
        storage = MockGraphStorage(rows=[])
        result = await get_module_symbols(storage, "mod:1")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_module_symbols_with_data(self) -> None:
        storage = MockGraphStorage(rows=[
            {
                "node_id": "sym:1",
                "name": "my_func",
                "kind": "Function",
                "signature": "def my_func() -> None",
                "docstring": "A function.",
                "start_line": 10,
                "end_line": 20,
                "is_exported": True,
            }
        ])
        result = await get_module_symbols(storage, "mod:1")
        assert len(result) == 1
        assert result[0].name == "my_func"
        assert result[0].kind == "Function"
        assert result[0].is_exported is True

    @pytest.mark.asyncio
    async def test_get_module_dependencies_empty(self) -> None:
        storage = MockGraphStorage(rows=[])
        result = await get_module_dependencies(storage, "mod:1")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_module_dependencies_with_data(self) -> None:
        storage = MockGraphStorage(rows=[
            {
                "source_module": "mod:1",
                "target_module": "mod:2",
                "relationship_type": "IMPORTS",
                "cnt": 3,
            }
        ])
        result = await get_module_dependencies(storage, "mod:1")
        assert len(result) == 1
        assert result[0].target_module == "mod:2"
        assert result[0].count == 3


# ---- Prompt Formatting ----


class TestPromptFormatting:
    """Tests for prompt template formatting."""

    def test_structure_prompt(self) -> None:
        result = format_structure_prompt("- src\n  - main.py")
        assert "- src" in result
        assert "module tree" in result.lower() or "Module tree" in result

    def test_detail_prompt(self) -> None:
        result = format_detail_prompt(
            "my_module", "/path/to/mod.py", "- func_a", "- imports mod_b"
        )
        assert "my_module" in result
        assert "func_a" in result

    def test_synthesis_prompt(self) -> None:
        result = format_synthesis_prompt("Core", "### Sub1\nContent")
        assert "Core" in result
        assert "Sub1" in result

    def test_overview_prompt(self) -> None:
        result = format_overview_prompt(
            "MyProject", "/path", "- Core\n- API", 10, 50, "Python, TypeScript"
        )
        assert "MyProject" in result
        assert "10" in result


# ---- Generator Helpers ----


class TestGeneratorHelpers:
    """Tests for generator helper functions."""

    def test_format_module_tree(self) -> None:
        modules = [
            ModuleNode(
                node_id="f:1",
                name="src",
                file_path="",
                children=[
                    ModuleNode(
                        node_id="f:2",
                        name="main.py",
                        file_path="/repo/main.py",
                    )
                ],
            )
        ]
        text = _format_module_tree(modules)
        assert "src" in text
        assert "main.py" in text

    def test_format_symbols_empty(self) -> None:
        assert "no public symbols" in _format_symbols([])

    def test_format_symbols_with_data(self) -> None:
        symbols = [
            SymbolInfo(
                node_id="s:1", name="foo", kind="Function",
                signature="def foo()", is_exported=True,
            )
        ]
        text = _format_symbols(symbols)
        assert "foo" in text
        assert "public" in text

    def test_format_dependencies_empty(self) -> None:
        assert "no external" in _format_dependencies([])

    def test_format_dependencies_with_data(self) -> None:
        deps = [
            DependencyEdge(
                source_module="a", target_module="b",
                relationship_type="IMPORTS", count=2,
            )
        ]
        text = _format_dependencies(deps)
        assert "IMPORTS" in text
        assert "x2" in text

    def test_count_modules(self) -> None:
        modules = [
            ModuleNode(
                node_id="f:1", name="src", file_path="",
                children=[
                    ModuleNode(node_id="f:2", name="a", file_path=""),
                    ModuleNode(node_id="f:3", name="b", file_path=""),
                ],
            )
        ]
        assert _count_modules(modules) == 3


# ---- Full Generation Pipeline ----


class TestGenerateWiki:
    """Tests for the full wiki generation pipeline."""

    @pytest.mark.asyncio
    async def test_generate_wiki_empty_repo(self) -> None:
        storage = MockGraphStorage(rows=[])

        async def mock_llm(prompt: str) -> str:
            return "Generated content."

        doc = await generate_wiki(
            repo_path="/tmp/myrepo",
            storage=storage,  # type: ignore[arg-type]
            llm_call=mock_llm,
        )
        assert doc.title == "myrepo"
        # Should have at least the overview section
        assert any(s.title == "Overview" for s in doc.sections)

    @pytest.mark.asyncio
    async def test_generate_wiki_custom_name(self) -> None:
        storage = MockGraphStorage(rows=[])

        async def mock_llm(prompt: str) -> str:
            return "Content."

        doc = await generate_wiki(
            repo_path="/tmp/repo",
            storage=storage,  # type: ignore[arg-type]
            llm_call=mock_llm,
            project_name="Custom Name",
        )
        assert doc.title == "Custom Name"


# ---- Augmentation Engine ----


class TestAugmentationEngine:
    """Tests for the augmentation engine."""

    @pytest.mark.asyncio
    async def test_augment_grep_empty(self) -> None:
        storage = MockGraphStorage(rows=[])
        result = await augment_grep_results([], storage)  # type: ignore[arg-type]
        assert result == []

    @pytest.mark.asyncio
    async def test_augment_grep_with_match(self) -> None:
        storage = MockGraphStorage(rows=[
            {"name": "process_data", "kind": "Function"}
        ])
        grep_results = [
            GrepResult(
                file_path="/repo/main.py",
                line_number=15,
                line_content="    process_data()",
                match_text="process_data",
            )
        ]
        enriched = await augment_grep_results(
            grep_results, storage  # type: ignore[arg-type]
        )
        assert len(enriched) == 1
        assert enriched[0].symbol_name == "process_data"
        assert enriched[0].symbol_kind == "Function"

    @pytest.mark.asyncio
    async def test_augment_grep_no_symbol(self) -> None:
        storage = MockGraphStorage(rows=[])
        grep_results = [
            GrepResult(
                file_path="/repo/readme.md",
                line_number=1,
                line_content="# README",
            )
        ]
        enriched = await augment_grep_results(
            grep_results, storage  # type: ignore[arg-type]
        )
        assert len(enriched) == 1
        assert enriched[0].symbol_name == ""

    @pytest.mark.asyncio
    async def test_augment_glob_empty(self) -> None:
        storage = MockGraphStorage(rows=[])
        result = await augment_glob_results([], storage)  # type: ignore[arg-type]
        assert result == []

    @pytest.mark.asyncio
    async def test_augment_glob_with_data(self) -> None:
        storage = MockGraphStorage(rows=[
            {"cnt": 5, "langs": ["Python"]}
        ])
        glob_results = [
            GlobResult(
                file_path="/repo/main.py",
                file_name="main.py",
                file_size=1024,
            )
        ]
        enriched = await augment_glob_results(
            glob_results, storage  # type: ignore[arg-type]
        )
        assert len(enriched) == 1
        assert enriched[0].symbol_count == 5
        assert enriched[0].languages == ["Python"]

    @pytest.mark.asyncio
    async def test_augment_grep_batch_limit(self) -> None:
        storage = MockGraphStorage(rows=[])
        many_results = [
            GrepResult(
                file_path=f"/repo/file{i}.py",
                line_number=1,
                line_content="x",
            )
            for i in range(MAX_ENRICHMENT_BATCH + 10)
        ]
        enriched = await augment_grep_results(
            many_results, storage  # type: ignore[arg-type]
        )
        assert len(enriched) == MAX_ENRICHMENT_BATCH + 10
