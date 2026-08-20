# 视频号脚本创作 API 契约

base 前缀：`/api/v1/social-analytics/collector`（部署方可能另有网关前缀，以实际为准）。
完整默认 base：`https://claw.lingyishuke.com/services`。

脚本生成主流程三个接口，均需 `Authorization: <API_KEY>`（裸 key，不带 Bearer）：

```text
GET  /api/v1/social-analytics/collector/wx-video-script-creations/config
POST /api/v1/social-analytics/collector/wx-video-script-creations
GET  /api/v1/social-analytics/collector/wx-video-script-creations/{script_task_id}
```

创建任务接口额外需 `Content-Type: application/json`。

> 二创只支持微信视频号分享链接，不支持本地视频文件上传。

## 输入分支

- **微信视频号分享链接**：直接创建脚本任务，body 传 `share_url`，并在 `source_video.shared_url` 中保留同一链接。

## 1. 参数配置 config

`GET .../wx-video-script-creations/config`，无入参。`data` 是字段配置数组：枚举字段含 `options`（取 `value`，不取 `label`），自由输入字段含 `input`。

| field | 类型 | 说明 |
|------|------|------|
| `mode` | options | 创作模式：`creation` / `recreation` |
| `direction` | options | 创作方向：常见 `ip_account` / `brand_account` / `influencer_commerce` |
| `platform` | options | 发布平台：常见 `channels` / `douyin` / `xiaohongshu` |
| `industry` | options | 行业 |
| `purpose` | options | 营销目的 |
| `script_type` | options | 脚本类型；不传由后端自动匹配 |
| `depth` | options | 创作深度：`fast` / `deep` |
| `product` | input | 商品/品牌信息对象 |
| `account_brief` | input | 账号/人设/品牌信息对象 |
| `source_video` | input | 二创源视频对象 |
| `count` | input | 生成条数 1–3，默认 1 |
| `target_duration_sec` | input | 目标时长 1–1800 秒 |

## 2. 创建任务

`POST .../wx-video-script-creations`，body JSON：

| 字段 | 必填 | 说明 |
|------|------|------|
| `mode` | 是 | 创作模式 value |
| `direction` | 是 | 创作方向 value |
| `platform` | 是 | 发布平台 value |
| `industry` / `industries` | 至少一个 | 行业（单值/数组，后端合并去重） |
| `purpose` / `campaign_type` / `campaign_types` | 至少一个 | 营销目的（后端合并去重） |
| `product` | 条件 | `mode=creation` 且 `direction=influencer_commerce` 时必填非空对象 |
| `source_video` | 条件 | `mode=recreation` 时必填，含 `shared_url`（微信视频号分享链接） |
| `share_url` | 否 | 二创源视频分享链接快捷顶层字段 |
| `account_brief` | 否 | 对象 |
| `script_type` | 否 | 不传自动匹配 |
| `count` / `script_count` | 否 | 1–3，默认 1 |
| `target_duration_sec` | 否 | 1–1800 |
| `depth` | 否 | 默认 `fast` |
| `additional_requirements` | 否 | 额外要求文本 |
| `origin` / `origin_method` | 否 | 调用来源/方式，本 skill 填 `workbuddy` / `skill` |

**校验规则**：mode/direction/platform/industry/purpose/script_type/depth 必须用 config 返回的 value（部分中文值兼容转换但不可依赖）；`product` 空对象会被拒；二创缺源视频（分享链接）会被拒。body 允许额外字段，会进入生成上下文。

成功响应 `data.script_task_id`（用于轮询）。

## 3. 查询状态

`GET .../wx-video-script-creations/{script_task_id}`，看 `data.status`：

| 状态集合 | 值 | 含义 |
|---------|----|----|
| 成功 | `completed` / `complete` / `success` / `succeeded` / `done` | 完成 |
| 失败 | `failed` / `error` / `cancelled` / `canceled` | 失败 |
| 执行中 | `pending` / `queued` / `running` / `processing` | 进行中 |

完成后的结果：
- `data.result.markdown`：**完整可交付的报告 Markdown**（含标题、生成概览、选题策略、逐条脚本、评估汇总、整体优化建议）。skill 直接解析此字段并原样输出，报告不依赖其它中间字段。

## 4. 错误码

| HTTP | result | 场景 |
|------|--------|------|
| 401 | `error.unauthorized` | 无 Authorization / key 无效 / 校验未返 user_id |
| 400 | `error.bad_request` | 必填缺失 / 枚举非法 / product 空 / 二创缺源视频 |
| 403 | `error.forbidden` | 查询任务时无权访问 |
| 404 | `error.not_found` | 任务不存在（查询接口） |
| 422 | `error.internal` | 类型/范围错（count 超 1-3、duration 超 1-1800、字段类型不符） |
| 5xx | `error.internal` | 脱敏，仅 `Internal server error` |
