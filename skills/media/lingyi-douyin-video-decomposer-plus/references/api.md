# 抖音爆款短视频拆解 API 契约（v0.1.0 · 异步任务）

**异步任务模型**：创建立即返回 `analysis_task_id`，客户端用 `GET` 轮询进度与结果。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。

鉴权：`Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw` + `Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。

幂等：Header `X-Idempotency-Key` 和/或 body `idempotency_key`（body 优先）；缺省脚本生成 UUID。

> **与标准范式的偏差（重要，实现已据此调整）**：
> 1. **无 `POST /retry` 接口**。脚本 `--retry-task <task_id>` 不调任何 retry 路由，而是**对同一 `analysis_task_id` 重新轮询**（等价 `--poll-task`，不重新创建、不重复扣点）。任务真失败（`failed`/`error`/`timeout`）后的“重试”= 经用户确认后用 `--input` **重新发起一次新拆解**（新 `analysis_task_id`、重新扣点）。
> 2. 任务 id 字段是 **`analysis_task_id`**（非通用 `task_id`）。
> 3. 报告 markdown 在 **`data.result.markdown`**（单一报告，非多模块 `results.<module>.markdown`）。
> 4. `status` **小写**，且含标准集没有的 `timeout` 终态。
> 5. **轮询响应不含 billing 字段**，`DY_VIDEO_POINTS_USED` 运行时常为空 → 按「约 128 点（实际以服务端为准）」回退。

脚本流程：本地视频时先「预签名→直传→确认」换 `video_id` → `POST .../douyin-video-analyses` 创建（传 `share_url` 或 `video_id`）→ `GET .../douyin-video-analyses/{id}` 轮询 → 终态交付。无 `/retry`。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 创建拆解任务 | POST | `/api/v1/social-analytics/collector/douyin-video-analyses` | 主路径（立即返回 `analysis_task_id`） |
| 查询拆解任务 | GET | `/api/v1/social-analytics/collector/douyin-video-analyses/{analysis_task_id}` | 轮询进度与结果 |
| 取预签名上传（本地视频） | POST | `/api/v1/content-ops/videos/public-upload-url` | 本地文件分支 |
| 确认上传（本地视频） | POST | `/api/v1/content-ops/videos/public-upload-confirm` | 本地文件分支，返回 201 换 `video_id` |
| 重试失败模块 | — | **无此接口** | `--retry-task` = 重新轮询同 task_id；真重试 = 重新发起 |

## 通用响应外壳

成功：
```json
{ "api_version": "v1", "result": "success", "code": 200, "message": "抖音拆解任务创建成功", "timestamp": "...", "data": {} }
```
失败（余额不足示例）：
```json
{ "api_version": "v1", "result": "error.payment_required", "code": 402, "message": "当前可用点数不足，抖音视频拆解需要 128 点，请充值后再试" }
```

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功（业务 status 另判） | — |
| 400 | 未传 `share_url` 且未传 `video_id`/`video_ids` | 3 |
| 401 | 缺/无效 API Key | 8 |
| 402 | 余额不足（创建阶段拦截） | 4 |
| 403 | 用该接口查其它平台任务（跨平台无权） | 10 |
| 404 | task 不存在 | 10 |
| 502 | 下游创建失败 | 11 |
| 5xx | 服务内部错误 | 11 |

---

## 1. 创建拆解任务（异步）

`POST /api/v1/social-analytics/collector/douyin-video-analyses`

落库后立即返回 `data`（含 `analysis_task_id`）。后续在后台执行；客户端必须用 GET 轮询至终态。**创建成功只表示已受理，不代表拆解完成。**

### 请求体

```json
{
  "share_url": "https://v.douyin.com/xxxxx/",
  "origin": "01workbuddy",
  "origin_method": "skill",
  "idempotency_key": "client-uuid-or-stable-key"
}
```

本地视频分支用 `video_id`（由「3. 上传本地视频」换取）替代 `share_url`。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `share_url` | string | 与 `video_id`/`video_ids` 二选一 | — | 抖音分享链接。短链 `https://v.douyin.com/xxxxx/` 优先；长链须带 `/video/<aweme_id>` |
| `video_id` | string | 同上 | — | 上传确认返回的视频 id |
| `video_ids` | string[] | 同上 | — | 视频 id 列表，会与 `video_id` 合并去重 |
| `industry` | string | 否（缺省不传） | — | 行业，如 `beauty`。可引导但不强制 |
| `campaign_type` | string | 否 | — | 活动类型 |
| `account_size` | string | 否 | — | 账号体量 |
| `origin` | string | 否（脚本固定 `01workbuddy`） | — | 调用来源埋点：`01claw`/`workbuddy`/`01workbuddy`/`coze` |
| `origin_method` | string | 否（脚本固定 `skill`） | — | 调用方式：`skill`/`api` |
| `platform` | string | **忽略** | — | 本接口固定写入 `douyin`，脚本不传 |
| `idempotency_key` | string | 否 | 脚本生成 UUID | 幂等键，重复提交同一任务保持不变 |

### 响应 `data`

```json
{
  "analysis_task_id": "xxxxxxxx",
  "capture_task_id": null,
  "content_ops_task_id": "xxxxxxxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis_task_id` | string | **轮询用任务 id** |
| `capture_task_id` | string\|null | 采集任务 id，可能为空 |
| `content_ops_task_id` | string\|null | 下游任务 id，通常与 `analysis_task_id` 相同 |

> ⚠️ **创建响应不返回 `status`**（与通用异步模板不同）。脚本在 `--only-create` 模式合成 `pending` 状态透出，后续以轮询返回的 `status` 为准。

### 常见错误

