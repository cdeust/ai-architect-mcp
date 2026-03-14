# Epic 6: Python MCP Server Migration — JIRA Issues

**Epic ID:** E6
**Document:** prd-jira.md
**Total Issues:** 12 (one per user story)
**Total SP:** 59

---

## JIRA Issue Specifications

### E6-1: Implement CLI Entry Point

**Issue Key:** E6-1
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 1
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Implement CLI Entry Point with Click Framework

**Description:**
Implement `ai-architect-mcp` CLI entry point using click framework. Support four subcommands:
1. `serve` — Start MCP server
2. `version` — Print package version
3. `health` — Query server health status
4. `config-validate` — Validate TOML config file

Entry point registered in pyproject.toml as `ai_architect_mcp = "ai_architect_mcp.__main__:main"`.

**Acceptance Criteria:**
- `ai-architect-mcp --help` displays all subcommands and global flags
- `ai-architect-mcp version` outputs "ai-architect-mcp 0.1.0\n"
- `ai-architect-mcp serve` starts FastMCP server without errors; logs "Server running on port 3000"
- `ai-architect-mcp health` queries running server; returns JSON with status, version, tool count
- CLI exits with code 0 on success, non-zero on error (invalid command, missing dependency)
- All CLI functions have docstrings and type hints

**Labels:** cli, feature, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Create ai_architect_mcp/__main__.py with click structure
- [ ] Implement serve subcommand
- [ ] Implement version subcommand
- [ ] Implement health subcommand
- [ ] Implement config-validate subcommand
- [ ] Write test_cli.py
- [ ] Code review

---

### E6-2: Implement TOML Config Loader with Environment Override

**Issue Key:** E6-2
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 1
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Implement Configuration System with TOML Loader and Environment Variable Override

**Description:**
Implement configuration loader (`ai_architect_mcp._config.loader`) that:
1. Reads TOML config file from standard location (or custom path via `--config` flag)
2. Merges with defaults from defaults.toml
3. Applies environment variable overrides (AI_ARCHITECT_* prefix)
4. Validates config against Pydantic schema
5. Raises ConfigError with actionable message on failure

Support hierarchical override: Default < Config file < Environment variable < CLI flag

**Acceptance Criteria:**
- `loader.load_config(path)` successfully parses valid TOML files
- Environment variables override config file values (e.g., AI_ARCHITECT_PORT=3001)
- Missing config file defaults to ~/.config/ai-architect/config.toml; if missing, uses in-code defaults
- Invalid TOML raises ConfigError with line number and suggestion (e.g., "Invalid key 'foo' on line 5")
- Type validation: port must be int 1024–65535; timeout must be positive int; log_level must be string in [debug, info, warning, error]
- Config object (Pydantic model) is immutable and serializable to dict/JSON
- `defaults.toml` bundled with package and validated at build time

**Labels:** config, feature, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Create _config/models.py with Pydantic schemas
- [ ] Create _config/loader.py with TOML parser
- [ ] Create _config/defaults.toml
- [ ] Implement environment variable override logic
- [ ] Implement validation and error handling
- [ ] Write test_config.py
- [ ] Code review

---

### E6-3: Finalize PyPI Package Metadata and Build System

**Issue Key:** E6-3
**Issue Type:** Story
**Story Points:** 3
**Sprint:** 2
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Finalize PyPI Package Metadata and Build System

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
- pyproject.toml has [project] section with name="ai-architect-mcp", version="0.1.0", description, requires-python=">=3.12"
- [project.scripts] has entry: ai_architect_mcp = "ai_architect_mcp.__main__:main"
- [project.dependencies] includes: fastmcp, pydantic>=2.0, anthropic, scipy, aiofiles, numpy, click (or typer)
- [project.optional-dependencies] has dev=[pytest, pytest-asyncio, mypy, ruff]
- Classifiers include: Development Status :: 3 - Alpha, License :: OSI Approved :: MIT License, Python :: 3.12, Python :: 3.13
- Author and repository URLs set correctly
- `pip install -e .` succeeds; `ai-architect-mcp --help` works without error
- Built wheel file <10 MB; `pip install <wheel>` succeeds in clean environment

