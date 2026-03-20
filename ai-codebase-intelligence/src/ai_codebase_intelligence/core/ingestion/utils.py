from __future__ import annotations

import asyncio
from typing import Any

from ...config.supported_languages import SupportedLanguages


async def yield_to_event_loop() -> None:
    await asyncio.sleep(0)


def find_sibling_child(parent: Any, sibling_type: str, child_type: str) -> Any | None:
    for i in range(parent.child_count):
        sibling = parent.child(i)
        if sibling is not None and sibling.type == sibling_type:
            for j in range(sibling.child_count):
                child = sibling.child(j)
                if child is not None and child.type == child_type:
                    return child
    return None


def get_language_from_filename(filename: str) -> str | None:
    # TypeScript (including TSX)
    if filename.endswith(".tsx"):
        return SupportedLanguages.TypeScript
    if filename.endswith(".ts"):
        return SupportedLanguages.TypeScript
    # JavaScript (including JSX, CJS, MJS)
    if filename.endswith(".jsx"):
        return SupportedLanguages.JavaScript
    if filename.endswith(".js"):
        return SupportedLanguages.JavaScript
    if filename.endswith(".cjs"):
        return SupportedLanguages.JavaScript
    if filename.endswith(".mjs"):
        return SupportedLanguages.JavaScript
    # Python
    if filename.endswith(".py"):
        return SupportedLanguages.Python
    # Java
    if filename.endswith(".java"):
        return SupportedLanguages.Java
    # C (source and headers)
    if filename.endswith(".c") or filename.endswith(".h"):
        return SupportedLanguages.C
    # C++ (all common extensions)
    if (filename.endswith(".cpp") or filename.endswith(".cc")
            or filename.endswith(".cxx") or filename.endswith(".hpp")
            or filename.endswith(".hxx") or filename.endswith(".hh")):
        return SupportedLanguages.CPlusPlus
    # C#
    if filename.endswith(".cs"):
        return SupportedLanguages.CSharp
    # Go
    if filename.endswith(".go"):
        return SupportedLanguages.Go
    # Rust
    if filename.endswith(".rs"):
        return SupportedLanguages.Rust
    # Kotlin
    if filename.endswith(".kt") or filename.endswith(".kts"):
        return SupportedLanguages.Kotlin
    # PHP (all common extensions)
    if (filename.endswith(".php") or filename.endswith(".phtml")
            or filename.endswith(".php3") or filename.endswith(".php4")
            or filename.endswith(".php5") or filename.endswith(".php8")):
        return SupportedLanguages.PHP
    # Swift
    if filename.endswith(".swift"):
        return SupportedLanguages.Swift
    return None
