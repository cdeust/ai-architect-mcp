# Epic 6: Python MCP Server Migration — Roadmap

**Epic ID:** E6
**Document:** prd-roadmap.md
**Timeline:** 9–12 weeks
**Total SP:** 59

---

## Sprint Overview

| Sprint | Duration | Theme | Stories | SP | Goals |
|--------|----------|-------|---------|----|----|
| 1 | Weeks 1–2 | CLI & Config | E6-001, E6-002 | 10 | CLI entry point and TOML config loader operational |
| 2 | Weeks 3–4 | Packaging | E6-003 | 8 | PyPI metadata and build system finalized |
| 3 | Weeks 5–6 | Tool Verification | E6-004 | 13 | All 32 tools verified in package context |
| 4 | Weeks 7–8 | Algorithm Verification | E6-005, E6-006, E6-007 | 15 | Algorithms, strategies, HOR rules verified |
| 5 | Weeks 9–10 | Documentation | E6-008, E6-009 | 10 | Migration guide and API reference complete |
| 6 | Weeks 11–12 | Publish & Verify | E6-010, E6-011, E6-012 | 14 | TestPyPI and production publish, protocol verification |

**Total: 6 sprints, 59 SP, 12 weeks**

---

## Sprint 1: CLI & Configuration (Weeks 1–2, 10 SP)

### Stories
- **STORY-E6-001:** CLI Entry Point Implementation (5 SP)
- **STORY-E6-002:** TOML Configuration Loader with Environment Override (5 SP)

### Sprint Goal
Establish CLI interface and configuration system. Users can start the server via `ai-architect-mcp serve` with config file and environment variable support.

### Key Deliverables
1. `ai_architect_mcp/__main__.py` with click CLI framework
   - Subcommands: serve, version, health, config-validate
   - Help text, error handling, exit codes
2. `ai_architect_mcp/_config/loader.py` with TOML parsing
   - Pydantic config schema
   - Environment variable override hierarchy
   - Validation and error messages
3. `ai_architect_mcp/_config/defaults.toml` with sensible defaults
4. Unit tests (test_cli.py, test_config.py)
   - CLI help, version, error cases
   - Config loading, env override, validation

### Success Criteria (Sprint-Level)
- All 10 ACs from STORY-E6-001 pass
- All 7 ACs from STORY-E6-002 pass
- Code review approved
- Mypy and ruff clean
- Test coverage >85%

### Dependencies
- None (foundational sprint)

### Risks
- Click framework learning curve (low risk; framework is standard)
- TOML parsing edge cases (low risk; tomllib is well-tested)

---

## Sprint 2: Packaging (Weeks 3–4, 8 SP)

### Story
- **STORY-E6-003:** PyPI Package Metadata and Build System (3 SP)

### Sprint Goal
Finalize pyproject.toml for PyPI distribution. Package is buildable and installable.

### Key Deliverables
1. Finalized `pyproject.toml` with all PyPI metadata
   - Name, version, description
   - Dependencies and optional-dependencies
   - Entry points
   - Classifiers, author, repository, license
2. License file (MIT)
3. Build verification
   - Wheel builds successfully
   - Wheel <10 MB
   - Wheel installable in clean environment
4. Documentation (README.md, CHANGELOG.md skeleton)

### Success Criteria (Sprint-Level)
- All 8 ACs from STORY-E6-003 pass
- Wheel builds without errors or warnings
- Package installable on Python 3.12 and 3.13
- Entry point resolves after installation

### Dependencies
- Sprint 1 (CLI structure in place)

### Risks
- Dependency version conflicts (low risk; hatchling handles most of this)

---

## Sprint 3: Tool Verification (Weeks 5–6, 13 SP)

### Story
- **STORY-E6-004:** Verify 32 Tools in Package Context (8 SP)

### Sprint Goal
Comprehensive testing of all 32 tools in package context. Each tool registers, is callable, and returns correct schema.

### Key Deliverables
1. test_tool_registration.py
   - Tests all 32 tools register via mcp.list_tools()
   - Tests tool names, descriptions, parameters
   - Tests all 6 tool modules import without error
2. test_tool_execution.py
   - Executes each of 32 tools with sample input
   - Validates response schema matches Pydantic models
   - Tests tool error handling
3. Tool execution benchmarks
   - Performance metrics for each tool
   - Latency histogram (p50, p95, p99)
