# 达人匹配 API 目录

后端「达人匹配」相关接口。base url 固定 `https://claw.lingyishuke.com/services`（写死在脚本里）。

鉴权：三个接口都必须携带 `Authorization: Bearer <api_key>`（仅支持 Bearer Token）；创建接口还需 `Content-Type: application/json`。API Key 由脚本从技能目录下 `config.json` 的 `LY_API_KEY` 字段读取（回退环境变量 `LY_API_KEY`）。账号身份由 API Key 自动识别，无需在请求中传递。轮询必须用创建任务时的同一个 API Key——`task_id` 与创建账号绑定，换号查询会 403。

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET  | `/api/v1/common-gateway/analysis-skill/creator-match/config` | 取可选枚举 |
| POST | `/api/v1/common-gateway/analysis-skill/creator-match` | 创建任务 |
| GET  | `/api/v1/common-gateway/analysis-skill/creator-match/{task_id}` | 轮询状态 |

---

## 1. 取参数配置

`GET /api/v1/common-gateway/analysis-skill/creator-match/config`

返回创建任务时可用的枚举配置。**请用 `options[].value` 作为创建任务入参，不要用 `label`。**

| 返回 field | 创建任务写入位置 |
| --- | --- |
| `industries` | 顶层 `industries` |
| `campaign_types` | 顶层 `campaign_types` |
| `price_band` | `product.price_band` |
| `decision_type` | `product.decision_type` |

`data` 是字段配置数组，每项 `{field, label, desc, options[]}`；`options[]` 单项 `{value, label, desc}`。

脚本 `--config` 以 `=== CREATOR_MATCH_CONFIG_START === / === END ===` 包裹原始 JSON 输出到 stdout，同时在 stderr 打一份人类可读清单（`label（value=…）`）供助手直接转述。

---

## 2. 创建任务

`POST /api/v1/common-gateway/analysis-skill/creator-match`

请求为平铺结构：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `platform` | string | 否 | 目标平台，默认 `channels`（微信视频号）；不能为空 |
| `industries` | string[] | 否 | 行业代码，可选值见配置接口 |
| `campaign_types` | string[] | 否 | 投放类型，可选值见配置接口 |
| `target_accounts` | object[] | 是 | 候选达人账号列表，**1～10 个**（超过 10 个返回 422）；`{account: 账号名称}`，首尾空白会被清理 |
| `product` | object | 是 | 产品信息，`name` 和 `selling_points` 必填 |
| `extra_data` | string | 否 | 扩展信息：文档抽取内容或其它补充文本，默认 `""` |

`product` 字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 产品名称；不能为空 |
| `selling_points` | string[] | 是 | 产品核心卖点列表，至少一个非空字符串 |
| `price` | number | 否 | 产品价格 |
| `price_band` | string | 否 | 产品价格档位 code；可选值见配置接口 `price_band.options` |
| `decision_type` | string | 否 | 消费决策类型（可透传）；可选值见配置接口 `decision_type.options` |

`extra_data` 选填字符串，用于承载文档抽取内容或其它补充文本；不传时默认 `""`。

成功响应 `data`：

| 字段 | 含义 |
| --- | --- |
| `data.task_id` | 任务凭证，用于轮询；原样保存，不要解析或修改 |
| `data.status` | 创建后通常为 `pending` |
| `data.<点数字段>` | **可选**。服务端有时在创建响应里返回点数（命名见「预计/实际扣点」）。返回了脚本就用真实值，没返回按 198 × 候选达人数 估算（预估参考，实际按账号数量/达人视频数量浮动，最终以服务端计费为准）。 |

脚本支持 `--estimate-only`：只创建任务、拿到 `task_id` 与预计扣点后即退出（不轮询），打三行标记：

```text
CREATOR_MATCH_TASK_ID=<task_id>
CREATOR_MATCH_ESTIMATE_POINTS=<预计扣点；服务端返回真实值，否则 198 × 达人数>
CREATOR_MATCH_ESTIMATE_SOURCE=<服务端返回 | 按 198 点/达人 × N 个达人估算（服务端未在创建响应里返回点数字段）>
```

助手据此在确认前把预计扣点告诉用户，用户确认后再用 `--task-id` 轮询。

错误响应 `result` 为 `error.*`，`code` 取 HTTP 语义：

| HTTP | 场景 | 处理 |
| --- | --- | --- |
| 400 | 参数错误、任务凭证无效 | 不要盲目重试；检查参数 |
| 401 | 缺/无效 API Key | 引导配置或更新 key |
| 403 | 无权访问该任务 | 确认是否用了创建任务时的 API Key |
| 404 | 任务不存在 | 确认 task_id |
| 422 | JSON 结构/字段校验失败（含 `target_accounts` 超过 10 个、`product.name`/`product.selling_points` 缺失等） | 按参数表修正，不要原样重试 |
| 500 | 未预期服务端错误 | 有限次数重试 |
| 502 | 服务暂时不可用 | 指数退避后有限次数重试 |

脚本：401/403 → 退出码 3；402 / `message` 命中「余额不足」「点数不足」或有 `recharge_url` → 退出码 4（并透出充值链接）；422 → 脚本前端已做必填校验（`product.name` / `product.selling_points` / `target_accounts` 1～10 个），若仍被 422 拒绝则 exit 4；网络/5xx → 退出码 6。

---

## 3. 查询任务状态

`GET /api/v1/common-gateway/analysis-skill/creator-match/{task_id}`

`task_id` 须 URL 路径编码并原样传递；无请求体。

> ⚠️ **HTTP 200 只表示「成功查询到任务状态」。任务本身失败时 HTTP 仍可能是 200，必须以 `data.status` 判断任务是否成功。**

