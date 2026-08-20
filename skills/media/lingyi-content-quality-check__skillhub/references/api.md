# 内容质检 API 契约（v0.3.0 · 异步任务）

**异步任务模型**：创建/重试立即返回 `task_id`，客户端用 `GET` 轮询进度与结果。

base url 固定 `https://claw.lingyishuke.com/services`（写死在脚本里，可用环境变量 `LY_BASE_URL` 覆盖）。

鉴权：`Authorization: Bearer <api_key>`。另带 `X-Appbuilder-From: openclaw`、`Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。

幂等：Header `X-Idempotency-Key` 和/或 body `idempotency_key`（body 优先）；缺省服务端生成 UUID。同一 account + 同一幂等键下，text/platform/modules/options 必须一致。

脚本流程：`POST /tasks` → 立即拿 `task_id` → `GET /tasks/{id}` 轮询 → 终态交付。失败可 `POST /retry` 后再轮询（已成功模块不重跑）。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| **创建/恢复任务** | `POST` | `/api/v1/content-quality/tasks` | **主路径**（立即返回） |
| **查询任务** | `GET` | `/api/v1/content-quality/tasks/{task_id}` | **轮询进度与结果** |
| 重试失败模块 | `POST` | `/api/v1/content-quality/tasks/{task_id}/retry` | `--retry-task`（立即返回，再 GET） |

## 通用响应外壳

成功：

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "Success",
  "timestamp": "2026-07-10T15:57:00.893695",
  "data": {}
}
```

失败：

```json
{
  "api_version": "v1",
  "result": "error.internal",
  "code": 422,
  "message": "Request validation failed",
  "timestamp": "...",
  "detail": null,
  "trace_id": null
}
```

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功（业务 status 另判） | — |
| 400 | 参数/幂等键冲突等 | 3 |
| 401 | 缺/无效 API Key | 8 |
| 402 | 余额不足（若网关返回） | 4 |
| 404 | task 不存在 | 10 |
| 422 | 校验失败（空 text、非法 platform、超长等） | 3 |
| 5xx | 服务内部错误 | 11 |

---

## 1. 创建/恢复任务（异步）

`POST /api/v1/content-quality/tasks`

落库后**立即**返回 `data`（含 `task_id`）。模块在后台执行；客户端必须用 GET 轮询至终态。

### 请求体

```json
{
  "text": "我们的面膜是全网最好用的，包治百病，赶紧下单！",
  "platform": "channels",
  "modules": ["compliance", "persona", "burst"],
  "options": {
    "personas": ["25-34-女-白领-高消费", "35-44-女-宝妈-中消费"],
    "comment_count": 6
  },
  "idempotency_key": "client-uuid-or-stable-key"
}
```

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `text` | string | 是 | — | 1–20000，strip 后非空 | 待检文本 |
| `platform` | string | 否 | `channels` | `channels` \| `mp` | 视频号 / 公众号 |
| `modules` | string[] | 是 | — | ≥1；`compliance` / `persona` / `burst` | 服务端按固定顺序执行 |
| `options` | object | 否 | `{}` | — | 主要给 persona |
| `options.personas` | string[] | 否 | `[]` | — | 空则后端默认 5 类人设 |
| `options.comment_count` | int | 否 | `6` | 1–20 | 其他声音条数 = max(0, count − 人群数) |
| `idempotency_key` | string | 否 | — | 1–128 | 与 Header 二选一；重复提交保持不变 |

Header 可选：`X-Idempotency-Key: <same-key>`。

### 响应 `data`

创建成功时多为进行中状态（`pending` / `running`），`results` 可能尚不完整：

```json
{
  "task_id": "uuid",
  "status": "running",
  "modules": ["compliance", "persona", "burst"],
  "current_module": "compliance",
  "results": {},
  "billing_status": "pending",
  "billing": null,
  "failure_code": null,
  "failure_message": null
}
```

终态 `succeeded` 时示例：

```json
{
  "task_id": "uuid",
  "status": "succeeded",
  "modules": ["compliance", "persona", "burst"],
  "current_module": null,
  "results": {
    "compliance": {
      "markdown": "## 合规检测\n...",
      "data": { "conclusion": "⚠️", "risk_level": "中", "summary": "...", "sensitive_hits": [], "ad_law_hits": [], "reminders": [] }
    },
    "persona": {
      "markdown": "## 观众反应沙盘\n...",
      "data": { "persona_feedback": [], "user_comments": [] }
    },
    "burst": {
      "markdown": "## 爆款概率预测\n...",
      "data": { "score": 7.5, "grade": "A", "reason": "...", "dimensions": [] }
    }
  },
  "billing_status": "settled",
  "billing": { "total_points": "18" },
  "failure_code": null,
  "failure_message": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID；轮询与重试都靠它 |
| `status` | string | 见下方枚举 |
| `modules` | string[] | 规范化后的模块列表（固定顺序） |
| `current_module` | string \| null | 进行中模块；完成时 null |
| `results.<module>` | object | **统一形状** `{ markdown, data }` |
| `results.<module>.markdown` | string | 该模块已渲染 MD，从 `##` 起。**正文不含免责语** |
| `results.<module>.data` | object | 结构化结果（见第 4 节）；失败时可能为 `{ status, error_type, error_message }` |
| `billing_status` | string | 如 `pending` / `settled` / `failed` |
| `billing` | object \| null | 正式扣点摘要 |
| `billing.total_points` | string | **本次实际扣点数（字符串）**，如 `"18"` |
| `failure_code` | string \| null | 失败码，如 `MODULE_FAILED` / `BILLING_FAILED` |
| `failure_message` | string \| null | 失败说明 |