**Labels:** packaging, build-system, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Update pyproject.toml with all fields
- [ ] Add entry_points section
- [ ] Add classifiers
- [ ] Create LICENSE file (MIT)
- [ ] Test `pip install -e .` on Python 3.12, 3.13
- [ ] Test wheel build and size
- [ ] Code review

---

### E6-4: Verify 32 Tools in Package Context

**Issue Key:** E6-4
**Issue Type:** Story
**Story Points:** 8
**Sprint:** 3
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Verify All 32 Tools Register and Function in Package Context

**Description:**
Test that all 32 tools register correctly in package context and are callable with correct schemas:
- 5 verification tools
- 8 HOR tools
- 6 prompting tools
- 5 context tools
- 5 adapter tools
- 3 scoring tools

For each tool: verify name, description, parameters, output schema, execution time.

**Acceptance Criteria:**
- `mcp.list_tools()` returns exactly 32 tools
- All tool names start with `ai_architect_` prefix
- Each tool has docstring describing purpose, args, returns
- Verification tools (5) execute successfully with test inputs and return ClaimEvaluation responses
- HOR tools (8) execute successfully; execute_hor_rule returns RuleResult with passed/failed status
- Prompting tools (6) execute successfully; enhance_prompt returns enhanced string
- Context tools (5) execute successfully; load_context returns StageContext model
- Adapter tools (5) execute successfully; git_status returns repo status dict
- Scoring tools (3) execute successfully; compound_score returns float 0–100
- Tool response time <5s (p95) for each tool category

**Labels:** testing, verification, tools, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Write test_tool_registration.py
- [ ] Write test_tool_execution.py
- [ ] Test all 32 tools register
- [ ] Test all 32 tools execute
- [ ] Collect performance metrics
- [ ] Verify tool annotations
- [ ] Code review

---

### E6-5: Verify Verification Algorithms in Package Context

**Issue Key:** E6-5
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 4
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Verify All 7 Verification Algorithms in Package Context

**Description:**
Test that all 7 verification algorithms are imported, instantiated, and executable in package context:
1. AtomicClaimDecomposer
2. ChainOfVerification
3. NLIEntailmentEvaluator
4. MultiAgentDebate
5. WeightedAverageConsensus
6. AdaptiveStabilityConsensus
7. GraphConstrainedVerifier

For each: verify class is importable, __init__ works, execute/run method is callable, output matches expected schema, edge cases handled.

**Acceptance Criteria:**
- All 7 algorithm classes importable from ai_architect_mcp._verification.algorithms
- AtomicClaimDecomposer.decompose() returns list of atomic claims
- ChainOfVerification.verify() returns VerificationReport with confidence score
- NLIEntailmentEvaluator.evaluate() returns entailment score (0–1)
- MultiAgentDebate.debate() returns consensus result with agent opinions
- WeightedAverageConsensus.consensus() returns weighted score (0–1)
- AdaptiveStabilityConsensus.consensus() returns stability-adjusted score
- GraphConstrainedVerifier.verify() returns constrained evaluation respecting dependencies
- Each algorithm handles empty input without crashing (returns sensible default or raises ValueError)
- All algorithms accessible via tool interface

**Labels:** testing, verification, algorithms, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Write test_algorithm_access.py
- [ ] Test all 7 algorithms importable
- [ ] Test all 7 algorithms executable
- [ ] Test algorithm edge cases
- [ ] Verify algorithm output schemas
- [ ] Code review

---

### E6-6: Verify Strategies & Enhancements in Package Context

**Issue Key:** E6-6
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 4
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Verify All 16 Strategies and 5 Enhancements in Package Context

**Description:**
Test that all 16 thinking strategies and 5 enhancements work in the packaged server.

