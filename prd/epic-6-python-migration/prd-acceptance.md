# Epic 6: Python MCP Server Migration — Acceptance Criteria

**Epic ID:** E6
**Document:** prd-acceptance.md
**Last Updated:** 2026-03-14

---

## Overview

This document details all acceptance criteria (AC) for Epic 6 requirements. Each AC is testable and measurable. Total: 35+ ACs covering packaging, CLI, config, tool verification, and documentation.

---

## Package & Distribution (AC-E6-001 through AC-E6-010)

**AC-E6-001: PyPI Package Published**
- Package `ai-architect-mcp` v0.1.0 available on pypi.org
- Package discoverable via `pip search ai-architect-mcp` (if enabled) or direct URL
- Package metadata complete: name, version, description, author, repository, license

**AC-E6-002: Installation Success on Python 3.12**
- Command: `pip install ai-architect-mcp==0.1.0` succeeds on Python 3.12
- Installation time <30 seconds on standard hardware
- All dependencies resolved and installed
- CLI entry point `ai-architect-mcp` is executable

**AC-E6-003: Installation Success on Python 3.13**
- Command: `pip install ai-architect-mcp==0.1.0` succeeds on Python 3.13
- Installation time <30 seconds
- All dependencies resolved and installed
- CLI entry point `ai-architect-mcp` is executable

**AC-E6-004: Package Size Constraint**
- Wheel file size <10 MB (compressed on disk)
- Installed size (with dependencies) <50 MB on disk
- No unnecessary files included (verified via wheel contents inspection)

**AC-E6-005: Build System Validation**
- `python -m build` succeeds in package directory
- Generates both wheel and source distribution
- No build errors or warnings
- Wheel is installable in clean Python environment

**AC-E6-006: Dependency Specification**
- pyproject.toml [project.dependencies] includes all required packages
- pyproject.toml [project.optional-dependencies][dev] includes dev tools
- Version constraints are correct (e.g., pydantic>=2.0, click>=8.0)
- No circular dependencies

**AC-E6-007: Entry Point Registration**
- Entry point defined: `ai_architect_mcp = "ai_architect_mcp.__main__:main"`
- Entry point resolves correctly after installation
- Command `ai-architect-mcp --version` returns version without error

**AC-E6-008: Classifiers Accuracy**
- Classifiers in pyproject.toml include:
  - Development Status :: 3 - Alpha
  - License :: OSI Approved :: MIT License
  - Python :: 3.12
  - Python :: 3.13
- Classifiers are accurate and meaningful

**AC-E6-009: License & Metadata**
- LICENSE file (MIT) included in distribution
- Author email and repository URL correct
- Homepage URL points to correct GitHub page

**AC-E6-010: TestPyPI Publish**
- Package published to test.pypi.org successfully
- Installation from TestPyPI succeeds: `pip install -i https://test.pypi.org/simple/ ai-architect-mcp`
- All functionality works identically on TestPyPI and PyPI

---

## CLI Implementation (AC-E6-011 through AC-E6-020)

**AC-E6-011: Help Text**
- `ai-architect-mcp --help` displays all subcommands: serve, version, health, config-validate
- Each subcommand has description
- Global flags are documented
- Exit code 0 on success

**AC-E6-012: Version Command**
- `ai-architect-mcp version` outputs exactly: `ai-architect-mcp 0.1.0\n`
- Exit code 0 on success
- No additional output

**AC-E6-013: Serve Command Basic**
- `ai-architect-mcp serve` starts server without error
- Server logs "Starting AI Architect MCP server on port 3000"
- Server listens on 127.0.0.1:3000 (default)
- Server shuts down cleanly on SIGTERM/SIGINT

**AC-E6-014: Serve Command with Config Flag**
- `ai-architect-mcp serve --config /path/to/config.toml` loads config file
- Server honors config settings (port, log level, etc.)
- Invalid config path reported with error message

**AC-E6-015: Serve Command with Port Flag**
- `ai-architect-mcp serve --port 3001` starts server on port 3001
- Port flag overrides config file value
- Invalid port (out of range 1024–65535) rejected with error

