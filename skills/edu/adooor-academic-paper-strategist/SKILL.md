---
name: academic-paper-strategist
description: Use when the user needs to plan, de-risk, or ground a software engineering / computer science undergraduate thesis from a real codebase before final writing. Trigger for requests such as "根据项目写毕业论文", "先做论文大纲", "用真实项目材料规划论文", "检查论文是否脱离代码", "根据检测报告降查重", "根据AIGC报告改写定稿", "继续在手改初稿上改", or when an existing draft thesis must be reworked against a school format sample. Produces an evidence-backed outline, chapter rewrite plan, figure plan, and handoff package for academic-paper-composer.
install_source: official
install_method: download
skill_id: official_zxK5ijm9
enabled_at: 1787232084092
version: 1.0.0
name_zh: 论文Academic
---

# Academic Paper Strategist

## Overview

This is the planning skill for Codex-based software engineering theses. Use it before drafting or finalizing a thesis from a real repository. Its job is to reduce hallucination risk, map project evidence to chapters, and define only the claims, figures, tables, and tests that can be justified by the actual codebase and supplied school format sample.

**Companion flow**:
1. `academic-paper-strategist` - planning, evidence mapping, rewrite scope
2. `academic-paper-composer` - content rewrite and final manuscript assembly
3. `drawio` - redraw engineering-style thesis figures when required
4. `playwright` - capture real runtime screenshots when the thesis needs running-system evidence
5. `doc` - produce and visually check the final DOCX

Do not skip the strategist step when the user asks for a submission-ready undergraduate thesis from an existing project and draft.

## Core Rules

- Read project evidence before outlining. Prefer repository files, SQL, config, docs, controllers, services, entities, and the existing draft.
- Treat the existing draft as untrusted input. Keep only what can be supported by project evidence.
- If the user has already hand-edited part of a draft, treat that working draft as a protected artifact and plan around it instead of blindly replacing the whole manuscript.
- If the user provides plagiarism, similarity, or AIGC detection reports, treat them as rewrite-priority signals, not as sources of truth about the project. Load `references/detection-report-rewrite-playbook.md` when this applies.
- If the user provides a school format sample, load `references/zjkj-undergrad-thesis-format.md` first and treat it as the highest authority for structure and formatting.
- If the task is to produce a final thesis from an existing draft, also load:
  - `references/project-grounding-rules.md`
  - `references/finalization-task-rules.md`
- Load `references/draft-salvage-handoff-playbook.md` when the user wants to continue a partially edited draft, keep original figures/tables, or add running-system screenshots.
- Never invent features, APIs, data tables, performance numbers, deployment scale, user scale, concurrency benchmarks, or test results.
- Reframe "innovation" conservatively as engineering highlights, implementation choices, integration value, or maintainability benefits.
- Only plan figures that are supported by code or project docs. Omit unsupported diagrams.
- Keep the thesis compatible with an automatic table of contents and school-required front matter.

## Inputs To Gather

- Repository root
- Existing draft thesis (`.docx`, `.md`, or both)
- School template or format sample (`.doc`, `.docx`, or `.pdf`)
- Core evidence files such as:
  - build file (`pom.xml`, `package.json`, etc.)
  - architecture docs
  - business logic docs
  - SQL schema / migration files
  - entities / DTOs / controllers / services
- Detection reports when available (`.pdf`, `.docx`, screenshots, extracted text)
- Required deliverable path(s)

## Workflow

### Step 1: Ingest Constraints

Record:
- target school and thesis type
- final deliverable format
- whether the task is planning only or full finalization
- whether the task must continue from a hand-edited working draft
- whether the user wants original figures/tables preserved
- whether real running screenshots are required
- required output paths

If the user gives explicit source and destination paths, treat them as binding.

### Step 2: Load School Format Authority

When a school sample is present, read `references/zjkj-undergrad-thesis-format.md` and extract:
- required front-matter order
- heading hierarchy
- body typography and spacing
- figure and table caption rules
- reference formatting
- appendix and acknowledgement rules
- any page-numbering constraints visible in the sample

If the sample contains instructional text boxes or placeholder hints, mark them as "remove from final manuscript".

### Step 3: Audit The Existing Draft

Classify each section into:
- keep with minor edits
- keep but downgrade claims
- rewrite from project evidence
- delete entirely
- preserve as a legacy asset and restore if lost later

Always flag for removal:
- process notes
- template prompts
- instructional text boxes
- unsupported novelty claims
- unsupported metrics or deployment claims
- colored headings or hyperlink-styled text
- diagrams that do not match engineering-paper style

Also mark:
- original E-R figures the user wants to keep
- original database per-table field-description blocks
- user manual edits that must not be overwritten
- sections where only a partial range should be replaced

### Step 3A: Triage Detection Reports When Present

When the user asks to lower similarity or AIGC risk and provides reports, read `references/detection-report-rewrite-playbook.md`.

