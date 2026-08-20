# Scan Report Format

Write the report to `.claude-scan/<skill-name>.md` using this structure:

```markdown
# Scan Report: <skill-name>

_Generated: <date> | Scope: <file patterns> | Files scanned: <N>_

## Executive Summary

<2-3 sentences summarizing the overall health of the codebase against these criteria. Mention the most critical findings and any positive patterns observed.>

## Criteria Evaluated

| ID | Criterion | Violations |
|----|-----------|------------|
| C1 | <description> | <count> |
| C2 | <description> | <count> |
| ... | ... | ... |

## Findings

### Critical

| File | Line | Criterion | Description |
|------|------|-----------|-------------|
| `path/to/file.ts` | 42 | C1 | <description> |

_<N> critical findings_

### Warning

| File | Line | Criterion | Description |
|------|------|-----------|-------------|
| `path/to/file.ts` | 88 | C3 | <description> |

_<N> warnings_

### Info

| File | Line | Criterion | Description |
|------|------|-----------|-------------|
| `path/to/file.ts` | 12 | C5 | <description> |

_<N> info findings_

## Patterns Observed

<Bullet list of cross-cutting observations. What patterns keep showing up? Are violations clustered in certain areas? Are there areas that are particularly clean?>

## Statistics

- **Files scanned**: <N>
- **Total violations**: <N> (<N> critical, <N> warning, <N> info)
- **Clean files**: <N> (<percentage>%)
- **Most violated criterion**: C<n> — <description> (<count> violations)

## Recommended Fix Order

Fix in this order to minimize conflicts and maximize impact:

### Batch 1 (Critical)
<List of files and violations to fix first — grouped so no file appears in multiple batches>

### Batch 2 (Warning - High Impact)
<Next priority group>

### Batch 3 (Warning - Remaining)
<Lower priority warnings>

### Batch 4 (Info)
<Style and minor improvements — optional>
```

## Notes

- If a severity level has zero findings, omit that section entirely
- Keep descriptions concise — one sentence per finding
- Sort findings within each severity by file path for easy scanning
- In Recommended Fix Order, group files that are in the same directory together