**AC-E6-016: Serve Command with Log Level Flag**
- `ai-architect-mcp serve --log-level debug` sets log level to debug
- Log level flag overrides config file value
- Invalid log level (not in [debug, info, warning, error]) rejected

**AC-E6-017: Health Command with Running Server**
- `ai-architect-mcp health` queries running server
- Returns JSON object with fields: status, version, tools_registered, algorithms_available, hor_rules_loaded, uptime_seconds
- Exit code 0 on healthy status

**AC-E6-018: Health Command with No Server**
- `ai-architect-mcp health` with no running server returns error or timeout
- Exit code 1 on failure
- Error message is actionable (e.g., "Could not connect to server")

**AC-E6-019: Config-Validate Command**
- `ai-architect-mcp config-validate --config /path/to/config.toml` validates file
- Valid config: "Config is valid." + exit code 0
- Invalid config: error message with line number + exit code 1

**AC-E6-020: CLI Error Handling**
- Invalid command (e.g., `ai-architect-mcp invalid`) shows error and help
- Missing required arguments show error and usage
- All error messages are actionable
- Exit codes follow convention: 0 = success, 1 = error

---

## Configuration System (AC-E6-021 through AC-E6-032)

**AC-E6-021: Default Config**
- If no config file specified or found, defaults apply
- Defaults: port=3000, host=127.0.0.1, log_level=info, timeout=30, etc.
- Server starts successfully with defaults

**AC-E6-022: Config File Loading**
- Valid TOML file at ~/.config/ai-architect/config.toml (or specified path) is loaded
- Config sections parsed: [server], [verification], [prompting], [context], [adapters], [logging]
- File modification time and hash logged (for debugging)

**AC-E6-023: Environment Variable Override (Port)**
- `AI_ARCHITECT_PORT=3001 ai-architect-mcp serve` starts server on port 3001
- Env var overrides config file value
- Env var is case-sensitive (AI_ARCHITECT_PORT, not ai_architect_port)

**AC-E6-024: Environment Variable Override (Log Level)**
- `AI_ARCHITECT_LOG_LEVEL=debug ai-architect-mcp serve` sets log level to debug
- All tool invocations log at debug level
- Env var overrides config file value

**AC-E6-025: Environment Variable Override (Verification Timeout)**
- `AI_ARCHITECT_VERIFICATION_TIMEOUT=60 ai-architect-mcp serve` sets timeout to 60 seconds
- Tools respect timeout setting
- Env var overrides config file value

**AC-E6-026: Environment Variable Override (Multiple)**
- Multiple env vars can be set simultaneously: `AI_ARCHITECT_PORT=3001 AI_ARCHITECT_LOG_LEVEL=debug ai-architect-mcp serve`
- All overrides are applied correctly
- No conflicts between env vars

**AC-E6-027: CLI Flag Override Priority**
- CLI flag `--port 3002` overrides env var `AI_ARCHITECT_PORT=3001`
- Overall priority: CLI flag > env var > config file > default
- Final port is 3002 (CLI flag wins)

**AC-E6-028: Config Validation (Type Check)**
- Port must be integer; string value (e.g., "3001") is rejected with error
- Timeout must be positive integer; negative values rejected
- Log level must be in [debug, info, warning, error]; other values rejected

**AC-E6-029: Config Validation (Required Fields)**
- Config is valid without optional fields (e.g., logging.file_path)
- Config is invalid if required field is missing and no default exists
- Error message specifies missing field name

**AC-E6-030: Config Validation (Range Check)**
- Port range 1024–65535; values outside rejected with error
- Timeout range ≥1; values <1 rejected
- Temperature range 0.0–2.0; values outside rejected

**AC-E6-031: Config Error Messages**
- Error message includes: field name, expected type/value, actual value
- If TOML file, error includes line number
- Suggestion for remediation included (if applicable)

**AC-E6-032: Config Immutability**
- Config object (Pydantic model) is frozen/immutable after loading
- Attempting to modify config field raises error
- Config is serializable to dict and JSON

---

## Tool Verification (AC-E6-033 through AC-E6-045)

