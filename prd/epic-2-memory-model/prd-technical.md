# Epic 2: Technical Architecture

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2

---

## Module Structure

```
ai_architect/
├── _models/
│   ├── pipeline_state.py           # PipelineState, PipelineStatus
│   ├── experience_pattern.py        # ExperiencePattern, PatternType
│   └── audit_event.py              # AuditEvent, AuditOutcome, AuditQuery
├── _context/
│   ├── progressive_disclosure.py   # ProgressiveDisclosure, DisclosureLevel
│   ├── budget_monitor.py           # ContextBudgetMonitor, ContextBudget
│   ├── handoff.py                  # HandoffDocument (existing, updated)
│   └── stage_context.py            # StageContext (existing, no changes)
├── _adapters/
│   ├── ports.py                    # PipelineStatePort, ExperiencePort, AuditPort (+ existing)
│   ├── local_pipeline_state.py     # LocalPipelineStateAdapter
│   ├── local_experience.py         # LocalExperienceAdapter
│   ├── local_audit.py              # LocalAuditAdapter
│   ├── cloudkit/
│   │   ├── cloudkit_pipeline.py    # CloudKitPipelineStateAdapter
│   │   ├── cloudkit_experience.py  # CloudKitExperienceAdapter
│   │   └── cloudkit_audit.py       # CloudKitAuditAdapter
│   └── composition_root.py         # CompositionRoot (updated)
└── tests/
    ├── test_pipeline_state.py
    ├── test_experience_pattern.py
    ├── test_audit_event.py
    ├── test_progressive_disclosure.py
    ├── test_budget_monitor.py
    ├── test_cloudkit_sync.py
    └── conftest.py
```

---

## Domain Models

### 1. PipelineState (`_models/pipeline_state.py`)

```python
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field

class PipelineStatus(str, Enum):
    """Session execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    HANDOFF_PENDING = "handoff_pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineState(BaseModel):
    """Session-scoped agent execution state.

    Represents the current stage and active context of a synthesis session,
    persisted to Session layer (local cache + CloudKit).
    """
    model_config = {"frozen": False}  # Mutable at API level

    session_id: UUID = Field(
        description="Unique identifier for this execution session"
    )
    current_stage: int = Field(
        ge=0, le=10,
        description="Stage index (0=initialization, 10=synthesis complete)"
    )
    active_finding: Optional[UUID] = Field(
        default=None,
        description="UUID of Finding currently being refined, or None"
    )
    agent_id: str = Field(
        description="Identifier of agent currently executing this session"
    )
    status: PipelineStatus = Field(
        default=PipelineStatus.IDLE,
        description="Current execution status (IDLE, RUNNING, etc.)"
    )
    skill_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of skill name to version string"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="Timestamp when session was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="Timestamp of last update"
    )

    # CloudKit sync metadata (not serialized to user-facing JSON)
    last_modified_by: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Agent ID that last modified this record (for conflict resolution)"
    )
    last_modified_at: Optional[datetime] = Field(
        default=None,
        exclude=True,
        description="UTC timestamp of last modification (for conflict resolution)"
    )

    def set_status(self, new_status: PipelineStatus) -> None:
        """Transition to a new execution status.

        Args:
            new_status: Target PipelineStatus

        Raises:
            ValueError: If transition is invalid
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def advance_stage(self) -> None:
        """Increment current_stage by 1 (capped at 10)."""
        if self.current_stage < 10:
            self.current_stage += 1
        self.updated_at = datetime.utcnow()
```

### 2. ExperiencePattern (`_models/experience_pattern.py`)

