# ai-automated-pipeline

MCP server for [ai-architect](https://github.com/cdeust/ai-architect-mcp) — the autonomous software-engineering pipeline for Claude Code.

Ships 49 MCP tools covering the 11-stage pipeline (health → discovery → impact → integration → PRD → interview → review → implementation → verification → benchmark → PR), 64 deterministic HOR verification rules, and 10 implemented algorithms (5 verification + 5 prompting).

## Install

```
/plugin marketplace add cdeust/ai-architect-mcp
/plugin install ai-architect
```

Or as a standalone MCP server:

```bash
uvx --from ai-automated-pipeline ai_architect_mcp
```

## Documentation

See the full project README, architecture notes, and stage skills at
<https://github.com/cdeust/ai-architect-mcp>.

## License

MIT
