# Debugging Skill

## Purpose
Trace bugs through the codebase using graph analysis to find root causes efficiently.

## When to Use
- Bug reports with stack traces
- Unexpected behavior requiring call chain analysis
- Performance issues requiring hotspot identification

## Operations

1. **Locate**: Use `ai_architect_codebase_query` to find the symptom location
2. **Context**: Get 360° view of the affected symbol
3. **Trace upstream**: Use `ai_architect_codebase_impact` with direction=upstream
4. **Trace downstream**: Check what the affected code calls
5. **Narrow**: Cross-reference with process membership to find the execution flow

## Workflow

```
Query symptom → Get context → Impact upstream → Check callers → Identify root cause
```

## Output
- Root cause identification with confidence level
- Affected execution processes
- Recommended fix location
