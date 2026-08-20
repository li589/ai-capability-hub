---
name: marketing-copy
description: >
  Sub-Skill for generating marketing copy and commercial persuasion content.
  Covers brand stories, campaign copy, proposals, host scripts, landing
  pages, and pitch decks. Dynamically determines audience profile, core
  promise, benefit structure, evidence layer, and call-to-action flow
  based on copy type, channel, and purchase friction. Inherits all
  constraints from doc-writing-guide-v2; adds marketing-specific workflows,
  templates, and quality gates.
---

# Marketing Copy

## 0. Relationship to Parent

This Skill inherits **all** constraints from `doc-writing-guide-v2`:

- Intent interpretation (SS1): purpose, audience, tone, scope, and constraint analysis.
- Genre & format selection (SS2): this scenario maps to the "Marketing / Copy" genre row in §2.1.
- Language to avoid (SS3): no checklist-jargon, no empty superlatives, no formulaic stubs. Marketing copy is especially prone to empty superlatives ("world-class", "cutting-edge", "revolutionary") — these are prohibited unless backed by specific evidence.
- Content structure principles (SS4): substance over format, no pre-imposed rigid outlines.
- Visual generation guide (SS5): charts and diagrams follow parent rules.
- Citation: marketing copy does not require inline citations unless the user explicitly requests evidence-backed claims that involve external data. However, every quantitative claim (metrics, percentages, comparisons) must be tagged with its evidence tier per §6.
- Evidence boundary: do not fabricate testimonials, metrics, endorsements, case-study results, or pricing claims. Mark unverifiable performance claims as `[Hypothesis]` or `[To be confirmed]`.

Anything defined below **extends** the parent; it never overrides.

---

## 1. Core Principles

1. **Audience-first, always.** Define the audience, the scenario they are in, and the purchase friction they face before writing a single line of copy. Copy that does not know who it is talking to cannot persuade.
2. **One core promise before sub-arguments.** State a single, specific core promise before stacking supporting benefits. The reader must know what you are offering before they encounter why it matters.
3. **Evidence over abstraction.** Every value claim must be grounded in evidence, a concrete scenario, or a quantifiable signal. "Saves time" is abstraction; "cuts report prep from 4 hours to 20 minutes" is evidence.
4. **Flow integrity.** Connect audience pain, core promise, evidence, use cases, and call-to-action in one continuous flow. The reader should move from hook to action without a jarring tonal or structural break.
5. **Benefits are audience-specific outcomes, not feature lists.** Translate every product feature into the specific outcome it produces for this audience. A feature is what the product does; a benefit is what the reader gets.

---

## 2. Workflow Overview

Execute the following steps in order:

```
Step 1: Requirement Recognition → §3 (classify across 5 dimensions)
Step 2: Structure Selection → §4 (match copy type to structure pattern)
Step 3: Modular Generation → §5 (select core + scenario-triggered modules)
Step 4: Evidence Annotation → §6 (tag every value claim)
Step 5: Quality Self-Check → §7 (verify 12 items)
```

---

## 3. Requirement Recognition (Five Dimensions)

On receiving a marketing copy request, classify the input across these five dimensions before proceeding:

| Dimension | Classification Options |
|-----------|----------------------|
| **Copy type** | Landing page / Campaign copy / Brand story / Proposal / Host script / Pitch / Email / Social post |
| **Audience** | Decision-maker (B2B) / End consumer (B2C) / Channel partner / Investor / Internal stakeholder / Event attendee |
| **Purchase friction** | Price sensitivity / Complexity barrier / Trust deficit / Risk aversion / Status-quo inertia / Awareness gap |
| **Channel** | Landing page / Email / Social media / Event stage / Printed collateral / In-app / Video script |
| **Tone register** | Formal proposal / Conversational campaign / Energetic host script / Authoritative brand / Urgent promotion |

**Execution rule:** Present classification as a brief table to the user. Confirm correctness before proceeding. If uncertain about any dimension, state your inference rationale and ask the user to confirm or correct.

---

## 4. Structure Selection Matrix

Match the copy type to its structure pattern. When multiple patterns apply (e.g., a campaign that includes a landing page and email), generate each format independently using its own pattern.

