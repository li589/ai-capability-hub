# 公众号贴图号爆款生成【零一数科·出品】 API 契约（v0.1.0 · 异步任务）

**异步任务模型**：创建立即返回 `task_id`，客户端用 `GET` 轮询进度与结果，`completed` 后从 `data.markdown` 取报告、从 `data.total_points` 取实扣。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。

鉴权：`Authorization: Bearer <api_key>` + `Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。所有接口仅支持 Bearer 头部鉴权，身份从 Key 解析；**请求体不得夹带 `account_id`**。
> 本 API **无幂等机制**：文档全文无 `idempotency` 字样，§3.2「只能包含参数表声明的字段，否则 422」。故标准 §9 的「`X-Idempotency-Key` 头 + body `idempotency_key`」**不适用**：脚本不发幂等头、不向 body 注入 `idempotency_key`，CLI 亦无 `--idempotency-key`。重复提交会创建新任务并独立计费——防重复扣点靠「同一意图避免重复 POST」由人/调用方保证。

> ⚠️ **本 API 与标准范式的偏差**（脚本与 SKILL.md 均已据此处理）：
> 1. **无 `POST /{id}/retry` 接口**：文档明示无重试接口，失败/超时需用**原始 payload 整体重交**创建新任务。脚本 `--retry-task` 仍保留 CLI 入口，但实现是「重新创建新任务」（新 `task_id`、**独立扣费**），而非传统原地 retry。
> 2. **每次新任务独立计费**：失败重提是一次新的可计费提交，不享受「已成功模块不重跑」。话术须如实告知用户。
> 3. **扣点字段是 `data.total_points`**（顶层，整数），非标准的 `data.billing.total_points`。脚本 extractor 已兼容。
> 4. **有额外 `GET /config` 接口**拉取 `tone`（内容调性）枚举，文档**禁止硬编码示例值**。脚本提供 `--fetch-config` 拉取实时枚举；默认不传 `tone`，走后端默认。
> 6. **本 API 无幂等机制**：文档无 `idempotency` 字段，§3.2 禁未声明字段。标准 §9 的「`X-Idempotency-Key` 头 + body `idempotency_key`」**不适用**，已移除——不发幂等头、不注入 body `idempotency_key`、无 `--idempotency-key` CLI。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 创建任务 | POST | `/api/v1/content/article-generation` | 主路径（立即返回 `task_id`） |
| 查询任务 | GET | `/api/v1/content/article-generation/{task_id}` | 轮询进度与结果 |
| 取配置 | GET | `/api/v1/content/article-generation/config` | `--fetch-config` 拉 `tone` 枚举（不创建任务、不扣点） |
| 重试 | — | **无** | `--retry-task` 实为重新创建新任务（见偏差①②） |

## 通用响应外壳

成功：
```json
{ "api_version": "v1", "result": "success", "code": 200, "message": "Success", "timestamp": "ISO8601", "data": {} }
```
失败：
```json
{ "api_version": "v1", "result": "error.bad_request", "code": 400, "message": "...", "timestamp": "...", "detail": null, "trace_id": null }
```

字段：`api_version`(恒 `v1`)、`result`(`success`/`error.<type>`)、`code`(HTTP/业务码)、`message`、`timestamp`(ISO 8601)、`detail`(通常 null)、`trace_id`(可选)。`null` 可选字段省略。

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功查询到状态（业务 status 另判；**失败任务仍返回 200**，必须按 `data.status` 分流） | — |
| 400 | 参数语义错误、`tone` 不在枚举、凭证/场景不一致 | 3 |
| 401 | 缺/格式错/无效 API Key | 8 |
| 402 | 点数不足最低门槛（≥100 预扣门槛） | 4 |
| 403 | 当前 Key 无权访问该任务（停止轮询、确认 Key） | 10 |
| 404 | 任务不存在 | 10 |
| 422 | JSON 结构/字段校验失败（非法 `content_format`、非法比例、夹带未声明字段等） | 3 |
| 5xx | 服务内部错误/上游暂不可用 | 11 |

---

## 1. 创建任务（异步）

`POST /api/v1/content/article-generation`

落库后立即返回 `data`（含 `task_id`，通常 `status: pending`）。后续在后台执行；客户端必须用 GET 轮询至终态。成功仅表示「已提交」。

### 请求体

```json
{
  "topic": "...",
  "word_count": 800,
  "product": { "name": "...", "selling_points": ["..."], "price": 99, "price_band": "mid", "decision_type": "considered" },
  "target_audience": { "description": "...", "pain_points": ["..."], "age_range": "25-35", "gender": "female" },
  "content_format": "xiaolvshu",
  "cover_image_ratio": "3:4",
  "body_image_ratio": "3:4",
  "tone": "knowledge",
  "main_image_count": 1,
  "inset_image_count": 1,
  "title_count": 3
}
```

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `topic` | string | 是 | — | 首尾空白清理后非空 | 选题/话题，作为正文与标题生成核心 |
| `word_count` | integer | 是 | — | 100–50000 | 正文字数 |
| `product` | object | 是 | — | 见下 | 产品信息 |
| `target_audience` | object | 是 | — | 见下 | 目标受众 |
| `content_format` | string | 否 | `xiaolvshu` | `xiaolvshu`(贴图号) / `image_message`(公众号) | 内容形式 |
| `cover_image_ratio` | string | 否 | 随格式 | 见 §比例速查 | 全角冒号 `：` 自动归一为半角 `:` |
| `body_image_ratio` | string | 否 | 随格式 | 见 §比例速查 | 同上 |
| `tone` | string | 否 | 不传 | 取自 `/config` 实时枚举，**勿硬编码示例值** | 内容调性；不传走后端默认 |
| `main_image_count` | integer | 否 | 1 | 1–5 | 主图/封面数量 |
| `inset_image_count` | integer | 否 | 1 | 1–5 | 正文配图数量 |
| `title_count` | integer | 否 | 3 | 1–5 | 候选标题数量 |

**`product`**：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `name` | string | 是 | 非空 |
| `selling_points` | string[] | 是 | ≥1 非空元素 |
| `price` | number | 否 | ≥0 |
| `price_band` | string | 否 | 如 `low`/`mid`/`high`；空串按不传 |
| `decision_type` | string | 否 | 如 `considered`；空串按不传 |

**`target_audience`**：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `description` | string | 是 | 非空 |
| `pain_points` | string[] | 是 | ≥1 非空元素 |
| `age_range` | string | 否 | 如 `25-35` |
| `gender` | string | 否 | 如 `female` |

> ⚠️ **禁止发送**：`scene`、`account_id`、`cover_image_quality`/`body_image_quality`（固定 `medium`）、`cover_image_size`/`body_image_size`（服务端按比例映射）。夹带未声明字段 → HTTP `422`。

### 响应 `data`

创建成功通常 `pending`，无 markdown：

```json
{ "task_id": "...", "status": "pending" }
```

终态 `completed` 示例：

```json
{
  "task_id": "...",
  "status": "completed",
  "current_stage": null,
  "progress_message": null,
  "error_message": null,
  "markdown": "# 标题\n\n## 封面图\n...## 内文配图\n...## 正文\n...",
  "total_points": 15
}
```

| 字段 | 类型 | 一定返回 | 说明 |
|------|------|----------|------|
| `task_id` | string | 是 | 任务 ID；轮询/重试靠它。**轮询须 URL-encode**（可能含 `+`/`/`/`=`） |
| `status` | string | 是 | 见枚举 |
| `current_stage` | string | 否 | 当前执行阶段 |
| `progress_message` | string | 否 | 进度说明 |
| `error_message` | string | 否 | 失败/渲染异常说明 |
| `markdown` | string | 否 | 通常仅 `completed` 返回；按 `content_format` 渲染 |
| `total_points` | integer | 否 | 实际消耗点数；扣点成功后返回（如 `15`）。缺失不当失败 |

> **报告 markdown 取法**：脚本从 `data.markdown`（单串）取。后端 `markdown` **已自带一级标题**（`# 标题`，见 §4.9 示例），脚本检测到 H1 即**原样输出、不再前置脚本标题、不插分隔线**，避免出现两个 H1；仅当后端 markdown 无 H1 时才前置 `# 爆款图文：<话题摘要>` 兜底。正文由后端渲染、不可改 table，**必须原样使用、不本地改写/总结/重排**；`completed` 但缺 markdown → 透出「结果暂不可用」，不本地伪造正文。

