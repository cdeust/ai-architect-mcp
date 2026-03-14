# Epic 6: Python MCP Server Migration — User Stories

**Epic ID:** E6
**Document:** prd-user-stories.md
**Total SP:** 59 (Fibonacci: 3, 5, 8)

---

## STORY-E6-001: CLI Entry Point Implementation

**As a** DevOps engineer
**I want to** invoke the AI Architect MCP server via command line
**So that** I can start the server in production and development environments

**SP:** 5

**Description:**
Implement `ai-architect-mcp` CLI entry point using click framework. Support three main subcommands:
- `serve` — Start MCP server
- `version` — Print package version
- `health` — Query server health status

Entry point registered in pyproject.toml as `ai_architect_mcp.__main__:main()`.

**Acceptance Criteria:**

- AC-E6-001-1: `ai-architect-mcp --help` displays all subcommands and global flags
- AC-E6-001-2: `ai-architect-mcp version` outputs "ai-architect-mcp 0.1.0\n"
- AC-E6-001-3: `ai-architect-mcp serve` starts FastMCP server without errors; logs "Server running on port 3000"
- AC-E6-001-4: `ai-architect-mcp health` queries running server; returns JSON with status, version, tool count
- AC-E6-001-5: CLI exits with code 0 on success, non-zero on error (invalid command, missing dependency)
- AC-E6-001-6: All CLI functions have docstrings and type hints

**Definition of Done:**
- Code complete and reviewed
- Unit tests pass (test_cli.py)
- Manual testing on macOS, Linux, Windows (or CI equivalent)
- No mypy or ruff violations

---

## STORY-E6-002: TOML Configuration Loader with Environment Override

**As a** platform engineer
**I want to** configure the MCP server via TOML file with environment variable overrides
**So that** I can deploy the same image in dev, staging, and production with different configs

**SP:** 5

**Description:**
Implement configuration loader (`ai_architect_mcp._config.loader`) that:
1. Reads TOML config file from standard location (or custom path via `--config` flag)
2. Merges with defaults from defaults.toml
3. Applies environment variable overrides (AI_ARCHITECT_* prefix)
4. Validates config against Pydantic schema
5. Raises ConfigError with actionable message on failure

Support hierarchical override:
- Default < Config file < Environment variable < CLI flag

**Acceptance Criteria:**

- AC-E6-002-1: `loader.load_config(path)` successfully parses valid TOML files
- AC-E6-002-2: Environment variables override config file values (e.g., AI_ARCHITECT_PORT=3001)
- AC-E6-002-3: Missing config file defaults to ~/.config/ai-architect/config.toml; if missing, uses in-code defaults
- AC-E6-002-4: Invalid TOML raises ConfigError with line number and suggestion (e.g., "Invalid key 'foo' on line 5")
- AC-E6-002-5: Type validation: port must be int 1024–65535; timeout must be positive int; log_level must be string in [debug, info, warning, error]
- AC-E6-002-6: Config object (Pydantic model) is immutable and serializable to dict/JSON
- AC-E6-002-7: `defaults.toml` bundled with package and validated at build time

**Definition of Done:**
- Code complete and reviewed
- test_config.py passes (all happy path and error cases)
- TOML schema documented in README or defaults.toml comments
- No mypy violations

---

## STORY-E6-003: PyPI Package Metadata and Build System

**As a** release manager
**I want to** publish ai-architect-mcp to PyPI with correct metadata and dependencies
**So that** users can `pip install ai-architect-mcp` and get a working package

**SP:** 3

**Description:**
Update and finalize pyproject.toml with all PyPI metadata:
- Package name, version, description
- Dependencies and optional-dependencies
- Entry points (ai-architect-mcp CLI)
- Classifiers (Development Status, Python Versions, License, Topics)
- Author, repository, homepage URLs
- License field (MIT)

Validate build process:
- `pip install -e .` succeeds and registers CLI
- `python -m build` creates valid wheel
- Wheel is <10 MB compressed

**Acceptance Criteria:**

