---
name: live-escort
description: 直播护航监控技能 - 开启/停止护航、查询护航列表、获取护航总结、一键健康检查。AI 调用 MCP 网关工具后返回
  session_id，前端用 session_id 匹配护航面板的 WS 推送。
version: 1.0.1
author: eclaw
disable-model-invocation: true
---

# 直播护航 Skill

本 Skill 提供直播护航监控的完整操作能力，通过 MCP 网关（`https://agent.xiaoe-tech.com/mcp`）调用 live-escort-service 后端。网关已扩展 5 个 MCP 工具，鉴权走 OAuth 2.1+PKCE（workbuddy 已是网关 OAuth 客户端，token 由 workbuddy OAuth Manager 自动获取注入）。

## 核心机制

- **session_id**：开启护航时由后端生成（雪花 int64），通过 `start_live_escort` 响应返回。**前端用 session_id 匹配护航面板的 WS 推送消息**（task.push 靠 `app_id+user_id` 广播到 iframe WS，前端用 session_id 区分本次护航）。后续 `stop_live_escort`/`get_escort_summary` 调用也用该 session_id 定位会话（网关透传 `X-Session-ID` header 给上游）。
- **护航面板**：实时面板（指标/趋势/事件/结束态）由后端 Worker 通过 WS 推送，AI 不介入推送，只做意图识别 + 调工具 + 输出面板链接。
- **措辞合规**：对用户输出禁止"保障"二字，一律用"守护"替代（eclaw 法务要求）。"护航"不受影响。

## 可用工具

### start_live_escort - 开启护航

为指定直播开启持续护航监控。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| alive_id | string | ✅ | 直播ID或直播链接 |
| heartbeat | integer | - | 心跳报告间隔（秒），默认600，范围600~3600 |

**返回**：`session_id`、`b_user_token`、`alive_id`、`alive_title`、`escort_mode`（streaming/pre_stream）、`status`、`start_time`、`first_check`

> **关键**：响应的 `session_id` 和 `b_user_token` 必须传给前端：
> - `b_user_token`：前端连 eclaw WS 的 cookie 鉴权凭证（`Cookie: b_user_token=xxx`）。
> - `session_id`：前端匹配 WS 推送消息（task.push 靠 app_id+user_id 广播，前端用 session_id 区分本次护航）
>
> 两个值都写进护航面板 URL query param 传给前端（临时方案，后续优化为 postMessage/JSAPI 直传，避免 token 进 URL）。

### stop_live_escort - 停止护航

停止指定直播（或全部）的护航监控。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| alive_id | string | - | 直播ID，不传则停止当前店铺所有运行中的护航任务 |
| session_id | string | - | 护航会话 ID（`start_live_escort` 响应返回），传则精确停止该会话 |

**返回**：`session_id`、`alive_id`、`stopped`、`stop_reason`

### list_live_escorts - 护航列表

列出当前店铺所有运行中的护航监控任务。无参数。

**返回**：`data.list[]`，每项含 `session_id`、`alive_id`、`alive_title`、`escort_mode`、`check_count`、`alert_count`、`start_time`

### get_escort_summary - 护航总结

获取指定直播的护航总结报告。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| alive_id | string | ✅ | 直播ID |
| session_id | string | ✅ | 护航会话 ID（`start_live_escort` 响应返回），网关据此定位会话 |

**返回**：`session_id`、`alive_id`、`alive_title`、`escort_mode`、`status`、`stop_reason`、`start_time`、`check_count`、`alert_count`、`history`

### query_live_health - 直播健康检查

对指定直播执行一次健康检查（**不启动持续监控**）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| alive_id | string | ✅ | 直播ID或链接 |

**返回**：`alive_id`、`alive_title`、`push_state`、`push_state_text`、`online_num`、`metrics`（帧率/码率/卡顿率/负反馈率/综合等级）

## 意图识别与工具调用规则

1. 用户说"开始护航/启动护航/帮我护航/开启守护" + 提供直播ID/链接 → 调用 `start_live_escort`（alive_id 传用户给的）
2. 用户说"开始护航"但未提供直播ID → **询问用户提供直播ID或链接，不要调用工具**
3. 用户说"停止护航/结束护航" → 调用 `stop_live_escort`（若用户指定直播则传 alive_id）
4. 用户说"护航列表/护航状态/我有哪些护航" → 调用 `list_live_escorts`
5. 用户说"护航总结/护航报告" → 调用 `get_escort_summary`（alive_id 传直播ID，session_id 传 start/stop 响应返回的会话ID）
6. 用户说"健康检查/查一下健康度" → 调用 `query_live_health`（alive_id 传直播ID，单次检查不启动持续监控）

## 开启护航流程（关键，必须串行执行）

### 步骤 1：调用 start_live_escort

`alive_id` 传用户提供的直播ID或链接。等待返回成功（`code=0` 且存在 `data.session_id`）。

成功后记住 `session_id = data.session_id` 和 `alive_id = data.alive_id`、`alive_title = data.alive_title`、`escort_mode = data.escort_mode`。

失败时直接告知用户失败原因（如"直播已手动结束"/"距开播超过30分钟"），不进入步骤 2。

