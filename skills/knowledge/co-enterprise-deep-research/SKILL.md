---
name: co-enterprise-deep-research
description: |
  Market and industry research with web_search, /research command, and MCP.
  Benchmarking, trend analysis, and competitive intelligence for enterprise context.
  Use when RESEARCHING industry trends, benchmarking competitors, gathering market data,
  or collecting evidence for enterprise transformation decisions.
tu_tools:
  - key: deep-research
    name: Deep Research MCP
install_source: official
install_method: download
skill_id: official_giH7mkbH
enabled_at: 1787232861607
version: 1.0.0
name_zh: 联合企业深度研究
---

# Deep Research (Enterprise)

Market and industry research with multi-tool search.

## Research Tools (Priority Order)

### 1. `web_search` (Built-in — Always Available)
```
web_search("enterprise digital transformation ROI benchmark 2025")
web_search("operating model redesign best practices McKinsey")
```

### 2. `/research` command (CLI — Interactive)
```
/research What are the key success factors for enterprise-wide transformation programs?
```

### 3. `deep-research` MCP (When Configured)
Full pipeline research.

## Deliverables

- `results/research-notes.md`: findings with source attribution.

## Quality Gates

- [ ] 3+ trusted sources.
- [ ] Key data cross-validated.
- [ ] Single-source claims marked ⚠️.

If any gate fails: identify the issue, fix, and re-validate.

## Gotchas

- `web_search` は常に利用可能。MCP なしでもリサーチは実行できる
- 検索は日英両方で行うこと
- 収集データは各ラウンド後にファイルに保存

## Validation Loop

1. リサーチ実行 → 2. 3+ソース確認 → 3. 合格後のみ完了
