---
name: collect-hot-news-data
description: 直接调用八爪鱼 search_platform_content
  完成热点快报唯一采集，快速模式1批、深度模式固定6批并发优先；list_platforms仅用于诊断。仅由 build-hot-news-brief 在
  planned 阶段执行，是唯一拥有MCP工具的内部Skill。
disable-model-invocation: true
---

# 采集热点新闻

## Mission

以最少宿主边界取得当前回合所需的全部真实新闻记录。

## When to use

- 仅在请求计划和敏感门禁通过后执行。
- 连接或来源异常时才调用 `list_platforms` 诊断。

## Hard constraints

- 只允许 `list_platforms` 与 `search_platform_content`。
- 正常快速模式直接调用1次搜索；正常深度模式同时发出6次搜索。
- 每批固定 `count=30`、`freshness=oneWeek`、`summary=false`、`needCount=false`。
- 正常响应不运行终端、不落盘、不重试普通错误、不增加第7批。
- 宿主自动落盘时只允许一次内置压缩器读取全部响应文件；禁止多轮结构探测、jq、Python或逐批解析。
- 鉴权或额度错误立即停止所有批次并输出脱敏提示。

## Core workflow

按计划直接调用搜索；深度模式一次提交6个调用，宿主不支持并发时才按编号顺序执行。正常响应保留在内存；超大文件响应一次压缩为最多40条紧凑记录。

## Output format

向主Skill返回：各批 `webPages.value`、批次状态、实际搜索数和失败原因分类。

## Done criteria

- 快速实际搜索数为1；深度逻辑批次为6且无额外调用。
- 没有主动写入原始响应；宿主落盘时压缩器调用数不超过1。
