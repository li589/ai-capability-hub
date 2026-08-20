# 连接器与 MCP 故障排查手册

> **版本**：v1.0 (2026-06-01)

---
## 问题诊断决策树（从现象到根因）

```
连接器出现问题？
    │
    ▼
[1] 状态栏显示 "disconnected"
    ├── 所有连接器都disconnected？
    │   ├── Yes → 代理服务挂了 → 见 §3.6 代理修复
    │   └── No  → 单个连接器问题 → 继续排查 ▶
    │
    ├── 检查：是认证问题吗？
    │   ├── token 过期 → 通过 WorkBuddy UI 重新登录
    │   ├── token 格式错 → 检查 Bearer 前缀
    │   └── header 缺失 → 补全 Authorization 头
    │
    └── 检查：是网络问题吗？
        ├── curl URL返回非200 → 服务不可用/被墙
        ├── curl URL返回200但超时 → timeout 太小 → 调整到600000
        └── curl URL通过 → 排查请求参数

[2] 状态显示 "connected" 但工具调用失败
    ├── 报错 "method not found" → tool name 大小写错误
    ├── 报错 "invalid params" → 参数缺少或类型不对
    ├── 返回空结果 → content 结构解析问题 → 见 §3.3
    └── 报错 "stdio 类型暂未支持" → 代理不支持 → 见 §5.2

[3] 时好时坏
    ├── 多session配置冲突 → 见 §3.4
    ├── 网络不稳定 → 增加timeout + 重试
    └── 服务限流 → 降低调用频率
```

---
## 一、连接器配置架构（三层覆盖机制）

### 1.1 配置文件层级

WorkBuddy 的 connector 配置采用**三层覆盖**机制，后加载的配置覆盖前面的：

```
Layer 1: ~/.workbuddy/mcp.json                    ← 顶层 MCP Server 定义
Layer 2: ~/.workbuddy/connectors/default/mcp.json  ← 连接器默认配置（基线）
Layer 3: ~/.workbuddy/connectors/{session}/mcp.json ← 会话级配置（实际凭证）
Layer 4: connector-states.json headerOverrides     ← 运行时动态覆盖
```

### 1.2 实际配置分析

| 层级 | 文件路径 | 作用 |
|------|----------|------|
| 顶层 | `~/.workbuddy/mcp.json` | 定义 stdio 类型服务（如 npx 启动的连接器） |
| 默认 | `~/.workbuddy/connectors/default/mcp.json` | 所有连接器默认 disabled=true（安全基线） |
| 会话 | `~/.workbuddy/connectors/{session-id}/mcp.json` | 实际启用的连接器（含 auth token） |
| 状态 | `~/.workbuddy/connectors/{session-id}/connector-states.json` | enabled 列表 + headerOverrides |

### 1.3 配置合并规则

```python
# 1. 先加载 default/mcp.json → configs.update()  # 基线
# 2. 按 session ID 排序，逐个加载 → configs.update()  # 后者覆盖前者
# 3. 应用 connector-states.json 的 headerOverrides → configs[key]["headers"].update()
```

**关键规则：**
- 同一个 connector key（如 `connector:qq-mail`）后加载的完全覆盖前面的
- `disabled: true` 会跳过加载，不会出现在最终配置中
- `headerOverrides` 只更新 headers，不替换整个配置

### 1.4 配置示例

```json
{
  "connector:qq-mail": {
    "timeout": 600000,
    "url": "https://api.mail.qq.com/mcp"
    // 无 disabled 字段 → 启用
  },
  "connector:lexiang": {
    "url": "https://mcp.lexiang-app.com/mcp",
    "headers": { "Authorization": "Bearer YOUR_TOKEN" }
  },
  "connector:tencent-docs": {
    "url": "https://docs.qq.com/openapi/mcp",
    "headers": { "Authorization": "Bearer YOUR_TOKEN" }
  },
  "connector:kdocs": {
    "headers": { "Authorization": "Bearer YOUR_TOKEN" }
  },
  "connector:github": {
    "headers": { "Authorization": "Bearer YOUR_TOKEN" }
  },
  "connector:ima-mcp": {
    "headers": { "Authorization": "Bearer YOUR_TOKEN" }
  },
  "connector:qcc-company": {
    "type": "streamableHttp",
    "url": "https://agent.qcc.com/mcp/company/stream"
  },
  "connector:tencent-survey": {
    "type": "streamableHttp",
    "url": "https://wj.qq.com/api/v2/mcp"
  },
  "connector:baidu-netdisk": {
    "type": "sse",
    "url": "https://mcp-pan.baidu.com/sse?access_token=YOUR_TOKEN"
  },
  "connector:tencent-weiyun": {
    "type": "streamableHttp",
    "url": "https://www.weiyun.com/api/v3/mcpserver"
  },
  "connector:edgeone-pages": {
    "command": "npx",
    "args": ["edgeone-pages-mcp-fullstack@latest", "--region", "china"]
  }
}
```

