"""Wiki generator (core orchestrator).

Coordinates the per-run lifecycle: connect → discover → build tree →
render leaf pages → render parent pages → render overview → save meta.
The actual content generation is delegated to wiki/phases.py so this
file stays focused on orchestration and remains under the 300-line
project rule.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Callable

from .graph_queries import close_wiki_db, get_all_files, get_files_with_exports, init_wiki_db
from .html_viewer import generate_html_viewer
from .phases import (
    build_module_tree,
    count_modules,
    flatten_tree,
    generate_leaf_page,
    generate_overview,
    generate_parent_page,
)
from ...config.ignore_service import should_ignore_path

WIKI_DIR = "wiki"
DEFAULT_MAX_TOKENS = 30_000


class WikiGenerator:
    def __init__(
        self,
        repo_path: str,
        storage_path: str,
        kuzu_path: str,
        llm_config: dict[str, Any],
        options: dict[str, Any] | None = None,
        on_progress: Callable[[str, int, str], None] | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.storage_path = storage_path
        self.wiki_dir = os.path.join(storage_path, WIKI_DIR)
        self.kuzu_path = kuzu_path
        self.llm_config = llm_config
        self.options = options or {}
        self.max_tokens = self.options.get("maxTokensPerModule", DEFAULT_MAX_TOKENS)
        self.concurrency = self.options.get("concurrency", 3)
        self._progress = on_progress or (lambda *a: None)
        self.failed_modules: list[str] = []
        self.module_registry: dict[str, dict[str, Any]] = {}

    def run(self) -> dict[str, Any]:
        os.makedirs(self.wiki_dir, exist_ok=True)
        existing_meta = self._load_wiki_meta()
        current_commit = self._get_current_commit()

        if (not self.options.get("force") and existing_meta
                and existing_meta.get("fromCommit") == current_commit):
            self._ensure_html_viewer()
            return {"pagesGenerated": 0, "mode": "up-to-date", "failedModules": []}

        if self.options.get("force"):
            self._purge_wiki_dir()

        self._progress("init", 2, "Connecting to knowledge graph...")
        init_wiki_db(self.kuzu_path)

        try:
            result = self._full_generation(current_commit)
        finally:
            close_wiki_db()

        self._ensure_html_viewer()
        return result

    def _purge_wiki_dir(self) -> None:
        """Delete cached metadata and previously rendered pages."""
        for f in ("first_module_tree.json", "meta.json", "module_tree.json"):
            try:
                os.unlink(os.path.join(self.wiki_dir, f))
            except OSError:
                pass
        for f in os.listdir(self.wiki_dir):
            if f.endswith(".md"):
                try:
                    os.unlink(os.path.join(self.wiki_dir, f))
                except OSError:
                    pass

    def _full_generation(self, current_commit: str) -> dict[str, Any]:
        pages = 0
        self._progress("gather", 5, "Querying graph for file structure...")
        files_with_exports = get_files_with_exports()
        all_files = get_all_files()
        source_files = [f for f in all_files if not should_ignore_path(f)]

        if not source_files:
            raise RuntimeError("No source files found. Nothing to document.")

        export_map = {f["filePath"]: f for f in files_with_exports}
        enriched = [
            export_map.get(fp, {"filePath": fp, "symbols": []}) for fp in source_files
        ]
        self._progress("gather", 10, f"Found {len(source_files)} source files")

        module_tree = build_module_tree(
            enriched, self.wiki_dir, self.llm_config, self._progress,
        )
        pages += self._render_module_pages(module_tree)
        pages += self._render_overview(module_tree)

        self._save_wiki_meta({
            "fromCommit": current_commit,
            "generatedAt": "",
            "model": self.llm_config.get("model", ""),
        })
        self._save_module_tree(module_tree)

        self._progress("done", 100, "Wiki generation complete")
        return {
            "pagesGenerated": pages,
            "mode": "full",
            "failedModules": list(self.failed_modules),
        }

    def _render_module_pages(self, module_tree: list[dict[str, Any]]) -> int:
        """Render leaf and parent module pages, return count rendered."""
        total = count_modules(module_tree)
        done = [0]
        rendered = 0

        def report(name: str) -> None:
            done[0] += 1
            pct = 30 + int((done[0] / max(total, 1)) * 55)
            self._progress("modules", pct, f"{done[0]}/{total} — {name}")

        leaves, parents = flatten_tree(module_tree)

        for node in leaves:
            page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
            if os.path.exists(page_path):
                report(node["name"])
                continue
            try:
                generate_leaf_page(
                    node, self.wiki_dir, self.repo_path,
                    self.max_tokens, self.llm_config,
                )
                rendered += 1
                report(node["name"])
            except Exception:
                self.failed_modules.append(node["name"])
                report(f"Failed: {node['name']}")

        for node in parents:
            page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
            if os.path.exists(page_path):
                report(node["name"])
                continue
            try:
                generate_parent_page(node, self.wiki_dir, self.llm_config)
                rendered += 1
                report(node["name"])
            except Exception:
                self.failed_modules.append(node["name"])

        return rendered

    def _render_overview(self, module_tree: list[dict[str, Any]]) -> int:
        """Render the top-level overview page."""
        self._progress("overview", 88, "Generating overview page...")
        try:
            generate_overview(module_tree, self.wiki_dir, self.llm_config)
            return 1
        except Exception:
            self.failed_modules.append("_overview")
            return 0

    def _get_current_commit(self) -> str:
        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=self.repo_path,
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except Exception:
            return ""

    def _load_wiki_meta(self) -> dict[str, Any] | None:
        try:
            with open(os.path.join(self.wiki_dir, "meta.json"), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def _save_wiki_meta(self, meta: dict[str, Any]) -> None:
        with open(os.path.join(self.wiki_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def _save_module_tree(self, tree: list[dict[str, Any]]) -> None:
        with open(os.path.join(self.wiki_dir, "module_tree.json"), "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2)

    def _ensure_html_viewer(self) -> None:
        try:
            entries = os.listdir(self.wiki_dir)
        except OSError:
            return
        if any(f.endswith(".md") for f in entries):
            generate_html_viewer(self.wiki_dir, os.path.basename(self.repo_path))
