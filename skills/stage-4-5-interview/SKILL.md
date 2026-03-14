# Stage 4.5: Plan Interview

## Purpose

Quality gate between Stage 4 (PRD Generation) and Stage 5 (PRD Review). Evaluates the generated PRD artifact against 10 deterministic dimensions before it enters review. Prevents structurally deficient PRDs from consuming review cycles.

## Trigger

Automatically invoked after Stage 4 completes and produces a PRD artifact. The orchestrator calls this stage before proceeding to Stage 5.

## Input Contract

- **Required:** PRD artifact from Stage 4 as a dictionary with keys: `title`, `content`, `sections`, `requirements`, `user_stories`, `assumptions`, `success_metrics`
- **Required:** `finding_id` from the current pipeline run
- **Source:** StageContext artifact for stage_id=4

## Output Contract

- **InterviewResult** written to StageContext at stage_id=45
- Contains: 10 dimension scores, gate decision (APPROVED/PROVISIONAL/REJECTED), finding_id, timestamp
- Gate decision determines pipeline flow:
  - APPROVED → proceed to Stage 5
  - PROVISIONAL → proceed to Stage 5 with advisory warnings attached
  - REJECTED → return to Stage 4 for regeneration (max 2 retries)

## Operations Sequence

1. Load PRD artifact from StageContext (stage_id=4)
2. Run all 10 dimension scorers against the artifact
3. Evaluate gate decision based on critical/advisory thresholds
4. Write InterviewResult to StageContext (stage_id=45)
5. If REJECTED: log findings, return control to orchestrator for retry
6. If APPROVED or PROVISIONAL: pass control to Stage 5

## Tools Used

- `ai_architect_score_dimension` — score a single dimension
- `ai_architect_run_interview_gate` — run all 10 scorers and gate
- `ai_architect_query_interview_results` — retrieve past interview results

## Stop Criteria

- Gate decision is APPROVED or PROVISIONAL → proceed
- Gate decision is REJECTED and retry count < 2 → retry Stage 4
- Gate decision is REJECTED and retry count ≥ 2 → fail the finding with interview rejection reason

## Constraints

- Zero LLM calls. All 10 scorers are deterministic.
- Execution must complete within 60 seconds (InterviewConfig.timeout_seconds).
- No modification of the Stage 4 artifact. Read-only access to upstream.
