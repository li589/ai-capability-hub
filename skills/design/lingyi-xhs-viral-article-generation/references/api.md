# 小红书爆款图文生成【零一数科·出品】 API 契约（v0.1.0 · 异步任务）

**异步任务模型**：创建立即返回 `task_id`，客户端用 `GET` 轮询进度与结果，`completed` 后从 `data.markdown` 取报告、从 `data.total_points` 取实扣。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。

> ⚠️ **基址偏差**：API 文档 §1.1 给出后端直连 `http://120.77.156.6:8001`（明文 IP+端口、无 SSL）；本 skill 按生成器标准 §3 写死生产网关 `https://claw.lingyishuke.com/services`。若网关未接入此接口、需直连后端调试，设 `LY_BASE_URL=http://120.77.156.6:8001` 并加 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure`（IP 走 http 无 SSL）。

鉴权：`Authorization: Bearer <api_key>` + `Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。所有接口仅支持 Bearer 头部鉴权，账号身份从 Key 解析；**请求体不得夹带账号信息**。脚本另带客户端约定头 `X-Appbuilder-From: openclaw`（API 文档 §1.3 未列，通常无害；用于平台侧来源标识）。配置/创建/轮询仅支持 Bearer；参考图上传两接口额外支持裸 key（脚本统一用 Bearer，无需分支）。

> 本 API **无幂等机制**：文档全文无 `idempotency` 字样，§4.3「请求体为 JSON 对象，禁止未声明字段，夹带会 422」。故标准 §9 的「`X-Idempotency-Key` 头 + body `idempotency_key`」**不适用**：脚本不发幂等头、不向 body 注入 `idempotency_key`，CLI 亦无 `--idempotency-key`。重复提交会创建新任务并独立计费——防重复扣点靠「同一意图避免重复 POST」由人/调用方保证。

