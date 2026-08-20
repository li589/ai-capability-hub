---
name: context-cartographer
description: >
  Optimizes context quality by building lightweight repo maps, targeted file reading, and
  maintaining a Context Ledger. Not about blindly saving tokens — about keeping context
  relevant and structured. Use at task start for codebase exploration, when reading multiple
  files, or when context length grows large.
description_zh: >
  通过构建轻量 repo 地图、定向文件读取和维护上下文账本来优化上下文质量。
  不是盲目省 token，而是保持上下文相关性和结构化。在任务开始时用于代码库探索、
  读取多个文件时、或上下文变长时使用。
version: 1.0.0
user-invocable: false
---

# Context Cartographer

## Core Principle

**Search first, read second.** Never blindly read entire files. Know what you need before reading.

**Quality over quantity.** Context optimization means keeping the RIGHT information, not just LESS information. If understanding the project requires reading more files, do it — but explain why.

## Configuration Defaults

```yaml
maxContextFiles: 30          # Suggested max files to read; exceed with justification
maxFileReadLines: 200        # Single-file read threshold; prefer targeted segments
enableContextLedger: true    # Track what was read and why
enableTokenBudgetReport: false  # Output context usage report at task end
```

These are soft limits. Exceeding them is fine with a brief reason.

## Workflow

### Phase 1: Repo Map (Task Start)

Before deep-diving into code, build a lightweight mental map:

1. **Scan structure**: Use Glob to list key directories (src/, lib/, components/, etc.)
2. **Identify entry points**: Find main files (index.ts, App.tsx, main.py, etc.)
3. **Find config**: Locate package.json, tsconfig.json, or equivalent
4. **Map dependencies**: Quick scan of imports/exports in relevant areas

Output a brief Repo Map:

```
REPO MAP — [project-name]
─────────────────────────
Stack: [language, framework, key tools]
Entry: [main entry file]
Structure:
  src/
    components/  — UI components (N files)
    services/    — API calls (N files)
    store/       — State management (N files)
  tests/         — Test files (N files)
Key configs: [config files found]
Relevant to task: [directories most likely needed]
```

### Phase 2: Targeted Reading

When reading files, follow this priority:

1. **LSP first** — Use goToDefinition, findReferences, documentSymbol for navigation
2. **Grep for patterns** — Search for specific functions, imports, or patterns
3. **Read segments** — Read specific line ranges, not whole files
4. **Full read only when** — File is short (<100 lines) OR you need complete understanding

#### Reading Decision Tree

```
Need to understand a file?
├── File < 100 lines → Read whole file
├── File 100-500 lines → Read with line range targeting key sections
├── File > 500 lines → LSP documentSymbol first, then targeted reads
└── File > 1000 lines → Always use LSP + Grep, never full read
```

### Phase 3: Context Ledger

Maintain a running Context Ledger:

```
CONTEXT LEDGER
──────────────
File                          | Purpose           | Key Facts        | Relevance
──────────────────────────────┼───────────────────┼──────────────────┼──────────
src/components/Header.tsx     | Existing UI comp  | Uses shadcn/ui   | HIGH
src/lib/utils.ts              | Shared utilities  | cn() helper      | MEDIUM
package.json                  | Dependencies      | React 18, shadcn | HIGH
src/app/settings/page.tsx     | Target file       | Does not exist   | HIGH
```

### Phase 4: Context Compression

When context grows large, compress while preserving critical info:

**Always retain:**
- File paths (exact, not approximated)
- Function/component/class names
- Type signatures and interfaces
- Import relationships
- Constraints and business rules
- Evidence sources (from Evidence Guard)

**Can compress:**
- Full file contents → summary of exports and key logic
- Verbose code → pseudocode of algorithm
- Multiple similar files → pattern description + one example

**Compression format:**

```
## Context Summary (compressed at step N)
### Files Read: [count]
### Key Architecture:
- [pattern 1]: [file] → [summary]
- [pattern 2]: [file] → [summary]
### Critical Constraints:
- [constraint from file X]
- [constraint from file Y]
### Active Task Context:
- Currently working on: [file/function]
- Next step: [action]
```

## Exceeding Limits Protocol

When you need to read beyond `maxContextFiles` or `maxFileReadLines`:

1. **State why**: "Need to read 5 more files because [reason]"
2. **Assess impact**: "These files are [highly relevant / needed for X / etc.]"
3. **Compress old context**: Summarize earlier reads before adding new ones
4. **Continue**: Don't stop just because of limits — quality matters more

## Anti-Patterns (Don't Do This)

1. **Reading entire 2000-line files** when you only need one function
2. **Reading every file in a directory** without filtering
3. **Re-reading files already in context** without purpose
4. **Ignoring the Repo Map** and diving deep too early
5. **Cutting context short** when the task genuinely needs more info
6. **Compressing away file paths or function names**

## Integration

- **Evidence Guard**: Context Ledger entries link to Evidence Ledger claims
- **UI Taste Guard**: Design system files get HIGH relevance in Context Ledger
- **Verification Runner**: Test files discovered during mapping feed into verification plan

## Additional Resources

- For context mapping examples, see [context-mapping-examples.md](references/context-mapping-examples.md)
