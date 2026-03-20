---
name: codebase-indexing
version: "1.0"
status: active
---

# Codebase Indexing

## Purpose
Index a repository to build the knowledge graph. Each phase is a separate tool call — if one fails, diagnose, fix, and continue without losing prior work.

## When to Use
- First time analyzing a repository
- After significant code changes
- When codebase tools return stale or empty results

## Tools (call in order)

### Phase 1: Scan
```
ai_architect_codebase_scan(repo_path="/path/to/repo")
```
Returns: file count, language breakdown, total bytes.

**If this fails:** Check repo_path exists and is a git repository.

### Phase 2: Parse + Resolve + Community + Process
```
ai_architect_codebase_parse(repo_path="/path/to/repo")
```
Returns: node count, relationship count, communities, processes.

**If this fails:** The scan succeeded so files exist. Check:
- tree-sitter grammar available for the language? Check language breakdown from scan.
- File too large? Default limit is 512KB — skip oversized files.
- Memory pressure? The 20MB chunk budget bounds per-chunk memory.

**If community detection fails:** Pipeline continues — communities are optional. Query/context/impact still work without communities.

**If process detection returns 0:** CALLS edges may have low confidence (< 0.5). This is expected for repos where most calls are cross-file fuzzy matches.

### Phase 3: Store
```
ai_architect_codebase_store(repo_path="/path/to/repo")
```
Returns: db_path, db_size_mb, node/edge counts.

**If this fails:** SQLite write error — check disk space and permissions on .gitnexus/ directory.

### Convenience: Full Pipeline
```
ai_architect_codebase_analyze(repo_path="/path/to/repo")
```
Runs all 3 phases in sequence. Use when you don't need per-phase control.

## After Indexing

Verify with:
```
ai_architect_codebase_query(query="main entry point")
```
If results are empty, the FTS index may not have built. Call `store` again.

## Recovery Patterns

| Error | Action |
|-------|--------|
| "No files scanned" | Wrong repo_path. Check it's absolute and exists. |
| Parse returns 0 nodes | Language not supported or all files too large. Check scan language breakdown. |
| Store fails | Disk full or permissions. Check .gitnexus/ is writable. |
| Query returns empty after index | FTS index didn't build. Re-run store. |
| Community count is 0 | leidenalg/igraph not installed. Install: `pip install leidenalg python-igraph` |
