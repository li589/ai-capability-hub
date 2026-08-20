---
name: "ths-gold-center-score"
description: "通过 external 接口和 X-Token 查询同花顺黄金数据中心评分及相关指标，支持单项、默认三项和全部指标查询。"
---

---
name: ths-gold-center-score
description: 通过 external 接口和 X-Token 查询同花顺黄金数据中心评分及相关指标，支持单项、默认三项和全部指标查询。
---

# 同花顺黄金数据中心评分

当用户要求获取、查询、汇总或对比“黄金数据中心评分”“黄金指标评分”，或者提到下列任一评分指标时使用本 Skill。

## 接口规范

所有黄金数据中心请求统一使用以下基础路径：

`http://jcj.thsi.cn/jcj_data_detail/external/api/gold_center/`

所有请求统一携带：

- `Content-Type: application/json`
- `X-Token: 10jqka`

评分接口：

- URL：`http://jcj.thsi.cn/jcj_data_detail/external/api/gold_center/comment/v1/latest`
- Method：`POST`

ETF 资金接口：

- URL：`http://jcj.thsi.cn/jcj_data_detail/external/api/gold_center/fund/v1/etf_capital`
- Method：`POST`

正常日志和用户输出不主动展示完整 Token；仅说明请求已携带鉴权头。调用其他黄金数据中心接口时，必须继续使用相同的 external 基础路径和鉴权请求头，并遵循该接口自身的 Method 与参数契约。

## 评分指标映射

| biz | 中文名称 |
|---|---|
| `market_trend` | 大盘趋势 |
| `main_force` | 黄金主力动向 |
| `smart_metrics` | 聪明指标 |
| `cn_gold_reserve` | 中国黄金储备 |
| `etf_capital` | 黄金ETF聪明资金 |
| `global_gold_reserve` | 全球黄金储备 |
| `london_gold_reserve` | 伦敦金库黄金持有量 |
| `cme_position` | CME资产管理机构多空头持仓对比 |
| `gold_spread` | 黄金价差 |
| `gold_oil_ratio` | 金油比 |
| `seasonality_regulation` | 金价季节性规律 |
| `fear_index` | 恐慌指数 |
| `gold_silver_ratio` | 金银比 |
| `term_spread` | 期限利差 VS 伦敦金 |
| `real_yield` | 10Y美债实际利率 VS 伦敦金 |
| `fed_interest_rate` | 加息概率 |

匹配用户输入时支持中文名称、biz 原值及常见无空格表达。发给接口时必须使用表中的 biz 原值。

## 评分查询模式

### 默认查询

如果用户仅说“查询黄金数据中心评分”“获取黄金评分”等，没有明确指定指标，也没有说“全部”或“整体”，默认查询大盘趋势、黄金主力动向和聪明指标：

```json
{
  "biz_list": ["market_trend", "main_force", "smart_metrics"]
}
```

### 单独查询

如果用户指定一个或多个指标，只查询指定项。例如查询“加息概率”：

```json
{
  "biz_list": ["fed_interest_rate"]
}
```

`biz_list` 必须是字符串数组。即使只查一个指标，也不能传字符串。若用户给出无法识别的指标名称，不要猜测最相近项；列出支持的指标并请用户确认。

### 整体查询

如果用户说“整体查询”“全部查询”“查询所有指标”“完整评分”等，查询全部 16 项：

```json
{
  "biz_list": [
    "market_trend",
    "main_force",
    "smart_metrics",
    "cn_gold_reserve",
    "etf_capital",
    "global_gold_reserve",
    "london_gold_reserve",
    "cme_position",
    "gold_spread",
    "gold_oil_ratio",
    "seasonality_regulation",
    "fear_index",
    "gold_silver_ratio",
    "term_spread",
    "real_yield",
    "fed_interest_rate"
  ]
}
```

## 评分接口调用参考

```python
import json
import urllib.request

URL = "http://jcj.thsi.cn/jcj_data_detail/external/api/gold_center/comment/v1/latest"

payload = {
    "biz_list": ["market_trend", "main_force", "smart_metrics"]
}

request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "X-Token": "10jqka",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    http_status = response.status
    result = json.loads(response.read().decode("utf-8"))
```

## ETF 资金接口调用

ETF 请求体使用 `market_type`，不能使用驼峰形式。已确认参数如下：

- `market_type`：`cn` 表示中国，`us` 表示美国。
- `tab`：当前使用字符串 `"1"`。
- `before`：正整数，表示需要返回的历史记录数量；例如 `1`、`7`、`30`。

中国市场七条数据请求：

```json
{
  "market_type": "cn",
  "tab": "1",
  "before": 7
}
```

完整调用参考：

```python
import json
import urllib.request

URL = "http://jcj.thsi.cn/jcj_data_detail/external/api/gold_center/fund/v1/etf_capital"
payload = {
    "market_type": "cn",
    "tab": "1",
    "before": 7,
}
request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "X-Token": "10jqka",
    },
    method="POST",
)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))
```

ETF 成功响应的 `data` 通常包含：