**AC-E6-033: Tool Count**
- `mcp.list_tools()` returns exactly 32 tools (not 31, not 33)
- Tool list includes all 32 tools from 6 modules

**AC-E6-034: Tool Names**
- All tool names start with `ai_architect_` prefix
- Tool names are lowercase with underscores (snake_case)
- No duplicate tool names

**AC-E6-035: Tool Descriptions**
- Each tool has a docstring describing its purpose
- Docstring is accessible via tool metadata (description field)
- Descriptions are concise (<200 characters) and actionable

**AC-E6-036: Tool Parameters**
- Each tool has documented parameters with type hints
- Parameter types match function signature
- Parameters have default values or are marked required

**AC-E6-037: Verification Tools (5)**
- ai_architect_verify_claim: executes and returns ClaimEvaluation
- ai_architect_decompose_claim: returns list[AtomicClaim]
- ai_architect_consensus_debate: returns ConsensusResult
- ai_architect_nli_evaluate: returns float (entailment score)
- ai_architect_graph_constrain: returns ConstrainedEvaluation

**AC-E6-038: HOR Tools (8)**
- ai_architect_execute_hor_rule: executes rule, returns RuleResult
- ai_architect_list_hor_rules: lists all 64 rules, returns list[RuleMetadata]
- ai_architect_validate_hor_rule: validates rule, returns bool
- ai_architect_batch_execute_hor_rules: executes multiple rules, returns list[RuleResult]
- (4 more HOR tools functional and tested)

**AC-E6-039: Prompting Tools (6)**
- ai_architect_enhance_prompt: enhances prompt, returns string
- ai_architect_thinking_strategy_select: selects strategy, returns string
- ai_architect_apply_enhancement: applies enhancement, returns string
- (3 more prompting tools functional and tested)

**AC-E6-040: Context Tools (5)**
- ai_architect_context_load: loads context, returns StageContext
- ai_architect_context_save: saves context, returns bool
- ai_architect_context_query: queries context, returns list[Finding]
- ai_architect_context_list: lists contexts, returns list[string]
- ai_architect_context_delete: deletes context, returns bool

**AC-E6-041: Adapter Tools (5)**
- ai_architect_git_status: returns git status dict
- ai_architect_github_search: returns list[GitHubResult]
- ai_architect_xcode_command: returns command output
- ai_architect_filesystem_read: returns file contents
- ai_architect_filesystem_write: writes file, returns bool

**AC-E6-042: Scoring Tools (3)**
- ai_architect_compound_score: returns float
- ai_architect_propagate_score: returns dict with propagated scores
- ai_architect_normalize_score: returns float 0–1

**AC-E6-043: Tool Response Schema**
- Each tool response is JSON-serializable
- Response matches expected Pydantic model
- Response includes metadata (timestamp, execution_time)

**AC-E6-044: Tool Performance**
- All tools execute in <5 seconds (95th percentile)
- No tool timeout on normal inputs
- Tool performance is consistent across multiple invocations

**AC-E6-045: Tool Idempotency**
- Read-only tools (verify, query, list) are idempotent
- Destructive tools (delete, write) are marked with destructiveHint
- Tool annotations (readOnlyHint, idempotentHint, etc.) are accurate

---

## Algorithm & Rule Verification (AC-E6-046 through AC-E6-055)

**AC-E6-046: 7 Algorithms Accessible**
- All 7 verification algorithms importable and instantiable
- Algorithms: AtomicClaimDecomposer, ChainOfVerification, NLIEntailmentEvaluator, MultiAgentDebate, WeightedAverageConsensus, AdaptiveStabilityConsensus, GraphConstrainedVerifier

**AC-E6-047: Algorithm Execution**
- Each algorithm has execute/verify/run method callable with sample input
- No import errors or initialization failures
- Output type matches expected schema

**AC-E6-048: Algorithm Output**
- Algorithms return Pydantic models or JSON-serializable dicts
- Output includes: result, confidence/score, metadata
- No null/empty outputs on valid input

**AC-E6-049: 64 HOR Rules Load**
- All 64 HOR rules loaded from rule store at startup
- No rule loading errors
- Rules are deduplicated (no duplicates)