- AC-E6-003-1: pyproject.toml has [project] section with name="ai-architect-mcp", version="0.1.0", description, requires-python=">=3.12"
- AC-E6-003-2: [project.scripts] has entry: ai_architect_mcp = "ai_architect_mcp.__main__:main"
- AC-E6-003-3: [project.dependencies] includes: fastmcp, pydantic>=2.0, anthropic, scipy, aiofiles, numpy, click (or typer)
- AC-E6-003-4: [project.optional-dependencies] has dev=[pytest, pytest-asyncio, mypy, ruff]
- AC-E6-003-5: Classifiers include: Development Status :: 3 - Alpha, License :: OSI Approved :: MIT License, Python :: 3.12, Python :: 3.13
- AC-E6-003-6: Author and repository URLs set correctly
- AC-E6-003-7: `pip install -e .` succeeds; `ai-architect-mcp --help` works without error
- AC-E6-003-8: Built wheel file <10 MB; `pip install <wheel>` succeeds in clean environment

**Definition of Done:**
- pyproject.toml reviewed and merged
- Build tested on CI (Python 3.12, 3.13)
- No warnings during wheel creation

---

## STORY-E6-004: Verify 32 Tools in Package Context

**As a** QA engineer
**I want to** ensure all 32 tools are registered and callable when the package is installed
**So that** migrations from Node.js don't lose any functionality

**SP:** 8

**Description:**
Test that all 32 tools register correctly in package context:
- 5 verification tools (verify_claim, decompose_claim, consensus_debate, nli_eval, graph_constrain)
- 8 HOR tools (execute_hor_rule, list_hor_rules, validate_rule, etc.)
- 6 prompting tools (enhance_prompt, select_strategy, apply_enhancement, etc.)
- 5 context tools (load_context, save_context, query_context, etc.)
- 5 adapter tools (git_status, github_search, xcode_command, filesystem_read, filesystem_write)
- 3 scoring tools (compound_score, propagate_score, normalize_score)

For each tool:
- Verify name and description
- Verify input parameters and types
- Verify output schema matches Pydantic model
- Execute with sample input and validate response

**Acceptance Criteria:**

- AC-E6-004-1: `mcp.list_tools()` returns exactly 32 tools
- AC-E6-004-2: All tool names start with `ai_architect_` prefix
- AC-E6-004-3: Each tool has docstring describing purpose, args, returns
- AC-E6-004-4: Verification tools (5) execute successfully with test inputs and return ClaimEvaluation responses
- AC-E6-004-5: HOR tools (8) execute successfully; execute_hor_rule returns RuleResult with passed/failed status
- AC-E6-004-6: Prompting tools (6) execute successfully; enhance_prompt returns enhanced string
- AC-E6-004-7: Context tools (5) execute successfully; load_context returns StageContext model
- AC-E6-004-8: Adapter tools (5) execute successfully; git_status returns repo status dict
- AC-E6-004-9: Scoring tools (3) execute successfully; compound_score returns float 0–100
- AC-E6-004-10: Tool response time <5s (p95) for each tool category

**Definition of Done:**
- test_tool_registration.py passes all 32 tool tests
- test_tool_execution.py passes with sample inputs
- Test coverage >95% for tool invocation path
- No mypy or ruff violations

---

## STORY-E6-005: Verify Verification Algorithms in Package Context

**As a** verification engineer
**I want to** ensure all 7 verification algorithms are accessible and functional when packaged
**So that** the verification pipeline doesn't degrade in production

**SP:** 5

**Description:**
Test that all 7 verification algorithms are imported, instantiated, and executable in package context:
1. AtomicClaimDecomposer — Decompose claims into atomic facts
2. ChainOfVerification — Multi-step verification process
3. NLIEntailmentEvaluator — Natural language inference evaluation
4. MultiAgentDebate — Debate-based consensus
5. WeightedAverageConsensus — Weighted aggregation
6. AdaptiveStabilityConsensus — Stability-based consensus
7. GraphConstrainedVerifier — Dependency constraint satisfaction

For each algorithm:
- Verify class is importable
- Verify __init__ works with expected parameters
- Verify execute/run method is callable
- Verify output matches expected schema
- Verify handles edge cases (empty input, invalid state)

