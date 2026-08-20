---
name: evidence-guard
description: >
  Reduces agent hallucinations by enforcing evidence-based reasoning. Maintains an Evidence Ledger
  to track sources of factual claims. Forces clear distinction between verified facts, assumptions,
  and unverified content. Use when making architectural decisions, citing API/library capabilities,
  referencing file paths or configurations, or producing final reports.
description_zh: >
  通过强制基于证据的推理来降低 agent 幻觉。维护证据账本追踪事实来源。
  强制区分已验证事实、假设和未验证内容。在进行架构决策、引用 API/库能力、
  引用文件路径或配置、或输出最终报告时使用。
version: 1.0.0
user-invocable: false
---

# Evidence Guard

## Core Principle

Every factual claim must trace to a source. No source = assumption. Mark it explicitly.

**Priority**: Final quality > Correctness > Evidence grounding > Context optimization > Token saving.

## Evidence Ledger

Maintain an internal Evidence Ledger throughout the task. For each significant factual claim, record:

```
[CLAIM] → [SOURCE_TYPE: details] → [CONFIDENCE: verified|assumed|unverified]
```

### Source Types (valid evidence)

| Source Type | Examples | Confidence |
|---|---|---|
| `local-code` | File contents, grep results, LSP lookups | verified |
| `project-docs` | README, AGENTS.md, .qoder/ configs | verified |
| `official-docs` | WebFetch from official documentation sites | verified |
| `command-output` | Terminal command results, build logs, test output | verified |
| `test-result` | Test runner output, lint results | verified |
| `browser-check` | Browser screenshot, console output, DOM inspection | verified |
| `user-input` | User's explicit statements in conversation | verified |

### Invalid Evidence (never use these as facts)

- Model's internal knowledge without verification
- Assumed file paths that haven't been read
- Assumed API endpoints or configurations
- Remembered library capabilities without checking docs or code
- "Common knowledge" about frameworks without verification

## Workflow

### Step 1: Before Making Claims

Before stating any fact about the project, APIs, or capabilities:

1. **Local code?** → Use Read/Grep/Glob/LSP to verify
2. **Library capability?** → Check project dependencies (package.json, Cargo.toml, etc.), then check official docs if needed
3. **File exists?** → Use Glob or Read to confirm
4. **API/config works?** → Check source code or run a test

### Step 2: When Evidence Is Unavailable

If you cannot verify a claim:

```markdown
> **ASSUMPTION**: [claim here]
> Reason: [why you believe this but couldn't verify]
> Risk: [what could go wrong if wrong]
> How to verify: [what the user could do to confirm]
```

### Step 3: Final Report Structure

Every task completion must include a verification status section:

```markdown
## Verification Status

### Verified
- [x] [claim] — source: [file/command/doc]

### Unverified (assumptions)
- [ ] [claim] — reason: [why not verified]

### Remaining Risks
- [risk description and mitigation]
```

## Prohibited Behaviors

1. **Never fabricate file paths.** If you haven't confirmed a file exists via Glob/Read, don't reference it.
2. **Never fabricate API capabilities.** If you haven't checked docs or source, mark as assumption.
3. **Never fabricate test results.** Only report tests you actually ran.
4. **Never fabricate command output.** Only report commands you actually executed.
5. **Never present assumptions as facts.** Use explicit markers.
6. **Never invent configuration values.** Read them from actual config files.

## Third-Party Library Rules

Before using any third-party library API or feature:

1. Check if it's in the project's dependencies (package.json, requirements.txt, etc.)
2. If yes, check the installed version
3. Verify the API exists in official docs or source code
4. If the library is NOT in dependencies, tell the user they need to install it

## Evidence Compression

When the Evidence Ledger grows large, compress to structured summary:

```
## Evidence Summary
- Verified: [N] claims from [sources]
- Assumed: [N] claims requiring user confirmation
- Key risk: [highest-impact unverified claim]
```

Always retain: file paths, function names, version numbers, and source URLs.

## Integration with Other Skills

- **Context Cartographer**: Evidence Ledger references files discovered during context mapping
- **Verification Runner**: Test results feed into Evidence Ledger as `test-result` sources
- **UI Taste Guard**: Design system facts must be evidenced by reading actual component code

## Additional Resources

- For detailed examples and templates, see [evidence-ledger-examples.md](references/evidence-ledger-examples.md)
