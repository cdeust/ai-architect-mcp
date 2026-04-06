"""MCP Tool definitions."""
from __future__ import annotations

TOOLS = [
    {
        "name": "list_repos",
        "description": "List all indexed repositories.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "query",
        "description": "Query the code knowledge graph for execution flows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language or keyword search query"},
                "task_context": {"type": "string"},
                "goal": {"type": "string"},
                "limit": {"type": "number", "default": 5},
                "max_symbols": {"type": "number", "default": 10},
                "include_content": {"type": "boolean", "default": False},
                "repo": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "cypher",
        "description": "Execute Cypher query against the code knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Cypher query to execute"},
                "repo": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "context",
        "description": "360-degree view of a single code symbol.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "uid": {"type": "string"},
                "file_path": {"type": "string"},
                "include_content": {"type": "boolean", "default": False},
                "repo": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "detect_changes",
        "description": "Analyze code changes and find affected execution flows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["unstaged", "staged", "all", "compare"], "default": "unstaged"},
                "base_ref": {"type": "string"},
                "changed_files": {"type": "array", "items": {"type": "string"}},
                "repo": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "rename",
        "description": "Multi-file coordinated rename using the knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol_name": {"type": "string"},
                "symbol_uid": {"type": "string"},
                "new_name": {"type": "string"},
                "file_path": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True},
                "repo": {"type": "string"},
            },
            "required": ["new_name"],
        },
    },
    {
        "name": "impact",
        "description": "Analyze the blast radius of changing a code symbol.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "direction": {"type": "string"},
                "maxDepth": {"type": "number", "default": 3},
                "relationTypes": {"type": "array", "items": {"type": "string"}},
                "includeTests": {"type": "boolean"},
                "minConfidence": {"type": "number"},
                "repo": {"type": "string"},
            },
            "required": ["target", "direction"],
        },
    },
]
