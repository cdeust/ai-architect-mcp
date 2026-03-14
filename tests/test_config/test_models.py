"""Tests for configuration models."""

from __future__ import annotations

import pytest

from ai_architect_mcp._config.models import (
    AdaptersSection,
    ContextSection,
    LoggingSection,
    PromptingSection,
    ServerConfig,
    ServerSection,
    VerificationSection,
)


class TestServerSection:
    """Tests for ServerSection model."""

    def test_defaults(self) -> None:
        section = ServerSection()
        assert section.host == "127.0.0.1"
        assert section.port == 8080
        assert section.log_level == "info"

    def test_custom_values(self) -> None:
        section = ServerSection(host="0.0.0.0", port=9090, log_level="debug")
        assert section.port == 9090

    def test_port_range_validation(self) -> None:
        with pytest.raises(ValueError):
            ServerSection(port=0)
        with pytest.raises(ValueError):
            ServerSection(port=70000)


class TestVerificationSection:
    """Tests for VerificationSection model."""

    def test_defaults(self) -> None:
        section = VerificationSection()
        assert section.hor_rule_count == 64
        assert section.consensus_algorithm == "weighted_average"
        assert section.confidence_threshold == 0.7

    def test_threshold_range(self) -> None:
        with pytest.raises(ValueError):
            VerificationSection(confidence_threshold=1.5)


class TestPromptingSection:
    """Tests for PromptingSection model."""

    def test_defaults(self) -> None:
        section = PromptingSection()
        assert section.default_strategy == "adaptive_expansion"
        assert section.max_thinking_depth == 5


class TestServerConfig:
    """Tests for the root ServerConfig model."""

    def test_defaults(self) -> None:
        config = ServerConfig()
        assert config.server.port == 8080
        assert config.verification.hor_rule_count == 64
        assert config.prompting.default_strategy == "adaptive_expansion"
        assert config.context.max_stages == 11

    def test_round_trip(self) -> None:
        config = ServerConfig()
        data = config.model_dump()
        restored = ServerConfig.model_validate(data)
        assert restored == config

    def test_partial_override(self) -> None:
        config = ServerConfig(
            server=ServerSection(port=9999),
        )
        assert config.server.port == 9999
        assert config.verification.hor_rule_count == 64
