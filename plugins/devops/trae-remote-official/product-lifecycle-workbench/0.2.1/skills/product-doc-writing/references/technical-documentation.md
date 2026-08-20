---
name: technical-documentation
description: >
  Sub-Skill for generating technical documentation and tutorial / how-to
  guides. Covers two sub-genres: formal institutional writing (notices,
  reports, plans) and structured user-facing documentation (manuals,
  handbooks, SOPs, guidelines, specifications, API guides, READMEs).
  Dynamically determines document type, register, task structure, and
  mandatory sections based on authority relationship, audience, and
  complexity. Inherits all constraints from doc-writing-guide-v2; adds
  documentation-specific workflows, templates, and quality gates.
---

# Technical Documentation

## 0. Relationship to Parent

This Skill inherits **all** constraints from `doc-writing-guide-v2`:

- Intent interpretation (SS1): purpose, audience, tone, scope, and constraint analysis.
- Genre & format selection (SS2): this scenario maps to the "Technical Documentation" and "Tutorial / How-to" genre rows in §2.1.
- Language to avoid (SS3): no checklist-jargon, no empty superlatives, no formulaic stubs.
- Content structure principles (SS4): substance over format, no pre-imposed rigid outlines.
- Visual generation guide (SS5): charts and diagrams follow parent rules.
- Citation: technical documentation is generally self-contained — do NOT add inline citations or a Sources/References section unless the user explicitly requests external evidence or regulatory basis lookup.
- Evidence boundary: do not fabricate document numbers, dates, department names, or legal/regulatory bases. Mark unverifiable regulatory citations as `[Unverified — requires human review]`.

Anything defined below **extends** the parent; it never overrides.

---

## 1. Core Principles

1. **Task-oriented, not system-oriented.** Organize documentation around what the reader wants to accomplish, not around how the system is internally structured. A manual section titled "Export your report" serves the user better than "Export module overview".
2. **Progressive disclosure.** Each task follows the arc: prerequisites → steps → expected result → troubleshooting. The reader should never encounter a step whose precondition was not stated earlier.
3. **Precision over eloquence.** Every instruction must be unambiguous and immediately actionable. If a reader could interpret a step in two ways, the step is incomplete — add the specific UI label, button name, or command.
4. **Separate procedure from reference.** Step-by-step flows must stay clean and linear. Push specifications, field tables, glossaries, and configuration reference material into dedicated reference sections that the procedure links to.
5. **One document, one core matter.** For formal institutional documents (notices, reports, requests), lead with purpose and basis, address a single core matter, and close with an explicit action, deadline, or handling requirement.

---

## 2. Workflow Overview

Execute the following steps in order:

```
Step 1: Requirement Recognition → §3 (classify across 5 dimensions)
Step 2: Structure Selection → §4 (match sub-genre to structure pattern)
Step 3: Modular Generation → §5 (select core + scenario-triggered modules)
Step 4: Evidence Annotation → §6 (tag every factual claim)
Step 5: Quality Self-Check → §7 (verify 12 items)
```

---

## 3. Requirement Recognition (Five Dimensions)

On receiving a documentation request, classify the input across these five dimensions before proceeding:

| Dimension | Classification Options |
|-----------|----------------------|
| **Document type** | Manual / Handbook / SOP / Tutorial / API guide / README / Specification / Guideline / Notice / Report / Plan / Meeting minutes |
| **Sub-genre** | Formal institutional writing (notices, reports, plans, requests) / Structured user-facing documentation (manuals, handbooks, SOPs, tutorials) |
| **Audience** | End user / System administrator / Developer / Operator / Reviewer / Superior (upward authority) / Subordinate (downward) / Peer / Public |
| **Authority relationship** | Upward (report to superiors) / Downward (instruct subordinates) / Peer (coordinate across units) / Public (external-facing notice) |
| **Complexity** | Quick reference (1–3 pages) / Standard manual (5–15 pages) / Comprehensive handbook (20+ pages) |

**Execution rule:** Present classification as a brief table to the user. Confirm correctness before proceeding. If uncertain about any dimension, state your inference rationale and ask the user to confirm or correct.

---

## 4. Structure Selection Matrix

Match the document type to its structure pattern. When multiple patterns apply, merge their mandatory sections.