| HTTP | 场景 |
|------|------|
| 400 | 未传 `share_url` 且未传 `video_id`/`video_ids` |
| 401 | API Key 无效 |
| 402 | 余额不足（需至少 128 点），任务未创建、不扣点 |
| 502 | 下游创建失败 |

---

## 2. 上传本地视频（可选，仅本地文件分支需要）

服务端校验上限当前 **200MB**；扩展名示例 `.mp4 .mov .m4v .mkv .webm .avi`。

### 2.1 取预签名上传地址

`POST /api/v1/content-ops/videos/public-upload-url`

请求：
```json
{ "filename": "aweme.mp4" }
```
`filename` 必填；`content_type`/`size` 可带（服务端目前只认 `filename`）。

成功 `data` 主要字段：

| 字段 | 说明 |
|------|------|
| `upload_id` | 确认上传时必填 |
| `upload_url` | 预签名地址（同义字段 `url`） |
| `method` | 一般为 `PUT` |
| `object_key` | 可选，确认时可带回 |

### 2.2 直传文件二进制

按返回的 `method`（通常 `PUT`）把**文件二进制**传到 `upload_url`，**不要带平台 `Authorization`/`X-Appbuilder-From`**，`Content-Type: application/octet-stream`：

```bash
curl -X PUT "${UPLOAD_URL}" --data-binary @"/path/to/aweme.mp4" -H "Content-Type: application/octet-stream"
```

成功一般为 HTTP `200`/`201`/`204`。

### 2.3 确认上传

`POST /api/v1/content-ops/videos/public-upload-confirm`

成功时 HTTP 状态码为 **201**。请求体：
```json
{ "upload_id": "upl_xxxxxxxx" }
```

成功 `data`：

| 字段 | 说明 |
|------|------|
| `video_id` | 创建拆解时传入 |
| `video_url` | 可访问地址（展示用） |

---

## 3. 查询拆解任务（进度轮询）

`GET /api/v1/social-analytics/collector/douyin-video-analyses/{analysis_task_id}`

必须用**同一个 API Key**。不要用本接口查微信/小红书任务（会 403）。其它错误：401 Key 无效；404 任务不存在。

响应 `data`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis_task_id` | string | 任务 id |
| `status` | string | 见下方枚举（小写） |
| `current_stage` | string\|null | 细分阶段，可能为空 |
| `progress_message` | string\|null | 进度文案，可能为空 |
| `error_message` | string\|null | 仅失败时有 |
| `result.markdown` | string\|null | **仅完成时**有，Markdown 报告 |
| `result.raw` | object\|null | 原始结构化结果，可忽略 |

处理中示例：
```json
{
  "result": "success", "code": 200,
  "data": {
    "analysis_task_id": "xxxxxxxx", "status": "running",
    "current_stage": null, "progress_message": null,
    "error_message": null, "result": null
  }
}
```
完成示例：
```json
{
  "result": "success", "code": 200,
  "data": {
    "analysis_task_id": "xxxxxxxx", "status": "completed",
    "result": { "markdown": "## 基础信息\n..." }
  }
}
```

### `status` 枚举（小写判断，大小写都可能出现）

| 值 | 是否终态 | 脚本处理 |
|----|----------|----------|
| `pending` / `queued` | 否 | 继续轮询 |
| `running` | 否 | 继续轮询 |
| `completed` / `success` / `done` | 是（成功） | 读 `result.markdown` 交付；详见「终态竞态兜底」 |
| `failed` / `error` | 是（失败） | 读 `error_message`，走失败分支 |
| `timeout` | 是（失败） | 走失败分支（标准集无此项，已补入终态集合） |

未列出的状态按未知处理：脚本原样透出 `progress_message`，不报错。

脚本默认每 5s 轮询，单次 HTTP 超时 60s，单次轮询等待上限 90s（到点非失败——emit 进行中后退出 13，可续 `--poll-task`）。等约 5 秒后再开始首次轮询；处理中每 4–8s 一次；总等待建议约 10 分钟。偶发 `500`/`502` 指数退避重试**轮询**，**不要**重复创建任务（每次创建都可能独立计费）。

---

## 4. 扣点字段

- 每次新创建拆解任务，成功完成后扣 **128** 点。余额不足创建接口返回 **402**，任务未创建、不扣点。轮询已有任务不重复扣点。
- ⚠️ **本 API 轮询响应不含 `billing` 字段**，`analysis_task_id` 链路里没有 `data.billing.total_points` 可读。脚本 `DY_VIDEO_POINTS_USED` 运行时常为空 → 由 assistant 按约定估值「约 128 点（实际以服务端扣点为准，可在 01Claw 账户查看）」回退。
- 约定预估（仅提示，非实扣）：128 点；实际消耗以最终完成任务时的点数为准。

---

## 5. 余额不足响应

```json
{ "api_version": "v1", "result": "error.payment_required", "code": 402,
  "message": "当前可用点数不足，抖音视频拆解需要 128 点，请充值后再试" }
```

脚本遇余额不以退出码 4 终止。注意：该响应只有 `message`，**不含 `recharge_url`** 字段（与通用模板不同）；引导用户前往 01Claw 账户充值。

---

## 6. 枚举速查

| 字段 | 取值 |
|------|------|
| `status` | `pending` / `queued` / `running` / `completed` / `success` / `done` / `failed` / `error` / `timeout` |
| `origin` | `01claw` / `workbuddy` / `01workbuddy` / `coze`（脚本固定 `01workbuddy`） |
| `origin_method` | `skill` / `api`（脚本固定 `skill`） |
| `platform` | 固定 `douyin`（忽略客户端传入） |
