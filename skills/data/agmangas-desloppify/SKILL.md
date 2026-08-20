---
name: desloppify
description: Improve code quality in a repository using desloppify. Use when auditing a codebase, raising code quality scores, cleaning up maintainability issues, or systematically working through desloppify findings.
argument-hint:
  - path
disable-model-invocation: true
install_source: official
install_method: download
skill_id: official_7Xfveyts
enabled_at: 1787231434110
version: 1.0.0
name_zh: 代码质量
---

Use this skill to improve the quality of the codebase with `desloppify`.

## Goal

Raise the strict score as high as possible through real code improvements. Do not game the score or apply cosmetic fixes that do not meaningfully improve the code.

## Arguments

- `$ARGUMENTS` is the scan target.
- If no argument is provided, use `.`.

Set:

```bash
SCAN_PATH="${ARGUMENTS:-.}"
```

## Setup

This workflow requires Python 3.11+.

Install and update the skill guidance:

```bash
pip install --upgrade "desloppify[full]"
desloppify update-skill claude
```

If the environment is not using Claude, use the appropriate target instead: `claude`, `cursor`, `codex`, `copilot`, `windsurf`, or `gemini`.

## Exclusions

Before scanning, inspect the repository for directories that should obviously be excluded, such as:

- Vendor or third-party code
- Build output
- Generated code
- Temporary worktrees
- Cache directories
- Dependency directories
- Large artifacts not intended for maintenance

Exclude obvious candidates with:

```bash
desloppify exclude <path>
```

If an exclusion is questionable, stop and ask for confirmation before applying it.

## Initial scan

Run:

```bash
desloppify scan --path "$SCAN_PATH"
desloppify next
```

## Main loop

This is your main job. Repeat the following until blocked, complete, or awaiting confirmation:

1. Run `desloppify next`.
2. Read the issue carefully.
3. Fix the problem properly in the indicated file or files.
4. Run the resolve command provided by `desloppify`.
5. Run `desloppify next` again.

Do not optimize for closing tickets quickly. Optimize for durable code quality improvements.

## Working style

Apply the same care to both large refactors and small detailed fixes.

- Fix root causes where practical.
- Keep changes coherent and maintainable.
- Avoid minimal edits that satisfy the tool without improving the code.
- Respect repository conventions unless they are part of the problem.
- Surface risky changes or ambiguous fixes before proceeding.

## Planning

Use:

```bash
desloppify plan
```

when it helps reorder priorities or cluster related work into a more efficient sequence.

Rescan periodically as the codebase changes:

```bash
desloppify scan --path "$SCAN_PATH"
```

## Rules

- Follow the instructions from `desloppify scan` and `desloppify next`.
- Do not replace tool guidance with your own ad hoc prioritization when the tool gives explicit workflow instructions.
- Ask before excluding questionable paths.
- Keep going until there is no meaningful next task or user input is required.
