from __future__ import annotations

from typing import Any


class SymbolTable:
    def __init__(self) -> None:
        # File-Specific Index: filePath -> (symbolName -> nodeId)
        self._file_index: dict[str, dict[str, str]] = {}
        # Global Reverse Index: symbolName -> [list of definitions]
        self._global_index: dict[str, list[dict[str, str]]] = {}

    def add(self, file_path: str, name: str, node_id: str, type_: str) -> None:
        # A. Add to File Index
        if file_path not in self._file_index:
            self._file_index[file_path] = {}
        self._file_index[file_path][name] = node_id

        # B. Add to Global Index
        if name not in self._global_index:
            self._global_index[name] = []
        self._global_index[name].append({
            "nodeId": node_id,
            "filePath": file_path,
            "type": type_,
        })

    def lookup_exact(self, file_path: str, name: str) -> str | None:
        file_symbols = self._file_index.get(file_path)
        if file_symbols is None:
            return None
        return file_symbols.get(name)

    def lookup_fuzzy(self, name: str) -> list[dict[str, str]]:
        return self._global_index.get(name, [])

    def get_stats(self) -> dict[str, int]:
        return {
            "fileCount": len(self._file_index),
            "globalSymbolCount": len(self._global_index),
        }

    def clear(self) -> None:
        self._file_index.clear()
        self._global_index.clear()


def create_symbol_table() -> SymbolTable:
    return SymbolTable()
