---
name: navigator-role
description: Adversarial navigator pattern for driver agents doing work where mistakes compound silently. Use when restaging commits, extracting shared utilities, multi-file refactors, or staging selective hunks into bisectable commits.
install_source: official
install_method: download
skill_id: official_9OHw1Hrv
enabled_at: 1787231481368
version: 1.0.0
name_zh: ROLE代理
---

# Navigator Role — Adversarial Pair for Driver Agents

Use a navigator (adversarial second agent) when the driver is doing work where mistakes compound silently: commit restaging, behavioral extraction, multi-file refactors, or any task where a subtle regression won't cause a test failure but will ship broken semantics.

## When to Spawn a Navigator

- Restaging commits (fixup+rebase changes behavioral identity)
- Extracting shared utilities from duplicated code (lazy vs eager evaluation)
- Multi-file type signature changes (widening can silently drop constraints)
- Staging selective hunks into bisectable commits (import ordering, dependency graphs)

## Navigator's Job

The navigator does NOT confirm the driver's work is correct. The navigator finds where it ISN'T:

1. **Behavioral identity** — Does the refactored code do exactly what the original did? Watch for eager-to-lazy, null-at-creation, and import-ordering regressions.
2. **Staging completeness** — After fixup+autosquash, are all dependent changes in the right commit? A fix applied after initial staging can be missed.
3. **Spec AC gaps** — Does the implementation satisfy the acceptance criteria literally, not just in spirit? (e.g., "use the proper type" means the named type, not an inline structural equivalent)
4. **Cross-file consistency** — When a signature widens in file A, do all callers in files B, C, D pass the right shape?

## How to Use

Spawn as `crew-challenger` with adversarial instructions:

```
Your job is to find where the work DOESN'T match the plan — not to confirm it does.
Check: behavioral identity after extraction, staging completeness after rebase,
AC satisfaction (literal, not spirit), cross-file type consistency.
```

## Evidence

- **spec-002**: GoldHawk navigator caught pre-claim timing regression
- **spec-003**: QuickRaven caught FileReservation not staged after fixup-rebase (import was applied after initial staging, so fixup missed it)
- **spec-003**: QuickRaven caught stuck-timer eager taskId capture (lobby.assignedTaskId is null at creation — must use lazy getter)
- **spec-003**: QuickRaven caught skip comment missing "why" rationale (R8 AC said "and why", comment only had "what")
