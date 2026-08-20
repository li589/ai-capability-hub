# AgentEarth TRAE Plugin

AgentEarth 是 AI 助手调用全球专家级工具的统一平台。本插件把 AgentEarth 的
1400+ 专业 API 以一个 Remote MCP Server + 一个 Skill 的形式接入 TRAE：用户只需
填写一次 API Key，就可以用自然语言调用实时金融行情、电商与社媒数据、AI 生图与
视频生成、学术论文与专利、地图与出行等真实业务能力，无需自行申请和维护上游
账号与 Key。

AgentEarth is the unified platform for AI assistants to access 1,400+
expert-grade APIs. This plugin exposes them to TRAE through one remote MCP
server and one Skill: the user pastes an API Key once, then calls everything in
natural language.

## 1. 能力列表 Capabilities

| 能力 | 内容 |
| :--- | :--- |
| MCP | `agentearth`（Streamable HTTP Remote MCP，`https://agentearth.ai/mcp-server/`） |
| Skill | `skills/agentearth/SKILL.md` |
| Connector | `agentearth`（`manual_token`，用户手动填写 API Key） |

MCP Server 暴露 5 个工具：

| 工具 | 用途 |
| :--- | :--- |
| `GetAccountOverview` | 查询当前账号的 `user_id`、`user_name`、`key_name` 与剩余额度 `credit` |
| `RecommendTools` | 按自然语言任务描述推荐候选工具，返回 `tool_url` 与 `input_schema` |
| `ListTools` | 按关键词/分页浏览工具列表 |
| `GetToolDetail` | 按精确工具名查询单个工具详情 |
| `ExecuteTool` | 使用 `tool_url` + `params` 执行选中的工具 |

## 2. 目录结构 Directory Layout

```text
agentearth/
├── .trae-plugin/
│   └── plugin.json                          # 插件清单：名称、版本、图标、Skill/MCP/Connector 引用
├── skills/
│   └── agentearth/
│       └── SKILL.md                         # 工具发现与执行的操作流程
├── examples/
│   └── connector-provider-template.json     # 平台侧授权表单模板（提交用，不由 plugin.json 加载）
├── .mcp.json                                # Remote MCP 配置 + Connector token 注入
├── connector.json                           # 插件侧最小 Connector 声明
├── icon.svg                                 # 插件图标
├── README.md
└── LICENSE
```

所有相对路径均以插件根目录 `agentearth/` 为基准，包内不含绝对路径、`../` 路径逃逸或软链。

## 3. Skill、MCP 与 Connector 的关系

三者是一条链：

1. **Connector**（`connector.json`）声明插件使用名为 `agentearth` 的
   `manual_token` 授权模板，触发策略为 `ON_INVOKE`——用户首次调用 AgentEarth
   工具时弹出授权表单，填写 AgentEarth API Key。
2. **MCP**（`.mcp.json`）通过占位符
   `${connector.agentearth.ACCESS_TOKEN}` 把授权结果注入 MCP 请求头
   `X-Api-Key`，建立到 `https://agentearth.ai/mcp-server/` 的连接，得到上述 5 个工具。
3. **Skill**（`skills/agentearth/SKILL.md`）告诉模型这 5 个工具怎么用：
   何时先 `RecommendTools` 再 `ExecuteTool`、`tool_url` 必须原样透传、
   如何用 `isError` 判断执行结果、失败后如何改参重试或换候选工具。

Skill 不接触凭据，也不允许模型自行发起 HTTP 请求或向用户索要 API Key。

## 4. 认证方式与凭据消费 Authentication

- **授权类型**：`manual_token`，主凭据字段为标准的 `ACCESS_TOKEN`，即 AgentEarth API Key。无额外 `metadata.*` 字段。
- **平台侧表单**：见 `examples/connector-provider-template.json`，含 `en` / `zh-cn` / `ja` 三语文案，以及获取 API Key 的 `docUrl`。该文件仅用于向 TRAE 提交配置，不会被 `plugin.json` 加载。
- **注入位置**：仅 `.mcp.json` 的 `headers.X-Api-Key`，占位符为 `${connector.agentearth.ACCESS_TOKEN}`。使用的是标准 `ACCESS_TOKEN` 字段，未使用 `metadata.*`，兼容性最广。
- **用户获取 API Key**：登录 `https://agentearth.ai` 后，在右上角头像菜单的 **API Keys** 中创建。
- 包内不包含任何真实 token、secret 或 private key；凭据全部由运行时解析注入，不回写插件包。

## 5. 运行依赖 Runtime Dependencies

- 无本地命令、无本地 MCP 进程、无第三方依赖，也不需要 Node.js 等运行时。
- 仅需网络可访问 `https://agentearth.ai`（MCP 端点为 `https://agentearth.ai/mcp-server/`）。部分工具（如 AI 生图/视频）单次调用可能需要数十秒，建议 MCP 请求超时不低于 60s。
- 因此不限制操作系统，可按 Universal 处理。

## 6. 配置与验证 Configuration and Verification

1. 在 TRAE 中安装插件，首次调用时按提示完成 `agentearth` Connector 授权，粘贴 AgentEarth API Key。
2. 验证连接：让 AI 助手执行「查询我的 AgentEarth 账号余额」，应触发 `GetAccountOverview` 并返回 `user_id`、`key_name` 与 `credit`（`error_no` 为 `0`）。
3. 验证工具链路，可用以下示例：
   - 使用 AgentEarth 查询当前比特币价格
   - 使用 AgentEarth 查询今天上海天气
   - 使用 AgentEarth 推荐上海评分较高的咖啡店
   - 通过 AgentEarth 生成一张产品海报图

## 7. 已知限制 Known Limitations

- `ExecuteTool` 返回的是上游第三方 API 的原始响应，各工具的结构不统一；成功与否以 MCP 结果的 `isError` 为准，而不是响应体内的某个固定字段。
- 部分工具的必填参数需要 ID/编码（如城市 ID、adcode），需先调用 `associated_tools` 中的配套查询工具获取，不能凭空构造。
- 工具调用会消耗账号额度（每个工具的 `credit` 字段标明单次成本），额度不足时调用会失败。
- `tool_url` 为不透明字符串，必须原样透传，禁止改写、重新编码或拼接。

## 8. 外部服务与来源 External Services and Provenance

- 外部服务：AgentEarth（`https://agentearth.ai`），由 AgentEarth 团队运营与维护。
- 本插件包内的清单、Connector、MCP 配置、Skill 文档与图标均由 AgentEarth 团队编写并持有，或已获授权使用，按专有许可分发（见 `LICENSE`）。
- 插件本身不捆绑第三方代码或二进制文件。

## License

专有许可，版权归 AgentEarth 所有，见 `LICENSE`。本包仅授权在 TRAE 中安装使用；
未经书面许可不得复制、修改或再分发。AgentEarth 服务的使用另受
https://agentearth.ai 公布的服务条款约束。
