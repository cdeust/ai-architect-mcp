# Epic 1: Plan Interview Stage — Technical Specification

## Module Architecture

### Package Structure
```
ai_architect_mcp/
├── _interview/                    # NEW: Stage 4.5 implementation
│   ├── __init__.py
│   ├── models.py                  # Domain models (Pydantic)
│   ├── ports.py                   # DimensionEvaluator port
│   ├── scorers/
│   │   ├── __init__.py
│   │   ├── group_1.py             # D1-D5 scorers (structural)
│   │   ├── group_2.py             # D6-D10 scorers (quality)
│   │   └── base.py                # Scorer base class & orchestration
│   ├── gate.py                    # Gate decision logic
│   └── mcp_tools.py               # FastMCP tool registrations
├── _adapters/
│   ├── ports.py                   # Updated: +DimensionEvaluatorPort
├── _context/
│   └── stage_context.py           # No changes; already supports stage 45
├── _models/
│   └── __init__.py
└── _orchestrator/
    └── __init__.py                # Updated: insert stage 4.5
```

## Domain Models (Pydantic v2)

### 1. DimensionType Enum

```python
"""_interview/models.py — Part 1"""

from enum import Enum

class DimensionType(str, Enum):
    """10 dimensions for PRD interview gate assessment."""

    # Group 1: Structural Completeness
    SECTIONS_PRESENT = "D1-sections-present"
    HEADER_FORMAT = "D2-header-format"
    ID_CONSISTENCY = "D3-id-consistency"
    OUTLINE_FLOW = "D4-outline-flow"
    ARTIFACT_COHERENCE = "D5-artifact-coherence"

    # Group 2: Content Quality
    CLARITY_LEVEL = "D6-clarity-level"
    STAKEHOLDER_ALIGNMENT = "D7-stakeholder-alignment"
    REQUIREMENT_PRECISION = "D8-requirement-precision"
    ASSUMPTION_VALIDATION = "D9-assumption-validation"
    SUCCESS_METRICS = "D10-success-metrics"
```

### 2. DimensionScore Model

```python
"""_interview/models.py — Part 2"""

from pydantic import BaseModel, Field

class DimensionScore(BaseModel):
    """Score for a single dimension evaluation."""

    dimension_id: str = Field(
        description="Dimension identifier (D1-D10 or enum value)"
    )
    dimension_name: str = Field(
        description="Human-readable dimension name (e.g., 'Sections Present')"
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized score from 0.0 (fail) to 1.0 (perfect)"
    )
    pass: bool = Field(
        description="True if score >= relevant threshold (critical or advisory)"
    )
    findings: list[str] = Field(
        default_factory=list,
        description="List of findings/issues identified during scoring"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "dimension_id": "D1-sections-present",
                "dimension_name": "Sections Present",
                "score": 0.95,
                "pass": True,
                "findings": []
            }
        }
```

### 3. InterviewConfig Model

```python
"""_interview/models.py — Part 3"""

from pydantic import BaseModel, Field, model_validator

class InterviewConfig(BaseModel):
    """Configuration for interview gate execution."""

    critical_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum score for critical dimensions (blocks gate if violated)"
    )
    advisory_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum score for advisory dimensions (informs decision)"
    )
    timeout_seconds: int = Field(
        default=60,
        gt=0,
        description="Maximum time (seconds) to evaluate all 10 dimensions"
    )
    dimensions_enabled: list[str] = Field(
        default_factory=lambda: [d.value for d in DimensionType],
        description="List of dimension IDs to evaluate (default: all)"
    )

    @model_validator(mode="after")
    def validate_thresholds_ordered(self) -> "InterviewConfig":
        """Ensure critical >= advisory threshold."""
        if self.critical_threshold < self.advisory_threshold:
            msg = (
                f"critical_threshold ({self.critical_threshold}) must be >= "
                f"advisory_threshold ({self.advisory_threshold})"
            )
            raise ValueError(msg)
        return self
```

### 4. GateDecision Enum