```python
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import math

class PatternType(str, Enum):
    """Category of learned pattern."""
    ARCHITECTURAL = "architectural"
    DOMAIN_MODELING = "domain_modeling"
    NAMING = "naming"
    INTERFACE_DESIGN = "interface_design"
    REFINEMENT_HEURISTIC = "refinement_heuristic"

class ExperiencePattern(BaseModel):
    """Learned pattern with biological half-life decay.

    Patterns represent insights from previous synthesis tasks that decay
    in relevance over time using a half-life model. Reinforcement boosts
    the pattern's relevance and extends its lifespan.
    """
    model_config = {"frozen": False}

    pattern_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this pattern"
    )
    pattern_type: PatternType = Field(
        description="Category of pattern (ARCHITECTURAL, NAMING, etc.)"
    )
    description: str = Field(
        min_length=1, max_length=1000,
        description="Concise description of the pattern"
    )
    initial_relevance: float = Field(
        ge=0.0, le=1.0,
        description="Starting relevance [0.0-1.0]"
    )
    half_life_days: int = Field(
        ge=1, le=365,
        description="Number of days for relevance to decay to 50%"
    )
    reinforcement_count: int = Field(
        ge=0,
        description="Number of times this pattern has been reinforced"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="Timestamp when pattern was discovered"
    )
    last_reinforced_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="Timestamp of most recent reinforcement"
    )

    last_modified_by: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Agent ID that last modified (for CloudKit conflict resolution)"
    )
    last_modified_at: Optional[datetime] = Field(
        default=None,
        exclude=True,
        description="UTC timestamp of last modification"
    )

    def current_relevance(self, as_of: Optional[datetime] = None) -> float:
        """Calculate current relevance using half-life decay formula.

        Formula: relevance = initial_relevance × 0.5^(elapsed_days / half_life_days)

        Args:
            as_of: Reference timestamp for decay calculation. Defaults to now().

        Returns:
            Current relevance [0.0-1.0]
        """
        if as_of is None:
            as_of = datetime.utcnow()

        elapsed = as_of - self.created_at
        elapsed_days = elapsed.total_seconds() / 86400.0

        if elapsed_days < 0:
            return self.initial_relevance

        exponent = elapsed_days / self.half_life_days
        decay_factor = math.pow(0.5, exponent)
        current = self.initial_relevance * decay_factor

        return max(0.0, min(1.0, current))  # Clamp to [0.0, 1.0]

    def reinforce(self) -> None:
        """Boost pattern relevance via reinforcement.

        Increments reinforcement_count and applies multiplicative boost:
        initial_relevance *= (1 + reinforcement_count × 0.05)
        """
        self.reinforcement_count += 1
        boost_factor = 1.0 + (self.reinforcement_count * 0.05)
        self.initial_relevance = min(1.0, self.initial_relevance * boost_factor)
        self.last_reinforced_at = datetime.utcnow()
```

### 3. AuditEvent (`_models/audit_event.py`)

```python
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AuditOutcome(str, Enum):
    """Result of an audited action."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    HANDOFF = "handoff"
    VALIDATION_ERROR = "validation_error"

class AuditEvent(BaseModel):
    """Immutable audit trail entry.

    Represents a single agent action with full context snapshot.
    Frozen to prevent mutations after creation; append-only semantics enforced.
    """
    model_config = {"frozen": True}

    event_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this audit event"
    )
    timestamp: datetime = Field(
        description="UTC timestamp when event occurred"
    )
    agent_id: str = Field(
        description="Identifier of agent that triggered this event"
    )
    action: str = Field(
        description="Description of action taken (e.g., 'synthesize_architecture')"
    )
    outcome: AuditOutcome = Field(
        description="Result of the action (SUCCESS, FAILURE, PARTIAL, etc.)"
    )
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON snapshot of relevant context (findings, stage, etc.)"
    )
    duration_ms: int = Field(
        ge=0,
        description="Elapsed time in milliseconds for action execution"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional action-specific metadata"
    )

    def __init__(self, **data: Any) -> None:
        """Create immutable audit event. Validates on construction."""
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class AuditQuery(BaseModel):
    """Query specification for audit trail filtering.

    Supports filtering by agent, action, outcome, and timestamp range.
    """
    agent_id_filter: Optional[str] = Field(
        default=None,
        description="Filter to specific agent_id, or None for all agents"
    )
    action_filter: Optional[str] = Field(
        default=None,
        description="Filter to specific action substring"
    )
    outcome_filter: Optional[AuditOutcome] = Field(
        default=None,
        description="Filter to specific outcome"
    )
    timestamp_range: Optional[tuple[datetime, datetime]] = Field(
        default=None,
        description="(start, end) datetime range (inclusive) or None for all"
    )
    limit: int = Field(
        default=1000, ge=1, le=10000,
        description="Maximum number of events to return"
    )
```

### 4. Progressive Disclosure (`_context/progressive_disclosure.py`)

