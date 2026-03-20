from __future__ import annotations
from enum import Enum


class SupportedLanguages(str, Enum):
    JavaScript = "javascript"
    TypeScript = "typescript"
    Python = "python"
    Java = "java"
    C = "c"
    CPlusPlus = "cpp"
    CSharp = "csharp"
    Go = "go"
    Rust = "rust"
    PHP = "php"
    Kotlin = "kotlin"
    # Ruby = "ruby"
    Swift = "swift"
