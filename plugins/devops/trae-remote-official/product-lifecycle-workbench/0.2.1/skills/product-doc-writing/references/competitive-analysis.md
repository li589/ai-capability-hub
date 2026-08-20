---
name: competitive-analysis
description: >
  Competitive analysis deliverables — competitor benchmarks, market landscape
  maps, player profiles, and competitor-vs-competitor comparison reports.
  Provides timeliness governance, top-down industry sweep, per-competitor deep
  dive workflow, and freshness quality gates calibrated to evidence-backed
  competitive intelligence.
---

# Competitive Analysis

## 1. Prime Directive — Timeliness Above All Else

In competitive analysis, **timeliness is always the single most important quality
attribute**. Stale information does not merely weaken a report — it produces
*wrong industry judgments*, which is worse than no report at all. Every rule
below exists to serve this directive. If any instruction ever conflicts with
timeliness, timeliness wins.

Internalize three axioms before doing anything else:

1. **Outdated data = invalid data.** Industries move fast. Unless for a historical
   analysis, **any data point older than ~12 months has no reference value** and must not anchor a conclusion. Treat it as background at best, and label it as historical.
2. **Do not trust your own training knowledge for current facts.** Market
   leaders, product line-ups, pricing, funding, and headcount all change
   constantly. Always fetch the latest situation via tools.
3. **Time-ambiguous data is unusable until disambiguated.** If a data point
   arrives without a clear "as-of" date, you MUST cross-confirm its date from
   multiple sources. If the date cannot be established, the data point **must not
   appear in the final report** — drop it or tag it `[DATE-UNKNOWN → excluded]`.

***

## 2. Relationship to `research-guide` (Mandatory Delegation)

This Skill is a **workflow orchestrator**, not an evidence collector. All actual
information gathering **MUST** go through the `research-guide` Skill.

If the task involves broad industry research (not just a narrow head-to-head
competitor comparison), you **MUST** invoke the `research-guide` Skill. Load it
explicitly.

***

## 3. Workflow Overview

```
Scope & Timeliness Setup (§4)
        │
        ▼
Top-Down Industry Sweep (§5.1)  ──►  Prioritize Competitors (§5.2)
        │                                     │
        ▼                                     ▼
Per-Competitor Deep Dive (§5.3)  ──►  Framework Evaluation (via research-guide comparison-analysis)
        │
        ▼
Timeliness Gate (§6)  ──►  Report Assembly (§7)
```

***

## 4. Step 1 — Scope & Timeliness Setup

Do this before the first search.

1. **Establish "now".** Determine the current date and treat it as the anchor
   for every query. Compute the freshness cutoff: default `now − 12 months`
   (`now − 6 months` for fast-moving spaces like AI, crypto, consumer social).
2. **Confirm the frame.** Is this a *current-state* analysis (default, freshness
   rules fully apply) or an explicitly *historical* analysis (freshness rules
   relax, but every point must still be date-stamped)?
3. **Define the comparison basis** with `research-guide` / `comparison-analysis`:
   which entities, which shared dimensions, which industry-defining KPIs.
4. **Resolve unclear terms.** If the user's query contains industry jargon,
   acronyms, or terms you don't fully understand, try to websearch them first.
5. **Domestic vs. international split (when relevant).** If the user's language
   or context implies a regional market (e.g., a Chinese-language query often
   implies China market relevance), segment competitors into domestic and
   international groups where it makes sense.

### 4.1 Time-in-Query Rule (Non-Negotiable)

Whenever you run a web search, or launch a subagent/Explore agent to research:

- **The current time MUST appear in the query.** Include the explicit year and,
  for volatile topics, the quarter or month — e.g.
  `"leading X market share 2026"`, `"CompA pricing July 2026"`,
  `"latest CompB funding round as of 2026"`.
- Prefer recency-biased phrasing: `latest`, `current`, `as of <year>`,
  `<year> update`, `most recent`. Add recency filters when the tool supports them.

### 4.2 Freshness Grading (applied to every retrieved data point)

| Grade | Age vs. cutoff | Handling |
|-------|----------------|----------|
| **Fresh** | Within cutoff, date confirmed | Usable; carry an `(as of <date>)` tag |
| **Aging** | Near the cutoff edge | Usable only if re-confirmed by a fresher source; flag for the user |
| **Stale** | Older than cutoff (non-historical task) | **Invalid** — exclude from conclusions; may appear only as explicitly labeled historical background |
| **Date-unknown** | No verifiable date | Cross-confirm the date first; if it stays unknown, **exclude entirely** |

***

## 5. Step 2 — Big-to-Small Data Collection Sequence

When the task involves broad industry data collection, gather from **large to
small**. Never jump straight to a favorite competitor. All searches run through
`research-guide` and obey §4.1 (time-in-query).

