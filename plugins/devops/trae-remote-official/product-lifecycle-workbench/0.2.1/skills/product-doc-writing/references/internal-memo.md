---
name: internal-memo
description: >
  Sub-Skill for internal memo and brief writing — decision memos, executive
  briefs, team announcements, meeting summaries, and status updates. Inherits
  all constraints from doc-writing-guide-v2; adds memo-specific workflows,
  audience-targeted templates, action-oriented structures, evidence
  annotation, and quality gates calibrated to internal-communication standards.
---

# Internal Memo

## 0. Relationship to Parent

This Skill inherits **all** constraints from `doc-writing-guide-v2`:

- Intent interpretation (SS1): purpose, audience, tone, scope, and constraint analysis.
- Genre & format selection (SS2): internal memos map to the "Internal Memo / Brief" genre row — direct, action-oriented, audience-aware.
- Language to avoid (SS3): no checklist-jargon, no empty superlatives, no formulaic stubs, no bureaucratic filler.
- Content structure principles (SS4): substance over format, no pre-imposed rigid outlines.
- Visual generation guide (SS5): charts and diagrams follow parent rules.
- Citation: internal memos do NOT require inline citations unless referencing external data; proprietary data must be marked `[Internal data]`. Claims drawn from user-provided context or internal dashboards are tagged at the evidence level (§7), not with formal citations.

Anything defined below **extends** the parent; it never overrides.

---

## 1. Core Principles

1. **Bottom Line Up Front (BLUF).** The first sentence states the decision requested, the key finding, or the action required — before any background. A reader who stops after paragraph one must already know what is being asked and why.
2. **Audience determines depth, not importance.** An executive needs the decision and risk in three sentences; a working team needs the rationale, dependencies, and edge cases. Calibrate paragraph density, jargon tolerance, and structural formality to the specific reader — never write one memo for "everyone."
3. **Every section ends with an action or decision.** Background without a trailing action is noise. Each section closes with a named owner, a decision point, or an explicit "no action required — informational" tag so readers can stop reading once they have what they need.
4. **Separate verified fact from recommendation.** What happened (data, events, prior decisions) stays distinct from what should happen (proposals, forecasts, judgments). Never let a recommendation ride on the coattails of an unverified fact — tag the evidence boundary (§7) so the reader can weigh each claim independently.
5. **Do not fabricate internal data, decisions, or people.** Metrics, attendance, prior approvals, org-chart relationships, and timeline commitments the user has not provided must be marked `[Internal data — to be confirmed]` or elicited (§4). Inventing internal facts is a trust-destroying error, not a convenience.

---

## 2. Workflow Overview

Execute the following steps in order:

```
Step 1: Requirement Recognition → §3 (classify across 5 dimensions)
Step 2: First-Round Value Delivery → §4 (BLUF statement, audience map, structure, action-owner list)
Step 3: Structure Selection → §5 (match memo type to canonical structure)
Step 4: Memo Drafting → §6 (modular sections, action-oriented)
Step 5: Evidence Annotation & Verification → §7 (tag claims, mark internal data)
Step 6: Quality Self-Check → §8 (verify 12 items, annotate remaining gaps)
```

---

## 3. Requirement Recognition (Five Dimensions)

On receiving a memo or brief request, classify the input across these five dimensions before proceeding:

| Dimension | Classification Options |
|-----------|------------------------|
| **Memo type** | Decision memo / Executive brief / Status update / Meeting summary / Team announcement |
| **Audience** | Executive / Cross-functional team / Direct team / Whole org / Single stakeholder |
| **Decision urgency** | Decision needed now (blocking) / Decision needed this week / Informational (no decision) |
| **Length** | Short (≤ 1 page) / Medium (1–3 pages) / Long (3+ pages, multi-section) |
| **Evidence basis** | Internal data provided / Needs data gathering / Expert judgment only / Mixed |

**Execution rule:** Present classification as a brief table to the user. Confirm correctness before proceeding. If a dimension is ambiguous, state the inference rationale and ask the user to confirm or correct.

---

## 4. First-Round Value Delivery

The first round of interaction delivers four artifacts that make the memo's intent legible before any body prose is written:

