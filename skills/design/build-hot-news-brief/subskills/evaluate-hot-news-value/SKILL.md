---
name: evaluate-hot-news-value
description: 在内存中从热点快报候选池选择并排序最多10条高价值新闻。仅由 build-hot-news-brief 在 cleaned
  阶段执行；只评分真实候选，不搜索、不运行脚本、不生成额外事实。
disable-model-invocation: true
---

# 评估热点新闻价值

## Mission

形成总结、专业分析和最终回复共同使用的唯一新闻集合。

## When to use

- 候选清洗完成后始终执行。
- 0条候选时直接返回空集合。

## Hard constraints

- 只接受候选中的真实记录，不修改标题、URL、来源和日期。
- 总分固定为相关性35、来源25、时效15、影响15、增量10。
- 最终最多10条、每域名最多2条、同一故事只保留1条。
- 不足10条按实际数量交付。

## Core workflow

对每个候选计算五项分数，按总分、发布时间和来源层级排序，再执行故事与域名上限。

## Output format

向主Skill返回最终新闻及其 `record_id`、总分和分项分。

## Done criteria

- 未知、重复或字段被修改的记录不能入选。
- 最终集合成为后续内容的唯一证据底座。