```python
from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

class DisclosureLevel(str, Enum):
    """Progressive disclosure level for context budget optimization."""
    L1 = "l1"     # ~500 tokens: keys + types
    L2 = "l2"     # ~300 tokens: keys + types + summaries
    L3 = "l3"     # ~3000 tokens: full JSON

@dataclass
class RenderedContext:
    """Output of progressive disclosure rendering."""
    level: DisclosureLevel
    content: str
    estimated_tokens: int

class ProgressiveDisclosure:
    """Renders findings/patterns at three disclosure levels.

    Implements token budget optimization by selectively omitting detail
    based on context window availability.
    """

    # Heuristic token counts (validated against tiktoken in tests)
    TOKEN_ESTIMATES = {
        DisclosureLevel.L1: 500,
        DisclosureLevel.L2: 300,
        DisclosureLevel.L3: 3000,
    }

    # Characters per token (approximation for GPT-4)
    CHARS_PER_TOKEN = 4

    def __init__(self, tokenizer_model: str = "gpt-4"):
        """Initialize disclosure engine.

        Args:
            tokenizer_model: Tokenizer model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        """
        self.tokenizer_model = tokenizer_model

    def render(
        self,
        findings: List[Dict[str, Any]],
        level: DisclosureLevel = DisclosureLevel.L3
    ) -> RenderedContext:
        """Render findings at specified disclosure level.

        Args:
            findings: List of finding dictionaries
            level: Disclosure level (L1, L2, L3)

        Returns:
            RenderedContext with content and estimated tokens
        """
        if level == DisclosureLevel.L1:
            return self._render_l1(findings)
        elif level == DisclosureLevel.L2:
            return self._render_l2(findings)
        else:  # L3
            return self._render_l3(findings)

    def _render_l1(self, findings: List[Dict[str, Any]]) -> RenderedContext:
        """L1: Entity keys and pattern types only."""
        lines = []
        for f in findings:
            key = f.get('key', 'unknown')
            f_type = f.get('type', 'unknown')
            lines.append(f"- {key} ({f_type})")

        content = "\n".join(lines)
        tokens = self.calculate_token_count(content)
        return RenderedContext(DisclosureLevel.L1, content, tokens)

    def _render_l2(self, findings: List[Dict[str, Any]]) -> RenderedContext:
        """L2: Keys, types, and 1-sentence summaries."""
        lines = []
        for f in findings:
            key = f.get('key', 'unknown')
            f_type = f.get('type', 'unknown')
            summary = f.get('summary', '')
            if summary and len(summary) > 100:
                summary = summary[:100] + "..."
            lines.append(f"- {key} ({f_type}): {summary}")

        content = "\n".join(lines)
        tokens = self.calculate_token_count(content)
        return RenderedContext(DisclosureLevel.L2, content, tokens)

    def _render_l3(self, findings: List[Dict[str, Any]]) -> RenderedContext:
        """L3: Full JSON representation."""
        content = json.dumps(findings, indent=2, default=str)
        tokens = self.calculate_token_count(content)
        return RenderedContext(DisclosureLevel.L3, content, tokens)

    def calculate_token_count(self, text: str) -> int:
        """Estimate token count for text.

        Uses heuristic: 4 characters ≈ 1 token (GPT-4 approximation)

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # In production, use tiktoken:
        # try:
        #     import tiktoken
        #     enc = tiktoken.encoding_for_model(self.tokenizer_model)
        #     return len(enc.encode(text))
        # except ImportError:
        #     pass

        # Fallback heuristic
        return max(1, len(text) // self.CHARS_PER_TOKEN)
```

### 5. ContextBudget and Monitor (`_context/budget_monitor.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class ContextBudget:
    """Tracks context window utilization."""

    def __init__(self, total_tokens: int = 8000):
        """Initialize budget.

        Args:
            total_tokens: Total available tokens (e.g., 8000 for GPT-4)
        """
        self.total_tokens = total_tokens
        self.used_tokens = 0
        self.timestamp = datetime.utcnow()

    def utilization_percent(self) -> float:
        """Return utilization as percentage [0.0-100.0]."""
        if self.total_tokens == 0:
            return 0.0
        return (self.used_tokens / self.total_tokens) * 100.0

    def remaining_tokens(self) -> int:
        """Return remaining tokens."""
        return max(0, self.total_tokens - self.used_tokens)

