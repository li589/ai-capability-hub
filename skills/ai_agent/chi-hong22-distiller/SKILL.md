---
install_source: official
install_method: download
skill_id: official_utMGWfid
enabled_at: 1785438819551
version: 1.0.0
name_zh: 文档知识蒸馏
---
---
name: distiller
description: Extract reusable knowledge from AI coding sessions into structured, Obsidian-compatible documents. Use whenever the user finishes a project, fixes a tricky bug, refactors code, explores a new framework, or simply feels a conversation was valuable. Trigger phrases include "distill", "extract knowledge", "summarize learnings", "retrospective", "what did I learn", "wrap up", "record this", or any hint that the user wants to convert ephemeral session experience into a lasting knowledge asset. Even if the user doesn't use these exact words — for instance, they say "I don't want to forget this" or "let's save what we learned" — this skill should activate. When in doubt, activate: undertriggering is worse than overtriggering because lost knowledge cannot be recovered.
---

<!--
Input: AI session content (current chat, today's transcripts, or specific files)
Output: Structured knowledge document (Obsidian-compatible .md) + updated .distiller/ memory
Pos: Experience extraction engine — transforms ephemeral AI sessions into compound knowledge assets (skills/distiller/)
-->

# Distiller

Transform one-off AI coding sessions into structured, reusable knowledge assets. Instead of "use once, forget once", extract underlying logic, reusable patterns, and pitfall guides — building compound interest on development experience.

## Why This Matters

Most valuable technical knowledge lives in conversations that get closed and forgotten. A debugging breakthrough at 2 AM, an architectural insight during pair programming, a hard-won understanding of a framework quirk — all gone the moment the chat window closes. Distiller exists because knowledge should compound, not evaporate.

## Core Principles

1. **Extract, don't interpret** — Faithfully capture what actually happened. Inventing rationale or over-generalizing beyond what the content supports produces unreliable notes that erode trust over time.
2. **Score by confidence** — Not all extractions are equal. Each point gets a confidence level (high/medium/low) so the user knows what to trust immediately vs. what needs verification.
3. **Scene-specific depth** — A bug retrospective needs root-cause chains; a project wrap-up needs architecture decision records. Generic "summarize everything" misses the dimensions that matter most in each context.
4. **User retains control** — AI proposes, user confirms. Every key decision (scene selection, storage location, create vs. append) requires explicit user approval because the user understands their knowledge base better than any model can.
5. **Zero external dependencies** — Pure skill, no CLI tools or package installs required. The search script (`scripts/search_distiller.py`) uses Python standard library only; if Python is unavailable, a built-in Grep fallback covers the same functionality.

## Resource Loading Strategy

This skill follows a three-level progressive disclosure model to stay lightweight:

| Level | What | When to Load |
| ----- | ---- | ------------ |
| **Always in context** | This SKILL.md body (~200 lines) | Automatically loaded on skill trigger |
| **Load on demand** | Scene template (`references/scene-*.md`) | Read only the ONE matched scene file during extraction (Phase 4.1) |
| **Load on demand** | `references/tags-taxonomy.md` | Read during extraction (Phase 4.1) to select proper tags |
| **Load on demand** | `assets/distiller-frontmatter.md` | Read during extraction (Phase 4.1) for the output skeleton |
| **Execute without loading** | `scripts/search_distiller.py` | Run as subprocess in Phase 3.2; if Python unavailable, use Grep fallback described in Phase 3.2 |

Only load what the current phase requires. Reading all reference files upfront wastes context.

## Workflow

The workflow has five phases. Each phase groups logically related actions.

### Phase 1: Setup

#### 1.1 Initialize Memory

Scan the project root for `.distiller/` directory. If it does not exist, create it:

```text
.distiller/
├── profile.json        → {}
├── history.jsonl       → (empty)
├── search-index.jsonl  → (empty)
└── index.md            → # Distilled Knowledge Index\n\n_No entries yet._
```

#### 1.2 Load Preferences

Read `.distiller/profile.json`. Stored values (preferred storage path, frequent tags, scene history) pre-fill later choices so returning users answer fewer questions. On first run, proceed with defaults.

#### 1.3 Resolve Interaction Language

Detect the user's language from their latest message:

- Contains Chinese characters → interact in Chinese
- Otherwise → interact in English

All user-facing prompts in subsequent phases MUST use this language.

### Phase 2: Scope & Scene

#### 2.1 Ask Scope

Ask the user which content to distill:

| Option | Description |
| ------ | ----------- |
| **Current chat** | Analyze this conversation only |
| **Today's all chats** | Scan `agent-transcripts/` for today's `.jsonl` files |
| **Specific files/dirs** | User provides file or directory paths |

#### 2.2 Analyze & Detect Scene

Read the scoped content and auto-detect the best-fit scene by matching content against signal patterns defined in each scene reference file:

| Scene | Reference File | Typical Signals |
| ----- | -------------- | --------------- |
| Project Wrap-up | `references/scene-project-wrapup.md` | Architecture decisions, module design, deployment, lessons learned |
| Bug Retrospective | `references/scene-bug-retrospective.md` | Error traces, debugging sessions, root cause analysis, fix verification |
| Code Refactoring | `references/scene-refactoring.md` | Code restructuring, design patterns, performance optimization |
| Tech Learning | `references/scene-tech-learning.md` | New framework/tool exploration, API discovery, concept learning |
| Universal | `references/scene-universal.md` | No scene exceeds threshold, or mixed content |

Select the scene with the highest match score. If none exceeds the threshold, fall back to Universal. Also detect the source language (en or zh) for the document body.

#### 2.3 Confirm Scene

Present the detected scene and confidence to the user. Ask them to confirm or override — they may know their intent better than signal matching can infer.

### Phase 3: Storage & Dedup

#### 3.1 Ask Storage Target

Ask the user where to save, pre-filling from `profile.json` if available:

| Option | Path |
| ------ | ---- |
| **Obsidian vault** | User specifies vault path |
| **Project local** | `docs/distiller/` in current project root |
| **Global knowledge base** | `~/.agents/distiller/` |

#### 3.2 Search Existing Docs

Search the chosen storage directory for documents with related topics or tags. This prevents knowledge fragmentation — related insights belong together.

**Primary method** — Run `scripts/search_distiller.py`:

```text
python scripts/search_distiller.py <keywords> --dir <storage_path> --distiller-dir <project_root>/.distiller
```

**Fallback** — If Python is unavailable (command fails or not installed), use the Grep tool directly:

1. Search for `distilled` tag in .md files: `Grep pattern="^  - distilled$" path=<storage_path> glob="*.md"`
2. Among matches, search for topic keywords: `Grep pattern="<keyword1>|<keyword2>" path=<storage_path> glob="*.md"`
3. If both match the same file, it is a related document

Present findings and offer:

- **Create new** — if no closely related docs found
- **Append to existing** — if a related doc exists (show filename and topic)

User confirms the choice.

### Phase 4: Extract & Review

#### 4.1 Extract

Now read the matched `references/scene-*.md` file. Follow its extraction dimensions, prompt template, and output structure. Apply confidence scoring to each extraction point:

- **high** — Explicitly stated in source, well-supported, directly actionable
- **medium** — Reasonably inferred from context, may need verification
- **low** — Weak signal, speculative, worth noting but needs validation

Format confidence inline: `**[high]** The race condition occurs because...`

**Language rule:** Frontmatter keys and values are always in English. Document body (section headers + content) follows the detected source language.

Use the frontmatter skeleton from `assets/distiller-frontmatter.md`. For tag selection, consult `references/tags-taxonomy.md`.

#### 4.2 User Review

Present the complete distilled document to the user. Ask them to confirm, revise specific sections, or request re-extraction with different parameters. The user's review is the most important quality gate — no document gets written without their approval.

### Phase 5: Persist

Once the user approves:

1. **Write the document** to the chosen path. Filename: `YYYY-MM-DD-<topic-slug>.md`
2. **Update `.distiller/profile.json`** — Increment scene frequency, update preferred storage, refresh frequent tags
3. **Append to `.distiller/history.jsonl`** — `{"date": "...", "scene": "...", "topic": "...", "tags": [...], "output_path": "...", "scope": "...", "lang": "..."}`
4. **Append to `.distiller/search-index.jsonl`** — `{"file": "...", "title": "...", "keywords": [...], "timestamp": "..."}`
5. **Regenerate `.distiller/index.md`** — Rebuild full index from `history.jsonl`, grouped by scene then date

## Output Specification

See `assets/distiller-frontmatter.md` for the complete frontmatter skeleton and field reference.

Key rules:

- All frontmatter fields and values in English (including `title`, `tags`, `aliases`)
- `tags` use hierarchical `/`-separated format per `references/tags-taxonomy.md`
- Base tag `distilled` always present
- Body language follows source (en or zh)
- Use `[[filename]]` wiki-links for cross-references between distilled docs
- Confidence shown inline per extraction point as `**[high]**`, `**[medium]**`, or `**[low]**`

### Example Output (Bug Retrospective, Chinese body)

```markdown
---
title: "Race Condition in Async Task Queue"
date: 2025-07-12
aliases:
  - "async queue deadlock"
  - "task scheduler race"
tags:
  - distilled
  - scene/bug-retrospective
  - tech/python
  - topic/concurrency
  - difficulty/advanced
scene: bug-retrospective
source_scope: current-chat
confidence_summary: high
lang: zh
---

## Bug 画像

**[high]** 在并发提交 >50 个任务时，队列偶发死锁。现象为 worker 线程全部阻塞在 `queue.get()`，CPU 降至 0%。

## 根因链

**[high]** 表面症状：任务不再被消费
→ 直接原因：`queue.put()` 在锁内调用
→ 底层原因：生产者持有 Lock A 的同时等待队列空间（需要 Lock B）
→ 根因：经典 AB-BA 死锁，两把锁的获取顺序不一致
```

## Quality Checks

When evaluating whether a distilled document meets quality standards, verify these points:

| Check | Pass Criteria |
| ----- | ------------- |
| Frontmatter completeness | All required fields present, all values in English |
| Tag compliance | Includes `distilled` + one `scene/*` + at least one `tech/*` + one `difficulty/*` |
| Confidence coverage | Every extraction point has an inline `**[high/medium/low]**` marker |
| Faithfulness | No claims that go beyond what the source content supports |
| Scene fit | Extraction dimensions match the declared scene template |
| Actionability | A developer reading this 6 months later can apply the knowledge without the original context |

These checks are useful both for the user reviewing a document (Phase 4.2) and for evaluating the skill itself during iteration. If setting up formal evaluation, place test prompts and assertions in `evals/evals.json` following the standard skill-creator schema.

## Resources

Loaded on demand — read only when the current phase requires them:

- `references/scene-project-wrapup.md` — Project wrap-up extraction template (read in Phase 4.1)
- `references/scene-bug-retrospective.md` — Bug retrospective extraction template (read in Phase 4.1)
- `references/scene-refactoring.md` — Code refactoring extraction template (read in Phase 4.1)
- `references/scene-tech-learning.md` — Tech learning extraction template (read in Phase 4.1)
- `references/scene-universal.md` — Universal extraction template, fallback (read in Phase 4.1)
- `references/tags-taxonomy.md` — Hierarchical tag taxonomy (read in Phase 4.1)
- `assets/distiller-frontmatter.md` — Obsidian-compatible frontmatter skeleton (read in Phase 4.1)
- `scripts/search_distiller.py` — Search existing distilled documents by keyword/tag (execute in Phase 3.2)