| Document Type | Structure Pattern | Mandatory Elements |
|---------------|-------------------|--------------------|
| **Manual / Handbook** | Task-oriented sections: prerequisites → numbered imperative steps → expected result → troubleshooting | Task heading, prerequisites, numbered steps, expected outcome, troubleshooting tips |
| **Tutorial / How-to** | Progressive disclosure: learning goal → guided steps → practice → knowledge check | Learning objective, hands-on steps, worked example, verification checkpoint |
| **SOP** | Strict procedural flow with mandatory checkpoints and responsible parties | Purpose, scope, prerequisites, step-by-step procedure, checkpoints, responsible roles, exception handling |
| **API guide** | Endpoint reference + usage examples | Endpoint table, request/response schema, parameters, error codes, code samples |
| **Specification** | Structural definition with field-level detail | Overview, data model, field definitions, constraints, validation rules |
| **Notice / Report** | Purpose/basis → matter → request or decision | Document basis, core matter, action required, effective date, responsible party |
| **README** | Project orientation → setup → usage → contribution | Project summary, installation, quick start, configuration, contributing |

**Routing rule:** Match the user's document type to the closest row. If the request is ambiguous (e.g., "write a guide"), infer from the audience and authority relationship: developer-facing → API guide or README; operator-facing → SOP or manual; superior-facing → report or plan.

---

## 5. Modular Template

Generate the document using these modules. **Select, expand, or omit modules based on the structure selection result** — do not blindly include everything.

### 5.1 Core Modules (always present)

#### Module 1: Document Identity

- Document type and title
- Intended audience and authority relationship
- Scope: what this document covers and explicitly does not cover
- Effective date and version (for formal institutional documents, these are mandatory)
- Responsible party / owner

> For quick-reference documents (1–3 pages), collapse this module to a single title line with audience note. Do not force a full metadata block.

#### Module 2: Task-Oriented Procedure

This is the document's core. Organize by tasks the reader wants to accomplish, in the order they would encounter them.

Each task section contains:

1. **Task heading** — states the outcome the reader will achieve (e.g., "Create a new user account"), not the system component.
2. **Prerequisites** — permissions, prior steps, environment state, or materials required before starting.
3. **Numbered imperative steps** — each step begins with a verb ("Click...", "Enter...", "Run..."), uses consistent numbering, and references exact UI labels or commands.
4. **Expected result** — what the reader should observe after completing the steps, so they can self-verify without external help.
5. **Troubleshooting** — common failure modes and their fixes, linked from the step where the failure typically occurs.

> **Imperative step rule:** Every step must be actionable in isolation. A reader who jumps to step 4 must have enough context to perform it without reading steps 1–3 — the prerequisite section and step numbering carry the sequential dependency.

#### Module 3: Reference Material

- Field definition tables (name, type, length, required, validation rule)
- Terminology glossary — every domain-specific term defined on first use and listed here for lookup
- Configuration parameter reference
- Error code tables (for API guides)
- Specs and standards cross-reference (for specification documents)

> Keep reference material **separate** from procedure steps. The procedure links to reference entries by name; the reference section never contains step-by-step instructions.

### 5.2 Scenario-Triggered Modules (include when sub-genre matches)

#### Formal Institutional Module (notices, reports, plans, requests)

- **Basis and authority** — the policy, prior document, regulation, or factual ground that authorizes this document. Annotated with `[Research-backed]` if citing external regulation, `[Expert judgment]` if inferred from organizational convention.
- **Core matter** — the single subject this document addresses. One document, one matter; do not mix unrelated items.
- **Action, deadline, or handling requirement** — the explicit instruction closing the document: who must do what by when.
- **Mandatory metadata** — document number, issuing department, effective date, responsible party. Do not fabricate any of these; mark unknowns as `[To be confirmed]`.

#### Tutorial Module (how-to guides)

- **Learning objective** — what the reader will be able to do after completing the tutorial, stated as a concrete capability.
- **Guided example** — a worked walkthrough with real (or realistic placeholder) data, not abstract descriptions.
- **Practice checkpoint** — an exercise or verification step where the reader confirms they achieved the expected result.
- **Next steps** — links to related tasks or advanced tutorials.

#### SOP Module (operating procedures)