### 5.1 Sweep the Industry First (top-down)

1. **Map the top before the parts.** Web-search the industry's *leaders* and
   *flagship products* first — who holds share, who sets the agenda, what the
   category-defining products are. **Do not rely on your own knowledge**; the
   leaderboard may have changed. Fetch the latest standings via tools.
2. **Construct broad, unbiased initial queries.** For the industry sweep, keep
   queries open-ended to let search engines surface current leaders. **GOOD**:
   `"best AI coding IDE 2026"`, `"top project management tools 2026"`. **BAD**:
   `"best AI coding IDE 2026 Cursor Windsurf GitHub Copilot Trae"` — this biases
   the search toward known names and risks missing emerging players or recent
   market shifts.
3. **Do NOT use subagents in this phase.** The initial industry sweep requires a
   unified, top-down cognitive grasp of the landscape. Splitting this across
   subagents risks missing connections and producing fragmented understanding.
   Conduct the broad survey yourself first.
4. **Scrutinize freshness and authority on every result.** Check the publication
   date and the source tier (P0/P1 preferred per `research-guide` §3.1). A
   confident-sounding but undated or old ranking is worthless here.
5. **Establish the frame**: total market size, growth rate, structure
   (dominant-player / duopoly / fragmented / nascent), and the 3–5 metrics that
   actually separate players — all date-stamped and cross-validated.

### 5.2 Prioritize Competitors by Importance

From the industry sweep, rank candidate competitors by relevance to the user's
goal (share, overlap with the user's product, threat level, growth momentum).
Investigate in **descending order of importance** — spend the deepest effort on
the players that matter most, and time-box or drop the long tail.

### 5.3 Competitor Deep Dive (subagents optional)

Once you have a unified global understanding of the landscape, subagents may be
considered for parallel deep dives. This is **not mandatory** — for a handful of
competitors, doing the research yourself is usually faster.

**Do NOT spawn one subagent per competitor.** That explodes into many parallel
agents and makes execution far too slow. Instead:
- **Batch competitors into a small number of subagents** (cap at ~2–3 total).
  Group several competitors per subagent — e.g. one agent covers 3–4 rivals on
  the same dimensions — rather than one agent per rival.
- Only split into a separate subagent when a competitor genuinely needs
  independent, deep investigation that would otherwise bottleneck the rest.
- If the competitor set is small (≤3–4), just research them yourself without
  subagents.

When delegating, provide each subagent with: the current date, the freshness
cutoff, the specific competitors to investigate, and explicit instructions to
follow `research-guide` constraints (source hierarchy, cross-validation, no
synthetic data).

***

## 6. Step 3 — Timeliness Gate

- **Timeliness Gate (must pass before report assembly):**
  - [ ] Current date/year is embedded in every search query and delegation prompt.
  - [ ] Every data point carries a verifiable `(as of <date>)` tag.
  - [ ] No Stale point (older than the cutoff, non-historical task) anchors any
        conclusion.
  - [ ] All Date-unknown points were cross-confirmed or excluded — none leaked
        into the report.
  - [ ] Industry leaderboard/landscape was verified via tools, not assumed from
        memory.
  - [ ] Any Aging point used is explicitly flagged for user re-verification.

***

## 7. Step 4 — Report Assembly

Assemble the report. File creation is recommended.

> **⚠️ Internal vocabulary MUST NOT leak into the final report.** The words
> **`aging`, `fresh`, `stale`, and `as of`** are internal timeliness-governance
> terminology used only during data collection and grading (§4.2, §6). They must
> **never appear in the final deliverable** — no `(as of <date>)` tags, no
> "fresh/aging/stale" freshness labels, and no wording derived from them.
> Present dates directly and naturally instead (e.g. "Q2 2026 revenue" or
> "priced at \$X in June 2026"), and keep all freshness reasoning behind the
> scenes. Before finalizing, scan the report and strip or rephrase any
> occurrence of these terms.

***

## 8. Red-Line Rules

1. **Timeliness first, always.** A fresh-but-incomplete picture beats a
   comprehensive-but-stale one.
2. **No current facts from memory.** Leaders, pricing, funding, headcount, and
   features must be tool-verified.
3. **Date-unknown = excluded.** Time-ambiguous data must be cross-confirmed;
   if its date cannot be established, it cannot appear in the final report.
4. **Time in every query.** Web searches and subagent delegations must embed the
   current year (and quarter/month for volatile spaces).
5. **Big-to-small.** Sweep the industry's leaders and flagship products first,
   then work down to competitors by importance — never start narrow.
6. **No internal freshness vocabulary in the report.** The terms `aging`,
   `fresh`, `stale`, and `as of` are for internal grading only and must never
   appear in the final deliverable — surface dates naturally instead.
