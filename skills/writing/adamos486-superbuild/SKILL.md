---
name: superbuild
description: Use when executing implementation plans phase-by-phase with strict enforcement of quality gates, tests, and Definition of Done. Triggers on "build this plan", "execute plan", "implement phases", or when user provides a plan document to execute.
metadata:
  version: 1.0.0
  author: skulto
compatibility: Requires plan document in superplan format. Works with any codebase with quality tools configured.
install_source: official
install_method: download
skill_id: official_1VDavTtM
enabled_at: 1787231636796
version: 1.0.0
name_zh: 文档计划执行
---

# Superbuild: Plan Execution Engine

Execute implementation plans one phase at a time with strict quality enforcement, test verification, and conventional commit generation.

## Overview

Superbuild is a **rigid execution engine** for implementation plans. It enforces:
- Phase-by-phase execution (no skipping ahead)
- Definition of Done verification before phase completion
- Test presence and passing verification
- Linter/formatter/typechecker enforcement
- Conventional commit message generation per phase

**This is NOT a planning skill.** Use `superplan` to create plans, then `superbuild` to execute them.

## Critical Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SUPERBUILD EXECUTION FLOW                       │
│                     (REPEAT FOR EACH PHASE)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INGEST PLAN    │  User provides plan document path              │
│         ↓          │  NO PLAN = EXIT (ask user, then exit if none)  │
│  2. READ PHASES    │  Output ALL phases with estimates              │
│         ↓          │  IF context high → suggest compact first       │
│  3. EXECUTE PHASE  │  One phase at a time (or parallel if marked)   │
│         ↓          │  USE SUB-AGENTS for parallel phases            │
│  4. ENFORCE DOD    │  Tests exist? Tests pass? Linter? Formatter?   │
│         ↓          │  ALL must pass → continue. ANY fail → STOP     │
│  5. UPDATE PLAN    │  Check off tasks, update status in plan file   │
│         ↓          │  ⚠️  THIS HAPPENS AFTER EVERY PHASE            │
│  6. COMMIT MSG     │  Generate conventional commit (NEVER git ops)  │
│         ↓          │  User handles all git operations               │
│  7. FUNCTIONAL TEST│  Explain how to test. Offer integration script │
│         ↓          │  NEVER auto-create scripts. ALWAYS ask first   │
│  8. STOP           │  Full stop. Suggest compact. Wait for user.    │
│                    │  OVERRIDE: --build-all flag continues          │
│                                                                     │
│  ════════════════════════════════════════════════════════════════   │
│  Steps 3-8 repeat for EACH PHASE. Plan updates after EVERY phase.  │
│  ════════════════════════════════════════════════════════════════   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Step 1: Ingest Plan

**REQUIRED: Plan document must be provided.**

```
I'll help you execute your implementation plan.

Please provide the plan document:
1. Path to plan file (e.g., docs/feature-plan.md)
2. Paste the plan content directly

Which would you prefer?
```

**If no plan provided after asking:** EXIT immediately.

```
I cannot execute without a plan document.

To create a plan, use the `superplan` skill first:
  /superplan

Then come back with the completed plan.

[EXIT - No further action]
```

**NO EXCEPTIONS.** Do not improvise. Do not create plans on the fly. Do not proceed without a plan document.

## Step 2: Read All Phases

After ingesting the plan:

1. **Output all phases** with their estimates and dependencies
2. **Check context usage** - if high, suggest compacting first

```
PLAN LOADED: [Feature Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Phase | Name | Est. | Depends On | Parallel With | Status |
|-------|------|------|------------|---------------|--------|
| 0 | Bootstrap | 5 | - | - | ⬜ |
| 1 | Setup | 3 | 0 | - | ⬜ |
| 2A | Backend | 8 | 1 | 2B, 2C | ⬜ |
| 2B | Frontend | 5 | 1 | 2A, 2C | ⬜ |
| 2C | Tests | 3 | 1 | 2A, 2B | ⬜ |
| 3 | Integration | 5 | 2A,2B,2C | - | ⬜ |

Total: 29 points | Parallel phases: 2A, 2B, 2C

⚠️  Context Usage Advisory
If context is high, consider compacting before continuing.
Large plans consume significant context per phase.

Ready to execute Phase 0?
```

## Step 3: Execute Phase

### Sequential Phases

Execute one at a time. Do not proceed to next phase until current is COMPLETE.

### Parallel Phases

For phases marked "Parallel With", **MUST use sub-agents or parallel Task tool calls**.

```
EXECUTING PARALLEL PHASES: 2A, 2B, 2C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Launching 3 parallel sub-agents...

[Sub-agent 2A: Backend implementation]
[Sub-agent 2B: Frontend implementation]
[Sub-agent 2C: Test implementation]

Each sub-agent MUST return:
- Implementation status
- Definition of Done checklist status
- Conventional commit message
```

