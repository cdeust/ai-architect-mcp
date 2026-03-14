"""Infrastructure adapters.

Concrete implementations of port interfaces defined in ports.py.
Each adapter wraps a specific external system (Git, Xcode, GitHub,
filesystem) and implements the corresponding port protocol.

Adapters are injected at the composition root. Stage logic never
imports adapters directly — only port interfaces.
"""

from __future__ import annotations

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._adapters.local_audit import LocalAudit
from ai_architect_mcp._adapters.local_experience import LocalExperience
from ai_architect_mcp._adapters.local_pipeline_state import LocalPipelineState
from ai_architect_mcp._adapters.mcp_client_base import (
    MCPClientBase,
    MCPClientError,
)
from ai_architect_mcp._adapters.memory_ports import (
    AuditPort,
    ExperiencePort,
    PipelineStatePort,
)

__all__ = [
    "AuditPort",
    "CompositionRoot",
    "ExperiencePort",
    "LocalAudit",
    "LocalExperience",
    "LocalPipelineState",
    "MCPClientBase",
    "MCPClientError",
    "PipelineStatePort",
]
