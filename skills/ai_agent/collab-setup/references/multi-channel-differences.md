# Multi-Channel Differences Framework

## Purpose

Provide the minimum necessary channel-specific knowledge for collaboration setup across different platforms.
This file does NOT replace each channel's full documentation — it only covers the config semantics that differ from Feishu and affect collaboration routing.

## Shared config patterns (all channels)

All supported channels share these core config keys:

| Key | Location | Purpose |
|---|---|---|
| `groupPolicy` | `channels.<ch>.groupPolicy` | `"allowlist"` or `"open"` |
| `groupAllowFrom` | `channels.<ch>.groupAllowFrom` | Array of allowed group IDs |
| `groups.<id>.requireMention` | `channels.<ch>.groups.<id>.requireMention` | Whether bot needs `@` to respond |
| `defaultAccount` | `channels.<ch>.defaultAccount` | Which account handles unmatched messages |
| `dmPolicy` | `channels.<ch>.dmPolicy` or per-account | DM handling policy (`"pairing"` etc.) |
| `accounts.<id>` | `channels.<ch>.accounts.<id>` | Per-account config (multi-bot) |

All channels support multi-account and agent binding via `bindings[]`.

## Channel-specific differences

### Feishu (飞书) — 当前最成熟

- Connection: WebSocket (推荐) or webhook
- Group ID format: `oc_xxxxxxxxxxxx`
- Multi-account: 每个 bot 是独立飞书应用（独立 appId/appSecret）
- Streaming: 支持 `streamResponse: true`
- 特殊能力: interactive cards, inline buttons (需配置 `capabilities.inlineButtons`)
- 群路由稳定模式: 顶层 `channels.feishu` 控制群行为，不在 `accounts.<id>` 下重复
- 已验证的协作模式: main 单入口 + 内部分派 + main 统一收口

### Telegram

- Connection: polling or webhook
- Group ID format: 负数 (如 `-1001234567890`)
- Multi-account: 每个 bot 是独立 Telegram Bot Token
- `requireMention`: 支持，语义与 Feishu 相同
- 特殊点: 
  - 支持 `groups["*"].requireMention` 通配符
  - 群内默认需要 `@botname` 才响应
  - supergroup 和普通 group 的 ID 格式不同
- 群路由: `channels.telegram.groupPolicy` + `channels.telegram.groupAllowFrom`

### Discord

- Connection: WebSocket (Discord Gateway)
- Group ID format: guild ID + channel ID 两层结构
- Multi-account: 每个 bot 是独立 Discord Application
- 特殊点:
  - 群路由是 guild + channel 两级：`channels.discord.guilds.<guildId>.channels`
  - 默认 mention-gated（需要 `@bot`）
  - 支持 thread session (`threadSession`)
- 群路由: `channels.discord.groupPolicy` + guild/channel allowlist

### Slack

- Connection: Socket Mode 或 webhook
- Group ID format: channel ID (如 `C0123456789`)
- Multi-account: 每个 bot 是独立 Slack App
- 特殊点:
  - 群路由按 channel allowlist：`channels.slack.channels`
  - 默认 mention-gated
  - 支持 interactive replies（需配置 `capabilities.interactiveReplies`）
- 群路由: `channels.slack.groupPolicy` + channel allowlist

### WhatsApp

- Connection: WhatsApp Business API
- Group ID format: `xxxxx@g.us`
- Multi-account: 每个号码是独立账号
- 特殊点:
  - `groupPolicy` / `groupAllowFrom` 语义与 Feishu 相同
  - DM 和群消息通过同一号码
  - 无 thread 概念
- 群路由: `channels.whatsapp.groupPolicy` + `channels.whatsapp.groupAllowFrom`

### Signal

- Connection: signal-cli 或 signald
- Group ID format: base64 编码的 group ID
- Multi-account: 每个号码是独立账号
- 特殊点:
  - `groupPolicy` / `groupAllowFrom` 语义与 Feishu 相同
  - 群消息默认不响应，需配置 allowlist
  - 无 inline buttons / interactive cards
- 群路由: `channels.signal.groupPolicy` + `channels.signal.groupAllowFrom`

## Decision impact: what changes per channel

| 决策点 | Feishu | Telegram | Discord | Slack | WhatsApp | Signal |
|---|---|---|---|---|---|---|
| 群ID获取方式 | 飞书管理后台 / API | 从群消息日志读取 | guild+channel ID | channel ID | 群信息 `@g.us` | signal-cli 导出 |
| 默认是否需要@| 可配置 | 默认需要 | 默认需要 | 默认需要 | 可配置 | 可配置 |
| 多bot同群 | 每个bot独立应用 | 每个bot独立token | 每个bot独立app | 每个bot独立app | 同号不支持 | 同号不支持 |
| streaming | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| thread session | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| interactive cards | ✅ | inline keyboard | embed | blocks | ❌ | ❌ |

## Migration checklist: Feishu → other channel

When extending collaboration from Feishu to another channel:

1. [ ] 确认目标 channel 插件已安装且 enabled
2. [ ] 确认目标 channel 的 group ID 格式并获取正确 ID
3. [ ] 配置 `channels.<ch>.groupPolicy` + `groupAllowFrom`
4. [ ] 配置 `channels.<ch>.groups.<id>.requireMention`（按需）
5. [ ] 确认 agent binding 包含新 channel 的 match 规则
6. [ ] 如果是多bot同群，确认每个bot的账号配置独立且不冲突
7. [ ] 验证：DM 正常 → 群消息正常 → 分工派发正常 → 群内收口正常
8. [ ] 记录稳定配置到 workspace docs

## Limitations

- 本框架基于 OpenClaw 2026.3.x 版本源码分析
- 各 channel 的具体 API 限制、rate limit、消息格式差异不在本文件覆盖范围
- 实际部署时应以各 channel 插件的官方文档和 `openclaw doctor` 输出为准
