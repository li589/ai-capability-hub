---
name: duoguan-fengchao
description: 夺冠蜂巢 AI 自媒体内容运营。从选题策划、文案撰写、图片配图到播客配音、视频封装一站式内容生产。用户要做抖音/小红书/公众号/视频等内容创作时使用。
---

# 夺冠蜂巢（Duoguan Fengchao）

夺冠蜂巢是 AI 自媒体内容运营平台，通过 `duoguan-fengchao-mcp` 提供标准 MCP 工具，覆盖内容生产的完整链路。

## 连接

MCP 未连接时读取 `https://fc.duoguan.com/agent-kit/manifest.json`，执行 `persistentInstall.bootstrap` 安装本地 Launcher，把返回的 `mcpConfig` 写入客户端。Agent Key 只写入环境变量 `DUOGUAN_FENGCHAO_API_TOKEN`，不要当作 Bearer Token 请求 manifest，不要连接远程 SSE。

连接后先调用 `system.health` 和 `account.context` 确认身份、租户与权限，再开始内容生产。

## 核心工具分组

| 分组 | 工具前缀 | 用途 |
|------|---------|------|
| 系统与上下文 | `system.*` / `account.*` / `work_context.*` | 健康检查、身份、当前选中分支 |
| 内容大脑 | `brain.*` / `personal_workspace.*` | 品牌画像、业务方向、资料初始化 |
| 内容成员 | `member.*` / `creator_brand.*` | 多账号成员入驻与画像 |
| 选题 | `topic.*` | 热点选题生成、研究、候选文案 |
| 文案 | `script.*` | 口播/图文文案生成、定稿 |
| 配图 | `image.*` | 小红书/图文配图生成 |
| 风格资产 | `opening_hook.*` / `content_style.*` / `visual_style.*` | 钩子、文案风格、视觉风格 |
| 媒体 | `media_asset.*` / `recording.*` | 素材上传、字幕、录制 |
| 音视频 | `podcast.*` / `voice.*` / `video_packaging.*` | 播客、配音、视频封装 |
| 发布 | `publish.*` / `platform_account.*` | 多平台发布与数据回传 |

## 典型工作流

1. **初始化内容大脑**：`brain.initialize` 或 `personal_workspace.organize` 录入品牌资料 → 生成画像。
2. **选题**：`topic.generate` 生成选题 → 用户选择 → `work_context.select_topic` 记录当前选题。
3. **文案**：`script.generate` 生成候选文案 → 用户反馈修订 → `script.finalize` 定稿。
4. **配图**：`image.generate_all` 为定稿文案生成封面/配图。
5. **音视频**：`podcast.generate` 生成播客音频，或 `video_packaging.create` 封装成片。
6. **发布**：`publish.create` 发布到抖音/小红书等平台，`metric.snapshot` 回传数据。

每个工具的具体参数以 MCP 返回的 schema 为准。生成类工具优先用 `wait=true`；返回超时表示任务仍在执行，按 `retryAfterMs` 查询，不要编造进度。

## Token 失效处理

当 MCP 返回认证失败（`AUTH_FAILED` / `INVALID_TOKEN`）时，说明 Agent Key 已失效或被吊销。引导用户：

1. 登录夺冠蜂巢 → 设置 → 创建 Agent；
2. 复制新的 `ca_live_` 开头完整凭证；
3. 在 WorkBuddy 连接器配置中重新填入 Agent Key（每次连接 MCP 时会读取最新凭证，无需重启 WorkBuddy）。

不要在对话中要求用户提供 Agent Key 明文，也不要把 Key 写入日志或对话记录。
