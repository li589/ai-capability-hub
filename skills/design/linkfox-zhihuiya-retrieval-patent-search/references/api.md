# 智慧芽-检索式专利检索 API 参考

## 调用规范

- **请求地址**：`${LINKFOX_TOOL_GATEWAY}/zhihuiya/querySearchPatent`
- **请求方式**：POST，Content-Type: application/json
- **认证方式**：Header `Authorization: <api_key>`，api_key 从环境变量 `LINKFOX_AGENT_API_KEY` 或 `LINKFOXAGENT_API_KEY` 读取（如未配置 按 SKILL.md 的 **## 解决认证和积分问题** 处理）
- **User-Agent**：`LinkFox-Skill/2.0`，超时 150s（与脚本一致），透传 `SESSION_ID` / `MODE_ID` / `APP_NAME`

## 请求参数

POST Body（JSON）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| queryText | string | 是 | Analytics 检索式，最大 12000 字符。支持字段前缀语法（如 `TACD:`、`TAC:`、`TA:`）与布尔运算（`AND`/`OR`/`NOT`）。 |
| limit | integer | 否 | 返回专利个数，范围 1–1000，默认 10 |
| offset | integer | 否 | 偏移量，范围 0–19999，默认 0；`limit + offset` 不能超过 20000 |
| sort | array | 否 | 排序条件数组，每个元素 `{field, order}`。`field` 取 `PBDT_YEARMONTHDAY`/`APD_YEARMONTHDAY`/`ISD`/`SCORE`；`order` 取 `DESC`/`ASC` |
| stemming | integer | 否 | 是否开启截词检索：`1` 开启 / `0` 关闭，默认关闭 |
| collapseType | string | 否 | 专利去重条件，不传默认 `ALL`。取值：`ALL`（不去重）、`APNO`（按申请号去重）、`DOCDB`（按简单同族去重）、`INPADOC`（按 INPADOC 同族去重）、`EXTEND`（按 Patsnap 同族去重） |
| collapseBy | string | 否 | 专利去重排序字段：`APD`（申请日）/`PBD`（公开日）/`AUTHORITY`（受理局）/`SCORE`（相关性） |
| collapseOrder | string | 否 | 专利去重排序顺序：`OLDEST`（最早）/`LATEST`（最新） |
| collapseOrderAuthority | array | 否 | 受理局优先级数组（仅当 `collapseBy=AUTHORITY` 时有效），按输入顺序的受理局优先级保留对应专利 |

> `queryText` 为必填项；缺失时网关返回 `errcode: 400, errmsg: "queryText 为必填项"`。

> **检索式示例**：`TACD: virtual reality`（在标题/摘要/权利要求/说明书中检索 "virtual reality"）；`TAC: drone AND camera`（标题/摘要/权利要求中同时包含 drone 与 camera）。

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| errcode | integer | 200 表示成功 |
| errmsg | string | `ok` 表示成功，否则为错误描述 |
| total | integer | 本次返回结果数 |
| data | array | 专利列表 |
| columns | array | 渲染的列（仅渲染元信息，非数据记录，长度可能与 `data` 不一致） |
| type | string | 渲染的样式（如 `tableListWorkbenches`） |
| costToken | integer | 消耗token |
| allRecordsCount | integer | 检索命中总数 |

### 数据字段（`data` 数组中的每个对象）

| 字段 | 类型 | 说明 |
|------|------|------|
| patentId | string | 智慧芽专利 ID |
| pn | string | 公开（公告）号 |
| title | string | 专利标题 |
| apdt | integer | 申请日（YYYYMMDD） |
| pbdt | integer | 公开日（YYYYMMDD） |
| apno | string | 申请号 |
| authority | string | 受理局（如 `US`） |
| inventor | string | 发明人（多人以 `\|` 分隔） |
| originalAssignee | string | 原始申请人（多个以 `\|` 分隔） |
| currentAssignee | string | 当前申请人（多个以 `\|` 分隔） |