**Acceptance Criteria:**

- AC-E6-005-1: All 7 algorithm classes importable from ai_architect_mcp._verification.algorithms
- AC-E6-005-2: AtomicClaimDecomposer.decompose() returns list of atomic claims
- AC-E6-005-3: ChainOfVerification.verify() returns VerificationReport with confidence score
- AC-E6-005-4: NLIEntailmentEvaluator.evaluate() returns entailment score (0–1)
- AC-E6-005-5: MultiAgentDebate.debate() returns consensus result with agent opinions
- AC-E6-005-6: WeightedAverageConsensus.consensus() returns weighted score (0–1)
- AC-E6-005-7: AdaptiveStabilityConsensus.consensus() returns stability-adjusted score
- AC-E6-005-8: GraphConstrainedVerifier.verify() returns constrained evaluation respecting dependencies
- AC-E6-005-9: Each algorithm handles empty input without crashing (returns sensible default or raises ValueError)
- AC-E6-005-10: All algorithms accessible via tool interface (ai_architect_verify_claim, etc.)

**Definition of Done:**
- test_algorithm_access.py passes all 7 algorithm tests
- test_algorithm_edge_cases.py handles null, empty, and malformed inputs
- Test coverage >90%
- No mypy violations

---

## STORY-E6-006: Verify Strategies & Enhancements in Package Context

**As a** prompting engineer
**I want to** ensure all 16 thinking strategies and 5 enhancements work in the packaged server
**So that** prompt optimization is fully available post-migration

**SP:** 5

**Description:**
Test that all 16 strategies and 5 enhancements are accessible and functional:

**Strategies (16):**
- tree_of_thought, chain_of_thought, zero_shot, few_shot, in_context_learning
- self_consistency, uncertainty_quantification, step_back_prompting, multi_hop_reasoning
- analogical_reasoning, constraint_satisfaction, counterfactual_reasoning
- perspective_taking, dialogue_based, meta_learning, retrieval_augmented

**Enhancements (5):**
- Clarity enhancement
- Detail enhancement
- Specificity enhancement
- Structure enhancement
- Reasoning enhancement

For each:
- Verify class/function is importable
- Verify can be selected/instantiated
- Verify can be applied to test prompt
- Verify output is a valid string
- Verify metadata is accurate

**Acceptance Criteria:**

- AC-E6-006-1: All 16 strategies listed in prompting module
- AC-E6-006-2: Strategy selection via ai_architect_thinking_strategy_select works; returns selected strategy name
- AC-E6-006-3: Each strategy can be applied to test prompt; returns enhanced string
- AC-E6-006-4: All 5 enhancements listed in prompting module
- AC-E6-006-5: Enhancement application via ai_architect_prompt_enhance works for each enhancement type
- AC-E6-006-6: Enhanced prompts are different from input (not just returned as-is)
- AC-E6-006-7: Strategy metadata (description, category, use_cases) is complete and accurate
- AC-E6-006-8: Enhancement metadata (type, effect, example_diff) is documented
- AC-E6-006-9: Chained application (strategy + enhancement) works without error
- AC-E6-006-10: Edge case: empty prompt, very long prompt, special characters handled gracefully

**Definition of Done:**
- test_strategies.py passes; tests all 16 strategies
- test_enhancements.py passes; tests all 5 enhancements
- test_strategy_chaining.py passes
- Test coverage >90%

---

## STORY-E6-007: Verify 64 HOR Rules in Package Context

**As a** verification lead
**I want to** ensure all 64 HOR (Hierarchical Optimization Rules) rules execute correctly in the packaged server
**So that** rule-based optimization is available in production

**SP:** 5

**Description:**
Test that all 64 HOR rules load, register, and execute without error in package context.

Rules are organized by category (estimated from Epic 2):
- Clarity rules (8–10)
- Reasoning rules (8–10)
- Structure rules (8–10)
- Constraints rules (8–10)
- Adaptation rules (8–10)
- Other rules (remaining to ~64)

