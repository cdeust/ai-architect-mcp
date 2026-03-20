"""Tests for import extraction from tree-sitter ASTs."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.import_extractor import (
    ImportInfo,
    extract_imports_from_tree,
)
from ai_codebase_intelligence._parsing.parser_loader import (
    clear_parser_cache,
    get_parser,
)


def _parse(language: SupportedLanguage, code: str, path: str = "") -> object:
    """Parse code and return the root node."""
    parser = get_parser(language, path)
    tree = parser.parse(code.encode("utf-8"))
    return tree.root_node


class TestPythonImports:
    """Tests for Python import extraction."""

    def setup_method(self) -> None:
        clear_parser_cache()

    def test_plain_import(self) -> None:
        """``import os`` extracts source_module='os'."""
        root = _parse(SupportedLanguage.PYTHON, "import os\n")
        results = extract_imports_from_tree(
            root, "/src/main.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 1
        assert results[0].source_module == "os"
        assert results[0].imported_names == []
        assert results[0].is_wildcard is False
        assert results[0].line == 1

    def test_from_import(self) -> None:
        """``from os.path import join`` extracts module and name."""
        root = _parse(
            SupportedLanguage.PYTHON, "from os.path import join\n"
        )
        results = extract_imports_from_tree(
            root, "/src/main.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 1
        assert results[0].source_module == "os.path"
        assert "join" in results[0].imported_names
        assert results[0].is_wildcard is False

    def test_relative_import(self) -> None:
        """``from . import sibling`` extracts relative dot prefix."""
        root = _parse(
            SupportedLanguage.PYTHON, "from . import sibling\n"
        )
        results = extract_imports_from_tree(
            root, "/src/pkg/__init__.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 1
        # Should start with a dot
        assert results[0].source_module.startswith(".")

    def test_wildcard_import(self) -> None:
        """``from os.path import *`` has is_wildcard=True."""
        root = _parse(
            SupportedLanguage.PYTHON, "from os.path import *\n"
        )
        results = extract_imports_from_tree(
            root, "/src/main.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 1
        assert results[0].is_wildcard is True

    def test_multiple_imports(self) -> None:
        """Multiple import statements produce multiple results."""
        code = "import os\nimport sys\nfrom pathlib import Path\n"
        root = _parse(SupportedLanguage.PYTHON, code)
        results = extract_imports_from_tree(
            root, "/src/main.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 3

    def test_aliased_import(self) -> None:
        """``import numpy as np`` extracts the module name."""
        root = _parse(
            SupportedLanguage.PYTHON, "import numpy as np\n"
        )
        results = extract_imports_from_tree(
            root, "/src/main.py", SupportedLanguage.PYTHON
        )
        assert len(results) == 1
        assert results[0].source_module == "numpy"


class TestTypeScriptImports:
    """Tests for TypeScript/JavaScript import extraction."""

    def setup_method(self) -> None:
        clear_parser_cache()

    def test_named_import(self) -> None:
        """``import { X } from './module'`` extracts module and name."""
        code = "import { X } from './module';\n"
        root = _parse(SupportedLanguage.TYPESCRIPT, code)
        results = extract_imports_from_tree(
            root, "/src/app.ts", SupportedLanguage.TYPESCRIPT
        )
        assert len(results) == 1
        assert results[0].source_module == "./module"
        assert "X" in results[0].imported_names

    def test_default_import(self) -> None:
        """``import React from 'react'`` extracts module and name."""
        code = "import React from 'react';\n"
        root = _parse(SupportedLanguage.TYPESCRIPT, code)
        results = extract_imports_from_tree(
            root, "/src/app.ts", SupportedLanguage.TYPESCRIPT
        )
        assert len(results) == 1
        assert results[0].source_module == "react"
        assert "React" in results[0].imported_names

    def test_multiple_named_imports(self) -> None:
        """``import { A, B } from './lib'`` extracts both names."""
        code = "import { A, B } from './lib';\n"
        root = _parse(SupportedLanguage.TYPESCRIPT, code)
        results = extract_imports_from_tree(
            root, "/src/app.ts", SupportedLanguage.TYPESCRIPT
        )
        assert len(results) == 1
        assert "A" in results[0].imported_names
        assert "B" in results[0].imported_names


class TestGoImports:
    """Tests for Go import extraction."""

    def setup_method(self) -> None:
        clear_parser_cache()

    def test_single_import(self) -> None:
        """Single Go import extracts the module path."""
        code = 'package main\n\nimport "fmt"\n'
        root = _parse(SupportedLanguage.GO, code)
        results = extract_imports_from_tree(
            root, "/src/main.go", SupportedLanguage.GO
        )
        assert len(results) == 1
        assert results[0].source_module == "fmt"

    def test_grouped_imports(self) -> None:
        """Go grouped import block extracts each package."""
        code = 'package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n'
        root = _parse(SupportedLanguage.GO, code)
        results = extract_imports_from_tree(
            root, "/src/main.go", SupportedLanguage.GO
        )
        assert len(results) >= 2
        modules = {r.source_module for r in results}
        assert "fmt" in modules
        assert "os" in modules


class TestImportInfoFrozen:
    """Test ImportInfo dataclass properties."""

    def test_frozen(self) -> None:
        """ImportInfo is immutable."""
        info = ImportInfo(
            source_module="os",
            imported_names=[],
            is_wildcard=False,
            file_path="/src/main.py",
            line=1,
        )
        with pytest.raises(AttributeError):
            info.source_module = "sys"  # type: ignore[misc]

    def test_fields(self) -> None:
        """ImportInfo has all required fields."""
        info = ImportInfo(
            source_module="os.path",
            imported_names=["join", "exists"],
            is_wildcard=False,
            file_path="/src/main.py",
            line=5,
        )
        assert info.source_module == "os.path"
        assert info.imported_names == ["join", "exists"]
        assert info.file_path == "/src/main.py"
        assert info.line == 5
