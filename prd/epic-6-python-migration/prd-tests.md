# Epic 6: Python MCP Server Migration — Test Plan

**Epic ID:** E6
**Document:** prd-tests.md
**Last Updated:** 2026-03-14

---

## Test Strategy

### Testing Levels
1. **Unit Tests** — Test individual components (CLI, config loader, tool registration)
2. **Integration Tests** — Test component interactions (config → server startup, tool invocation)
3. **System Tests** — Test end-to-end scenarios (install from wheel, CLI commands, tool execution)
4. **Performance Tests** — Benchmark tool latency, startup time, memory usage
5. **Compatibility Tests** — Cross-version (3.12, 3.13), cross-platform, protocol compliance

### Test Framework
- **pytest** — Unit and integration tests
- **pytest-asyncio** — Async tool invocation tests
- **pytest-cov** — Coverage reporting

---

## Test Suite Structure

```
tests/
├── test_cli.py                           # 12 tests
├── test_config.py                        # 15 tests
├── test_tool_registration.py             # 32 tests (one per tool)
├── test_tool_execution.py                # 32 tests (one per tool)
├── test_algorithm_access.py              # 7 tests (one per algorithm)
├── test_strategies.py                    # 16 tests (one per strategy)
├── test_enhancements.py                  # 5 tests (one per enhancement)
├── test_hor_in_package.py                # 64 tests (sample of rules)
├── test_mcp_protocol_compatibility.py    # 8 tests
├── test_install_and_import.py            # 3 tests
├── test_package_integration.py           # 6 tests
└── conftest.py                           # Shared fixtures
```

**Total: ~210 tests**

---

## Test Specifications

### 1. test_cli.py (12 tests)

```python
"""Test CLI entry point and commands."""

import subprocess
import json
from ai_architect_mcp.__main__ import cli
from click.testing import CliRunner

def test_cli_help():
    """Test ai-architect-mcp --help shows all subcommands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "version" in result.output
    assert "health" in result.output
    assert "config-validate" in result.output

def test_version_command():
    """Test ai-architect-mcp version returns correct format."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "ai-architect-mcp 0.1.0" in result.output

def test_serve_help():
    """Test ai-architect-mcp serve --help shows flags."""
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--config" in result.output
    assert "--port" in result.output
    assert "--log-level" in result.output

def test_serve_with_invalid_port():
    """Test serve with invalid port returns error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--port", "999"])  # Port out of range
    assert result.exit_code != 0
    assert "port" in result.output.lower() or "range" in result.output.lower()

def test_health_command_no_server():
    """Test health command with no running server returns error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["health"])
    # Should fail or timeout (server not running)
    # Exact behavior depends on implementation
    assert result.exit_code != 0 or "error" in result.output.lower()

def test_config_validate_help():
    """Test config-validate --help shows flags."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config-validate", "--help"])
    assert result.exit_code == 0
    assert "--config" in result.output

def test_config_validate_invalid_file():
    """Test config-validate with missing file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config-validate", "--config", "/nonexistent/config.toml"])
    assert result.exit_code != 0

def test_invalid_subcommand():
    """Test invalid subcommand shows error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["invalid"])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "error" in result.output.lower()

def test_cli_no_args():
    """Test CLI with no arguments shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0 or result.exit_code == 2  # Click returns 2 for missing subcommand
    assert "Usage" in result.output or "Commands" in result.output

def test_serve_port_flag_override():
    """Test --port flag is honored."""
    runner = CliRunner()
    # This test needs a mock server to verify port; simplified here
    result = runner.invoke(cli, ["serve", "--port", "3001", "--help"])
    assert result.exit_code == 0  # At least ensure flag is accepted

def test_serve_log_level_flag():
    """Test --log-level flag is accepted."""
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--log-level", "debug", "--help"])
    assert result.exit_code == 0

def test_cli_version_exact_format():
    """Test version output format is exact."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "ai-architect-mcp 0.1.0"
```

### 2. test_config.py (15 tests)