- **Purpose and scope** — why this procedure exists and where it applies.
- **Responsible roles** — who performs each step, who verifies, who approves. Use role names, not person names.
- **Mandatory checkpoints** — steps where a verification, sign-off, or system confirmation is required before proceeding.
- **Exception handling** — what to do when a step fails, including escalation path and rollback procedure.

---

## 6. Evidence Annotation System

Every factual claim in the document must be tagged so the reader (and reviewer) can distinguish verified facts from inferences. Use these four labels inline, immediately after the claim:

| Label | Meaning | Example Usage |
|-------|---------|---------------|
| `[Data-backed]` | Supported by quantitative data the user provided or that is publicly verifiable | "The system processes 10,000 requests per second `[Data-backed]`" |
| `[Research-backed]` | Supported by external research, regulation, or standard that was looked up | "GDPR Article 22 requires..." `[Research-backed]`" |
| `[Expert judgment]` | Inferred from domain expertise or organizational convention, not independently verified | "This field should be marked required `[Expert judgment]`" |
| `[Hypothesis]` | An assumption made to fill an information gap; must be confirmed before publication | "Users typically access this feature weekly `[Hypothesis]`" |

**Rules:**
- Never present a `[Hypothesis]` or `[Expert judgment]` claim as established fact.
- When a claim's evidence tier is unclear, default to `[Hypothesis]` and flag it for user confirmation.
- Regulatory or legal citations must be `[Research-backed]` with the source named, or marked `[Unverified — requires human review]` if the source could not be confirmed.

---

## 7. Quality Self-Check

After generation, verify every item internally. If any item does not pass, revise the document until it passes. Do NOT include the self-check table or results in the final deliverable — this checklist is for internal quality assurance only.

| # | Check Item | Pass Criteria |
|---|-----------|---------------|
| 1 | **Organization is task-oriented** | Sections are organized around reader tasks, not system components — no "Module Overview" headings where a task heading would serve the user |
| 2 | **Steps are actionable** | Every step begins with an imperative verb and references exact UI labels, commands, or field names — no vague wording like "configure the settings" |
| 3 | **Prerequisites are stated** | Every task section lists what the reader needs before starting — permissions, prior steps, environment state |
| 4 | **Expected results are defined** | Every procedure states what the reader should observe upon completion, enabling self-verification |
| 5 | **Troubleshooting is covered** | Common failure modes for each task are documented with specific fixes, not generic "contact support" |
| 6 | **Procedure and reference are separated** | Step-by-step flows contain no embedded specification tables; reference material lives in its own section |
| 7 | **Terminology is consistent** | The same term is used for the same concept throughout; every domain term is defined on first use |
| 8 | **Mandatory sections are present** | For formal institutional documents: basis, scope, effective date, responsible party are all present — none fabricated |
| 9 | **Register is consistent** | No mixing of formal institutional register with casual or marketing tone within the same document |
| 10 | **No fabricated identifiers** | Document numbers, dates, department names, and legal bases are either user-provided or marked `[To be confirmed]` — never invented |
| 11 | **Evidence tags are applied** | Every factual claim carries one of `[Data-backed]`, `[Research-backed]`, `[Expert judgment]`, or `[Hypothesis]`; no untagged assertions of fact |
| 12 | **Depth matches complexity** | A quick-reference card is not 20 pages; a comprehensive handbook is not a single page — depth aligns with the complexity tier from §3 |

---

## 8. Red-Line Rules

1. **Do not fabricate institutional facts.** Document numbers, dates, department names, legal bases, and regulatory citations must come from the user or verifiable sources. Unknowns are marked `[To be confirmed]` or `[Unverified — requires human review]`.
2. **Do not write from the system's perspective.** Documentation serves the reader's task, not the system's architecture. "The export module processes the request" is wrong; "Click Export to download your report" is right.
3. **Do not mix registers.** A formal notice stays formal throughout; a tutorial stays instructional. Switching tone mid-document breaks reader trust.
4. **Do not present hypotheses as facts.** Any inferred content must carry the appropriate evidence tag and be flagged for confirmation.
5. **Do not omit mandatory sections to save space.** If the sub-genre requires a basis, scope, effective date, or responsible party, include it — even if briefly. A missing mandatory section is a compliance gap, not a concision win.
