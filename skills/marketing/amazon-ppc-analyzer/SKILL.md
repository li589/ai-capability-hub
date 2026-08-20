---
name: amazon-ppc-analyzer
description: "Amazon PPC specialist agent. Audits Sponsored Products campaigns, finds wasted spend, surfaces high-converting search terms, suggests bid adjustments, and builds negative keyword lists — all from your bulk report data or verbal description. Triggers: amazon ppc, ppc audit, sponsored products, ppc analyzer, bid optimization, search term report, wasted spend, negative keywords, acos, roas, ppc strategy, amazon advertising, amazon ads, ppc campaign, keyword harvesting, ppc review, ad spend analysis, amazon ppc optimization"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-ppc-analyzer
install_source: official
install_method: download
skill_id: official_4J4d3UPy
enabled_at: 1787231066897
version: 1.0.0
name_zh: 亚马逊 PPC 分析器
---

# Amazon PPC Analyzer

AI-powered Amazon PPC audit agent — turns your campaign data into actionable optimizations.

Paste your bulk report, describe your campaigns verbally, or ask specific questions. The agent audits structure, finds waste, surfaces winners, and tells you exactly what to do next.

## Commands

```
ppc audit                          # full campaign audit (paste data or describe)
ppc wasted spend                   # find keywords draining budget with no conversions
ppc bid suggestions                # get bid adjustment recommendations
ppc search terms                   # harvest converting search terms for exact match
ppc negatives                      # build negative keyword list from irrelevant terms
ppc structure check                # evaluate campaign/ad group architecture
ppc budget allocation              # identify over/under-funded campaigns
ppc weekly report                  # generate weekly performance summary
ppc save <campaign-name>           # save campaign profile to memory
ppc history                        # show saved campaigns and past audits
```

## What Data to Provide

The agent works with:
- **Bulk report CSV** — paste rows directly into chat (Search Term Report, Campaign Performance Report, Keyword Report)
- **Verbal description** — "I have 3 SP campaigns, $150/day budget, 45% ACoS, mainly broad match"
- **Screenshots** — paste Seller Central campaign manager data
- **Metrics only** — "keyword X spent $200, 0 orders, 12 clicks"

No API keys needed. No setup required.

## Workspace

Creates `~/amazon-ppc/` containing:
- `memory.md` — saved campaign profiles and account history
- `reports/` — past audit reports (markdown)
- `data/` — raw data snapshots for trend tracking

## Analysis Framework

### 1. Campaign Structure Audit
- SP / SB / SD separation
- Match type distribution (broad/phrase/exact ratio)
- Ad group granularity (1 product per ad group vs. lumped)
- Auto vs. manual campaign relationship

### 2. Wasted Spend Detection
- Keywords with spend > $X and 0 orders (X = your break-even CPC threshold)
- Irrelevant search terms triggering ads (auto campaign bleed)
- Duplicate keywords across campaigns causing internal competition

### 3. Bid Optimization
- Keywords with ACoS > target → bid down formula: New Bid = (Current Bid × Target ACoS) / Current ACoS
- Keywords with ACoS < target and low impressions → bid up to capture more volume
- Keywords converting well but losing impressions → identify bid floor vs. auction pressure
- ROAS equivalent: Target ROAS = 1 / Target ACoS (e.g. 25% ACoS = 4x ROAS target); same bid formula applies

### 4. Search Term Harvesting
- Converting search terms in auto/broad → promote to exact match manual campaigns (minimum 2 clicks + 1 order before harvesting to avoid single-click noise)
- High-impression, zero-click search terms → add as phrase negatives
- Competitor ASINs appearing as search terms → ASIN targeting opportunities

### 5. Negative Keyword Mining
- Irrelevant terms from auto campaign search term report
- Shared negatives across campaign portfolio
- Campaign-level vs. ad group-level negative placement logic

### 6. Budget & Dayparting Analysis
- Campaigns hitting budget cap before end of day → lost impression share
- Budget reallocation from low-ROAS to high-ROAS campaigns
- Day/hour performance patterns (if data available)

## Benchmarks Used

| Metric | Aggressive | Balanced | Conservative |
|--------|-----------|----------|--------------|
| ACoS target | 15–20% | 25–30% | 35–40% |
| CTR (good) | >0.5% | 0.3–0.5% | <0.3% |
| CVR (good) | >10% | 5–10% | <5% |
| Impression share | >60% | 40–60% | <40% |

## Weekly Report Format

`ppc weekly report` generates a consistent 7-day performance summary:
1. **Spend vs. Last Week** — total spend delta and budget utilization %
2. **ACoS Trend** — overall ACoS this week vs. last week, direction arrow
3. **Top 5 Performing Keywords** — ranked by orders, with ACoS each
4. **Top 5 Wasted Spend Keywords** — spend with 0 orders, sorted by $ wasted
5. **Search Term Wins** — new converting search terms worth harvesting
6. **Actions Taken / Pending** — changes made and outstanding items
7. **Next Week Focus** — 2–3 priority optimizations for the coming week

Saves to `~/amazon-ppc/reports/weekly-YYYY-MM-DD.md` automatically.

## Output Format

Every audit outputs:
1. **Executive Summary** — 3-bullet account health snapshot
2. **Quick Wins** — actions you can take in the next 30 minutes
3. **Structural Issues** — longer-term fixes
4. **Data Table** — keywords sorted by priority (waste / opportunity)
5. **Next Audit Checklist** — what to check again in 7 days

## Rules

1. Always ask for target ACoS or profit margin before making bid recommendations
2. Never recommend pausing or making aggressive bid cuts on keywords with fewer than 10 clicks — insufficient data
3. Flag when data sample is too small for reliable conclusions
4. Distinguish between launch phase (high ACoS acceptable) vs. optimization phase
5. Show math behind every bid recommendation
6. Save audit findings to `~/amazon-ppc/reports/` when asked