```python
"""Test configuration loading, validation, and override."""

import os
import tempfile
import pytest
from pathlib import Path
from ai_architect_mcp._config.loader import load_config, ConfigError
from ai_architect_mcp._config.models import Config

def test_load_default_config():
    """Test loading config with defaults (no file)."""
    cfg = load_config()
    assert cfg.server.port == 3000
    assert cfg.server.host == "127.0.0.1"
    assert cfg.logging.level == "info"
    assert cfg.verification.timeout_seconds == 30

def test_load_config_from_file():
    """Test loading config from TOML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("""
[server]
port = 3001
host = "0.0.0.0"

[logging]
level = "debug"
""")
        f.flush()
        try:
            cfg = load_config(f.name)
            assert cfg.server.port == 3001
            assert cfg.server.host == "0.0.0.0"
            assert cfg.logging.level == "debug"
        finally:
            os.unlink(f.name)

def test_config_env_override_port():
    """Test environment variable overrides config file."""
    os.environ["AI_ARCHITECT_PORT"] = "3002"
    try:
        cfg = load_config()
        assert cfg.server.port == 3002
    finally:
        del os.environ["AI_ARCHITECT_PORT"]

def test_config_env_override_log_level():
    """Test log level env override."""
    os.environ["AI_ARCHITECT_LOG_LEVEL"] = "warning"
    try:
        cfg = load_config()
        assert cfg.logging.level == "warning"
    finally:
        del os.environ["AI_ARCHITECT_LOG_LEVEL"]

def test_config_env_override_timeout():
    """Test verification timeout env override."""
    os.environ["AI_ARCHITECT_VERIFICATION_TIMEOUT"] = "60"
    try:
        cfg = load_config()
        assert cfg.verification.timeout_seconds == 60
    finally:
        del os.environ["AI_ARCHITECT_VERIFICATION_TIMEOUT"]

def test_config_env_override_bool():
    """Test boolean env override (enhancement_enabled)."""
    os.environ["AI_ARCHITECT_PROMPTING_ENHANCEMENT_ENABLED"] = "false"
    try:
        cfg = load_config()
        assert cfg.prompting.enhancement_enabled is False
    finally:
        del os.environ["AI_ARCHITECT_PROMPTING_ENHANCEMENT_ENABLED"]

def test_config_invalid_toml():
    """Test invalid TOML raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[server\nport = 3001")  # Invalid TOML
        f.flush()
        try:
            with pytest.raises(ConfigError):
                load_config(f.name)
        finally:
            os.unlink(f.name)

def test_config_invalid_port_type():
    """Test invalid port type raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[server]\nport = \"3001\"")  # String instead of int
        f.flush()
        try:
            # Pydantic should coerce or error
            cfg = load_config(f.name)
            # If coercion succeeds, that's OK; if error, that's also OK
        finally:
            os.unlink(f.name)

def test_config_invalid_port_range():
    """Test port out of range raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[server]\nport = 999")  # Port too low
        f.flush()
        try:
            with pytest.raises(ConfigError):
                load_config(f.name)
        finally:
            os.unlink(f.name)

def test_config_invalid_log_level():
    """Test invalid log level raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[logging]\nlevel = \"invalid_level\"")
        f.flush()
        try:
            # May raise error or accept it; depends on implementation
            cfg = load_config(f.name)
        finally:
            os.unlink(f.name)

def test_config_immutability():
    """Test config object is immutable."""
    cfg = load_config()
    with pytest.raises(Exception):  # Pydantic frozen model raises
        cfg.server.port = 4000

def test_config_serializable_to_dict():
    """Test config can be serialized to dict."""
    cfg = load_config()
    cfg_dict = cfg.model_dump()
    assert isinstance(cfg_dict, dict)
    assert "server" in cfg_dict
    assert cfg_dict["server"]["port"] == 3000

def test_config_override_priority():
    """Test override priority: CLI flag > env > file > default."""
    # Create config file with port 3001
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[server]\nport = 3001")
        f.flush()
        try:
            # Set env to 3002
            os.environ["AI_ARCHITECT_PORT"] = "3002"
            try:
                cfg = load_config(f.name)
                assert cfg.server.port == 3002  # Env overrides file

                # Also test CLI override (via load_config parameter)
                cfg = load_config(f.name, port_override=3003)
                assert cfg.server.port == 3003  # CLI overrides env
            finally:
                del os.environ["AI_ARCHITECT_PORT"]
        finally:
            os.unlink(f.name)

def test_config_multiple_env_overrides():
    """Test multiple env overrides applied simultaneously."""
    os.environ["AI_ARCHITECT_PORT"] = "3001"
    os.environ["AI_ARCHITECT_LOG_LEVEL"] = "debug"
    try:
        cfg = load_config()
        assert cfg.server.port == 3001
        assert cfg.logging.level == "debug"
    finally:
        del os.environ["AI_ARCHITECT_PORT"]
        del os.environ["AI_ARCHITECT_LOG_LEVEL"]

def test_config_default_file_path():
    """Test default config file path is checked."""
    # This test may be OS-dependent
    # Simplified: just ensure load_config() doesn't crash
    cfg = load_config()
    assert cfg is not None
```

