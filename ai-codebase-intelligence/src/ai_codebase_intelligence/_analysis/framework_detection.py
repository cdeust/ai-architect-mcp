"""Framework detection from file path patterns.

Identifies web frameworks (Django, Express, Flask, FastAPI, Rails,
Spring) by matching file paths against known directory and file
naming conventions.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FrameworkType(str, Enum):
    """Known web framework types."""

    DJANGO = "django"
    EXPRESS = "express"
    FLASK = "flask"
    FASTAPI = "fastapi"
    RAILS = "rails"
    SPRING = "spring"
    UNKNOWN = "unknown"


class FrameworkDetectionResult(BaseModel):
    """Result of framework detection.

    Args:
        framework: The detected framework type.
        confidence: Detection confidence (0.0-1.0).
        matched_files: Files that matched the detection pattern.
    """

    framework: FrameworkType = Field(description="Detected framework")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Detection confidence",
    )
    matched_files: list[str] = Field(
        default_factory=list,
        description="Files that matched the detection pattern",
    )


def detect_framework(files: list[str]) -> FrameworkDetectionResult:
    """Detect the web framework from a list of file paths.

    Args:
        files: List of file paths in the project.

    Returns:
        FrameworkDetectionResult with the detected framework.
    """
    normalized = [f.lower().replace("\\", "/") for f in files]

    result = _check_django(normalized, files)
    if result is not None:
        return result

    result = _check_express(normalized, files)
    if result is not None:
        return result

    result = _check_flask(normalized, files)
    if result is not None:
        return result

    result = _check_fastapi(normalized, files)
    if result is not None:
        return result

    result = _check_rails(normalized, files)
    if result is not None:
        return result

    result = _check_spring(normalized, files)
    if result is not None:
        return result

    return FrameworkDetectionResult(framework=FrameworkType.UNKNOWN)


def _check_django(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    for norm, orig in zip(normalized, originals):
        if norm.endswith("manage.py"):
            matched.append(orig)
        elif norm.endswith("views.py"):
            matched.append(orig)
        elif norm.endswith("models.py") and "app" in norm:
            matched.append(orig)
        elif norm.endswith("urls.py"):
            matched.append(orig)
        elif "/templates/" in norm:
            matched.append(orig)
    if any(n.endswith("manage.py") for n in normalized):
        return FrameworkDetectionResult(
            framework=FrameworkType.DJANGO,
            confidence=0.9,
            matched_files=matched,
        )
    if sum(1 for n in normalized if n.endswith(("views.py", "urls.py"))) >= 2:
        return FrameworkDetectionResult(
            framework=FrameworkType.DJANGO,
            confidence=0.7,
            matched_files=matched,
        )
    return None


def _check_express(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    has_server = False
    has_routes = False
    for norm, orig in zip(normalized, originals):
        if "server.js" in norm or "server.ts" in norm or "app.js" in norm:
            matched.append(orig)
            has_server = True
        elif "/routes/" in norm and norm.endswith((".js", ".ts")):
            matched.append(orig)
            has_routes = True
        elif "express" in norm:
            matched.append(orig)
    if has_server and has_routes:
        return FrameworkDetectionResult(
            framework=FrameworkType.EXPRESS,
            confidence=0.8,
            matched_files=matched,
        )
    if has_server:
        return FrameworkDetectionResult(
            framework=FrameworkType.EXPRESS,
            confidence=0.5,
            matched_files=matched,
        )
    return None


def _check_flask(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    for norm, orig in zip(normalized, originals):
        if norm.endswith("app.py"):
            matched.append(orig)
        elif "flask" in norm:
            matched.append(orig)
    if any("flask" in n for n in normalized) and matched:
        return FrameworkDetectionResult(
            framework=FrameworkType.FLASK,
            confidence=0.8,
            matched_files=matched,
        )
    return None


def _check_fastapi(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    for norm, orig in zip(normalized, originals):
        if "fastapi" in norm:
            matched.append(orig)
        elif ("/routers/" in norm or "/endpoints/" in norm) and norm.endswith(".py"):
            matched.append(orig)
    if matched:
        return FrameworkDetectionResult(
            framework=FrameworkType.FASTAPI,
            confidence=0.7,
            matched_files=matched,
        )
    return None


def _check_rails(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    for norm, orig in zip(normalized, originals):
        if "gemfile" in norm:
            matched.append(orig)
        elif "/app/controllers/" in norm:
            matched.append(orig)
        elif "/app/models/" in norm and norm.endswith(".rb"):
            matched.append(orig)
        elif "/config/routes.rb" in norm:
            matched.append(orig)
    if sum(1 for n in normalized if "/app/controllers/" in n) >= 1:
        return FrameworkDetectionResult(
            framework=FrameworkType.RAILS,
            confidence=0.8,
            matched_files=matched,
        )
    return None


def _check_spring(
    normalized: list[str], originals: list[str],
) -> FrameworkDetectionResult | None:
    matched: list[str] = []
    for norm, orig in zip(normalized, originals):
        if "/controller/" in norm and norm.endswith(".java"):
            matched.append(orig)
        elif "/controllers/" in norm and norm.endswith(".java"):
            matched.append(orig)
        elif norm.endswith("controller.java"):
            matched.append(orig)
        elif "application.java" in norm or "application.kt" in norm:
            matched.append(orig)
    if matched:
        return FrameworkDetectionResult(
            framework=FrameworkType.SPRING,
            confidence=0.7,
            matched_files=matched,
        )
    return None