---
## 二、传输类型兼容性矩阵

| 传输类型 | 配置字段 | 代理支持 | 说明 |
|----------|----------|----------|------|
| HTTP POST | `url` (默认) | ✅ | 标准 JSON-RPC over HTTP |
| streamableHttp | `type: "streamableHttp"` 或 `transportType: "streamable-http"` | ✅ | 走 session.post() |
| SSE | `type: "sse"` | ✅ | 百度网盘使用 |
| stdio | `command` + `args` | ❌ | 代理不支持子进程管理 |
| WebSocket | `url` 以 websocket:// 或 wss:// | ❌ | TAPD 使用，代理不支持 |

**代理代码关键逻辑：**
```python
# 代理服务对 stdio 类型的处理逻辑
if self.config.get("command"):
    self.online = False
    self.error = "stdio 类型暂未支持"
    return False
```

---
## 三、故障排查清单（逐步骤执行）

### 3.1 连接器不显示在 WorkBuddy 中

**检查顺序：**

1. `disabled` 字段是否为 `true`
   ```bash
   # 检查所有配置中的 disabled 状态
   grep -r "disabled" ~/.workbuddy/connectors/*/mcp.json
   ```

2. URL 是否可访问
   ```bash
   # 测试连通性
   curl -s -o /dev/null -w "%{http_code}" https://api.mail.qq.com/mcp
   ```
   **判断标准**：返回 `200` / `202` - 正常；`401` / `403` - 认证问题；`404` - URL路径错误；无响应 - 网络不通或服务挂掉

3. 认证头是否正确
   ```bash
   # 检查 headers 字段
   grep -A5 '"headers"' ~/.workbuddy/connectors/{session-id}/mcp.json
   ```
   **常见错误**：
   - 缺少 `Bearer` 前缀 → 应写 `"Bearer YOUR_TOKEN"`
   - token 中混入换行符 → 确保 token 是单行字符串
   - 用了旧 session 的 token → 确认当前 session-id 正确

4. 传输类型是否支持
   - stdio 类型（有 `command` 字段）→ 代理不支持，需要原生 WorkBuddy 连接器

### 3.2 MCP 工具调用失败 — 错误码对照表

| 错误码/现象 | 原因 | 修复方法 |
|-----------|------|---------|
| `HTTP 404` | URL 路径错误或服务下线 | 检查 URL 是否正确，确认服务是否存活 |
| `HTTP 401` | 认证 token 过期 | 通过 WorkBuddy UI 重新登录该连接器 |
| `HTTP 403` | 权限不足 | 检查账号是否开通该服务权限 |
| `HTTP 429` | 请求频率过高被限流 | 降低调用频率，增加请求间隔 2-3 秒 |
| `HTTP 500/502/503` | 服务端内部错误 | 等待 2-5 分钟后重试，仍失败则服务可能下线 |
| `连接超时` | 网络不通或服务响应慢 | 检查防火墙，调整 timeout 到 600000（10分钟） |
| `stdio 类型暂未支持` | 代理不支持子进程 | 使用原生 WorkBuddy 连接器机制 |
| `tools/list 返回空` | 服务端 MCP 协议版本不兼容 | 检查 WorkBuddy/服务端的 MCP 协议版本 |
| `method not found` | tool name 大小写不匹配 | 用 `ListMcpResources` 确认正确的 tool name |
| `invalid params` | 参数缺失/类型错误/格式不对 | 对照该工具的 schema 检查每个参数 |

### 3.3 工具调用成功但返回空结果

**排查步骤：**

1. 检查 tool name 是否匹配（区分大小写）
2. 检查 arguments 格式是否正确
3. 查看返回的 content 结构：
   ```python
   # 代理提取逻辑
   content = result.get("result", {}).get("content", [])
   texts = [item.get("text", "") for item in content if isinstance(item, dict)]
   ```
