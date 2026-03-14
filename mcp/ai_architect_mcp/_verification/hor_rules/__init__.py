"""Higher-Order Reasoning (HOR) rules.

64 deterministic rules that verify implementation output against PRD
requirements. Each rule is a pure function: input → pass/fail with
explanation. No LLM calls. No fuzzy matching. No interpretation.

Rules are organized by category and numbered sequentially.
The 3 pipeline gates are separate from HOR rules and live in the
orchestrator logic.
"""
