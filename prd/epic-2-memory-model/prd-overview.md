# Epic 2: Four-Layer Memory Model — Product Requirements Document

**Status:** In Planning
**Date:** 2026-03-14
**Epic ID:** EPIC-E2
**Version:** 1.0

---

## Executive Summary

Epic 2 implements a **four-layer context memory system** that separates concerns across temporal and functional boundaries, enabling AI Architect to maintain coherent multi-agent reasoning across sessions, projects, and long-running synthesis tasks. The four layers are:

1. **Session** (PipelineState): Current agent execution state, stage progress, active findings, skill versions
2. **Project** (Finding + StageOutput): Structured outputs from each synthesis stage, persisted to Project scope
3. **Experience** (ExperiencePattern): Learned patterns with biological half-life decay, reinforced by agent interactions
4. **Analytics** (AuditEvent): Immutable append-only trail for compliance, debugging, and pattern discovery

This epic also introduces **progressive disclosure** (3 levels: ~500t, ~300t, ~3Kt token budgets) to optimize context window usage, **context budget monitoring** (70% trigger → summaries, 93% → auto-handoff), and **CloudKit/iCloud sync** to enable cross-device memory coherence.

---

## Problem Statement

- **Current State**: AI Architect stores findings and stage outputs per-project but has no semantic memory layer across projects or decay mechanism for stale patterns
- **Pain Point 1**: Agents cannot learn from repeated synthesis patterns; each project reinvents the same architectural insights
- **Pain Point 2**: Long-running sessions consume unbounded context; no principled way to compress or summarize accumulated knowledge
- **Pain Point 3**: Multi-agent handoffs lack structured context; agents context-switch without semantic grounding
- **Pain Point 4**: CloudKit-native workflows (iOS/macOS) cannot sync memory across devices; users must re-create findings on each device

---

## Solution Overview

### Four-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│ Session (PipelineState)                          │
│ current_stage, active_finding, agent_id         │
└─────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────┐
│ Project (Finding + StageOutput)                  │
│ Structured per-stage synthesis outputs          │
└─────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────┐
│ Experience (ExperiencePattern)                   │
│ Learned patterns with half-life decay           │
└─────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────┐
│ Analytics (AuditEvent)                           │
│ Immutable append-only compliance trail          │
└─────────────────────────────────────────────────┘
```

### Progressive Disclosure (Context Budget)

- **Level 1** (~500 tokens): Entity keys, patterns with top-2 keywords
- **Level 2** (~300 tokens): Keys + summaries (1 sentence per finding)
- **Level 3** (~3,000 tokens): Full findings + stage outputs

### CloudKit Sync

- Bidirectional sync for all four layers (Session, Project, Experience, Analytics)
- Last-writer-wins conflict resolution
- Sync latency target: <2 seconds
- Offline-first: all writes to local store, async push to CloudKit

---

## Objectives & Key Results

| Objective | Key Result | Target |
|-----------|-----------|--------|
| Agents learn from experience | Patterns reinforced across ≥3 projects | 80% of synthetic findings reused |
| Context stays within budget | 70% threshold → summaries, 93% → auto-handoff | ≤2s budget recalculation |
| Cross-device coherence | CloudKit sync propagates all layers | <2s latency, last-writer-wins |
| Audit compliance | 100% of agent actions logged immutably | ≥100 events/sec write throughput |

---

## Scope

### In Scope ✓
- PipelineState model (Agent execution state)
- ExperiencePattern model + half-life decay calculation
- AuditEvent model (immutable, append-only)
- Three new adapter ports (PipelineStatePort, ExperiencePort, AuditPort)
- CloudKit adapters for all three ports
- Conflict resolution (last-writer-wins with timestamp-based ordering)
- Progressive disclosure engine (3 levels, token budget calculation)
- Context budget monitor (70%/93% thresholds, auto-handoff trigger)
- Composition root updates to inject memory services
- Integration tests for cross-device sync

### Out of Scope ✗
- Real-time multi-user editing (offline-first only)
- Machine learning on experience patterns (heuristic decay only)
- Blockchain/cryptographic audit trail (CloudKit signature sufficient)
- Custom conflict resolution strategies (last-writer-wins only)
- Mobile UI for memory visualization (backend only)

---

## Team & Timeline

| Role | Count | Notes |
|------|-------|-------|
| Tech Lead / Architect | 1 | Designs ports, CloudKit adapter architecture |
| Backend Engineer | 1 | Implements models, adapters, sync logic |
| **AI / Automation** | +1 | Code generation, test suite automation |
| **Total Staffing** | **1 + AI** | |

| Phase | Duration | Target SP |
|-------|----------|-----------|
| Sprint 0 (CloudKit Prototype) | 1 week | 5 SP |
| Sprint 1 (Domain Models) | 2 weeks | 16 SP |
| Sprint 2 (Ports + Local Adapters) | 2 weeks | 11 SP |
| Sprint 3 (CloudKit Adapters) | 2 weeks | 16 SP |
| Sprint 4 (Progressive Disclosure + Budget) | 2 weeks | 13 SP |
| Sprint 5 (Integration Tests + Docs) | 2 weeks | 8 SP |
| **Total** | **9–12 weeks** | **~76 SP (XL)** |

---

## Success Criteria

1. **Completeness**: All 9 files of PRD in place; 15+ user stories with detailed ACs
2. **Architecture**: Domain models have zero framework imports; all I/O via ports
3. **Test Coverage**: ≥85% line coverage for domain models; all acceptance criteria verified by pytest
4. **Performance**: Decay calculation <100ms for 10K patterns; sync latency <2s
5. **CloudKit Integration**: Bidirectional sync functional; last-writer-wins conflict resolution verified
6. **Progressive Disclosure**: All 3 levels emit correct token counts; 70%/93% thresholds trigger correctly
7. **Immutability**: AuditEvent append-only enforcement verified; no update/delete port methods

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| CloudKit quota limits for large-scale audit trails | Medium | High | Sprint 0 prototype validates assumptions; implement filtering on read path |
| Decay calculation becomes bottleneck | Low | Medium | Vectorize with numpy if needed; benchmark in Sprint 4 |
| Conflict resolution loses concurrent edits | Low | Medium | Last-writer-wins + timestamp ordering; document trade-off |
| Progressive disclosure token counting inaccuracy | Medium | Low | Encode actual tokenizer model; validate against GPT-4 counting |

---

## Dependencies & Prerequisites

- **Upstream**: Pydantic v2 models established (ADR-003), ports pattern in place (ADR-004)
- **External**: CloudKit Account (Apple Developer Program required for testing)
- **Assumptions**: iCloud/CloudKit available on target platforms; offline-first architecture compatible with existing StageContext

---

## Success Handoff Criteria

1. All 9 PRD files complete with consistent AC IDs, SP estimates, and cross-references
2. Domain models compiling; all fields typed with Pydantic v2 validators
3. Adapter ports defined; composition root updated to inject memory services
4. CloudKit adapter prototype working (mock or real); sync latency measured
5. Progressive disclosure and budget monitor logic implemented and tested
6. Full test suite passing with ≥85% coverage
7. Verification document with explicit verdicts (PASS / SPEC-COMPLETE / NEEDS-RUNTIME)

---

## Related Documents

- **ADR-007**: Experience Pattern Decay Model
- **ADR-004**: Ports & Adapters Architecture
- **ADR-003**: Pydantic v2 Models
- **Epic 1 PRD**: Synthesis Pipeline (prerequisite)
