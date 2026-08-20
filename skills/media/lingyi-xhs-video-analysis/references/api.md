# 小红书爆款短视频拆解 API 契约（v0.1.0 · 异步任务）

把一条小红书视频（分享链接或本地视频文件上传后的 `video_id`）提交拆解，创建后立即返回 `analysis_task_id`，轮询至终态取 `data.result.markdown`。本 API 是标准「创建/重试立即返回 task_id + GET 轮询至终态 + 扣点结算」的异步范式，但有如下偏差（脚本已适配）：

> **偏差**：
> 1. 任务 id 字段为 `data.analysis_task_id`（非 `task_id`）——脚本统一经 `analysis_task_id` 读取，兼容 `task_id`/`content_ops_task_id`。
> 2. 无 `data.billing.total_points` / `data.recharge_url` 字段——扣点前置约定为「每次新创建任务成功完成扣 **128 点**」；余额不足以 HTTP 402 + 服务端 message 透出（无充值链接），任务不创建、不扣点；轮询不重复扣点。
> 3. 重试端点 `POST .../{id}/retry` 未在文档明示——脚本按统一异步范式保留 `--retry-task`，若服务端不支持会以 4xx 透出，届时优先 `--poll-task` 续查或重新创建。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。

鉴权：`Authorization: Bearer <api_key>`（也兼容裸 key）+ `X-Appbuilder-From: openclaw` + `Content-Type: application/json`。Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量）。

幂等：Header `X-Idempotency-Key` 与 body `idempotency_key`（缺省自动生成 UUID，同任务重复提交保持不变）。

脚本流程（链接分支）：`POST <tasks>` → 立即拿 `analysis_task_id` → `GET <tasks/{id}>` 轮询 → 终态交付。
脚本流程（本地上传分支）：`POST <upload-url>` → `PUT` 文件二进制 → `POST <upload-confirm>` 拿 `video_id` → 再走创建/轮询。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 取预签名上传地址 | POST | `/api/v1/content-ops/videos/public-upload-url` | 本地视频上传第一步（`--video-file` 时） |
| 直传文件二进制 | PUT | （预签名返回的 `upload_url`） | 本地视频上传第二步，**不带平台 Authorization** |
| 确认上传 | POST | `/api/v1/content-ops/videos/public-upload-confirm` | 本地视频上传第三步，换 `video_id` |
| 创建拆解任务 | POST | `/api/v1/social-analytics/collector/xiaohongshu-video-analyses` | 主路径（立即返回 `analysis_task_id`） |
| 查询拆解状态 | GET | `/api/v1/social-analytics/collector/xiaohongshu-video-analyses/{analysis_task_id}` | 轮询进度与结果 |
| 重试失败任务（未明示） | POST | `/api/v1/social-analytics/collector/xiaohongshu-video-analyses/{analysis_task_id}/retry` | `--retry-task`，按统一范式实现，未在文档明示 |

## 通用响应外壳

成功：
```json
{ "api_version": "v1", "result": "success", "code": 200, "message": "...", "timestamp": "...", "data": {} }
```
失败：
```json
{ "result": "error.payment_required", "code": 402, "message": "当前可用点数不足，小红书视频拆解需要 128 点，请充值后再试" }
```

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功（业务 status 另判） | — |
| 400 | 未传 `share_url` 且未传 `video_id`/`video_ids` | 3 |
| 401 | API Key 无效 | 8 |
| 402 | 余额不足（需至少 128 点） | 4 |
| 403 | 无权查该任务（用了别的 Key / 非小红书任务） | 10 |
| 404 | 任务不存在 | 10 |
| 500 / 502 | 服务端 / 下游创建失败 | 11 |
| 其他 5xx | 服务内部错误 | 11 |

## 1. 本地视频上传（可选，仅 `--video-file` 时）

仅本地文件需要。上限以服务端校验为准（当前 200MB）。扩展名示例：`.mp4` `.mov` `.m4v` `.mkv` `.webm` `.avi`。

### 1.1 取预签名 `POST /api/v1/content-ops/videos/public-upload-url`

请求体：
```json
{ "filename": "note.mp4" }
```
`filename` 必填；`content_type` / `size` 可带（服务端目前只认 `filename`）。

成功 `data`：
| 字段 | 说明 |
|------|------|
| `upload_id` | 确认上传时必填 |
| `upload_url` | 预签名地址（同义字段 `url`） |
| `method` | 一般为 `PUT` |
| `object_key` | 可选，确认时可带回 |

### 1.2 直传文件

按返回的 `method` 把**文件二进制**传到 `upload_url`，**不要**带平台 `Authorization`（用返回的 `headers` 或 `Content-Type: application/octet-stream`）：
```bash
curl -X PUT "${UPLOAD_URL}" --data-binary @"/path/to/note.mp4" -H "Content-Type: application/octet-stream"
```
成功一般为 HTTP `200`/`201`/`204`。

### 1.3 确认上传 `POST /api/v1/content-ops/videos/public-upload-confirm`

成功时 HTTP 状态码为 **201**。请求体：
```json
{ "upload_id": "upl_xxxxxxxx" }
```
成功 `data`：
| 字段 | 说明 |
|------|------|
| `video_id` | 创建拆解时传入 |
| `video_url` | 可访问地址（展示用） |

## 2. 创建拆解任务（异步）

`POST /api/v1/social-analytics/collector/xiaohongshu-video-analyses`