4. Tool annotation verification
   - Tests readOnlyHint, destructiveHint, idempotentHint, openWorldHint

### Success Criteria (Sprint-Level)
- All 13 ACs from STORY-E6-004 pass
- All 32 tools register and are callable
- Tool response time <5s (p95)
- Test coverage >95% for tool invocation path

### Dependencies
- Sprint 1 (CLI and config in place)
- Sprint 2 (packaging complete)

### Risks
- Tool response schema mismatch (low risk; schemas defined in existing code)
- Performance regression (low risk; baseline from existing engine)

---

## Sprint 4: Algorithm & Strategy Verification (Weeks 7–8, 15 SP)

### Stories
- **STORY-E6-005:** Verify Verification Algorithms in Package Context (5 SP)
- **STORY-E6-006:** Verify Strategies & Enhancements in Package Context (5 SP)
- **STORY-E6-007:** Verify 64 HOR Rules in Package Context (5 SP)

### Sprint Goal
Comprehensive testing of verification algorithms, prompting strategies, enhancements, and HOR rules. All components functional in packaged context.

### Key Deliverables
1. test_algorithm_access.py
   - Tests all 7 algorithms importable
   - Tests algorithm execution with sample inputs
   - Tests output format and types
   - Tests edge cases (null, empty, invalid)
2. test_strategies.py
   - Tests all 16 thinking strategies selectable and applicable
   - Tests strategy metadata (description, category)
   - Tests strategy selection logic
3. test_enhancements.py
   - Tests all 5 enhancements available and applicable
   - Tests enhancement composition
   - Tests effect on prompt text
4. test_hor_in_package.py
   - Loads all 64 HOR rules
   - Tests rule execution (execute, validate)
   - Tests rule result format
   - Tests batch execution and dependency order
5. Benchmarks and metrics
   - Algorithm execution time
   - Rule batch execution time
   - Strategy selection latency

### Success Criteria (Sprint-Level)
- All 10 ACs from STORY-E6-005 pass
- All 10 ACs from STORY-E6-006 pass
- All 10 ACs from STORY-E6-007 pass
- All 7 algorithms functional
- All 16 strategies selectable
- All 5 enhancements applicable
- All 64 HOR rules execute
- Test coverage >85% for each component

### Dependencies
- Sprint 3 (tools verified)

### Risks
- HOR rule count discrepancy (low risk; count established in Epic 2)
- Algorithm compatibility (low risk; components from existing engine)

---

## Sprint 5: Documentation (Weeks 9–10, 10 SP)

### Stories
- **STORY-E6-008:** Create Migration Guide from Node.js to Python (5 SP)
- **STORY-E6-009:** Create Python API Reference Documentation (5 SP)

### Sprint Goal
Complete documentation for migration and API reference. Users can understand and navigate the transition.

### Key Deliverables
1. docs/MIGRATION_GUIDE.md
   - Pre-migration checklist
   - Node.js → Python tool mapping (13 tools covered)
   - Configuration translation guide
   - Step-by-step migration procedure
   - Testing and validation guide
   - Rollback plan
   - Troubleshooting (5+ common errors)
   - Performance comparison
2. docs/API_REFERENCE.md (or docs/api/)
   - Tool reference (all 32 tools)
   - Configuration reference
   - CLI reference
   - Models & types reference
   - Health endpoint specification
   - Error codes and handling
   - Code examples (tested)
3. docs/QUICKSTART.md
   - Installation
   - Basic usage (serve, version, health)
   - Example config
   - Example tool invocation
4. docs/TROUBLESHOOTING.md
   - Common errors and solutions
   - Debug tips and log inspection
5. Updated README.md
   - Description and features
   - Installation instructions
   - Quick start
   - Tool overview
   - Configuration overview

### Success Criteria (Sprint-Level)
- All 10 ACs from STORY-E6-008 pass (migration guide complete)
- All 12 ACs from STORY-E6-009 pass (API reference complete)
- All documentation is peer-reviewed
- All code examples tested and working
- No broken links
- Spelling and grammar checked

### Dependencies
- Sprint 4 (all components verified; can document accurately)

### Risks
- Documentation accuracy (low risk; based on tested code)
- Maintenance burden (mitigated by auto-generating from docstrings where possible)

---

## Sprint 6: Publish & Verify (Weeks 11–12, 14 SP)