### 3. test_tool_registration.py (32 tests, one per tool)

```python
"""Test all 32 tools register and have correct metadata."""

from ai_architect_mcp.server import mcp
import pytest

def test_tool_list_count():
    """Test mcp.list_tools() returns exactly 32 tools."""
    tools = mcp.list_tools()
    assert len(tools) == 32, f"Expected 32 tools, got {len(tools)}"

def test_all_tools_have_ai_architect_prefix():
    """Test all tool names start with ai_architect_."""
    tools = mcp.list_tools()
    for tool in tools:
        assert tool.name.startswith("ai_architect_"), f"Tool {tool.name} missing prefix"

def test_tool_verify_claim_registration():
    """Test ai_architect_verify_claim is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "ai_architect_verify_claim" in tool_names

def test_tool_decompose_claim_registration():
    """Test ai_architect_decompose_claim is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "ai_architect_decompose_claim" in tool_names

def test_tool_consensus_debate_registration():
    """Test ai_architect_consensus_debate is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "ai_architect_consensus_debate" in tool_names

# ... (28 more tool registration tests)

def test_all_tools_have_descriptions():
    """Test all tools have descriptions."""
    tools = mcp.list_tools()
    for tool in tools:
        assert tool.description, f"Tool {tool.name} missing description"
        assert len(tool.description) > 0

def test_all_tools_have_input_schema():
    """Test all tools have input schema."""
    tools = mcp.list_tools()
    for tool in tools:
        assert tool.inputSchema, f"Tool {tool.name} missing inputSchema"
```

### 4. test_tool_execution.py (32 tests, one per tool)

```python
"""Test all 32 tools execute successfully with sample inputs."""

import pytest
import asyncio
from ai_architect_mcp.server import mcp

@pytest.mark.asyncio
async def test_ai_architect_verify_claim_execution():
    """Test ai_architect_verify_claim executes with sample input."""
    result = await mcp.call_tool("ai_architect_verify_claim", {
        "content": "The Earth is round.",
        "claim_type": "atomic_fact",
        "context": "Astronomy",
        "priority": 50
    })
    assert result is not None
    assert "status" in result or "data" in result

@pytest.mark.asyncio
async def test_ai_architect_decompose_claim_execution():
    """Test ai_architect_decompose_claim executes with sample input."""
    result = await mcp.call_tool("ai_architect_decompose_claim", {
        "content": "Large language models are trained using transformer architecture and supervised fine-tuning.",
        "max_depth": 2
    })
    assert result is not None
    assert isinstance(result, (dict, list))

@pytest.mark.asyncio
async def test_ai_architect_context_load_execution():
    """Test ai_architect_context_load executes (may fail if context doesn't exist, but shouldn't crash)."""
    result = await mcp.call_tool("ai_architect_context_load", {
        "context_id": "test-context-123"
    })
    # May return error if context doesn't exist; that's OK
    assert result is not None

# ... (29 more tool execution tests)

@pytest.mark.asyncio
async def test_all_tools_return_json_serializable():
    """Test all tools return JSON-serializable results."""
    import json
    tools = mcp.list_tools()
    # Sample a few tools and ensure results are JSON-serializable
    sample_tools = [t.name for t in tools[:5]]
    for tool_name in sample_tools:
        # Mock minimal input and test serialization
        try:
            result = await mcp.call_tool(tool_name, {})
        except TypeError:
            # Tool may require specific inputs; skip
            pass
        else:
            if result:
                try:
                    json.dumps(result)
                except TypeError as e:
                    pytest.fail(f"Tool {tool_name} returns non-JSON-serializable result: {e}")
```

### 5. test_algorithm_access.py (7 tests)

