---
name: amazon-collector-skill-family
version: "1.3.2"
display_name: 八爪鱼|亚马逊商品数据抓取
description: 通过八爪鱼 MCP 采集 Amazon 商品数据并导出 CSV。用于按关键词和站点完成商品列表、详情、评论的端到端采集，也用于按 ASIN 单独采集详情或评论、仅采集关键词商品列表，或把已有阶段数据导出为 CSV；支持 AU、CA、UK、US、IN、DE、SE、NL、BE、JP、IT、FR、ES、PL、TR、MX、AE、SA、IE、SG、BR、EG 站点。
---

# Amazon 商品采集（八爪鱼）

## Mission

将用户的关键词或 ASIN 请求路由到一个明确的采集流程，通过已配置的八爪鱼 MCP 生成可恢复、可核验的阶段结果，并交付 UTF-8-BOM CSV。根 `SKILL.md` 是唯一主编排器；内部 Skill 只执行所属阶段，完成后必须返回根编排器。

## When to use

- 关键词完整采集：读取 `subskills/amazon-keyword-collector/SKILL.md`，依次采集列表、详情、评论并导出 CSV。
- 关键词列表：读取 `subskills/amazon-product-list/SKILL.md`。
- ASIN 详情：读取 `subskills/amazon-product-details/SKILL.md`。
- ASIN 评论：读取 `subskills/amazon-product-reviews/SKILL.md`。
- 已有运行结果导出：读取 `subskills/amazon-csv-export/SKILL.md`，不得创建 MCP 任务。

宿主支持子 Skill 时逐阶段调用；不支持时按上述路径读取对应 `SKILL.md` 并执行。不要一次加载所有内部 Skill。

## Hard constraints

- 在首次 MCP 调用前，用中文明确提示：`免费版与个人版通过 MCP 调用每周最多 2000 条；团队版不限条数。`
- 将该限制视为套餐提示，不臆测用户本周剩余额度；遇到额度错误时保留运行状态并建议用户检查套餐或稍后恢复。
- MCP 未加载时，引导用户添加或启用包根目录的 `mcp.json`，在连接成功前不得创建采集任务。
- API Key 只能由用户在 WorkBuddy 的安全连接配置中填写。不得在对话、日志、状态文件、CSV 或最终答复中显示或保存密钥。
- 每次运行前读取 `contracts/mcp-routing.json`、请求 schema 和当前模板的 `inputSchema`、`sourceTree`；以当前模板字段为准。
- 一个采集阶段只创建一个模板任务，传入完整规范化数组；不得拆分 ASIN、重复创建已完成任务或伪造完成状态。
- 所有阶段必须使用版本化 JSON 契约交接；只报告契约记录的 `COMPLETE`、`PARTIAL` 或 `FAILED`。
- 用户未提供必需参数时，只补问最少缺失项。关键词流程要求 `keyword`、`quantity`、`site`；ASIN 流程要求 `asins`、`site`。

## Core workflow

1. 识别完整关键词、列表、详情、评论或导出意图，并选择一个内部 Skill。
2. 验证输入；站点列表和数量边界以 `capability-catalog.json` 与 `contracts/` 为准。
3. 若流程需要 MCP，先显示套餐提示，再检查 `search_templates`、`execute_task`、`get_task_status`、`start_or_stop_task`、`export_data` 是否可用。
4. MCP 不可用时，说明需添加或启用 `mcp.json` 中的 `bazhuayu-amazon-collector` 连接，并等待连接完成；不要索取明文 API Key。
5. 读取并执行所选内部 Skill。阶段结束后校验 `contracts/stage-result.schema.json`，更新 `run-state.json`，再由根编排器决定下一阶段。
6. 完整关键词流程按 `list → details → reviews → export` 顺序执行；单项流程只执行请求的阶段。
7. 对任务 ID、批次号、终态、导出页数、ASIN 覆盖和 CSV 行数进行对账后再交付。

## Output format

返回简短中文摘要和机器状态：

```json
{
  "status": "COMPLETE|PARTIAL|FAILED",
  "workflow": "keyword|list|details|reviews|export",
  "run_id": "amazon-...",
  "files": {},
  "row_counts": {},
  "coverage": {},
  "warnings": [],
  "errors": []
}
```

若创建了 CSV，提供可点击文件路径并说明编码为 UTF-8-BOM。若为 `PARTIAL`，列出缺失 ASIN 或失败阶段；若为 `FAILED`，保留可恢复的运行目录和已记录任务身份。

## Done criteria

- 已在首次 MCP 调用前显示免费版、个人版和团队版的额度提示。
- 选中的内部 Skill 和输入契约均匹配用户意图。
- 每个云采集阶段最多创建一个任务，任务身份与终态可追溯。
- 完整关键词流程的列表、详情、评论和导出阶段均有有效契约，或明确记录部分失败。
- CSV 通过 BOM、表头宽度、行宽和行数回读检查。
- 任何产物均不含 API Key、MCP 会话 ID 或签名导出 URL 密钥。