**Strategies (16):** tree_of_thought, chain_of_thought, zero_shot, few_shot, in_context_learning, self_consistency, uncertainty_quantification, step_back_prompting, multi_hop_reasoning, analogical_reasoning, constraint_satisfaction, counterfactual_reasoning, perspective_taking, dialogue_based, meta_learning, retrieval_augmented

**Enhancements (5):** clarity, detail, specificity, structure, reasoning

For each: verify importable, instantiable, applicable to test prompt, output valid string, metadata accurate.

**Acceptance Criteria:**
- All 16 strategies listed in prompting module
- Strategy selection via ai_architect_thinking_strategy_select works; returns selected strategy name
- Each strategy can be applied to test prompt; returns enhanced string
- All 5 enhancements listed in prompting module
- Enhancement application via ai_architect_prompt_enhance works for each enhancement type
- Enhanced prompts are different from input (not just returned as-is)
- Strategy metadata (description, category, use_cases) is complete and accurate
- Enhancement metadata (type, effect, example_diff) is documented
- Chained application (strategy + enhancement) works without error
- Edge case: empty prompt, very long prompt, special characters handled gracefully

**Labels:** testing, verification, prompting, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Write test_strategies.py
- [ ] Write test_enhancements.py
- [ ] Write test_strategy_chaining.py
- [ ] Test all 16 strategies
- [ ] Test all 5 enhancements
- [ ] Test chaining
- [ ] Code review

---

### E6-7: Verify 64 HOR Rules in Package Context

**Issue Key:** E6-7
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 4
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Verify All 64 HOR Rules Execute in Package Context

**Description:**
Test that all 64 HOR (Hierarchical Optimization Rules) rules load, register, and execute without error in package context.

For each rule: verify rule ID and name, rule loads from rule store, rule has preconditions and effects, rule executes on sample input, rule output includes status (pass/fail), score, metadata, rule respects dependency order.

**Acceptance Criteria:**
- HOR rule store loads all 64 rules without error
- All rule IDs are unique (no duplicates)
- Each rule has: name (string), precondition (callable or string), effect (callable or string), priority (int)
- ai_architect_execute_hor_rule can execute any of the 64 rules with valid inputs
- Rule execution returns RuleResult with: rule_id, passed (bool), score (float 0–100), metadata (dict)
- Batch rule execution (execute multiple rules) respects dependency graph; no circular deps
- Rule violations are reported with: rule_id, violation_type, suggestion for remediation
- Rules handle edge cases: null values, invalid types, missing context gracefully
- ai_architect_list_hor_rules returns all 64 rule IDs and descriptions
- Rule validation via ai_architect_validate_hor_rule succeeds for all 64 rules

**Labels:** testing, verification, hor-rules, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Write test_hor_in_package.py
- [ ] Write test_hor_batch_execution.py
- [ ] Write test_hor_dependency_order.py
- [ ] Load and verify all 64 rules
- [ ] Test rule execution
- [ ] Test batch execution
- [ ] Audit rule count (confirm 64)
- [ ] Code review

---

### E6-8: Create Migration Guide from Node.js to Python

**Issue Key:** E6-8
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 5
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Create Comprehensive Migration Guide from Node.js to Python MCP Server

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

**Acceptance Criteria:**
- Pre-migration checklist has ≥5 items; printable one-pager available
- Tool mapping table covers 13 Node.js tools → Python equivalents (100% coverage)
- For each Node.js tool: document new Python tool name, parameter mapping, response schema diff (if any)
- Configuration translation guide shows: example Node.js env config → TOML/Python env config
- Step-by-step procedure is clear and actionable; includes commands to run at each stage
- Testing guide includes: unit tests to run, integration scenarios, performance benchmarks to collect
- Rollback plan includes: data backup procedure, Node.js server restart steps, validation after rollback
- Troubleshooting covers ≥5 common errors: tool not found, config parsing error, tool timeout, performance degradation, etc.
- Document includes: estimated migration time, team coordination steps, communication template
- Document is peer-reviewed and approved by migration lead and at least one engineer not on Epic 6 team

