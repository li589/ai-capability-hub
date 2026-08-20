# Git History Mining Reference

This file is used in the scaffold step (batch-launching git commands) and knowledge
extraction step (analyzing output in subagents).

## Why Git Mining Matters

Git history reveals knowledge that static code analysis cannot: implicit couplings between
files, bug patterns, migration context, and conventions. A knowledge tree without git-mined
insights is hollow — it contains only surface-level information.

## Knowledge Types from Git History

| Type | Signal | Entry pattern |
|------|--------|---------------|
| **Implicit coupling** | Files changing together | Modifying A usually requires updating B in sync |
| **Bug pattern** | "fix/resolve" in messages | `<error pattern>` causes `<problem>`, solved by `<approach>` |
| **Convention** | Consistent patterns | All X follow Y naming/structure convention |
| **Performance** | "optimize/perf" | `<optimization>` applied to `<component>` |
| **Security** | "security/auth" | `<security consideration>` in `<area>` |
| **Migration** | "refactor/migrate/deprecate" | Migrating from X to Y, new code should use Y |

## Batch Execution

Before launching subagents, batch-launch ALL git mining commands. Build a tracking checklist:

Git mining must respect Git ignore rules. Use only Git-visible source path inputs, and do
not pass ignored generated/vendor/build paths to the history script. The script filters
ignored files in diffs as a final guard, but command planning must still avoid ignored
locations.

```
=== Git Mining Checklist ===
[ ] domain-1 (top-level)   → output: <knowledges-root>/.knowledges-task/git/domain-1-history.md
[ ] domain-2 (top-level)   → output: <knowledges-root>/.knowledges-task/git/domain-2-history.md
[ ] component-1            → output: <knowledges-root>/.knowledges-task/git/component-1-history.md
[ ] crosscut-1             → output: <knowledges-root>/.knowledges-task/git/crosscut-1-history.md
...
Total: N nodes | Completed: 0/N
```

Command template:
```bash
python3 <skill-path>/scripts/git-agent-history.py \
  --since "60 days ago" --max-count 100 --max-lines-per-file 20 --show-line-numbers \
  <path/to/source/1> <path/to/source/2> \
  > <knowledges-root>/.knowledges-task/git/<slug>-history.md
```

- Launch multiple commands in parallel
- Adjust `--max-count` per domain size (50–200)
- Keep path inputs limited to Git-visible project files or directories
- Mark each item `[done]` after completion
- ALL items must be checked before proceeding to knowledge extraction

## Analysis Patterns

When reading a git history output file, apply these 5 patterns:

### Pattern A — Co-change Detection (→ coupling/dependency entries)

Scan for commits touching 2+ Git-visible files across different subdirectories. If files A
and B change together in 3+ commits, they have an implicit coupling worth recording.

Example: `commit:287a7a50` modified both `terminal-mirror/runner.tsx` and `chat-input/index.tsx`
→ Entry: `Modifying terminal mirror run state requires syncing chat input panel settings
  (terminal-mirror/runner.tsx, chat-input/index.tsx, git:287a7a5)`

### Pattern B — Bug Pattern Extraction (→ gotcha entries)

Look for commits containing fix/resolve/bugfix/hotfix. Read changed code to understand
what broke and why. These are high-value gotcha entries.

Example: `commit:e480106c fix: tracking event type mismatch`
→ Entry: `Tracking event parameters must match backend schema exactly — type mismatches
  are silently dropped, not rejected (src/tracking/events.ts, git:e480106)`

### Pattern C — Hotspot Files (→ gotcha/architecture entries)

If the same file appears in 3+ commits within the time window, it's a maintenance hotspot.
Read the diffs to understand why it keeps changing.

Example: `runner.tsx` appeared in 3 of 5 commits
→ Entry: `runner.tsx is a high-churn hotspot — terminal stop/output truncation logic is
  concentrated here, modifications require careful regression testing (src/runner.tsx, git:287a7a5)`

### Pattern D — Migration/Deprecation Signals (→ decision entries)

Look for commits containing refactor/migrate/deprecate/replace/new-approach. These reveal
active transitions and prevent the agent from using outdated patterns.

### Pattern E — Convention Signals (→ pattern/convention entries)

Look for patterns in file naming, directory structure, or code style consistently followed
across commits. These reveal unwritten rules.

## Reconcile & Distribute

After mining, reconcile with static analysis results:
- **Contradicts** static insight (e.g., pattern was deprecated) → keep the newest
- **Elaborates** existing insight → merge into one stronger statement
- **Redundant** → keep the better-written version
- **Net new** → add it

**Distribute to subdomains**: Check the file paths in each knowledge — if they fall entirely
within a subdomain's scope, assign there. Keep at the top level only if it spans multiple
subdomains or concerns overall architecture.
