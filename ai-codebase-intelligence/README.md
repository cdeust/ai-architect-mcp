# AI Codebase Intelligence

Language-agnostic codebase intelligence engine — index, search, and analyze code across 13 languages via MCP.

## Architecture

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each module has one job. `parser_loader.py` loads parsers. `call_routing.py` classifies calls. `export_detection.py` checks exports. |
| **Open/Closed** | New languages added by implementing extractors/resolvers — existing code untouched. Registry pattern in `__init__.py` dispatches by language. |
| **Liskov Substitution** | `InMemoryGraphStorage` and `KuzuAdapter` both implement `GraphStoragePort` — interchangeable in all consumers. |
| **Interface Segregation** | Three focused ports: `GraphStoragePort` (graph ops), `FullTextSearchPort` (FTS), `GitPort` (git ops). No god-interface. |
| **Dependency Inversion** | Stage logic depends on port ABCs, never on concrete adapters. `KuzuAdapter` injected at composition root. |

### Dependency Injection

```
Port (ABC)          ←  Stage Logic depends on
  ↑
Adapter (Concrete)  →  Injected at server.py / composition root
```

- `GraphStoragePort` → `KuzuAdapter` (production) / `InMemoryGraphStorage` (test)
- `GitPort` → `GitAdapter` (production) / test doubles
- `FullTextSearchPort` → KuzuDB FTS (production)

### Factory Pattern

- `get_type_extractor(language)` → returns language-specific `TypeExtractor`
- `get_resolver(language)` → returns language-specific `Resolver`
- `classify_call(name, receiver, language)` → dispatches to per-language classifier

### Package Structure (DDD Layers)

```
_models/        → Domain models (Pydantic v2)
_config/        → Configuration (supported languages, ignore lists)
_storage/       → Infrastructure (ports + adapters for graph DB, git)
_parsing/       → AST parsing (tree-sitter integration)
_extraction/    → Symbol extraction (types, calls, imports, heritage)
_resolution/    → Symbol resolution (4-tier with caching)
_analysis/      → Graph analysis (Leiden communities, process detection)
_search/        → Search (BM25 + RRF hybrid)
_pipeline/      → Orchestration (6-phase ingestion)
_embeddings/    → Vector embeddings (sentence-transformers)
_wiki/          → Documentation generation (4-phase LLM pipeline)
_server/        → HTTP API + MCP-over-StreamableHTTP
_cli/           → CLI commands (typer)
_tools/         → MCP tool definitions (7 tools + 8 resources + 2 prompts)
```

### Enforcement

| Rule | Limit | Verified |
|------|-------|----------|
| File length | ≤ 300 lines | All 80 modules compliant |
| Function length | ≤ 40 lines | Enforced by design |
| Type hints | 100% coverage | `from __future__ import annotations` on every file |
| Docstrings | Google style | On every public function |
| No bare except | Zero | Specific exceptions only |
| No wildcard imports | Zero | Explicit imports only |

## 10 Key Algorithms

1. **Ingestion Pipeline** — 6 phases: scan → structure → parse → resolve → community → process
2. **Symbol Resolution** — 4 tiers: same-file (0.95) → named imports (0.9) → import-scoped (0.9) → global (0.5)
3. **Call Extraction** — classify form (free/member/constructor) → resolve receiver → constructor binding verification
4. **Type Environment** — scope-aware binding: function scope > class scope > file scope
5. **Import Resolution** — suffix index O(1) lookup, 100K cache with 20% FIFO eviction
6. **MRO** — C3 linearization for diamond inheritance, DFS fallback for single-inheritance languages
7. **Community Detection** — Leiden algorithm (resolution 1.0 small / 2.0 large), 60s timeout
8. **Process Tracing** — entry point scoring → BFS (depth 10, branching 4) → subset dedup
9. **Hybrid Search** — BM25 across 5 FTS indexes → RRF fusion (K=60)
10. **Impact Analysis** — BFS from target, depth 1-3, confidence ≥ 0.7, risk categorization

## 7 MCP Tools

| Tool | Description |
|------|-------------|
| `ai_architect_codebase_analyze` | Index a repository |
| `ai_architect_codebase_query` | Hybrid search: BM25 + process ranking |
| `ai_architect_codebase_context` | 360° symbol view |
| `ai_architect_codebase_impact` | Blast radius analysis |
| `ai_architect_codebase_detect_changes` | Git diff → affected symbols |
| `ai_architect_codebase_cypher` | Raw Cypher queries (read-only) |
| `ai_architect_codebase_list_repos` | List indexed repositories |

## 13 Supported Languages

TypeScript, JavaScript, Python, Swift, Java, Kotlin, C#, Go, Rust, PHP, Ruby, C, C++

## Installation

```bash
pip install ./ai-codebase-intelligence
```

## Usage

```bash
# CLI
ai-codebase-intelligence analyze /path/to/repo
ai-codebase-intelligence query "bias correction"
ai-codebase-intelligence context BiasCorrector

# MCP Server
python3 -m ai_codebase_intelligence.server
```

## Testing

```bash
cd ai-codebase-intelligence
PYTHONPATH=src python3 -m pytest tests/ -q
# 335 passed, 0 skipped
```

## License

MIT
