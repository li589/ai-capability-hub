# Frontmatter Skeleton

Copy this template for every distilled document. All keys and values in English.

```yaml
---
title: "<Concise English title describing the core distilled knowledge>"
date: YYYY-MM-DD
aliases:
  - "<search alias 1>"
  - "<search alias 2>"
tags:
  - distilled
  - scene/<scene-type>
  - tech/<technology>
  - topic/<domain>
  - difficulty/<level>
scene: <project-wrapup | bug-retrospective | refactoring | tech-learning | universal>
source_scope: <current-chat | today-all | specific-files>
confidence_summary: <high | medium | low>
lang: <en | zh>
---
```

## Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `title` | yes | string | Concise English title. Use descriptive noun phrases. |
| `date` | yes | date | Extraction date in `YYYY-MM-DD` format. |
| `aliases` | yes | list | 1-3 alternative search terms in English. |
| `tags` | yes | list | Hierarchical tags per `tags-taxonomy.md`. Min 4 (distilled + scene + tech + difficulty). |
| `scene` | yes | string | One of: `project-wrapup`, `bug-retrospective`, `refactoring`, `tech-learning`, `universal`. |
| `source_scope` | yes | string | One of: `current-chat`, `today-all`, `specific-files`. |
| `confidence_summary` | yes | string | Highest confidence among all extraction points: `high`, `medium`, or `low`. |
| `lang` | yes | string | Body language: `en` or `zh`. Frontmatter always English regardless. |

## Rules

1. **All frontmatter in English** — field names, tag values, title, aliases, scene, scope — always English even when body is Chinese.
2. **Title style** — Use noun phrases: "Race Condition in Async Task Queue", not "I learned about race conditions".
3. **Aliases** — Include abbreviated forms, alternative phrasings, or technology-specific keywords that aid Obsidian search.
4. **Tags** — Follow `references/tags-taxonomy.md`. Always include `distilled` as the first tag.
5. **Date** — Use the actual extraction date, not the date the source event happened.