4. 如果 content 为 `[]`，尝试打印原始返回：
   ```bash
   # 直接调用MCP endpoint，查看原始响应
   curl -X POST https://api.example.com/mcp \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"your_tool","arguments":{}}}' | python -m json.tool
   ```

### 3.4 多会话配置冲突

**症状：** 某个连接器在两个 session 中配置不同，实际使用的是旧配置

**原因：** session 按 ID 排序后覆盖，字母序靠后的 session 配置优先

**修复：**
```bash
# 查看所有 session 目录
ls ~/.workbuddy/connectors/ | grep -v "default\|skills"

# 查看当前使用的 session（从 WorkBuddy 设置中确认）
# 确保当前 session 的 mcp.json 包含正确的配置
```

### 3.5 日志分析方法

当以上步骤都无法定位问题时，查看代理日志：

```bash
# 代理日志通常位于
ls ~/.workbuddy/logs/

# 搜索最近的错误日志
grep -i "error\|fail\|timeout" ~/.workbuddy/logs/*.log | tail -20

# 查看连接器相关的日志
grep "connector" ~/.workbuddy/logs/*.log | tail -30
```

**日志关键信息提取**：
- `mcp_server::` 开头的行 → MCP 服务端问题
- `proxy::` 开头的行 → 代理层问题
- `connector::` 开头的行 → 连接器连接/断开事件

### 3.6 代理服务修复

**症状**：所有连接器都 disconnected，或 curl localhost:51103 无响应

**修复步骤**：
```bash
# 1. 检查代理是否运行
curl -s http://127.0.0.1:51103/health

# 2. 如果无响应，重启代理
# 通过 WorkBuddy 退出并重新启动

# 3. 检查端口是否被占用
netstat -ano | findstr 51103

# 4. 如果端口被其他进程占用，释放端口
taskkill /PID <pid> /F
```

---
## 四、一键诊断命令集合

```bash
# 1. 查看所有 connector 配置
for f in ~/.workbuddy/connectors/*/mcp.json; do echo "=== $f ==="; cat "$f"; done

# 2. 查看哪些 connector 被启用
for f in ~/.workbuddy/connectors/*/connector-states.json; do
  echo "=== $f ==="
  cat "$f" | python -c "import sys,json; d=json.load(sys.stdin); print('Enabled:', d.get('enabled',[]))"
done

# 3. 测试单个 connector 连通性
curl -X POST https://api.mail.qq.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# 4. 查看代理服务状态
curl -s http://127.0.0.1:51103/health

# 5. 批量测试所有HTTP连接器的连通性
for url in $(grep -ohP '"url":\s*"https?://[^"]+"' ~/.workbuddy/connectors/*/mcp.json | cut -d'"' -f4 | sort -u); do
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url")
  echo "$status $url"
done

# 6. 检查最近5分钟的代理错误
grep -i "error\|fail" ~/.workbuddy/logs/*.log | tail -30
```

---
## 五、已知问题与解决方案

### 5.1 邮箱认证问题

**现象：** QQ Mail 连接器调用失败，返回 401

**原因：** QQ Mail MCP 服务使用 Bearer token 认证，token 可能已过期

**解决步骤：**
1. 检查 `~/.workbuddy/connectors/{session-id}/mcp.json` 中是否有 `headers.Authorization`
2. 如果没有，通过 WorkBuddy UI 重新登录 QQ 邮箱
3. token 格式：`Bearer {access_token}`
4. 确认 QQ 邮箱账号正常（未被冻结）

**快速验证**：
```bash
# 测试token是否有效
curl -s -H "Authorization: Bearer YOUR_TOKEN" https://api.mail.qq.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# 如果返回 200 + JSON 响应 → token有效
# 如果返回 401 → token过期
```

### 5.2 stdio 类型连接器无法使用

**现象：** edgeone-pages 等 npx 类型的连接器显示"暂未支持"

**原因：** 代理只支持 HTTP/SSE/streamableHttp，不支持子进程

**解决：** 这些连接器需要通过 WorkBuddy 原生 connector 机制运行，不走代理

### 5.3 飞书/企业微信 认证失败

**现象：** 授权后仍提示 "disconnected"

