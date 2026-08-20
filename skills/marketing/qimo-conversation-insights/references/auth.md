# 七陌会话洞察 MCP 鉴权与连接

本参考用于处理 `qimo-conversation-insights` MCP 的连接配置、Token/Header 注入、连接验证和鉴权排障。只在 MCP 不可用、连接失败、Token 失效或 account 权限不明确时读取。

## 首次使用

首次安装使用时，先判断当前需要用户环境是否已经配置Token，若未配置Token或Token过期，请按照下面方式回复并引导用户提供Token以进行skill使用：

> 环境检测结果出来了： 当前 WorkBuddy 已就绪，但您这边还没有完成七陌数据授权，需要先配置 App Key，我才能继续帮您分析七陌会话数据。
>
> - 如果您已经是七陌客户，但还没有 Appkey，请到七陌客服后台 -> 系统设置 -> App Key申请。七陌将完成申请处理和数据同步(数据同步是T+1)后，可查看使用 Appkey。
>
> - 如果您还不是七陌客户，请先联系七陌商务开通七陌服务。
> 
> 获取后把APP KEY发给我，我来帮您完成配置，继续当前任务。

## 连接约束

使用固定 MCP 服务，不要临时改写 URL、server id 或鉴权方式。

| 项 | 取值 |
|----|------|
| MCP server id | `qimo-conversation-insights` |
| MCP URL | `https://mcp-ykfdoris.7moor.com/mcp` |
| transport | `http`（Streamable HTTP；mcporter 配置参数写作 `--transport http`） |
| Header | `Authorization: Bearer <QIMO_TOKEN>` |
| timeout | `30000` |

> 七陌 MCP Server 使用 **Streamable HTTP** 传输。mcporter 通过 `--transport http` 注册；不要再用 `--transport sse`，否则握手会失败或挂起。本地开发调试时可把 URL 指向本机服务，线上分析时改回默认远程地址。

## Token/Header 规则

- 将 Token 写入 mcporter 的本地配置，由 mcporter 在调用时注入 `Authorization` Header。
- 后续调用只执行 `mcporter call "https://mcp-ykfdoris.7moor.com/mcp" "<tool>" --args '<JSON>'`。
- 不要在每次工具调用时重新拼接 Token。
- 不要把 Token 写入 Skill、prompt、SQL、`--args`、日志、错误信息或用户回答。
- 只有在 Token 未配置、失效或需要轮换时，才引导用户更新 mcporter 配置。

## 配置方式

通过 mcporter 注册 Token（不依赖 connector）。mcporter 的 `--header "Authorization=Bearer xxx"` 注册的就是标准 `Authorization: Bearer xxx` HTTP 头——`=` 只是 mcporter CLI 的参数分隔符，注入 HTTP 请求时即为标准 Bearer 鉴权头。

> **版本要求**：mcporter `0.9.0` 及以上需要 Node.js `≥ 20.11.0`（`engines` 字段强制）。确认 `node --version` 满足要求后再继续。

**macOS / Linux：**

```bash
mcporter config add qimo-conversation-insights "https://mcp-ykfdoris.7moor.com/mcp" \
  --transport http \
  --header "Authorization=Bearer <QIMO_TOKEN>" \
  --scope home
```

**Windows PowerShell：**

```powershell
mcporter config add qimo-conversation-insights "https://mcp-ykfdoris.7moor.com/mcp" --transport http --header "Authorization=Bearer <QIMO_TOKEN>" --scope home
```

配置完成后，后续调用只使用 `mcporter call qimo-conversation-insights.<tool>`，不必再传 URL 或 Token。切换本地/线上时，用 `mcporter config` 更新 baseUrl 即可。

## 连接验证

配置完成或连接异常时，调用 `get_catalog_list` 验证 MCP 是否可用。

**macOS / Linux：**

```bash
mcporter call qimo-conversation-insights.get_catalog_list --args '{"random_string":"check"}'
```

**Windows PowerShell：**

```powershell
chcp 65001 >nul && mcporter call qimo-conversation-insights.get_catalog_list --args "{`"random_string`":`"check`"}"
```

| 输出/现象 | 处理 |
|-----------|------|
| 返回 catalog 列表 | 连接正常，继续业务查询 |
| `401` / `unauthorized` / token invalid | Token 失效，更新 mcporter 配置中的 `Authorization` Header |
| `403` / forbidden | Token 有效但无权访问目标 account 或表，确认 Token 范围和 account |
| 工具不可见 | 检查 mcporter 配置是否存在（`mcporter list` 中能否看到 `qimo-conversation-insights`）、MCP server 是否正常运行 |
| 调用挂起 / 超时 / 无输出退出 | 大概率是 transport 配置错误：确认配置里 `transport` 为 `http`（Streamable HTTP），不是 `sse`；用 `curl -v -X POST <URL> ... -d '{"jsonrpc":"2.0",...,"method":"initialize",...}'` 确认服务端对 POST 有响应 |
| mcporter 无任何输出且非零退出 | mcporter 版本与 Node.js 不匹配（需 Node ≥ 20.11.0），检查 Node.js 版本 |
| 连接超时 | 检查目标 URL（线上 `https://mcp-ykfdoris.7moor.com/mcp` 或本机 `http://localhost:<port>/mcp`）网络可达性和服务状态 |
| Doris backend not alive | 数据服务故障，停止业务判断，联系七陌管理员 |

## account 权限处理

Token 只解决连接鉴权，不替代业务租户隔离。MCP Server 会根据 Token 解析出服务端认证的 `account`，并在业务 SQL 执行前自动注入 account 隔离条件。

首次使用或需要向用户说明当前租户时执行以下流程：

1. 调用 `get_account` 获取当前 Token 对应的服务端认证 account。
2. 只信任 `get_account` 返回的 `account`，不要从 Token、`sid` 或业务表内容反推。
3. 后续业务 SQL 不要手写 account 条件，交给 MCP Server 自动注入。

macOS / Linux：

```bash
mcporter call qimo-conversation-insights.get_account --args '{}'
```

Windows PowerShell：

```powershell
chcp 65001 >nul && mcporter call qimo-conversation-insights.get_account --args "{}"
```

以下是不要使用的 account 探测 SQL，也不要查询 `ods_chat.mcp_account_secret`：

```sql
SELECT DISTINCT account
FROM internal.<db_name>.<table_name>
LIMIT 50
```

## Token 轮换

Token 失效或轮换时，只更新 mcporter 本地配置中的 `Authorization` Header。不要要求用户提供 Doris 数据库密码、连接串或其他底层凭证。
