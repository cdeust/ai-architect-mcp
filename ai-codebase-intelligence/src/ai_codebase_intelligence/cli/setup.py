"""Setup command."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _get_mcp_entry() -> dict[str, object]:
    return {
        "command": "python3",
        "args": ["-m", "ai_codebase_intelligence.mcp.server"],
    }


def _merge_mcp_config(existing: dict[str, object] | None) -> dict[str, object]:
    if not existing or not isinstance(existing, dict):
        existing = {}
    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        servers = {}
    servers["ai-codebase-intelligence"] = _get_mcp_entry()
    existing["mcpServers"] = servers
    return existing


def _read_json(path: str) -> dict[str, object] | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: str, data: dict[str, object]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


EDITOR_CONFIGS = {
    "Claude Code": os.path.join(str(Path.home()), ".claude", "mcp.json"),
    "Cursor": os.path.join(str(Path.home()), ".cursor", "mcp.json"),
    "VS Code": os.path.join(str(Path.home()), ".vscode", "mcp.json"),
}


def setup_command() -> None:
    print("\n  Codebase Intelligence Setup\n")
    configured = []

    for editor, config_path in EDITOR_CONFIGS.items():
        config_dir = os.path.dirname(config_path)
        if not os.path.isdir(config_dir):
            continue
        existing = _read_json(config_path)
        merged = _merge_mcp_config(existing)
        _write_json(config_path, merged)
        configured.append(editor)
        print(f"  Configured: {editor} ({config_path})")

    if not configured:
        print("  No supported editors detected.")
        print("  Supported: Claude Code, Cursor, VS Code")
        print("  Create the editor config directory and re-run setup.")
    else:
        print(f"\n  Setup complete! {len(configured)} editor(s) configured.\n")
