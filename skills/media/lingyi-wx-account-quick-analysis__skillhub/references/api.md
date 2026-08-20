# 微信视频号账号拆解（付费版）API 契约（v0.1.0 · 异步任务 · 账号快拆）

**异步任务模型**：创建立即返回 `task_id`，客户端用 `GET` 轮询进度与结果。

> 该接口为「账号**快拆**」（`wx-video-account-quick-analysis`），与全量「账号拆解」（`wx-video-account-analysis`）是两套独立路径，`task_id` 凭证**互不通用**，不可用拆解接口的 task_id 查询快拆，反之亦然。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。

鉴权：`Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw` + `Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。

幂等：Header `X-Idempotency-Key` 和/或 body `idempotency_key`（body 优先）；缺省脚本生成 UUID。

脚本流程：`POST /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis` → 立即拿 `task_id` → `GET /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis/{id}` 轮询 → 终态交付。

> **与标准范式的偏差**：① 输入是 `account_name`（账号名）而非 `text`；② 成功终态为 `completed`（非 `succeeded`）；③ 完成态报告 markdown 由后端预渲染、自带一级标题，落在顶层 `data.markdown`；④ 实扣点数字段为 `data.total_points`（number，顶层），非 `data.billing.total_points`（string）；⑤ **本接口只提供「创建 + 查询」两个端点，无重试端点**——任务失败后由调用方用原账号名重新 `--only-create` 发起（重新计费）。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 创建任务 | `POST` | `/api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis` | 主路径（立即返回） |
| 查询任务 | `GET` | `/api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis/{task_id}` | 轮询进度与结果 |
| 重试失败模块 | — | **本接口未提供** | 无。失败后重新发起 |

## 通用响应外壳

成功：

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "微信视频号账号快拆任务创建成功",
  "timestamp": "2026-07-31T12:00:00.000000",
  "data": {}
}
```

失败：

```json
{
  "api_version": "v1",
  "result": "error.bad_request",
  "code": 400,
  "message": "account_name 不能为空",
  "timestamp": "2026-07-31T12:00:00.000000"
}
```

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功（业务 status 另判） | — |
| 400 | 参数无效（account_name 为空等） | 3 |
| 401 | API Key 无效或缺失 | 8 |
| 402 | 点数不足 | 4 |
| 403 | 无权访问该 task_id | 10 |
| 404 | 任务不存在 | 10 |
| 5xx / 502 | 服务暂时不可用 / 服务内部错误 | 11 |

---

## 1. 创建任务（异步）

`POST /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis`

落库后立即返回 `data`（含 `task_id`）。后续在后台执行；客户端必须用 GET 轮询至终态。

### 请求头

| Header | 必填 | 说明 |
|------|------|------|
| `Authorization` | 是 | `Bearer <API_KEY>` |
| `Content-Type` | 创建接口必填 | `application/json` |

### 请求体

```json
{
  "account_name": "央视新闻",
  "idempotency_key": "client-uuid-or-stable-key"
}
```

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `account_name` | string | 是 | — | 非空 | 视频号账号名称（昵称） |
| `platform` | string | 否 | — | — | 平台，可不传；本期固定按微信视频号处理。**可引导但不强制、缺省不传** |
| `idempotency_key` | string | 否 | — | 1–128 | 与 Header `X-Idempotency-Key` 二选一；重复提交保持不变 |

### 响应 `data`

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID；轮询靠它，原样保存。须用创建时的同一 API Key |
| `status` | string | 见下方枚举，创建后通常为 `pending` |