> ⚠️ **本 API 与标准范式的偏差**（脚本与 SKILL.md 均已据此处理）：
> 1. **基址差异**：见上。生产网关 vs 后端直连 IP。
> 2. **状态枚举**为 `pending`/`running`/`completed`/`failed`/`timeout`（非标准 `succeeded`/`failed`/`partial_failed`/`billing_failed`）。终态成功 = `completed`。
> 3. **报告 markdown 取法**为 `data.markdown`（单串，后端自带一级标题），非 `data.results.<module>.markdown`。脚本 `extract_markdown` 兼容多种形态。
> 4. **扣点字段为 `data.total_points`**（顶层整数），非标准的 `data.billing.total_points`（字符串）。脚本 `extract_total_points` 已兼容。
> 5. **无 `POST /{id}/retry` 接口**：文档无重试接口，失败/超时需用**原始 payload 整体重交**创建新任务。脚本 `--retry-task` 仍保留 CLI 入口，但实现是「重新创建新任务」（新 `task_id`、**独立扣费**），而非传统原地 retry。
> 6. **每次新任务独立计费**：失败重提是一次新的可计费提交，不享受「已成功模块不重跑」。话术须如实告知用户。
> 7. **有额外 `GET /config` 接口**拉取 `target_platform` / `seeding_structure` / `brand_tone` **三组枚举**，三者均为创建必填且值须来自 config 实时 options，文档**禁止硬编码示例值**。脚本提供 `--fetch-config` 拉取实时枚举。
> 8. **有可选参考图上传分支**（§3）：取预签名 URL → PUT 文件二进制 → 确认换 `image_id`，最多 3 张，**单张 ≤10MB**（脚本本地预判，超限退码 3 不发起上传、不扣点；API 文档未明示该上限，属脚本侧约定）。**偏差**：上传 PUT 直传单次 HTTP 超时设为 **300s**（标准 §9 默认 60s，图片上传放宽），JSON 接口仍 60s；上传发生在创建任务之前，任一步失败任务未发起、未扣点。
> 9. **上传确认接口成功 HTTP 201**（非 200）：脚本对该步独立判定 `status in (200,201)`+`result.success`，不复用只认 200 的 `_parse_task_response`。
> 10. **completed 但 markdown 延迟落库的宽限处理**：后端不保证 `status=completed` 时 `data.markdown` 已原子回填（§5.5 明示可选字段可省略，§5.9 示例不代表原子性）。脚本设 `COMPLETED_REPORT_GRACE_SECONDS=60` 宽限窗口——终态出口若见 `completed` 但 markdown 空，在 60s 内继续轮询等补齐（参照视频拆解 v5.0.0 的 `COMPLETED_REPORT_GRACE_SECONDS`）；宽限内命中 md 即正常交付(exit 0)，status 翻 failed/timeout 则走失败分支(exit 12)，超时仍空则**兜底落盘**一个含续查指引的 md + stdout 正文 + exit 12（不本地伪造真实正文，agent 据指引建议续查/重提）。三处终态出口（`wait_for_task` 入口短路 / 轮询循环内 / `--poll-task` 已终态分支）均触发宽限。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 创建任务 | POST | `/api/v1/content/seeding-article-generation` | 主路径（立即返回 `task_id`） |
| 查询任务 | GET | `/api/v1/content/seeding-article-generation/{task_id}` | 轮询进度与结果 |
| 取配置 | GET | `/api/v1/content/seeding-article-generation/config` | `--fetch-config` 拉三组枚举（不创建任务、不扣点） |
| 取预签名上传 URL | POST | `/api/v1/content-ops/images/public-upload-url` | 上传参考图第 1 步（可选） |
| 直传图片二进制 | PUT | `<预签名 upload_url>` | 上传参考图第 2 步（可选，不带平台 Authorization） |
| 确认上传 | POST | `/api/v1/content-ops/images/public-upload-confirm` | 上传参考图第 3 步换 `image_id`（成功 HTTP 201） |
| 重试 | — | **无** | `--retry-task` 实为重新创建新任务（见偏差 5） |

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
| 400 | 参数语义错误、枚举不在 config options、配置缺失 | 3 |
| 401 | 缺/格式错/无效 API Key | 8 |
| 402 | 点数不足最低门槛（账户需 ≥100 点） | 4 |
| 403 | 当前 Key 无权访问该任务（停止轮询、确认 Key） | 10 |
| 404 | 任务不存在 | 10 |
| 422 | JSON 结构/字段校验失败（夹带未声明字段、类型错误等） | 3 |
| 5xx | 服务内部错误/上游暂不可用 | 11 |

---

## 1. 创建任务（异步）

`POST /api/v1/content/seeding-article-generation`

落库后立即返回 `data`（含 `task_id`，通常 `status: pending`）。后续在后台执行；客户端必须用 GET 轮询至终态。成功仅表示「已提交」。

### 请求体

