---
name: create-plan
description: Convert requirements into executable stories with tasks, dependencies, and targeted technical guidance for coding execution. Use when user wants a requirements doc or feature brief turned into an implementation plan or story JSON.
install_source: official
install_method: download
skill_id: official40838904
enabled_at: 1785348233175
version: 1.0.0
name_zh: 创建计划
---

# Create Plan

Turn requirements + repo context into executable stories. Return JSON only unless user asks for discussion. Do not write files unless user asks.

## Quick start

1. Get requirements source and repo path
2. Read requirements, context, ADRs, repo shape
3. Return blocker-ordered stories as one JSON object

## Inputs

- Requirements from user or file
- Repo path from user
- If either is missing, ask before planning

## Workflow

1. **Load requirements**
   - Read requirements file if provided
   - Otherwise use conversation context or ask user to paste requirements

2. **Scan codebase**
   - Read `<project-root>/.agent/CONTEXT.md` if present
   - Read ADRs under `<project-root>/.agent/adr/` if present
   - Briefly scan repo structure to identify modules, conventions, and constraints

3. **Draft stories**
   - Map each use case, or tight group of related use cases, into one story
   - Prefer migration-wave stories over broad cross-cutting stories
   - Keep each story to one user-visible outcome or one bounded implementation concern

4. **Define execution details**
   - Add ordered implementation tasks
   - Add story dependencies (`blockedBy`)
   - Add concise tech guidance only when architecture, patterns, or prior decisions matter

5. **Normalize story size**
   - Every story must be completable in one `coding-mode` run
   - Split any story that:
     - covers multiple outcomes
     - spans multiple loose domains or seams
     - has multiple major phases
     - lacks a clear test/demo boundary
     - needs more than 5–7 tasks

6. **Validate**
   - Every use case and acceptance criterion must map to at least one story task
   - Edge cases must appear in story tasks
   - Final output must contain only stories with `executionFit: "fits-one-run"`

7. **Present**
   - Return single JSON object using schema below
   - Ask user whether story split, dependencies, and tech guidance look right
   - If user wants plan saved, ask for path and write it there
   - If user wants markdown, default under `<project-root>/.agent/`

## Example mapping

Requirement use case: "User can reset password by email"

Story shape:
- title: `Add password reset request flow`
- covers: `[2]`
- tasks: add endpoint, issue token, send email, add tests
- demoBoundary: `User can request reset email successfully`

## JSON Schema

```json
{
  "feature": "[Feature Name]",
  "source": ".agent/requirements.md",
  "codebase": "[repo path]",
  "stories": [
    {
      "id": "S1",
      "title": "[Title]",
      "covers": [1, 2],
      "tasks": ["Task 1", "Task 2"],
      "executionFit": "fits-one-run",
      "demoBoundary": "User can complete X flow end-to-end",
      "scopeNotes": "Single bounded concern. Clear test boundary.",
      "blockedBy": [],
      "techGuidance": null
    }
  ]
}
```

## Rules

- Every story must trace to requirement use case(s)
- Order stories with blockers first
- `blockedBy` = array of story IDs
- `techGuidance` = string or `null`
- Do not output oversized stories; split them first