| Copy Type | Structure Pattern | Mandatory Elements |
|-----------|-------------------|--------------------|
| **Landing page** | Hero promise → benefit stack → evidence → social proof → CTA | Headline promise, 3–5 benefit points, evidence block, CTA above and below fold |
| **Campaign copy** | Pain point → core promise → scenario → evidence → CTA | Opening hook, single promise, use-case scenario, supporting evidence, action prompt |
| **Brand story** | Origin → tension → resolution → values → invitation | Narrative arc, authentic voice, values statement, soft CTA |
| **Proposal** | Context → problem → solution → evidence → pricing → CTA | Client context, problem framing, proposed solution, proof points, pricing tiers, next steps |
| **Host script** | Hook → narrative beats → key messages → interaction → close | Opening hook, segment transitions, key talking points, audience interaction cues, closing CTA |
| **Pitch** | Problem → opportunity → solution → traction → ask | Market pain, market size, product, traction evidence, funding ask |
| **Email** | Subject line → hook → body → CTA | Subject hook, opening line, value body, single clear CTA |

**Routing rule:** Match the user's copy type to the closest row. If the request is ambiguous (e.g., "write copy for our product"), infer from the audience and channel: investor-facing → pitch; consumer-facing landing → landing page; event context → host script.

---

## 5. Modular Template

Generate the copy using these modules. **Select, expand, or omit modules based on the structure selection result** — do not blindly include everything.

### 5.1 Core Modules (always present)

#### Module 1: Audience & Scenario Definition

- Target audience sketch: who they are, what they currently do, what frustrates them
- Purchase friction: the specific barrier between this audience and a purchase decision
- Scenario: the moment or context in which the audience encounters this copy
- Evidence strength annotation: audience profile tagged `[Data-backed]` if backed by user research, `[Hypothesis]` if inferred

> This module is internal scaffolding — it informs the copy but is not included as a visible section in the final deliverable unless the user requests a creative brief.

#### Module 2: Core Promise

- A single, specific promise stated in the audience's language
- Must answer: what outcome will the reader get, and why should they care now?
- Stated before any supporting benefits or features
- Tagged with its evidence tier — a promise without evidence is `[Hypothesis]`

#### Module 3: Benefit Stack

- 3–5 supporting benefits, each translated from a product feature into an audience-specific outcome
- Ordered by perceived value to this audience (highest first)
- Each benefit pairs the outcome with a brief evidence anchor (metric, scenario, or comparison)
- No benefit is a bare feature description — "Real-time sync" is a feature; "Your team always works from the latest data, no version conflicts" is a benefit

#### Module 4: Evidence Layer

- Quantitative proof: metrics, benchmarks, before/after comparisons — tagged `[Data-backed]`
- Qualitative proof: case studies, testimonials, use-case scenarios — tagged `[Research-backed]` if from external sources
- Objection handling: anticipate the top 1–3 objections for this audience and address them with evidence, not assertion

> Do not fabricate testimonials, metrics, or case studies. If the user has not provided evidence, mark claims as `[Hypothesis]` and flag for the user to supply real data before publication.

#### Module 5: Call to Action

- A single, specific action the reader should take next
- Placed in the same flow as the evidence — the reader should reach it through natural momentum, not a structural jump
- States what happens after the action (e.g., "Start your 14-day trial — no credit card required")

### 5.2 Scenario-Triggered Modules (include when copy type matches)

#### Pricing & Tiers Module (landing pages, proposals)

- Clear, plain-language pricing with no hidden conditions
- Benefit/pricing tiers: what each tier includes, stated as outcomes not feature lists
- Tier comparison table (when ≥2 tiers)
- All pricing claims tagged `[Data-backed]` — do not invent prices

#### First-Paragraph Sample Copy Module (all types)

- A sample opening paragraph written in the correct register for this copy type
- Opens with an audience pain point or an immediate benefit — never with a meta-statement about the company
- Demonstrates the tone the full draft should carry

#### Channel Adaptation Module (multi-channel campaigns)

- Tone and length adjustments per channel (e.g., social post is punchier than landing page body)
- Key message consistency: the core promise and primary evidence stay identical across channels; expression adapts
- CTA adaptation: channel-appropriate action (e.g., "Learn more" on social vs. "Start trial" on landing page)

#### Rewrite Checklist Module (revision passes)