```python
"""_interview/models.py — Part 4"""

from enum import Enum

class GateDecision(str, Enum):
    """Final verdict from the interview gate."""

    APPROVED = "approved"
    """All critical dimensions pass threshold; PRD is ready for review."""

    PROVISIONAL = "provisional"
    """All critical pass but some advisory dimensions below threshold.
    PRD advances but with flagged improvement areas."""

    REJECTED = "rejected"
    """One or more critical dimensions below threshold.
    PRD must be regenerated (Stage 4 re-entry)."""
```

### 5. InterviewResult Model

```python
"""_interview/models.py — Part 5"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

class InterviewResult(BaseModel):
    """Complete result of an interview gate execution."""

    finding_id: str = Field(
        description="Finding identifier (e.g., FIND-001)"
    )
    stage_id: int = Field(
        default=45,
        description="Stage ID (45 for Stage 4.5 Plan Interview)"
    )
    dimension_scores: list[DimensionScore] = Field(
        description="Scores for all evaluated dimensions"
    )
    gate_decision: GateDecision = Field(
        description="Final gate verdict (APPROVED/PROVISIONAL/REJECTED)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of interview execution"
    )
    scored_by: str = Field(
        default="stage-4.5-scorer",
        description="Component that scored the dimensions"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "finding_id": "FIND-001",
                "stage_id": 45,
                "dimension_scores": [
                    {
                        "dimension_id": "D1-sections-present",
                        "dimension_name": "Sections Present",
                        "score": 0.95,
                        "pass": True,
                        "findings": []
                    }
                ],
                "gate_decision": "approved",
                "created_at": "2025-03-14T12:00:00Z",
                "scored_by": "stage-4.5-scorer"
            }
        }
```

## Ports (Abstract Interfaces)

### DimensionEvaluator Port

```python
"""_interview/ports.py"""

from abc import ABC, abstractmethod
from ai_architect_mcp._interview.models import (
    DimensionScore,
    InterviewConfig,
)

class DimensionEvaluatorPort(ABC):
    """Port for dimension evaluation implementations.

    Concrete implementations evaluate a single dimension of a PRD artifact
    and return a normalized score.
    """

    @abstractmethod
    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Evaluate a single dimension of a PRD artifact.

        Args:
            prd_artifact: PRD content as dict (from Stage 4 artifact)
            dimension_id: Dimension to evaluate (must be in DimensionType)
            config: Interview configuration with thresholds

        Returns:
            DimensionScore with score (0.0-1.0) and findings

        Raises:
            ValueError: If dimension_id is invalid or artifact malformed
            TimeoutError: If evaluation exceeds config.timeout_seconds
        """
        ...
```

## Scorer Implementations

### Dimension Definitions & Pass Thresholds

| Dimension | Type | Critical? | Default Threshold | Algorithm Summary |
|-----------|------|-----------|-------------------|-------------------|
| D1: Sections Present | Group 1 | Yes | 0.8 | Count required sections / 9 |
| D2: Header Format | Group 1 | Yes | 0.8 | Proportion of valid markdown headers |
| D3: ID Consistency | Group 1 | Yes | 0.8 | Matching IDs to FR-E1-XXX pattern / total |
| D4: Outline Flow | Group 1 | Yes | 0.8 | 1.0=correct order, 0.5=scrambled, 0.0=missing |
| D5: Artifact Coherence | Group 1 | No | 0.6 | shared_terms / total_unique_terms across sections |
| D6: Clarity Level | Group 2 | Yes | 0.7 | Penalty for long sentences (>20 words) and passive voice |
| D7: Stakeholder Alignment | Group 2 | No | 0.6 | Stories with stakeholder mentions / total stories |
| D8: Requirement Precision | Group 2 | Yes | 0.7 | Testable requirements / total; penalize vague language |
| D9: Assumption Validation | Group 2 | No | 0.6 | 1.0 if ≥3 assumptions OR "No assumptions" statement |
| D10: Success Metrics | Group 2 | Yes | 0.75 | Tables with all 4 columns / total KPI tables |

### Group 1 Scorers (Structural)

