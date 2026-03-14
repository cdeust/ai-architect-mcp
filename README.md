# AI Architect

An autonomous software engineering platform that generates verified specifications before implementation, enforces compliance through deterministic gates, and delivers merge-ready pull requests — without human intervention.

Built on Anthropic Skills + MCP best practices. Three layers, strictly separated: Skills define WHAT, Tools define HOW, Claude decides WHY.

## Architecture

The system has three layers and an 11-stage pipeline (0–10):

| Stage | Name | Purpose |
|-------|------|---------|
| 0 | Health Check | Pre-flight validation |
| 1 | Discovery | Source scanning and signal detection |
| 2 | Impact | Blast radius and compound scoring |
| 3 | Integration | Architecture design (ports and adapters) |
| 4 | PRD | Machine-verifiable specification generation |
| 5 | Review | Hostile verification of the PRD |
| 6 | Implementation | Code generation against acceptance criteria |
| 7 | Verification | Deterministic validation (64 HOR rules) |
| 8 | Benchmark | Performance gate |
| 9 | Deployment | Full test suite execution |
| 10 | Pull Request | Delivery with audit trail |

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Repository structure

- `skills/` — Stage skill definitions (Markdown, Survival Architecture v2.2)
- `mcp/` — Python MCP server (FastMCP, verification algorithms, adapters)
- `hooks/` — Pipeline enforcement (pre/post tool-use, .env protection)
- `scripts/` — Verification scripts (security, Python, Swift)
- `docs/` — Architecture and decision documents (6-point MIT framework)
- `tests/` — Test suite with deterministic fixtures
- `app/` — Mac app reference placeholder (display layer only)