When revising existing copy, apply this checklist:

| Action | Question |
|--------|----------|
| **Preserve** | What legally or factually required wording must stay unchanged? |
| **Shorten** | What can be cut without losing the core promise or key evidence? |
| **Strengthen evidence** | Which claims currently lack backing and need specific data or scenarios? |
| **Move closer to CTA** | What content sits too far from the action prompt and should be repositioned? |

---

## 6. Evidence Annotation System

Every value claim in the copy must be tagged so the reviewer can distinguish verified claims from aspirations. Use these four labels inline, immediately after the claim:

| Label | Meaning | Example Usage |
|-------|---------|---------------|
| `[Data-backed]` | Supported by quantitative data the user provided or that is publicly verifiable | "Reduces processing time by 73% `[Data-backed]`" |
| `[Research-backed]` | Supported by external research, industry report, or third-party study | "Teams using collaborative tools report 32% faster delivery `[Research-backed]`" |
| `[Expert judgment]` | Inferred from domain expertise or market knowledge, not independently verified | "This pricing positions us in the premium-mid segment `[Expert judgment]`" |
| `[Hypothesis]` | An assumption made to fill an information gap; must be confirmed before publication | "Users will likely upgrade after 2 weeks `[Hypothesis]`" |

**Rules:**
- Never present a `[Hypothesis]` claim as a verified fact in published copy.
- Quantitative claims (metrics, percentages, savings) without a data source must be `[Hypothesis]` and flagged for user verification.
- Testimonials and endorsements must be real — never fabricate. If none are available, omit the social-proof section rather than invent quotes.

---

## 7. Quality Self-Check

After generation, verify every item internally. If any item does not pass, revise the copy until it passes. Do NOT include the self-check table or results in the final deliverable — this checklist is for internal quality assurance only.

| # | Check Item | Pass Criteria |
|---|-----------|---------------|
| 1 | **Audience is defined** | The copy addresses a specific audience with a named purchase friction — not "everyone" or "all users" |
| 2 | **Purchase friction is identified** | The specific barrier this copy must overcome is stated in the internal scaffolding (Module 1) |
| 3 | **Core promise comes first** | A single, specific promise appears before any supporting benefits or features — no benefit stacking without a lead promise |
| 4 | **Benefits are audience-specific outcomes** | Every benefit translates a feature into what the reader gets — no bare feature descriptions posing as benefits |
| 5 | **Evidence supports each value claim** | Every quantitative or comparative claim carries an evidence tag; no untagged assertions of superiority |
| 6 | **CTA is in the same flow** | The call-to-action is reached through natural momentum from the evidence — not a structural jump or afterthought |
| 7 | **Tone is consistent within the format** | No switching between formal proposal register and casual campaign tone within the same deliverable |
| 8 | **Opening hooks with pain or benefit** | The first line opens with an audience pain point or immediate benefit — never with a company meta-statement |
| 9 | **No abstract value claims** | No claim like "world-class", "revolutionary", or "best-in-class" without specific, tagged evidence |
| 10 | **No fabricated proof** | No invented testimonials, metrics, endorsements, or case-study results — unproven claims are tagged `[Hypothesis]` |
| 11 | **Objections are addressed** | The top 1–3 likely objections for this audience are anticipated and answered with evidence |
| 12 | **Rewrite checklist applied** | If this is a revision, the preserve/shorten/strengthen/move checklist has been run — nothing required was lost |

---

## 8. Red-Line Rules

1. **Do not list features without audience-specific outcomes.** A feature list is not copy. Every feature must be translated into the benefit it delivers to this specific audience.
2. **Do not switch tone between formats.** If generating multiple deliverables (e.g., proposal + campaign email), each maintains its own consistent register — no bleeding of formal proposal language into casual campaign copy.
3. **Do not make abstract value claims without evidence.** "Industry-leading", "next-generation", and similar phrases are prohibited unless immediately followed by specific, tagged evidence.
4. **Do not fabricate proof.** Testimonials, metrics, endorsements, and case studies must be real. If none are available, omit the proof section and flag the gap — never invent social proof.
5. **Do not present hypotheses as facts.** Any aspirational or inferred claim must carry `[Hypothesis]` and be flagged for user verification before publication.