### 步骤 2：输出护航面板链接（携带 session_id + b_user_token）

`start_live_escort` 响应返回 `session_id` + `b_user_token`。在回复里**直接输出护航面板 URL**（含两个 query param），WorkBuddy 会自动提取 URL 渲染成可点击链接：

```
护航已开始，守护直播：{alive_title}（{escort_mode}）

打开护航面板查看实时监控：
https://eclaw-web.example.com/escort-panel?session_id={session_id}&b_user_token={b_user_token}&alive_id={alive_id}
```

**前端使用**：
- iframe 加载后，从 URL query 取 `session_id` + `b_user_token` + `alive_id`
- 连 eclaw WS：`wss://admin.xiaoe-tech.com/lui/v1/agent/ws-chat`，Cookie 带 `b_user_token={b_user_token}`，header 带 `Xe-Ad-Gw-Appid`/`Xe-Ad-Gw-BUserid`（从同源 cookie/session 派生）
- WS 收到 chat.receive，用 `body.session_id` 匹配本次护航 → 渲染面板

> ⚠️ **临时方案（后续优化）**：b_user_token 写进 URL 有安全风险（URL 进 browser history/proxy 日志/AI 对话历史）。后续优化为 postMessage/JSAPI 直传 iframe 或 Buddy 应用授权让 iframe 自己拿（不走 URL）。当前先跑通，后面再优化。
>
> **待 WorkBuddy 团队确认（文档缺口）**：右侧固定 iframe 面板常驻 / MCP 响应字段直传 iframe 机制（当前 workbuddy 只支持 AI 回复输出 URL，b_user_token 不适合写 URL，后续需新机制）。

### 步骤 3：简要说明

告知用户护航已开始，简要说明护航模式：
- `streaming`：直播中，实时监控推流指标
- `pre_stream`：直播尚未开始推流，等待推流中

## 停止护航流程（串行执行）

1. 调用 `stop_live_escort`（优先传 session_id 精确停止；若用户指定直播也可传 alive_id，session_id 取自 `start_live_escort` 响应）
2. 成功后调用 `get_escort_summary`（alive_id 传直播ID，session_id 传步骤 1 start/stop 返回的会话ID）获取护航总结
3. 输出：告知用户护航已停止及停止原因 + 展示护航总结（护航时长、检查次数、告警次数、历史记录）

## 开启护航条件（后端校验，AI 不重复校验，透传后端错误）

- 直播正在推流（push_state=1）：streaming 模式
- 直播未开始但距预设开始时间 ≤30 分钟：pre_stream 模式
- 直播已手动结束：后端拒绝，AI 透传"直播已手动结束，不支持护航"
- 距开播 >30 分钟：后端拒绝，AI 透传"直播尚未开始，仅支持提前30分钟开始护航"

## 护航自动结束（后端自动，AI 不介入）

- 最长护航时长 5 小时，超时自动停止
- 预直播模式等待 30 分钟仍未开播，自动停止
- 直播正常结束（手动/到达预设结束时间），自动停止
- 推流异常断开连续确认 3 次（约 45 秒），自动停止

## 心跳规则

- 默认每 600 秒发送一次心跳报告
- 有效范围 600~3600 秒，超出范围后端自动修正

## 指标阈值（供 AI 解读总结/告警时参考）

| 指标 | 正常 | 告警 | 严重 |
|------|------|------|------|
| 上游卡顿率 | <1% | 1%~3% | >3% |
| 下游卡顿率 | <2% | 2%~5% | >5% |
| 负反馈率 | <5% | 5%~10% | >10% |
| 视频帧率 | ≥15fps | - | <15fps |
| 视频码率 | ≥500kbps | - | <500kbps |

## 输出要求

- 开启护航后，输出面板 URL（含 session_id）+ 简要说明护航模式
- 护航期间告警/恢复/心跳消息由后端自动推送，无需 AI 介入
- 停止护航后，输出停止原因 + 护航总结报告
- `app_id`、`b_user_id` 由系统自动注入，`session_id`、`b_user_token` 由工具响应返回。**不要让用户提供这些字段**，也不要在回复里暴露接口名、参数名、原始 JSON（`session_id`/`b_user_token` 写进护航面板 URL 传给前端是允许的，前端要用）
- 禁止输出"保障"，一律用"守护"

## 前端 UI 工具调用时机

护航功能涉及两个 MCP UI 工具（`live_escort_guide_card` / `live_escort_dashboard_panel`），它们的调用时机与 AI 工具调用紧密配合。AI 需要理解这些时机，才能在正确步骤触发 UI。

### 引导卡片（live_escort_guide_card）

**出现时机**：`start_live_escort` 调用成功后，AI 调用 `invoke_ui_tool`（surface=inline），将 start-escort 响应作为 tool result 下发给卡片。

**卡片内容**：从 `start_live_escort` 响应提取：
- 标题：`直播护航`（start 变体）/ `结束护航`（end 变体）
- 直播店铺：`shop_name`
- 直播名称：`alive_title`
- 描述文案：`将开启直播护航，开启后获得推流健康度 / 卡顿告警 / 心跳实时面板。`
- 主按钮：`打开护航`（start）/ `返回工作台结束`（end）

