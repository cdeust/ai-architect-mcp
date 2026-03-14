# Decision Documents

This directory contains all architectural, algorithmic, and pipeline decision documents for AI Architect. Every document follows the **6-point decision framework**, aligned with MIT Applied AI & Data Science standards for reproducible research.

## Why this framework

Software architecture decisions are often recorded as preferences — "we chose X because it felt right." This is insufficient for a system that must be maintained, extended, and verified by engineers who were not present when the decision was made.

The 6-point framework requires that every decision be grounded in observation, specify a falsifiable problem, document a reproducible solution, justify itself against rejected alternatives, provide exact reproduction steps, and include verification data proving the solution works. A document missing any of these six points is incomplete.

This standard exists because:

1. **Observation without data is opinion.** If you cannot cite what you measured, you did not observe — you assumed.
2. **Problems without metrics are feelings.** "The system is slow" is not a problem statement. "P95 latency exceeds 200ms on the verification endpoint, affecting 12% of pipeline runs" is.
3. **Solutions without reproduction steps are anecdotes.** If an independent engineer cannot reproduce your solution from your document alone, the document has failed.
4. **Justification without alternatives is a preference.** Every decision implies rejected alternatives. If you cannot articulate why the alternatives were rejected with specific technical reasons, you have not made an architectural decision — you have expressed a preference.
5. **Claims without verification data are hypotheses.** A solution that has not been measured is not proven. It is speculated.

## Document types

| Prefix | Scope | Directory |
|--------|-------|-----------|
| ADR | Architectural decisions (system-wide) | `architectural/` |
| ALG | Algorithm design and selection | `algorithmic/` |
| STG | Pipeline stage design | `pipeline/` |

## Template

See [template.md](template.md) for the exact template. Every new decision document must use this template without modification to the section structure.

## Completeness checklist

A decision document is complete when:

- [ ] All 6 sections have substantive content (not stubs)
- [ ] Observation cites concrete data or failure modes
- [ ] Problem statement is falsifiable
- [ ] Solution is reproducible by an independent engineer
- [ ] Justification table has ≥2 rejected alternatives with specific reasons
- [ ] Reproducibility section has exact steps and expected outputs
- [ ] Verification data table has before/after metrics

A document without verification data is not complete. A solution without justification of rejected alternatives is not an architectural decision — it is a preference.
