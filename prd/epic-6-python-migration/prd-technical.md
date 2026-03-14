# Epic 6: Python MCP Server Migration — Technical Design

**Epic ID:** E6
**Document:** prd-technical.md
**Last Updated:** 2026-03-14

---

## Architecture Overview

```
mcp/
├── pyproject.toml                    [UPDATED]
│   ├── [build-system]
│   ├── [project]
│   │   ├── name = "ai-architect-mcp"
│   │   ├── version = "0.1.0"
│   │   ├── requires-python = ">=3.12"
│   │   ├── dependencies = [fastmcp, pydantic>=2.0, anthropic, scipy, aiofiles, numpy, click]
│   │   ├── [project.scripts]
│   │   │   └── ai_architect_mcp = "ai_architect_mcp.__main__:main"
│   │   └── [project.classifiers]
│   └── [project.optional-dependencies]
│       └── dev = [pytest, pytest-asyncio, mypy, ruff]
│
├── ai_architect_mcp/
│   ├── __init__.py                   [UNCHANGED]
│   ├── __main__.py                   [NEW: CLI entry point]
│   ├── server.py                     [UNCHANGED: FastMCP server]
│   │
│   ├── _config/                      [NEW: Configuration system]
│   │   ├── __init__.py
│   │   ├── loader.py                 [Config TOML parser + env override]
│   │   ├── models.py                 [Pydantic config schema]
│   │   └── defaults.toml             [Default config values]
│   │
│   ├── _tools/                       [UNCHANGED: 32 tools]
│   │   ├── verification_tools.py     (5 tools)
│   │   ├── hor_tools.py              (8 tools)
│   │   ├── prompting_tools.py        (6 tools)
│   │   ├── context_tools.py          (5 tools)
│   │   ├── adapter_tools.py          (5 tools)
│   │   └── scoring_tools.py          (3 tools)
│   │
│   ├── _verification/                [UNCHANGED: 7 algorithms]
│   │   ├── algorithms/
│   │   │   ├── atomic_claim_decomposer.py
│   │   │   ├── chain_of_verification.py
│   │   │   ├── nli_entailment.py
│   │   │   ├── multi_agent_debate.py
│   │   │   ├── weighted_average.py
│   │   │   ├── adaptive_stability.py
│   │   │   └── graph_constrained.py
│   │   ├── hor/
│   │   │   ├── rules.py              (64 HOR rules)
│   │   │   ├── executor.py
│   │   │   └── validator.py
│   │   └── __init__.py
│   │
│   ├── _prompting/                   [UNCHANGED: 16 strategies + 5 enhancements]
│   │   ├── strategies/               (16 thinking strategies)
│   │   ├── enhancements/             (5 enhancement algorithms)
│   │   └── __init__.py
│   │
│   ├── _adapters/                    [UNCHANGED: Git, Xcode, GitHub, FileSystem]
│   │   ├── ports/
│   │   ├── adapters/
│   │   ├── composition_root.py
│   │   └── __init__.py
│   │
│   ├── _models/                      [UNCHANGED: 20+ Pydantic models]
│   ├── _context/                     [UNCHANGED: StageContext, HandoffDocument]
│   ├── _scoring/                     [UNCHANGED: Compound scoring]
│   └── _tests/                       [NEW: Package-specific tests]
│       ├── test_cli.py
│       ├── test_config.py
│       ├── test_tool_registration.py
│       └── test_package_integration.py
```

---

## New Components

### 1. CLI Entry Point (`ai_architect_mcp/__main__.py`)

