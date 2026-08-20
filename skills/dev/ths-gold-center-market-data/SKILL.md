---
name: ths-gold-center-market-data
description: 通过受限 external API
  直接获取同花顺黄金数据中心的利率概率、美债实际利率、期限利差、恐慌指数、CME持仓、伦敦金库持有量、季节性、黄金储备和ETF资金数据。供 Agent
  执行黄金宏观与资金面数据查询时使用。
disable-model-invocation: true
---

---
name: ths-gold-center-market-data
description: 通过受限 external API 直接获取同花顺黄金数据中心的利率概率、美债实际利率、期限利差、恐慌指数、CME持仓、伦敦金库持有量、季节性、黄金储备和ETF资金数据。供 Agent 执行黄金宏观与资金面数据查询时使用。
---

# 同花顺黄金数据中心行情数据

本 Skill 供 Agent 直接调用黄金数据中心接口。收到查询任务后，根据用户指定的指标选择接口、发起请求、解析实时返回并输出结果。不要展示内部接口选择过程，也不要把历史示例数据当成当前数据。

## 服务地址

生产环境：`http://jcj.thsi.cn/jcj_data_detail`

测试环境：`http://testm.10jqka.com.cn/jcj/jcj_data_detail`

默认使用生产环境。所有请求必须走 `/external/api/` 对外安全路由，并携带请求头 `X-Token: 10jqka`。请求和响应均按 JSON 处理。禁止回退到旧路由；若返回 401 或 403，停止重试并报告权限问题。

## 可查询数据

| 查询项 | 方法 | 路径 |
|---|---|---|
| 美联储议息会议降息概率 | GET | `/external/api/gold_center/ifind/v1/fed_interest_rate` |
| 10Y 美债实际利率 VS 伦敦金 | GET | `/external/api/gold_center/ifind/v1/real_yield` |
| 10Y-2Y 美债期限利差 VS 伦敦金 | GET | `/external/api/gold_center/ifind/v1/term_spread` |
| 恐慌指数（日度） | GET | `/external/api/gold_center/ifind/v1/fear_index` |
| CME 资产管理机构多空头持仓（周度） | GET | `/external/api/gold_center/ifind/v1/cme_position` |
| 伦敦金库黄金持有量（月度） | GET | `/external/api/gold_center/ifind/v1/london_gold_reserve` |
| 金价波动季节性表格 | GET | `/external/api/gold_center/fund/v1/seasonality_table` |
| 金价波动季节性图表 | GET | `/external/api/gold_center/fund/v1/seasonality_line` |
| 黄金储备榜单 | POST | `/external/api/gold_center/fund/v1/gold_reserve_rank` |
| 全球或中国黄金储备 | POST | `/external/api/gold_center/fund/v1/gold_reserve` |
| 黄金 ETF 聪明资金 | POST | `/external/api/gold_center/fund/v1/etf_capital` |

支持中文名称及常见简称，例如“降息概率”“实际利率”“期限利差”“VIX/恐慌指数”“CME 多空”“伦敦金库存”“黄金季节性”“黄金储备”“ETF 资金”。用户未指定指标时，先询问要查询的数据；用户明确要求全部或整体行情时才请求全部接口。

## 执行原则

优先直接执行，不要为已有默认值的参数向用户提问。只有用户要求非默认口径且缺少必要参数时才澄清。全球和中国黄金储备的指标 ID 已内置；用户同时查询两者时，必须并发发起两个请求，不得先查全球再询问中国 ID。

同一请求最多执行两次：第一次使用本 Skill 中的准确参数；只有网络超时或 5xx 时才重试一次。业务参数错误、401、403 或明确的非零业务码不进行多种字段名试探，直接报告错误。禁止依次尝试 JSON、query、form 或不同参数拼写。

## 默认参数

所有 GET 接口无请求体、无业务参数，直接调用。