### Stories
- **STORY-E6-010:** TestPyPI Publish & Cross-Version Testing (5 SP)
- **STORY-E6-011:** Production PyPI Publish (3 SP)
- **STORY-E6-012:** MCP Protocol Compatibility Verification (5 SP)

### Sprint Goal
Finalize and publish package to PyPI. Verify protocol compliance and production readiness.

### Key Deliverables
1. TestPyPI publish workflow
   - Build wheel and source distribution
   - Publish to test.pypi.org
   - Document process (for future releases)
2. Cross-version testing
   - Install on Python 3.12 virtual environment
   - Install on Python 3.13 virtual environment
   - Test all CLI commands
   - Test tool registration and invocation
   - Performance benchmarks
   - Document results
3. Docker build (optional)
   - Dockerfile
   - Docker Compose example
   - Test Docker build and container runtime
4. test_mcp_protocol_compatibility.py
   - Protocol initialization handshake
   - list_tools response format
   - call_tool request/response marshaling
   - Error response format
   - Concurrent tool invocations
   - Test with multiple MCP clients (Claude SDK, Cursor, etc.)
5. Production publish
   - Finalize version number (0.1.0)
   - Update CHANGELOG.md
   - Create git tag v0.1.0
   - Publish wheel to PyPI
   - Verify package on pypi.org
   - Create GitHub release

### Success Criteria (Sprint-Level)
- All 12 ACs from STORY-E6-010 pass (TestPyPI and cross-version)
- All 8 ACs from STORY-E6-011 pass (production publish)
- All 10 ACs from STORY-E6-012 pass (protocol compatibility)
- Package published on PyPI
- Installation via `pip install ai-architect-mcp` works
- No critical issues found during cross-version testing
- Protocol compliance verified with multiple clients

### Dependencies
- Sprint 5 (documentation complete; ready for public release)
- All prior sprints (all components complete and tested)

### Risks
- PyPI publish workflow (low risk; standard process)
- Cross-version incompatibilities (low risk; tested with Makefile/CI)
- Protocol compliance issues (low risk; FastMCP is standard)

---

## Milestone Timeline

```
Week 1-2:  [SPRINT 1] CLI & Config
             ✓ CLI entry point
             ✓ TOML config loader
             ✓ Environment variable overrides

Week 3-4:  [SPRINT 2] Packaging
             ✓ pyproject.toml finalized
             ✓ Wheel builds
             ✓ Entry points register

Week 5-6:  [SPRINT 3] Tool Verification
             ✓ 32 tools verified
             ✓ Tool registration tests
             ✓ Tool execution benchmarks

Week 7-8:  [SPRINT 4] Algorithm Verification
             ✓ 7 algorithms verified
             ✓ 16 strategies verified
             ✓ 64 HOR rules verified

Week 9-10: [SPRINT 5] Documentation
             ✓ Migration guide complete
             ✓ API reference complete
             ✓ README and troubleshooting

Week 11-12:[SPRINT 6] Publish & Verify
             ✓ TestPyPI publish
             ✓ Cross-version testing
             ✓ Protocol verification
             ✓ Production PyPI publish
             ✓ Release announcement
```

---

## Resource Allocation

### Estimated Team Composition
- **Lead Developer (1)** — CLI, config, packaging, publish
- **QA Engineer (1)** — Testing (tools, algorithms, cross-version, protocol)
- **Documentation Lead (1)** — Migration guide, API reference, README
- **DevOps/Release Engineer (1)** — PyPI publish, CI/CD, Docker (optional)

**Total: 4 people, part-time overlap (can scale to 2–3 if needed)**

### Key Roles & Responsibilities

| Role | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 |
|------|----------|----------|----------|----------|----------|----------|
| Lead Dev | CLI, Config | pyproject.toml | ✓ | ✓ | ✓ | Publish |
| QA Eng | Tests | Build verify | Tool tests | Algo tests | ✓ | Protocol tests |
| Doc Lead | ✓ | README draft | ✓ | ✓ | Migration, API | ✓ |
| DevOps | ✓ | ✓ | ✓ | ✓ | ✓ | Publish |

---

## Risk & Contingency