```json
{
  "product_or_topic": "怡宝本优矿泉水",
  "selling_points": ["来自深岩矿泉水源，天然均衡矿物质", "口感清甜顺滑日常补水"],
  "target_platform": "xhs",
  "seeding_structure": "pain",
  "brand_tone": "premium",
  "reference_text": "偏小红书真人分享语气，不要硬广",
  "generate_images": true,
  "render_text_on_image": true,
  "image_count_config": { "cover": 1, "image": 1 },
  "reference_images": ["3876497687e04f52831afc216c4039ad"],
  "reference_image_desc": "晨光桌面、透亮水杯倒水瞬间、清新自然光",
  "origin": "01workbuddy",
  "origin_method": "skill"
}
```

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `product_or_topic` | string | 是 | — | 去空白后非空，≤30 字 | 产品或话题名称 |
| `selling_points` | string[] | 是 | — | 1–3 条非空；单条 >20 字后端截断 | 核心卖点 |
| `target_platform` | string | 是 | — | 必须取自 config 实时枚举 value | 目标发布平台 |
| `seeding_structure` | string | 是 | — | 必须取自 config 实时枚举 value | 种草正文结构型 |
| `brand_tone` | string | 是 | — | 必须取自 config 实时枚举 value | 品牌/内容调性 |
| `reference_text` | string | 否 | `""` | ≤500 字 | 用户补充/参考文案 |
| `generate_images` | boolean | 否 | `false` | — | 是否实际调生图；`false` 时通常只产方案与 AI 生图 Prompt |
| `render_text_on_image` | boolean | 否 | `false` | 仅 `generate_images=true` 有意义 | 是否允许把文字画进图 |
| `image_count_config` | object | 否 | cover=1/image=1 | 见下 | 封面与配图张数 |
| `reference_images` | string[] | 否 | `[]` | 最多 3 个 image_id | 参考图 id 数组（由上传确认接口返回） |
| `reference_image_desc` | string | 否 | `""` | >100 字截断 | 参考图附加提示词 |
| `origin` | string | 否 | `""` | — | 调用来源/宿主（埋点），如 `01workbuddy`。脚本默认 `01workbuddy` |
| `origin_method` | string | 否 | `""` | — | 调用方式（审计/溯源），如 `skill`。脚本默认 `skill` |

**`image_count_config` 子字段**：

| 子字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| `cover` | integer | 否 | 1 | 0–3 | 封面张数 |
| `image` | integer | 否 | 1 | 0–8 | 配图张数 |

> ⚠️ **禁止夹带未声明字段**：§4.3 明示请求体禁止未声明字段，夹带会 HTTP `422`。脚本只构造上表字段；可选参数缺省即不传。`render_text_on_image` 仅在 `generate_images=true` 时脚本才写入。`image_count_config` 仅在 `--cover-count` 或 `--image-count` 显式传时才构造，且只含显式传入的子键。`reference_image_desc` 仅在 `reference_images` 非空时才写入。

### 响应 `data`

创建成功通常 `pending`，无 markdown：

```json
{ "task_id": "eyJhbGciOiJIUzI1NiI...", "status": "pending" }
```

终态 `completed` 示例：

```json
{
  "task_id": "eyJhbGciOiJIUzI1NiI...",
  "status": "completed",
  "current_stage": null,
  "progress_message": "种草图文生成已完成",
  "error_message": null,
  "markdown": "# 种草图文方案 · 怡宝本优矿泉水\n\n> 平台：小红书 · 结构：pain · 调性：高级\n\n## 0. 输入要素\n\n...\n## 1. 钩子标题\n\n...\n## 3. 正文文案\n\n...\n",
  "total_points": 12
}
```

| 字段 | 类型 | 一定返回 | 说明 |
|------|------|----------|------|
| `task_id` | string | 是 | 任务 ID；轮询/重试靠它。**JWT 形，含 `.`，轮询须 URL 路径编码并原样传** |
| `status` | string | 是 | 见枚举 |
| `current_stage` | string | 否 | 当前执行阶段 |
| `progress_message` | string | 否 | 进度说明 |
| `error_message` | string | 否 | 失败/渲染异常说明 |
| `markdown` | string | 否 | 通常仅 `completed` 返回；种草图文方案 Markdown |
| `total_points` | integer | 否 | 实际消耗点数；扣点成功后返回（如 `12`）。缺失不当失败 |

> **报告 markdown 取法**：脚本从 `data.markdown`（单串）取。后端 `markdown` **已自带一级标题**（`# 种草图文方案 · …`），脚本检测到 H1 即**原样输出、不再前置脚本标题、不插分隔线**，避免出现两个 H1；仅当后端 markdown 无 H1 时才前置 `# 种草图文方案：<话题摘要>` 兜底。正文由后端渲染、不可改 table，**必须原样使用、不本地改写/总结/重排**；`completed` 但缺 markdown → 透出「结果暂不可用」，不本地伪造正文。

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

`GET /api/v1/content/seeding-article-generation/{task_id}`