| 查询项 | 默认参数 |
|---|---|
| 美联储降息概率、实际利率、期限利差、恐慌指数、CME 持仓、伦敦金库存、季节性 | 无 |
| 黄金储备榜单 | `type=up`、`time_type=year`、`limit=5`、`global=0` |
| 全球黄金储备 | `index_id=S017537657`、`type=all`、`before=2` |
| 中国黄金储备 | `index_id=S003140577`、`type=all`、`before=2` |
| 黄金 ETF 聪明资金 | `market_type=cn`、`before=10`、`intervals=[3,5,10,20]`、`tab=au` |

## 请求参数

### 黄金储备榜单

```json
{
  "type": "up",
  "time_type": "year",
  "limit": 5,
  "global": "0"
}
```

`limit` 必须为正整数。已知 `time_type` 默认使用 `year`，`type` 默认使用 `up`。其他取值没有完整定义，用户要求不同榜单口径且无法确定参数时，应先确认，不要猜测。

### 全球或中国黄金储备

接口实际接收的字段名是 `index_id`，必须使用下划线形式，禁止使用 `indexId`。

全球黄金储备默认请求：

```json
{
  "index_id": "S017537657",
  "type": "all",
  "before": 2
}
```

中国黄金储备默认请求：

```json
{
  "index_id": "S003140577",
  "type": "all",
  "before": 2
}
```

`type` 支持 `all`（全量储备数据）和 `up`（每期增持数据）；`before` 是历史年份，必须为正整数。用户只说“最新全球及中国黄金储备”时，直接并发使用以上两组默认请求。默认返回全量储备；只有用户明确要求“增持、变化、环比增量”时才使用 `type=up`。

### 黄金 ETF 聪明资金

```json
{
  "market_type": "cn",
  "before": 10,
  "intervals": [3, 5, 10, 20],
  "tab": "au"
}
```

`market_type` 使用 `cn` 或 `us`；`before` 为最近天数；`intervals` 为净流入统计周期；`tab=au` 表示黄金，`tab=ag` 表示白银。本 Skill 查询黄金时默认使用 `au`。

## 调用代码

优先使用 Python 标准库直接请求。GET 不发送 body，POST 使用 JSON body。

```python
import json
import urllib.request

BASE_URL = "http://jcj.thsi.cn/jcj_data_detail"


def request_json(path, method="GET", payload=None, timeout=10):
    if not path.startswith("/external/api/gold_center/"):
        raise ValueError("仅允许调用黄金数据中心 external API")

    body = None
    headers = {
        "Accept": "application/json",
        "X-Token": "10jqka",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))
```

查询多个指标时并发请求，并发数最多为 4。每个接口独立记录成功、失败和耗时；单个接口失败不能丢弃其他成功结果。全球与中国黄金储备属于同一用户意图时，固定并发调用，两项均使用 JSON body，不做传参形式探测。每次请求都必须包含 `X-Token: 10jqka`；不得在普通用户回复中重复展示该请求头值。

## 通用响应校验

HTTP 状态必须为 200，响应必须是有效 JSON。业务状态兼容两种包装：优先读取 `status_code/status_msg`，不存在时读取 `code/msg`；数字 `0` 和字符串 `"0"` 均表示成功。

业务状态非 0 时，返回接口名称和业务消息，不继续解析该项。`data` 缺失或为空时标记“暂无有效数据”。遇到未知结构时保留原始结构摘要并报告解析失败，不凭字段名猜测。

数值单位未明确时只展示原值，不补写单位。日期按接口原值展示，并区分数据日期与请求时间。接口结果只能用于数据说明，不直接输出买入、卖出等投资建议。

## 解析规则

### 美联储降息概率

读取 `data.list[]`。每个会议包含 `meeting_date` 和 `items[]`，区间项包含 `rate_range`、`probability`，可能包含 `is_in_range`。

将概率小数转换为百分比，同时保留原值，例如 `0.37700000` 展示为 `37.70%`。按会议日期分组，每组按概率降序排列。没有 `is_in_range` 时不要推断当前利率所在区间。

### 宏观指标、持仓和库存

实际利率、期限利差、恐慌指数、CME 持仓、伦敦金库持有量均读取 `data.metrics[]`。每项通常为：

