"""Embedding types."""
from __future__ import annotations

EMBEDDABLE_LABELS: list[str] = ["Function", "Class", "Method", "Interface", "File"]


def is_embeddable_label(label: str) -> bool:
    return label in EMBEDDABLE_LABELS


DEFAULT_EMBEDDING_CONFIG: dict[str, object] = {
    "modelId": "Snowflake/snowflake-arctic-embed-xs",
    "batchSize": 16,
    "dimensions": 384,
    "device": "auto",
    "maxSnippetLength": 500,
}
