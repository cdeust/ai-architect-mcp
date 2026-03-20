# Refactoring Skill

## Purpose
Plan and execute safe refactoring operations with full dependency awareness.

## When to Use
- Renaming symbols across the codebase
- Extracting modules or classes
- Moving code between files
- Reducing coupling between communities

## Operations

1. **Analyze**: Get context for the target symbol
2. **Impact**: Full blast radius in both directions
3. **Plan**: Generate refactoring steps ordered by dependency depth
4. **Verify**: After changes, re-run detect_changes to confirm completeness
5. **Community**: Check if refactoring improves community cohesion

## Workflow

```
Context → Impact → Plan steps → Execute → Detect changes → Verify completeness
```

## Output
- Ordered list of files to modify
- Expected impact on community cohesion
- Verification checklist