- {task_id} 必须 **URL-path-encode** 后原样传入（JWT 含 `.` 等，先编码）。
- 必须用创建时的**同一 API Key**（身份绑定任务）；`403` 表示「当前 Key 无权访问该任务」。
- 响应 `data` 形状与创建相同。脚本默认每 5s 轮询，单次 HTTP 超时 60s，单次轮询等待上限 90s（到点非失败，emit 进行中后退出码 13，可续 `--poll-task`）。整体建议封顶 ~25 分钟（开启 `generate_images=true` 时更耗时）避免无限轮询。

---

## 3. 上传参考图（可选，最多 3 张）

创建任务时如需 `reference_images`，先按本流程拿到 `image_id`（最多 3 个），再写入创建请求。不需要参考图时跳过本节全部接口。流程固定三步：

1. `POST .../public-upload-url` 取预签名上传地址与 `upload_id`
2. 用返回的 `method`（一般为 `PUT`）把**原始图片二进制**上传到 `upload_url`（不再套 JSON）
3. `POST .../public-upload-confirm` 确认上传，得到 `image_id`

### 3.1 取预签名上传 URL

`POST /api/v1/content-ops/images/public-upload-url`

请求体：`{ "filename": "product_shot.png" }`（`filename` 需带合法扩展名）。

允许扩展名：`.png` / `.jpg` / `.jpeg` / `.webp` / `.gif` / `.bmp`。最多 3 张，**单张 ≤10MB**（脚本本地预判，超限退码 3 不发起上传；API 文档未明示该上限，属脚本侧约定）。

成功返回 `data` 主要字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | string | 本次上传会话 id，确认时必填 |
| `upload_url` | string | 预签名上传 URL（同义字段 `url`） |
| `method` | string | 上传 HTTP 方法，一般为 `PUT` |
| `expires_in` | integer | 预签名有效期（秒） |

```json
{ "data": { "upload_id": "upl_xxxxxxxx", "upload_url": "https://oss.../path?signature=...", "url": "https://oss.../path?signature=...", "method": "PUT", "expires_in": 3600 } }
```

### 3.2 直传图片二进制

拿到 `upload_url` 后，在有效期内用 `method` 上传**文件二进制**（不带平台 Authorization，OSS 直传），Content-Type 按实际图片类型（如 `image/png`）：

```bash
curl -X PUT "${UPLOAD_URL}" --data-binary @"/path/to/product_shot.png" -H "Content-Type: image/png"
```

成功 HTTP 200/201/204。脚本判 `status in (200,201,204)`；4xx（预签名失效）归退出码 11 视作设施性可重试错误。**偏差**：此步单次 HTTP 超时设为 **300s**（图片上传放宽，标准默认 60s）。

### 3.3 确认上传

`POST /api/v1/content-ops/images/public-upload-confirm`

> 成功时 HTTP 状态码为 **201**。脚本判 `status in (200,201)`+`result.success`（不复用只认 200 的 `_parse_task_response`）。

请求体：`{ "upload_id": "upl_xxxxxxxx", "extra_data": {} }`。

成功返回 `data` 主要字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `image_id` | string | **业务图片 id**；创建任务时写入 `reference_images` |
| `image_url` | string | 可访问图片 URL（展示用） |

```json
{ "data": { "image_id": "3876497687e04f52831afc216c4039ad", "image_url": "https://cdn.example.com/path/product_shot.png" } }
```

### 3.4 与创建任务的衔接

- 对每张参考图重复「取 URL → PUT → 确认」，收集最多 **3** 个 `image_id`。
- 创建任务时：`"reference_images": ["3876497687e04f52831afc216c4039ad"]`，可附 `"reference_image_desc": "产品实拍，白底，正面 45 度"`。
- `reference_images` 只接受确认上传后的 `image_id` 字符串数组，**不要传 URL 或本地路径**。
- 上传发生在创建任务**之前**；任一步失败任务未发起、未扣点（脚本按性质归入退出码 3/8/10/11，不自创码 9）。