### High-Priority Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|-----------|------------|
| Cross-version incompatibility | Low | High | Test on CI early (Sprint 2) | 1-week buffer (move release to Sprint 6 + 1) |
| PyPI publish failure | Low | High | TestPyPI integration test (Sprint 6) | Re-publish after fix; notify users |
| Protocol compliance issue | Low | Medium | Verify with FastMCP maintainers (Sprint 6) | Patch release after feedback |
| HOR rule count mismatch | Low | Medium | Audit rule count at Sprint 4 start | Inventory and verify each rule |
| Performance regression | Low | Medium | Benchmark baseline at Sprint 3 | Optimize hot paths; document differences |

### Schedule Buffers
- **Buffer 1:** 1 week between Sprints 4 and 5 for async reviews and fixes
- **Buffer 2:** 1 week after Sprint 6 for production monitoring and hotfixes

**Total scheduled timeline: 12 weeks (9–12 as stated); with buffers: 12–14 weeks realistic**

---

## Exit Criteria

### Minimum Viable Release (MVR)
- Package installable on Python 3.12 via PyPI
- All 32 tools register and are callable
- CLI commands work (serve, version, health)
- Config loading works (TOML + env override)
- Test coverage >85%
- Migration guide provided
- API reference provided

### Production Release
- MVR + all ACs pass
- Tested on Python 3.13
- Tested in Docker
- Protocol compliance verified
- Zero critical bugs found in testing
- Documentation peer-reviewed
- Release notes published

---

## Post-Launch Support Plan

### Phase 1: Monitoring (Week 13)
- Monitor PyPI downloads and error reports
- Monitor GitHub issues and discussions
- Hotfix critical bugs (within 24 hours)

### Phase 2: Iteration (Weeks 14+)
- Gather user feedback on migration experience
- Plan v0.2.0 with new features (optional)
- Establish support SLA for bug reports

---

## Appendix: Sprint Checklist

### Sprint 1 Checklist
- [ ] Create __main__.py with click CLI
- [ ] Implement serve, version, health, config-validate commands
- [ ] Create _config/loader.py with Pydantic schema
- [ ] Create defaults.toml
- [ ] Write test_cli.py (test all commands)
- [ ] Write test_config.py (test loading, override, validation)
- [ ] All tests pass
- [ ] Mypy clean
- [ ] Ruff clean
- [ ] Code review approved

### Sprint 2 Checklist
- [ ] Finalize pyproject.toml
- [ ] Add LICENSE file
- [ ] Build wheel and verify size <10 MB
- [ ] Test installation on Python 3.12, 3.13
- [ ] Test CLI entry point resolution
- [ ] Verify README and CHANGELOG exist
- [ ] Code review approved
- [ ] Build in CI passes on multiple Python versions

### Sprint 3 Checklist
- [ ] Write test_tool_registration.py (all 32 tools)
- [ ] Write test_tool_execution.py (tool invocation)
- [ ] All tests pass
- [ ] Collect tool performance metrics
- [ ] Verify tool annotations
- [ ] Code review approved
- [ ] Test coverage >95%

### Sprint 4 Checklist
- [ ] Write test_algorithm_access.py (7 algorithms)
- [ ] Write test_strategies.py (16 strategies)
- [ ] Write test_enhancements.py (5 enhancements)
- [ ] Write test_hor_in_package.py (64 rules)
- [ ] All tests pass
- [ ] Collect algorithm performance metrics
- [ ] Audit HOR rule count (confirm 64)
- [ ] Code review approved
- [ ] Test coverage >85%

### Sprint 5 Checklist
- [ ] Write docs/MIGRATION_GUIDE.md
- [ ] Write docs/API_REFERENCE.md
- [ ] Write docs/QUICKSTART.md
- [ ] Write docs/TROUBLESHOOTING.md
- [ ] Update README.md
- [ ] Peer-review documentation (2+ reviewers)
- [ ] Test all code examples
- [ ] Verify all links

### Sprint 6 Checklist
- [ ] Build wheel and publish to TestPyPI
- [ ] Install from TestPyPI and test (Python 3.12, 3.13)
- [ ] Write test_mcp_protocol_compatibility.py
- [ ] Protocol compatibility tests pass
- [ ] (Optional) Build Docker image and test
- [ ] Finalize version number (0.1.0)
- [ ] Update CHANGELOG.md
- [ ] Create git tag v0.1.0
- [ ] Publish to PyPI
- [ ] Verify package on pypi.org
- [ ] Create GitHub release
- [ ] Announce release (email, Slack, etc.)

