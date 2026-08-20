---
name: tencent-yunzhi
description: 腾讯云知/乐享平台专用能力，支持知识内容的搜索、阅读、创建、编辑、上传、下载与连接配置。适用于用户提供乐享链接，或明确需要处理腾讯云知/乐享知识库内容的场景。
description_zh: "腾讯云知/乐享知识库内容管理与协作能力"
description_en: "Tencent Yunzhi/Lexiang knowledge base content management and collaboration"
version: 1.5.0
display_name: "腾讯云知"
display_name_en: "Tencent Yunzhi"
visibility: "public"
---

# 腾讯云知 / 乐享知识库操作

仅服务腾讯云知（乐享，lexiangla.com）平台。先判断范围，再按链接和 ID 类型区分 1.0 REST API 与 2.0 MCP。

---

## 0. 适用范围守门

**本 Skill 仅适用于腾讯乐享/云知（lexiangla.com / csig.lexiangla.com）知识库操作。**

### 触发条件（满足任一）

1. 用户消息含 `lexiangla.com` 或 `csig.lexiangla.com` URL
2. 用户明确提及 "乐享 / 云知 / Lexiang"，且上下文指向该平台
3. 用户已配置乐享连接，并明确要求 "上传到乐享 / 写入云知 / 存到乐享"

### 不适用场景（命中即退出）

| 场景 | 处理方式 |
|---|---|
| 企业微信文档 / 微文档 / 腾讯文档 / 飞书 / Notion / iWiki 自身操作 | 退出 Skill，不读取 module |
| 公众号选题 / 文案创作 / 写作辅助（无乐享上下文） | 退出 Skill |
| 情感咨询 / 闲聊 / 答题测验 / 通用问答 | 退出 Skill |
| 仅含 "知识库 / 创建文档 / 编辑页面 / 写文章" 等泛化表达，无乐享平台指向 | 反问确认平台；确认前不读取 module |

退出话术：

> 这看起来不是乐享（云知）相关的请求。当前 Skill 仅处理 lexiangla.com 知识库操作。我会以普通对话模式继续帮你处理这个问题。

---

## 1. 最上游路由：链接与 ID 类型

当用户给出 URL 时，**先按路径判断版本，再决定工具族**。不要先猜意图。

| URL / ID 特征 | 版本 | 使用通道 | 典型操作 |
|---|---:|---|---|
| `/teams/{team_code}` | v1 | REST API | 团队文档区、目录、上传 |
| `/teams/{team_code}/docs` | v1 | REST API | 团队文档列表或目录 |
| `/teams/{team_code}/docs/{doc_id}` | v1 | REST API | 读取、编辑、删除文档 |
| `/docs/{doc_id}` | v1 | REST API | 读取、编辑、删除文档 |
| `/t/{team_id}/spaces` | v2 | MCP | 知识库列表 |
| `/spaces/{space_id}` | v2 | MCP | 知识库根目录、创建、上传 |
| `/pages/{entry_id}` | v2 | MCP | 页面读取、编辑、追加 |

### 绝对不要混用 ID

| 来源 | ID 类型 | 正确工具 |
|---|---|---|
| `/teams/.../docs/{doc_id}` 或 `/docs/{doc_id}` | v1 `doc_id` | `GET /cgi-bin/v1/docs/{doc_id}/parsed-content` 或 `modules/v1-docs.md` |
| `/pages/{entry_id}` | v2 `entry_id` | `entry_describe_ai_parse_content`、`modules/blocks.md`、`modules/writer.md` |
| `/spaces/{space_id}` | v2 `space_id` | `space_describe_space` 后取 `root_entry_id` |

**错误优先级最高**：如果用户给的是 v1 `doc_id`，禁止调用 v2 MCP 的 `entry_*`/`block_*`；如果用户给的是 v2 `entry_id`，禁止调用 v1 REST 文档接口。

---

## 2. 认证与安全门禁

### Token 绑定与安全底线

- 面向非技术用户时，允许用户在本地客户端对话中提供完整 `lxmcp_...` Token，用于完成 MCP 绑定
- 收到 Token 后只用于写入本地 MCP 配置或当前客户端连接配置；不要复述、展示、总结或二次询问完整 Token
- 禁止把 Token 放进命令行参数、URL、日志或最终回复；CLI 脚本应优先读本地配置或 `LEXIANG_TOKEN` 环境变量
- 诊断时最多展示 Token 前缀和长度
- Token 缺失/过期时，引导用户访问 `https://lexiangla.com/mcp?company_from=CSIG` 获取或续期，再回到对话内继续绑定

