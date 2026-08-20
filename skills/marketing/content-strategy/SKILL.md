---
name: content-strategy
description: |
  Premium content creation and SEO optimization suite for marketers, founders, and content creators. Four specialized agents: (1) Blog Writer — creates SEO-optimized long-form blog posts in multiple formats (listicle, how-to, thought leadership, case study, comparison) with title tags, meta descriptions, internal linking, and featured snippet optimization. (2) Newsletter Writer — drafts email newsletters in multiple formats (weekly roundup, deep dive, curated links, personal update) with subject line formulas, segmentation recommendations, and A/B test plans. (3) SEO Optimizer — performs comprehensive on-page SEO audits, readability analysis, content gap identification, keyword clustering, and AI Overview/featured snippet strategy with prioritized action plans. (4) Content Repurposer — transforms one piece of content into platform-native assets for Twitter/X threads, LinkedIn posts, Instagram carousels, YouTube scripts, podcast outlines, and email snippets with a 14-day distribution calendar. Triggers: "blog post", "write a blog", "newsletter", "email newsletter", "SEO audit", "optimize for SEO", "keyword strategy", "repurpose content", "content strategy", "editorial calendar", "Twitter thread from blog", "LinkedIn post", "Instagram carousel", "content plan", "create content", "write content". NOT for: ad copy (use ad-copy-generator), social media scheduling, PR writing, technical documentation, or code generation.
version: 1.0.0
argument-hint: <topic or content> [--type blog|newsletter|seo|repurpose]
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
model: sonnet
metadata:
  superbot:
    emoji: 📝
install_source: official
install_method: download
skill_id: official_zW9L1I4Q
enabled_at: 1787231015790
name_zh: 内容策略
---

# Content Strategy Suite

Premium AI-powered content creation and SEO optimization toolkit. Like having a content team — strategist, writer, SEO specialist, and distribution manager — powered by proven frameworks that drive organic traffic, build audiences, and convert readers into customers.

## What This Skill Does

Takes your topic, audience, and goals — and generates:
- **SEO-optimized blog posts** in 5 content formats with complete metadata, internal linking strategy, and featured snippet targeting
- **Email newsletters** with 7-10 subject line options, platform-formatted content, segmentation notes, and A/B test plans
- **Comprehensive SEO audits** with prioritized action plans, readability scoring, content gap analysis, and keyword clustering
- **Multi-platform content packages** transforming one piece into Twitter threads, LinkedIn posts, Instagram carousels, YouTube scripts, podcast outlines, and email snippets

## Agents

### Blog Writer (`blog-writer`)

Creates SEO-optimized long-form blog posts (1,500-3,000 words) across 5 content architectures.

**What it produces**:
- Content in listicle, how-to, thought leadership, case study, or comparison format
- SEO metadata: title tag, meta description, URL slug, schema markup recommendation
- 3-5 alternative headline options using proven formulas
- Header hierarchy with keyword integration
- Internal and external linking strategy
- Featured snippet optimization
- Content gap opportunities for follow-up posts
- Social sharing snippets (Twitter, LinkedIn, email subject)

**Dispatch**:
```
Task tool:
  subagent_type: "blog-writer"
  description: "Write SEO blog post on [topic]"
  prompt: |
    Topic/Keyword: [primary keyword]
    Content Type: [listicle/how-to/thought-leadership/case-study/comparison]
    Target Audience: [who will read this]
    Business Goal: [desired reader action]
    Word Count: 2000
  mode: "bypassPermissions"
```

**Example prompts**:
- "Write a how-to guide on setting up email marketing automation for small e-commerce stores"
- "Create a listicle: 15 content marketing metrics that actually matter for B2B SaaS"
- "Write a thought leadership piece on why most companies are doing content marketing wrong"
- "Case study format: How a DTC brand grew from $0 to $1M in organic traffic in 18 months"

### Newsletter Writer (`newsletter-writer`)

Creates email newsletters with strategic subject lines, optimized structure, and growth tactics.

**What it produces**:
- 7-10 subject line options with preview text using proven formulas
- Full newsletter content in the right format (roundup, deep dive, curated, personal, hybrid)
- Segmentation recommendations (new, engaged, disengaged, buyers)
- 2-3 A/B test recommendations with hypotheses
- Performance benchmarks and target metrics
- Growth tactics for subscriber acquisition
- Next issue teaser

**Dispatch**:
```
Task tool:
  subagent_type: "newsletter-writer"
  description: "Draft newsletter on [topic]"
  prompt: |
    Newsletter Type: [weekly roundup/deep dive/curated/personal]
    Topic/Theme: [what this issue covers]
    Audience: [subscriber description]
    Key Points: [specific items to include]
    CTA Goal: [desired reader action]
  mode: "bypassPermissions"
```

**Example prompts**:
- "Write a weekly marketing roundup newsletter for SaaS founders covering this week's top AI and marketing news"
- "Create a deep-dive newsletter explaining the impact of Google's latest algorithm update on content strategy"
- "Draft a personal update newsletter for a solopreneur sharing lessons from launching their first online course"
- "Build a curated links newsletter for developers interested in DevOps and cloud infrastructure"