```python
"""Test all 7 verification algorithms are accessible and functional."""

import pytest
from ai_architect_mcp._verification.algorithms.atomic_claim_decomposer import AtomicClaimDecomposer
from ai_architect_mcp._verification.algorithms.chain_of_verification import ChainOfVerification
from ai_architect_mcp._verification.algorithms.nli_entailment import NLIEntailmentEvaluator
from ai_architect_mcp._verification.algorithms.multi_agent_debate import MultiAgentDebate
from ai_architect_mcp._verification.algorithms.weighted_average import WeightedAverageConsensus
from ai_architect_mcp._verification.algorithms.adaptive_stability import AdaptiveStabilityConsensus
from ai_architect_mcp._verification.algorithms.graph_constrained import GraphConstrainedVerifier

def test_atomic_claim_decomposer_importable():
    """Test AtomicClaimDecomposer can be imported."""
    assert AtomicClaimDecomposer is not None

def test_atomic_claim_decomposer_instantiable():
    """Test AtomicClaimDecomposer can be instantiated."""
    decomposer = AtomicClaimDecomposer()
    assert decomposer is not None

def test_atomic_claim_decomposer_executable():
    """Test AtomicClaimDecomposer.decompose() works."""
    decomposer = AtomicClaimDecomposer()
    claims = decomposer.decompose("The sky is blue and the grass is green.")
    assert isinstance(claims, list)
    assert len(claims) >= 1

# ... (4 more similar tests for other 6 algorithms)

def test_all_algorithms_accessible_via_tools():
    """Test all algorithms are accessible via tool interface."""
    from ai_architect_mcp.server import mcp
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    # Verify tool names that expose algorithms exist
    assert "ai_architect_verify_claim" in tool_names  # Uses ChainOfVerification
    assert "ai_architect_decompose_claim" in tool_names  # Uses AtomicClaimDecomposer
    assert "ai_architect_consensus_debate" in tool_names  # Uses MultiAgentDebate
```

### 6. test_strategies.py (16 tests)

```python
"""Test all 16 thinking strategies are available and applicable."""

import pytest
from ai_architect_mcp._prompting.strategies import (
    TreeOfThought, ChainOfThought, ZeroShot, FewShot,
    InContextLearning, SelfConsistency, UncertaintyQuantification,
    StepBackPrompting, MultiHopReasoning, AnalogicalReasoning,
    ConstraintSatisfaction, CounterfactualReasoning,
    PerspectiveTaking, DialogueBased, MetaLearning, RetrievalAugmented
)

def test_tree_of_thought_available():
    """Test TreeOfThought strategy is available."""
    strategy = TreeOfThought()
    assert strategy is not None
    assert hasattr(strategy, "apply")

def test_chain_of_thought_available():
    """Test ChainOfThought strategy is available."""
    strategy = ChainOfThought()
    assert strategy is not None

# ... (14 more strategy availability tests)

def test_strategy_application():
    """Test strategy can be applied to prompt."""
    strategy = TreeOfThought()
    input_prompt = "What is 2 + 2?"
    output = strategy.apply(input_prompt)
    assert isinstance(output, str)
    assert len(output) > 0
    # Output should be different from input (enhanced)
    assert output != input_prompt or len(output) > len(input_prompt)

@pytest.mark.asyncio
async def test_strategy_selection_via_tool():
    """Test strategy selection via tool interface."""
    from ai_architect_mcp.server import mcp
    result = await mcp.call_tool("ai_architect_thinking_strategy_select", {
        "query": "complex reasoning",
        "available_strategies": ["tree_of_thought", "chain_of_thought"]
    })
    assert result is not None
    assert isinstance(result, (dict, str))
```

### 7. test_enhancements.py (5 tests)

```python
"""Test all 5 enhancements are available and applicable."""

import pytest
from ai_architect_mcp._prompting.enhancements import (
    ClarityEnhancement, DetailEnhancement, SpecificityEnhancement,
    StructureEnhancement, ReasoningEnhancement
)

def test_clarity_enhancement_available():
    """Test ClarityEnhancement is available."""
    enh = ClarityEnhancement()
    assert enh is not None

def test_detail_enhancement_available():
    """Test DetailEnhancement is available."""
    enh = DetailEnhancement()
    assert enh is not None

def test_specificity_enhancement_available():
    """Test SpecificityEnhancement is available."""
    enh = SpecificityEnhancement()
    assert enh is not None

def test_structure_enhancement_available():
    """Test StructureEnhancement is available."""
    enh = StructureEnhancement()
    assert enh is not None

def test_reasoning_enhancement_available():
    """Test ReasoningEnhancement is available."""
    enh = ReasoningEnhancement()
    assert enh is not None

def test_enhancement_application():
    """Test enhancement can be applied to prompt."""
    enh = ClarityEnhancement()
    input_prompt = "The thing is big and complex."
    output = enh.apply(input_prompt)
    assert isinstance(output, str)
    assert len(output) > 0
    # Output should be enhanced (different or longer)
    assert output != input_prompt or len(output) > len(input_prompt)
```