**AC-E6-050: 64 HOR Rules Execute**
- Each of 64 rules executable via ai_architect_execute_hor_rule
- Execution time <1 second per rule
- All rules return RuleResult with status (pass/fail)

**AC-E6-051: HOR Rule Metadata**
- Each rule has: id (unique), name, category, preconditions, effects, priority
- Rule metadata is accurate and consistent
- Rule descriptions are actionable

**AC-E6-052: 16 Strategies Available**
- All 16 thinking strategies listed and selectable
- Strategies include: tree_of_thought, chain_of_thought, zero_shot, few_shot, etc.
- Strategy selection returns strategy name and metadata

**AC-E6-053: Strategies Applicable**
- Each strategy can be applied to test prompt
- Output is enhanced/modified version of input prompt
- Output is non-empty and different from input

**AC-E6-054: 5 Enhancements Available**
- All 5 enhancement types available: clarity, detail, specificity, structure, reasoning
- Enhancement application returns enhanced prompt
- Enhancements are composable (can apply multiple in sequence)

**AC-E6-055: Enhancement Metadata**
- Each enhancement has: type, description, effect_description
- Metadata is accurate and documented
- Enhancement categories are well-defined

---

## Cross-Version & Compatibility (AC-E6-056 through AC-E6-065)

**AC-E6-056: Python 3.12 Compatibility**
- All code is Python 3.12 compatible (no 3.13+ only syntax)
- Uses tomllib (available in 3.11+) for TOML parsing
- asyncio and type hints are 3.12 compatible

**AC-E6-057: Python 3.13 Compatibility**
- All code runs on Python 3.13 without modification
- No deprecation warnings on Python 3.13
- Tool performance is equivalent on 3.13

**AC-E6-058: Dependency Version Compatibility**
- All dependencies support Python 3.12 and 3.13
- Dependency versions specified in pyproject.toml are compatible
- No conflicts between transitive dependencies

**AC-E6-059: Node.js Tool Mapping**
- All 13 Node.js tools have Python equivalents
- Response schemas are compatible (no breaking changes)
- Node.js users can migrate without code changes

**AC-E6-060: MCP Protocol Compliance**
- Server responds to protocol initialization handshake
- list_tools returns correct schema
- call_tool marshals parameters correctly
- Error responses follow MCP spec

**AC-E6-061: Docker Compatibility**
- Dockerfile builds successfully with base image python:3.12-slim
- Docker image can be created with: `docker build -t ai-architect-mcp:0.1.0 .`
- Image size <500 MB
- Container starts and serves requests

**AC-E6-062: Docker Entrypoint**
- Docker entrypoint starts `ai-architect-mcp serve`
- Health check via `ai-architect-mcp health` works in container
- Environment variables can be set via docker run -e

**AC-E6-063: Environment Variable Compatibility**
- All environment variable overrides work consistently
- AI_ARCHITECT_* variables override config file
- No platform-specific issues (Linux, macOS, Windows)

**AC-E6-064: Logging Compatibility**
- Logging format (JSON) is parseable by standard log aggregators
- Log levels match standard levels: DEBUG, INFO, WARNING, ERROR
- Sensitive data (API keys, tokens) not logged

**AC-E6-065: Backward Compatibility Statement**
- No breaking changes to tool APIs
- All responses are compatible with Node.js equivalent
- Migration guide documents any minor parameter changes

---

## Documentation & Delivery (AC-E6-066 through AC-E6-075)

**AC-E6-066: Migration Guide Complete**
- Migration guide available in docs/MIGRATION_GUIDE.md or wiki
- Guide covers: pre-migration checklist, tool mapping, configuration translation, testing, rollback
- Estimated migration time provided
- All code examples are tested

**AC-E6-067: API Reference Complete**
- API reference documents all 32 tools
- Each tool has: name, description, parameters, returns, example
- Configuration reference documents all fields
- CLI reference documents all commands

**AC-E6-068: Docstring Coverage**
- All public functions and classes have docstrings
- Docstrings follow standard format (description, args, returns, raises)
- Docstrings are complete and accurate

**AC-E6-069: README Complete**
- README includes: description, installation, quick start, configuration, tools overview
- README has table of contents and links to detailed docs
- Code examples in README are tested and work

