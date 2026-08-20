# Decision Table

## Purpose

Map user intent + current capability level → concrete action path.
Use this table as the primary routing logic when the skill is triggered.

## How to use

1. Classify the user request (column A)
2. Detect current capability level (column B)
3. Follow the prescribed action (column C)
4. Check the referenced file for details (column D)

## Table

| A: User Intent | B: Current Level | C: Action | D: Reference |
|---|---|---|---|
| 从头配置多 agent 协作 | Level 0 (single-agent) | 引导创建额外 agent + 基础 binding | `multi-agent-onboarding-playbook.md` |
| 从头配置多 agent 协作 | Level 1 (multi-agent, no group) | 引导创建协作群 + 配置群路由 | `feishu-group-routing-spec.md` |
| 从头配置多 agent 协作 | Level 2+ (有群) | 检查当前群路由是否健康，补缺即可 | `diagnostic-flow.md` Step 2 |
| 配置协作群 / 设置默认同步群 | Level 0-1 | 先确认 agent 数量，再建群 + 路由 | `multi-agent-onboarding-playbook.md` |
| 配置协作群 / 设置默认同步群 | Level 2 | 直接配置 default sync group | `multi-agent-config-templates.md` |
| 分工处理不生效 | Level 0 | 降级为单 agent 执行，说明缺 agent | `diagnostic-flow.md` Step 5 |
| 分工处理不生效 | Level 1 | 检查 agent binding + sessions_send 连通性 | `task-dispatch-sync-modes.md` |
| 分工处理不生效 | Level 2+ | 检查群路由 + 群内可见性 + 收口逻辑 | `feishu-group-routing-spec.md` |
| 群里不回复 | 任意 | 先检查 groupPolicy/allowlist/requireMention | `feishu-group-routing-spec.md` |
| 群里不回复 | 任意 | 再检查 bot 是否在群内 + 账号绑定 | `diagnostic-flow.md` Step 2 |
| 超时 / 回执丢失 | Level 1+ | 检查 sessions_send 超时处理 + 兜底逻辑 | `task-dispatch-sync-modes.md` |
| 想换同步群 / 多群同步 | Level 2 | 升级到 Level 3：配置多 sync group | `multi-agent-config-templates.md` |
| 行为策略调整（不涉及配置） | Level 2+ | 走 workflow policy 路径，不改 config | `workflow.md` Step 2 |

## Cross-channel routing

| A: User Intent | B: Current Channel | C: Action | D: Reference |
|---|---|---|---|
| 在 Telegram 配置协作 | Telegram | 确认 group ID（负数）+ groupPolicy + allowlist | `multi-channel-differences.md` |
| 在 Discord 配置协作 | Discord | 确认 guild+channel 两级结构 + allowlist | `multi-channel-differences.md` |
| 在 Slack 配置协作 | Slack | 确认 channel ID + groupPolicy + channel allowlist | `multi-channel-differences.md` |
| 在 WhatsApp 配置协作 | WhatsApp | 确认 @g.us 群 ID + groupPolicy + allowlist | `multi-channel-differences.md` |
| 在 Signal 配置协作 | Signal | 确认 base64 群 ID + groupPolicy + allowlist | `multi-channel-differences.md` |
| 从 Feishu 迁移到其他渠道 | 任意 | 走 migration checklist | `multi-channel-differences.md` |

## Edge cases

| Situation | Action |
|---|---|
| 用户说"分工"但只有 1 个 agent | 不伪装分工，直接单 agent 执行 + 说明 |
| 用户要求非 Feishu 渠道协作 | 先读 `multi-channel-differences.md`，确认该渠道 config 语义差异 |
| 检测到 config 语法错误 | 先修语法，再继续诊断 |
| 检测到 gateway 不健康 | 先恢复 gateway，再继续配置 |
| 用户环境有 workspace 双层结构 | 必须同时检查 agent-side 和 project-side workspace |
| 目标渠道不支持 thread/streaming/cards | 降级处理，说明该渠道限制 |

## Decision priority

When multiple paths match:
1. 先修阻塞性问题（gateway down > config syntax > routing broken）
2. 再补缺失层级（Level 0→1→2→3）
3. 最后调行为策略