At this stage, the strategist should:
- extract the headline score and hotspot pages
- map hotspots back to thesis sections
- classify causes and rewrite intensity
- tell the composer where to perform heavy structural rewrites versus light cleanup

### Step 4: Build An Evidence Map

For each chapter, map every major claim to repo evidence:
- **Background / system positioning** -> docs and project summary
- **Architecture** -> package structure, config, controllers, services
- **Database design** -> SQL schema and entities
- **Business workflows** -> controllers, services, docs
- **Security / consistency mechanisms** -> config, service logic, transactional code, locking, signatures, validation
- **Testing chapter** -> only real screenshots, test classes, manual verification records, or observable system behavior

If a claim cannot be mapped to an evidence source, it cannot appear in the final thesis.

### Step 5: Produce The Thesis Plan

Output a handoff package for the composer containing:
- cleaned chapter outline
- per-chapter evidence sources
- claims allowed
- claims forbidden
- figures to redraw
- legacy figures/tables to retain or restore
- exact section ranges to replace if the user only wants partial rewriting
- risky items requiring manual verification
- runtime screenshot capture plan when screenshots are needed
- when detection reports exist: a page-to-section rewrite matrix and a rewrite-priority list

When the handoff will drive a live DOCX revision, make it explicit enough that the composer can execute without re-deciding replacement boundaries, preserve lists, or screenshot targets.

The outline should normally include:
- cover / declarations / abstracts / TOC
- chapter 1 introduction
- chapter 2 requirements analysis
- chapter 3 overall design
- chapter 4 detailed implementation
- chapter 5 testing
- chapter 6 conclusion
- references
- acknowledgements
- appendices if needed

### Step 6: Produce A Figure And Screenshot Plan

Only the following figure types are allowed when the user asks for a software engineering undergraduate thesis:
- system architecture diagram
- functional module diagram
- business process diagram
- sequence diagram
- E-R diagram
- use case diagram
- real running-system screenshots tied to actual thesis sections

For every planned figure or screenshot, define:
- chapter placement
- source basis in code/docs/runtime
- labels that must appear
- labels or components that must not appear
- whether an old figure can be retained or must be redrawn
- whether the screenshot needs seeded demo data first

All redrawn figures must use engineering-paper visual style:
- white background
- black or gray lines
- no decorative icons
- no infographic styling
- no color-dependent meaning

## Existing-Draft Rework Mode

When the user asks for a final thesis from an existing draft:
- do not start from a blank paper unless the draft is unusable
- identify what to preserve and what to rewrite
- create a section-by-section rewrite brief for `academic-paper-composer`
- explicitly note any unsupported content that must be deleted rather than softened
- require the composer to operate on a copied draft or user-designated working draft, never the wrong file

When the user specifically asks to continue on a hand-edited draft:
- record the working draft path and the protected backup/original path separately
- plan replacement anchors by body heading style only
- forbid TOC-based anchor matching in the handoff
- identify which old figures/tables must survive the rewrite

When the user specifically asks to lower similarity or AIGC:
- identify the smallest set of sections that dominates the score
- prioritize Chinese narrative paragraphs over low-yield formal sections
- prefer a few high-impact structural rewrites over broad shallow edits
- use the rewrite modes defined in `references/detection-report-rewrite-playbook.md`

## References To Load As Needed

- `references/zjkj-undergrad-thesis-format.md` - school format authority
- `references/project-grounding-rules.md` - anti-fabrication and evidence rules
- `references/finalization-task-rules.md` - mandatory workflow for final DOCX delivery
- `references/detection-report-rewrite-playbook.md` - how to triage plagiarism / AIGC reports into a rewrite brief
- `references/draft-salvage-handoff-playbook.md` - how to plan partial replacement, legacy-asset retention, and runtime screenshots
- `references/chinese-call-prompt-templates.md` - copy-paste Chinese prompts for planning and handoff tasks

## Example Prompts

- `根据当前仓库和学校模板，先给我做一个本科论文定稿规划，只保留代码里能证实的内容。`
- `我已经手改初稿到正文 2.3 前了，帮我做 keep/rewrite/delete 矩阵，要求保留原数据库 E-R 图和每张表的字段说明。`
- `这是查重报告和 AIGC 报告，先别直接改正文，先把热点页映射到章节并给出重写优先级。`
- `继续在我现在的 working draft 上做规划，只替换 2.4 之后的正文内容，前面手改部分不要动。`
- `帮我给论文补一个运行截图规划，说明每张截图对应哪个角色、哪个页面、哪个章节。`

## Output Expectations

Produce:
- a thesis outline with up to 3 heading levels
- a chapter-by-chapter evidence map
- a keep / rewrite / delete matrix for the current draft
- a figure/table/screenshot rebuild plan
- a list of unsupported claims to remove
- a handoff package for `academic-paper-composer`
- when reports are supplied: a detection-report triage summary with hotspot pages, mapped sections, and recommended rewrite intensity

Do not claim that the paper is submission-ready at this stage. That decision belongs to the composer + drawio + playwright + doc flow.
