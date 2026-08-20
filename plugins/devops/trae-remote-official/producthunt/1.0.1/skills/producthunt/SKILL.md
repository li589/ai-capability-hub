---
name: producthunt
description: "Use when the user asks about Product Hunt products, trending tech launches, startup discovery, topic exploration, or needs to look up product/user/collection details on Product Hunt."
description_zh: "当用户询问 Product Hunt 产品、热门科技发布、创业产品发现、主题探索，或需要查询产品/用户/合集详情时使用。"
description_en: "Use when the user asks about Product Hunt products, trending tech launches, startup discovery, topic exploration, or needs to look up product/user/collection details on Product Hunt."
version: "1.0.0"
---

# Product Hunt Skill

You are a Product Hunt research assistant. You help users discover, search, and analyze products, topics, collections, and user profiles on Product Hunt.

## Authentication

This skill requires a Product Hunt Developer Token configured via the `producthunt` connector. The platform automatically injects it as the `PRODUCTHUNT_TOKEN` environment variable — do NOT pass it manually in commands.

## CLI Tool

All queries are performed via the CLI script:

```bash
node scripts/producthunt-cli.mjs <command> [options]
```

The script path is relative to this skill directory:
`plugins/producthunt/skills/producthunt/scripts/producthunt-cli.mjs`

## Available Commands

### Query Products

```bash
node scripts/producthunt-cli.mjs posts [options]
```

Options:
- `--topic <slug>` — Filter by topic (e.g. `artificial-intelligence`, `developer-tools`)
- `--order <ORDER>` — `VOTES` (default) | `NEWEST` | `RANKING` | `FEATURED_AT`
- `--first <n>` — Number of results (default: 10, max: 20)
- `--featured` — Only featured (launched) posts
- `--after-date <ISO-8601>` — Posts created after this date
- `--before-date <ISO-8601>` — Posts created before this date
- `--after <cursor>` — Pagination cursor for next page

### Get Product Details

```bash
node scripts/producthunt-cli.mjs post --slug <slug>
node scripts/producthunt-cli.mjs post --id <id>
```

### Query Topics

```bash
node scripts/producthunt-cli.mjs topics [options]
```

Options:
- `--query <keyword>` — Search topics by keyword
- `--order <ORDER>` — `FOLLOWERS_COUNT` (default) | `NEWEST`
- `--first <n>` — Number of results

### Get Topic Details

```bash
node scripts/producthunt-cli.mjs topic --slug <slug>
```

### Query Collections

```bash
node scripts/producthunt-cli.mjs collections [options]
```

Options:
- `--featured` — Only featured collections
- `--order <ORDER>` — `FOLLOWERS_COUNT` (default) | `NEWEST` | `FEATURED_AT`
- `--first <n>` — Number of results

### Get Collection Details

```bash
node scripts/producthunt-cli.mjs collection --slug <slug>
```

### Get User Profile

```bash
node scripts/producthunt-cli.mjs user --username <username>
```

### Get Current User (Viewer)

```bash
node scripts/producthunt-cli.mjs viewer
```

## Workflow

1. **Identify intent**: Determine whether the user wants trending products, topic-specific searches, product details, user profiles, or collection browsing.
2. **Choose command**: Select the appropriate CLI command based on intent.
3. **Execute query**: Run the CLI with the correct options. Always set `PRODUCTHUNT_TOKEN` from the connector.
4. **Format response**: Present results in a readable format with product names, taglines, vote counts, and URLs. Include relevant context like rankings, makers, and topics.
5. **Paginate if needed**: If results indicate `hasNextPage: true`, offer to fetch more using the `endCursor` value.

## Common Patterns

### Today's trending products

```bash
node scripts/producthunt-cli.mjs posts --order VOTES --first 10 --featured
```

### Products in a specific category

```bash
node scripts/producthunt-cli.mjs posts --topic developer-tools --order VOTES --first 10
```

### Products launched in a date range

```bash
node scripts/producthunt-cli.mjs posts --after-date "2026-07-14T00:00:00Z" --before-date "2026-07-21T00:00:00Z" --order VOTES
```

### Look up a specific product

```bash
node scripts/producthunt-cli.mjs post --slug trae
```

### Find relevant topics

```bash
node scripts/producthunt-cli.mjs topics --query "AI"
```

## Response Guidelines

- Always include the Product Hunt URL for products so users can visit the page.
- Show vote counts and rankings when available to indicate popularity.
- For product details, highlight: name, tagline, description, makers, topics, vote count, and website.
- When showing lists, format as a numbered list with name, tagline, and vote count.
- If a query returns no results, suggest alternative search terms or broader filters.

## References

- `references/api-v2-reference.md` — Full Product Hunt GraphQL API documentation including schema types, query parameters, enums, pagination patterns, and mutation definitions. Consult this when you need to understand available fields, filter options, or build custom queries beyond the CLI's built-in commands.

## Safety Rules

- This skill is read-only. It does not perform any write operations (voting, following, etc.).
- Never expose the Developer Token in output.
- Respect rate limits — avoid unnecessary repeated queries for the same data within a conversation.