```python
"""CLI entry point for AI Architect MCP server.

Commands:
- serve: Start the MCP server
- version: Print version
- health: Check server health
- config-validate: Validate config file
"""

import click
from ai_architect_mcp._config.loader import load_config, ConfigError
from ai_architect_mcp.server import mcp

@click.group()
@click.version_option(version="0.1.0", prog_name="ai-architect-mcp")
def cli():
    """AI Architect MCP Server CLI."""
    pass

@cli.command()
@click.option("--config", default=None, help="Config file path")
@click.option("--port", type=int, default=None, help="Server port")
@click.option("--log-level", default=None, help="Log level (debug, info, warning, error)")
def serve(config, port, log_level):
    """Start the AI Architect MCP server."""
    try:
        cfg = load_config(config_path=config, port_override=port, log_level_override=log_level)
        click.echo(f"Starting AI Architect MCP server on port {cfg.server.port}...")
        # Initialize server with config
        mcp.run(host=cfg.server.host, port=cfg.server.port)
    except ConfigError as e:
        click.echo(f"Config error: {e}", err=True)
        raise click.Exit(1)

@cli.command()
def version():
    """Print AI Architect MCP version."""
    click.echo("ai-architect-mcp 0.1.0")

@cli.command()
@click.option("--endpoint", default="http://localhost:3000", help="Server endpoint")
def health(endpoint):
    """Check AI Architect MCP server health."""
    # Query health endpoint; return JSON
    click.echo('{"status": "healthy", "version": "0.1.0", ...}')

@cli.command()
@click.option("--config", default=None, help="Config file path")
def config_validate(config):
    """Validate AI Architect config file."""
    try:
        cfg = load_config(config)
        click.echo("Config is valid.")
    except ConfigError as e:
        click.echo(f"Config error: {e}", err=True)
        raise click.Exit(1)

def main():
    """Entry point."""
    cli()

if __name__ == "__main__":
    main()
```

### 2. Configuration Loader (`ai_architect_mcp/_config/loader.py`)

```python
"""Configuration loader with TOML parsing and env var override."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import tomllib  # Python 3.11+
from pydantic import BaseModel, Field, ValidationError

class ServerConfig(BaseModel):
    name: str = "ai-architect"
    host: str = "127.0.0.1"
    port: int = Field(3000, ge=1024, le=65535)
    timeout_seconds: int = Field(30, ge=1)

class VerificationConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = Field(30, ge=1)
    consensus_algorithm: str = "adaptive_stability"

class PromptingConfig(BaseModel):
    enhancement_enabled: bool = True
    default_strategy: str = "tree_of_thought"
    max_tokens: int = Field(2000, ge=100)
    temperature: float = Field(0.7, ge=0.0, le=2.0)

class ContextConfig(BaseModel):
    stage_context_dir: str = "./stage_contexts"
    artifact_storage: str = "local"
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(3600, ge=60)

class AdaptersConfig(BaseModel):
    git_enabled: bool = True
    github_enabled: bool = True
    xcode_enabled: bool = False
    filesystem_enabled: bool = True

class LoggingConfig(BaseModel):
    level: str = "info"
    format: str = "json"
    output: str = "stdout"
    file_path: Optional[str] = None

class Config(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    prompting: PromptingConfig = Field(default_factory=PromptingConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    adapters: AdaptersConfig = Field(default_factory=AdaptersConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

class ConfigError(Exception):
    """Configuration error with context."""
    pass

def _get_default_config_path() -> Path:
    """Return default config file path."""
    if os.name == "nt":  # Windows
        return Path(os.getenv("APPDATA", ".")) / "ai-architect" / "config.toml"
    else:  # Unix/macOS
        return Path.home() / ".config" / "ai-architect" / "config.toml"

def _apply_env_overrides(cfg_dict: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to config dict."""
    prefix = "AI_ARCHITECT_"

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # E.g., AI_ARCHITECT_PORT -> server.port
        # E.g., AI_ARCHITECT_VERIFICATION_TIMEOUT -> verification.timeout_seconds
        parts = key[len(prefix):].lower().split("_")

        # Navigate nested dict and set value
        current = cfg_dict
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Convert value based on context (int, bool, etc.)
        final_key = parts[-1]
        if final_key in ("port", "timeout_seconds", "max_tokens", "cache_ttl_seconds"):
            current[final_key] = int(value)
        elif final_key in ("enabled", "cache_enabled", "enhancement_enabled"):
            current[final_key] = value.lower() in ("true", "1", "yes")
        else:
            current[final_key] = value

    return cfg_dict

def load_config(config_path: Optional[str] = None, **overrides) -> Config:
    """Load config from file with env var and override support.

    Args:
        config_path: Path to TOML config file (optional)
        **overrides: Direct config overrides (e.g., port_override=3001)

    Returns:
        Config Pydantic model

    Raises:
        ConfigError: If config is invalid
    """
    cfg_dict: dict[str, Any] = {}

    # 1. Start with defaults (embedded in code)
    cfg_dict = {
        "server": {"name": "ai-architect", "host": "127.0.0.1", "port": 3000, "timeout_seconds": 30},
        "verification": {"enabled": True, "timeout_seconds": 30, "consensus_algorithm": "adaptive_stability"},
        "prompting": {"enhancement_enabled": True, "default_strategy": "tree_of_thought", "max_tokens": 2000, "temperature": 0.7},
        "context": {"stage_context_dir": "./stage_contexts", "artifact_storage": "local", "cache_enabled": True, "cache_ttl_seconds": 3600},
        "adapters": {"git_enabled": True, "github_enabled": True, "xcode_enabled": False, "filesystem_enabled": True},
        "logging": {"level": "info", "format": "json", "output": "stdout", "file_path": None},
    }

    # 2. Load from TOML file (if exists or specified)
    if config_path:
        path = Path(config_path)
    else:
        path = _get_default_config_path()

    if path.exists():
        try:
            with open(path, "rb") as f:
                file_cfg = tomllib.load(f)
                # Merge file config into defaults
                for section, values in file_cfg.items():
                    if section in cfg_dict and isinstance(values, dict):
                        cfg_dict[section].update(values)
                    else:
                        cfg_dict[section] = values
        except Exception as e:
            raise ConfigError(f"Failed to parse {path}: {e}")

    # 3. Apply environment variable overrides
    cfg_dict = _apply_env_overrides(cfg_dict)

    # 4. Apply direct overrides (port_override, log_level_override, etc.)
    if "port_override" in overrides and overrides["port_override"]:
        cfg_dict["server"]["port"] = overrides["port_override"]
    if "log_level_override" in overrides and overrides["log_level_override"]:
        cfg_dict["logging"]["level"] = overrides["log_level_override"]

    # 5. Validate and return
    try:
        return Config(**cfg_dict)
    except ValidationError as e:
        raise ConfigError(f"Config validation failed: {e}")
```