**CRITICAL:** Each sub-agent returns its commit message. Main agent MUST bubble up ALL commit messages to user.

## Step 4: Enforce Definition of Done

**EVERY phase must pass ALL quality gates before completion.**

### Quality Gate Checklist

```
DEFINITION OF DONE - Phase [X]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Tests exist for new code
[ ] All tests pass (new AND existing)
[ ] Linter passes ([detected linter])
[ ] Formatter passes ([detected formatter])
[ ] Type checker passes ([detected checker])
[ ] No new warnings introduced
[ ] Plan document updated (checkboxes, status)  ← BEFORE commit message
```

### Enforcement Rules

| Check | If PASS | If FAIL |
|-------|---------|---------|
| Tests exist | Continue | **STOP** - Point out missing tests |
| Tests pass | Continue | **STOP** - Ask user to fix |
| Linter | Continue | **STOP** - Ask user to fix |
| Formatter | Continue | **STOP** - Ask user to fix |
| Type checker | Continue | **STOP** - Ask user to fix |
| Plan updated | Generate commit | **STOP** - Update plan first |

**STOP means STOP.** Do not proceed. Do not offer to fix automatically. Ask user to fix and re-run.

### Failure Output Format

When any check fails, output:

```
⛔ DEFINITION OF DONE FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issue: [Missing tests | Tests failing | Linter errors | etc.]
[Details of what failed]
Please fix, then tell me to continue.
[EXECUTION HALTED]
```

**See `references/ENFORCEMENT-GUIDE.md`** for detailed failure message templates and output parsing patterns.

## Step 5: Update Plan Document (EVERY PHASE)

**⚠️ MANDATORY: This step executes after EVERY phase, not just at the end.**

After ALL quality gates pass, BEFORE generating commit message, UPDATE THE PLAN FILE:

1. **Check off completed tasks** (`- [ ]` → `- [x]`)
2. **Update phase status** in overview table (`⬜` → `✅`)
3. **Mark DoD items complete** (`- [ ]` → `- [x]`)

```
PLAN DOCUMENT UPDATED - Phase [X]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: [plan-file-path]

Updates applied:
- Tasks: X/X items checked [x]
- DoD: X/X items checked [x]
- Status: ⬜ → ✅

The plan now reflects Phase [X] completion.
```

**See `references/PLAN-UPDATES.md` for detailed patterns and error handling.**

**WHY EVERY PHASE:**
- Plan survives context compaction (conversation may not)
- Progress visible to anyone reading the plan
- Enables clean handoff between sessions
- Creates audit trail in git history

**DO NOT SKIP THIS STEP.** If you find yourself generating a commit message without updating the plan first, STOP and update the plan.

## Step 6: Generate Conventional Commit

**After Definition of Done passes, generate commit message.**

**CRITICAL: OUTPUT ONLY. NEVER run git commands.**

```
PHASE [X] COMPLETE - Conventional Commit Message
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<type>(<scope>): <short summary>

<body - detailed description of changes>

Files changed:
- path/to/file1.ts (CREATE)
- path/to/file2.ts (MODIFY)
- path/to/file3.ts (DELETE)

<footer - issue refs, breaking changes>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  DO NOT COMMIT - Copy this message and run:
    git add . && git commit -m "..."

User handles all git operations.
```

### Commit Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructure (no behavior change) |
| `test` | Adding/updating tests |
| `docs` | Documentation |
| `style` | Formatting (no code change) |
| `chore` | Build, config, dependencies |
| `perf` | Performance improvements |

### Git CLI Safe Commit Messages

**CRITICAL: Commit messages must be safe for direct use with `git commit -m`.**

**AVOID:** Double quotes, backticks, dollar signs, exclamation marks, backslashes, hash at line start
**SAFE:** Letters, numbers, spaces, `-`, `_`, `.`, `,`, `:`, `(`, `)`, `/`, `'`

**See `references/COMMIT-FORMAT.md` for full character table and HEREDOC format for multi-line messages.**

### Parallel Phase Commits

When parallel phases complete, output ALL commit messages:

```
PARALLEL PHASES COMPLETE (2A, 2B, 2C)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 2A - Commit Message:
━━━━━━━━━━━━━━━━━━━━━━━━━━
feat(api): implement user authentication endpoints
...

PHASE 2B - Commit Message:
━━━━━━━━━━━━━━━━━━━━━━━━━━
feat(ui): create login form component
...

PHASE 2C - Commit Message:
━━━━━━━━━━━━━━━━━━━━━━━━━━
test(auth): add authentication test coverage
...

⚠️  Create separate commits for each phase, or squash as appropriate.
    User handles all git operations.
```

## Step 7: Functional Testing Instructions

**After commit message, explain how to functionally test the phase.**

