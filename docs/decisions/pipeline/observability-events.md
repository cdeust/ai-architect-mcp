# STG-012: Pipeline Observability Event Infrastructure

**Status:** Accepted
**Date:** 2026-03
**Author:** AI Architect
**Replaces:** —

---

## 1. Observation

Pipeline execution produces no structured real-time signals. Debugging
relies on text logs which cannot be parsed, visualized, or correlated
across stages. When a pipeline run fails at Stage 7, there is no way to
trace which tool calls, HOR rule evaluations, or gate decisions led to
the failure without manually reading log output.

During 23 pipeline runs in March 2026:
- Average debugging time per failure: 12 minutes (manual log search)
- 4 failures were misattributed to the wrong stage due to log interleaving
- Gate pass/fail outcomes were only visible in tool return values, not logged

## 2. Problem

**Who:** Engineers debugging pipeline failures and tuning pipeline behaviour.
**What:** No structured, machine-readable event stream for pipeline execution.
**How often:** Every pipeline run produces zero observability events.
**Cost:** 12 minutes average per failure diagnosis; misattribution of 17% of
failures to wrong pipeline stage; no data for pipeline performance analysis.

Falsifiable: After implementation, every pipeline tool call, HOR rule
evaluation, gate decision, and OODA checkpoint must produce a structured
PipelineEvent that validates against the schema and can be consumed by
external visualization tools.

## 3. Solution

### Architecture

```
Tool call → @observe_tool_call decorator → ObservabilityPort.emit()
                                                  ↓
                                   CompositeObservabilityAdapter
                                    ↙                    ↘
                     FileObservabilityAdapter    SSEObservabilityAdapter
                     (brain-trace.jsonl)         (HTTP SSE, port 0)
```

### Components (7 files, `_observability/` module)

| File | Purpose |
|------|---------|
| `event_types.py` | `EventType(str, Enum)` — 12 types; `PipelineEvent(BaseModel, frozen=True)` |
| `observability_port.py` | `ObservabilityPort(ABC)` — emit/flush/close |
| `file_adapter.py` | JSONL append to `brain-trace.jsonl` |
| `sse_adapter.py` | HTTP SSE on ephemeral port, no-op when no clients |
| `composite_adapter.py` | Multiplexes N adapters, error-isolated |
| `instrumentation.py` | `observe_tool_call` decorator + `emit_artifact_saved` + `emit_hor_rule` |
| `__init__.py` | Re-exports public API |

### 12 Event Types

`STAGE_STARTED`, `STAGE_COMPLETED`, `STAGE_FAILED`, `TOOL_CALLED`,
`TOOL_COMPLETED`, `TOOL_FAILED`, `ARTIFACT_SAVED`, `HOR_RULE_EVALUATED`,
`GATE_EVALUATED`, `OODA_CHECKPOINT`, `CONTEXT_LOADED`, `PIPELINE_ERROR`

### Integration Points

- **Composition root:** `create_observability()` factory method
- **Stage context:** Optional `observability` param, emits `ARTIFACT_SAVED` on save
- **HOR engine:** Async migration, emits `HOR_RULE_EVALUATED` per rule
- **All 43 tools:** `@observe_tool_call` decorator emits `TOOL_CALLED/COMPLETED/FAILED`
- **POST_TOOL hook:** `observe_events.py` emits `GATE_EVALUATED` for gate tools
- **OODA tool:** `ai_architect_emit_ooda_checkpoint` for decision point visibility

### Interface Contract

```python
class ObservabilityPort(ABC):
    async def emit(self, event: PipelineEvent) -> None: ...
    async def flush(self) -> None: ...
    async def close(self) -> None: ...
```

## 4. Justification

| Alternative | Why rejected |
|-------------|-------------|
| OpenTelemetry integration | External dependency; violates zero-dependency policy for MCP server |
| Structured logging (JSON logger) | Cannot be consumed in real-time by visualization; conflates observability with application logging |
| Direct file writes per tool | No abstraction; violates port/adapter pattern; cannot add SSE later |
| Synchronous event emission | Blocks tool execution; codebase mandates async throughout |
| Global singleton port | Matches `_app.py` pattern but prevents testing; chose module-level setter instead |

## 5. Reproducibility

### Environment
- Python 3.12+, pydantic 2.x, pytest, pytest-asyncio

### Validation Steps

1. Run observability unit tests:
   ```bash
   python3 -m pytest tests/test_observability/ -v
   ```
   Expected: 32 tests pass.

2. Validate fixture covers all 12 event types:
   ```bash
   python3 -m pytest tests/test_observability/test_event_types.py -v
   ```

3. Run full test suite (no regressions from async migration):
   ```bash
   python3 -m pytest tests/ -v
   ```
   Expected: 587 tests pass.

4. Verify brain-trace-sample.jsonl validates:
   ```bash
   python3 -c "
   import json
   from ai_architect_mcp._observability.event_types import PipelineEvent
   for line in open('tests/fixtures/brain-trace-sample.jsonl'):
       PipelineEvent.model_validate(json.loads(line))
   print('All lines valid')
   "
   ```

## 6. Verification Data

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Structured events per pipeline run | 0 | 12 types, ~200+ events | +200 |
| Observability test count | 0 | 32 | +32 |
| Full test suite size | 555 | 587 | +32 |
| Full test suite pass rate | 100% | 100% | 0% regression |
| Full test suite duration | 4.2s | 4.7s | +0.5s (12% overhead) |
| Tool instrumentation coverage | 0/43 tools | 43/43 tools | 100% |
| HOR engine async migration | sync | async | No regressions |

---

*This document follows the AI Architect 6-point decision framework,
aligned with MIT Applied AI & Data Science reproducibility standards.*
