# AI Architect — CLAUDE.md

## Project identity

This is `anthropic/ai-architect` — the autonomous software engineering pipeline built on Anthropic best practices. Three layers, strictly separated:

- **Skills** (`skills/`) — WHAT to do. Markdown only. Zero code. Each stage is a self-contained SKILL.md that defines the stage's purpose, trigger conditions, input/output contracts, operations sequence, and stop criteria. Skills are read by Claude at the start of each stage. They are never executed directly.
- **Tools** (`mcp/`) — HOW to do it. Python only. Zero markdown logic. The MCP server exposes typed, annotated tools that perform discrete operations: verification algorithms, scoring functions, context management, and infrastructure adapters. Tools are stateless. They receive input, produce output, and have no knowledge of which stage called them.
- **Hooks** (`hooks/`) — Enforcement. Shell only. Pre-tool-use hooks block prohibited actions before they execute. Post-tool-use hooks validate outputs after they return. Hooks are deterministic gatekeepers — they do not reason, interpret, or decide. They pattern-match and pass or fail.

Claude's role: read the skill, understand context, call tools, evaluate output, decide whether to retry or proceed. Never mix layers. Skills tell Claude what to do. Tools give Claude capabilities. Hooks prevent Claude from violating constraints. Claude orchestrates everything but owns nothing except the decision of what to do next.

## Architecture rules (absolute)

1. **Skills define WHAT. Tools define HOW. Claude decides WHY. Never mix layers.** A skill must never contain executable code. A tool must never contain pipeline logic or stage sequencing. Claude must never hardcode a decision that should come from a skill or be enforced by a hook.
2. **Every pipeline stage is an independent skill with its own SKILL.md.** Never embed stage logic in the orchestrator. The orchestrator skill coordinates stage execution order and agent lifecycle — it does not know what any stage does internally. Each stage skill is self-contained and can be understood without reading any other skill.
3. **Adapters implement Protocols from `_adapters/ports.py`.** Never hardcode infrastructure calls (git, file system, Xcode) directly in stage logic. All external system interactions go through typed port interfaces. Concrete adapters are injected at the composition root. This allows testing with mock adapters and swapping implementations without touching stage logic.
4. **No license gates, no tier checks, no feature flags based on payment.** Full engine on every run. Every user gets every algorithm, every verification rule, every capability. The free tier with chain-of-thought-only verification was removed after 60% failure rate on complex PRDs vs 8% with the full suite.
5. **The model generates. The system verifies. No LLM judges LLM output.** Verification in Stage 7 is deterministic — HOR rules, graph analysis, build compilation, visual regression diffs. Scripts judge LLM output. When an LLM is used in Stages 4–5 for generation and review, the verification suite (not another LLM call) determines whether the output meets acceptance criteria.
6. **Every tool call in Stage 7 (verification) must be on the allowlist.** No LLM calls in a deterministic stage. The verification engine runs 64 HOR rules, structural checks, and build gates — all of which produce binary pass/fail results without interpretation.
7. **Context flows forward, never backward.** Each stage reads its predecessor's output from StageContext and writes its own output to StageContext. A stage must never modify a previous stage's artifact. Read-only access to upstream. Write access only to your own stage slot.

## Code standards — Python (MCP server)

- Type hints on every function parameter and return type. No exceptions. Use `from __future__ import annotations` at the top of every module.
- Docstrings on every public function. Google style. Include Args, Returns, and Raises sections.
- Constants in `UPPER_CASE`. No magic strings anywhere. If a string appears more than once, it must be a named constant.
- Pydantic v2 for all input/output models. Use `model_validator` for cross-field validation. Use `Field(description=...)` on every field.
- `async`/`await` throughout the MCP server. No sync calls in async context. Use `asyncio.to_thread()` if wrapping unavoidable sync libraries.
- No bare `except`. Catch specific exceptions only. Every except block must either re-raise, log and handle, or convert to a typed error.
- No wildcard imports (`from module import *`). Never. Every import must be explicit.
- Internal modules prefixed with `_` following Anthropic convention (`_verification`, `_prompting`, `_context`, `_adapters`, `_scoring`).
- All MCP tools prefixed with `ai_architect_`. Annotations on every tool: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
- Actionable error messages. Every error must tell the caller what went wrong and what to do about it. "Validation failed" is not acceptable. "Field 'acceptance_criteria' is empty — every requirement must have at least one acceptance criterion" is.

