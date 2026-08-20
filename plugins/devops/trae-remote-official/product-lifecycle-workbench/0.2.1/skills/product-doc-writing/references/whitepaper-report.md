---
name: whitepaper-report
description: >
  Sub-Skill for whitepapers and industry reports — trend analyses, market
  research, and strategic industry briefings. Inherits all constraints from
  doc-writing-guide-v2; adds report-specific workflows, chart and data-slot
  checklists, executive-summary framing, per-chapter evidence placeholders,
  and quality gates calibrated to board-level and operational decision-making.
---

# Whitepaper & Industry Report

## 0. Relationship to Parent

This Skill inherits **all** constraints from `doc-writing-guide-v2`:

- Intent interpretation (SS1): purpose, audience, tone, scope, and constraint analysis.
- Genre & format selection (SS2): whitepaper/report maps to the structured-report lineage — it draws on the evidence-based rigor of the "Academic / Research Paper" genre row for its research sections and the direct, decision-oriented register of "Internal Memo / Brief" for its recommendations.
- Language to avoid (SS3): no checklist-jargon, no empty superlatives, no formulaic stubs, no trend rhetoric without evidence.
- Content structure principles (SS4): substance over format, no pre-imposed rigid outlines.
- Visual generation guide (SS5): charts and diagrams follow parent rules.
- Citation: market data, statistics, and third-party findings require inline source attribution. Reusable framework recommendations (the report's own analysis) are distinguished from current market facts. Unverifiable market claims are flagged for external verification, never presented as confirmed.

Anything defined below **extends** the parent; it never overrides.

---

## 1. Core Principles

1. **Frame the market problem first.** The report opens by defining the market or industry problem, its time window, its readers, and the decision scenario it serves. A whitepaper that begins with trends before establishing why the reader should care has lost its audience.
2. **Separate judgment from evidence from recommendation.** Trend judgments, the evidence supporting them, the cases illustrating them, and the recommendations flowing from them occupy distinct roles. Mixing market facts, opinions, and strategy in the same section forces the reader to disentangle what is observed from what is advised.
3. **Each chapter answers one question.** Every chapter resolves a single board-level or operational-level question. A chapter that addresses multiple questions has no verifiable claim to completeness on any of them.
4. **Shape the executive summary early, not at the end.** The executive summary is the report's spine — its angle is defined when the outline is locked, not bolted on after the body is written. Deferring it to the end produces a summary that paraphrases rather than frames.
5. **Name observable evidence for every trend.** Trend rhetoric without observable evidence is opinion dressed as analysis. Every trend judgment points to the data, case, or market signal that makes it visible.

---

## 2. Workflow Overview

Execute the following steps in order:

```
Step 1: Requirement Recognition → §3 (classify across 5 dimensions)
Step 2: First-Round Value Delivery → §4 (outline, chart/data-slot checklist, conclusion hypotheses, executive-summary angle, per-chapter evidence placeholders)
Step 3: Structure Selection → §5 (match report type to structure)
Step 4: Chapter Drafting → §6 (one question per chapter, evidence-annotated)
Step 5: Evidence Annotation & Verification Boundary → §7 (tag claims, separate facts from frameworks, mark external-verification needs)
Step 6: Quality Self-Check → §8 (verify 12 items, annotate remaining gaps)
```

---

## 3. Requirement Recognition (Five Dimensions)

On receiving a whitepaper or industry report request, classify the input across these five dimensions before proceeding:

| Dimension | Classification Options |
|-----------|------------------------|
| **Document type** | Strategic whitepaper / Industry report / Trend analysis / Market research / Competitive landscape |
| **Audience** | Board-level executives / Operational leaders / Industry analysts / Investors / General professional readers |
| **Evidence base** | User-provided data & material / Needs external market research / Mixed (some provided, some to gather) |
| **Time horizon** | Current-state snapshot / 1-year outlook / Multi-year trend (3–5 years) |
| **Decision orientation** | Strategic recommendations / Reusable framework delivery / Trend briefing / Investment thesis |

**Execution rule:** Present classification as a brief table to the user. Confirm correctness before proceeding. If a dimension is ambiguous, state the inference rationale and ask the user to confirm or correct.

---

## 4. First-Round Value Delivery

The first round delivers five artifacts that make the report's skeleton legible before any body prose is written:

| Artifact | Purpose | Content |
|----------|---------|---------|
| **Structured outline** | Give structure to the analysis | Chapter list, each phrased as the board-level or operational question it answers — not a topic label |
| **Executive-summary angle** | Define the report's spine early | The one-sentence core trend judgment; the 3–5 questions the report will answer; the reader's decision scenario |
| **Chart and data-slot checklist** | Plan evidence before drafting | Per chapter: what chart or data point would prove the trend; marked as available, needs-research, or placeholder |
| **Conclusion hypotheses** | State where the analysis will land | Tentative conclusion per chapter, tagged `[Hypothesis]` until evidence is gathered |
| **Per-chapter evidence-placeholder checklist** | Track what each chapter needs | For each chapter: facts derivable from user material vs. facts needing external verification |

**Execution rule:** Deliver all five in the first round. The executive summary angle is defined here, not deferred to the end. Do not begin body expansion until the outline's questions and the chart/data-slot checklist are confirmed.

---

## 5. Structure Selection Matrix

Match the report type to its canonical structure. These are starting points — adapt to the audience and the analysis's needs.

| Report Type | Canonical Structure | Key Structural Rule |
|-------------|--------------------|--------------------|
| **Strategic whitepaper** | Market problem → Trend judgments → Evidence & cases → Framework → Recommendations | Separate trend judgments, evidence, cases, and recommendations into distinct sections |
| **Industry report** | Industry overview → Market size & segments → Competitive landscape → Trends & drivers → Outlook | Each chapter answers one board-level question; market facts distinguished from outlook opinions |
| **Trend analysis** | Trend identification → Observable evidence → Drivers & inhibitors → Implications → Outlook | Every trend judgment names the observable evidence that makes it visible |
| **Market research** | Market definition → Sizing & segmentation → Demand analysis → Competitive analysis → Entry/positioning | Quantitative claims tagged `[Data-backed]`; sizing assumptions explicit |
| **Competitive landscape** | Market context → Competitor profiles → Capability matrix → Strategic gaps → Implications | Competitor facts cited; strategic-gap analysis tagged `[Expert judgment]` |

**Routing rule:** Match the user's report type to the closest row. If the work spans types (e.g., "trend analysis with competitive landscape"), merge structural rules from both rows, keeping the primary type's section ordering and its key structural rule.

---

## 6. Modular Template

Generate the report using these modules. Select, expand, or omit modules based on the report type and audience — do not blindly include everything.

### 6.1 Core Modules (always present)

**Module 1: Market Problem & Decision Scenario**
- The market or industry problem the report addresses
- The time window, the intended readers, and the decision scenario the report serves
- The core trend judgment in one sentence
- Evidence annotation: problem-framing tagged `[Expert judgment]`; market context facts tagged `[Data-backed]` or `[Research-backed]`

**Module 2: Trend Judgments**
- Each trend stated as a judgment with its observable evidence named
- Drivers and inhibitors that strengthen or weaken the trend
- Evidence annotation: trend judgments tagged `[Expert judgment]` or `[Hypothesis]`; the data points supporting them tagged `[Data-backed]` or `[Research-backed]`

**Module 3: Evidence & Cases**
- Data, statistics, and market signals that make the trends visible
- Cases illustrating how the trend manifests in real organizations or markets
- Charts placed immediately after the relevant analysis, captioned and interpreted
- Evidence annotation: all quantitative claims tagged `[Data-backed]` with source attribution

**Module 4: Framework & Recommendations**
- Reusable framework derived from the analysis (separated from current market facts)
- Strategic or operational recommendations flowing from the framework
- Evidence annotation: framework tagged `[Expert judgment]`; recommendations tagged `[Hypothesis]` where they project future outcomes

**Module 5: Executive Summary**
- Written from the angle locked in §4, not paraphrased from the body at the end
- The core trend judgment, the 3–5 questions answered, and the headline recommendation
- Evidence annotation: summary claims inherit the tags of their source sections

### 6.2 Scenario-Triggered Modules

| Trigger | Module | Content |
|---------|--------|---------|
| Investment thesis | Valuation & risk assessment | Market sizing, competitive moat, risk factors; projections tagged `[Hypothesis]` |
| Regulatory scan | Policy & compliance landscape | Current and anticipated regulations; compliance implications tagged `[Research-backed]` |
| Technology adoption | Adoption curve & maturity analysis | Technology maturity stage, adoption barriers, acceleration factors |
| Geographic expansion | Regional market comparison | Per-region market facts, entry barriers, localization requirements |

---

## 7. Evidence Annotation & Verification Boundary

Every claim in the report carries an evidence tag. The verification boundary has a whitepaper-specific rule: current market facts are separated from reusable framework recommendations, and anything needing external verification is marked.

| Tag | Meaning | Typical Use |
|-----|---------|-------------|
| `[Data-backed]` | Supported by data the user provided or cited market data | Market sizes, statistics, survey results, measured metrics |
| `[Research-backed]` | Supported by a cited source | Industry findings, third-party research, published statistics |
| `[Expert judgment]` | Reasoned analysis by the report's authors | Trend interpretations, framework derivations, significance arguments |
| `[Hypothesis]` | Tentative claim awaiting evidence or verification | Outlook projections, recommendations, conclusion hypotheses |

**Verification rules:**

1. Separate current market facts (tagged `[Data-backed]` or `[Research-backed]`) from reusable framework recommendations (tagged `[Expert judgment]`). Do not blend observed market conditions with the report's strategic advice in the same passage.
2. Mark what can be derived from user material versus what needs external verification. Before verification, do not treat "current rules" or "current market" conclusions as final — keep them tagged and flag the verification need.
3. Do not use trend rhetoric without naming observable evidence. A trend judgment tagged `[Expert judgment]` or `[Hypothesis]` must point to the `[Data-backed]` signal that makes it visible.
4. The per-chapter evidence-placeholder checklist (§4) tracks every claim needing external verification. Resolve externally-verified claims before the report is considered complete; unresolved claims stay tagged and listed.

---

## 8. Quality Self-Check

After generation, verify every item internally. If any item does not pass, revise until it passes. Do NOT include the self-check in the final deliverable — this is internal quality assurance only.

### Detailed Checklist (12 Items)

| # | Check Item | Pass Criteria |
|---|-----------|---------------|
| 1 | **Market problem is framed first** | The report opens by defining the market problem, time window, readers, and decision scenario — not with trends |
| 2 | **Core trend judgment is stated** | The core trend judgment appears in one sentence early in the report |
| 3 | **Each chapter answers one question** | Every chapter resolves a single board-level or operational question; no chapter bundles multiple questions |
| 4 | **Trends have observable evidence** | Every trend judgment names the data, case, or market signal that makes it visible; no bare trend rhetoric |
| 5 | **Judgment, evidence, cases, and recommendations are separated** | These occupy distinct sections or clearly bounded passages — not blended in the same section |
| 6 | **Market facts and frameworks are separated** | Current market facts (tagged `[Data-backed]`/`[Research-backed]`) are distinct from reusable framework recommendations (tagged `[Expert judgment]`) |
| 7 | **Evidence tags are present** | Every claim carries `[Data-backed]` / `[Research-backed]` / `[Expert judgment]` / `[Hypothesis]`; no claim is untagged |
| 8 | **Executive summary is shaped early** | The summary reflects the angle locked in §4, not a paraphrase appended at the end |
| 9 | **Chart and data slots are planned** | Every chapter's evidence needs are mapped in the data-slot checklist; charts placed after the relevant analysis and captioned |
| 10 | **External-verification needs are marked** | Claims needing external research are flagged and listed; none treated as final before verification |
| 11 | **Conclusion stated once** | The headline conclusion appears in full exactly once in its canonical location; other sections reference it with new evidence, not rephrasing |
| 12 | **No fabricated market data** | No invented statistics, market sizes, competitor facts, or survey results; unverifiable claims are tagged, not fabricated |

---

## 9. Red-Line Rules

1. **Do not fabricate market data.** Invented statistics, market sizes, or survey results are prohibited. If data cannot be verified, tag the claim `[Hypothesis — verification pending]` and list it in the evidence-placeholder checklist.
2. **Do not use trend rhetoric without observable evidence.** Every trend judgment points to a data point, case, or market signal.
3. **Do not blend market facts with strategy in the same section.** Observed conditions and recommendations occupy distinct roles.
4. **Do not defer the executive summary to the end.** Its angle is defined when the outline is locked.
5. **Do not treat unverified market conclusions as final.** Current-rules and current-market claims stay tagged until externally verified.

---

## 10. Related Skills

| Skill | Relationship |
|-------|-------------|
| `research-guide` | Before writing, run market research and source gathering to populate the evidence-placeholder checklist |
| `academic-writing` | If the report contains a rigorous literature or methodology section, route that portion's conventions here |
