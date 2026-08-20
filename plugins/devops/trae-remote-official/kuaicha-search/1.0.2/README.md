# 快查企业数据 TRAE 插件（kuaicha-search）

查询中国企业工商、股权投资、经营司法风险、知识产权、招投标及新闻舆情数据的 TRAE Plugin。
数据来源于同花顺旗下快查企业数据引擎。

## 插件用途与能力

- 企业筛选：按地区、产业链、成立时间、企业规模、资质荣誉等条件筛选企业
- 工商数据：企业基本信息、股东、对外投资、实际控制人、分支机构、最终受益人
- 经营状况：融资历史、招聘、核心团队、主要客户供应商、竞品、招投标
- 经营风险：经营异常、行政处罚、欠税、股权质押、严重违法、破产重整
- 司法风险：被执行人、失信被执行人、法院公告、裁判文书、限制高消费、司法协助
- 知识产权：商标、专利、软件著作权、作品著作权、网站备案
- 上市信息：十大股东、资产负债表、利润表、现金流量表、董监高
- 新闻舆情：企业新闻、公告及详情

完整的使用流程、参数规范与能力边界见 `skills/kuaicha-search/SKILL.md`。

## 组成与关系

| 模块 | 文件 | 说明 |
|------|------|------|
| 插件清单 | `.trae-plugin/plugin.json` | TRAE 识别插件的入口，声明名称、版本、图标及对 Skill / MCP / Connector 的引用 |
| Skill | `skills/kuaicha-search/SKILL.md` | 沉淀快查企业数据的使用流程：工具发现、参数规范、结果处理与来源标注 |
| MCP | `.mcp.json` | 声明快查 Remote MCP 服务地址，并在请求头中注入 Connector 提供的凭证 |
| Connector | `connector.json` | 声明 `manual_token` 认证，让用户在授权弹窗中填写快查 API Key |

## 认证方式

插件使用 Manual Token（手动 API Key）认证：

1. 平台侧配置授权表单（`examples/connector-provider-template.json`，该文件仅供提交与说明，不会由 `plugin.json` 自动加载）。
2. 用户安装/调用时，TRAE 展示授权弹窗，用户填写从快查数据平台获取的 API Key。
3. TRAE 将凭证保存为用户本地的 Connector 结果；调用 MCP 时把 `ACCESS_TOKEN` 注入 `open-authorization` 请求头（见 `.mcp.json`）。

插件包内不包含任何真实凭据。API Key 的获取地址：<https://open.kuaicha365.com/mcp/>。

## 依赖

- 外部服务：快查 Remote MCP（`https://bizveris.kuaicha365.com/mcp`），需要可以访问该地址。
- 本地依赖：无。本插件为纯 HTTP Remote MCP，不包含本地命令、本地运行时或第三方依赖。
- 支持系统：Universal（不限系统）。

## 配置与验证

1. 将本目录按 TRAE 插件要求打包为 `.zip` 提交上架。
2. 在平台为 Manual Token Connector 配置 Provider Template（使用 `examples/connector-provider-template.json`）。
3. 安装插件并填写快查 API Key 后，触发任一快查查询（例如“查询腾讯的股东结构”），确认结果正确返回，且回答末尾标注“数据来源于同花顺旗下快查企业数据引擎”。

## 已知限制

- 仅支持中国大陆企业、个体工商户、社会组织、事业单位等组织的数据查询。
- 不支持实时股价、汇率、期货等行情数据，也不支持天气、地图、个人征信等非企业查询。
- 平台侧未配置 Manual Token Provider Template 时，无法收集用户凭证。

## 许可证

当前未指定。请按实际授权情况补充 `LICENSE` 文件后再发布。