class ContextBudgetMonitor:
    """Monitors context usage and triggers budget actions.

    Thresholds:
    - 70%: Recommend downgrade to L2 (summaries)
    - 93%: Emit CRITICAL alert and trigger auto-handoff
    """

    THRESHOLD_WARN = 0.70
    THRESHOLD_CRITICAL = 0.93

    def check_and_downgrade(
        self,
        context: List[Dict[str, Any]],
        max_tokens: int = 8000
    ) -> Tuple[str, bool, Optional[str]]:
        """Check budget utilization and recommend disclosure level.

        Args:
            context: List of context items (findings, patterns, etc.)
            max_tokens: Total available tokens

        Returns:
            Tuple of (recommended_disclosure_level, trigger_handoff, alert_message)
            - disclosure_level: "L1", "L2", or "L3"
            - trigger_handoff: bool indicating if handoff should occur
            - alert_message: human-readable message or None
        """
        # Simple heuristic: 4 chars per token
        used = sum(len(str(item)) for item in context) // 4
        utilization = used / max_tokens

        if utilization >= self.THRESHOLD_CRITICAL:
            return (
                "L3",
                True,
                f"CRITICAL: Context at {utilization*100:.1f}% - initiating auto-handoff"
            )
        elif utilization >= self.THRESHOLD_WARN:
            return (
                "L2",
                False,
                f"WARNING: Context at {utilization*100:.1f}% - downgrading to L2"
            )
        else:
            return (
                "L3",
                False,
                None
            )
```

---

## Adapter Ports

### Ports Definition (`_adapters/ports.py` - additions)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional, Dict, Any
from ..._models.pipeline_state import PipelineState, PipelineStatus
from ..._models.experience_pattern import ExperiencePattern, PatternType
from ..._models.audit_event import AuditEvent, AuditQuery

class PipelineStatePort(ABC):
    """Port for PipelineState persistence (Session layer)."""

    @abstractmethod
    async def load(self, session_id: str) -> Optional[PipelineState]:
        """Load session state by ID.

        Args:
            session_id: Session identifier

        Returns:
            PipelineState if found, None otherwise
        """

    @abstractmethod
    async def save(self, state: PipelineState) -> None:
        """Persist session state.

        Args:
            state: PipelineState to save
        """

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session state by ID.

        Args:
            session_id: Session identifier
        """

class ExperiencePort(ABC):
    """Port for ExperiencePattern persistence (Experience layer)."""

    @abstractmethod
    async def list_patterns(
        self,
        min_relevance: float = 0.0
    ) -> List[ExperiencePattern]:
        """List all patterns with relevance >= min_relevance.

        Args:
            min_relevance: Minimum current relevance threshold

        Returns:
            List of ExperiencePattern objects
        """

    @abstractmethod
    async def save_pattern(self, pattern: ExperiencePattern) -> None:
        """Persist a pattern.

        Args:
            pattern: ExperiencePattern to save
        """

    @abstractmethod
    async def get_pattern(self, pattern_id: UUID) -> Optional[ExperiencePattern]:
        """Retrieve pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            ExperiencePattern if found, None otherwise
        """

    @abstractmethod
    async def query_by_type(
        self,
        pattern_type: PatternType
    ) -> List[ExperiencePattern]:
        """List all patterns of a specific type.

        Args:
            pattern_type: PatternType to filter by

        Returns:
            List of matching ExperiencePattern objects
        """

class AuditPort(ABC):
    """Port for AuditEvent persistence (Analytics layer). Append-only."""

    @abstractmethod
    async def append_event(self, event: AuditEvent) -> None:
        """Append a new audit event. No update/delete semantics.

        Args:
            event: AuditEvent to append
        """

    @abstractmethod
    async def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events with filtering and limit.

        Args:
            query: AuditQuery specification

        Returns:
            List of matching AuditEvent objects
        """
```

---

## CloudKit Adapter Architecture

### Overview