---

## 4. 取配置（拉取三组枚举）

`GET /api/v1/content/seeding-article-generation/config`

- 无 path/query/body 参数；Bearer 鉴权。
- 不创建任务、不涉扣点。
- 返回 `data` 为字段配置数组，含三组 field：

```json
{
  "data": [
    { "field": "target_platform", "label": "目标平台", "desc": "必填；创建任务时传入 target_platform，值必须来自 options", "options": [{"value": "xhs", "label": "小红书", "desc": ""}, {"value": "wechat", "label": "公众号", "desc": ""}] },
    { "field": "seeding_structure", "label": "种草结构", "desc": "必填；创建任务时传入 seeding_structure，值必须来自 options", "options": [{"value": "aida", "label": "AIDA型", "desc": ""}, {"value": "pain", "label": "痛点型", "desc": ""}, {"value": "dry_goods", "label": "干货型", "desc": ""}, {"value": "emotion", "label": "情绪型", "desc": ""}, {"value": "list", "label": "清单型", "desc": ""}, {"value": "comparison", "label": "对比型", "desc": ""}] },
    { "field": "brand_tone", "label": "品牌调性", "desc": "必填；创建任务时传入 brand_tone，值必须来自 options", "options": [{"value": "premium", "label": "高级", "desc": ""}, {"value": "sincere", "label": "活泼", "desc": ""}, {"value": "professional", "label": "专业", "desc": ""}] }
  ]
}
```

> 以上 `options` 仅为示例，**实际可选值以接口实时返回为准**。

- 三组（`target_platform` / `seeding_structure` / `brand_tone`）均为创建任务**必填**，且 value 必须取自实时 options。脚本 `--fetch-config` 拉取并展示给用户选；选定后以 `--target-platform` / `--seeding-structure` / `--brand-tone` 传入创建。
- **禁止硬编码示例值**（如直接写 `xhs`/`pain`/`premium`）；后端枚举可能随运营配置变化。
- 若某 field 的 `options` 为空，创建任务会因无法校验枚举而失败，应提示配置缺失、联系管理员，不要硬填。

---

## 5. 扣点字段

```json
{ "total_points": 12 }
```

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.total_points` | integer | **本次实际扣点（终态 `completed` 后返回）** |

- 创建前会校验账户可用点数门槛（账户需 ≥**100 点**，为门槛、非价格）。不足 → HTTP `402`，不创建任务。
- **实际扣点仅 `completed` 时发生**；`pending`/`running`/`failed`/`timeout` 均不扣。
- 重复轮询同一 `completed` 任务**不重复扣点**。
- `total_points` 为可选字段，缺失不当失败。
- 约定预估（仅提示、非实扣）：100 点起步（=账户门槛值，作约估上限提示）；最终以服务端实际扣除为准。

---

## 6. 余额不足响应

```json
{ "api_version": "v1", "result": "error.payment_required", "code": 402, "message": "当前可用点数不足，种草图文生成至少需要 100 点，请充值后再试", "timestamp": "...", "detail": null, "trace_id": null }
```

本 API 通常**无 `recharge_url`** 字段，充值提示在 `message` 内。脚本遇 402 以退出码 4 终止，透出 message（若响应含 `recharge_url` 则一并透出，引导充值后重新创建）。

---

## 7. 枚举速查

**`status`**：`pending` / `running` / `completed` / `failed` / `timeout`。

**`target_platform`** / **`seeding_structure`** / **`brand_tone`**：均取自 `/config` 实时枚举（如 `xhs` / `pain` / `premium` 等示例），**勿硬编码**。

**`image_count_config`**：`cover` 0–3（默认 1）、`image` 0–8（默认 1）。

**参考图扩展名**：`.png` / `.jpg` / `.jpeg` / `.webp` / `.gif` / `.bmp`；最多 3 张。
