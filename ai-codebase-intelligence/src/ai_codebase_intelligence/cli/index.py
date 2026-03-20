"""CLI entry point — 1:1 port of gitnexus cli/index.js."""
from __future__ import annotations

import sys


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="ai-codebase-intelligence", description="Codebase intelligence CLI and MCP server")
    sub = parser.add_subparsers(dest="command")

    # setup
    sub.add_parser("setup", help="Configure MCP for editors")

    # analyze
    p = sub.add_parser("analyze", help="Index a repository")
    p.add_argument("path", nargs="?", default="")
    p.add_argument("-f", "--force", action="store_true")
    p.add_argument("--embeddings", action="store_true")

    # serve
    p = sub.add_parser("serve", help="Start HTTP server")
    p.add_argument("-p", "--port", type=int, default=4747)
    p.add_argument("--host", default="127.0.0.1")

    # mcp
    sub.add_parser("mcp", help="Start MCP server (stdio)")

    # list
    sub.add_parser("list", help="List indexed repositories")

    # status
    sub.add_parser("status", help="Show index status")

    # clean
    p = sub.add_parser("clean", help="Delete index")
    p.add_argument("-f", "--force", action="store_true")
    p.add_argument("--all", action="store_true")

    # wiki
    p = sub.add_parser("wiki", help="Generate wiki from knowledge graph")
    p.add_argument("path", nargs="?", default="")
    p.add_argument("-f", "--force", action="store_true")
    p.add_argument("--model", default="")
    p.add_argument("--api-key", default="")
    p.add_argument("--concurrency", type=int, default=3)

    # augment
    p = sub.add_parser("augment", help="Augment pattern with graph context")
    p.add_argument("pattern")

    # query
    p = sub.add_parser("query", help="Search the knowledge graph")
    p.add_argument("search_query")
    p.add_argument("-r", "--repo", default="")
    p.add_argument("-l", "--limit", type=int, default=5)
    p.add_argument("--content", action="store_true")

    # context
    p = sub.add_parser("context", help="360-degree symbol view")
    p.add_argument("name", nargs="?", default="")
    p.add_argument("-u", "--uid", default="")
    p.add_argument("-r", "--repo", default="")
    p.add_argument("--content", action="store_true")

    # impact
    p = sub.add_parser("impact", help="Blast radius analysis")
    p.add_argument("target")
    p.add_argument("-d", "--direction", default="upstream")
    p.add_argument("-r", "--repo", default="")
    p.add_argument("--depth", type=int, default=3)

    # cypher
    p = sub.add_parser("cypher", help="Execute Cypher query")
    p.add_argument("query")
    p.add_argument("-r", "--repo", default="")

    args = parser.parse_args()

    if args.command == "setup":
        from .setup import setup_command
        setup_command()
    elif args.command == "analyze":
        from .analyze import analyze_command
        analyze_command(args.path, args.force, args.embeddings)
    elif args.command == "serve":
        from .serve import serve_command
        serve_command(args.port, args.host)
    elif args.command == "mcp":
        from .mcp import mcp_command
        mcp_command()
    elif args.command == "list":
        from .list import list_command
        list_command()
    elif args.command == "status":
        from .status import status_command
        status_command()
    elif args.command == "clean":
        from .clean import clean_command
        clean_command(args.all, args.force)
    elif args.command == "augment":
        from .augment import augment_command
        augment_command(args.pattern)
    elif args.command == "query":
        from .tool import query_command
        query_command(args.search_query, args.repo, args.limit, args.content)
    elif args.command == "context":
        from .tool import context_command
        context_command(args.name, args.uid, "", args.repo, args.content)
    elif args.command == "impact":
        from .tool import impact_command
        impact_command(args.target, args.direction, args.depth, args.repo)
    elif args.command == "cypher":
        from .tool import cypher_command
        cypher_command(args.query, args.repo)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
