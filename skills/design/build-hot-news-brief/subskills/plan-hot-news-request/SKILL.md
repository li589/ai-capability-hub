---
name: plan-hot-news-request
description: 在内存中解析隐式新闻意图、深度模式强触发词、热点快报主题、输出模式和固定查询角色，并执行敏感范围守卫。仅由
  build-hot-news-brief 在 connector_ready 阶段执行；不搜索、不运行脚本。
disable-model-invocation: true
---

# 规划热点快报请求

## Mission

形成当前回合唯一的主题、模式、时间窗口和查询计划。

## When to use

- 仅在连接检查通过后执行。
- 解析未提 Skill 名的新闻意图、深度强触发词及四种输出意图。

## Hard constraints

- 所有近期新闻意图优先归属主 Skill；“深度模式”“深度搜索”“深度检索”“深搜”“deep mode”“deep search”固定解析为 `search_mode=deep`。
- 默认 `search_mode=fast`；只有用户明确要求时使用 `deep`，深度强触发不得降级。
- 深度强触发词后没有主题时只返回主题追问，搜索调用数为0。
- 快速模式恰好1个查询；深度模式固定6个不同角色，不增加第7个。
- 敏感主题立即停止且搜索调用数为0。
- 固定中文可信信源优先、近7天、最多10条。

## Core workflow

先识别隐式新闻意图与深度强触发词；规范主题并删除模式指令词；缺少主题时返回追问；否则确定输出模式并生成快速1类或深度固定6类查询。

## Output format

向主Skill返回内存计划：`topic`、`search_mode`、`output_mode`、`query_roles`、`logical_batch_count`。

## Done criteria

- 快速计划1批，深度计划6批且角色唯一。
- 深度强触发词没有被快速模式或通用搜索覆盖；无主题时未生成查询。
- 未进行工具、终端或文件操作。
