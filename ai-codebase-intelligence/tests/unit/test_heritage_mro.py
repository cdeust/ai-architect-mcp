"""Tests for heritage processing and MRO (Epic 7)."""

from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.mro_processor import (
    MROEntry,
    compute_mro,
)
from ai_codebase_intelligence._extraction.structure_processor import (
    build_structure,
)


class TestC3Linearization:
    """Tests for C3 MRO algorithm."""

    def test_single_class(self) -> None:
        mro = compute_mro("A", "A", {}, SupportedLanguage.PYTHON)
        assert len(mro) == 1
        assert mro[0].class_name == "A"
        assert mro[0].depth == 0

    def test_simple_chain(self) -> None:
        chains = {"A": ["B"], "B": ["C"]}
        mro = compute_mro("A", "A", chains, SupportedLanguage.PYTHON)
        names = [e.class_name for e in mro]
        assert names[0] == "A"
        assert "B" in names
        assert "C" in names

    def test_diamond_inheritance(self) -> None:
        # Classic diamond: D -> B, C; B -> A; C -> A
        chains = {
            "D": ["B", "C"],
            "B": ["A"],
            "C": ["A"],
        }
        mro = compute_mro("D", "D", chains, SupportedLanguage.PYTHON)
        ids = [e.class_id for e in mro]
        # A should appear only once
        assert ids.count("A") == 1
        # D should be first
        assert ids[0] == "D"


class TestDFSMro:
    """Tests for single-inheritance DFS MRO."""

    def test_java_chain(self) -> None:
        chains = {"Child": ["Parent"], "Parent": ["Object"]}
        mro = compute_mro("Child", "Child", chains, SupportedLanguage.JAVA)
        names = [e.class_name for e in mro]
        assert names == ["Child", "Parent", "Object"]

    def test_swift_protocol(self) -> None:
        chains = {"MyVC": ["UIViewController"]}
        mro = compute_mro("MyVC", "MyVC", chains, SupportedLanguage.SWIFT)
        assert len(mro) == 2
        assert mro[0].depth == 0
        assert mro[1].depth == 1


class TestStructureProcessor:
    """Tests for file/folder hierarchy building."""

    def test_build_structure(self, tmp_path: object) -> None:
        repo_root = "/tmp/repo"
        files = [
            "/tmp/repo/src/main.py",
            "/tmp/repo/src/utils.py",
            "/tmp/repo/tests/test_main.py",
        ]
        nodes, rels = build_structure(files, repo_root)

        file_nodes = [n for n in nodes if n.label.value == "File"]
        folder_nodes = [n for n in nodes if n.label.value == "Folder"]

        assert len(file_nodes) == 3
        assert len(folder_nodes) >= 2  # src/ and tests/

        # All relationships should be CONTAINS
        for rel in rels:
            assert rel.relationship_type.value == "CONTAINS"

    def test_language_detection(self) -> None:
        nodes, _ = build_structure(["/repo/app.swift"], "/repo")
        file_node = nodes[0]
        assert file_node.language == "swift"
