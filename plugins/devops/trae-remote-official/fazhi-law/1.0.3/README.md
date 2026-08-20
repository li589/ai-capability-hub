# 法智法律数据 TRAE 插件（fazhi-law）

查询中国法律法规、司法案例、裁判文书及互联网法律实务资讯的 TRAE Plugin。
数据来源于法智法律数据引擎。

## 插件用途与能力

- **法条检索**：语义检索法律条文、精确检索指定法规名称+条号、阅读法规全文
- **类案检索**：按案情描述检索相似司法案例、阅读指定案号裁判文书全文
- **深度法律研究**：三源并行（法规+案例+互联网）系统性法律研究，正反观点交叉验证
- **法律文书起草**：起草、修改、润色、完善、改写各类法律文书，以 DOCX 文件交付
- **民事诉讼可视化**：将案件事实、法律关系、证据链、诉讼流程等转化为可视化图表
- **互联网法律资讯**：检索法律实务文章、官方解读、热点事件背景

完整的使用流程、参数规范与能力边界见各技能目录下的 `SKILL.md`。

## 组成与关系

| 模块 | 文件 | 说明 |
|------|------|------|
| 插件清单 | `.trae-plugin/plugin.json` | TRAE 识别插件的入口，声明名称、版本、图标及对 Skill / MCP / Connector 的引用 |
| MCP | `.mcp.json` | 声明法智 Remote MCP 服务地址，并在请求头中注入 Connector 提供的凭证 |
| Connector | `connector.json` | 声明 `manual_token` 认证，让用户在授权弹窗中填写法智 API Key |
| Skill | `skills/fazhi-law-mcp/SKILL.md` | 法智 MCP 底层工具调用技能，专门处理 MCP 法律数据查询，供其他技能调用 |
| Skill | `skills/case-search/SKILL.md` | 类案检索技能：诉求分析、多层 query 规划、迭代补检与案例筛选排序 |
| Skill | `skills/law-search-neo/SKILL.md` | 法条检索助手：意图分析、深度优先纵深检索、结构化规则整理输出 |
| Skill | `skills/fazhi-deep-research/SKILL.md` | 深度法律研究技能：六工具体系三源并行系统性法律研究 |
| Skill | `skills/document-drafting/SKILL.md` | 法律文书起草技能：起草、修改、润色、完善、改写各类法律文书，以 DOCX 文件交付 |
| Skill | `skills/civil-litigation-visualization/SKILL.md` | 民事诉讼可视化技能：案件事实、法律关系、证据链等转化为可视化图表 |

## 认证方式

插件使用 Manual Token（手动 API Key）认证：

1. 平台侧配置授权表单（`examples/connector-provider-template.json`，该文件仅供提交与说明，不会由 `plugin.json` 自动加载）。
2. 用户安装/调用时，TRAE 展示授权弹窗，用户填写从法智数据平台获取的 API Key。
3. TRAE 将凭证保存为用户本地的 Connector 结果；调用 MCP 时把 `ACCESS_TOKEN` 注入 `open-authorization` 请求头（见 `.mcp.json`）。

插件包内不包含任何真实凭据。API Key 的获取地址：<https://open.kuaicha365.com/lawskills/>。

## MCP 工具列表

法智 MCP 服务提供以下 6 个工具，由 `fazhi-law-mcp` 技能统一调用：

| # | 工具 ID | 工具名称 | 功能 |
|---|---|---|---|
| 1 | `case_search` | 案例检索 | 在本地案例数据库中检索与用户问题相关的司法案例 |
| 2 | `case_browser` | 案例全文阅读 | 根据指定案号或案件名称精确检索单个案例，返回裁判文书正文 |
| 3 | `legal_article_search` | 法条综合检索 | 在本地法律数据库中检索与用户问题相关的法条 |
| 4 | `law_content_visit` | 法规全文阅读 | 阅读指定的法规全文，按目标提取相关制度规则 |
| 5 | `webpage_search` | 联网搜索 | 执行互联网搜索并返回与用户查询相关的网页内容摘要 |
| 6 | `webpage_visit` | 网页阅读 | 浏览指定 URL 的网页内容并返回与查询目标相关的内容摘要 |

## 依赖

- 外部服务：法智 Remote MCP（`https://bizveris.kuaicha365.com/law_agent/mcp`），需要可以访问该地址。
- 本地依赖：无。本插件为纯 HTTP Remote MCP，不包含本地命令、本地运行时或第三方依赖。
- 支持系统：Universal（不限系统）。

## 配置与验证

1. 将本目录按 TRAE 插件要求打包为 `.zip` 提交上架。
2. 在平台为 Manual Token Connector 配置 Provider Template（使用 `examples/connector-provider-template.json`）。
3. 安装插件并填写法智 API Key 后，触发任一查询（例如"民法典关于合同解除有哪些规定"），确认结果正确返回。

## 技能调用关系

```
用户问题
    │
    ├─→ case-search（类案检索）
    │      └─→ 调用 fazhi-law-mcp（使用 case_search / case_browser / webpage_search / webpage_visit）
    │
    ├─→ law-search-neo（法条检索）
    │      └─→ 调用 fazhi-law-mcp（使用 legal_article_search / law_content_visit / webpage_search / webpage_visit）
    │
    ├─→ fazhi-deep-research（深度法律研究）
    │      └─→ 调用 fazhi-law-mcp（使用全部 6 个工具三源并行）
    │
    ├─→ document-drafting（法律文书起草）
    │      └─→ 调用 fazhi-law-mcp（按需使用全部 6 个工具核验法规、案例和范本）
    │
    ├─→ civil-litigation-visualization（诉讼可视化）
    │      └─→ 独立技能（无 MCP 调用，纯可视化生成）
    │
    └─→ fazhi-law-mcp（底层 MCP 调用）
           └─→ MCP 6 工具：case_search / case_browser / legal_article_search / law_content_visit / webpage_search / webpage_visit
```

各业务技能（case-search、law-search-neo、fazhi-deep-research、document-drafting）需要检索数据时，
应通过 `fazhi-law-mcp` 技能调用 MCP 工具，不再直接调用 HTTP API。

## 已知限制

- 仅支持中国大陆法律法规、司法案例及中文法律实务资讯查询。
- 不支持实时股价、汇率、期货等非法律行情数据。
- 平台侧未配置 Manual Token Provider Template 时，无法收集用户凭证。

## 许可证

当前未指定。请按实际授权情况补充 `LICENSE` 文件后再发布。