**AC-E6-070: Troubleshooting Guide**
- Troubleshooting guide covers ≥5 common errors
- Each error has: description, root cause, solution, example log output
- Errors covered: tool not found, config parsing error, timeout, connectivity, dependency issues

**AC-E6-071: Example Configuration**
- Example config.toml provided (in README or docs)
- Example shows all configurable options
- Example is valid and works without modification

**AC-E6-072: Tool Examples**
- Each tool has at least one code example
- Examples are Python code (if applicable) or curl/MCP client requests
- Examples show typical usage pattern

**AC-E6-073: Release Notes**
- Release notes (CHANGELOG.md) document all features and fixes
- Release notes for v0.1.0 include: features, tools, algorithms, breaking changes (if any)
- Release notes link to migration guide and API reference

**AC-E6-074: Links & References**
- All documentation links are valid and not broken
- Links to GitHub repo, PyPI page, issue tracker are correct
- References to other epics (1–5) are clear

**AC-E6-075: Documentation Review**
- Documentation is peer-reviewed by ≥2 people
- Reviewers include: at least 1 team member not on Epic 6, at least 1 user-facing role
- All review feedback is addressed

---

## Testing & Quality (AC-E6-076 through AC-E6-085)

**AC-E6-076: Unit Test Coverage**
- Test coverage for CLI (test_cli.py): ≥90%
- Test coverage for config (test_config.py): ≥90%
- Test coverage for tool registration (test_tool_registration.py): ≥90%
- Total coverage for new code: ≥85%

**AC-E6-077: Integration Tests Pass**
- test_package_integration.py passes all tests
- Tests verify: installation, CLI invocation, tool registration, config loading
- No flaky tests (deterministic, no timing issues)

**AC-E6-078: CLI Tests**
- Test version command output format
- Test serve command startup
- Test health command with running server
- Test config-validate command
- Test error handling and exit codes

**AC-E6-079: Config Tests**
- Test TOML file loading (valid and invalid files)
- Test environment variable overrides
- Test CLI flag overrides
- Test override priority (CLI > env > file > default)
- Test validation errors

**AC-E6-080: Tool Invocation Tests**
- Test all 32 tools can be invoked
- Test tool parameters and return types
- Test tool error handling
- Test tool annotations are accurate

**AC-E6-081: Algorithm Tests**
- Test all 7 algorithms can be instantiated
- Test algorithm execution with sample inputs
- Test algorithm output format
- Test algorithm edge cases (null, empty, invalid)

**AC-E6-082: HOR Rule Tests**
- Test all 64 rules load without error
- Test rule execution (execute, validate)
- Test rule result format
- Test batch rule execution

**AC-E6-083: Mypy Type Checking**
- `mypy ai_architect_mcp/` passes with no errors
- All type hints are correct
- No `Any` types without justification

**AC-E6-084: Ruff Linting**
- `ruff check ai_architect_mcp/` passes with no errors
- Code style is consistent (PEP 8 compliant)
- No unused imports or variables

**AC-E6-085: Security Audit**
- `pip-audit` finds no known vulnerabilities in dependencies
- No hardcoded secrets in code
- Config files with sensitive data can be protected (file permissions)

---

## Summary Table

| Category | AC Range | Count | Status |
|----------|----------|-------|--------|
| Package & Distribution | AC-E6-001 to AC-E6-010 | 10 | Pending |
| CLI Implementation | AC-E6-011 to AC-E6-020 | 10 | Pending |
| Configuration System | AC-E6-021 to AC-E6-032 | 12 | Pending |
| Tool Verification | AC-E6-033 to AC-E6-045 | 13 | Pending |
| Algorithm & Rules | AC-E6-046 to AC-E6-055 | 10 | Pending |
| Cross-Version & Compat | AC-E6-056 to AC-E6-065 | 10 | Pending |
| Documentation & Delivery | AC-E6-066 to AC-E6-075 | 10 | Pending |
| Testing & Quality | AC-E6-076 to AC-E6-085 | 10 | Pending |
| **TOTAL** | | **85** | |

