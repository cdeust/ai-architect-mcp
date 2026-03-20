"""Wiki generator — port of gitnexus core/wiki/generator.js (core orchestrator)."""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Callable

from .graph_queries import (
    init_wiki_db, close_wiki_db, get_files_with_exports, get_all_files,
    get_intra_module_call_edges, get_inter_module_call_edges,
    get_processes_for_files, get_all_processes,
    get_inter_module_edges_for_overview,
    get_community_file_mapping, get_inter_community_call_edges,
    get_cross_community_processes,
)
from .html_viewer import generate_html_viewer
from .llm_client import call_llm, estimate_tokens
from .prompts import fill_template, format_call_edges, format_processes, short_path
from .diagrams import build_call_graph_mermaid, build_sequence_diagram, build_inter_module_diagram
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

        self._progress("init", 2, "Connecting to knowledge graph...")
        init_wiki_db(self.kuzu_path)

        try:
            result = self._full_generation(current_commit)
        finally:
            close_wiki_db()

        self._ensure_html_viewer()
        return result

    def _full_generation(self, current_commit: str) -> dict[str, Any]:
        pages = 0
        self._progress("gather", 5, "Querying graph for file structure...")
        files_with_exports = get_files_with_exports()
        all_files = get_all_files()
        source_files = [f for f in all_files if not should_ignore_path(f)]

        if not source_files:
            raise RuntimeError("No source files found. Nothing to document.")

        export_map = {f["filePath"]: f for f in files_with_exports}
        enriched = [export_map.get(fp, {"filePath": fp, "symbols": []}) for fp in source_files]
        self._progress("gather", 10, f"Found {len(source_files)} source files")

        # Phase 1: Build module tree
        module_tree = self._build_module_tree(enriched)

        # Phase 2: Generate module pages
        total = self._count_modules(module_tree)
        done = [0]

        def report(name: str) -> None:
            done[0] += 1
            pct = 30 + int((done[0] / max(total, 1)) * 55)
            self._progress("modules", pct, f"{done[0]}/{total} — {name}")

        leaves, parents = self._flatten_tree(module_tree)
        for node in leaves:
            page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
            if os.path.exists(page_path):
                report(node["name"])
                continue
            try:
                self._generate_leaf_page(node)
                pages += 1
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
                self._generate_parent_page(node)
                pages += 1
                report(node["name"])
            except Exception:
                self.failed_modules.append(node["name"])

        # Phase 3: Overview
        self._progress("overview", 88, "Generating overview page...")
        try:
            self._generate_overview(module_tree)
            pages += 1
        except Exception:
            self.failed_modules.append("_overview")

        # Save metadata
        self._save_wiki_meta({
            "fromCommit": current_commit,
            "generatedAt": "",
            "model": self.llm_config.get("model", ""),
        })
        self._save_module_tree(module_tree)

        self._progress("done", 100, "Wiki generation complete")
        return {"pagesGenerated": pages, "mode": "full", "failedModules": list(self.failed_modules)}

    def _build_module_tree(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        snapshot = os.path.join(self.wiki_dir, "first_module_tree.json")
        try:
            with open(snapshot, encoding="utf-8") as f:
                parsed = json.load(f)
            if isinstance(parsed, list) and parsed:
                return parsed
        except (OSError, json.JSONDecodeError):
            pass

        self._progress("grouping", 12, "Querying graph communities...")
        communities = get_community_file_mapping()

        file_list = "\n".join(f"- {f['filePath']}: {', '.join(s['name'] for s in f.get('symbols', []))}" for f in files[:200])

        if communities:
            comm_text = "\n".join(f"**{c['label']}** ({len(c['files'])} files)" for c in communities[:20])
            prompt = f"Group these files into documentation modules.\n\nCommunities:\n{comm_text}\n\nFiles:\n{file_list}\n\nRespond with JSON only."
        else:
            prompt = f"Group these files into documentation modules.\n\nFiles:\n{file_list}\n\nRespond with JSON only."

        system = "You are a documentation architect. Group files into logical modules. Respond with JSON mapping module names to file arrays."
        self._progress("grouping", 18, "Asking LLM to group files...")
        result = call_llm(prompt, self.llm_config, system)
        content = result.get("content", "{}")
        m = re.search(r"\{[\s\S]*\}", content)
        if not m:
            return [{"name": "All", "slug": "all", "files": [f["filePath"] for f in files], "children": []}]

        grouping = json.loads(m.group(0))
        tree: list[dict[str, Any]] = []
        for name, file_paths in grouping.items():
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            tree.append({"name": name, "slug": slug, "files": file_paths, "children": []})

        with open(snapshot, "w", encoding="utf-8") as f:
            json.dump(tree, f)
        return tree

    def _generate_leaf_page(self, node: dict[str, Any]) -> None:
        files = node.get("files", [])
        intra = get_intra_module_call_edges(files)
        inter = get_inter_module_call_edges(files)
        processes = get_processes_for_files(files, 5)

        source = self._read_source_snippets(files, self.max_tokens)
        prompt = fill_template(
            "Write documentation for **{{MODULE_NAME}}**.\n\nSource:\n{{SOURCE_CODE}}\n\nInternal calls: {{INTRA_CALLS}}\nOutgoing: {{OUTGOING_CALLS}}\nIncoming: {{INCOMING_CALLS}}\nFlows: {{PROCESSES}}",
            {
                "MODULE_NAME": node["name"],
                "SOURCE_CODE": source,
                "INTRA_CALLS": format_call_edges(intra),
                "OUTGOING_CALLS": format_call_edges(inter.get("outgoing", [])),
                "INCOMING_CALLS": format_call_edges(inter.get("incoming", [])),
                "PROCESSES": format_processes(processes),
            },
        )
        result = call_llm(prompt, self.llm_config, "You are a technical documentation writer.")
        content = result.get("content", "")

        # Append deterministic diagrams
        call_graph = build_call_graph_mermaid(node["name"], intra)
        if call_graph:
            content += f"\n\n## Call Graph\n\n```mermaid\n{call_graph}\n```\n"
        for proc in processes[:3]:
            seq = build_sequence_diagram(proc)
            if seq:
                content += f"\n\n### {proc.get('label', '')}\n\n```mermaid\n{seq}\n```\n"

        page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_parent_page(self, node: dict[str, Any]) -> None:
        children_docs = ""
        for child in node.get("children", []):
            child_path = os.path.join(self.wiki_dir, f"{child['slug']}.md")
            try:
                with open(child_path, encoding="utf-8") as f:
                    doc = f.read()
                summary_end = doc.find("<!-- summary-end -->")
                snippet = doc[:summary_end] if summary_end > 0 else doc[:500]
                children_docs += f"### {child['name']}\n{snippet}\n\n"
            except OSError:
                children_docs += f"### {child['name']}\n(documentation not yet generated)\n\n"

        prompt = f"Write documentation for **{node['name']}** module group.\n\nSub-modules:\n{children_docs}"
        result = call_llm(prompt, self.llm_config, "You are a technical documentation writer. Synthesize child docs.")
        page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(result.get("content", ""))

    def _generate_overview(self, module_tree: list[dict[str, Any]]) -> None:
        all_files_per_module: dict[str, list[str]] = {}
        for node in module_tree:
            all_files_per_module[node["name"]] = node.get("files", [])

        module_edges = get_inter_module_edges_for_overview(all_files_per_module)
        all_procs = get_all_processes(10)

        summaries = ""
        for node in module_tree:
            page_path = os.path.join(self.wiki_dir, f"{node['slug']}.md")
            try:
                with open(page_path, encoding="utf-8") as f:
                    doc = f.read()
                end = doc.find("<!-- summary-end -->")
                summary = doc[:end] if end > 0 else doc[:300]
                summaries += f"**{node['name']}**: {summary.strip()}\n\n"
            except OSError:
                summaries += f"**{node['name']}**: (not yet generated)\n\n"

        edge_text = "\n".join(f"{e['from']} -> {e['to']}: {e['count']} calls" for e in module_edges[:20])
        proc_text = format_processes(all_procs[:5])

        prompt = (
            f"Write the overview page for this repository wiki.\n\n"
            f"Module summaries:\n{summaries}\n\n"
            f"Inter-module edges:\n{edge_text}\n\n"
            f"Key flows:\n{proc_text}"
        )
        result = call_llm(prompt, self.llm_config, "You are a technical documentation writer. Write the top-level overview.")
        content = result.get("content", "")

        diagram = build_inter_module_diagram(module_edges)
        if diagram:
            content += f"\n\n## Architecture\n\n```mermaid\n{diagram}\n```\n"

        page_path = os.path.join(self.wiki_dir, "overview.md")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _read_source_snippets(self, file_paths: list[str], max_tokens: int) -> str:
        snippets: list[str] = []
        total = 0
        for fp in file_paths:
            try:
                full = os.path.join(self.repo_path, fp)
                with open(full, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                tokens = estimate_tokens(content)
                if total + tokens > max_tokens:
                    break
                snippets.append(f"--- {fp} ---\n{content}")
                total += tokens
            except OSError:
                pass
        return "\n\n".join(snippets) if snippets else "(no source available)"

    def _flatten_tree(self, tree: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        leaves: list[dict[str, Any]] = []
        parents: list[dict[str, Any]] = []
        for node in tree:
            if node.get("children"):
                parents.append(node)
                l, p = self._flatten_tree(node["children"])
                leaves.extend(l)
                parents.extend(p)
            else:
                leaves.append(node)
        return leaves, parents

    def _count_modules(self, tree: list[dict[str, Any]]) -> int:
        count = 0
        for node in tree:
            count += 1
            if node.get("children"):
                count += self._count_modules(node["children"])
        return count

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