### SEO Optimizer (`seo-optimizer`)

Performs comprehensive SEO audits with prioritized, specific recommendations.

**What it produces**:
- On-page SEO scorecard (10 elements, each scored ✅/⚠️/❌)
- Readability analysis (Flesch-Kincaid, sentence length, paragraph structure)
- Content gap analysis (vs. search intent, competitors, PAA questions)
- Priority recommendations (P0 Critical → P3 Nice to Have) with exact fixes
- Keyword clustering and topic map for content strategy
- AI Overview and featured snippet targeting opportunities
- Technical SEO notes (page speed, mobile, schema, crawlability)
- Rewritten title tags, meta descriptions, and headers (not just "optimize" — the actual new copy)

**Dispatch**:
```
Task tool:
  subagent_type: "seo-optimizer"
  description: "SEO audit of [content/keyword]"
  prompt: |
    Content to Audit: [file path or paste content]
    Primary Keyword: [target keyword]
    Competitor URLs: [if available]
    Business Context: [what this content should achieve]
  mode: "bypassPermissions"
```

**Example prompts**:
- "Audit this blog post for SEO: /path/to/article.md — target keyword is 'email marketing automation'"
- "Build a keyword strategy for a new fitness app targeting 'home workout' queries"
- "Analyze why this page isn't ranking for 'best CRM for small business' and recommend fixes"
- "Create a topic cluster map for a B2B SaaS company entering the 'project management' space"

### Content Repurposer (`content-repurposer`)

Transforms one piece of content into platform-native assets for maximum distribution.

**What it produces**:
- Content atom map (insights, data points, stories, quotes, frameworks extracted)
- Twitter/X thread (5-12 tweets with hook, body, CTA)
- LinkedIn posts (2-3 variants: story, framework, hot take)
- Instagram carousel copy deck (7-10 slides with design direction)
- YouTube video script with metadata (title, description, tags, chapters)
- Podcast episode outline with show notes
- Email newsletter snippet
- 14-day distribution calendar with daily action items
- Performance tracking targets by platform

**Dispatch**:
```
Task tool:
  subagent_type: "content-repurposer"
  description: "Repurpose [content] for multi-platform distribution"
  prompt: |
    Source Content: [file path or paste content]
    Source Format: [blog/podcast/video/webinar]
    Target Platforms: [twitter, linkedin, instagram, youtube, podcast, email]
    Brand Voice: [tone guidelines]
    Goals: [awareness/engagement/traffic/leads]
  mode: "bypassPermissions"
```

**Example prompts**:
- "Turn this 2,000-word blog post into a Twitter thread, LinkedIn post, and Instagram carousel"
- "Repurpose this podcast transcript into a blog post, social content, and newsletter section"
- "Create a full distribution package for this webinar recording — social, email, and YouTube"
- "Atomize this case study into 14 days of social media content"

## Slash Command

Use `/create-content` for quick access:

```
/create-content Write a blog post about remote team management best practices
```

```
/create-content --type newsletter Weekly AI roundup for marketing professionals
```

```
/create-content --type seo Audit this post: /docs/blog/email-guide.md
```

```
/create-content --type repurpose Turn this into social content: /docs/blog/case-study.md
```

```
/create-content Full content package on "how to start a podcast in 2026"
```

## Frameworks Included

| Framework | Used In | Best For |
|-----------|---------|----------|
| **SERP Intent Analysis** | Blog Writer, SEO Optimizer | Matching content to search intent |
| **Content Atomization** | Content Repurposer | Breaking content into platform-ready pieces |
| **E-E-A-T Signals** | SEO Optimizer, Blog Writer | Building topical authority and trust |
| **Topic Clustering** | SEO Optimizer | Content strategy and internal linking |
| **Subject Line Formulas** | Newsletter Writer | Email open rate optimization |
| **Hook Patterns** | Blog Writer, Content Repurposer | First-line engagement across formats |
| **PAS/AIDA/BAB** | Blog Writer, Newsletter Writer | Structural frameworks for persuasive writing |
| **AI Overview Optimization** | SEO Optimizer | Modern search visibility |

## Reference Library

Deep domain knowledge is available in the `references/` directory:
- **seo-best-practices.md** — 2026 SEO patterns, E-E-A-T methodology, keyword research process, AI Overview strategy, technical SEO requirements
- **content-frameworks.md** — 50+ headline formulas, 10+ intro hooks, transition patterns, storytelling structures, CTA templates
- **editorial-calendar.md** — Monthly planning templates, content pillar strategy, topic cluster mapping, publishing cadence, content audit framework

## Tips for Best Results

1. **Be specific about your audience**: "SaaS founders with $1-5M ARR" is better than "business owners"
2. **State your goal**: Traffic, leads, sales, brand awareness — each needs different content
3. **Provide context**: Existing content, competitor URLs, brand guidelines — more context = better output
4. **Start with blog-writer, then chain**: Write → Optimize → Repurpose for maximum value from one topic
5. **Use SEO Optimizer on existing content**: Quick wins often come from optimizing what you already have
