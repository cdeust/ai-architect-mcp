# CLI Skill

## Purpose
Provide command-line interface workflows for codebase intelligence operations.

## When to Use
- Direct terminal usage of the intelligence engine
- Scripting and automation
- CI/CD pipeline integration

## Commands

| Command | Description |
|---------|-------------|
| `analyze <path>` | Index a repository |
| `query <text>` | Search the codebase |
| `context <name>` | Get symbol context |
| `impact <name>` | Blast radius analysis |
| `cypher <query>` | Raw Cypher query |
| `list` | List indexed repos |
| `status` | Engine status |
| `clean <path>` | Delete repo index |
| `mcp` | Start MCP server |

## Usage Examples

```bash
# Index a repo
ai-codebase-intelligence analyze /path/to/repo

# Search for symbols
ai-codebase-intelligence query "bias correction"

# Get context for a class
ai-codebase-intelligence context BiasCorrector
```
