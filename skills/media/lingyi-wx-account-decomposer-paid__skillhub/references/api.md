# 微信视频号账号拆解 API 目录

后端「微信视频号账号拆解」相关接口。base url 固定 `https://claw.lingyishuke.com/services`（写死在脚本里）。

鉴权：所有接口都带 `Authorization: Bearer <api_key>`；创建接口还需 `Content-Type: application/json`。API Key 由脚本从技能目录下 `config.json` 的 `LY_API_KEY` 字段读取（回退环境变量 `LY_API_KEY`）。

## 接口一览

| 方法 | 路径 |
| --- | --- |
| POST | `/api/v1/common-gateway/analysis-skill/wx-video-account-analysis` |
| GET  | `/api/v1/common-gateway/analysis-skill/wx-video-account-analysis/{task_id}` |

---

## 1. 创建任务

`POST /api/v1/common-gateway/analysis-skill/wx-video-account-analysis`

按视频号账号名称发起拆解任务。

- **请求**：

```json
{
  "account_name": "央视新闻"
}
```

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `account_name` | string | 是 | 视频号账号名称（昵称） |
| `platform` | string | 否 | 平台，可不传 |

- **成功响应**：外壳与查询接口一致，`data` 含任务信息：

```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "微信视频号账号拆解任务创建成功",
  "timestamp": "2026-07-10T12:00:00.000000",
  "data": {
    "task_id": "eyJvcHNfdGFza19pZCI6Li4uIn0.xxxxx",
    "status": "pending"
  }
}
```

| 字段 | 含义 |
| --- | --- |
| `data.task_id` | 任务 ID，用于轮询；原样保存 |
| `data.status` | 任务状态，创建后通常为 `pending` |
| `data.<点数字段>` | **可选**。服务端有时在创建响应里返回本次预计/已扣点数（命名见下方「预计/实际扣点」）。返回了脚本就用真实值，没返回回退约 168 点（预估参考，实际按任务复杂度而定，最终以服务端计费为准）。 |

脚本支持 `--estimate-only`：只创建任务、拿到 `task_id` 与预计扣点后即退出（不轮询），打三行标记：

```text
ACCOUNT_TASK_ID=<task_id>
ACCOUNT_ESTIMATE_POINTS=<预计扣点；服务端返回真实值，否则 168>
ACCOUNT_ESTIMATE_SOURCE=<服务端返回 | 默认估算（服务端未在创建响应里返回点数字段）>
```

助手据此在确认前把预计扣点告诉用户，用户确认后再用 `--task-id` 轮询。

- **错误响应**：`result` 为 `error.*`，`code` 取 HTTP 语义：

```json
{
  "api_version": "v1",
  "result": "error.bad_request",
  "code": 400,
  "message": "account_name 不能为空",
  "timestamp": "2026-07-10T12:00:00.000000"
}
```

| HTTP | 常见 `message` 场景 |
| --- | --- |
| 400 | 参数无效 |
| 401 | API Key 无效或缺失 |
| 402 | 点数不足 |
| 502 | 服务暂时不可用 |

脚本：401/403 → 退出码 3；402 / `message` 命中「余额不足」「点数不足」或有 `recharge_url` → 退出码 4（并透出充值链接）；其它非 `success` 终止 → 退出码 4。

---

## 2. 查询任务状态

`GET /api/v1/common-gateway/analysis-skill/wx-video-account-analysis/{task_id}`

任务 id 作为路径参数。

- **响应**：外壳与创建接口相同。`data` 字段分两种情况：

**进行中 / 未落库报告**（`status` 为 `pending` / `running` 等）：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `task_id` | string | 任务 ID |
| `scene` | string | 场景，如 `account_analysis` |
| `status` | string | `pending` / `running` / `completed` / `failed` |
| `current_stage` | string \| null | **可选**。当前阶段标识（脚本按 `STAGE_LABEL` 映射成中文）。真实样例里 pending/running 通常不返回。 |
| `progress_message` | string \| null | **可选**。进度文案。真实样例里通常不返回。 |
| `progress` / `progress_percent` | number \| null | **可选**。进度百分比（0~100 或 0~1，脚本自动归一）。 |
| `steps_timing` | object \| null | **可选**。各阶段 `{stage, description, duration_ms}`；完成态常见，脚本会取其中最后一个有时长的阶段作为「已推进到」提示。 |

