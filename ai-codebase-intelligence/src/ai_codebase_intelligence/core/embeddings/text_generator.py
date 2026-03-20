"""Text generator — 1:1 port of gitnexus core/embeddings/text-generator.js."""
from __future__ import annotations

from typing import Any

DEFAULT_MAX_SNIPPET_LENGTH = 500


def _get_file_name(file_path: str) -> str:
    parts = file_path.split("/")
    return parts[-1] if parts else file_path


def _get_directory(file_path: str) -> str:
    parts = file_path.split("/")
    parts.pop()
    return "/".join(parts)


def _truncate_content(content: str, max_length: int) -> str:
    if len(content) <= max_length:
        return content
    truncated = content[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        return truncated[:last_space] + "..."
    return truncated + "..."


def _clean_content(content: str) -> str:
    import re
    content = content.replace("\r\n", "\n")
    content = re.sub(r"\n{3,}", "\n\n", content)
    lines = [line.rstrip() for line in content.split("\n")]
    return "\n".join(lines).strip()


def _generate_symbol_text(label: str, node: dict[str, Any], max_snippet: int) -> str:
    parts = [f"{label}: {node.get('name', '')}", f"File: {_get_file_name(node.get('filePath', ''))}"]
    d = _get_directory(node.get("filePath", ""))
    if d:
        parts.append(f"Directory: {d}")
    content = node.get("content", "")
    if content:
        cleaned = _clean_content(content)
        snippet = _truncate_content(cleaned, max_snippet)
        parts.extend(["", snippet])
    return "\n".join(parts)


def generate_embedding_text(node: dict[str, Any], config: dict[str, Any] | None = None) -> str:
    max_snippet = (config or {}).get("maxSnippetLength", DEFAULT_MAX_SNIPPET_LENGTH)
    label = node.get("label", "")
    if label == "File":
        parts = [f"File: {node.get('name', '')}", f"Path: {node.get('filePath', '')}"]
        content = node.get("content", "")
        if content:
            cleaned = _clean_content(content)
            parts.extend(["", _truncate_content(cleaned, min(max_snippet, 300))])
        return "\n".join(parts)
    if label in ("Function", "Class", "Method", "Interface"):
        return _generate_symbol_text(label, node, max_snippet)
    return f"{label}: {node.get('name', '')}\nPath: {node.get('filePath', '')}"


def generate_batch_embedding_texts(nodes: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[str]:
    return [generate_embedding_text(n, config) for n in nodes]
