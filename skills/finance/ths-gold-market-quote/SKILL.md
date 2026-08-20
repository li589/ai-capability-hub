---
name: ths-gold-market-quote
description: 调用同花顺 Fuyao single_trend 接口获取伦敦金现、银行积存金、AU9999 和 AUTD 黄金分时行情，并检查接口连通性。
disable-model-invocation: true
---

---
name: ths-gold-market-quote
description: 调用同花顺 Fuyao single_trend 接口获取伦敦金现、银行积存金、AU9999 和 AUTD 黄金分时行情，并检查接口连通性。
---

# 同花顺黄金行情获取

当用户要求获取、查询、对比或验证同花顺黄金行情，或提到伦敦金现、广发积存金、民生积存金、浙商积存金、AU9999、AUTD 时使用本 Skill。

## 接口

- URL：`https://quota-h.10jqka.com.cn/fuyao/common_hq_aggr/quote/v1/single_trend`
- Method：`POST`
- Content-Type：`application/json`
- X-Fuyao-Auth：`eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRob3JpemVyX25hbWVzcGFjZSI6ImNvbW1vbi1ocS1hZ2dyIiwibGljZW5zZWVfdHlwZSI6IkZST05UX0FQUCIsImxpY2Vuc2VlX25hbWVzcGFjZSI6Imh4a2xpbmUtR01UX2FpQnV5R29sZF9QYWdlIn0.gAC_QltNrfp6TXxZmW5ARTWfogjcO4qpVffmWskBeYw`

注意：令牌属于敏感凭据。不得在面向用户的正常回复、日志摘要或错误信息中重复展示完整令牌。若接口返回 401、403 或鉴权失败，说明令牌可能过期或授权范围变化，应请用户提供新令牌并更新本 Skill。

## 品种映射

| 名称 | market | code |
|---|---|---|
| 伦敦金现 | `218` | `AUUSDO` |
| 广发积存金 | `UAGM` | `GF001` |
| 民生积存金 | `UAGM` | `MS001` |
| 浙商积存金 | `UAGM` | `ZS001` |
| AU9999 | `81` | `AU9999` |
| AUTD | `81` | `AUTD` |

名称匹配时允许常见大小写差异，但发给接口的 `market` 和 `code` 必须严格使用表中的值。代码区分大小写，不得将 `GF001`、`MS001`、`ZS001`、`AU9999` 改成小写。

## 基础请求体

```json
{
  "code_list": [
    {"market": "218", "codes": ["AUUSDO"]}
  ],
  "trade_class": "intraday",
  "trade_date": 0
}
```

同一市场的多个代码应合并到同一个 `code_list` 项中，例如：

```json
{
  "code_list": [
    {"market": "218", "codes": ["AUUSDO"]},
    {"market": "UAGM", "codes": ["GF001", "MS001", "ZS001"]},
    {"market": "81", "codes": ["AU9999", "AUTD"]}
  ],
  "trade_class": "intraday",
  "trade_date": 0
}
```

## 行情字段

接口响应中的 `data_fields` 定义每一行 `value` 数组的字段顺序，必须按 `data_fields` 动态映射，禁止假定固定下标。

| 字段 ID | 含义 |
|---|---|
| `10` | 最新价 |
| `1` | 时间戳 |
| `6` | 昨收价 |
| `7` | 开盘价 |
| `8` | 最高价 |
| `9` | 最低价 |
| `13` | 成交量 |
| `11` | 收盘价 |
| `19` | 成交额 |
| `199112` | 涨跌幅 |
| `264648` | 涨跌额 |
| `1968584` | 换手率 |

未明确确认可选字段参数名时，不要擅自增加 `fields`、`field_list` 等参数；直接使用默认字段，并以服务端实际返回的 `data_fields` 为准。不同品种默认字段可能不同：银行积存金实测可返回 `1`、`10`、`13`，AU9999、AUTD 和伦敦金现通常还可能返回 `19`。

## 调用方式

优先使用 Python 标准库发起请求，避免在命令行参数、控制台输出和异常栈中泄露令牌。可执行如下脚本逻辑：

