"""Scoring engine.

Compound scoring functions that combine multiple signals into a single
score. Used by impact analysis (Stage 2), PRD review (Stage 5), and
verification (Stage 7). All scoring is deterministic — no LLM calls.
"""