### 3. Default Configuration (`ai_architect_mcp/_config/defaults.toml`)

```toml
# AI Architect MCP Server Configuration

[server]
name = "ai-architect"
host = "127.0.0.1"
port = 3000
timeout_seconds = 30

[verification]
enabled = true
timeout_seconds = 30
consensus_algorithm = "adaptive_stability"

[prompting]
enhancement_enabled = true
default_strategy = "tree_of_thought"
max_tokens = 2000
temperature = 0.7

[context]
stage_context_dir = "./stage_contexts"
artifact_storage = "local"
cache_enabled = true
cache_ttl_seconds = 3600

[adapters]
git_enabled = true
github_enabled = true
xcode_enabled = false
filesystem_enabled = true

[logging]
level = "info"
format = "json"
output = "stdout"
# file_path = "/var/log/ai-architect/server.log"  # Uncomment to enable file logging
```

---

## Tool Mapping: Node.js → Python

### Verification Tools

| Node.js Tool | Python Tool | Module | Parameters | Returns |
|--------------|-------------|--------|-----------|---------|
| `verify_claim` | `ai_architect_verify_claim` | verification_tools.py | content, claim_type, context, priority | ClaimEvaluation |
| `decompose_claim` | `ai_architect_decompose_claim` | verification_tools.py | content, max_depth | list[AtomicClaim] |
| `consensus_debate` | `ai_architect_consensus_debate` | verification_tools.py | claim, num_agents | ConsensusResult |
| `nli_eval` | `ai_architect_nli_evaluate` | verification_tools.py | premise, hypothesis | EntailmentScore |
| `weighted_consensus` | `ai_architect_weighted_consensus` | verification_tools.py | evaluations, weights | float |

