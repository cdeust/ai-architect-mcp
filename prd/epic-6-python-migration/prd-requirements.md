# Epic 6: Python MCP Server Migration — Requirements

**Epic ID:** E6
**Document:** prd-requirements.md
**Last Updated:** 2026-03-14

---

## Functional Requirements

### Package & Distribution

**FR-E6-001: PyPI Package Structure**
- Package name: `ai-architect-mcp`
- Publish to TestPyPI for validation
- Publish to PyPI for production
- Support Python 3.12+ (minimum 3.12)
- Include all source code, no binaries

**FR-E6-002: Build System**
- Use hatchling build backend (already in pyproject.toml)
- pyproject.toml includes: name, version, description, dependencies, optional-dependencies, entry_points, classifiers
- Version: 0.1.0 (incremental from existing)
- Classifiers: Development Status, Python Versions, License (MIT)

**FR-E6-003: CLI Entry Point**
- Entry point: `ai-architect-mcp` (via pyproject.toml entry_points)
- Resolves to `ai_architect_mcp.__main__:main()`
- Uses `click` or equivalent CLI framework
- Supports subcommands: serve, version, health, config-validate

**FR-E6-004: Serve Command**
- `ai-architect-mcp serve [--config PATH] [--port PORT] [--log-level LEVEL]`
- Loads config from file (default: ~/.config/ai-architect/config.toml or /etc/ai-architect/config.toml)
- Overrides via CLI flags and environment variables
- Starts FastMCP server on specified port
- Logs startup status and registered tools

**FR-E6-005: Version Command**
- `ai-architect-mcp version` prints: "ai-architect-mcp <version>"
- Version sourced from pyproject.toml [project] version field
- Exit code 0 on success

**FR-E6-006: Health Command**
- `ai-architect-mcp health [--endpoint URL]` queries health status
- Returns JSON: { status, version, tools_registered, algorithms_available, hor_rules_loaded, uptime_seconds }
- Used for monitoring and CI/CD validation
- Exit code 0 if healthy, 1 otherwise

**FR-E6-007: Config-Validate Command**
- `ai-architect-mcp config-validate [--config PATH]` validates TOML config
- Checks schema, required fields, data types
- Reports errors with line numbers
- Exit code 0 if valid, 1 if invalid

### Configuration System

**FR-E6-008: TOML Configuration File**
- Default location: `~/.config/ai-architect/config.toml` (Linux/macOS) or `%APPDATA%\ai-architect\config.toml` (Windows)
- Alternative: `/etc/ai-architect/config.toml` (system-wide)
- File is optional; defaults apply if missing
- Format: TOML 1.0.0 compliant

**FR-E6-009: Configuration Schema**
- Sections: [server], [verification], [prompting], [context], [adapters], [logging]
- Each section has required and optional fields
- Schema defined in Pydantic model with validation

**FR-E6-010: Server Configuration**
- `[server]` section:
  - name (string, default: "ai-architect")
  - port (int, default: 3000, range: 1024–65535)
  - host (string, default: "127.0.0.1")
  - timeout_seconds (int, default: 30)

**FR-E6-011: Verification Configuration**
- `[verification]` section:
  - enabled (bool, default: true)
  - timeout_seconds (int, default: 30)
  - consensus_algorithm (string, default: "adaptive_stability")
  - algorithms_available (list, auto-populated at runtime)

**FR-E6-012: Prompting Configuration**
- `[prompting]` section:
  - enhancement_enabled (bool, default: true)
  - default_strategy (string, default: "tree_of_thought")
  - max_tokens (int, default: 2000)
  - temperature (float, default: 0.7)

**FR-E6-013: Context Configuration**
- `[context]` section:
  - stage_context_dir (string, default: "./stage_contexts")
  - artifact_storage (string, default: "local")
  - cache_enabled (bool, default: true)
  - cache_ttl_seconds (int, default: 3600)

**FR-E6-014: Adapters Configuration**
- `[adapters]` section:
  - git_enabled (bool, default: true)
  - github_enabled (bool, default: true)
  - xcode_enabled (bool, default: false)
  - filesystem_enabled (bool, default: true)

**FR-E6-015: Logging Configuration**
- `[logging]` section:
  - level (string, default: "info")
  - format (string, default: "json")
  - output (string, default: "stdout")
  - file_path (string, optional)

**FR-E6-016: Environment Variable Override Hierarchy**
- Override precedence: CLI flag > Environment variable > Config file > Default
- Environment variables prefixed: `AI_ARCHITECT_`
- Examples:
  - `AI_ARCHITECT_PORT=3001`
  - `AI_ARCHITECT_VERIFICATION_TIMEOUT=60`
  - `AI_ARCHITECT_PROMPTING_ENHANCEMENT_ENABLED=false`
  - `AI_ARCHITECT_LOG_LEVEL=debug`

**FR-E6-017: Config Loader Implementation**
- Module: `ai_architect_mcp._config.loader`
- Function: `load_config(config_path: str | None = None) -> Config`
- Reads TOML file, applies env var overrides, validates, returns Config Pydantic model
- Raises ConfigError on validation failure with detailed error message

**FR-E6-018: Default Configuration File**
- File: `ai_architect_mcp/_config/defaults.toml`
- Contains all configurable options with defaults
- Bundled with package distribution
- Used as fallback if user config missing

### Tool Verification in Package Context

**FR-E6-019: 32 Tools Verified**
- All 32 tools register correctly when package imported
- Each tool callable via MCP protocol or direct Python call
- Tool responses match expected schema (Pydantic models)
- Tool execution time <5s (p95)
- Tools tested individually and in integration scenarios

