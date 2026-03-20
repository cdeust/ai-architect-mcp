from __future__ import annotations

from collections import OrderedDict
from typing import Any


class ASTCache:
    def __init__(self, max_size: int = 50) -> None:
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size

    def get(self, file_path: str) -> Any | None:
        if file_path in self._cache:
            self._cache.move_to_end(file_path)
            return self._cache[file_path]
        return None

    def set(self, file_path: str, tree: Any) -> None:
        if file_path in self._cache:
            self._cache.move_to_end(file_path)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[file_path] = tree

    def clear(self) -> None:
        self._cache.clear()

    def stats(self) -> dict[str, int]:
        return {"size": len(self._cache), "maxSize": self._max_size}


def create_ast_cache(max_size: int = 50) -> ASTCache:
    return ASTCache(max_size)
