# Test Fixtures

This directory contains fixture files for deterministic module tests.

Every deterministic function in the MCP server must have a corresponding fixture file that defines the exact expected output for a given input. Tests compare actual output against fixture data using bit-for-bit matching — no fuzzy comparisons, no "close enough."

## Convention

Fixture files follow the naming pattern:

```
{module}_{function}_{scenario}.json
```

For example:

- `hor_rule_001_pass.json` — Expected output when HOR rule 1 passes
- `hor_rule_001_fail.json` — Expected output when HOR rule 1 fails
- `compound_score_basic.json` — Expected compound score for basic input

## Requirements

- Every new deterministic function must have a fixture file before the function is considered complete
- Fixture files are JSON for structured data or `.txt` for string outputs
- Fixture data must be committed alongside the function implementation
- Modifying a deterministic function requires updating its fixture files