**FR-E6-020: Tool Registration Verification**
- Tools listed in `mcp.list_tools()` output (all 32)
- Tool names start with `ai_architect_` prefix
- Tool descriptions accurate and complete
- Tool parameters documented with types and defaults
- Tool output schemas defined

**FR-E6-021: Tool Response Schema Validation**
- Each tool response validated against Pydantic model
- Response includes: status, data, metadata, error (if applicable)
- No breaking changes in response schema vs. existing engine
- Schema matches Node.js tool equivalents (backward compatibility)

**FR-E6-022: Verification Algorithm Access**
- All 7 algorithms accessible as tool inputs
- Algorithms include:
  1. AtomicClaimDecomposer
  2. ChainOfVerification
  3. NLIEntailmentEvaluator
  4. MultiAgentDebate
  5. WeightedAverageConsensus
  6. AdaptiveStabilityConsensus
  7. GraphConstrainedVerifier
- Each algorithm tested with sample inputs

**FR-E6-023: 64 HOR Rules Verified**
- All 64 HOR rules load and execute without error
- Rules accessible via `ai_architect_execute_hor_rule` tool
- Rules execute in correct order (dependency graph respected)
- Rules return expected output format
- Rules tested in batch mode

**FR-E6-024: 16 Strategies + 5 Enhancements Verified**
- All 16 prompting strategies selectable
- All 5 enhancement algorithms applicable
- Strategies include: tree_of_thought, chain_of_thought, zero_shot, few_shot, etc.
- Enhancements: clarity, detail, specificity, structure, reasoning
- End-to-end prompting pipeline tested

**FR-E6-025: Tool Annotations Preserved**
- All tools retain annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint
- Annotations tested for accuracy
- Annotations enforced in package context

---

## Non-Functional Requirements

**NFR-E6-001: Installation Time**
- `pip install ai-architect-mcp` completes in <30 seconds on standard hardware
- No post-install build steps (hatchling pre-builds wheel)
- Dependency resolution <10 seconds

**NFR-E6-002: Package Size**
- Installed size <50 MB (including dependencies)
- Compressed package <10 MB on PyPI
- No unnecessary files in distribution (use MANIFEST.in or .gitignore)

**NFR-E6-003: Python Version Support**
- Minimum: Python 3.12
- Tested: Python 3.12, 3.13
- Specify `requires-python = ">=3.12"` in pyproject.toml

**NFR-E6-004: Startup Performance**
- CLI commands start in <2 seconds
- MCP server `serve` command initializes in <5 seconds
- All tools registered before accepting requests

**NFR-E6-005: Tool Response Latency**
- 95th percentile response time: <5 seconds
- 99th percentile: <10 seconds
- Timeout: configurable, default 30 seconds

**NFR-E6-006: Configuration Validation**
- Config parsing error messages <200 characters, actionable
- Validation catches type mismatches, missing required fields, out-of-range values
- Validation time <100ms

**NFR-E6-007: Documentation Coverage**
- 100% of public APIs documented (docstrings)
- CLI help text for all commands and flags
- API reference covers all 32 tools with examples
- Migration guide covers Node.js → Python transition

**NFR-E6-008: Test Coverage**
- >85% line coverage for new code (CLI, config loader, package structure)
- 100% coverage for tool registration and health endpoint
- All acceptance criteria tested

**NFR-E6-009: Backward Compatibility**
- All Node.js tool calls map 1:1 to Python equivalents
- Response schemas identical or compatible
- No breaking changes to existing tool behavior

**NFR-E6-010: Logging & Observability**
- Structured logging (JSON format by default)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include timestamps, request IDs, tool execution time
- Sensitive data (API keys, tokens) redacted from logs

**NFR-E6-011: Error Handling**
- All errors include: error code, message, context
- Tool errors are caught and reported via MCP error response
- Config errors report line number and suggestion
- No stack traces in production logs (only in debug mode)

**NFR-E6-012: Security**
- Config files respect OS permissions (warn if world-readable)
- Environment variables (AI_ARCHITECT_*) validated
- No hardcoded secrets in package
- Dependency audit via pip-audit or similar

---

## Dependencies on Epics 1–4

**From Epic 1 (Plan & Interview):**
- StageContext framework
- HandoffDocument model
- Context query interface

**From Epic 2 (Memory Model):**
- HOR rule definitions (all 64)
- Artifact store implementation
- Rule execution engine

**From Epic 3 (Consensus Algorithms):**
- All 7 verification algorithms (ChainOfVerification, etc.)
- Consensus model definitions

**From Epic 4 (Hooks & Adapters):**
- Git, GitHub, Xcode, FileSystem adapters
- Adapter port interfaces
- Composition root

---

## Implementation Notes

### CLI Framework Choice
- Recommended: `click` (lightweight, standard in Python ecosystem)
- Alternative: `typer` (modern, async-friendly)
- Avoid: argparse (verbose), custom parsing (fragile)

### Configuration Format Choice
- Chosen: TOML (human-readable, section-based, matches pyproject.toml)
- Why: Standard in Python ecosystem (PEP 518, PEP 660)
- Examples provided in defaults.toml

### Build System
- Hatchling already in place; no changes needed
- Wheel-only distribution (no sdist required for PyPI, optional for archive)

### Testing Strategy
- Unit tests: config loader, CLI commands, tool registration
- Integration tests: serve command starts, tools respond, config overrides work
- Cross-version tests: run on Python 3.12, 3.13 in CI
- Package tests: pip install, import, health check in clean environment