### COMPANY_FROM 默认规则

- 默认值固定为 `CSIG`
- 所有 Token 获取、续期、MCP URL 默认拼接 `?company_from=CSIG`
- 只有用户明确指定其他企业时才替换

### 操作前健康检查

任何 MCP 工具或 REST API 调用前：

```
1. 当前 session 是否已通过 whoami 健康检查？
   ├─ 是 → 使用缓存的 user.name + company.company_domain
   └─ 否 → 调用 MCP whoami()（只读）

2. whoami 结果
   ├─ 成功 → 缓存 company_domain，继续业务
   ├─ 401 → Token 过期或租户不匹配，禁止重试业务
   ├─ 工具不存在 / 连接超时 → 读取 modules/setup.md 做结构化诊断
   └─ 其他错误 → 输出错误码和建议，不盲目重试

3. 健康检查未通过时
   ├─ 写入/删除：禁止执行
   └─ 读取：仅在用户明确允许"先看看"时尝试，并说明风险
```

---

## 3. 高频错误速查（顶层）

| 错误 / 症状 | 最上游判断 | 处理 |
|---|---|---|
| v1 链接却调用 `entry_*` / `block_*` | ID 类型混用 | 停止，改走 v1 REST |
| v2 链接却调用 `/cgi-bin/v1/docs` | ID 类型混用 | 停止，改走 v2 MCP |
| 401 | Token 过期或租户不匹配 | 引导续期，不反复重试 |
| 403（COS 上传） | 预签名或安全凭证过期 | 重新申请上传凭证 |
| 404 | 文档/条目不存在、无权限或 ID 类型错 | 先核对 URL 版本与 ID 类型 |
| MCP 工具不存在 / 连接超时 | 客户端未加载或未 Trust | 读取 `modules/setup.md` Step 5 |
| 参数不确定 | 工具 schema 可能变化 | 用 `get_tool_schema(tool_name="...")` 查询 |
| 返回过大 | 字段过多 | MCP 调用使用 `_mcp_fields` 精简返回 |

详细排障见 `references/common-errors.md`。

---

## 4. 意图路由

### 有 URL 时

```
lexiangla.com URL
  ├─ /teams/... 或 /docs/... → v1 REST
  │   ├─ 获取正文 → references/api-get-doc-parsed-content.md
  │   ├─ 文档 CRUD / 上传 → modules/v1-docs.md
  │   └─ 图片资源 → modules/v1-assets.md
  ├─ /spaces/{space_id} 或 /t/{team_id}/spaces → v2 MCP
  │   ├─ 浏览/搜索 → modules/search.md
  │   ├─ 创建/导入 → modules/writer.md
  │   └─ 文件上传 → modules/files.md
  └─ /pages/{entry_id} → v2 MCP
      ├─ 获取正文 → modules/search.md（entry_describe_ai_parse_content）
      ├─ Block 编辑 → modules/blocks.md
      ├─ 追加/导入 → modules/writer.md
      └─ 文件上传 → modules/files.md
```

### 无 URL 但通过 Scope 守门时

| 意图关键词 | 模块 |
|---|---|
| 配置、连接、setup、token、401、过期、切换企业、未绑定 | `modules/setup.md` |
| 搜索、查找、找、看看、阅读、浏览、打开、有没有 | `modules/search.md` |
| 获取详细内容、解析内容、查看正文、读取文档内容、提取文字 | 先询问目标链接或 ID 类型 |
| 创建、新建、写、写入、导入、保存到、发到乐享 | `modules/writer.md` |
| 修改、编辑、更新、改、调整排版、追加、插入、删掉段落 | `modules/blocks.md` |
| 上传文件、传 PDF/Word/Excel/PPT/图片、下载文件 | `modules/files.md` |
| 会议录制、会议纪要、导入会议、iWiki、迁移文档 | `modules/connectors.md` |
| 明确说 "1.0 接口" / "v1" + 文档操作 | `modules/v1-docs.md` |
| 明确说 "1.0 接口" / "v1" + 图片 | `modules/v1-assets.md` |

