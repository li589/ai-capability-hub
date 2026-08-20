---
name: ensure-hot-news-connector
description: 在内存中检查热点快报所需八爪鱼连接及两个只读工具。仅由 build-hot-news-brief 在 initialized
  阶段执行；不搜索、不运行脚本、不创建文件。
disable-model-invocation: true
---

# 检查热点快报连接

## Mission

确认宿主已暴露 `list_platforms` 与 `search_platform_content`，决定是否可以进入请求规划。

## When to use

- 每次热点快报开始时执行。
- 工具缺失或连接异常时停止流程。

## Hard constraints

- 只检查工具是否可用，不读取或显示 `.mcp.json`、API Key、Header及鉴权响应。
- 正常请求不调用 `list_platforms`；该工具仅由采集职责在诊断时使用。
- 未就绪时搜索调用数必须为0。

## Core workflow

检查两个工具的宿主暴露状态；均存在则在内存中标记 `connector_ready`，否则输出缺失工具和恢复提示。

## Output format

向主Skill返回内存状态：`ready`、`missing_tools`、`next_action`。

## Done criteria

- 两个工具均存在时才能继续。
- 全程无MCP调用、终端调用、文件和凭证输出。
