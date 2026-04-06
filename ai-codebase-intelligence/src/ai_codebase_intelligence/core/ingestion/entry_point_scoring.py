"""Entry point scoring."""
from __future__ import annotations

import re
from typing import Any

from .framework_detection import detect_framework_from_path

_UNIVERSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(main|init|bootstrap|start|run|setup|configure)$", re.I),
    re.compile(r"^handle[A-Z]"), re.compile(r"^on[A-Z]"),
    re.compile(r"Handler$"), re.compile(r"Controller$"),
    re.compile(r"^process[A-Z]"), re.compile(r"^execute[A-Z]"),
    re.compile(r"^perform[A-Z]"), re.compile(r"^dispatch[A-Z]"),
    re.compile(r"^trigger[A-Z]"), re.compile(r"^fire[A-Z]"),
    re.compile(r"^emit[A-Z]"),
]

_LANG_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "javascript": [re.compile(r"^use[A-Z]")],
    "typescript": [re.compile(r"^use[A-Z]")],
    "python": [re.compile(r"^app$"), re.compile(r"^(get|post|put|delete|patch)_", re.I), re.compile(r"^api_"), re.compile(r"^view_")],
    "java": [re.compile(r"^do[A-Z]"), re.compile(r"^create[A-Z]"), re.compile(r"^build[A-Z]"), re.compile(r"Service$")],
    "csharp": [re.compile(r"^(Get|Post|Put|Delete)"), re.compile(r"Action$"), re.compile(r"^On[A-Z]"), re.compile(r"Async$")],
    "go": [re.compile(r"Handler$"), re.compile(r"^Serve"), re.compile(r"^New[A-Z]"), re.compile(r"^Make[A-Z]")],
    "rust": [re.compile(r"^(get|post|put|delete)_handler$", re.I), re.compile(r"^handle_"), re.compile(r"^new$"), re.compile(r"^run$"), re.compile(r"^spawn")],
    "c": [re.compile(r"^main$"), re.compile(r"^init_"), re.compile(r"^start_"), re.compile(r"^run_")],
    "cpp": [re.compile(r"^main$"), re.compile(r"^init_"), re.compile(r"^Create[A-Z]"), re.compile(r"^Run$"), re.compile(r"^Start$")],
    "swift": [re.compile(r"^viewDidLoad$"), re.compile(r"^viewWillAppear$"), re.compile(r"^viewDidAppear$"), re.compile(r"^application\("), re.compile(r"^body$"), re.compile(r"Coordinator$"), re.compile(r"ViewController$"), re.compile(r"^configure[A-Z]"), re.compile(r"^setup[A-Z]")],
    "php": [re.compile(r"Controller$"), re.compile(r"^handle$"), re.compile(r"^execute$"), re.compile(r"^boot$"), re.compile(r"^register$"), re.compile(r"^__invoke$"), re.compile(r"^(index|show|store|update|destroy|create|edit)$"), re.compile(r"Service$"), re.compile(r"Repository$")],
}

_UTILITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(get|set|is|has|can|should|will|did)[A-Z]"),
    re.compile(r"^_"),
    re.compile(r"^(format|parse|validate|convert|transform)", re.I),
    re.compile(r"^(log|debug|error|warn|info)$", re.I),
    re.compile(r"^(to|from)[A-Z]"),
    re.compile(r"^(encode|decode)", re.I),
    re.compile(r"^(serialize|deserialize)", re.I),
    re.compile(r"Helper$"), re.compile(r"Util$"), re.compile(r"Utils$"),
    re.compile(r"^utils?$", re.I), re.compile(r"^helpers?$", re.I),
]


def calculate_entry_point_score(
    name: str,
    language: str,
    is_exported: bool,
    caller_count: int,
    callee_count: int,
    file_path: str = "",
) -> dict[str, Any]:
    reasons: list[str] = []

    if callee_count == 0:
        return {"score": 0, "reasons": ["no-outgoing-calls"]}

    base_score = callee_count / (caller_count + 1)
    reasons.append(f"base:{base_score:.2f}")

    export_multiplier = 2.0 if is_exported else 1.0
    if is_exported:
        reasons.append("exported")

    name_multiplier = 1.0
    if any(p.search(name) for p in _UTILITY_PATTERNS):
        name_multiplier = 0.3
        reasons.append("utility-pattern")
    else:
        all_patterns = _UNIVERSAL_PATTERNS + _LANG_PATTERNS.get(language, [])
        if any(p.search(name) for p in all_patterns):
            name_multiplier = 1.5
            reasons.append("entry-pattern")

    framework_multiplier = 1.0
    if file_path:
        hint = detect_framework_from_path(file_path)
        if hint is not None:
            framework_multiplier = hint["entryPointMultiplier"]
            reasons.append(f"framework:{hint['reason']}")

    final_score = base_score * export_multiplier * name_multiplier * framework_multiplier
    return {"score": final_score, "reasons": reasons}


def is_test_file(file_path: str) -> bool:
    p = file_path.lower().replace("\\", "/")
    return (
        ".test." in p or ".spec." in p
        or "__tests__/" in p or "__mocks__/" in p
        or "/test/" in p or "/tests/" in p or "/testing/" in p
        or p.endswith("_test.py") or "/test_" in p
        or p.endswith("_test.go")
        or "/src/test/" in p
        or p.endswith("tests.swift") or p.endswith("test.swift")
        or "uitests/" in p
        or ".tests/" in p or "tests.cs" in p
        or p.endswith("test.php") or p.endswith("spec.php")
        or "/tests/feature/" in p or "/tests/unit/" in p
    )


def is_utility_file(file_path: str) -> bool:
    p = file_path.lower().replace("\\", "/")
    return (
        "/utils/" in p or "/util/" in p
        or "/helpers/" in p or "/helper/" in p
        or "/common/" in p or "/shared/" in p or "/lib/" in p
        or p.endswith("/utils.ts") or p.endswith("/utils.js")
        or p.endswith("/helpers.ts") or p.endswith("/helpers.js")
        or p.endswith("_utils.py") or p.endswith("_helpers.py")
    )