**Labels:** documentation, migration, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Create migration guide outline
- [ ] Write pre-migration checklist
- [ ] Create tool mapping table
- [ ] Write configuration translation section
- [ ] Write step-by-step migration procedure
- [ ] Write testing guide
- [ ] Write rollback plan
- [ ] Write troubleshooting
- [ ] Write performance comparison
- [ ] Peer review and revise
- [ ] Code review

---

### E6-9: Create Python API Reference Documentation

**Issue Key:** E6-9
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 5
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Create Complete Python API Reference Documentation

**Description:**
Generate comprehensive API reference documentation covering all tools, config options, CLI commands, models, and error codes.

Sections:
1. Tool reference (all 32 tools): name, description, parameters, return type, examples
2. Configuration reference: all config sections, fields, types, defaults
3. CLI reference: all commands, flags, options, examples, exit codes
4. Models & types: Pydantic models used by tools, field descriptions
5. Health endpoint specification: response format, status values, interpretation
6. Error codes and handling: standard error codes, interpretation, remediation

**Acceptance Criteria:**
- Tool reference has entry for all 32 tools with name, description, parameters, return, example
- For each tool: parameter types documented with constraints (e.g., port 1024–65535)
- For each tool: return type documented with example JSON/dict
- For each tool: at least one usage example (Python code or curl/MCP request)
- Configuration reference covers all config sections and fields
- For each config field: type, default, valid range/values, and purpose
- CLI reference has entry for all 4 commands with flags and examples
- Models reference documents all public Pydantic models used in responses
- Health endpoint specification includes: response format, status values, interpretation guide
- Error codes documented with: error code, meaning, common causes, remediation steps
- Documentation is peer-reviewed for accuracy and completeness
- All code examples are tested and verified to work

**Labels:** documentation, api-reference, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Create API reference structure
- [ ] Document all 32 tools
- [ ] Document all config options
- [ ] Document all CLI commands
- [ ] Document all models
- [ ] Document health endpoint
- [ ] Document error codes
- [ ] Create code examples
- [ ] Test all code examples
- [ ] Peer review and revise
- [ ] Code review

---

### E6-10: TestPyPI Publish & Cross-Version Testing

**Issue Key:** E6-10
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 6
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Publish to TestPyPI and Verify Cross-Version Compatibility

**Description:**
Set up TestPyPI publishing workflow and validate package on Python 3.12 and 3.13:
1. Build wheel and source distribution
2. Publish to TestPyPI (test.pypi.org)
3. Create test environments for Python 3.12 and 3.13
4. Install package from TestPyPI
5. Validate all tools, CLI commands, and config loading work
6. Benchmark install time and package size
7. Test in Docker container (optional but recommended)

**Acceptance Criteria:**
- Wheel and source distribution build without warnings
- Package published to TestPyPI successfully
- Installation via `pip install -i https://test.pypi.org/simple/ ai-architect-mcp` succeeds on Python 3.12
- Installation via `pip install -i https://test.pypi.org/simple/ ai-architect-mcp` succeeds on Python 3.13
- All CLI commands work after installation (version, health, serve --help)
- All 32 tools register and are callable after installation
- Config loading works with test TOML file
- Environment variable overrides (AI_ARCHITECT_PORT=3001) work correctly
- Install time is <30 seconds (both 3.12 and 3.13)
- Package size is <10 MB compressed
- No breaking differences between Python 3.12 and 3.13 test runs
- Docker build (optional) succeeds; image size <500 MB

**Labels:** publishing, testing, release, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Build wheel and source distribution
- [ ] Publish to TestPyPI
- [ ] Set up Python 3.12 test environment
- [ ] Set up Python 3.13 test environment
- [ ] Install from TestPyPI and test (3.12)
- [ ] Install from TestPyPI and test (3.13)
- [ ] Benchmark install time and size
- [ ] (Optional) Build and test Docker image
- [ ] Document results
- [ ] Code review

