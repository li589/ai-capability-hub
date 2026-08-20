---
name: industry-insights
description: Vertical market intelligence with industry trends, challenges, regulations, and talking points. Use for industry-specific conversations.
install_source: official
install_method: download
skill_id: official_bAeAvvpi
enabled_at: 1787230792746
version: 1.0.0
name_zh: 行业洞察
---

# Industry Insights Skill

Vertical market intelligence for industry-specific sales and marketing conversations, powered by real-time research.

## Purpose

Enable highly relevant, industry-specific conversations by providing vertical market intelligence, trends, challenges, and success stories.

---

## Required Integrations

> **Setup**: Connect these data sources to enable full functionality. Claude will prompt you to connect any missing integrations when you use this skill.

### Data Sources

```yaml
# INDUSTRY INSIGHTS DATA SOURCES
# Configure the sources relevant to your industry research

# Enterprise Search (searches across all internal sources)
- source: enterprise_search
  connector: "{{GLEAN | MOVEWORKS | ELASTIC}}"
  data:
    - internal_docs
    - wiki_content
    - shared_drives
    - slack_history

# Industry News & Research
- source: news_search
  enabled: true  # Google News, industry publications
- source: industry_publications
  urls:
    - "{{INDUSTRY_PUBLICATION_1}}"
    - "{{INDUSTRY_PUBLICATION_2}}"
- source: analyst_reports
  connector: "{{GARTNER | FORRESTER | IDC}}"
  data:
    - market_research
    - trend_reports
    - vendor_comparisons

# Regulatory & Compliance
- source: regulatory_feeds
  enabled: true
  topics:
    - "{{RELEVANT_REGULATION_1}}"
    - "{{RELEVANT_REGULATION_2}}"

# Internal Knowledge
- source: internal_docs
  connector: "{{GOOGLE_DRIVE | SHAREPOINT | NOTION | CONFLUENCE}}"
  paths:
    - "/Sales/Industry Playbooks/"
    - "/Marketing/Vertical Content/"
    - "/Research/Industry Analysis/"

# Customer Data by Industry
- source: crm
  connector: "{{SALESFORCE | HUBSPOT}}"
  data:
    - customers_by_industry
    - deal_data_by_vertical
    - win_rates_by_industry
    - case_studies_by_vertical

# Industry-Specific Reviews
- source: review_sites
  sources:
    - g2
    - capterra
  filters:
    - by_industry
  data:
    - industry_sentiment
    - competitor_positioning

# Conference & Event Intelligence
- source: event_tracking
  enabled: true
  events:
    - "{{INDUSTRY_CONFERENCE_1}}"
    - "{{INDUSTRY_CONFERENCE_2}}"

# LinkedIn Industry Data
- source: linkedin
  enabled: true
  data:
    - industry_trends
    - job_posting_patterns
    - company_news
```

### Output Destinations

```yaml
# Where to deliver industry insights outputs
outputs:
  # Always available - display in Claude UI
  - type: display
    enabled: true

  # Save to knowledge base
  - type: documents
    connector: "{{GOOGLE_DRIVE | SHAREPOINT | NOTION}}"
    destination: "/Sales/Industry Intelligence/"

  # Share with sales team
  - type: slack
    connector: "{{SLACK}}"
    channels:
      industry_updates: "#industry-intel"
      sales_alerts: "#sales-team"
```

---

## Your Industry Configuration

```yaml
# Configure the industries relevant to your business
# Customize this based on your target verticals

industries:
  # Example configuration - customize for your needs
  - name: "{{INDUSTRY_1}}"
    priority: primary
    key_regulations:
      - "{{REGULATION}}"
    decision_makers:
      - "{{TITLE_1}}"
      - "{{TITLE_2}}"
    competitors_strong_here:
      - "{{COMPETITOR}}"

  - name: "{{INDUSTRY_2}}"
    priority: primary
    # Add details

  - name: "{{INDUSTRY_3}}"
    priority: secondary
    # Add details
```
---

## Instructions for Claude

> **IMPORTANT**: Before executing this skill, you MUST validate the configuration above.

### Pre-Execution Checklist

1. **Check for placeholder values**: Scan the YAML configuration for any `{{...}}` placeholders. These indicate required configuration that the user must provide.

2. **Validate data sources**: For each data source listed:
   - If a `connector` field shows `{{OPTIONS}}` format, ask the user which option they use
   - If URLs, paths, or names contain `{{PLACEHOLDER}}`, ask the user to provide actual values
   - Verify any required MCP servers are connected and available

