---
name: clean-rank-hot-news
description: 在内存中把热点快报1批或6批原始结果清洗为严格近7天、去重、可信且最多40条的候选池。仅由 build-hot-news-brief
  在 collected 阶段执行；不搜索、不运行脚本、不生成总结。
disable-model-invocation: true
---

# 清洗热点新闻候选

## Mission

形成当前回合唯一可进入价值评估的候选集合。

## When to use

- 全部计划批次结束后执行。
- 鉴权或额度错误时不执行。

## Hard constraints

- 只处理大小写准确的 `webPages.value`。
- 必须有标题、HTTP(S) URL和有效 `datePublished`；排除未来日期和7天外记录。
- 清除跟踪参数，去重规范URL，聚类转载，每域名最多2条。
- 排除导航、广告、低相关、低可信和敏感内容；候选最多40条。

## Core workflow

在内存中合并成功批次，依次执行字段、时间、相关性、来源、URL和故事去重门禁。

## Output format

向主Skill返回最多40条候选及原始数、有效数、去重数、来源分布和排除原因。

## Done criteria

- 候选标题、URL、来源和日期均来自MCP记录。
- 无重复故事、超期内容、终端或文件操作。