### `status` 枚举

| 值 | 含义 | 是否终态 | 脚本处理 |
|----|------|----------|----------|
| `pending` | 排队中 | 否 | 续轮询（退出码 13） |
| `running` | 执行中 | 否 | 续轮询（退出码 13） |
| `completed` | 完成 | 是 | 取 `data.markdown` 交付（退出码 0） |
| `failed` | 失败 | 是 | 停止轮询；透出 `error_message`（退出码 12） |
| `timeout` | 超时 | 是 | 停止轮询（退出码 12） |

未知状态不自行判定失败：原样透出 `progress_message`，按退出码表对号入座。

---

## 2. 查询任务（进度轮询）

`GET /api/v1/content/article-generation/{task_id}`

- {task_id} 必须 **URL-path-encode** 后原样传入（若含 `+`/`/`/`=` 先编码）。
- 必须用创建时的同一 API Key（身份绑定任务）；`403` 表示「当前 Key 无权访问该任务」。
- 响应 `data` 形状与创建相同。脚本默认每 5s 轮询，单次 HTTP 超时 60s，单次轮询等待上限 90s（到点非失败，emit 进行中后退出码 13，可续 `--poll-task`）。整体建议封顶 ~30 分钟避免无限轮询。

---

## 3. 重试（偏差：实为重新创建）

