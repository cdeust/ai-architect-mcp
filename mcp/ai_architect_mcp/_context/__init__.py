"""Context management engine.

Provides StageContext (per-finding, per-stage artifact storage) and
HandoffDocument (session boundary persistence). Supports progressive
disclosure: config (500t) -> summaries (300t) -> full docs (3Kt).

Uses iCloud for persistence when available, falls back to local filesystem.
Four memory layers: session, project, experience (with biological decay),
analytics.
"""