落库后立即返回 `data`（含 `analysis_task_id`），**不代表拆解完成**。客户端必须 GET 轮询至终态。

### 2.1 请求体

`share_url` 与 `video_id` / `video_ids` **二选一必填**。

```json
{
  "share_url": "https://www.xiaohongshu.com/explore/64f0xxxx",
  "origin": "01workbuddy",
  "origin_method": "skill",
  "idempotency_key": "client-uuid"
}
```

| 字段 | 类型 | 必填 | 默认 | 约束/说明 |
|------|------|------|------|------|
| `share_url` | string | 与 `video_id`/`video_ids` 二选一 | — | 小红书视频笔记链接 |
| `video_id` | string | 同上 | — | 上传确认返回的视频 id |
| `video_ids` | string[] | 同上 | — | 视频 id 列表；会与 `video_id` 合并去重 |
| `industry` | string | 否 | — | 行业，如 `beauty`。**可引导但不强制、缺省不传** |
| `campaign_type` | string | 否 | — | 活动类型。可引导不强制 |
| `account_size` | string | 否 | — | 账号体量。可引导不强制 |
| `origin` | string | 否 | — | 调用来源埋点：`01claw`/`workbuddy`/`01workbuddy`/`coze`。脚本默认 `01workbuddy` |
| `origin_method` | string | 否 | — | 调用方式，如 `skill`/`api`。脚本默认 `skill` |
| `platform` | string | 忽略 | — | **固定忽略**，本接口固定写入 `xiaohongshu` |

> 链接请用**视频笔记**。图文笔记没有可拆的视频文件，任务可能失败。
> 常见链接形态：`https://www.xiaohongshu.com/explore/<note_id>`、`https://www.xiaohongshu.com/discovery/item/<note_id>`、`https://xhslink.com/...` 短链。

### 2.2 响应 data

```json
{
  "analysis_task_id": "xxxxxxxx",
  "capture_task_id": null,
  "content_ops_task_id": "xxxxxxxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis_task_id` | string | **轮询用任务 id**（脚本统一取此字段） |
| `capture_task_id` | string / null | 采集任务 id，可能为空 |
| `content_ops_task_id` | string / null | 下游任务 id，通常与 `analysis_task_id` 相同 |

## 3. 查询拆解状态（进度轮询）

`GET .../xiaohongshu-video-analyses/{analysis_task_id}`，必须用**同一个 API Key**。不要用本接口查微信/抖音任务（会 403）。

脚本默认每 5s 轮询，单次 HTTP 超时 60s；首次可等约 5s 再开始，处理中每 4–8s 一次，总等待建议 10 分钟。

成功 `data`：
| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis_task_id` | string | 任务 id |
| `status` | string | 见下方状态（大小写都可能出现，按小写判断） |
| `current_stage` | string / null | 细分阶段，可能为空 |
| `progress_message` | string / null | 进度文案，可能为空 |
| `error_message` | string / null | 仅失败时有 |
| `result.markdown` | string / null | **仅完成时有**，Markdown 报告 |
| `result.raw` | object / null | 原始结构化结果，可忽略 |

### 报告 markdown 取法

终态成功时取 `data.result.markdown`（单段 Markdown）。脚本 `extract_markdown` 兼容 `data.markdown` / `data.result.markdown` / `data.results.<module>.markdown`，取不到返回空。

## 4. status 枚举

`status` 大小写都可能出现，**脚本统一按小写判断**。

| 值 | 含义 | 是否终态 | 脚本处理 |
|----|------|----------|----------|
| `pending` / `queued` | 已受理 / 排队 | 否 | 非终态，继续轮询（退出码 13） |
| `running` | 处理中 | 否 | 同上 |
| `completed` / `success` / `done` | 完成 | 是 | 读 `data.result.markdown` 交付（退出码 0）；md 暂空进 60s 宽限 |
| `failed` / `error` | 失败 | 是 | 读 `error_message`，退出码 12 |
| `timeout` | 超时 | 是 | 退出码 12 |

未列出的状态按未知处理：原样透出 `progress_message`/`status`，不自行判定失败，按退出码表对号入座。

## 5. 扣点字段

- 本 API **无** `data.billing.total_points` / `data.recharge_url` 字段。
- 扣点口径：每次**新创建**拆解任务成功完成后扣 **128 点**；余额不足创建接口返回 402（任务不创建、不扣点）；轮询已有任务不重复扣点。
- 脚本 `XHS_VIDEO_POINTS_USED` 常为空（无结算字段可提取），按前置约定「约 128 点」提示，**不当作实扣数字**；真正实扣以 01Claw 账户为准。

## 6. 余额不足响应

402 示例：
```json
{
  "result": "error.payment_required",
  "code": 402,
  "message": "当前可用点数不足，小红书视频拆解需要 128 点，请充值后再试"
}
```
脚本遇 402 以退出码 4 终止，透出服务端 `message`（本 API 无 `recharge_url`，不附充值链接，引导用户自行充值后重试）。任务未创建、不扣点。

## 7. 备注

1. 交付物只保证 `data.result.markdown`。
2. 不要在处理中重复创建——每次创建都可能独立计费。
3. 本接口只拆**小红书**。微信走 `/wx-video-analyses`，抖音走 `/douyin-video-analyses`。
4. 小红书请传视频笔记；图文笔记没有视频流，拆解会失败。
