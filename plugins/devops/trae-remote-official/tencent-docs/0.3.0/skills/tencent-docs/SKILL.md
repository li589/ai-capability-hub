---
name: tencent-docs
description: 腾讯文档（docs.qq.com）在线文档操作。用于创建、读取、搜索、编辑和管理腾讯文档，以及处理 Word、Excel、PPT、智能文档、智能表格、知识库空间、思维导图、流程图、文件导入导出和网页剪藏。
---

# 腾讯文档 MCP 使用指南

腾讯文档插件通过 Trae connector 授权，并由 Trae 直接加载四个 MCP 服务：

| 服务 | 主要能力 |
|---|---|
| `tencent-docs` | 通用文档、文件管理、空间、智能文档、智能表格、OCR、网页剪藏 |
| `slide-mcp` | PPT 精细编辑 |
| `doc-mcp` | Word 精细编辑 |
| `sheet-mcp` | Excel 精细编辑 |

首次使用或出现鉴权错误时，阅读 `references/auth.md`。不要安装额外 MCP 客户端，不要要求用户提供 Token。

## 文档类型路由

先确认目标文档类型，再选择对应服务和参考文档。不要跨类型调用编辑工具。

| 用户意图或文档类型 | 首选工具 | 参考文档 |
|---|---|---|
| PPT、幻灯片、演示文稿 | `slide-mcp` 的 `slide_*` 工具 | `slide/entry.md` |
| Word、传统文档 | `doc-mcp` 的 `doc.*` 工具 | `doc/entry.md`、`references/docengine_references.md` |
| Excel、在线表格 | `sheet-mcp` 的 `sheet.*` 工具 | `sheet/entry.md` |
| 报告、笔记、文章、会议纪要 | `create_smartcanvas_by_mdx`、`smartcanvas.*` | `smartcanvas/entry.md` |
| 智能表格、结构化数据 | `smartsheet.*` | `references/smartsheet_references.md` |
| 思维导图 | `create_mind_by_markdown` | `references/diagram_references.md` |
| 流程图 | `create_flowchart_by_mermaid` | `references/diagram_references.md` |
| 文件、目录、权限、导入导出 | `manage.*` | `references/manage_references.md` |
| 知识库空间和节点 | 空间工具 | `references/space_references.md` |
| 图片 OCR | `ocr.*` | `references/ocr_references.md` |

## 场景工作流

### 从零创建

- PPT：按 `slide/entry.md` 生成 DESIGN 和 JSX，使用 `slide_add_page_with_jsx` 严格串行写入。
- Word：创建空文档后使用 `doc.insert_markdown`，或直接调用 `doc.create_with_markdown`。
- Excel：创建表格后使用 `sheet.set_range_value` 等批量接口。
- 报告、总结、会议纪要：优先使用 `create_smartcanvas_by_mdx`。
- 空白文件或未覆盖品类：使用 `manage.create_file`。

### 编辑已有内容

1. 从链接前缀判断类型，或调用 `manage.query_file_info`。
2. 根据类型选择 `smartcanvas.*`、`slide_*`、`doc.*`、`sheet.*` 或 `smartsheet.*`。
3. 连续三次及以上写入必须优先使用对应批量接口。

### 文件管理

- 重命名、移动、删除、复制、导入导出和权限操作使用 `manage.*`。
- 空间、节点和文件夹结构使用空间工具。
- `node_id` 同时可作为文档 `file_id`。
- 删除空间节点前确认范围；递归删除必须获得用户明确确认。

### 转换和导入

- 网页链接使用 `scrape_url`，再轮询 `scrape_progress`。
- 本地 HTML 可以先用 `node aipage_pack.js` 打包成 `.aipage`，再执行标准导入流程。
- 本地文件导入按 `manage.pre_import` → PUT 上传到返回的 URL → `manage.async_import` → `manage.import_progress` 执行。
- 公网图片可以直接调用 `ocr.*`。本地图片不要把超长 base64 粘贴进对话；若当前客户端无法安全传递文件内容，请要求用户提供可访问的图片 URL。

## PPT 核心规则

- 所有 PPT 任务都走 `slide-mcp`，禁止使用 Word 或通用文档工具修改 PPT 内部结构。
- 写操作前调用 `slide_get_info`、必要的 `slide_get_page_info` 和 `slide_get_design` 获取状态。
- 生成或修改整页时先持久化 DESIGN，再调用写工具。
- 多页 `slide_add_page_with_jsx` 必须严格串行，并显式传入互不重叠的 `page_index`。
- 完成后重新获取页面信息，核对页数、顺序、尺寸和关键内容。
- JSX 组件规范位于 `pptx-generator/references/component-*.md`，设计规范位于 `pptx-generator/references/design-principle.md`。

## 公共能力

| 场景 | 参考文档 |
|---|---|
| 获取内容、上传图片、常用组合流程 | `references/workflows.md` |
| 本地 HTML 打包和导入 | `references/aipage_references.md` |
| Word 精细编辑 | `references/docengine_references.md` |
| PPT 精细编辑 | `references/slideengine_references.md` |
| Excel 精细编辑 | `sheet/entry.md` |
| 智能表格 | `references/smartsheet_references.md` |
| 文件管理 | `references/manage_references.md` |
| 空间管理 | `references/space_references.md` |
| OCR | `references/ocr_references.md` |

## 操作约束

- 参考文档与 MCP 工具 Schema 冲突时，以 Trae 当前加载的工具 Schema 为准。
- 连续三次及以上写入必须使用批量接口，减少版本冲突和限流。
- Markdown 内容使用 UTF-8；智能文档直接传 MDX/Markdown，无需额外转换。
- `create_smartcanvas_by_mdx` 不支持 `parent_id` 时，不要伪造该参数。
- OCR 的 `image_url` 与 `image_base64` 严格二选一。
- 异步任务按接口建议间隔轮询，达到失败状态或超时后停止。
- 找不到用户请求对应的能力时，如当前工具集中存在 `report_unsupported_feature`，可调用它上报；不得伪造成功结果。

## 错误排查

| 错误码 | 含义 | 处理 |
|---|---|---|
| `400006` | Token 鉴权失败 | 按 `references/auth.md` 在 Trae 中重新连接 |
| `400007` | VIP 权限不足 | 引导用户确认腾讯文档 VIP 权限 |
| `400008` | 积分不足 | 引导用户确认腾讯文档积分 |
| `400016` | 文档类型不匹配 | 重新查询类型并切换到对应 MCP 服务 |
| `-32601` | 工具不存在 | 检查当前加载的工具列表和服务 |
| `-32603` / `11607` | 参数错误 | 根据当前工具 Schema 修正参数 |

排查顺序：

1. 确认腾讯文档 connector 已连接。
2. 确认目标文档类型和对应 MCP 服务。
3. 读取当前工具 Schema，检查工具名和参数。
4. 检查文件权限、VIP 和积分状态。