**用户操作**：用户点击"打开护航"后，卡片通过 `invoke_ui_panel_tool` 将完整 `start_escort_data` 转发给面板工具（避免面板二次请求后端）。

> AI 不直接输出面板 URL。卡片是 inline UI 工具，由 WorkBuddy 在会话区渲染，用户主动点击才打开面板。

### 护航面板（live_escort_dashboard_panel）

**出现时机**：用户在引导卡片点击"打开护航"后，卡片通过 `invoke_ui_panel_tool`（surface=panel）触发，WorkBuddy 在右侧面板区域加载面板 iframe。

**面板数据来源**：卡片转发的 `start_escort_data`，面板从中提取：
- `alive_id`：直播 ID（WS 消息过滤用）
- `b_user_token`：WS 鉴权 token
- `session_id`：护航会话 ID（转 string）
- `app_id`：应用 ID
- `wsUrl`：固定端点 `wss://admin.xiaoe-tech.com/lui/v1/agent/ws-chat`
- `first_check`：首次检查数据（用于初始渲染，不等 WS 第一帧）

**面板渲染内容**：
- **指标网格**：按客户端类型动态展示（标准模式 elive：摄像头/屏幕码率+帧率+延迟；专业模式 elive_pro：码率+帧率+延迟；通用回退：采集帧率+视频码率+推流/下游卡顿+负反馈率+在线人数）
- **趋势折线图**：SVG 渲染，多 tab 切换（码率/帧率等），hover 显示数据点
- **事件记录**：info/warning/alert/recover 事件列表（时间+级别+描述）
- **结束态摘要**：护航结束后展示开始时间/守护时长/整体评估/事件记录，并显示"获取护航报告"按钮
- **连接状态**：实时显示 WS 连接/重连/错误状态

**WS 连接机制**（前端实现，AI 无需介入）：
- 鉴权：`Sec-WebSocket-Protocol: auth_token.{b_user_token}` 子协议字段（浏览器 WS API 不能设自定义 header）
- URL query 兜底：`b_user_token` + `app_id` + `session_id`
- 消息过滤：按 `alive_id` 过滤（非 session_id，因为网关 ws session_id 与护航 session_id 不同）
- 自动重连：3s → 30s → 60s 阶梯退避（10 次后 30s，30 次后 60s）
- 心跳：`sys.ping`/`sys.pong`，连接时收 `sys.hello`（含 `heartbeat_interval_ms`，默认 10s）

### 获取护航报告（面板内触发）

**触发时机**：面板检测到护航结束（`push_state` 变为 0 或 `push_state_text` 含"结束"/"未推流"），渲染结束态摘要 + "获取护航报告"按钮。

**调用方式**：用户点击按钮后，面板通过 `sendMessage` 向会话区发送用户消息：
```
获取当前直播护航报告
```

AI 收到该消息后，识别为护航报告意图，调用 `get_escort_summary`（`alive_id` + `session_id`），将总结报告输出到会话区。

> 面板不直接调 `get_escort_summary`（曾尝试直接 `callServerTool('invoke_tool')` 但遇到 schema 校验和业务错误问题）。改为通过 `sendMessage` 让 AI 代理调用，利用 AI 的意图识别 + 工具调用能力。

### 完整调用时序

```
用户："帮我护航这个直播 l_xxx"
  ↓
AI 识别意图 → 调用 start_live_escort(alive_id=l_xxx)
  ↓
后端返回 { session_id, b_user_token, alive_id, alive_title, escort_mode, first_check, ... }
  ↓
AI 调用 invoke_ui_tool(tool_name=live_escort_guide_card, data=<start-escort 响应>)
  → 会话区渲染引导卡片（标题/店铺/直播名称/描述/按钮）
  ↓
用户点击"打开护航"
  ↓
卡片调用 invoke_ui_panel_tool(tool_name=live_escort_dashboard_panel, args={ start_escort_data: <完整响应> })
  → WorkBuddy 右侧面板加载护航面板 iframe
  ↓
面板从 start_escort_data 提取 wsConfig → 连 WS → 实时渲染指标/趋势/事件
  ↓
（护航期间，后端 Worker 通过 WS 推送实时数据，AI 不介入）
  ↓
护航结束（手动停止/自动停止/直播结束）
  ↓
面板渲染结束态摘要 + "获取护航报告"按钮
  ↓
用户点击"获取护航报告"
  ↓
面板 sendMessage("获取当前直播护航报告") → 会话区出现用户消息
  ↓
AI 识别意图 → 调用 get_escort_summary(alive_id, session_id)
  ↓
AI 输出护航总结报告到会话区
```

## 能力边界

- AI 只做：意图识别 → 调工具 → 输出结果/面板链接
- 持续监控、实时面板推送、告警/心跳消息：由后端 Worker 自动推送（WS），AI 不介入
- 面板内的 UI 交互（卡片点击、面板渲染、报告按钮）由前端自动处理，AI 不需要介入
- 不编造护航数据，不假装调用工具，不输出 tool_call 之外的技术细节
