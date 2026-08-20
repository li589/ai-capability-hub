---
name: summarize-hot-news
description: 在内存中只基于最终入选新闻生成1–3条有真实证据的中文短总结。仅由 build-hot-news-brief
  在价值评估后执行；不搜索、不读取淘汰候选、不运行脚本、不生成长报告。
disable-model-invocation: true
---

# 总结热点新闻

## Mission

把最终新闻压缩成客户可快速阅读的事实短句。

## When to use

- 所有输出模式在最终新闻选定后执行。
- 0条新闻时返回空总结。

## Hard constraints

- 只使用最终入选新闻。
- 最多3条，每条不超过80个中文字符。
- 每条绑定真实 `record_id`；不加入预测、热度、互动、因果或无证据数字。

## Core workflow

归纳不同故事的共同变化或最重要事实，优先覆盖高分且互不重复的新闻。

## Output format

向主Skill返回 `text` 与 `evidence_record_ids`。

## Done criteria

- 所有证据编号都在最终新闻中。
- 无搜索、终端、文件或长篇扩写。