For each rule:
- Verify rule ID and name
- Verify rule loads from rule store
- Verify rule has preconditions and effects
- Verify rule executes on sample input
- Verify rule output includes: status (pass/fail), score, metadata
- Verify rule respects dependency order

**Acceptance Criteria:**

- AC-E6-007-1: HOR rule store loads all 64 rules without error
- AC-E6-007-2: All rule IDs are unique (no duplicates)
- AC-E6-007-3: Each rule has: name (string), precondition (callable or string), effect (callable or string), priority (int)
- AC-E6-007-4: ai_architect_execute_hor_rule can execute any of the 64 rules with valid inputs
- AC-E6-007-5: Rule execution returns RuleResult with: rule_id, passed (bool), score (float 0–100), metadata (dict)
- AC-E6-007-6: Batch rule execution (execute multiple rules) respects dependency graph; no circular deps
- AC-E6-007-7: Rule violations are reported with: rule_id, violation_type, suggestion for remediation
- AC-E6-007-8: Rules handle edge cases: null values, invalid types, missing context gracefully
- AC-E6-007-9: ai_architect_list_hor_rules returns all 64 rule IDs and descriptions
- AC-E6-007-10: Rule validation via ai_architect_validate_hor_rule succeeds for all 64 rules

**Definition of Done:**
- test_hor_in_package.py passes all 64 rule tests
- test_hor_batch_execution.py passes
- test_hor_dependency_order.py passes
- Test coverage >85%
- HOR rule count audit performed (confirm 64 rules)

---

## STORY-E6-008: Create Migration Guide from Node.js to Python

**As a** migration lead
**I want to** have a complete step-by-step guide for migrating from Node.js MCP server to Python engine
**So that** the team can transition workflows with zero downtime and high confidence

**SP:** 5

**Description:**
Create comprehensive migration documentation including:
1. Pre-migration checklist (inventory current Node.js tools, validate tool usage, backup configs)
2. Node.js → Python tool mapping (13 Node.js tools → 32 Python tools; explain new tools)
3. Configuration translation (Node.js env vars → TOML + Python env vars)
4. Step-by-step migration procedure (start Python server, validate all tools, switch DNS/routing, monitor)
5. Testing and validation (run smoke tests, compare outputs, performance benchmarks)
6. Rollback plan (if issues detected, return to Node.js with minimal data loss)
7. Troubleshooting guide (common errors, logs to check, debugging)
8. Performance comparison (Node.js vs Python latency, memory, throughput)

Document format: Markdown with code examples, diagrams, and checklists.

**Acceptance Criteria:**

- AC-E6-008-1: Pre-migration checklist has ≥5 items; printable one-pager available
- AC-E6-008-2: Tool mapping table covers 13 Node.js tools → Python equivalents (100% coverage)
- AC-E6-008-3: For each Node.js tool, document: new Python tool name, parameter mapping, response schema diff (if any)
- AC-E6-008-4: Configuration translation guide shows: example Node.js env config → TOML/Python env config
- AC-E6-008-5: Step-by-step procedure is clear and actionable; includes commands to run at each stage
- AC-E6-008-6: Testing guide includes: unit tests to run, integration scenarios, performance benchmarks to collect
- AC-E6-008-7: Rollback plan includes: data backup procedure, Node.js server restart steps, validation after rollback
- AC-E6-008-8: Troubleshooting covers ≥5 common errors: tool not found, config parsing error, tool timeout, performance degradation, etc.
- AC-E6-008-9: Document includes: estimated migration time, team coordination steps, communication template
- AC-E6-008-10: Document is peer-reviewed and approved by migration lead and at least one engineer not on Epic 6 team

**Definition of Done:**
- docs/MIGRATION_GUIDE.md written and reviewed
- Tool mapping table peer-reviewed for accuracy
- Rollback plan tested in staging
- Links to all referenced commands/docs valid

---

## STORY-E6-009: Create Python API Reference Documentation

**As a** developer integrating AI Architect
**I want to** complete API reference documentation for all tools and config options
**So that** I can use the package without reading source code

**SP:** 5

**Description:**
Generate comprehensive API reference documentation:
1. Tool reference (all 32 tools):
   - Name, description, parameters, return type, examples
   - Node.js equivalent (if applicable)
   - Typical use cases
