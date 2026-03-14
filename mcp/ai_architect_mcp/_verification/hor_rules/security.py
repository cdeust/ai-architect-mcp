"""HOR Rules 31-38: Security and data protection checks."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ai_architect_mcp._models.verification import (
    PENALTY_CRITICAL,
    PENALTY_WARNING,
    HORRuleResult,
    HORSeverity,
)

CATEGORY = "security"
SECRET_PATTERNS = [
    r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{8,}",
    r"(?:secret|token|password)\s*[=:]\s*['\"][^'\"]{8,}",
    r"sk-[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
]


def _make_result(rule_id: int, name: str, passed: bool, message: str, severity: HORSeverity) -> HORRuleResult:
    penalty = PENALTY_CRITICAL if severity == HORSeverity.CRITICAL else PENALTY_WARNING
    return HORRuleResult(rule_id=rule_id, rule_name=name, category=CATEGORY, passed=passed, message=message, severity=severity, penalty=penalty)


def rule_031_no_hardcoded_secrets(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return _make_result(31, "no_hardcoded_secrets", False, "Hardcoded secret pattern detected — use environment variables", HORSeverity.CRITICAL)
    return _make_result(31, "no_hardcoded_secrets", True, "No hardcoded secrets found", HORSeverity.CRITICAL)


def rule_032_input_sanitization(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_user_input = any(kw in content for kw in ["user input", "form data", "request body", "query param"])
    has_sanitization = any(kw in content for kw in ["sanitiz", "validat", "escape", "parameterized"])
    if has_user_input and not has_sanitization:
        return _make_result(32, "input_sanitization", False, "User input handling without sanitization/validation documented", HORSeverity.CRITICAL)
    return _make_result(32, "input_sanitization", True, "Input sanitization documented or not applicable", HORSeverity.CRITICAL)


def rule_033_auth_requirements(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_api = any(kw in content for kw in ["api", "endpoint", "route", "service"])
    has_auth = any(kw in content for kw in ["authenticat", "authoriz", "oauth", "jwt", "rbac"])
    if has_api and not has_auth:
        return _make_result(33, "auth_requirements", False, "API/service defined without authentication/authorization requirements", HORSeverity.CRITICAL)
    return _make_result(33, "auth_requirements", True, "Authentication requirements documented", HORSeverity.CRITICAL)


def rule_034_encryption_at_rest(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_sensitive = any(kw in content for kw in ["password", "credential", "pii", "personal data", "sensitive"])
    has_encryption = any(kw in content for kw in ["encrypt", "aes", "hashing", "bcrypt", "argon"])
    if has_sensitive and not has_encryption:
        return _make_result(34, "encryption_at_rest", False, "Sensitive data without encryption specification", HORSeverity.CRITICAL)
    return _make_result(34, "encryption_at_rest", True, "Encryption documented for sensitive data", HORSeverity.CRITICAL)


def rule_035_gdpr_compliance(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_pii = any(kw in content for kw in ["personal data", "pii", "user data", "email", "name", "address"])
    has_gdpr = any(kw in content for kw in ["gdpr", "retention", "consent", "right to delete", "data protection"])
    if has_pii and not has_gdpr:
        return _make_result(35, "gdpr_compliance", False, "PII handling without GDPR compliance documentation", HORSeverity.WARNING)
    return _make_result(35, "gdpr_compliance", True, "GDPR compliance addressed or no PII", HORSeverity.WARNING)


def rule_036_no_force_operations(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    force_patterns = [r"!\s*$", r"try!\s", r"as!\s", r"force_unwrap", r"\.unwrap\(\)"]
    for pattern in force_patterns:
        if re.search(pattern, content):
            return _make_result(36, "no_force_operations", False, "Force-unwrap/try/cast found — handle errors explicitly", HORSeverity.CRITICAL)
    return _make_result(36, "no_force_operations", True, "No force operations found", HORSeverity.CRITICAL)


def rule_037_env_file_prohibition(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    if re.search(r"\.env\b|dotenv|load_dotenv", content):
        return _make_result(37, "env_file_prohibition", False, "References to .env files — use environment variables directly", HORSeverity.CRITICAL)
    return _make_result(37, "env_file_prohibition", True, "No .env file references", HORSeverity.CRITICAL)


def rule_038_data_residency(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_storage = any(kw in content for kw in ["database", "storage", "cloud", "s3", "blob"])
    has_residency = any(kw in content for kw in ["region", "residency", "data location", "jurisdiction"])
    if has_storage and not has_residency:
        return _make_result(38, "data_residency", False, "Data storage without location/residency documentation", HORSeverity.WARNING)
    return _make_result(38, "data_residency", True, "Data residency documented or not applicable", HORSeverity.WARNING)


def get_rules() -> list[tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]]:
    return [
        (31, rule_031_no_hardcoded_secrets, CATEGORY, "no_hardcoded_secrets", HORSeverity.CRITICAL),
        (32, rule_032_input_sanitization, CATEGORY, "input_sanitization", HORSeverity.CRITICAL),
        (33, rule_033_auth_requirements, CATEGORY, "auth_requirements", HORSeverity.CRITICAL),
        (34, rule_034_encryption_at_rest, CATEGORY, "encryption_at_rest", HORSeverity.CRITICAL),
        (35, rule_035_gdpr_compliance, CATEGORY, "gdpr_compliance", HORSeverity.WARNING),
        (36, rule_036_no_force_operations, CATEGORY, "no_force_operations", HORSeverity.CRITICAL),
        (37, rule_037_env_file_prohibition, CATEGORY, "env_file_prohibition", HORSeverity.CRITICAL),
        (38, rule_038_data_residency, CATEGORY, "data_residency", HORSeverity.WARNING),
    ]
