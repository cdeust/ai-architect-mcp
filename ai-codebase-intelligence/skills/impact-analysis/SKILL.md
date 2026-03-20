# Impact Analysis Skill

## Purpose
Assess the blast radius of proposed changes before implementation.

## When to Use
- Before refactoring a symbol
- Planning API changes
- Evaluating dependency upgrades
- Pre-PR risk assessment

## Operations

1. **Target**: Identify the symbol(s) being changed
2. **Impact**: Run `ai_architect_codebase_impact` with both directions
3. **Processes**: Check which execution processes are affected
4. **Risk**: Categorize impact by depth (d=1 HIGH, d=2 MEDIUM, d=3 LOW)
5. **Test plan**: Generate test recommendations from affected processes

## Workflow

```
Identify target → Impact analysis → Group by depth → Identify processes → Generate test plan
```

## Output
- Impacted symbols grouped by depth and risk level
- Affected processes listed by priority
- Test plan covering all affected paths