> **不返回**外层整份总报告 `markdown`。脚本按 `modules` 顺序取 `results[m].markdown`，顶部加 `# 质检报告：…`，段间 `\n\n---\n\n` 拼接。

### `status` 枚举

| 值 | 含义 | 脚本处理 |
|----|------|----------|
| `pending` | 待执行 | 继续轮询 |
| `running` | 执行中 | 继续轮询，stderr 打进度 |
| `succeeded` | 全部成功且结算成功 | 交付报告 + 实扣 |
| `failed` | 无成功模块 | 退出码 12 |
| `partial_failed` | 部分模块成功 | 默认退出码 12；`--allow-partial` 可交付已有段落 |
| `billing_failed` | 模块成功但扣点失败 | 退出码 12 |

---

## 2. 查询任务（进度轮询）

`GET /api/v1/content-quality/tasks/{task_id}`

响应 `data` 形状与创建相同。脚本默认每约 5s 轮询，直到 `status` 为终态；单次 HTTP 超时 60s，全链路最长等待默认 180s。

进度字段：

| 字段 | 用途 |
|------|------|
| `status` | `pending` / `running` / 终态 |
| `current_module` | 当前正在执行的模块（完成时 `null`） |
| `results.<module>.markdown` | 已完成模块会有内容；未完成可能为空 |

---

## 3. 重试失败模块（异步）

`POST /api/v1/content-quality/tasks/{task_id}/retry`

- **立即**返回当前快照；客户端继续 GET 轮询
- 已成功模块 **不会** 重复调用
- 从失败模块继续；全部成功后统一结算
- 脚本：`python3 scripts/quality_check.py --retry-task <task_id> --out ./质检报告.md`

---

## 4. 扣点字段

```json
"billing": {
  "total_points": "18"
}
```

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.billing.total_points` | string | **唯一正式实扣字段** |

- 任务级汇总：一次提交只扣一次（成功结算后）
- 内部 token/公式明细不对外暴露
- 脚本优先读 `data.billing.total_points`；未命中则 `CONTENT_QUALITY_POINTS_USED` 留空，由 assistant 按约定估值「约 N 点」说明

约定预估（仅提示，非实扣）：compliance 8 / persona 22 / burst 8 / 全跑约 38；实际消耗以最终完成任务时的点数为准。

---

## 5. 各模块 `results.<module>.data` 结构

### 5.1 compliance

| 字段 | 类型 | 说明 |
|------|------|------|
| `conclusion` | string | 词库结论 `✅` / `⚠️` / `❌`（权威） |
| `risk_level` | string | `无` / `低` / `中` / `高` |
| `summary` | string | 建设性总体说明 2–4 句 |
| `sensitive_hits` | array | 敏感词命中；无命中为 `[]` |
| `ad_law_hits` | array | 广告法命中；无命中为 `[]` |
| `reminders` | array | 平台合规提醒 `{text}`；可空 |

`sensitive_hits[]`：`word` / `category` / `severity`(`high|medium|low`) / `platform` / `positions` / `count` / `suggestion`

`ad_law_hits[]`：`word` / `clause` / `severity` / `positions` / `count` / `reason` / `suggestion`

### 5.2 persona

| 字段 | 类型 | 说明 |
|------|------|------|
| `persona_feedback` | array | 人群卡片，顺序与传入人群一致 |
| `user_comments` | array | 其他声音；条数 = max(0, comment_count − 人群数) |

`persona_feedback[]`：`persona` / `identity` / `reaction` / `comment` / `sentiment`(`正|中|负`) / `action`（`会看完`/`会划走`/`想试`/`想囤`/`观望`/`不感兴趣`/`会点赞`/`会转发` 等 1–3 个）

`user_comments[]`：`sentiment` / `comment`

默认人设（`personas` 为空时）：

- `18-24-女-学生-中消费`
- `25-34-女-白领-高消费`
- `35-44-女-宝妈-中消费`
- `25-34-男-白领-中消费`
- `45+-男-退休-低消费`

人群格式：`年龄段-性别-职业-消费层级`。

### 5.3 burst

| 字段 | 类型 | 说明 |
|------|------|------|
| `score` | number | 综合分 0–10（一位小数） |
| `grade` | string | `S` / `A` / `B` / `C` |
| `reason` | string | 总体评估 2–4 句 |
| `dimensions` | array | 7 项（6 个 0–10 维度 + 1 个合规风险） |

`dimensions[]`：

| 字段 | 说明 |
|------|------|
| `name` | `钩子力`/`选题与情绪价值`/`受众广度`/`记忆点与传播性`/`结构与节奏`/`平台适配度`/`合规风险` |
| `score` | 0–10；仅「合规风险」为 `null` |
| `comment` | 针对文本的点评 |
| `conclusion` | 仅「合规风险」：`✅`/`⚠️`/`❌`；其余项省略 |

---

## 6. 枚举速查

| 字段 | 取值 |
|------|------|
| `platform` | `channels`（视频号）、`mp`（公众号） |
| `modules` | `compliance`、`persona`、`burst`（执行顺序固定） |
| `severity` | `high`、`medium`、`low` |
| `conclusion` | `✅`、`⚠️`、`❌` |
| `risk_level` | `无`、`低`、`中`、`高` |
| `grade` | `S`、`A`、`B`、`C` |
| `sentiment` | `正`、`中`、`负` |
| 任务 `status` | `pending` / `running` / `succeeded` / `failed` / `partial_failed` / `billing_failed` |
