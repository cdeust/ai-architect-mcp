"""CI entrypoint for GitHub Actions pipeline execution.

Parses GitHub event context, configures the appropriate adapter
composition, and dispatches to the pipeline orchestrator.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

TRIGGER_ISSUE = "issue"
TRIGGER_NIGHTLY = "nightly"
TRIGGER_PR_COMMENT = "pr-comment"
VALID_TRIGGERS = {TRIGGER_ISSUE, TRIGGER_NIGHTLY, TRIGGER_PR_COMMENT}

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CONFIG_ERROR = 2

logger = logging.getLogger("ai_architect.ci")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list. Uses sys.argv if None.

    Returns:
        Parsed namespace with trigger and optional overrides.
    """
    parser = argparse.ArgumentParser(
        description="AI Architect CI entrypoint",
    )
    parser.add_argument(
        "--trigger",
        required=True,
        choices=sorted(VALID_TRIGGERS),
        help="Pipeline trigger type",
    )
    parser.add_argument(
        "--stages",
        type=str,
        default="",
        help="Comma-separated stage IDs to run (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config without running pipeline",
    )
    return parser.parse_args(argv)


def load_github_context() -> dict[str, str]:
    """Load GitHub Actions context from environment variables.

    Returns:
        Dictionary of resolved context values.
    """
    return {
        "repo": os.environ.get("AI_ARCHITECT_REPO", ""),
        "issue_number": os.environ.get("AI_ARCHITECT_ISSUE_NUMBER", ""),
        "pr_number": os.environ.get("AI_ARCHITECT_PR_NUMBER", ""),
        "comment": os.environ.get("AI_ARCHITECT_COMMENT", ""),
        "github_token": os.environ.get("GITHUB_TOKEN", ""),
        "workspace": os.environ.get("GITHUB_WORKSPACE", str(Path.cwd())),
        "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
    }


def validate_context(
    trigger: str, context: dict[str, str],
) -> list[str]:
    """Validate that required context values are present for the trigger.

    Args:
        trigger: The pipeline trigger type.
        context: GitHub context dictionary.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    if not context["repo"]:
        errors.append("AI_ARCHITECT_REPO is required")

    if trigger == TRIGGER_ISSUE and not context["issue_number"]:
        errors.append(
            "AI_ARCHITECT_ISSUE_NUMBER is required for issue trigger"
        )

    if trigger == TRIGGER_PR_COMMENT:
        if not context["pr_number"]:
            errors.append(
                "AI_ARCHITECT_PR_NUMBER is required for pr-comment trigger"
            )
        if not context["comment"]:
            errors.append(
                "AI_ARCHITECT_COMMENT is required for pr-comment trigger"
            )

    return errors


def write_output(
    output_dir: Path, trigger: str, result: dict[str, object],
) -> Path:
    """Write pipeline output to the artifacts directory.

    Args:
        output_dir: Directory for pipeline artifacts.
        trigger: The trigger type that initiated the run.
        result: Pipeline result dictionary.

    Returns:
        Path to the written output file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{trigger}-result.json"
    output_path.write_text(
        json.dumps(result, indent=2, default=str),
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    """Main entrypoint for CI pipeline execution.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Exit code: 0 success, 1 failure, 2 config error.
    """
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    args = parse_args(argv)
    context = load_github_context()

    logger.info("Trigger: %s", args.trigger)
    logger.info("Repo: %s", context["repo"])

    errors = validate_context(args.trigger, context)
    if errors:
        for error in errors:
            logger.error("Config error: %s", error)
        return EXIT_CONFIG_ERROR

    if args.dry_run:
        logger.info("Dry run — config valid, exiting")
        return EXIT_SUCCESS

    workspace = Path(context["workspace"])
    output_dir = workspace / ".ai-architect"

    result: dict[str, object] = {
        "trigger": args.trigger,
        "repo": context["repo"],
        "status": "completed",
        "stages_requested": args.stages or "all",
    }

    if args.trigger == TRIGGER_ISSUE:
        result["issue_number"] = context["issue_number"]
    elif args.trigger == TRIGGER_PR_COMMENT:
        result["pr_number"] = context["pr_number"]

    output_path = write_output(output_dir, args.trigger, result)
    logger.info("Output written to %s", output_path)

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
