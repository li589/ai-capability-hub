---
name: wecom-weisheng-scrm
description: "当用户需要查询或管理微盛企微管家（企业微信） SCRM 中的客户信息、客户标签、客户群、营销素材、活码、群发、跟进记录、聊天记录、会话存档、联系人、商机、汇报、抽奖、客户日程、客户画像等相关业务能力时触发。即使用户未明确提到 SCRM、企微管家、开放接口或 API，也应在这些企业微信客户运营与管理场景下触发。"
description_zh: "微盛AI·企微管家提供的技能，帮助用户查询和管理企业微信 SCRM 中的客户、客户群、标签、活码、群发、跟进、聊天记录内容等业务数据，可询问AI当前支持的能力清单。"
description_en: "Built for WeCom customer operations, helping teams review customer and group activity, prepare campaign assets, and move follow-up, messaging, and opportunity workflows forward."
version: 1.0.6
display_name: "微盛企微管家SCRM"
display_name_en: "Wecom Weisheng SCRM"
visibility: "public"
---

# 微盛企微管家SCRM

微盛企微管家 SCRM 面向企业微信客户运营场景，帮助团队围绕客户、社群、素材、活码、群发、会话与商机等业务，更高效地完成查询、协同与执行。

本 Skill 适用于客户信息、客户标签、客户群、素材、活码、群发、跟进记录、会话存档、联系人、商机、产品库、汇报、抽奖、日程、客户画像等场景。你可以直接用业务语言提出问题，例如"帮我查最近7天新添加的客户""看看某个客户的标签和跟进情况""帮我查客户群或群发情况"。

## 使用说明

触发 Skill 后，应先用简短话术向用户说明：微盛AI·企微管家 SCRM 是基于企业微信的 AI 聊天、营销和服务平台，可协助客户运营、社群营销、SCRM 与会话管理，本技能支持查询或管理客户信息、客户标签、客户群、素材、活码、群发、跟进记录、会话存档、联系人、商机、汇报、抽奖、客户日程、客户画像等相关能力；如需进一步支持，可联系专属客服。

**触发 Skill 后，必须先阅读 [references/agent-runbook.md](references/agent-runbook.md) 并严格按其中的调用流程执行（包括 `check-env` → `check-identity` 的顺序），不得跳过或自行编排步骤。**

### 推荐提问方式

- 帮我查一下最近新增客户和重点跟进客户的情况。
- 帮我看看这个客户的标签、跟进记录和聊天情况。
- 帮我整理一下当前客户群和群发相关情况。
- 帮我看一下最近活码和素材相关情况。

### 处理原则

- 默认使用业务语言回复用户，先说结论，再说明还缺什么信息或下一步怎么处理。
- 如需补充条件，优先向用户追问时间范围、客户名称、标签、员工、群发范围等业务信息。
- 查询类需求可直接处理；创建、编辑、删除、发送等写操作应在用户确认后再执行。
- 若用户当前所在模式无法执行命令或脚本，应先提示切换到具备执行能力的模式。
- `call-api` 必须先通过 `fetch-raw-doc` 读取对应接口文档（已读缓存有效期 2 小时），无有效缓存时脚本自动拒绝调用。
- `call-api` 以 `--doc-url` 为唯一文档绑定参数，`service_name`、`uri`、`method` 由脚本自动补齐，不再需要 AI 手动传入。
- 直接执行命令时，仍然使用 `python3 scripts/scrm.py <command>` 或等价的 `$SCRM_PYTHON "$SCRM_SCRIPT" <command>`。
- 只有在运行时需要用 Python 继续解析 `scrm.py` 的 JSON 输出时，才优先使用 `scripts/scrm_sdk.py`；不要手写 `subprocess + json.loads(stdout)`。

对普通用户回复时，不要主动暴露 `service_name`、`api_path`、`doc_url`、`biz_params`、JSON、代理调用等内部术语，除非用户明确要求查看。

## 安全与隐私

本 Skill 需要你的企微管家 APP KEY 授权。KEY 仅保存在本地设备（Shell 配置 / Windows 注册表），不会上传到 QClaw 服务器或任何第三方。

- 获取：企业微信 → 工作台 → 企微管家 → 我的 → 我的 APP KEY
- 撤销：在企微管家后台重置 APP KEY，或执行 `python3 scripts/scrm.py set-app-key ""`

### 企微机器人场景自动初始化

当在企微智能机器人对话中触发本 Skill 且尚未配置 `SCRM_APP_KEY` 时，本 Skill 会用对话上下文中的员工身份（`sender_id` + `bot_id`）自动向 SCRM 开放平台申请并持久化 APP KEY，无需用户手动填写（命令：`setup-context` / `get-bot-id`）。该能力原为独立的 `wecom-weisheng-robot` Skill，现已合并入本 Skill；普通 CLI / IDE 场景不触发此流程，仍由用户手动 `set-app-key`。

## 文档索引

| 文档 | 说明 |
|------|------|
| [references/guide.md](references/guide.md) | 使用参考与常见业务场景 |
| [references/examples.md](references/examples.md) | 示例问题与使用示例 |
| [references/agent-runbook.md](references/agent-runbook.md) | AI 执行手册（流程、命令参考、权限、错误处理、数据依赖） |
| [references/file-utils.md](references/file-utils.md) | 文件上传与下载（本地图片转公网 URL），涉及图片/文件操作时参考 |

## 安装

- **QClaw 用户**：本 Skill 已上架 QClaw，
  无需手动安装，可在 **设置 → 技能管理** 直接启用。
- **其他宿主（如 OpenClaw）**：执行 `./install.sh install`
  创建软链接到对应 skills 目录。
