# PR Review Skill

## Purpose
Review pull requests with full codebase context — not just the diff.

## When to Use
- Reviewing any pull request
- Assessing whether a PR's changes are complete
- Checking for unintended side effects

## Operations

1. **Changes**: Use `ai_architect_codebase_detect_changes` on the PR diff
2. **Impact**: For each changed symbol, run impact analysis
3. **Context**: Get 360° views for modified symbols
4. **Gaps**: Identify symbols that should have been modified but weren't
5. **Processes**: Check all affected execution processes have test coverage

## Workflow

```
Detect changes → Impact per symbol → Check completeness → Identify gaps → Summarize risk
```

## Output
- Change summary with blast radius
- Missing modifications (symbols that should have changed)
- Process coverage assessment
- Risk level for the PR