```python
"""_interview/scorers/group_1.py"""

from ai_architect_mcp._interview.models import (
    DimensionScore,
    InterviewConfig,
    DimensionType,
)
from ai_architect_mcp._interview.ports import DimensionEvaluatorPort

class SectionsPresentScorer(DimensionEvaluatorPort):
    """D1: SECTIONS_PRESENT scorer."""

    REQUIRED_SECTIONS = [
        "Overview",
        "Requirements",
        "User Stories",
        "Technical",
        "Acceptance",
        "Roadmap",
        "JIRA",
        "Tests",
        "Verification",
    ]

    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Score presence of all required sections."""
        sections_found = []
        if isinstance(prd_artifact.get("sections"), list):
            for section in prd_artifact["sections"]:  # type: ignore
                if isinstance(section, dict) and "name" in section:
                    sections_found.append(section["name"])

        count_present = sum(
            1 for req_section in self.REQUIRED_SECTIONS
            if any(req_section.lower() in found.lower() for found in sections_found)
        )
        score = count_present / len(self.REQUIRED_SECTIONS)
        missing = [s for s in self.REQUIRED_SECTIONS if s not in sections_found]

        return DimensionScore(
            dimension_id=dimension_id or DimensionType.SECTIONS_PRESENT.value,
            dimension_name="Sections Present",
            score=score,
            pass=score >= config.critical_threshold,
            findings=[f"Missing section: {s}" for s in missing] if missing else [],
        )


class HeaderFormatScorer(DimensionEvaluatorPort):
    """D2: HEADER_FORMAT scorer."""

    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Score markdown header formatting."""
        content = prd_artifact.get("content", "")
        if not isinstance(content, str):
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.HEADER_FORMAT.value,
                dimension_name="Header Format",
                score=0.0,
                pass=False,
                findings=["PRD content is not a string"],
            )

        lines = content.split("\n")
        header_count = 0
        malformed_count = 0

        for line in lines:
            if line.startswith("#"):
                header_count += 1
                if not line.startswith(("# ", "## ")):
                    malformed_count += 1

        if header_count == 0:
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.HEADER_FORMAT.value,
                dimension_name="Header Format",
                score=0.0,
                pass=False,
                findings=["No markdown headers found"],
            )

        score = max(0.0, 1.0 - (malformed_count * 0.1))
        return DimensionScore(
            dimension_id=dimension_id or DimensionType.HEADER_FORMAT.value,
            dimension_name="Header Format",
            score=score,
            pass=score >= config.critical_threshold,
            findings=[f"{malformed_count} malformed headers found"] if malformed_count > 0 else [],
        )


class IDConsistencyScorer(DimensionEvaluatorPort):
    """D3: ID_CONSISTENCY scorer."""

    ID_PATTERNS = [
        r"FR-E1-\d{3}",
        r"STORY-E1-\d{1,2}",
        r"AC-E1-\d{3}",
    ]

    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Score consistency of requirement/story/acceptance criterion IDs."""
        import re

        content = prd_artifact.get("content", "") or ""
        if not isinstance(content, str):
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.ID_CONSISTENCY.value,
                dimension_name="ID Consistency",
                score=0.0,
                pass=False,
                findings=["Content not a string"],
            )

        all_ids = []
        for pattern in self.ID_PATTERNS:
            all_ids.extend(re.findall(pattern, content))

        if not all_ids:
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.ID_CONSISTENCY.value,
                dimension_name="ID Consistency",
                score=0.0,
                pass=False,
                findings=["No recognized IDs found"],
            )

        consistent_ids = [
            id_ for id_ in all_ids
            if any(re.match(pattern, id_) for pattern in self.ID_PATTERNS)
        ]
        score = len(consistent_ids) / len(all_ids) if all_ids else 0.0

        return DimensionScore(
            dimension_id=dimension_id or DimensionType.ID_CONSISTENCY.value,
            dimension_name="ID Consistency",
            score=score,
            pass=score >= config.critical_threshold,
            findings=[] if score >= config.critical_threshold else [
                f"Found {len(all_ids) - len(consistent_ids)} non-conforming IDs"
            ],
        )


class OutlineFlowScorer(DimensionEvaluatorPort):
    """D4: OUTLINE_FLOW scorer."""

    SECTION_ORDER = [
        "overview",
        "requirements",
        "user stories",
        "technical",
        "acceptance",
        "roadmap",
        "jira",
        "tests",
        "verification",
    ]

    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Score section order and flow."""
        sections = prd_artifact.get("sections", [])
        if not isinstance(sections, list) or not sections:
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.OUTLINE_FLOW.value,
                dimension_name="Outline Flow",
                score=0.0,
                pass=False,
                findings=["No sections found"],
            )

        section_names = [
            str(s.get("name", "")).lower()
            for s in sections
            if isinstance(s, dict)
        ]

        # Check if all required sections present
        all_present = all(
            any(req.lower() in name for name in section_names)
            for req in self.SECTION_ORDER
        )

        if not all_present:
            missing = [
                req for req in self.SECTION_ORDER
                if not any(req.lower() in name for name in section_names)
            ]
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.OUTLINE_FLOW.value,
                dimension_name="Outline Flow",
                score=0.0,
                pass=False,
                findings=[f"Missing sections: {', '.join(missing)}"],
            )

        # Find positions and check order
        positions = []
        for req_section in self.SECTION_ORDER:
            for i, name in enumerate(section_names):
                if req_section.lower() in name:
                    positions.append(i)
                    break

        is_ordered = positions == sorted(positions)
        score = 1.0 if is_ordered else 0.5

        return DimensionScore(
            dimension_id=dimension_id or DimensionType.OUTLINE_FLOW.value,
            dimension_name="Outline Flow",
            score=score,
            pass=score >= config.critical_threshold,
            findings=[] if is_ordered else ["Sections out of logical order"],
        )


class ArtifactCoherenceScorer(DimensionEvaluatorPort):
    """D5: ARTIFACT_COHERENCE scorer."""

    async def evaluate(
        self,
        prd_artifact: dict[str, object],
        dimension_id: str,
        config: InterviewConfig,
    ) -> DimensionScore:
        """Score semantic coherence across artifact sections."""
        import re

        def extract_keywords(text: str) -> set[str]:
            """Extract non-trivial words from text."""
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            stop_words = {'that', 'this', 'from', 'with', 'have', 'will', 'must', 'shall'}
            return {w for w in words if w not in stop_words}

        content = prd_artifact.get("content", "")
        if not content or not isinstance(content, str):
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.ARTIFACT_COHERENCE.value,
                dimension_name="Artifact Coherence",
                score=0.5,
                pass=True,  # Default to pass for partial data
                findings=["No content to analyze"],
            )

        # Split into major sections and extract keywords
        section_keywords = []
        for section in ["overview", "requirements", "technical"]:
            if section in content.lower():
                # Crude extraction: content between section header and next section
                idx = content.lower().find(section)
                if idx != -1:
                    end_idx = min(
                        (content.lower().find(s, idx + 1) for s in ["overview", "requirements", "technical", "acceptance"]
                         if content.lower().find(s, idx + 1) > idx),
                        default=len(content)
                    )
                    section_text = content[idx:end_idx]
                    section_keywords.append(extract_keywords(section_text))

        if len(section_keywords) < 2:
            return DimensionScore(
                dimension_id=dimension_id or DimensionType.ARTIFACT_COHERENCE.value,
                dimension_name="Artifact Coherence",
                score=0.6,
                pass=True,
                findings=["Insufficient sections for coherence analysis"],
            )

        # Calculate shared terms across sections
        all_keywords = set().union(*section_keywords)
        shared = set.intersection(*section_keywords) if section_keywords else set()

        score = len(shared) / len(all_keywords) if all_keywords else 0.5

        return DimensionScore(
            dimension_id=dimension_id or DimensionType.ARTIFACT_COHERENCE.value,
            dimension_name="Artifact Coherence",
            score=score,
            pass=score >= config.advisory_threshold,
            findings=[] if score > 0.5 else ["Low keyword overlap between sections"],
        )
```