**排查步骤：**
1. 确认授权页面是否真正完成（而非被浏览器拦截）
2. 检查 `connector:{service}` 的 headers 中是否有 auth token
3. 部分服务需要定期刷新 token（通常 2 小时）

### 5.4 百度网盘 token 过期

**现象：** 百度网盘连接器突然不可用

**原因：** 百度网盘使用 access_token 参数，token 有效期通常为 30 天

**解决：**
```bash
# 检查当前 token 是否过期
# 百度网盘 URL 格式：https://mcp-pan.baidu.com/sse?access_token={token}
# 如果返回 400/401 → 重新授权
```

---
## 六、配置模板

### 6.1 新增 HTTP 类型连接器

```json
{
  "mcpServers": {
    "connector:my-service": {
      "url": "https://api.example.com/mcp",
      "timeout": 60000,
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### 6.2 新增 SSE 类型连接器

```json
{
  "mcpServers": {
    "connector:my-sse": {
      "type": "sse",
      "url": "https://api.example.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### 6.3 动态启用/禁用

```json
{
  "enabled": ["qq-mail", "lexiang", "tencent-docs"],
  "headerOverrides": {
    "qq-mail": {
      "Authorization": "Bearer NEW_TOKEN"
    }
  }
}
```

---
## 七、扩展阅读

- `troubleshooting.md` — 跨领域综合诊断决策树
- `05-quick-cards.md` 卡片1 — MCP失败的即查即用诊断
- 官方文档：`https://www.codebuddy.cn/docs/workbuddy/Overview` → 连接器章节
- 脚本：`scripts/check_env.py` — 一键环境诊断

---
## 八、踩坑经验

### 通用：平台识别优先
- **WorkBuddy 内置连接器**（乐享、飞书、腾讯文档等）：完全通过 WorkBuddy UI OAuth 管理，**禁止手动编辑 mcp.json**，遇到 disconnected/401 直接点「重新授权」
- **其他平台**（OpenClaw、Claude 等）：才需要手动配置 Bearer Token 到 mcp.json

### 通用：Token 生命周期三阶段
- **未配置**：引导用户访问服务的 MCP 配置页面获取 COMPANY_FROM + TOKEN，直接写入 mcp.json
- **即将过期**：MCP 返回正常结果但附带过期预警 → 先返回结果，末尾附加续期提醒（从 mcp.json 的 `url` 字段提取 `company_from` 拼续期链接）
- **已过期（401）**：**立即停止重试**，读取 mcp.json 中 `url` 的 `company_from` 参数，引导用户打开续期页面（格式：`https://服务域名/mcp?company_from=xxx`），**无需重新获取 token**

### 乐享特有：company_from 不能拼子域名
- `company_from` **只能**作为 `?company_from=xxx` 查询参数，不能拼成子域名（如 `csig.lexiangla.com` 是错的）
- 链接生成必须用 `whoami()` 返回的 `company.company_domain`，不要用 MCP endpoint 拼接

### 乐享特有：配置后强制验证
- 写入 mcp.json 后，**立即调用** `whoami()` 确认连接成功再继续
- 成功时展示欢迎信息（用户名、绑定企业）；401 时引导续期；连接超时时检查 mcp.json 配置

### 乐享特有：租户隔离
- `COMPANY_FROM` 和 `LEXIANG_TOKEN` **必须属于同一租户**，不同租户的 token 不能混用
- 切换企业/租户时，必须重新获取对应租户的 token 并更新 mcp.json

### 通用：不要回显完整 Token
- 任何输出中都**不要回显** TOKEN 的完整值（安全考虑），最多展示前 8 位 + `...`

---
### 原有经验（保留）
- QQ邮箱MCP：Bearer token可能因重新登录而失效，优先检查session级mcp.json
- 多session配置：按字母序覆盖，主session配置可能被其他session覆盖
- 百度网盘token有效期约30天，定期检查是否需要重新授权
- stdio类型连接器（npx启动）代理不支持，需走原生WorkBuddy通道
- 工具调用返回空结果：检查content结构，可能数据在 `result.text` 而非 `result.content[0].text`

---

## 相关 FAQ（快速跳转）

- 连接器显示"已连接"但工具调用失败 → `12-faq.md` 连接器章节第 1 条
- 连接器突然全部不可用 → `12-faq.md` 连接器章节第 2 条
- 排查后仍无法解决 → `troubleshooting.md` 速查表 + `check_env.py` 诊断