> `columns` 顶层字段为渲染元信息，不应作为数据列表使用。如需某条专利的完整著录/全文/法律状态等，请用返回的 `patentId` 或 `pn` 调用对应的 `linkfox-zhihuiya-bibliography` / `linkfox-zhihuiya-simple-bibliography` 等技能。

## 错误码

正常情况下，接口的 HTTP 状态码均为 200，业务的成功与否通过响应体中的 errcode 字段区分（errcode = 200 表示成功，其他值表示业务错误）。当遇到未授权等情况时，HTTP 状态码为 401，且对应的 errcode 也是 401。

| errcode | 含义 | 处理建议 |
|---------|------|----------|
| 200 | 成功 | 正常解析 `data`、`allRecordsCount` 等业务字段 |
| 400 | 参数错误 | 检查 `queryText` 是否提供、`limit`/`offset` 范围是否合法 |
| 401 | 认证失败 | HTTP 401 或 authorized error：按 SKILL.md 的 **## 解决认证和积分问题** 处理 |
| 402 | 积分不足 | HTTP 402：按 SKILL.md 的 **## 解决认证和积分问题** 处理 |
| 501 | 无权限或套餐配额耗尽 | `errmsg` 含 "No permission or API package quota has exceeded the limit"：当前 Key 未开通检索式检索专利权限或配额已用尽。属权限/套餐问题（非单纯余额不足），**充值无法解决**，**不要重试**，提示用户开通/启用检索式检索专利 API 套餐后重试 |
| 其他非200值 | 业务异常 | 参考 `errmsg` 字段获取具体错误原因 |

错误响应示例：

```json
// 缺少 queryText
{"errcode": 400, "errmsg": "queryText 为必填项"}

// 无权限 / 配额耗尽
{"errcode": 501, "errmsg": "检索式检索专利失败: No permission or API package quota has exceeded the limit!"}
```

## curl 示例

**基础检索式检索：**

```bash
curl -X POST ${LINKFOX_TOOL_GATEWAY}/zhihuiya/querySearchPatent \
  -H "Authorization: $LINKFOX_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"queryText": "TACD: virtual reality", "limit": 10}'
```

**按相关性排序：**

```bash
curl -X POST ${LINKFOX_TOOL_GATEWAY}/zhihuiya/querySearchPatent \
  -H "Authorization: $LINKFOX_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"queryText": "TACD: drone AND camera", "sort": [{"field": "SCORE", "order": "DESC"}]}'
```

**分页 + 简单同族去重：**

```bash
curl -X POST ${LINKFOX_TOOL_GATEWAY}/zhihuiya/querySearchPatent \
  -H "Authorization: $LINKFOX_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"queryText": "TACD: virtual reality", "offset": 10, "limit": 10, "collapseType": "DOCDB", "collapseBy": "APD", "collapseOrder": "LATEST"}'
```

---

## Feedback API

> This endpoint is **separate** from the tool API above. Do not mix the two base URLs.

- **POST** `https://skill-api.linkfox.com/api/v1/public/feedback`
- **Content-Type:** `application/json`

```json
{
  "skillName": "linkfox-zhihuiya-retrieval-patent-search",
  "sentiment": "POSITIVE",
  "category": "OTHER",
  "content": "Results were accurate, user was satisfied."
}
```

**Field rules:**
- `skillName`: Use this skill's `name` from the YAML frontmatter
- `sentiment`: Choose ONE — `POSITIVE` (praise), `NEUTRAL` (suggestion without emotion), `NEGATIVE` (complaint or error)
- `category`: Choose ONE — `BUG` (malfunction or wrong data), `COMPLAINT` (user dissatisfaction), `SUGGESTION` (improvement idea), `OTHER`
- `content`: Include what the user said or intended, what actually happened, and why it is a problem or praise
