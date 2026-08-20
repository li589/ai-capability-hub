# Source strategy

## Source ladder

Use sources for different jobs; do not treat every source as equally probative.

| Tier | Source class | Best use | Claim treatment |
|---|---|---|---|
| A | Official changelog, pricing, docs, newsroom, regulator, filing, public repository release | Confirm product, price, policy, funding, and availability changes | Primary evidence |
| B | Named executive or team account, conference talk, public roadmap, partner announcement, app store | Confirm intent, launch context, distribution, and ecosystem change | Firsthand; verify material details |
| C | Reputable trade press, financial media, research body, standards organization | Independent context and corroboration | Secondary evidence |
| D | Product Hunt, Hacker News, GitHub issues/discussions, Reddit, public WeChat, public Xiaohongshu, public communities | Detect early adoption, pain, launch, and narrative shifts | Lead or weak evidence unless corroborated |
| E | Aggregators, reposts, SEO summaries, anonymous rumor accounts | Discover a possible original source | Never sole support for a material claim |

Prefer the original page over a summary about it. For financing, regulation, legal terms, pricing, or
security claims, require Tier A or strong independent corroboration.

## Query mesh

For each monitored entity, build a compact multilingual mesh:

1. **Identity** — canonical name, product names, former names, ticker, domain, repository, official
   social accounts, and common local-language spellings.
2. **Change theme** — launch, release, changelog, pricing, plan, enterprise, integration, model,
   acquisition, funding, leadership, partnership, policy, standard, developer program.
3. **Time** — last successful run through now; also query the last seven days to catch late indexing.
4. **Source** — official domain, repository, regulator, app store, launch/community surface.
5. **Language** — search English plus the market language; translate the concept, not just the name.

Use a small number of high-yield queries, then follow sources. Do not expand into an exhaustive
industry crawl when the decision can already be supported.

Default budget: use one official/primary query path for each in-scope entity or theme, then one
corroborating path only for the strongest consequential candidates. Stop after three to five
qualified net-new signals or when the decision is already supported. Expand the mesh only for P0,
sensitive claims, unresolved contradictions, or an explicit request for deeper coverage.

## Timeliness protocol

Record:

- `event_at`: when the underlying event occurred;
- `published_at`: when the page was published;
- `observed_at`: when the radar found it;
- `effective_at`: when the change takes effect.

An undated page is not proof of a recent change. Look for release history, archived copies, structured
metadata, repository history, or corroborating dated announcements. If recency cannot be established,
label the date unknown.

## Verification protocol

For every P0/P1 candidate:

1. locate the strongest primary source;
2. confirm date, geography, product/plan, availability, and effective conditions;
3. find one independent or complementary source when the claim is consequential;
4. compare with the last known baseline;
5. identify contradictions and state which interpretation is used;
6. downgrade priority or confidence if the delta remains ambiguous.

One source can be sufficient for a straightforward official release. Two-source confirmation is
preferred for financing amounts, layoffs, leadership intent, policy interpretation, customer impact,
and claims based on community reports.

## Frontier-source handling

Frontier channels improve lead time but require restraint:

- Use Product Hunt launch pages for launch timing, positioning, maker statements, and early reaction;
  verify features and pricing on the product's own site.
- Use GitHub releases and public repositories for shipped versions, integrations, issue velocity, and
  developer response; do not infer enterprise adoption from stars.
- Use public WeChat articles for Chinese company announcements and practitioner commentary; link the
  original public article and paraphrase.
- Use public Xiaohongshu posts for emerging workflows, pain points, and vocabulary; treat engagement
  as directional and never as market share.
- Use Hacker News, Reddit, reviews, and public communities to form hypotheses; report repeated themes
  with sample size and selection caveats.

If a page requires login, payment, invitation, CAPTCHA bypass, or scraping against access controls,
do not circumvent it. Use visible public information, an authorized connected session, or another
source.

## Rights and privacy guardrails

- Link to sources; do not republish them.
- Summarize in original language and use only short quotations when they add evidentiary value.
- Do not copy article bodies, paid reports, images, charts, or large screenshots.
- Do not reproduce user handles unless identity is relevant and public; prefer aggregate themes.
- Do not collect private profiles, closed-group content, personal contact details, precise location,
  or sensitive personal attributes.
- Honor robots, access controls, rate limits, and platform terms.
- Record only the minimum evidence needed to support the intelligence claim.

## Coverage ledger

Close every scan with a compact ledger:

| Theme | Sources checked | Latest verified change | Gap |
|---|---|---|---|
| Product/model | official changelogs, docs, repos | date or none | missing region detail |
| Pricing/commercial | pricing and terms pages | date or none | enterprise quote unavailable |
| Organization/capital | newsroom, filings, credible media | date or none | unconfirmed rumor excluded |
| Market/technology/policy | regulators, standards, research bodies | date or none | publication lag |
| Ecosystem | partners, stores, communities | date or none | community sample bias |

This ledger proves coverage and makes `no material change` meaningful.