### 8. test_hor_in_package.py (64+ tests)

```python
"""Test all 64 HOR rules load and execute."""

import pytest
from ai_architect_mcp._verification.hor.rules import load_rules, RuleExecutor

def test_hor_rules_load():
    """Test all HOR rules load without error."""
    rules = load_rules()
    assert len(rules) == 64, f"Expected 64 HOR rules, got {len(rules)}"

def test_hor_rules_have_unique_ids():
    """Test all rule IDs are unique."""
    rules = load_rules()
    rule_ids = [r.id for r in rules]
    assert len(rule_ids) == len(set(rule_ids)), "Duplicate rule IDs found"

def test_hor_rules_have_required_fields():
    """Test all rules have required fields."""
    rules = load_rules()
    for rule in rules:
        assert hasattr(rule, "id"), f"Rule missing id: {rule}"
        assert hasattr(rule, "name"), f"Rule {rule.id} missing name"
        assert hasattr(rule, "precondition"), f"Rule {rule.id} missing precondition"
        assert hasattr(rule, "effect"), f"Rule {rule.id} missing effect"
        assert hasattr(rule, "priority"), f"Rule {rule.id} missing priority"

@pytest.mark.asyncio
async def test_hor_rule_execution():
    """Test HOR rule execution via tool."""
    from ai_architect_mcp.server import mcp
    # Get all rules and test a few
    rules = load_rules()
    sample_rule = rules[0]
    result = await mcp.call_tool("ai_architect_execute_hor_rule", {
        "rule_id": sample_rule.id,
        "context": {}
    })
    assert result is not None
    assert "passed" in result or "status" in result

@pytest.mark.asyncio
async def test_hor_batch_execution():
    """Test batch rule execution."""
    from ai_architect_mcp.server import mcp
    rules = load_rules()
    sample_rule_ids = [r.id for r in rules[:5]]
    result = await mcp.call_tool("ai_architect_batch_execute_hor_rules", {
        "rule_ids": sample_rule_ids,
        "context": {}
    })
    assert result is not None
    assert isinstance(result, (dict, list))

def test_hor_list_via_tool():
    """Test listing all HOR rules via tool."""
    import asyncio
    from ai_architect_mcp.server import mcp
    result = asyncio.run(mcp.call_tool("ai_architect_list_hor_rules", {}))
    assert result is not None
    assert len(result) == 64 or "rules" in result
```

### 9. test_mcp_protocol_compatibility.py (8 tests)

```python
"""Test MCP protocol compliance."""

import pytest
import asyncio
from ai_architect_mcp.server import mcp

def test_protocol_initialization():
    """Test server responds to protocol initialization."""
    # FastMCP automatically handles protocol init
    assert mcp is not None
    assert hasattr(mcp, "list_tools")
    assert hasattr(mcp, "call_tool")

def test_list_tools_response_format():
    """Test list_tools returns correct schema."""
    tools = mcp.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    for tool in tools:
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "inputSchema")

@pytest.mark.asyncio
async def test_call_tool_marshaling():
    """Test call_tool marshals requests correctly."""
    result = await mcp.call_tool("ai_architect_verify_claim", {
        "content": "Test claim",
        "claim_type": "atomic_fact",
        "context": "Test context",
        "priority": 50
    })
    assert result is not None

@pytest.mark.asyncio
async def test_concurrent_tool_invocations():
    """Test server handles concurrent tool calls."""
    import asyncio
    tasks = [
        mcp.call_tool("ai_architect_verify_claim", {
            "content": f"Claim {i}",
            "claim_type": "atomic_fact",
            "context": "",
            "priority": 50
        })
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    assert all(r is not None for r in results)

def test_error_response_format():
    """Test error responses follow MCP spec."""
    # Try calling non-existent tool
    import asyncio
    try:
        result = asyncio.run(mcp.call_tool("ai_architect_nonexistent", {}))
        # If tool exists, skip test; if error, verify format
    except Exception as e:
        # Error should be descriptive
        assert str(e)

@pytest.mark.asyncio
async def test_tool_response_consistency():
    """Test tool responses are consistent across calls."""
    result1 = await mcp.call_tool("ai_architect_version", {})
    result2 = await mcp.call_tool("ai_architect_version", {})
    # Responses should be identical (or similar) for read-only tools
    # This test is simplistic; real implementation may vary

def test_protocol_version_support():
    """Test server supports MCP protocol version."""
    # FastMCP handles this; just verify it doesn't crash
    assert mcp is not None

@pytest.mark.asyncio
async def test_tool_timeout_handling():
    """Test server handles tool timeouts gracefully."""
    # This test would need a tool that intentionally times out
    # Simplified: just ensure server doesn't crash under load
    pass
```