成功示例：

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "微信视频号账号快拆任务创建成功",
  "timestamp": "2026-07-31T12:00:00.000000",
  "data": {
    "task_id": "eyJvcHNfdGFza19pZCI6Li4uIn0.xxxxx",
    "status": "pending"
  }
}
```

### `status` 枚举

| 值 | 含义 | 是否终态 | 脚本处理 |
|----|------|----------|----------|
| `pending` | 排队中 | 否 | 继续轮询 |
| `running` | 执行中 | 否 | 继续轮询，stderr 打进度 |
| `completed` | 已完成 | 是 | 交付 `data.markdown` 报告 + `data.total_points` 实扣 |
| `failed` | 已失败 | 是 | 退出码 12；本接口无重试端点，可重新发起 |

> 脚本对大小写做了归一（兼容大写枚举）。未列出的状态按未知处理：原样透出进度，不报错。

---

## 2. 查询任务（进度轮询）

`GET /api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis/{task_id}`

须使用创建任务时的同一个 API Key。`task_id` 与账号绑定，且与「账号拆解」凭证隔离，不可互用。

### 响应 `data`

外壳与创建接口相同。`data` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID |
| `status` | string | `pending` / `running` / `completed` / `failed` |
| `current_stage` | string \| null | 当前阶段 |
| `progress_message` | string \| null | 进度文案 |
| `error_message` | string \| null | 失败原因（failed 时） |
| `markdown` | string \| null | **完成后的 Markdown 报告；未完成时为 null**。后端预渲染、自带一级标题 |
| `total_points` | number \| null | **本次实际消耗点数；仅任务完成且扣费成功时有值，其余为 null** |

> 响应可能省略值为 `null` 的可选字段，调用方不应假设所有可选字段一定出现。

脚本默认每 5s 轮询，单次 HTTP 60s 超时，单次轮询等待上限 90s（到点非失败，emit 进行中后退出 13，可续 `--poll-task`）。

进度字段：`status` / `current_stage` / `progress_message`。

### 不同状态示例

**pending**

```json
{ "result": "success", "code": 200, "data": { "task_id": "...", "status": "pending",
  "current_stage": null, "progress_message": "账号快拆任务排队中", "error_message": null, "markdown": null } }
```

**running**

```json
{ "result": "success", "code": 200, "data": { "task_id": "...", "status": "running",
  "current_stage": null, "progress_message": "账号快拆任务执行中", "error_message": null, "markdown": null } }
```

**completed**

```json
{ "result": "success", "code": 200, "data": { "task_id": "...", "status": "completed",
  "current_stage": null, "progress_message": "账号快拆已完成", "error_message": null,
  "markdown": "# 微信视频号账号拆解报告\n\n## 1. 账号总览\n\n...", "total_points": 120 } }
```

**failed**

```json
{ "result": "success", "code": 200, "data": { "task_id": "...", "status": "failed",
  "current_stage": null, "progress_message": "账号快拆失败", "error_message": "账号快拆任务失败", "markdown": null } }
```

### 查询错误

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 401 | API Key 无效 | 8 |
| 403 | 无权访问该 `task_id` | 10 |
| 404 | 任务不存在 | 10 |
| 400 | 任务凭证无效（含类型不匹配） | 3 |

---

## 3. 重试失败模块

**本接口未提供重试端点。** 任务失败（退出码 12）时，由调用方用原账号名重新 `--only-create` 发起一次新任务（重新计费）。

---

## 4. 扣点字段

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.total_points` | number \| null | **本接口实际扣点字段；仅任务完成且扣费成功时有值**，其余为 null |

- 唯一正式实扣字段：`data.total_points`（number，顶层）。
- 任务级汇总：一次提交只扣一次（成功结算后）。
- 脚本优先读 `data.total_points`；未命中则回退历史候选 key，仍无则 `WX_ACCOUNT_QUICK_POINTS_USED` 留空，由 assistant 按约定估值「约 N 点」说明。
- 约定预估（仅提示，非实扣）：约 120 点；实际消耗以最终完成任务时的点数为准，以 01Claw 账户为准。

---

## 5. 余额不足响应

```json
{ "result": "error.*", "code": 402, "message": "点数不足", "data": { "recharge_url": "https://claw.lingyishuke.com/..." } }
```

脚本遇 402 以退出码 4 终止，透出 `recharge_url`（若有）。

---

## 6. 枚举速查

| 字段 | 取值 |
|------|------|
| 任务 `status` | `pending` / `running` / `completed` / `failed` |
| 创建接口 `platform` | 可选，可不传；本期固定按微信视频号处理 |