| Artifact | Purpose | Content |
|----------|---------|---------|
| **BLUF statement** | Anchor the entire memo | One sentence stating the decision requested or the key finding; what the reader must do after reading; the deadline if applicable |
| **Audience map** | Calibrate depth and tone | Primary reader(s), their decision authority, what they already know, what they need from this memo, reading time budget |
| **Structure outline** | Give shape to the argument | Section list, each with its one-line purpose — not just a topic label; marked with which sections are "action" vs "informational" |
| **Action-owner list** | Pre-register every commitment | Every action item with a named owner and due date; decisions to be made with the decision-maker named; explicitly "no action" items flagged |

**Execution rule:** Deliver all four in the first round. Do not begin body drafting until the BLUF statement is confirmed and the audience map is locked. Drafting the body before the BLUF and audience are fixed is a documented failure mode (see §8, item 10).

---

## 5. Structure Selection Matrix

Match the memo type to its canonical structure. These are starting points — adapt to the organization's conventions and the reader's expectations.

| Memo Type | Canonical Structure | Key Structural Rule |
|-----------|---------------------|---------------------|
| **Decision memo** | BLUF → Recommendation → Rationale → Alternatives considered → Risks → Decision requested | Present the recommendation before the rationale; the reader must see the ask before the reasoning |
| **Executive brief** | BLUF → Key findings (3–5 bullets) → Implications → Recommended actions → Next steps | Keep to one page; every section earns its place by serving the executive's decision |
| **Status update** | BLUF (on-track / at-risk / off-track) → Progress this period → Blockers → Next period plan → Asks | Lead with the traffic-light status; detail follows only if the reader opts in |
| **Meeting summary** | BLUF (key decisions) → Attendees → Decisions made → Action items (owner + due) → Open questions | Decisions and action items come before narrative; the summary is a record of commitments, not a transcript |
| **Team announcement** | BLUF (what is changing) → What this means for you → Timeline → What stays the same → Where to get help | Answer "how does this affect me" by the second section; reassurance about what is NOT changing reduces anxiety |

**Routing rule:** Match the user's memo type to the closest row. If the request spans types (e.g., "decision memo with a status-update section"), merge structural rules, keeping the primary type's section ordering.

---

## 6. Modular Template

Generate the memo using these modules. Select, expand, or omit modules based on the memo type and audience — do not blindly include everything.

> **Default length is Medium (1–3 pages).** Unless the request clearly matches Short or Long criteria, generate at Medium length.

### 6.1 Core Modules (always present)

**Module 1: BLUF & Header**
- Memo metadata: To / From / Date / Subject (or Re:)
- The BLUF statement: decision requested or key finding in one sentence
- Audience cue: a one-line note on who should read which sections
- Evidence annotation: the BLUF claim tagged `[Data-backed]` or `[Expert judgment]` — never presented as self-evident

**Module 2: Context / Background**
- Why this memo exists now (trigger event, prior decision, new data)
- Only the context the reader does not already have — skip shared history
- Evidence annotation: factual claims tagged `[Internal data]` or `[Data-backed]`; interpretive framing tagged `[Expert judgment]`

**Module 3: Findings or Recommendation**
- For decision memos: the recommended option with one-paragraph justification
- For briefs: 3–5 key findings, each with its evidence basis
- For status updates: progress, blockers, and status verdict
- Evidence annotation: recommendations tagged `[Expert judgment]`; supporting metrics tagged `[Data-backed]` or `[Internal data]`

**Module 4: Action Items & Decisions Requested**
- Named owner + due date for every action
- Decision requested: who decides, by when, what happens if no decision
- Explicit "no action required — informational" tag when applicable
- Evidence annotation: commitments tagged `[Internal data — to be confirmed]` until the owner acknowledges

### 6.2 Scenario-Triggered Modules

| Trigger | Module | Content |
|---------|--------|---------|
| Decision memo | Alternatives & trade-offs | Options considered, why rejected, residual risks of the recommended path |
| Executive brief | Implications | What the findings mean for strategy, budget, or roadmap; tagged `[Expert judgment]` |
| Status update | Risk & mitigation | Blockers with named owners and mitigation steps; escalation path if unresolved |
| Meeting summary | Open questions | Unresolved items parked for the next meeting with a named owner to follow up |
| Team announcement | Change scope & timeline | What changes, when it takes effect, what does NOT change, transition support |
| Cross-functional memo | Dependencies & handoffs | Upstream inputs needed, downstream teams affected, integration points |

---

## 7. Evidence Annotation & Verification Boundary

Every claim in the memo carries an evidence tag. This is the verification boundary — it prevents internal assertions from being presented as established fact without a traceable basis.