---

### E6-11: Production PyPI Publish

**Issue Key:** E6-11
**Issue Type:** Story
**Story Points:** 3
**Sprint:** 6
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Publish ai-architect-mcp to PyPI for Production

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
- Package version is 0.1.0 in pyproject.toml
- CHANGELOG.md has entry for v0.1.0 with all features and fixes
- Git tag v0.1.0 created and pushed
- Wheel published to PyPI successfully
- Package is discoverable on pypi.org/project/ai-architect-mcp/
- `pip install ai-architect-mcp` installs from PyPI (not TestPyPI)
- Package page includes: description, README, installation instructions, links to docs
- Release notes are published in GitHub Releases

**Labels:** publishing, release, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Finalize version number (0.1.0)
- [ ] Write CHANGELOG.md entry
- [ ] Create git tag v0.1.0
- [ ] Publish wheel to PyPI
- [ ] Verify package on pypi.org
- [ ] Test installation from PyPI
- [ ] Create GitHub Release
- [ ] Update documentation links
- [ ] Code review

---

### E6-12: MCP Protocol Compatibility Verification

**Issue Key:** E6-12
**Issue Type:** Story
**Story Points:** 5
**Sprint:** 6
**Status:** Not Started
**Assignee:** TBD
**Reporter:** Epic Lead

**Title:** Verify MCP Protocol Compatibility and Multi-Client Support

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
- Server responds to protocol initialization handshake within 1 second
- list_tools returns all 32 tools with correct schema (name, description, inputSchema)
- call_tool properly marshals request parameters to tool function arguments
- Tool responses are JSON-serializable and follow expected schema
- Error responses include: error code, message, data (if applicable)
- Server handles multiple concurrent tool invocations without deadlock
- Server shutdown gracefully closes all connections and resources
- Protocol compatibility verified with ≥2 different MCP clients
- No protocol-related errors in test logs
- Response latency is consistent across tools (not degraded for later calls)

**Labels:** testing, protocol, mcp, epic-6

**Epic Link:** E6

**Subtasks:**
- [ ] Write test_mcp_protocol_compatibility.py
- [ ] Test protocol initialization
- [ ] Test list_tools response format
- [ ] Test call_tool marshaling
- [ ] Test error response format
- [ ] Test server lifecycle
- [ ] Test with Claude SDK
- [ ] Test with Cursor (if available)
- [ ] Test concurrent invocations
- [ ] Code review

---

## JIRA CSV Export

```csv
Issue Key,Issue Type,Story Points,Sprint,Status,Summary,Epic Link
E6-1,Story,5,1,Not Started,Implement CLI Entry Point with Click Framework,E6
E6-2,Story,5,1,Not Started,Implement Configuration System with TOML Loader and Environment Override,E6
E6-3,Story,3,2,Not Started,Finalize PyPI Package Metadata and Build System,E6
E6-4,Story,8,3,Not Started,Verify All 32 Tools Register and Function in Package Context,E6
E6-5,Story,5,4,Not Started,Verify All 7 Verification Algorithms in Package Context,E6
E6-6,Story,5,4,Not Started,Verify All 16 Strategies and 5 Enhancements in Package Context,E6
E6-7,Story,5,4,Not Started,Verify All 64 HOR Rules Execute in Package Context,E6
E6-8,Story,5,5,Not Started,Create Comprehensive Migration Guide from Node.js to Python MCP Server,E6
E6-9,Story,5,5,Not Started,Create Complete Python API Reference Documentation,E6
E6-10,Story,5,6,Not Started,Publish to TestPyPI and Verify Cross-Version Compatibility,E6
E6-11,Story,3,6,Not Started,Publish ai-architect-mcp to PyPI for Production,E6
E6-12,Story,5,6,Not Started,Verify MCP Protocol Compatibility and Multi-Client Support,E6
```