### Group 2 Scorers (Quality) — Implementation Summary

Group 2 scorers follow similar patterns to Group 1 but focus on prose quality, stakeholder alignment, precision, assumptions, and success metrics:

- **D6 (CLARITY_LEVEL)**: Parse prose, count sentence length (<20 words target), detect passive voice usage, apply -0.05 penalty per violation
- **D7 (STAKEHOLDER_ALIGNMENT)**: Check user stories for stakeholder keywords (e.g., "As a", persona names), score = stories_with_stakeholder / total
- **D8 (REQUIREMENT_PRECISION)**: Detect vague keywords ("shall be", "might", "consider"), penalize their presence
- **D9 (ASSUMPTION_VALIDATION)**: Search for explicit "Assumption:", "Assumes:", or "No assumptions" statements; score = 1.0 if found, 0.0 otherwise
- **D10 (SUCCESS_METRICS)**: Scan for KPI tables with 4 required columns (Baseline, Target, Measurement, Business Impact), score = complete_tables / total_tables

(Full implementations available in `_interview/scorers/group_2.py`, following same pattern as Group 1)

## Gate Logic

```python
"""_interview/gate.py"""

from ai_architect_mcp._interview.models import (
    InterviewResult,
    DimensionScore,
    GateDecision,
    InterviewConfig,
)

class InterviewGate:
    """Interview gate decision logic."""

    @staticmethod
    def decide(
        dimension_scores: list[DimensionScore],
        config: InterviewConfig,
    ) -> GateDecision:
        """Determine gate verdict based on dimension scores.

        Args:
            dimension_scores: All 10 dimension scores
            config: Interview configuration with thresholds

        Returns:
            GateDecision (APPROVED, PROVISIONAL, or REJECTED)

        Logic:
            - APPROVED: All critical dimensions score >= critical_threshold
                        AND all advisory >= advisory_threshold
            - PROVISIONAL: All critical >= critical_threshold
                           BUT some advisory < advisory_threshold
            - REJECTED: Any critical dimension < critical_threshold
        """

        # Classify dimensions as critical or advisory
        CRITICAL_DIMS = {
            "D1-sections-present",
            "D2-header-format",
            "D3-id-consistency",
            "D4-outline-flow",
            "D6-clarity-level",
            "D8-requirement-precision",
            "D10-success-metrics",
        }
        ADVISORY_DIMS = {
            "D5-artifact-coherence",
            "D7-stakeholder-alignment",
            "D9-assumption-validation",
        }

        critical_scores = [
            s for s in dimension_scores
            if s.dimension_id in CRITICAL_DIMS
        ]
        advisory_scores = [
            s for s in dimension_scores
            if s.dimension_id in ADVISORY_DIMS
        ]

        # Check critical threshold
        all_critical_pass = all(
            s.score >= config.critical_threshold
            for s in critical_scores
        )

        # Check advisory threshold
        all_advisory_pass = all(
            s.score >= config.advisory_threshold
            for s in advisory_scores
        )

        if not all_critical_pass:
            return GateDecision.REJECTED
        elif all_advisory_pass:
            return GateDecision.APPROVED
        else:
            return GateDecision.PROVISIONAL
```

