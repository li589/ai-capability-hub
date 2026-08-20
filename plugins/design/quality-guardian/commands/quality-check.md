---
description: Run a full quality check on the current project — evidence, context, UI, and verification
argument-hint: [optional: specific file or feature to check]
---

# /quality-guardian:quality-check

Run the complete Quality Suite check on the current project or a specific area.

## What This Does

1. **Context Cartographer** — Builds a repo map and identifies relevant files
2. **Evidence Guard** — Verifies key claims about the project structure and dependencies
3. **UI Taste Guard** — Reviews UI code for anti-patterns (if web/UI files exist)
4. **Verification Runner** — Runs lint, typecheck, test, and build

## Usage

```
/quality-guardian:quality-check                    # Full project
/quality-guardian:quality-check src/components     # Specific directory
/quality-guardian:quality-check settings feature   # Feature area
```

## Expected Output

The agent will produce a **Quality Report** containing:

1. **Repo Map** — Project structure and stack summary
2. **Evidence Summary** — Verified vs unverified claims
3. **UI Review** (if applicable) — Anti-pattern check results
4. **Verification Report** — Lint, typecheck, test, build results
5. **Recommendations** — Prioritized list of improvements

## Steps the Agent Will Follow

1. Scan project structure (Glob)
2. Read package.json / config files
3. Identify design system and key patterns
4. Run available verification commands
5. Review UI files for anti-patterns (if found)
6. Compile final quality report