```
FUNCTIONAL TESTING - Phase [X]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To manually verify this phase works:

1. [Step 1 - e.g., Start the development server]
   $ npm run dev

2. [Step 2 - e.g., Navigate to the feature]
   Open http://localhost:3000/[feature]

3. [Step 3 - e.g., Test the happy path]
   - Fill in [field1] with "test value"
   - Click [button]
   - Verify [expected result]

4. [Step 4 - e.g., Test error handling]
   - Submit empty form
   - Verify error message appears

Expected Results:
- [Result 1]
- [Result 2]
```

### Integration Test Script Offer

**ONLY if applicable. ALWAYS ask. NEVER auto-create.**

```
Would you like me to write an integration test script for this phase?

This would:
- Automate the manual verification steps above
- Be saved to scripts/test-phase-[X].sh (or .py)
- Be runnable for regression testing

Options:
1. Yes, write the integration test script
2. No, manual testing is sufficient

[WAIT FOR USER RESPONSE]
```

**If user says yes:** Write script to `scripts/` directory.
**If user says no:** Continue to Step 8.

## Step 8: Stop Execution

**FULL STOP after each phase (unless --build-all override).**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE [X] EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
- Definition of Done: ✅ All checks passed
- Plan Document: ✅ Updated (tasks and status checked off)
- Conventional Commit: ✅ Generated (user to commit)
- Functional Testing: ✅ Instructions provided

Progress:
| Phase | Status |
|-------|--------|
| 0 | ✅ Complete |
| 1 | ✅ Complete |
| 2A | ⬜ Next |
| 2B | ⬜ Pending |
| 2C | ⬜ Pending |
| 3 | ⬜ Pending |

💡 Context Management Suggestion
Consider compacting the conversation before the next phase
to preserve context for the remaining work.

[EXECUTION PAUSED]

To continue: "Continue to Phase 2A"
To compact first: Use /compact then return with "Resume superbuild"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Context Compaction Behavior

**CRITICAL: If this session resumes after context compaction:**

1. Complete ONLY the phase that was in-progress
2. Output the commit message and functional test instructions
3. STOP - Do not auto-continue to next phase
4. Wait for explicit user instruction: "Continue to Phase X"

The todo list showing pending phases is NOT authorization to continue.
Only explicit user instruction authorizes next phase execution.

```
POST-COMPACTION RESUME
━━━━━━━━━━━━━━━━━━━━━━

Detected: Session resumed after compaction
Phase in progress: [X]

Completing Phase [X]...
[finish work]

PHASE [X] COMPLETE
[commit message + functional test instructions]

[EXECUTION PAUSED]

Remaining phases: [list]
To continue: "Continue to Phase [Y]"

⚠️  I will NOT auto-continue. Awaiting your instruction.
```

### Build-All Override

**ONLY if user explicitly specifies.**

```
⚠️  BUILD-ALL MODE DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━

You've requested to build the entire plan without stopping.

This is NOT RECOMMENDED because:
- Context may be exhausted mid-build
- Errors compound across phases
- You lose ability to commit incrementally

Are you sure you want to continue?
1. Yes, build all phases (override safety)
2. No, execute phase by phase (recommended)
```

## Rationalizations to Reject

| Excuse | Reality |
|--------|---------|
| "Let me just do the next phase too" | **NO.** Stop after each phase. |
| "The tests are mostly there" | **NO.** Tests must exist for ALL new code. |
| "It's just a small linting error" | **NO.** All quality gates must pass. |
| "I'll commit later" | **NO.** Generate commit message NOW. |
| "This phase doesn't need tests" | **NO.** Every phase with code needs tests. |
| "Let me skip to the important part" | **NO.** Execute phases in dependency order. |
| "I can fix the formatter later" | **NO.** Formatter must pass before completion. |
| "The user wants to move fast" | **NO.** Quality enforcement is non-negotiable. |

## Red Flags - STOP Immediately

If you catch yourself thinking any of these, STOP:

- "This is taking too long, let me skip ahead"
- "The user seems impatient, let me batch phases"
- "Tests can come after the feature works"
- "Linting is just style, not critical"
- "I'll generate all commit messages at the end"
- "The plan doesn't explicitly require tests"

**All of these = violation of superbuild protocol.**

## Quality Commands by Stack

**See `references/ENFORCEMENT-GUIDE.md`** for stack-specific commands (JS/TS, Python, Go, Rust).

## Summary: The Iron Rules

1. **No plan = No execution** - Exit if plan not provided
2. **One phase at a time** - Unless parallel phases (use sub-agents)
3. **All quality gates must pass** - No exceptions
4. **Update plan after EVERY phase** - Check off tasks, update status
5. **Generate commit message** - Never run git commands
6. **Explain functional testing** - Ask before writing scripts
7. **Full stop after phase** - Unless --build-all override
8. **Suggest compact** - Context management is critical

**Superbuild is rigid by design.** The enforcement protects code quality. Do not rationalize around it.
