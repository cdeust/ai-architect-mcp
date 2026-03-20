"""Wiki prompt templates — 1:1 port of gitnexus core/wiki/prompts.js."""
from __future__ import annotations

from typing import Any

MODULE_SYSTEM_PROMPT = """You are a technical documentation writer. Write clear, developer-focused documentation for a code module.

Rules:
- Reference actual function names, class names, and code patterns — do NOT invent APIs
- Use the call graph and execution flow data for accuracy
- Include Mermaid diagrams only when they genuinely help understanding
- Write for a developer who needs to understand and contribute to this code
- Begin with a concise overview. Place <!-- summary-end --> after the opening section."""

MODULE_USER_PROMPT = """Write documentation for the **{{MODULE_NAME}}** module.

## Source Code
{{SOURCE_CODE}}

## Call Graph & Execution Flows
Internal calls: {{INTRA_CALLS}}
Outgoing calls: {{OUTGOING_CALLS}}
Incoming calls: {{INCOMING_CALLS}}
Execution flows: {{PROCESSES}}

## Other Modules
{{MODULE_REGISTRY}}"""

OVERVIEW_SYSTEM_PROMPT = """You are a technical documentation writer. Write the top-level overview page for a repository wiki."""

OVERVIEW_USER_PROMPT = """Write the overview page for this repository wiki.

## Project Info
{{PROJECT_INFO}}

## Module Summaries
{{MODULE_SUMMARIES}}

## Reference Data
Inter-module edges: {{MODULE_EDGES}}
Key flows: {{TOP_PROCESSES}}

## Module Registry
{{MODULE_REGISTRY}}"""


def fill_template(template: str, vars_: dict[str, str]) -> str:
    result = template
    for key, value in vars_.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


def short_path(fp: str) -> str:
    parts = fp.replace("\\", "/").split("/")
    return "/".join(parts[-3:]) if len(parts) > 3 else fp


def format_call_edges(edges: list[dict[str, str]]) -> str:
    if not edges:
        return "None"
    return "\n".join(
        f"{e['fromName']} ({short_path(e['fromFile'])}) -> {e['toName']} ({short_path(e['toFile'])})"
        for e in edges[:30]
    )


def format_processes(processes: list[dict[str, Any]]) -> str:
    if not processes:
        return "No execution flows detected."
    parts = []
    for p in processes:
        steps = "\n".join(f"  {s['step']}. {s['name']} ({short_path(s['filePath'])})" for s in p.get("steps", []))
        parts.append(f"**{p['label']}** ({p.get('type', '')}):\n{steps}")
    return "\n\n".join(parts)
