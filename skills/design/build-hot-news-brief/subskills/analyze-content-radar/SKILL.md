---
name: analyze-content-radar
description: 在内存中只基于最终入选新闻生成最多3个有真实证据的中文内容选题。仅由 build-hot-news-brief 在
  content_radar 或 both 模式执行；不搜索、不运行脚本、不虚构热度指标。
disable-model-invocation: true
---

# 分析内容选题

## Mission

把最终新闻转为可创作但不夸大的受众、角度、标题和内容切口。

## When to use

- 仅在 `content_radar` 或 `both` 模式执行。
- 最终新闻集合确定后执行。

## Hard constraints

- 每项绑定最终新闻中的真实证据。
- 不宣称爆款、全网排名、阅读量、播放量或互动量。
- 低可信内容平台只能辅助探索，不能单独支撑高影响事实。

## Core workflow

从不同故事或不同切口生成最多3个选题，明确目标受众和可验证的内容入口。

## Output format

每项包含选题角度、受众、建议标题、内容切口及证据编号。

## Done criteria

- 最多3项且证据全部来自最终新闻。
- 不含虚构热度、事实夸大或脱离新闻的断言。