## StageContext Integration

```python
"""Stage 4.5 artifact read/write pattern"""

# Stage 4.5 reads PRD from Stage 4
stage_4_artifact = await context.load_artifact(stage_id=4, finding_id=finding_id)
prd_content = stage_4_artifact.get("content", {})

# Stage 4.5 scores and writes result
interview_result = InterviewResult(
    finding_id=finding_id,
    stage_id=45,
    dimension_scores=dimension_scores,
    gate_decision=gate_decision,
)
await context.save_artifact(
    stage_id=45,
    finding_id=finding_id,
    artifact=interview_result.model_dump(mode="json"),
)

# Stage 5 retrieves both Stage 4 and Stage 4.5 artifacts
prd_artifact = await context.load_artifact(stage_id=4, finding_id=finding_id)
interview_result = await context.load_artifact(stage_id=45, finding_id=finding_id)
```

## MCP Tool Signatures

```python
"""_interview/mcp_tools.py"""

import json
from ai_architect_mcp._interview.models import InterviewResult, InterviewConfig
from ai_architect_mcp._interview.scorers.base import Scorer
from ai_architect_mcp._context.stage_context import StageContext

class InterviewMCPTools:
    """FastMCP tool registrations for Stage 4.5."""

    def __init__(self, context: StageContext, scorer: Scorer):
        """Initialize with dependencies."""
        self.context = context
        self.scorer = scorer

    async def score_dimension(
        self,
        finding_id: str,
        stage_id: int,
        dimension_id: str,
        prd_content: str,
    ) -> dict:
        """Score a single dimension.

        Tool: ai_architect_score_dimension

        Args:
            finding_id: Finding identifier (e.g., "FIND-001")
            stage_id: Stage ID (typically 4 for PRD input, 45 for interview)
            dimension_id: Dimension to score (D1-D10)
            prd_content: PRD content as JSON string

        Returns:
            DimensionScore as dict
        """
        try:
            prd_artifact = json.loads(prd_content)
            config = InterviewConfig()
            dimension_score = await self.scorer.evaluate_single(
                prd_artifact, dimension_id, config
            )
            return dimension_score.model_dump(mode="json")
        except Exception as e:
            return {
                "error": str(e),
                "dimension_id": dimension_id,
                "score": 0.0,
                "pass": False,
            }

    async def run_interview_gate(
        self,
        finding_id: str,
        stage_id: int,
    ) -> dict:
        """Run full interview gate for a finding.

        Tool: ai_architect_run_interview_gate

        Args:
            finding_id: Finding identifier
            stage_id: Input stage ID (typically 4)

        Returns:
            InterviewResult as dict with gate_decision
        """
        try:
            # Load PRD from Stage 4
            prd_artifact = await self.context.load_artifact(
                stage_id=4, finding_id=finding_id
            )

            # Run interview gate
            config = InterviewConfig()
            interview_result = await self.scorer.evaluate_all(
                prd_artifact, finding_id, config
            )

            # Persist result to Stage 4.5
            await self.context.save_artifact(
                stage_id=45,
                finding_id=finding_id,
                artifact=interview_result.model_dump(mode="json"),
            )

            return interview_result.model_dump(mode="json")
        except Exception as e:
            return {
                "error": str(e),
                "finding_id": finding_id,
                "gate_decision": "rejected",
            }

    async def query_interview_results(
        self,
        finding_id: str,
    ) -> list[dict]:
        """Query interview results for a finding.

        Tool: ai_architect_query_interview_results

        Args:
            finding_id: Finding identifier

        Returns:
            List of InterviewResult dicts in chronological order
        """
        try:
            results = await self.context.query_artifacts(
                finding_id=finding_id,
                query="interview stage 4.5 dimensions",
            )
            return [r for r in results if r.get("stage_id") == 45]
        except Exception as e:
            return [{"error": str(e)}]
```