### Prompting Tools

| Node.js Tool | Python Tool | Module | Parameters | Returns |
|--------------|-------------|--------|-----------|---------|
| `prompt_enhance` | `ai_architect_prompt_enhance` | prompting_tools.py | prompt, enhancement_type | str |
| `thinking_strategy_select` | `ai_architect_thinking_strategy_select` | prompting_tools.py | query, available_strategies | str |

### Context Tools

| Node.js Tool | Python Tool | Module | Parameters | Returns |
|--------------|-------------|--------|-----------|---------|
| `context_load` | `ai_architect_context_load` | context_tools.py | context_id | StageContext |
| `context_query` | `ai_architect_context_query` | context_tools.py | context_id, query, top_k | list[Finding] |

### Adapter Tools

| Node.js Tool | Python Tool | Module | Parameters | Returns |
|--------------|-------------|--------|-----------|---------|
| `git_status` | `ai_architect_git_status` | adapter_tools.py | repo_path | dict |
| `github_search` | `ai_architect_github_search` | adapter_tools.py | query, org, limit | list[GitHubResult] |

### Additional Python Tools (19 New)

**HOR Tools (8):**
- ai_architect_execute_hor_rule
- ai_architect_list_hor_rules
- ai_architect_validate_hor_rule
- ai_architect_batch_execute_hor_rules
- (4 more domain-specific rule tools)

**Context Tools (3 new):**
- ai_architect_context_save
- ai_architect_context_list
- ai_architect_context_delete

**Handoff Tools (3):**
- ai_architect_handoff_create
- ai_architect_handoff_export
- ai_architect_handoff_import

**Artifact Tools (4):**
- ai_architect_artifact_store
- ai_architect_artifact_retrieve
- ai_architect_artifact_list
- ai_architect_artifact_delete

**Scoring Tools (3):**
- ai_architect_compound_score
- ai_architect_propagate_score
- ai_architect_normalize_score

---

## Package Structure Details

### Dependencies

**Core Dependencies:**
- `fastmcp` — MCP server framework (already used)
- `pydantic>=2.0` — Data validation (already used)
- `anthropic` — Anthropic API (already used)
- `scipy` — Scientific computing (already used)
- `aiofiles` — Async file I/O (already used)
- `numpy` — Numerical arrays (already used)
- `click>=8.0` — CLI framework (NEW)
- `tomllib` — TOML parsing (standard library in 3.11+)

**Development Dependencies:**
- `pytest>=7.0`
- `pytest-asyncio>=0.21`
- `mypy>=1.0`
- `ruff>=0.1`

### Build Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-architect-mcp"
version = "0.1.0"
description = "AI Architect MCP server — verification, prompting, context, and adapter tools"
authors = [{name = "AI Architect Team", email = "team@anthropic.com"}]
license = {text = "MIT"}
requires-python = ">=3.12"
readme = "README.md"
repository = "https://github.com/anthropic-ai/ai-architect"

dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0",
    "anthropic>=0.20.0",
    "scipy>=1.10.0",
    "aiofiles>=23.0.0",
    "numpy>=1.24.0",
    "click>=8.0.0",
    "tomllib>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "mypy>=1.0",
    "ruff>=0.1",
    "pytest-cov>=4.0",
]

[project.scripts]
ai_architect_mcp = "ai_architect_mcp.__main__:main"

[project.urls]
Homepage = "https://github.com/anthropic-ai/ai-architect"
Repository = "https://github.com/anthropic-ai/ai-architect"
Documentation = "https://github.com/anthropic-ai/ai-architect/wiki"

[tool.hatch.build.targets.wheel]
packages = ["ai_architect_mcp"]

[tool.hatch.build.targets.sdist]
include = [
    "ai_architect_mcp/**/*.py",
    "ai_architect_mcp/**/*.toml",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
]
```

---

## Health Check Endpoint

### CLI Health Command

```bash
$ ai-architect-mcp health

