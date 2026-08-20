# PatSeek API 接口参考

> 本文档供第三方开发者调用 PatSeek API 时参考，包含完整的接口规范、参数说明、返回字段和错误码。所有字段信息均基于实测验证（2026-08-09，28 组 API 调用）。

## 基本信息

| 项目 | 值 |
|---|---|
| 基础 URL | `https://patseek.cn` |
| 协议 | HTTPS |
| 认证方式 | Bearer Token（`Authorization` 请求头） |
| 内容类型 | `application/json` |

## 认证

API Key 格式：`ps_` + 32 位十六进制字符串。

```
Authorization: Bearer ps_<你的API_KEY>
```

### 如何获取 API Key

1. 访问 [https://patseek.cn](https://patseek.cn) 注册/登录
2. 进入「个人中心 → API Key 管理」
3. 点击「创建新 Key」，复制保存（只显示一次）

## 调用计量

以响应中的 `credits_charged` 为准。0 结果也扣费。

| 接口 | 消耗 |
|---|---|
| Bool 检索 `POST /v1/search` | 1 积分 |
| 专利详情 `GET /v1/patent/{id}` | 1 积分 |
| 语义检索（异步） | 5 积分 |
| key-info `GET /v1/key-info` | 0 积分 |
| 任务查询/列表/取消 | 0 积分 |

## 频率限制

| 接口 | 限制 |
|---|---|
| Bool 检索 | **10 次/分钟（硬限）**：实测第 11 次起返回 429，错误消息 "Rate limit exceeded: 10 per 1 minute"。客户端已按 6.5s 同类间隔自动节流（≈9.2 次/分） |
| 专利详情 | 60 次/分钟（文档值；实测连发 25 次 0.5s 间隔无 429，与 Bool 独立计数） |
| 语义检索提交 | 5 次/分钟 |
| 语义检索并发 | 同一 Key 最多 3 个并发任务，全局最多 10 个 |
| 任务查询/列表/取消 | 120 次/分钟 |

---

## 接口详情

### 1. Bool 关键词检索

**POST** `/v1/search`

请求体:

```json
{ "query": "低空空域 AND 无人机", "page": 1, "page_size": 20, "market": "cn" }
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 检索表达式，语法见 `query_syntax.md` |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数 1-50，默认 20（实测 51 起返回 422） |
| `market` | string | 否 | `cn`（默认）或 `world`。两库表面语法相同但字段行为不同，详见 `world_search_reference.md` |

**响应顶层字段：**

```
credits_charged, credits_remaining, total, total_pages, current_page,
page_size, has_next, has_prev, patent_list
```

- `total`：命中总数。10000 为显示上限，不代表精确数量。
- `total_pages`：总页数（total 达上限时也显示 10000）。

**patent_list 字段：**

始终返回的字段（所有查询类型）：

```
pid, appnum, title, ipcs, appdate, pubdate, applicant, abstract, claims
```

条件返回的字段（取决于**命中数量**和专利数据填充情况；规则 cn/world 两库一致）：

| 字段 | 命中 ≥10 | 命中 <10（含 PID 精确查） |
|---|:---:|:---:|
| `description` | ❌ 不返回 | ✅ 返回（个别专利仍缺/空，见下） |
| `figures` | ⚠️ 因专利而异 | ⚠️ 因专利而异 |
| `cited_cnt` | ⚠️ 因专利而异（world 恒返回，cn 不返回） | ⚠️ 因专利而异（world 恒返回，cn 不返回） |

> **注意**：API 不返回值为 null/empty 的字段键。`figures` 和 `cited_cnt` 是否出现取决于该专利在数据库中是否有对应数据。客户端必须用 `dict.get(key)` 或 `in` 检查字段是否存在，不能用固定索引访问。`figures` 字段为字符串（分号分隔的文件名列表），不是数组。
>
> **`description` 返回规则（2026-08-09 后台更新后实测）**：Bool 检索命中 <10 条（含 PID 精确查）返回 `description`；≥10 条不返回。**即使命中 <10，个别国际专利仍缺 `description`**（键缺失，或键在但空串，如 GB `D0` 检索报告类实测 `GB202010345D0` 空串）——客户端须兼容三态：键缺失 / 键在但空串 / 有内容。国际专利单篇全文的获取路径详见 §2「world 库获取 `description`」。

**query 语法要点：**

- `A B` 或 `A AND B` — 所有词都必须出现
- `A OR B` — 任一出现即命中
- `(A OR B) C` — 括号控制优先级
- 字段前缀：`AP=` 申请人、`IPC=` 分类、`PID=` 公开号、`AN=` 申请号（world 库无数据）、`AD`/`PD` 日期、`NOT=` 排除、`CC=` 国家（仅 world）

完整语法见 `query_syntax.md`，world 库差异见 `world_search_reference.md`。

### 2. 专利详情

**GET** `/v1/patent/{identifier}?market=cn|world&include_enrichment=true|false`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `identifier` | string | 是 | 公开号或申请号（路径参数） |
| `market` | string | 否 | `cn`（默认）或 `world` |
| `include_enrichment` | bool | 否 | 默认 `true`；补充发明人、优先权、法律状态等 |

返回与 Bool 相同的 `SearchResponse` 结构，`patent_list` 含 0 或 1 条结果。0 结果也扣 1 积分。

> **market 必须匹配**：查 CN 专利不带 `market=world`，查国际专利必须带 `market=world`。默认 `cn` 库查不到 US/EP 等专利。

**patent_list[0] 字段（cn 库）：**

始终返回：`pid, appnum, title, ipcs, appdate, pubdate, applicant, abstract, claims, description, figures, aggregation`

条件返回：

| 字段 | enrichment=true (complete) | enrichment=false | identity_mismatch |
|---|:---:|:---:|:---:|
| `enrichment` | ✅ | ❌ | ❌（安全丢弃） |

> cn 库详情接口不返回 `cited_cnt`。aggregation 始终返回，其 `status` 字段反映增强状态。

**patent_list[0] 字段（world 库）：**

与 cn 库相同，但额外返回 `cited_cnt`。

#### world 库获取 `description`（国际专利全文）

**三条可用路径（2026-08-09 后台更新后实测）：**

1. **`bool "PID=(<公开号>)" --market world`（首选，覆盖最全）**：PID 精确查命中 1 条，直接返回 `description`，覆盖整个检索索引——**包括 DE/KR 等详情接口查不到的专利**（实测 DE102022213181A1=50k、KR20240171247A=25k 字符）。
2. **详情接口 `GET /v1/patent/{pid}?market=world`**：返回 `description`，但覆盖率是**子集**——WO/EP/US/JP/FR/GB 可返回，**DE/KR 等 `patent_list` 为空**（仍扣 1 积分）。
3. **普通关键词命中 <10 时**：结果直接带 `description`，无需额外调用。

**覆盖率矩阵（实测，详情接口 / battery cooling 各国家抽样）：**

| 国家/类型 | 详情接口 | `bool "PID="` | `description` | `aggregation.status` | 说明 |
|---|:---:|:---:|:---:|:---:|---|
| WO | ✅ | ✅ | 有（~17k 字符） | `complete` | 完整全文 |
| EP | ✅ | ✅ | 有（~20k 字符） | `complete` | 完整全文 |
| US | ✅ | ✅ | 有（~22k 字符） | `complete` | 完整全文 |
| JP | ✅ | ✅ | 有（~108k 字符） | `primary_only` | 全文在，增强源暂不可用 |
| FR | ✅ | ✅ | 有（~23k 字符） | `identity_mismatch` | 全文在，增强被安全丢弃 |
| GB（`D0` 类） | ✅ | ✅ | `""`（空串） | `primary_only` | D0 为检索报告类文献，本身无说明书正文 |
| DE | ❌ `patent_list` 空 | ✅ 有（~50k） | 有 | — | 详情库无记录，但 bool PID 可拿全文 |
| KR | ❌ `patent_list` 空 | ✅ 有（~25k） | 有 | — | 详情库无记录，但 bool PID 可拿全文 |

> **关键结论**：
> - **`bool "PID=()"` 覆盖整个检索索引（含 DE/KR），详情接口只是子集**——优先级见上方三条路径。
> - **客户端必须兼容三种空态**：`patent_list` 为空、`description` 键缺失、或 `description` 为空串。对空态用快速链接回退 Google Patents / 各国官源阅读全文，不应重复调用接口。

**aggregation.status 含义：**

| status | 说明 |
|---|---|
| `complete` | 双源聚合成功，enrichment 字段可用 |
| `primary_only` | 增强源暂不可用，已返回主源详情 |
| `identity_mismatch` | 双源公开号不一致，enhancement 安全丢弃 |
| `disabled` | 请求关闭了增强（include_enrichment=false） |

**enrichment 字段（仅 status=complete 时存在）：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `inventors` | array | 发明人列表 |
| `priority_date` | string | 最早优先权日 |
| `prior_art_date` | string | 现有技术日 |
| `legal_status` | string | 法律状态（如 Pending、Granted） |
| `latest_legal_event` | object | 最新法律事件 `{date, code, title}` |
| `legal_event_count` | int | 法律事件总数 |
| `family_count` | int | 同族数量 |
| `citation_count` | int | 引证数 |
| `cited_by_count` | int | 被引数 |
| `similar_count` | int | 相似专利数 |
| `keywords` | array | 关键词列表 |
| `pdf_url` | string | PDF 链接（Google Patents） |
| `canonical_url` | string | 来源页（Google Patents） |

> enhancement 字段均为可选，客户端必须兼容字段不存在或 `aggregation.status` 非 complete 的情况，不应因此重复调用。
>
> **PDF 兜底原则（2026-08-09 实测）**：`pdf_url` 为空/缺失时，可对**已知公开号**尝试外源 PDF 兜底——如 freepatentsonline 两步取：①`GET https://www.freepatentsonline.com/{pid}.pdf` 返回 HTML 详情页（非直链），解析页内 `<iframe>` 的 `s3.amazonaws.com/pdf.sumobrain.com/...` 签名 URL（有效期约 2 天，须现抓现用）；②下载该 S3 URL 即得真 PDF。**覆盖（实测）**：**EP/WO 稳定可用**；**US 部分覆盖**（存在单件缺口，如部分 US 申请公开号、新近授权件）；**CN/JP/FR/DE/GB 不可用**（抽样均返回无 iframe 的通用落地页）。**未覆盖判据**：页面标题为 "FPO IP Research & Communities" 且无 iframe——直接判不可用，不要误读为成功。**注意**：①PDF 为**扫描件、无文本层**，仅供阅读/展示，不可程序提取文本；②公开号会被规范化（如 `US20260231843` → iframe 实为 `US20260231843P1.pdf`），一律以 iframe URL 为准。外源仅用于 **PDF 文件获取**，**不得替代 PatSeek 检索**；报告须标注 PDF 来源与获取日期。
>
> **CN 专利 pdf_url 专项（2026-08-09 实测 10 条）**：有值时即 Google Patents 存储直链（`patentimages.storage.googleapis.com/{hash}/{pid}.pdf`），**可直接下载、5/5 有效**（353KB–1MB）；**空值率约 50%**（`identity_mismatch`/`primary_only` 时 enrichment 被丢弃而为空，个别 `complete` 也空）。CN 空值时 **freepatentsonline 不覆盖、无自动化 PDF 兜底**——可经 Google Patents 页面（`https://patents.google.com/patent/{pid}/zh`，WebFetch 可达、可读全文）或 CNIPA 人工获取，报告中标注"PDF 需人工获取"。

### 3. Key 信息查询

**GET** `/v1/key-info`

返回当前 API Key 的状态信息，不扣积分。

```json
{
  "key_type": "personal",
  "billing_mode": "web_wallet",
  "active": true,
  "expires_at": "2026-10-27T15:59:59Z",
  "credits": null,
  "allowed_routes": ["search", "detail", "semantic"],
  "blocked_routes": [],
  "free_routes": []
}
```

| 字段 | 说明 |
|---|---|
| `key_type` | Key 类型（personal） |
| `billing_mode` | 计费模式（web_wallet） |
| `active` | Key 是否有效 |
| `expires_at` | 过期时间（ISO 8601 带时区） |
| `credits` | 余额（web_wallet 模式下为 null，以每次调用 `credits_remaining` 为准） |
| `allowed_routes` | 允许的路由 |
| `blocked_routes` | 被阻止的路由 |
| `free_routes` | 免费路由 |

### 4. 语义检索（异步任务）

**POST** `/v1/semantic/async`

请求体: `{ "query": "技术描述" }`

> 语义检索查询须用**中文技术描述**（传入 `market=world` 不会报错但返回空结果）。**实测结果含国际公开号（US/WO/JP/EP/KR，约占 20-25%）**——"仅支持 CN 库"指查询语言而非结果来源；结果集的 IPC 分布可用于分类方向确认，但**新兴领域排序可能失真（top-1 可为噪声），一律以整体结果集与 IPC 分布为准**。
>
> **语义先行用法**：完整深度且用户已给详细方案时，Bool 前先做 1 次语义检索，用于 IPC 分布确认 + 关键词扩展 + 新候选人发现（语义与 Bool 召回互补，不可互相替代；详见 SKILL.md"检索模式选择→语义先行"）。

**提交响应字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `task_id` | string | 任务 ID |
| `status` | string | 初始为 `pending` |
| `type` | string | 固定 `semantic` |
| `cache_hit` | bool | 是否命中缓存 |
| `credits_charged` | int | 本次消耗积分（5） |
| `credits_remaining` | int | 剩余积分 |
| `created_at` | string | 创建时间（ISO 8601） |
| `expires_at` | string | 过期时间（7 天后） |
| `estimated_wait_seconds` | int | 预计等待秒数 |
| `queue_position` | int | 队列位置 |

### 5. 查询任务状态/结果

**GET** `/v1/tasks/{task_id}?include_partial=true|false`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 任务 ID（路径参数） |
| `include_partial` | bool | 否 | `true` 时在 `running` 状态下返回已接收的部分结果 |

**任务状态流转：** `pending → running → succeeded | failed | cancelled`

**响应字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `task_id` | string | 任务 ID |
| `type` | string | 任务类型（semantic） |
| `status` | string | 当前状态 |
| `cache_hit` | bool | 是否命中缓存 |
| `progress` | object | 进度 `{received: N}`（已接收结果数） |
| `queue` | object/null | 队列信息 `{position, estimated_wait_seconds}`，running 后为 null |
| `result` | array/null | **列表**（非 dict）：succeeded 时为 patent 对象数组，pending/running 时为 null |
| `partial_results` | array/null | include_partial=true 且 running 时的部分结果，结构与 result 相同 |
| `credits_charged` | int | 消耗积分 |
| `refunded` | bool | 是否已退款 |
| `error` | string/null | 错误信息 |
| `created_at` | string | 创建时间 |
| `started_at` | string/null | 开始执行时间 |
| `finished_at` | string/null | 完成时间 |
| `expires_at` | string | 过期时间 |

**result/partial_results 中 patent 对象字段：**

| 字段 | 说明 |
|---|---|
| pid, title, ipcs, appdate, pubdate, applicant, abstract, claims | 基础字段 |
| similarity | 语义相似度分数（0-100，越高越相似） |
| cited_cnt | 引证数 |
| figures | 附图文件名列表（字符串） |

> 语义结果**不返回** `description` 和 `appnum`。`claims` 可能被截断，需用详情接口补全。

**轮询建议：** 每 20 秒查询一次。`progress.received` 可用于显示进度。`include_partial=true` 可在 running 时获取已到部分结果，适合流式处理。

### 6. 取消任务

**DELETE** `/v1/tasks/{task_id}`

响应: `{ "task_id": "...", "status": "cancelling" }`

取消不存在或已终止的任务返回 404 `TASK_NOT_FOUND`。

### 7. 列出任务历史

**GET** `/v1/tasks?limit=20`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 返回条数 1-100，默认 20（实测 101 起返回 422） |

**响应字段：**

```json
{ "items": [...], "limit": 20 }
```

> 响应键为 `items`（非 `tasks` 或 `task_list`）。

**items 中每个任务字段：**

`task_id, type, status, cache_hit, created_at, finished_at, progress`

（比查询单个任务少 `result`、`partial_results`、`credits_charged` 等字段）

---

## 错误码

| HTTP | code | 说明 |
|---|---|---|
| 401 | MISSING_API_KEY | 未提供 Authorization |
| 401 | INVALID_API_KEY | Key 无效 |
| 402 | INSUFFICIENT_CREDITS | 积分不足 |
| 403 | KEY_DISABLED | Key 已禁用 |
| 404 | — | 路径不存在（如空 identifier） |
| 404 | TASK_NOT_FOUND | 任务不存在或已过期 |
| 409 | TASK_ALREADY_TERMINATED | 任务已终止，无法取消 |
| 422 | — | 参数校验失败（如 page_size>50、limit>100），返回 detail 数组指明具体字段 |
| 429 | TASK_LIMIT_EXCEEDED | 语义并发超限 |
| 429 | — | 频率限制 |
| 500 | TASK_SUBMIT_FAILED | 任务创建失败 |
| 503 | DB_UNAVAILABLE | 数据库不可用 |

**422 响应示例：**

```json
{
  "detail": [{
    "type": "less_than_equal",
    "loc": ["body", "page_size"],
    "msg": "Input should be less than or equal to 50",
    "input": 51,
    "ctx": {"le": 50}
  }]
}
```

> 401/402/403 错误后，应停止当前操作并处理错误（更新 Key 或充值）。skill 中的处理协议见 SKILL.md "API Key 失效处理协议"。