本 API **无 `POST /{id}/retry` 接口**。文档明示：失败/超时需用**原始 payload 整体重交**创建新任务。

脚本 `--retry-task <id>` 入口保留（保持三模式 CLI 一致），但行为是：用相同的 `--text`+业务参数重建 body 后 `POST` 创建，拿到**新 `task_id`** 再轮询。
- 旧 `<id>` 仅作日志参考，不会被「原地续跑」。
- **每次重提是一次新的可计费提交、独立扣费**，不享受「已成功模块不重跑」。
- 调用 `--retry-task` 时必须重供 `--text` 与业务参数以重建 body（同创建时）。

```bash
python3 scripts/article_generation.py --retry-task <旧task_id参考> \
  --text "<同创建话题>" --word-count 800 --product-name "..." --selling-points "..." \
  --audience-desc "..." --pain-points "..." --out ./爆款图文.md
```

---

## 4. 取配置（拉取调性枚举）

`GET /api/v1/content/article-generation/config`

- 无 path/query/body 参数；Bearer 鉴权。
- 不创建任务、不涉扣点。
- 返回 `data` 为字段配置数组，目前含 `field==tone`：

```json
{ "field": "tone", "label": "内容调性", "desc": "...", "options": [ {"value": "knowledge", "label": "知识型", "desc": "..."} ] }
```

- 仅当用户明确要选内容调性时，脚本 `--fetch-config` 拉取实时 `options[].value` 展示给用户选；选定后以 `--tone` 传入创建。文档示例值仅供说明，**不得硬编码**。
- 其它字段（`content_format`、比例）为静态约束，见 §比例速查，不在 config 返回。

```bash
python3 scripts/article_generation.py --fetch-config
```

---

## 5. 扣点字段

```json
{ "total_points": 15 }
```

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.total_points` | integer | **本次实际扣点（终态 `completed` 后返回）** |

- 创建时预扣余额门槛：开启计费时账户需 ≥**100 点**，不足 → HTTP `402`（100 是门槛、非价格，无任务创建）。
- **实际扣点仅 `completed` 时发生**；`pending`/`running`/`failed`/`timeout` 均不扣。
- 重复轮询同一 `completed` 任务**不重复扣点**。
- `total_points` 为可选字段，缺失不当失败。
- 约定预估（仅提示、非实扣）：60 点起步；最终以服务端实际扣除为准（实际消耗以最终完成任务时的点数为准）。

---

## 6. 余额不足响应

```json
{ "api_version": "v1", "result": "error.payment_required", "code": 402, "message": "当前可用点数不足，贴图号爆款生成至少需要 100 点，请充值后再试", "timestamp": "...", "detail": null, "trace_id": null }
```

脚本遇 402 以退出码 4 终止，透出 message（若响应含 `recharge_url` 则一并透出，引导充值后重新创建）。

---

## 7. 枚举速查

**`content_format`**：`xiaolvshu`（贴图号，默认）/ `image_message`（公众号）。

**`status`**：`pending` / `running` / `completed` / `failed` / `timeout`。

**比例速查**（仅传比例，服务端映射像素尺寸；全角 `：`→半角 `:`）：

| 格式 | 封面比例（默认） | 配图比例（默认） |
|------|------|------|
| `xiaolvshu` 贴图号 | `3:4`(1080×1440 默认) / `1:1`(1080×1080) | `3:4`(默认) / `1:1` |
| `image_message` 公众号 | `2.35:1`(900×383，**仅允许**) | `16:9`(1280×720 默认) / `3:4` / `1:1` |

> 比例须与 `content_format` 匹配，否则 HTTP `422`；不传走该格式的默认比例。勿传 `*_image_size`。

**`tone`**：取自 `/config` 实时枚举（如 `knowledge` 等示例），**勿硬编码**。