`data` 字段：

| 字段 | 是否一定返回 | 含义 |
| --- | --- | --- |
| `task_id` | 是 | 与路径中一致 |
| `status` | 是 | 任务状态 |
| `current_stage` | 否 | 当前执行阶段 |
| `progress_message` | 否 | 进度说明 |
| `error_message` | 否 | 失败时的错误说明 |
| `markdown` | 否 | 完成后的达人匹配 Markdown 报告；通常仅在 `completed` 返回 |
| `total_points` | 否 | 实际消耗点数；当前版本通常不会返回 |

响应会省略值为 `null` 的可选字段，不应假设所有可选字段都存在。

### 状态枚举

| 值 | 是否终态 | 行为建议 |
| --- | --- | --- |
| `pending` | 否 | 排队中，等待后继续轮询 |
| `running` | 否 | 执行中，等待后继续轮询 |
| `completed` | 是 | 读取 `markdown` 作为最终报告 |
| `failed` | 是 | 停止轮询，将 `error_message` 告知用户 |
| `timeout` | 是 | 停止轮询，提示超时，可用 `--task-id` 恢复 |

脚本对大小写做了归一（兼容大写枚举）。

### 进度反馈（脚本侧）

`poll_loop` 在轮询期间持续向 stderr 输出进度，供调用方转述：

- 状态/进度文案/百分比**任一变化** → 立刻打一行；
- 否则**每 30s（`PROGRESS_KEEPALIVE_SECONDS`）打一行保活**，更新已等待时长，避免长时间沉默；
- 服务端无进度细节时打「服务端处理中，请稍候…」。

行形如 `[执行中] · 已等待45s · 达人匹配任务执行中`。

> ⚠️ API 文档里的 `current_stage` / `progress_message` 在 pending/running 阶段**通常不返回**。脚本 `extract_progress(data)` 做兼容——有就用，没有回退用「状态 + 已等待时长」反馈，**绝不伪造进度**。判定任务是否完成只看 `status`。

### completed 与竞态

`completed` 时 `data.markdown` 即为最终报告。服务端可能先置 `completed` 再写入 `markdown`：脚本在状态为 `completed` 但 `markdown` 为空时，会在 60s 宽限窗口内继续轮询等报告补齐；超时仍空则退出码 7。

### failed / timeout

失败原因在 `data.error_message`（或 `data.errors` / `data.message`）。`timeout` 是终态，附 `task_id` 可用 `--task-id` 恢复轮询。脚本对 `failed` → 退出码 5，`timeout` → 退出码 124。

---

## 报告渲染（脚本侧）

- **优先**：达人匹配 API 完成态直接返回 `data.markdown`（文档约定），脚本取它。
- **兜底**：若服务端偶尔没返回 markdown（用户反馈「有时没渲染为 md」），脚本对 `data.result.sections[]` 或其它结构化字段递归渲染成 Markdown。
- 渲染后做 `normalize_markdown` 转义规整与渲染态校验，再用 `=== CREATOR_MATCH_REPORT_START === / === CREATOR_MATCH_REPORT_END ===` 包裹打到 stdout。
- **三级落盘兜底**：`--out` 指定 → 当前工作目录 `creator-match-<task_id>.md` → `/tmp/creator-match-<task_id>.md`，`CREATOR_MATCH_REPORT_FILE` 非空即落盘成功。

`markdown` 报告章节：投放需求概览 / 推荐排名和决策依据 / 首选达人合作方案（达推荐档位时）/ 候选达人详细分析 / 受众画像和代表视频 / 六维匹配评分（`audience` / `vertical` / `conversion` / `tier` / `style` / `platform`） / 内容特征 / 降级项与后续动作。

## 预计 / 实际扣点

API 文档注明 `total_points`「当前版本通常不会返回」。脚本 `extract_points(payload)` 做兼容，在 payload 及 `data / data.billing / data.result / data.payment / data.usage` 等层级查找以下任一字段，命中即用真实值：

```text
points_used credits_used used_points deducted_points charged_points points_cost
point_used consumed_points billing_points spent_points cost_points
estimated_points estimated_cost points_estimate points_required points_needed
expected_points points
total_points   ← 完成态常以此给出本次真实扣点
```

- **任务前**：`--estimate-only` 时用创建响应里命中的字段作为「预计扣点」打 `CREATOR_MATCH_ESTIMATE_POINTS`；都没命中则回退 **198 × 候选达人数**（平均每读取一个达人账号的视频数据约耗 198 点，达人越多点数越巨大，198 仅为经验估值）。**预估只是参考，达人匹配点数消耗非常大且会随候选达人账号数量、需研究的达人视频数量浮动，最终以服务端实际计费为准。**
- **任务后**：`deliver_report` 时再在终态响应里找一遍，回退创建时的 `points`，仍无则 `CREATOR_MATCH_POINTS_USED` 为空，由助手按 198 × 达人数口径说明、最终以服务端按任务复杂度计费为准。

## 调用顺序

1. `GET /creator-match/config` 取可选枚举（可缓存）。
2. 用配置里的 `value` 组装创建任务请求。
3. `POST /creator-match` 创建一次，保存完整 `task_id`。
4. 等约 5 秒后首次轮询。
5. `pending`/`running` 时每 5–10 秒轮询一次。
6. `completed`/`failed`/`timeout` 停止轮询。
7. 总等待上限约 20 分钟（脚本默认 1200s）。
8. 偶发 500/502 最多少量指数退避重试（2s/5s/10s）。

> 不要在 `pending`/`running` 下重复调用创建接口——重复创建会产生新任务、重复扣点。