```
┌────────────────────────────────────────┐
│ CloudKitPipelineStateAdapter           │
│ (PipelineStatePort implementation)     │
├────────────────────────────────────────┤
│ - Wraps SwiftData + CloudKit SDK       │
│ - Serializes PipelineState to Record   │
│ - Conflict detection: last_modified_at │
│ - Offline-first: local write + async   │
└────────────────────────────────────────┘

        Similar for:
    - CloudKitExperienceAdapter
    - CloudKitAuditAdapter
```

**Conflict Resolution Logic** (implemented in each adapter):

```python
def resolve_conflict(local: Record, remote: Record) -> Record:
    """Last-writer-wins: most recent timestamp wins."""
    local_time = local.metadata.get('last_modified_at')
    remote_time = remote.metadata.get('last_modified_at')

    if remote_time > local_time:
        return remote
    elif local_time > remote_time:
        return local
    else:  # Timestamps equal: use agent_id tiebreaker (lexicographic)
        local_agent = local.metadata.get('last_modified_by', '')
        remote_agent = remote.metadata.get('last_modified_by', '')
        if remote_agent > local_agent:
            return remote
        return local
```

---

## Progressive Disclosure Algorithm

```python
def calculate_disclosure_level(
    context_tokens_used: int,
    total_tokens: int
) -> DisclosureLevel:
    """Determine optimal disclosure level based on budget."""
    utilization = context_tokens_used / total_tokens

    if utilization >= 0.93:
        return DisclosureLevel.L1  # Minimal disclosure
    elif utilization >= 0.70:
        return DisclosureLevel.L2  # Balanced disclosure
    else:
        return DisclosureLevel.L3  # Full disclosure
```

---

## CompositionRoot Integration

```python
class CompositionRoot:
    """Factory for all service dependencies."""

    def __init__(self, environment: str = "local"):
        self.environment = environment
        self._pipeline_state_port: Optional[PipelineStatePort] = None
        self._experience_port: Optional[ExperiencePort] = None
        self._audit_port: Optional[AuditPort] = None

    async def initialize_async(self) -> None:
        """Initialize async services (CloudKit adapters, etc.)."""
        if self.environment == "cloudkit":
            # Initialize CloudKit adapters
            self._pipeline_state_port = CloudKitPipelineStateAdapter()
            self._experience_port = CloudKitExperienceAdapter()
            self._audit_port = CloudKitAuditAdapter()
        else:  # local
            # Initialize local adapters
            self._pipeline_state_port = LocalPipelineStateAdapter()
            self._experience_port = LocalExperienceAdapter()
            self._audit_port = LocalAuditAdapter()

        # Perform any async setup
        if hasattr(self._pipeline_state_port, 'initialize'):
            await self._pipeline_state_port.initialize()

    def get_pipeline_state_port(self) -> PipelineStatePort:
        """Get PipelineStatePort instance."""
        if self._pipeline_state_port is None:
            raise RuntimeError("CompositionRoot not initialized; call initialize_async()")
        return self._pipeline_state_port

    def get_experience_port(self) -> ExperiencePort:
        """Get ExperiencePort instance."""
        if self._experience_port is None:
            raise RuntimeError("CompositionRoot not initialized; call initialize_async()")
        return self._experience_port

    def get_audit_port(self) -> AuditPort:
        """Get AuditPort instance."""
        if self._audit_port is None:
            raise RuntimeError("CompositionRoot not initialized; call initialize_async()")
        return self._audit_port
```

---

## Key Design Principles

1. **Domain models have zero framework imports** — Only standard library + Pydantic v2
2. **All I/O via ports** — No direct CloudKit calls in domain models
3. **Immutability where enforced** — AuditEvent is frozen; others mutable at API layer
4. **Offline-first writes** — Local state updated immediately, CloudKit push async
5. **Deterministic conflict resolution** — Last-writer-wins with timestamp + agent_id tiebreaker
6. **Progressive disclosure is automatic** — Engine decides level based on budget, not user
7. **Decay is deterministic** — Same pattern + reference time = same relevance value

---

## Performance Targets

| Operation | Target | Rationale |
|-----------|--------|-----------|
| Decay calc (10K patterns) | <100ms | Don't block context budget checks |
| Progressive disclosure rendering | <200ms | User-facing; must feel instant |
| CloudKit sync latency | <2s | Near-real-time cross-device |
| Audit write throughput | ≥100 events/sec | Support high-frequency logging |