## Code standards — Shell (hooks)

- `set -euo pipefail` on every hook script. No exceptions.
- Never read, echo, or log the contents of `.env` files.
- Never log API keys, tokens, or secrets — even partially. No `echo $API_KEY`, no `echo ${TOKEN:0:4}...`, no logging of authorization headers.
- All hook scripts must be idempotent where possible. Running a hook twice with the same input must produce the same result.
- Exit codes: `0` = pass, `1` = block (with explanation on stdout), `2` = error in the hook itself.
- Every hook must identify itself in output: `echo "PASS [hook-name]: description"` or `echo "BLOCK [hook-name]: description"`.

## Zero-tolerance rules (no exceptions, no overrides)

These rules are enforced by hooks and CI. Violations block the pipeline.

1. **Files ≤ 300 lines.** If a file exceeds 300 lines, it must be split. No "but this file is special" exceptions.
2. **One type/class per file.** A file defines exactly one public type. Private helper types used only by that public type are permitted.
3. **Functions/methods ≤ 40 lines.** Measured by logical lines (excluding blank lines and comments). Extract helper functions.
4. **No god-object names.** `Utils`, `Helper`, `Helpers`, `Manager`, `Handler`, `Processor` as suffix — all banned. Name things for what they do, not what they are.
5. **No nested types** (except `CodingKeys` in Swift for Codable conformance).
6. **No backward-compatibility hacks.** No `typealias` shims, no `@available(*, deprecated)` wrappers, no version-conditional compilation for removed features.
7. **No force-unwrap (`!`), force-try (`try!`), force-cast (`as!`)** in Python or Swift. Handle errors explicitly.
8. **No `TODO`/`FIXME`/`HACK` in production code.** If something needs to be done, create a finding. If something is broken, fix it now.
9. **No hardcoded secrets, API keys, or tokens.** Anywhere. Ever. In any file type. `verify-security.sh` scans for this on every commit.

## Anti-patterns (explicitly refused)

Claude must refuse to implement any of the following, even if asked:

- Importing a concrete adapter inside a stage skill or use case — use the port interface
- Writing engine logic in CLAUDE.md or any SKILL.md — skills are specifications, not code
- Calling git, filesystem, or Xcode tools directly from stage logic — go through the adapter port
- Using `print()` for logging in production Python — use the `logging` module
- Returning `Any` type from Python functions — always specify the concrete return type
- Mutable default arguments in Python functions (`def f(items=[])`) — use `None` with internal initialization
- Global mutable state — all state flows through StageContext or function parameters
- Singletons outside the composition root — dependency injection only
- Skipping the OODA checkpoint because "it's obvious this passed" — every checkpoint is verified explicitly
- Proceeding to the next stage without writing the stage artifact to StageContext — the artifact is the proof of work
- Reading `.env` files at any point during a session — environment variables are set before session start
- Merging a PR without a passing verification report — Stage 7 gate is absolute

## Before writing any code

1. Read the relevant stage SKILL.md first. Every stage has one. Read it completely.
2. Read the relevant decision document in `docs/decisions/` if it exists. Understand the rationale.
3. Check `docs/architecture.md` for cross-engine implications. Changes rarely affect only one layer.
4. State which stage, module, and algorithm you are working on before starting. This is not optional.

## Before any implementation

- Verify the change does not break the port/adapter pattern. If you need a new infrastructure capability, define a new port method first, then implement the adapter.
- Verify deterministic modules remain deterministic. No LLM calls in HOR rules, scoring functions, or graph analysis. If you find yourself wanting to "ask Claude" inside a deterministic module, the module's contract is wrong.
- Verify LLM-dependent modules have both structural tests (schema validation, field presence, type correctness) and behavioral tests (convergence within N iterations, confidence above threshold, no regression on known inputs).