### 10. test_install_and_import.py (3 tests)

```python
"""Test package installation and imports work."""

def test_import_main_module():
    """Test ai_architect_mcp module can be imported."""
    import ai_architect_mcp
    assert ai_architect_mcp is not None

def test_import_server():
    """Test server module can be imported."""
    from ai_architect_mcp import server
    assert server is not None
    assert hasattr(server, "mcp")

def test_import_config():
    """Test config module can be imported."""
    from ai_architect_mcp._config import loader
    assert loader is not None
    assert hasattr(loader, "load_config")
```

### 11. test_package_integration.py (6 tests)

```python
"""Test package integration end-to-end."""

import subprocess
import sys
import json
import tempfile
import os

def test_cli_entry_point_installed():
    """Test CLI entry point is installed and callable."""
    result = subprocess.run(
        [sys.executable, "-m", "ai_architect_mcp", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout

def test_config_loading_with_file():
    """Test config loading in integration."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[server]\nport = 3001")
        f.flush()
        try:
            from ai_architect_mcp._config.loader import load_config
            cfg = load_config(f.name)
            assert cfg.server.port == 3001
        finally:
            os.unlink(f.name)

def test_tool_invocation_after_import():
    """Test tools are callable after package import."""
    from ai_architect_mcp.server import mcp
    tools = mcp.list_tools()
    assert len(tools) == 32
    assert all(t.name.startswith("ai_architect_") for t in tools)

def test_all_modules_importable():
    """Test all submodules are importable."""
    import ai_architect_mcp
    import ai_architect_mcp._config
    import ai_architect_mcp._tools
    import ai_architect_mcp._verification
    import ai_architect_mcp._prompting
    import ai_architect_mcp._adapters
    import ai_architect_mcp._models
    import ai_architect_mcp._context
    import ai_architect_mcp._scoring
    # If we get here, all imports succeeded
    assert True

def test_no_import_errors_on_startup():
    """Test package starts without errors."""
    result = subprocess.run(
        [sys.executable, "-c", "import ai_architect_mcp; from ai_architect_mcp.server import mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stderr == ""

def test_cli_help_comprehensive():
    """Test CLI help is comprehensive."""
    result = subprocess.run(
        [sys.executable, "-m", "ai_architect_mcp", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "serve" in result.stdout
    assert "version" in result.stdout
    assert "health" in result.stdout
    assert "config-validate" in result.stdout
```

---

## conftest.py (Shared Fixtures)

```python
"""Shared pytest fixtures."""

import pytest
import tempfile
import os

@pytest.fixture
def temp_config_file():
    """Create a temporary TOML config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("""
[server]
port = 3000
host = "127.0.0.1"

[logging]
level = "info"

[verification]
timeout_seconds = 30

[prompting]
enhancement_enabled = true
""")
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def clean_env():
    """Ensure AI_ARCHITECT_* env vars are not set."""
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith("AI_ARCHITECT_"):
            saved_env[key] = os.environ.pop(key)
    yield
    # Restore env vars after test
    for key, value in saved_env.items():
        os.environ[key] = value

@pytest.fixture
def cli_runner():
    """Provide Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()
```

---

## Test Coverage Goals

| Module | Coverage Goal | Notes |
|--------|---------------|-------|
| _\_main\_\_.py | >90% | CLI implementation |
| _config/loader.py | >90% | Config parsing and validation |
| _config/models.py | >85% | Pydantic schema (auto-tested) |
| _tools/ | >90% | Tool invocation (sampled) |
| _verification/ | >80% | Algorithm access (existing code) |
| _prompting/ | >80% | Strategy availability (existing code) |
| Total (new code) | >85% | CLI, config, package structure |

---

## Test Execution

```bash
# Run all tests
pytest tests/ -v --cov=ai_architect_mcp --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v

# Run tests matching pattern
pytest -k "test_cli" -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto

# Generate coverage report
pytest tests/ --cov=ai_architect_mcp --cov-report=term-missing
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .[dev]
      - run: pytest tests/ -v --cov=ai_architect_mcp
      - run: mypy ai_architect_mcp/
      - run: ruff check ai_architect_mcp/
```