2. Configuration reference:
   - All config sections, fields, types, defaults
   - Environment variable names and examples
   - Validation rules
3. CLI reference:
   - All commands (serve, version, health, config-validate)
   - Flags, options, examples
   - Exit codes
4. Models & types:
   - Pydantic models used by tools (VerificationReport, ClaimEvaluation, etc.)
   - Field descriptions and constraints
5. Health endpoint specification:
   - Response format, status values, interpretation
6. Error codes and handling:
   - Standard error codes returned by tools
   - Interpretation and remediation

Format: Auto-generated from docstrings + hand-written examples; hosted as HTML or in GitHub wiki.

**Acceptance Criteria:**

- AC-E6-009-1: Tool reference has entry for all 32 tools with name, description, parameters, return, example
- AC-E6-009-2: For each tool: parameter types documented with constraints (e.g., port 1024–65535)
- AC-E6-009-3: For each tool: return type documented with example JSON/dict
- AC-E6-009-4: For each tool: at least one usage example (Python code or curl/MCP request)
- AC-E6-009-5: Configuration reference covers all config sections and fields
- AC-E6-009-6: For each config field: type, default, valid range/values, and purpose
- AC-E6-009-7: CLI reference has entry for all 4 commands with flags and examples
- AC-E6-009-8: Models reference documents all public Pydantic models used in responses
- AC-E6-009-9: Health endpoint specification includes: response format, status values, interpretation guide
- AC-E6-009-10: Error codes documented with: error code, meaning, common causes, remediation steps
- AC-E6-009-11: Documentation is peer-reviewed for accuracy and completeness
- AC-E6-009-12: All code examples are tested and verified to work

**Definition of Done:**
- docs/API_REFERENCE.md (or docs/api/) complete
- All tool examples tested
- Documentation auto-generated where possible (docstring extraction)
- Links to source code available for deeper investigation
- No broken links or references

---

## STORY-E6-010: TestPyPI Publish & Cross-Version Testing

**As a** release engineer
**I want to** publish to TestPyPI and verify installation on multiple Python versions
**So that** production publish is low-risk

**SP:** 5

**Description:**
Set up TestPyPI publishing workflow and validate package on Python 3.12 and 3.13:
1. Build wheel and source distribution
2. Publish to TestPyPI (test.pypi.org)
3. Create test environments for Python 3.12 and 3.13
4. Install package from TestPyPI
5. Validate all tools, CLI commands, and config loading work
6. Benchmark install time and package size
7. Test in Docker container (optional but recommended)

Testing includes:
- CLI help, version, health commands
- Tool registration and invocation
- Config loading and env var overrides
- Cross-version compatibility

**Acceptance Criteria:**

- AC-E6-010-1: Wheel and source distribution build without warnings
- AC-E6-010-2: Package published to TestPyPI successfully
- AC-E6-010-3: Installation via `pip install -i https://test.pypi.org/simple/ ai-architect-mcp` succeeds on Python 3.12
- AC-E6-010-4: Installation via `pip install -i https://test.pypi.org/simple/ ai-architect-mcp` succeeds on Python 3.13
- AC-E6-010-5: All CLI commands work after installation (version, health, serve --help)
- AC-E6-010-6: All 32 tools register and are callable after installation
- AC-E6-010-7: Config loading works with test TOML file
- AC-E6-010-8: Environment variable overrides (AI_ARCHITECT_PORT=3001) work correctly
- AC-E6-010-9: Install time is <30 seconds (both 3.12 and 3.13)
- AC-E6-010-10: Package size is <10 MB compressed
- AC-E6-010-11: No breaking differences between Python 3.12 and 3.13 test runs
- AC-E6-010-12: Docker build (optional) succeeds; image size <500 MB

**Definition of Done:**
- TestPyPI publish workflow documented
- Test results (pass/fail) for both Python versions documented
- Installation guide for TestPyPI available
- Feedback addressed before production publish

---

## STORY-E6-011: Production PyPI Publish

**As a** release manager
**I want to** publish ai-architect-mcp to PyPI for general availability
**So that** users can install it via `pip install ai-architect-mcp`