## Testing

- **Deterministic modules:** bit-for-bit output matching against fixtures in `tests/fixtures/`. Given the same input, the output must be identical every time. No fuzzy matching. No "close enough."
- **LLM-dependent modules:** structural matching (schema, field types, required fields present) + behavioral tests (convergence, confidence thresholds, no catastrophic regression). These tests may be non-deterministic but must pass reliably (>95% of runs).
- **Every new module must have tests before it is considered complete.** Code without tests is not done. Tests without fixtures (for deterministic modules) are not done.
- **Run `pytest` after every change.** Do not proceed if tests fail. Do not comment out failing tests. Do not mark them as `xfail` without a linked finding.

## Documentation — 6-point framework (MIT standard)

Every architectural decision, algorithm, rule, and stage must be documented with:

1. **OBSERVATION** — what was measured, observed, or encountered that triggered this decision. Cite concrete data, failure modes, or system behavior — not opinion.
2. **PROBLEM** — specific, measurable problem being solved. Must be falsifiable. Include who is affected, what fails, how frequently, and what the cost is.
3. **SOLUTION** — implementation details sufficient for an independent engineer to reproduce the solution without this document's author.
4. **JUSTIFICATION** — why this solution over the alternatives considered. Every rejected alternative must have a specific, technical reason for rejection.
5. **REPRODUCIBILITY** — exact steps, inputs, expected outputs, and environment requirements to validate the solution.
6. **VERIFICATION DATA** — before/after metrics, test results, statistical significance where applicable. A claim without data is a hypothesis, not a finding.

Do not ship code without its decision document. Do not write a decision document without verification data.

## Pipeline-specific rules

- **11 stages numbered 0–10.** Never reference "10 stages" or misnumber. Stage 0 is HealthCheck. Stage 10 is PullRequest.
- **10 implemented algorithms:** 5 verification (KS Adaptive Stability Consensus, Multi-Agent Debate, Zero-LLM Graph Verification, NLI Entailment Evaluator, Weighted Average Consensus) + 5 prompting (Adaptive Expansion/ToT/GoT, Metacognitive, Collaborative Inference, Signal-Aware Thought Buffer, Confidence Fusion). Never inflate or deflate the count.
- **64 HOR rules.** Plus 3 pipeline gates which are gates, not HOR rules. Never conflate them.
- **DriftReconciler is deleted dead code.** Never reference it.
- **Semantic Verification as a separate stage is deleted.** Stage 7 is merged deterministic verification.
- **Bayesian Consensus and Majority Voting consensus are enum stubs only.** Never reference them as implemented algorithms.

## Security

- **Never read `.env` files.** Not in hooks, not in tools, not in scripts, not in tests. Environment variables are set before session start and accessed via `os.environ`.
- **Never log or echo secret values.** Not even partially. Not even in debug mode. Not even to stderr.
- **Never commit credentials, tokens, or API keys.** `verify-security.sh` runs on every commit attempt and scans for known patterns.
- **Pre-tool-use hooks enforce security checks.** The `.env` protection block runs on every tool call in every stage. It is not a stub. It is not optional. It cannot be bypassed.

## Context management

- At session start, check `pipeline_state.md` for current project state. If it exists, resume from where the last session left off.
- At session end, update the HandoffDocument via the `stop.sh` hook. Include: what was completed, what is in progress, what is blocked, and what the next session should do first.
- When context exceeds 70%, switch to L2 summaries. Load configuration and summaries only — not full documents.
- At 93%, create handoff and compact — never lose state. Write everything needed for the next session to continue without re-reading source material.
- Never reload full documentation when a summary exists and suffices. Progressive disclosure: config (500t) → summaries (300t) → full docs (3Kt).

## Communication style

- Be direct. No filler. No "great question" or "that's interesting."
- When something is wrong in the codebase, say what and why. Don't soften it.
- When the architecture is being violated, block and explain. Don't suggest — refuse.
- When referencing algorithms, use their exact names and numbers (1–10).
- When estimating effort, give honest timelines. Don't underestimate to be encouraging.
