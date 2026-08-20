# 去 AI 味 · 真人评估 API 契约（v0.2.0）

> 对齐 `content-quality-service` deai 模块当前实现。
> Base URL：`https://claw.lingyishuke.com/services`
> 路径前缀：`/api/v1/content-quality/deai`

## 概述

本接口提供**异步**的「去 AI 味改写」与「真人评估」能力。按 skill 交互节奏，**改写与评估分两次调用**：

| 步骤 | mode | 输入 text | 输出 markdown | 计费 |
|------|------|-----------|---------------|------|
| 1. 改写 | `rewrite` | 原文 | `## 去 AI 味改写` 段 | 按 LLM token 扣点 |
| 2. 评估 | `eval` | **改写终稿**（或用户指定待评估稿） | `## 真人评估` 段 | 按 LLM token 扣点 |

### 接口一览

| 接口 | Method | 路径 |
|------|--------|------|
| 创建/恢复任务 | `POST` | `/api/v1/content-quality/deai/tasks` |
| 查询任务 | `GET` | `/api/v1/content-quality/deai/tasks/{task_id}` |
| 重试失败任务 | `POST` | `/api/v1/content-quality/deai/tasks/{task_id}/retry` |

完整 URL 示例：

```text
https://claw.lingyishuke.com/services/api/v1/content-quality/deai/tasks
https://claw.lingyishuke.com/services/api/v1/content-quality/deai/tasks/{task_id}
https://claw.lingyishuke.com/services/api/v1/content-quality/deai/tasks/{task_id}/retry
```

### 鉴权

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 是 | `Bearer <API_KEY>`；也兼容裸 key：`Authorization: <API_KEY>` |
| `Content-Type` | POST 时建议 | `application/json` |
| `X-Idempotency-Key` | 否 | 幂等键；与 body `idempotency_key` 二选一，**body 优先** |

API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。

### 通用响应外壳

所有接口成功时均为统一外壳 + `data`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `api_version` | string | `v1` |
| `result` | string | 成功为 `"success"` |
| `code` | int | 成功为 `200` |
| `message` | string | 成功多为 `"Success"` |
| `timestamp` | string | ISO 日期时间 |
| `data` | object \| null | 业务数据，见下文 |

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "Success",
  "timestamp": "2026-07-18T10:00:00.000000",
  "data": {}
}
```

### 常见 HTTP 状态

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 请求被接受（业务是否成功看 `data.status`） | — |
| 400 | 参数/幂等冲突等业务校验失败 | 3 |
| 401 | 缺/无效 API Key | 8 |
| 402 | 余额不足（网关或服务返回时） | 4 |
| 404 | task 不存在（查询/重试） | 10 |
| 422 | 请求体校验失败（缺 `mode`、text 空等） | 3 |
| 5xx | 服务内部错误 | 11 |

---

## 1. 异步任务模型

1. **创建/重试立即返回**：`status` 多为 `pending` / `running`，`markdown` 可能为空字符串。
2. **客户端轮询**：对同一 `task_id` 调用 GET，建议间隔 3～5s，直到终态。
3. **终态**：`succeeded` / `failed` / `billing_failed`。
4. **成功交付**：读 `data.markdown`（已渲染 Markdown）。

### `data.status` 枚举

| 值 | 含义 | 客户端建议 |
|----|------|------------|
| `pending` | 已落库，待执行 | 继续轮询 |
| `running` | 执行中 | 继续轮询 |
| `succeeded` | 成功且结算成功 | 交付 `markdown` + 告知扣点 |
| `failed` | 执行失败 | 可 `retry` 或新建任务 |
| `billing_failed` | 内容可能已生成，但扣点失败 | 可 `retry`（仅重试扣点） |

### `data.mode` 枚举

| 值 | 含义 |
|----|------|
| `rewrite` | 仅去 AI 味改写 |
| `eval` | 仅真人评估 |

---

## 2. 创建/恢复任务

`POST /api/v1/content-quality/deai/tasks`

落库后**立即**返回 `task_id`。相同 `account + idempotency_key` 且请求内容一致时会恢复已有任务。

### 请求体字段

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `text` | string | 是 | — | 1～20000，strip 后非空 | `rewrite`=原文；`eval`=改写稿或待评估稿 |
| `mode` | string | **是** | — | `rewrite` \| `eval` | 单步能力，不可省略 |
| `platform` | string | 否 | `xhs` | `xhs` \| `channels` \| `mp` \| `dy` | 小红书 / 视频号 / 公众号 / 抖音 |
| `options` | object | 否 | `{}` | — | **仅 `mode=eval` 生效** |
| `options.personas` | string[] | 否 | `[]` | — | 空则后端默认 5 类人设 |
| `options.comment_count` | int | 否 | `6` | 1～20 | 评论名额；其他声音条数 = max(0, count − 读者数) |
| `idempotency_key` | string | 否 | 服务端 UUID | 1～128 | 幂等键；与 Header 二选一，body 优先 |

改写请求示例：

```json
{
  "text": "在数字化浪潮持续奔涌的当下，我们正站在一个前所未有的关键节点上……",
  "mode": "rewrite",
  "platform": "xhs",
  "idempotency_key": "client-uuid-rewrite-001"
}
```

评估请求示例：

```json
{
  "text": "姐妹们，最近我迷上了研究怎么把健康管理这件事变简单……",
  "mode": "eval",
  "platform": "xhs",
  "options": {
    "personas": ["25-34-女-白领-高消费", "35-44-女-宝妈-中消费"],
    "comment_count": 6
  },
  "idempotency_key": "client-uuid-eval-001"
}
```

### 响应 `data`（`DeaiTaskResponse`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID（UUID） |
| `status` | string | 见枚举 |
| `mode` | string \| null | `rewrite` / `eval` |
| `markdown` | string | 成功时为报告正文；进行中/失败可能为空字符串 |
| `billing_status` | string | `pending` / `settled` / `failed` |
| `billing` | object \| null | 计费摘要；未结算时多为 `null` |
| `billing.total_points` | string | **本次实际扣点数**（字符串），如 `"12"`、`"15"` |
| `failure_code` | string \| null | `DEAI_FAILED` / `BILLING_FAILED` / `ATTEMPTS_EXCEEDED` |
| `failure_message` | string \| null | 失败说明 |

创建成功（进行中）示例：

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "data": {
    "task_id": "e4bd4f6d-2f32-4825-8fa2-431b58470323",
    "status": "pending",
    "mode": "rewrite",
    "markdown": "",
    "billing_status": "pending",
    "billing": null,
    "failure_code": null,
    "failure_message": null
  }
}
```

