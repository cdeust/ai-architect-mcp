"""Tests for security tier hook."""

from __future__ import annotations

import pytest

from ai_architect_mcp._hooks.base import HookContext, HookStatus
from ai_architect_mcp._hooks.security_tier import (
    SecurityTier,
    SecurityTierHook,
    classify_command,
)


class TestClassifyCommand:
    """Tests for command classification."""

    def test_ls_is_t1(self) -> None:
        assert classify_command("ls -la") == SecurityTier.T1_READ

    def test_cat_is_t1(self) -> None:
        assert classify_command("cat file.txt") == SecurityTier.T1_READ

    def test_grep_is_t1(self) -> None:
        assert classify_command("grep pattern file") == SecurityTier.T1_READ

    def test_uname_is_t2(self) -> None:
        assert classify_command("uname -a") == SecurityTier.T2_ENV_QUERY

    def test_pip_list_is_t3(self) -> None:
        assert classify_command("pip list") == SecurityTier.T3_PACKAGE

    def test_touch_is_t4(self) -> None:
        assert classify_command("touch file.txt") == SecurityTier.T4_WRITE

    def test_mkdir_is_t4(self) -> None:
        assert classify_command("mkdir -p dir") == SecurityTier.T4_WRITE

    def test_git_push_is_t5(self) -> None:
        assert classify_command("git push origin main") == SecurityTier.T5_PUBLISH

    def test_git_commit_is_t5(self) -> None:
        assert classify_command("git commit -m 'msg'") == SecurityTier.T5_PUBLISH

    def test_docker_run_is_t6(self) -> None:
        assert classify_command("docker run ubuntu") == SecurityTier.T6_CONTAINER

    def test_chmod_is_t7(self) -> None:
        assert classify_command("chmod 755 file") == SecurityTier.T7_PERMISSION

    def test_kill_is_t8(self) -> None:
        assert classify_command("kill -9 1234") == SecurityTier.T8_KILL

    def test_pkill_is_t8(self) -> None:
        assert classify_command("pkill python") == SecurityTier.T8_KILL

    def test_write_etc_is_t9(self) -> None:
        assert classify_command("tee /etc/passwd") == SecurityTier.T9_SYSTEM_FILE

    def test_rm_rf_root_is_t10(self) -> None:
        assert classify_command("rm -rf /") == SecurityTier.T10_DESTRUCTIVE

    def test_mkfs_is_t10(self) -> None:
        assert classify_command("mkfs.ext4 /dev/sda1") == SecurityTier.T10_DESTRUCTIVE

    def test_unknown_defaults_t1(self) -> None:
        assert classify_command("python script.py") == SecurityTier.T1_READ


class TestSecurityTierHook:
    """Tests for SecurityTierHook."""

    @pytest.mark.asyncio
    async def test_allows_safe_command(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="ls -la")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert result.metadata["tier"] == 1

    @pytest.mark.asyncio
    async def test_blocks_destructive(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="rm -rf /")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.BLOCK
        assert result.metadata["tier"] == 10

    @pytest.mark.asyncio
    async def test_asks_for_container(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="docker run ubuntu")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert result.metadata.get("requires_confirmation") is True

    @pytest.mark.asyncio
    async def test_blocks_kill(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="kill -9 1")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.BLOCK

    @pytest.mark.asyncio
    async def test_empty_command_passes(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_allows_git_push(self) -> None:
        hook = SecurityTierHook()
        ctx = HookContext(command="git push origin main")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert result.metadata["tier"] == 5