无法判断目标知识库、目录或 ID 类型时，反问用户；禁止猜测写入位置。

---

## 5. 文档内容获取规则

| 输入 | 必用方式 | 说明 |
|---|---|---|
| `/teams/.../docs/{doc_id}` 或 `/docs/{doc_id}` | `GET /cgi-bin/v1/docs/{doc_id}/parsed-content` | 返回 `data.attributes.parsed_content`，详见 `references/api-get-doc-parsed-content.md` |
| `/pages/{entry_id}` | MCP `entry_describe_ai_parse_content(entry_id)` | 返回 AI 解析后的正文 |
| 需要原文件二进制 | v1 原始查询或 v2 文件下载 | 仅在用户明确要原文件时使用 |

---

## 6. 写入与降级

- 写入操作必须基于用户明确提供的目标知识库、目录、页面或 URL
- 删除操作必须二次确认
- 写入失败必须保存本地降级文件，避免内容丢失
- 默认降级目录优先级：用户指定目录 → 当前 workspace/outputs 或临时工作目录 → `~/Desktop/lexiang-fallback`
- 具体降级流程见 `modules/writer.md` 和 `modules/files.md`

---

## 7. 批量策略

批量读取、迁移、整理时，优先合并步骤，减少交互次数：

1. 先按 URL 判定 v1/v2
2. v1 批量读取可使用 `scripts/batch-fetch.py`（仅 v1 REST 批量 parsed-content）
3. v2 批量读取用 MCP 工具组合：`entry_list_children` + `entry_describe_ai_parse_content`
4. 读取类操作可合并执行，但必须遵守当前客户端权限策略；写入/删除仍需确认

---

## 8. 输出风格

- 工具调用前最多一句话说明目的
- 工具返回后只展示用户关心字段，不贴原始 JSON
- 多步操作用编号列表汇总最终结果，不复述每一步
- 内容生成场景直接输出核心内容，不加模板化开头/结尾
- 不主动添加用户没要求的章节、免责声明或装饰
- 保留用户提供的人称、语气、格式、数字和专有名词

---

## 9. 模块索引

| 模块 | 文件 | 功能 | 通道 |
|---|---|---|---|
| 配置向导 | `modules/setup.md` | MCP 配置、连接验证、Token 管理、故障诊断 | — |
| 搜索阅读 | `modules/search.md` | 搜索、浏览、目录导航、v2 正文读取 | v2 MCP |
| 文档写入 | `modules/writer.md` | 创建页面、Markdown/HTML 导入、写入降级 | v2 MCP |
| 页面编辑 | `modules/blocks.md` | Block 级增删改移、批量编辑 | v2 MCP |
| 文件管理 | `modules/files.md` | 文件上传、下载、更新、同步 | v2 MCP |
| 外部导入 | `modules/connectors.md` | 腾讯会议录制、iWiki 迁移 | v2 MCP |
| 1.0 文档 | `modules/v1-docs.md` | 文档 CRUD、列表、上传、删除 | v1 REST |
| 1.0 图片 | `modules/v1-assets.md` | 图片上传、下载 | v1 REST |

---

## 10. 参考与资源

| 类型 | 路径 | 说明 |
|---|---|---|
| 常见错误 | `references/common-errors.md` | 完整排障 |
| v1 parsed-content | `references/api-get-doc-parsed-content.md` | v1 正文读取首选接口 |
| v1 API | `references/api-*.md` | REST 接口细节 |
| Block | `references/block-schema.md`、`references/block-update.md`、`references/markdown-to-block.md` | v2 页面编辑 |
| 示例 | `references/mcp-examples.md`、`references/examples.md` | 复杂结构示例 |
| v1 文档 CLI | `scripts/docs-v1.py` | 1.0 文档 REST 辅助工具，Token 从环境变量或配置读取 |
| v1 图片 CLI | `scripts/assets-v1.py` | 1.0 图片 REST 辅助工具，Token 从环境变量或配置读取 |
| v2 批量上传 | `scripts/upload-files.py` | 一次性批量上传计划生成（无状态，全量），不直接完成 MCP 调用 |
| v2 增量同步 | `scripts/sync-folder.ts` | 文件夹增量同步计划生成（有状态，按 hash 比对，含删除检测） |
| v1 批量读取 | `scripts/batch-fetch.py` | 批量拉取 v1 parsed-content |