## Composition Root

```python
"""_composition.py updates for Stage 4.5"""

from ai_architect_mcp._interview.models import InterviewConfig
from ai_architect_mcp._interview.scorers.base import Scorer
from ai_architect_mcp._interview.scorers.group_1 import (
    SectionsPresentScorer,
    HeaderFormatScorer,
    IDConsistencyScorer,
    OutlineFlowScorer,
    ArtifactCoherenceScorer,
)
from ai_architect_mcp._interview.scorers.group_2 import (
    ClarityLevelScorer,
    StakeholderAlignmentScorer,
    RequirementPrecisionScorer,
    AssumptionValidationScorer,
    SuccessMetricsScorer,
)

def setup_interview_stage(context_port):
    """Initialize Stage 4.5 components."""

    # Create dimension evaluators
    evaluators = {
        "D1-sections-present": SectionsPresentScorer(),
        "D2-header-format": HeaderFormatScorer(),
        "D3-id-consistency": IDConsistencyScorer(),
        "D4-outline-flow": OutlineFlowScorer(),
        "D5-artifact-coherence": ArtifactCoherenceScorer(),
        "D6-clarity-level": ClarityLevelScorer(),
        "D7-stakeholder-alignment": StakeholderAlignmentScorer(),
        "D8-requirement-precision": RequirementPrecisionScorer(),
        "D9-assumption-validation": AssumptionValidationScorer(),
        "D10-success-metrics": SuccessMetricsScorer(),
    }

    # Create scorer orchestrator
    config = InterviewConfig()
    scorer = Scorer(evaluators, config)

    # Register MCP tools
    from ai_architect_mcp._interview.mcp_tools import InterviewMCPTools
    tools = InterviewMCPTools(context_port, scorer)

    return scorer, tools
```

---

**Document**: Technical Specification | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