> ⚠️ **注意**：API 文档里写的 `current_stage`、`progress_message`、进度百分比，在真实响应里**通常并不存在**（样例里这些只在完成态的 `steps_timing` 出现过）。脚本 `extract_progress(data)` 做兼容——有就用，没有返回 `(None,None,None)`，由 `poll_loop` 回退用「状态 + 已等待时长」反馈，**绝不伪造进度**。判定任务是否完成只看 `status`。

### 进度反馈（脚本侧）

`poll_loop` 在轮询期间持续向 stderr 输出进度，供调用方转述：

- 状态/阶段/进度文案/百分比**任一变化** → 立刻打一行；
- 否则**每 30s（`PROGRESS_KEEPALIVE_SECONDS`）打一行保活**，更新已等待时长，避免长时间沉默；
- 服务端无进度细节时打「服务端处理中，请稍候…」。

行形如 `[执行中] · 已等待45s · 当前阶段：视频拆解`。

**已完成、报告已落库**（`status` = `completed`）——真实响应**不含 `data.markdown`**，报告是结构化 JSON，按 schema 版本不同落在：

- **v1 / v1c**：`data.result.sections[]`
- **v2**：`data.report_v2`

`data` 完整键（真实样例）：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `task_id` | string | 任务 ID |
| `scene` | string | 场景，如 `account_analysis` |
| `status` | string | `completed` / `failed` |
| `result` | object \| null | v1/v1c 报告结构（进行中可为 null） |
| `report_v2` | object \| null | v2 报告结构（仅 v2） |
| `errors` | array | 失败原因列表（failed 时可能有内容） |
| `started_at` / `completed_at` | string | 开始 / 完成时间 |
| `steps_timing` | object | 各阶段耗时（仅完成态，**不是**当前阶段） |
| `usage_tokens` | array | 各模型 token 用量 |

**v1 / v1c 的 `data.result`**：

| 字段 | 含义 |
| --- | --- |
| `sections[]` | 报告版块数组，按 `order` 排序 |
| `next_actions[]` | 下一步动作 |
| `degradation_info` | 数据降级说明 |
| `raw_result` | 原始分块产出（account/overview/portrait/...） |
| `errors[]` | 错误列表 |

每个 `section` = `{ order, key, title, section_type, content }`：

| 字段 | 含义 |
| --- | --- |
| `order` | 版块序号 |
| `key` | 版块标识（account/overview/portrait/...） |
| `title` | 版块中文标题 |
| `section_type` | `markdown`（content 已是 markdown 字符串）或 `raw_json`（content 为 dict/list） |
| `content` | 版块内容（类型随 section_type） |

**v2 的 `data.report_v2`** 为一个对象，8 个块：`account` / `overview` / `portrait` / `content_structure` / `videos` / `explosive_formula` / `competitors` / `recommendations`（字段结构详见 `素材/报告字段映射.md`）。

**completed 示例（v1c，结构已精简）**：

```json
{
  "api_version": "v1c",
  "result": "success",
  "code": 200,
  "data": {
    "task_id": "ee23bef4d9404a3d964c66e380b6a5d9",
    "scene": "account_analysis",
    "status": "completed",
    "result": {
      "task_id": "ee23bef4d9404a3d964c66e380b6a5d9",
      "status": "completed",
      "sections": [
        { "order": 1, "key": "account", "title": "账号信息", "section_type": "raw_json",
          "content": { "name": "零一数科", "platform": "视频号", "..." : "..." } },
        { "order": 2, "key": "overview", "title": "账号概览", "section_type": "markdown",
          "content": "**账号定位**：...\n**阶段判断**：起步期\n..." }
      ],
      "raw_result": { "account": {...}, "overview": {...}, "..." : "..." }
    },
    "errors": [],
    "started_at": "2026-07-08T17:33:06.987353",
    "completed_at": "2026-07-08T17:35:21.422494"
  }
}
```

