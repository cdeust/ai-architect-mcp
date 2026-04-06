from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage

_CONSTRUCTOR_LANGUAGES = frozenset({
    SupportedLanguage.SWIFT,
    SupportedLanguage.KOTLIN,
    SupportedLanguage.JAVA,
    SupportedLanguage.CSHARP,
})


class CallForm(str, Enum):
    """Classification of how a function or method is invoked."""

    FREE = "free"
    MEMBER = "member"
    STATIC = "static"
    SUPER = "super"
    CONSTRUCTOR = "constructor"


@dataclass(frozen=True, slots=True)
class CallInfo:
    """Structured representation of a call site.

    Args:
        name: The function or method name being called.
        receiver: The receiver expression (e.g. "self", "Factory", "super").
        form: The classified call form.
        language: The source language.
    """

    name: str
    receiver: str
    form: CallForm
    language: SupportedLanguage


def classify_call(
    name: str,
    receiver: str,
    language: SupportedLanguage,
) -> CallForm:
    """Classify a call site into a canonical form.

    Args:
        name: The function or method name.
        receiver: The receiver/qualifier expression, or empty string for
            bare calls.
        language: The source language of the call site.

    Returns:
        The classified CallForm.
    """
    if receiver == "super":
        return CallForm.SUPER

    if receiver in ("self", "this"):
        return CallForm.MEMBER

    if receiver:
        if receiver[0].isupper():
            return CallForm.STATIC
        return CallForm.MEMBER

    if name == "__init__":
        return CallForm.CONSTRUCTOR

    if name and name[0].isupper() and language in _CONSTRUCTOR_LANGUAGES:
        return CallForm.CONSTRUCTOR

    return CallForm.FREE
