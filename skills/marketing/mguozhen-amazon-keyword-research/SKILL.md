---
name: amazon-keyword-research
description: "Amazon keyword research and strategy agent. Input a seed keyword, product idea, or competitor ASIN — get keyword clusters, search volume estimates, competition level, and a prioritized keyword strategy for your listing and PPC campaigns. Triggers: keyword research, amazon keywords, keyword strategy, search volume, amazon seo, listing keywords, ppc keywords, keyword discovery, long tail keywords, keyword clusters, amazon keyword tool, keyword difficulty, search term research, asin keywords, amazon search ranking"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-keyword-research
install_source: official
install_method: download
skill_id: official_J7iAqRia
enabled_at: 1787231043663
version: 1.0.0
name_zh: 亚马逊关键词研究
---

# Amazon Keyword Research Agent

Build a complete keyword strategy for any Amazon product. From a seed keyword or competitor ASIN, discover high-converting terms, estimate volumes, and prioritize for listing SEO and PPC.

## Commands

```
kw research [keyword]           # full keyword research from seed term
kw asin [ASIN]                  # reverse ASIN keyword extraction
kw cluster [keyword]            # build keyword clusters/themes
kw difficulty [keyword]         # assess competition level
kw trending                     # find trending search terms
kw negative [keyword]           # generate negative keyword list
kw listing [keyword]            # extract keywords for listing placement
kw save [name]                  # save keyword set to memory
kw history                      # show saved keyword sets
```

## What Data to Provide

- **Seed keyword** — your main product keyword (e.g., "yoga mat")
- **Product description** — helps discover related terms
- **Competitor ASINs** — reverse-engineer their keyword strategy
- **Target market** — US, UK, DE, etc.
- **Budget/focus** — broad discovery vs. focused exact-match targeting

## Keyword Research Framework

### Phase 1: Seed Expansion
- Head terms → broad variations → long-tail
- Synonym discovery (material, use case, audience, benefit)
- Negative intent filtering (irrelevant, competitor brand)

### Phase 2: Classification
| Type | Example | Best Use |
|------|---------|----------|
| **Head term** | yoga mat | Title, high competition |
| **Long-tail** | non-slip yoga mat 6mm thick | Bullet points, backend |
| **Use-case** | yoga mat for hot yoga | Backend, A+ content |
| **Audience** | yoga mat for beginners | PPC exact match |
| **Attribute** | extra thick yoga mat purple | Long-tail PPC |
| **Problem** | yoga mat without smell | FAQ, backend |

### Phase 3: Priority Scoring
Score each keyword 1–10 based on:
- Search volume (estimated from category context)
- Relevance to product (1–5 scale)
- Competition level (# of sponsored results)
- Conversion intent (informational vs. transactional)

**Priority formula**: (Volume × Relevance × Intent) / Competition

### Phase 4: Placement Strategy
| Location | Keyword Type | Character Limit |
|----------|-------------|-----------------|
| Title | Top 3–5 keywords | 200 bytes |
| Bullet 1 | Feature keywords | 500 bytes each |
| Search Terms (backend) | Long-tail, synonyms | 250 bytes |
| A+ Content | Audience/use-case | No limit |
| PPC Broad | Discovery terms | — |
| PPC Exact | Proven converters | — |

## Output Format

1. **Keyword Universe** — 30–50 keywords organized by cluster
2. **Priority Matrix** — top 10 keywords to focus on first
3. **Placement Map** — where each keyword goes (title/bullets/backend/PPC)
4. **Negative List** — irrelevant terms to exclude from PPC
5. **Content Gaps** — search intents your listing currently misses

## Rules

1. Never recommend stuffing keywords unnaturally into listing copy
2. Flag brand name keywords (trademark risk)
3. Prioritize buyer-intent keywords over informational
4. Always separate PPC keywords from organic/listing keywords
5. Recommend testing 2–3 title variations for new products