**SP:** 3

**Description:**
Publish finalized package to PyPI:
1. Finalize version number (0.1.0 for initial release)
2. Update changelog
3. Tag release in git
4. Build wheel (hatchling automatically)
5. Publish to PyPI via GitHub Actions or local script
6. Verify package is discoverable on Pypi.org
7. Update package documentation links to point to PyPI

**Acceptance Criteria:**

- AC-E6-011-1: Package version is 0.1.0 in pyproject.toml
- AC-E6-011-2: CHANGELOG.md has entry for v0.1.0 with all features and fixes
- AC-E6-011-3: Git tag v0.1.0 created and pushed
- AC-E6-011-4: Wheel published to PyPI successfully
- AC-E6-011-5: Package is discoverable on pypi.org/project/ai-architect-mcp/
- AC-E6-011-6: `pip install ai-architect-mcp` installs from PyPI (not TestPyPI)
- AC-E6-011-7: Package page includes: description, README, installation instructions, links to docs
- AC-E6-011-8: Release notes are published in GitHub Releases

**Definition of Done:**
- Package published to PyPI
- Installation verified in clean environment
- PyPI page reviewed for correctness
- Release notes published

---

## STORY-E6-012: MCP Protocol Compatibility Verification

**As a** protocol engineer
**I want to** verify the Python MCP server is fully compatible with the MCP protocol specification
**So that** it works with all MCP clients (Claude, Cursor, other tools)

**SP:** 5

**Description:**
Comprehensive testing of MCP protocol compliance:
1. Verify server responds to protocol initialization requests
2. Verify tool listing (list_tools) returns correct schema
3. Verify tool invocation (call_tool) marshals requests and responses correctly
4. Verify error responses follow MCP spec (error codes, messages)
5. Verify server lifecycle (startup, ready, shutdown) follows spec
6. Test with multiple MCP clients (Claude SDK, Cursor, cli)
7. Verify request/response format matches FastMCP expectations
8. Verify async handling and concurrency

**Acceptance Criteria:**

- AC-E6-012-1: Server responds to protocol initialization handshake within 1 second
- AC-E6-012-2: list_tools returns all 32 tools with correct schema (name, description, inputSchema)
- AC-E6-012-3: call_tool properly marshals request parameters to tool function arguments
- AC-E6-012-4: Tool responses are JSON-serializable and follow expected schema
- AC-E6-012-5: Error responses include: error code, message, data (if applicable)
- AC-E6-012-6: Server handles multiple concurrent tool invocations without deadlock
- AC-E6-012-7: Server shutdown gracefully closes all connections and resources
- AC-E6-012-8: Protocol compatibility verified with ≥2 different MCP clients
- AC-E6-012-9: No protocol-related errors in test logs
- AC-E6-012-10: Response latency is consistent across tools (not degraded for later calls)

**Definition of Done:**
- test_mcp_protocol_compatibility.py passes all tests
- Protocol testing verified with multiple clients
- No blocking issues found
- Compatibility statement published in docs

---

## Story Point Summary

| Story | Title | SP | Sprint |
|-------|-------|----|----|
| STORY-E6-001 | CLI Entry Point | 5 | 1 |
| STORY-E6-002 | TOML Config + Env Override | 5 | 1 |
| STORY-E6-003 | PyPI Packaging | 3 | 2 |
| STORY-E6-004 | Verify 32 Tools | 8 | 3 |
| STORY-E6-005 | Verify Algorithms | 5 | 4 |
| STORY-E6-006 | Verify Strategies & Enhancements | 5 | 4 |
| STORY-E6-007 | Verify 64 HOR Rules | 5 | 4 |
| STORY-E6-008 | Migration Guide | 5 | 5 |
| STORY-E6-009 | API Reference Docs | 5 | 5 |
| STORY-E6-010 | TestPyPI Publish | 5 | 6 |
| STORY-E6-011 | Production PyPI Publish | 3 | 6 |
| STORY-E6-012 | MCP Protocol Verification | 5 | 6 |
| | **TOTAL** | **59** | |

