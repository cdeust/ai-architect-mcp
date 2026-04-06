"""Data models for the REST API layer.

Provides request/response dataclasses used by route matching,
handlers, and the HTTP transport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Type alias for the repo name -> path mapping.
RepoIndex = dict[str, str]


@dataclass
class APIRequest:
    """Incoming HTTP request."""

    method: str
    path: str
    body: dict[str, Any] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)


@dataclass
class APIResponse:
    """Outgoing HTTP response."""

    status: int
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