**failed 示例**：失败原因可能在 `data.error_message`（文档口径）、`data.errors`（真实响应常出现）、或 `data.result.errors`：

```json
{
  "result": "success",
  "code": 200,
  "data": {
    "task_id": "...",
    "scene": "account_analysis",
    "status": "failed",
    "errors": ["抓取失败", "LLM 超时"],
    "started_at": "...",
    "completed_at": "..."
  }
}
```

### 查询错误

| HTTP | 场景 |
| --- | --- |
| 401 | API Key 无效 |
| 403 | 无权访问该 `task_id` |
| 404 | 任务不存在 |

## 状态枚举

| 值 | 含义 | 是否终态 |
| --- | --- | --- |
| `pending` | 排队中 | 否 |
| `running` | 执行中 | 否 |
| `completed` | 完成 | 是 |
| `failed` | 失败 | 是 |

脚本对大小写做了归一（兼容大写枚举）。未列出的状态值按未知处理：脚本原样透出 status，不报错。

## 报告渲染（脚本侧）

真实接口**不返回现成 markdown**。脚本 `build_report(data)` 按优先级取报告：

1. 若 `data.markdown` 存在（服务端偶尔返回现成 markdown），直接用它；
2. 否则用 `data.result.sections[]`（v1/v1c），按 `order` 排序、每块出 `## 标题`，`section_type=markdown` 的原样输出、`raw_json` 的递归渲染成 bullet 列表；
3. 否则用 `data.report_v2`（v2），按 8 块顺序出标题并渲染。

渲染后做 `normalize_markdown` 转义规整与渲染态校验，再用 `=== ACCOUNT_REPORT_START === / === ACCOUNT_REPORT_END ===` 包裹打到 stdout。失败原因用 `_extract_error` 从 `error_message` / `errors` / `result.errors` 多处提取。

## 预计 / 实际扣点

真实样例响应里**没有显式的点数字段**（只有 `steps_timing`、`usage_tokens`）。脚本 `extract_points(payload)` 做兼容，在 payload 及 `data / data.billing / data.result / data.payment / data.usage` 等层级查找以下任一字段，命中即用真实值：

```text
points_used credits_used used_points deducted_points charged_points points_cost
point_used consumed_points billing_points spent_points cost_points
estimated_points estimated_cost points_estimate points_required points_needed
expected_points points
total_points   ← 完成态常以此给出本次真实扣点
```

- **任务前**：`--estimate-only` 时用创建响应里命中的字段作为「预计扣点」打 `ACCOUNT_ESTIMATE_POINTS`；都没命中则回退约 168 点（标记 `ACCOUNT_ESTIMATE_SOURCE=默认估算…`）。**预估只是参考，实际扣点按任务复杂度而定，最终以服务端实际计费为准。**
- **任务后**：`deliver_report` 时再在终态响应里找一遍（完成态常命中的是 `total_points`，给出本次真实扣点），回退创建时的 `points`，仍无则 `ACCOUNT_POINTS_USED` 为空，由助手按约 168 点口径说明、最终以服务端按任务复杂度计费为准。

> 之所以回退而不是硬报：避免向付费用户报错数字；168 是经验估值，实际扣点按任务复杂度而定，最终以服务端实际计费 / 01Claw 账户扣减为准（可高可低）。

## 调用顺序

1. `POST` 创建 → 取 `data.task_id`
2. 间隔 5～15 秒 `GET` 轮询（脚本默认 8s）
3. `data.status` 为 `completed` 时，由脚本把 `data.result.sections`（或 `data.report_v2`）渲染成 Markdown 输出
4. `data.status` 为 `failed` 时从 `error_message` / `errors` 取失败原因

> 竞态：服务端可能先置 `completed` 再写入 `markdown`。脚本在状态为 `completed` 但 `markdown` 为空时，会在 60s 宽限窗口内继续轮询等报告补齐；超时仍空则退出码 7。