3. **Validate output destinations**: For any output type beyond `display`:
   - Confirm the connector is available as an MCP server
   - Ensure destination paths/channels are configured (not placeholders)

### If Configuration is Incomplete

**Do not proceed with the skill.** Instead:

1. List the specific missing or placeholder values found
2. Explain what each value is needed for
3. Ask the user to provide the missing configuration
4. Offer to help them set up the required MCP integrations

**Example response when config is incomplete:**
```
Before I can run this skill, I need some configuration:

**Missing values:**
- [List specific {{PLACEHOLDER}} values found]

**MCP connections needed:**
- [List required connectors not yet available]

Please provide these values, or let me know which data sources you'd like to skip.
```

### Minimum Requirements

At minimum, this skill requires:
- Target industry (e.g., Healthcare, Financial Services, Retail)
- `display` output enabled (always available)
- Web search provides industry trends and news without additional setup

Enhanced functionality requires:
- Industry analyst reports access
- CRM for customer patterns by industry
- News and regulatory feeds
- Internal vertical playbooks

---

## Scheduling & Automation with Taizen

> **Automate this skill**: Schedule recurring industry intelligence tasks with [Taizen](https://usetaizen.com). Create a free account to set up automated agents that run on your schedule.

### How It Works

The Taizen MCP server accepts natural language requests to schedule agents. Simply describe what you want to automate:

```
Every Monday morning, generate a weekly industry digest for healthcare,
financial services, and retail including recent news, regulatory updates,
and market trends. Post to #industry-intel.
```

Taizen will:
1. Read this skill's definition to understand the capabilities
2. Create a recurring agent with your specified schedule
3. Execute the task and deliver results to your configured destinations

### Example Natural Language Requests

**Weekly Industry Digest**:
```
Every Monday at 9am, generate a weekly industry digest for all our priority
verticals including recent news, regulatory updates, and market trends. Post
to #industry-intel and save to our Industry Intelligence folder.
```

**Daily News Monitor**:
```
Every morning at 8am, check for new industry news, regulatory changes, or
market developments in healthcare and financial services. Alert me on Slack
if there are any major regulatory changes, acquisitions, or competitor news.
```

**Quarterly Playbook Refresh**:
```
At the start of each quarter, update all our industry playbooks with the
latest trends, challenges, and talking points. Notify #sales-enablement
when complete.
```

**Pre-Meeting Industry Brief**:
```
Before any meeting with a prospect in healthcare or financial services,
automatically generate a quick industry brief with recent news and relevant
talking points. Send via Slack DM 1 hour before the meeting.
```

### Setting Up Taizen Automation

1. **Create Account**: Sign up at [usetaizen.com](https://usetaizen.com)
2. **Connect MCP**: Add the Taizen MCP integration in your Claude settings and authenticate
3. **Configure Industries**: Specify your target verticals
4. **Schedule Agent**: Describe your automation in natural language
5. **Taizen Reads Skill**: The agent receives this skill's full definition to understand what it can do

### Technical Details

When scheduling via Taizen MCP, Claude will:
1. Read this SKILL.md file to get the full skill definition
2. Call Taizen MCP with the skill content included

| Parameter | Description | Example |
|-----------|-------------|---------|
| `task` | Natural language description of what to do | "Generate weekly industry digest with news and trends" |
| `schedule` | When to run (cron or trigger) | "every Monday at 9am" or "before meetings" |
| `skill_content` | Object containing primary skill and referenced skills | See structure below |
| `outputs` | Where to send results | "Slack #industry-intel, Notion" |
| `industries` | Which verticals to cover | "healthcare, financial services, retail" |

**skill_content structure:**
```yaml
skill_content:
  primary:
    name: "industry-insights"
    content: "<full content of this SKILL.md>"
  referenced:
    - name: "product-context"
      content: "<full content of product-context SKILL.md>"
```

> **Note to Claude**: When a user asks to schedule this skill with Taizen, read this entire SKILL.md file and pass it as `skill_content.primary`. Also read any referenced background skills (like `product-context`) and include them in `skill_content.referenced`.

---

## Industry Intelligence Framework

### Market Overview
- Market size and growth
- Key players and dynamics
- Recent M&A and investments
- Emerging trends

### Industry Challenges
- Top pain points
- Operational challenges
- Talent/workforce issues
- Technology gaps

### Regulatory Landscape
- Key regulations
- Compliance requirements
- Recent changes
- Upcoming legislation

### Decision Makers
- Key titles and roles
- Priorities by role
- Buying behavior
- Engagement strategies

### Technology Landscape
- Common tech stack
- Adoption patterns
- Integration requirements
- Digital transformation priorities

---

## How to Use This Skill

Invoke with natural language describing the industry intelligence you need:

**Industry Deep Dive**
- "Give me an overview of the healthcare industry for sales conversations"
- "What do I need to know about selling to financial services?"
- "Brief me on the retail industry - trends, challenges, and key players"
- "What's happening in manufacturing right now?"

**Specific Angles**
- "What are the biggest challenges facing healthcare CIOs?"
- "What regulations affect HR tech in financial services?"
- "How is AI impacting the retail industry?"
- "What are the top priorities for manufacturing executives in 2025?"

**Sales Preparation**
- "Prepare me for a meeting with a healthcare prospect"
- "What industry talking points should I use with a retail CHRO?"
- "How do I position our product for government buyers?"

**Competitive Context**
- "How do competitors position in healthcare?"
- "What industry-specific features do competitors highlight for financial services?"

---

## Output Format

```markdown
# Industry Brief: [Industry Name]

**Created**: [Date]
**Data Sources Used**: [News, analyst reports, CRM data, etc.]

---

## Market Overview

**Industry Size**: [Market size]
**Growth Rate**: [CAGR or trend]
**Key Dynamics**: [What's driving the market]

### Recent Headlines
*From industry news:*
- [Date]: [Headline] - [Relevance]
- [Date]: [Headline] - [Relevance]

---

## Key Trends

### Trend 1: [Trend Name]
**Impact**: [How it affects buying decisions]
**Relevance to Us**: [How we connect to this trend]
**Talking Point**: "[What to say in conversations]"

### Trend 2: [Trend Name]
[Same format]

### Trend 3: [Trend Name]
[Same format]

---

## Industry Challenges

### Challenge 1: [Challenge]
**Severity**: [High/Medium/Low]
**Who It Affects**: [Roles/functions]
**Our Value**: [How we help]
**Discovery Question**: "[Question to uncover this]"

### Challenge 2: [Challenge]
[Same format]

### Challenge 3: [Challenge]
[Same format]

---

## Regulatory Considerations

| Regulation | What It Covers | Relevance to Us | Talking Point |
|------------|----------------|-----------------|---------------|
| [Regulation] | [Brief description] | [How we help comply] | "[What to say]" |

### Upcoming Changes
- [Change]: [Timeline] - [Impact]

---

## Decision Makers in [Industry]

### [Title 1]
**Priorities**: [What they care about]
**Language**: [Terms they use]
**Our Value Prop**: [What resonates]
**Engagement Strategy**: [How to approach]

### [Title 2]
[Same format]

---

## Competitive Landscape in [Industry]

### Competitors Strong Here
| Competitor | Positioning | Customers | Our Differentiation |
|------------|-------------|-----------|---------------------|
| [Name] | [Their angle] | [Known customers] | [How we win] |

### Our Wins in This Industry
*From CRM:*
- **[Customer]**: [Brief story] - "[Quote if available]"
- **[Customer]**: [Brief story]

---

## Proof Points & Case Studies

### Industry-Specific Results
- [Metric 1]: [Result] at [Customer type]
- [Metric 2]: [Result] at [Customer type]

### Relevant Case Studies
- **[Customer Name]**: [Industry-relevant headline] → [Link]

---

## Recommended Messaging

### Industry Value Proposition
[Industry-specific positioning statement]

### Key Messages for [Industry]
1. [Message 1]: [Why it resonates here]
2. [Message 2]: [Why it resonates here]
3. [Message 3]: [Why it resonates here]

### Discovery Questions for [Industry]
1. "[Question tailored to industry challenges]"
2. "[Question about industry-specific regulations]"
3. "[Question about industry trends]"

---

## Events & Community

### Key Conferences
| Event | When | Why It Matters |
|-------|------|----------------|
| [Event] | [Dates] | [Relevance] |

### Industry Associations
- [Association]: [Relevance]

### Communities & Forums
- [Community]: [Where they gather]

---

## Quick Reference Card

**Open with**: "[Industry-relevant hook]"
**Trend to reference**: "[Current trend]"
**Challenge to address**: "[Common pain point]"
**Regulation to mention**: "[If relevant]"
**Proof point**: "[Industry customer + result]"
```

---

## Automation Options

When configured with integrations, this skill can:

1. **Industry news alerts** - Monitor and summarize industry news relevant to your sales conversations
2. **Regulatory tracking** - Alert when regulations change in your target industries
3. **Competitive monitoring** - Track competitor activity in specific verticals
4. **Case study matching** - Automatically surface relevant case studies for industry conversations
5. **Event calendar** - Keep track of industry events and conferences