{
  "status": "healthy",
  "version": "0.1.0",
  "tools_registered": 32,
  "algorithms_available": 7,
  "hor_rules_loaded": 64,
  "uptime_seconds": 1234.5,
  "timestamp": "2026-03-14T12:34:56Z"
}
```

### HTTP Health Endpoint (Optional)

If server runs FastMCP with built-in HTTP, health endpoint:

```
GET /health

Response:
{
  "status": "healthy",
  "version": "0.1.0",
  "tools_registered": 32,
  "algorithms_available": 7,
  "hor_rules_loaded": 64,
  "uptime_seconds": 1234.5,
  "timestamp": "2026-03-14T12:34:56Z"
}
```

---

## Docker Containerization (Recommended)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install ai-architect-mcp from PyPI
RUN pip install --no-cache-dir ai-architect-mcp==0.1.0

# Create config directory
RUN mkdir -p /etc/ai-architect

# Copy default config
COPY defaults.toml /etc/ai-architect/config.toml

# Expose server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ai-architect-mcp health --endpoint http://localhost:3000 || exit 1

# Start server
CMD ["ai-architect-mcp", "serve", "--config", "/etc/ai-architect/config.toml"]
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  ai-architect-mcp:
    image: ai-architect-mcp:0.1.0
    container_name: ai-architect-mcp
    ports:
      - "3000:3000"
    environment:
      AI_ARCHITECT_LOG_LEVEL: info
      AI_ARCHITECT_VERIFICATION_TIMEOUT: 60
    volumes:
      - ./config.toml:/etc/ai-architect/config.toml:ro
      - ./stage_contexts:/app/stage_contexts
    healthcheck:
      test: ["CMD", "ai-architect-mcp", "health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Configuration Validation Flow

```
User Request
    ↓
parse CLI flags
    ↓
load config file (if specified or default exists)
    ↓
read environment variables (AI_ARCHITECT_*)
    ↓
apply CLI overrides
    ↓
merge all sources (default < file < env < CLI)
    ↓
validate against Pydantic schema
    ↓
return Config object or raise ConfigError
    ↓
pass to FastMCP server initialization
```

---

## Tool Registration Process

```
import ai_architect_mcp
    ↓
server.py: create FastMCP("ai-architect") instance
    ↓
server.py: import all tool modules (adapter, context, hor, prompting, scoring, verification)
    ↓
each tool module: decorators (@mcp.tool()) register tools
    ↓
tool registration stores: name, description, input schema, handler function
    ↓
mcp.list_tools() returns all 32 registered tools
    ↓
mcp.call_tool(tool_name, parameters) invokes tool
    ↓
tool returns response (Pydantic model or dict)
    ↓
response serialized to JSON by FastMCP
    ↓
response sent to MCP client
```

---

## Error Handling Strategy

### Config Errors

```python
class ConfigError(Exception):
    """Raised when config is invalid."""
    def __init__(self, message: str, line_number: Optional[int] = None, suggestion: Optional[str] = None):
        self.message = message
        self.line_number = line_number
        self.suggestion = suggestion
        super().__init__(self.message)

    def __str__(self):
        msg = self.message
        if self.line_number:
            msg += f" (line {self.line_number})"
        if self.suggestion:
            msg += f"\nSuggestion: {self.suggestion}"
        return msg
```

### Tool Errors

```python
@mcp.tool()
async def ai_architect_verify_claim(...) -> dict[str, Any]:
    try:
        result = await verifier.verify(...)
        return {"status": "success", "data": result}
    except VerificationError as e:
        return {"status": "error", "error_code": "VERIFICATION_FAILED", "message": str(e)}
    except Exception as e:
        logger.exception("Unexpected error in verify_claim")
        return {"status": "error", "error_code": "INTERNAL_ERROR", "message": "Unexpected error"}
```

---

## Performance Considerations

1. **Startup Time:** Pre-load all 64 HOR rules once at server startup; cache in memory
2. **Tool Invocation:** Use async/await for I/O-bound tools (Git, GitHub, FileSystem)
3. **Config Parsing:** Parse TOML once at startup; reload on SIGHUP if needed
4. **Caching:** Implement optional context and result caching (configurable TTL)