rewrite 终态成功示例：

```json
{
  "data": {
    "task_id": "e4bd4f6d-2f32-4825-8fa2-431b58470323",
    "status": "succeeded",
    "mode": "rewrite",
    "markdown": "## 去 AI 味改写\n\n姐妹们，最近我迷上了研究怎么把健康管理这件事变简单。……\n\n**改动小结**\n\n去掉营销通稿腔与赋能黑话，改成小红书口语体验……",
    "billing_status": "settled",
    "billing": { "total_points": "12" },
    "failure_code": null,
    "failure_message": null
  }
}
```

eval 终态成功示例：

```json
{
  "data": {
    "task_id": "7a03d7cd-321f-4626-9973-25798fc1418b",
    "status": "succeeded",
    "mode": "eval",
    "markdown": "## 真人评估\n\n> 人味总评：目标读者普遍觉得像真人分享，可发（均分 8.0/10）\n\n### 👩‍💼 25-34 · 女 · 白领 · 高消费\n> ……",
    "billing_status": "settled",
    "billing": { "total_points": "15" },
    "failure_code": null,
    "failure_message": null
  }
}
```

### markdown 形态

**rewrite 成功**：`## 去 AI 味改写` + 改写终稿正文 + `**改动小结**` + 可选 `**待核实内容**`

**eval 成功**：`## 真人评估` + 人味总评 + 人群卡片（含 human_score/ai_suspect）+ 其他声音。完整渲染规格见 [persona-eval-prompt.md](persona-eval-prompt.md)。

---

## 3. 查询任务

`GET /api/v1/content-quality/deai/tasks/{task_id}`

响应与创建接口相同的 `DeaiTaskResponse`。HTTP 200 仅表示查询成功，任务是否成功看 `data.status`。

task 不存在：HTTP 404。

---

## 4. 重试失败任务

`POST /api/v1/content-quality/deai/tasks/{task_id}/retry`

异步重试，**立即返回当前快照**，客户端继续 GET 轮询。沿用创建时的 `mode` / `text` / `platform` / `options`。

| 当前 status | retry 行为 |
|-------------|------------|
| `succeeded` | **不重跑**，直接返回原结果 |
| `billing_failed` 且已有 `markdown` | **只重试扣点**，不再调 LLM |
| `failed` | 按原 `mode` **重新入队**执行 LLM |
| `running` 且租约未过期 | 可能抢不到执行权 |
| 超过最大尝试次数（默认 3） | 不再执行，保持失败 |

---

## 5. 扣点字段

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.billing.total_points` | string | 唯一正式实扣字段 |

- 两种 mode 均按 LLM token 计点，结算后写 `billing.total_points`
- 脚本优先读此字段；未命中则 `HUMAN_EVAL_POINTS_USED` 留空，assistant 按约定估值说明
- 约定预估（仅提示，非实扣）：rewrite 约 12 点 / eval 约 15 点；实际以最终完成任务时的点数为准

---

## 6. 枚举速查

| 字段 | 取值 |
|------|------|
| `platform` | `xhs`（小红书）、`channels`（视频号）、`mp`（公众号）、`dy`（抖音） |
| `mode` | `rewrite`（改写）、`eval`（评估） |
| `status` | `pending` / `running` / `succeeded` / `failed` / `billing_failed` |
| `sentiment` | `正`、`中`、`负` |
| `action` | `会看完`/`会划走`/`想试`/`想囤`/`观望`/`不感兴趣`/`会点赞`/`会转发` |
| `human_score` | 0–10 整数 |

---

## 7. 集成注意事项

1. **不要**在一次请求里期望同时拿到改写+评估；必须分 `mode` 两次调用。
2. **不要**并发多次创建相同 eval（会导致多次扣点）。
3. 对外只依赖 `markdown` + `billing.total_points` 即可完成 skill 交付。
4. `retry` 不会改 `mode`，也不能把 rewrite 任务变成 eval。
5. rewrite 与 eval **必须用不同 `idempotency_key`**；相同 key + 不同 body → 400 冲突。
6. 人群格式、默认人设、评论条数语义与「爆款内容预检」persona 模块一致，详见 [persona-eval-prompt.md](persona-eval-prompt.md)。