```python
import json
import urllib.request

URL = "https://quota-h.10jqka.com.cn/fuyao/common_hq_aggr/quote/v1/single_trend"
AUTH = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRob3JpemVyX25hbWVzcGFjZSI6ImNvbW1vbi1ocS1hZ2dyIiwibGljZW5zZWVfdHlwZSI6IkZST05UX0FQUCIsImxpY2Vuc2VlX25hbWVzcGFjZSI6Imh4a2xpbmUtR01UX2FpQnV5R29sZF9QYWdlIn0.gAC_QltNrfp6TXxZmW5ARTWfogjcO4qpVffmWskBeYw"

payload = {
    "code_list": [{"market": "218", "codes": ["AUUSDO"]}],
    "trade_class": "intraday",
    "trade_date": 0,
}

request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-Fuyao-Auth": AUTH},
    method="POST",
)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))
```

如果 WebFetch/WebSearch 无法访问该接口，不得用其他方式绕过其访问限制；但在允许访问内部业务接口的本地执行环境中，可以按用户授权通过标准 HTTP 客户端直接调用。

## 响应解析

成功响应的顶层结构通常为：

```json
{
  "status_code": 0,
  "data": {"quote_data": []},
  "status_msg": "ok"
}
```

处理规则：

1. HTTP 状态必须为 200。
2. JSON 必须可解析。
3. `status_code` 必须为 `0`；否则报告 `status_msg`，但不要输出认证令牌。
4. 遍历 `data.quote_data`。每个品种读取其 `market`、`code`、`delay`、`base_price`、`data_fields` 和 `value`。
5. 将每条 `value` 与 `data_fields` 用 `zip` 组合成字段对象。
6. 最新有效行情应从 `value` 尾部向前查找，选择字段 `10` 非空的最后一条，而不是盲目取最后一行。
7. 字段 `1` 是毫秒时间戳；展示时转换为用户本地时区，并同时保留原始时间戳以便排查。
8. `quote_data` 为空不等于网络不通。应区分“HTTP/鉴权成功但当前品种无数据”和“请求失败”。可能原因包括非交易时段、代码映射/大小写变化、权限范围或服务端暂无该品种数据。
9. 多品种批量请求可能只返回有数据的品种。输出时必须按请求清单补齐缺失品种，并标记为“本次未返回行情”。

推荐的动态解析代码：

```python
def parse_quote(item):
    fields = [str(x) for x in item.get("data_fields", [])]
    rows = [dict(zip(fields, row)) for row in item.get("value", [])]
    latest = next((row for row in reversed(rows) if row.get("10") is not None), None)
    return {
        "market": item.get("market"),
        "code": item.get("code"),
        "delay": item.get("delay"),
        "base_price": item.get("base_price"),
        "latest": latest,
        "point_count": len(rows),
    }
```

## 连通性验证

当用户要求验证连通性时，至少测试伦敦金现 `218/AUUSDO`，并报告：测试时间、HTTP 状态、JSON 是否有效、业务 `status_code`、`status_msg`、返回品种、点数、最新有效时间和最新价。需要全面验证时，再逐个测试全部六个映射，避免批量请求掩盖单个品种缺失。

最新映射更新验证结果（2026-08-10，Asia/Shanghai）：接口 HTTP 200，业务 `status_code=0`、`status_msg=ok`；`UAGM/GF001`、`UAGM/MS001`、`UAGM/ZS001`、`81/AU9999` 均成功返回对应品种的分时数据，返回的 market 和 code 与请求一致。这只是更新时基线，后续使用必须重新实时验证，不可将当时价格当成当前行情。

## 输出要求

用户只查询行情时，用简洁中文输出品种名称、代码、行情时间、最新价、成交量、成交额、是否延迟；服务端未返回的字段写“未返回”，不要自行推算。用户要求原始数据时可以给经过脱敏和适度截断的 JSON，但不得包含请求头中的完整认证令牌。用户要求对比时统一时间戳和单位，并明确不同市场品种可能存在报价口径差异。