- `indic_data`：日期到指标数组的映射。
- `intervals`：区间信息，可能为 null。
- `interval_data`：区间数据，可能为 null。

## 评分响应结构

成功响应示例结构：

```json
{
  "status_code": 0,
  "status_msg": "ok",
  "data": [
    {
      "biz": "market_trend",
      "comment": "评论内容",
      "comment_date": "2026-08-10 10:31:34",
      "id": 1562,
      "score": 8.1,
      "title": "标题"
    }
  ]
}
```

字段含义：`status_code` 为业务响应码，`status_msg` 为响应状态，`data` 为评分列表；列表项中的 `biz` 是业务标识，`comment` 是评论内容，`comment_date` 是评论日期，`id` 是主键，`score` 是 0–10 分的评分，`title` 是评论标题。

## 安全与结果校验

每次请求必须同时校验传输层、鉴权层、业务层和数据层：

1. 确认最终 URL 位于 `/external/api/gold_center/`。
2. 确认请求携带 `X-Token`，但正常日志不得打印完整值。
3. HTTP 状态必须为 200。HTTP 401 通常表示鉴权头缺失或无效。
4. 响应必须为有效 JSON。
5. 顶层 `status_code` 必须为数字或可转数字的 `0`；否则报告 `status_msg` 并停止解析。部分参数错误仍可能使用 HTTP 200，因此不能只检查 HTTP 状态。
6. 评分接口的 `data` 成功时应为数组。若为 null 或其他类型，标记为无有效评分数据。
7. 按 `biz` 建立响应索引，再按照请求的 `biz_list` 顺序输出，不能依赖服务端返回顺序。
8. 如果某个请求指标未出现在 `data` 中，应保留该指标并标记“本次未返回”，不能静默遗漏。
9. `score` 必须是 0–10 范围内的有效数字。超出范围或类型异常时标记为无效数据，不纳入均值、最高分和最低分计算。
10. `comment` 或 `title` 可能为空字符串、JSON null，或者字符串字面值 `"null"`，统一展示为“暂无”。
11. `comment_date` 按接口返回值展示，并明确为数据更新时间；不要把接口评论当作当前实时行情。
12. 整体查询应核对 16 个预期 biz。返回数量不等于 16 或出现未知 biz 时，需要明确列出缺失项或异常项。
13. ETF 接口应检查 `data.indic_data` 是否为非空对象，并核对返回记录数不超过 `before`。日期键应可按 `YYYY-MM-DD` 解析，指标数组中的值应为有效数字。
14. 评分和评论是数据源结论，不得在没有额外证据时改写为确定性的投资建议。

推荐评分清洗逻辑：

```python
def normalize_text(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    return text

requested = payload["biz_list"]
rows = result.get("data") or []
by_biz = {row.get("biz"): row for row in rows if isinstance(row, dict)}
normalized = []
for biz in requested:
    row = by_biz.get(biz)
    if not row:
        normalized.append({"biz": biz, "returned": False})
        continue
    score = row.get("score")
    score_valid = isinstance(score, (int, float)) and not isinstance(score, bool) and 0 <= score <= 10
    normalized.append({
        "biz": biz,
        "returned": True,
        "id": row.get("id"),
        "score": score if score_valid else None,
        "score_valid": score_valid,
        "title": normalize_text(row.get("title")),
        "comment": normalize_text(row.get("comment")),
        "comment_date": row.get("comment_date"),
    })
```

## 输出规范

默认或单项评分查询时，优先用简洁中文逐项展示：中文名称、评分（x/10）、更新时间、标题、评论。标题或评论为空时写“暂无”。

整体评分查询时，先展示全部 16 项的紧凑评分结果，再给出最高分、最低分和整体均分。均分只能基于本次实际返回且 `score` 为有效数字的项目计算，同时注明有效项目数。若用户只要求原始结果，则直接返回清洗后的结构化 JSON，不做额外分析。

ETF 查询时，按日期升序展示资金值，明确市场类型和返回记录数；未经接口文档确认，不擅自转换单位。若用户同时查询中美市场，应分别展示并避免直接相加。

可按以下区间为评分添加纯展示性标签：8.0–10.0 为偏强，6.0–7.9 为中性偏强，4.0–5.9 为中性偏弱，0–3.9 为偏弱。必须说明这是 Skill 的展示规则，不是接口字段；不得把标签直接表述为买入或卖出建议。

## 验证基线

2026-08-10（Asia/Shanghai）完成实际验证：

- 评分接口携带鉴权头时，HTTP 200、`status_code=0`、`status_msg=ok`；默认查询返回 3 项，整体查询返回全部 16 项。
- ETF 资金接口携带鉴权头且请求体为 `market_type`、`tab`、`before` 时，HTTP 200、`status_code=0`、`status_msg=ok`。
- ETF 的 `market_type=cn` 与 `market_type=us` 均可返回有效 `indic_data`；`before=1`、`7`、`30` 均已验证可用。
- 缺失或无效鉴权头时请求会被拒绝。

以上仅为创建和更新时的连接基线。每次用户实际查询都必须重新请求并执行完整结果校验。

