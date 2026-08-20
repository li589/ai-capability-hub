# 视频号拆解 API 目录

后端「微信视频号视频拆解」相关接口。base url 固定 `https://claw.lingyishuke.com/services`（写死在脚本里）。

鉴权：除特别说明外，所有接口都带 `Authorization: <api_key>`（裸 API Key，不带 `Bearer` 前缀）、`X-Appbuilder-From: openclaw`。API Key 由脚本从技能目录下 `config.json` 的 `LY_API_KEY` 字段读取（回退环境变量 `LY_API_KEY`）。

> 本地视频上传接口、视频号拆解接口均已按后端真实路径更新。脚本主流程使用拆解接口 `wx-video-analyses`。

## 输入分支

- **视频号分享链接**：直接走「3. 发起拆解」，body 传 `share_url`。
- **本地视频文件**：先走「1. 预签名上传」+「2. 确认上传」拿到 `video_id`，再走「3. 发起拆解」，body 传 `video_id`。

---

## 1. 预签名上传（本地视频）

`POST /api/v1/content-ops/videos/public-upload-url`

取一个可直传的预签名地址。

- **请求**：

```json
{ "filename": "video.mp4", "content_type": "video/mp4", "size": 12345678 }
```

- **响应**：

```json
{
  "result": "success",
  "data": {
    "upload_url": "https://oss.../bucket/key?signature=...",
    "method": "PUT",
    "headers": { "Content-Type": "application/octet-stream" },
    "upload_id": "upload_xxx",
    "object_key": "uploads/xxx.mp4"
  }
}
```

- 拿到 `upload_url` 后，按 `method` 把文件字节直传到该地址（预签名 PUT：`PUT upload_url`，body=文件内容，带 `headers`）。若响应未给 `headers`，当前线上 OSS 签名要求默认带 `Content-Type: application/octet-stream`。OSS 直传**不带** Authorization 头。
- 压缩：服务端处理。客户端直传原文件即可，不做压缩，仅在文件过大时告警。

## 2. 确认上传

`POST /api/v1/content-ops/videos/public-upload-confirm`

通知后端上传完成，换取 `video_id`。

- **请求**：

```json
{ "upload_id": "upload_xxx", "object_key": "uploads/xxx.mp4" }
```

线上实测 `upload_id` 为确认必需字段，`object_key` 可一并传入用于兼容/追踪。

- **响应**：

```json
{
  "result": "success",
  "code": 200,
  "data": {
    "video_id": "video_xxx",
    "video_url": "https://oss.../video.mp4"
  }
}
```

## 3. 发起拆解

- **Body**：`share_url` 与 `video_id` **二选一必填**。

`POST /api/v1/social-analytics/collector/wx-video-analyses`

```json
{
  "share_url": "https://weixin.qq.com/sph/AbCdEf"
}
```

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `share_url` | 与 `video_id` 二选一 | 视频号分享链接 |
| `video_id` | 与 `share_url` 二选一 | 本地视频上传后返回的 id |

- **成功响应**：

```json
{
  "result": "success",
  "code": 200,
  "data": { "analysis_task_id": "analysis_xxx" }
}
```

- **余额不足响应**：

```json
{
  "result": "fail",
  "code": 402,
  "message": "余额不足",
  "data": { "recharge_url": "https://claw.lingyishuke.com/recharge" }
}
```

脚本遇到余额不足以退出码 4 终止，并把 `recharge_url`（若有）透出给用户。

## 4. 轮询拆解状态

`GET /api/v1/social-analytics/collector/wx-video-analyses/{analysis_task_id}`

- **请求**：任务 id 作为路径参数。
- **鉴权**：脚本默认带 `Authorization`，兼容鉴权开启场景。

### 处理中 / 完成 / 失败

```json
{
  "result": "success",
  "data": {
    "status": "ANALYZING",
    "current_stage": "llm",
    "progress_message": "正在拆解视频...",
    "result": { "markdown": "...（仅 COMPLETED 时存在）" },
    "error_message": "...（仅 FAILED 时存在）"
  }
}
```

| 字段 | 含义 |
| --- | --- |
| `status` | 任务总状态，见下方枚举。 |
| `current_stage` | 当前细分阶段（如 `llm`、`completed`、`failed`）。 |
| `progress_message` | 面向用户的进度文案，轮询时透出。 |
| `error_message` | 仅 `status=FAILED` 时存在，失败原因。 |
| `result.markdown` | 仅 `status=COMPLETED` 时存在，最终分析报告（Markdown）。 |

## 状态枚举

| 值 | 含义 | 是否终态 |
| --- | --- | --- |
| `QUEUED` | 已入队 | 否 |
| `PENDING` | 等待中 | 否 |
| `PROCESSING_MEDIA` | 素材处理中 | 否 |
| `ANALYZING` | LLM 拆解中 | 否 |
| `UPLOADING` | 上传中 | 否 |
| `GENERATING_REPORT` | 生成报告中 | 否 |
| `COMPLETED` | 完成 | 是 |
| `FAILED` | 失败 | 是 |

未列出的状态值按未知处理：脚本原样透出 `progress_message`，不报错。