```json
{
  "metrics_name": "指标名称",
  "metrics_data": {
    "time": ["2026-05-20"],
    "value": ["1.23"]
  }
}
```

将 `time` 和 `value` 按索引配对。两者长度不一致时，仅使用共同长度，并报告未配对数量。保留接口返回的所有指标序列，包括伦敦金对照序列，不要只读取第一项。

### 季节性数据

两个季节性接口可能返回以下任一结构：

- `time_range + indexes + data`
- `total + indexes + data + part_order_code_list`

必须按运行时字段识别结构，不要根据接口名称固定解析器。保留 `code`、`idx`、`values` 等字段。若 `value` 是 JSON 字符串，尝试再次解析；失败则保留原字符串。数字时间戳转换为日期时，同时保留原始时间戳。

### 黄金储备榜单

结果列表可能直接位于 `data`，也可能位于 `data.list`，两种形式都要兼容。列表项常见字段为 `name`、`index_id`、`value`、`start`、`end`、`update_time`。字段为 null 时展示“暂无”。默认保持服务端顺序。

### 全球或中国黄金储备

读取 `data.time_range`、`data.values`、`data.update_time`，将日期和值按索引配对。接口按最新到最旧返回，最新一期取配对后的第一项；仍应校验日期顺序，不能无条件假定。长度不一致时仅使用共同长度并报告。`type=all` 表示全量储备序列，`type=up` 表示增持序列。

默认指标映射：全球为 `S017537657`，中国为 `S003140577`。同时查询时输出两者最新值、上一期值、绝对变化和环比变化率。绝对变化应使用本次 `all` 序列中最新值减上一期值计算；需要核对时可再调用 `type=up`，但正常查询无需额外请求。接口未明确单位时不得擅自补充单位。

### 黄金 ETF 聪明资金

读取 `data.indic_data`、`data.intervals`、`data.interval_data`。`indic_data` 是以日期为键的对象，按日期排序；值通常为数值数组。将 `intervals` 与 `interval_data` 按索引配对。正值标记为净流入，负值标记为净流出，但不扩展成交易建议。

## 输出要求

单指标查询先输出最近一期数据，包括数据名称、最近日期、最新值或核心结果、数据点数；用户要求时再展开历史序列。

多指标查询使用紧凑汇总，包含数据名称、请求状态、最近数据日期、最新值或摘要、数据点数。全部查询按“利率与风险、机构持仓与库存、季节性、储备与 ETF 资金”分组。

用户要求原始数据时返回结构化 JSON；数据量较大时保存完整数据文件，并在回复中只给摘要。涉及概率时同时输出小数和百分比；科学计数法可增加易读格式，但必须保留原值。

## 性能与失败处理

直接使用已确认的默认参数发起一次请求。单接口超时设为 10 秒；批量查询并发执行，总等待时间不应因接口数量线性增长。网络超时、连接重置或 HTTP 5xx 可原参数重试一次；其他错误不重试。

安全约束：请求路径必须以 `/external/api/gold_center/` 开头，请求头必须包含 `X-Token`。不允许调用旧的 open 路由，不允许在 external 失败后降级到其他路由，也不允许把 Token 放入 URL、query 参数、日志或用户输出。

不要为了探索接口而连续尝试不同字段名、Content-Type 或 query/form/body 传参。若业务返回“参数为空”，先检查本 Skill 的准确字段拼写；黄金储备字段固定为 `index_id`。除非用户要求诊断，否则不要保存完整响应文件，只在内存中解析并输出摘要。

## 兼容性要求

执行时必须兼容：`status_code/status_msg` 与 `code/msg`；榜单的 `data[]` 与 `data.list[]`；ETF 的动态日期键；季节性数据的两类结构；宏观 `metrics[]` 中的对象结构。

不要在用户输出中讨论接口资料来源、内部编号或结构差异的历史原因。只有运行时解析失败或用户要求非默认口径且参数不足时，才简洁说明问题并请求必要信息。