| Tag | Meaning | Typical Use |
|-----|---------|-------------|
| `[Data-backed]` | Supported by data the user provided or the analysis produced | Measured metrics, observed counts, tracked outcomes |
| `[Research-backed]` | Supported by a cited external source | Industry benchmarks, regulatory references, published studies |
| `[Expert judgment]` | Reasoned inference by the author or named domain expert | Recommendations, risk assessments, prioritization rationale |
| `[Hypothesis]` | Tentative claim awaiting evidence or confirmation | Forecasts, predicted outcomes, untested assumptions |
| `[Internal data]` | Drawn from internal systems, dashboards, or prior decisions — not for external citation | Proprietary metrics, internal attendance, prior approval records |

**Verification rules:**

1. Do not present an `[Internal data]` or `[Hypothesis]` claim as established fact. Keep provisional phrasing (e.g., "internal dashboards indicate…") until the source is confirmed.
2. Do not mix verified facts with recommendations in the same paragraph without a visible tag boundary. The reader must be able to weigh the evidence and the proposal independently.
3. When internal data is unavailable, mark the claim `[Internal data — to be confirmed]` and add it to the action-owner list (§4) for follow-up. Do not substitute a fabricated number.
4. External citations (regulations, benchmarks) follow parent SS5 citation rules — include the source inline only when the memo references external evidence.

---

## 8. Quality Self-Check

After generation, verify every item internally. If any item does not pass, revise until it passes. Do NOT include the self-check in the final deliverable — this is internal quality assurance only.

### Detailed Checklist (12 Items)

| # | Check Item | Pass Criteria |
|---|-----------|---------------|
| 1 | **BLUF is present and first** | The first substantive sentence states the decision, finding, or action — before any background |
| 2 | **Audience is calibrated** | Depth, jargon, and formality match the named reader; a one-size memo for "everyone" is not accepted |
| 3 | **Every section ends with action or decision** | Each section closes with a named owner, a decision point, or an explicit "no action — informational" tag |
| 4 | **Facts and recommendations are separated** | What happened is distinct from what should happen; no recommendation rides on an unverified fact without a tag boundary |
| 5 | **Action items have owners and dates** | Every action item names an owner and a due date; decisions requested name the decision-maker and deadline |
| 6 | **Evidence tags are present** | Every claim carries `[Data-backed]` / `[Research-backed]` / `[Expert judgment]` / `[Hypothesis]` / `[Internal data]`; no claim is untagged |
| 7 | **Internal data is marked, not fabricated** | Proprietary metrics, attendance, prior decisions are tagged `[Internal data]` or `[Internal data — to be confirmed]`; no invented internal facts |
| 8 | **Structure matches memo type** | The section order follows the §5 matrix for the identified memo type; the recommendation precedes the rationale in decision memos |
| 9 | **Length matches need** | Short request is not padded to 3 pages; complex decision is not compressed to a single paragraph |
| 10 | **Body not drafted before BLUF locked** | No section body was written before the BLUF statement and audience map were confirmed |
| 11 | **Alternatives are documented (decision memos)** | Decision memos include options considered and why rejected — not just the recommended path |
| 12 | **No hallucination** | No fabricated metrics, attendance, prior approvals, org relationships, or timeline commitments; unverifiable claims are tagged, not invented |

---

## 9. Red-Line Rules

1. **Do not bury the ask.** The decision requested or key finding appears in the first sentence — never after multiple paragraphs of context.
2. **Do not fabricate internal data or people.** Metrics, attendance, prior decisions, org-chart relationships, and commitments the user has not provided must be marked `[Internal data — to be confirmed]` or elicited. Inventing internal facts destroys trust.
3. **Do not present a recommendation as fact.** Recommendations carry `[Expert judgment]`; supporting evidence carries its own tag. The reader must be able to accept the evidence while rejecting the recommendation.
4. **Do not write action-free sections.** Every section ends with an action, a decision point, or an explicit "no action required" flag. Background without a trailing action is noise.
5. **Do not write one memo for everyone.** Audience determines depth. If the memo must reach multiple audiences with different needs, split into a primary memo and an appendix, or write separate memos.

---

## 10. Related Skills

| Skill | Relationship |
|-------|-------------|
| `research-guide` | Before writing a brief that cites external benchmarks or regulations, run source gathering to verify external claims |
| `prd-document` | If the memo references a product decision, route the detailed requirements separately to avoid overloading the memo with spec-level detail |
