---
name: etf-filter
description: 查询/筛选场内ETF基金，当用户询问"筛选/推荐某类ETF""低估值行业ETF""规模最大的宽基ETF""近1月涨幅超10%的ETF""沪深300/中证500/恒生科技/纳斯达克/半导体/红利/科技ETF有哪些""高股息/低费率/可T0交易的ETF"等场内ETF筛选相关问题时，使用此
  skill。
version: 1.0.0
author: Ping An Securities
display_name: 平安证券 ETF 筛选
display_name_en: Ping An ETF Filter
description_zh: 按分类、主题、跟踪指数、估值、规模、费率、流动性、收益和标签筛选场内 ETF。
description_en: Screen listed ETFs by category, theme, index, valuation, scale,
  fee, liquidity, return, and tags.
visibility: public
disable-model-invocation: true
---

# ETF 筛选 Skill

## 这个 Skill 做什么

查询/筛选场内ETF基金，覆盖按分类（宽基/行业/债券/风格/跨境等）、估值（PE/PB及历史分位）、涨跌幅（近5/20/60/120日、今年以来、近一年）、规模、流动性、费率、股息率、ROE、RSI、资金流向等维度的组合筛选，以及可T0交易/可融资融券/互联互通/指数增强等标签筛选。

#### 任何时候都应该用这个 skill 实际查询，不要依赖训练知识回答ETF代码、行情、规模、估值分位等具体数字。

## 环境准备

- 检查是否已经设置环境变量 `PINGAN_SKILL_APIKEY`（用于鉴权用的 API Key），如未设置，提示用户登录平安证券skill开放平台获取 https://stock.pingan.com/huodong/aiskill/skillPage/index.html
- 依赖 Python 库 `requests`。

## 基本调用格式

```bash
python scripts/get_data.py --payload '<请求体JSON>'
```

`<请求体JSON>` 直接对应下方「请求体结构」，自己按需拼 `wheres`/`fields`/`orderBy`/`orderType`。


---

## 请求体结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `wheres` | Array | 否 | 筛选条件列表，数组内条件为 **AND** 关系，见下方字段/操作符说明 |
| `fields` | String | 是 | 返回字段，逗号分隔，例如 `code,etfName,fundCompany,fundType1,fundType2,indexName, scope, cost, pe,pb` |
| `orderBy` | String | 否 | 排序字段名 |
| `orderType` | String | 否 | 排序方式：`A` 升序 / `D` 降序 |
| `pageSize` | Int | 否 | 返回数量，正整数 |

`wheres` 里每一项结构为：

```json
{"field": "字段名", "type": "操作符编号", "value": "条件值"}
```

### 常用字段映射表

百分比类字段（分位、涨跌幅、ROE、费率、股息率、规模增幅等）的 `value` 按小数格式填写，如 `0.2` 表示 20%，不要写成 `20`。
对于`pe` / `pb`/`scopeIncreaseM` / `scopeIncrease3M` /`yielD`字段，传原始值，不用除以100，例如用户说`5%`或`5`，都传`5`,不要除以100。

| 字段名 | 中文说明 | 类型 | 说明 |
|---|---|---|---|
| `code` | 基金代码 | 字符串 | 需带市场前缀，格式为 `SH`/`SZ` + 6位数字，如沪深300ETF（华泰柏瑞）代码为 `SH510300`，不要只传 `510300` |
| `etfName` / `etfName1` | 产品简称 / 全称 | 字符串 | 当用户未明确说明查简称全称时，优先用简称`etfName`,搭配`type:7` 模糊匹配|
| `fundCompany` | 基金公司 | 字符串 | — |
| `fundType1` | 一级分类 | 字符串 | 规模宽基、行业主题、风格策略、全球市场、债券资产、商品资产、货币基金，要严格用枚举值，没有枚举值映射的时候，type要为7，进行模糊匹配|
| `fundType2` | 二级分类 | 字符串 | 细分类型，见文末「参考字典」，要严格用枚举值，优先用`type:7` LIKE 进行模糊匹配|
| `indexName` | 指数名称 | 字符串 | 跟踪指数，一般用 `type:7` LIKE |
| `indexCode` | 指数代码 | 字符串 | 需带市场前缀，格式为 `SH`/`SZ` + 6位数字，如沪深300指数代码为 `SH000300`，不要只传 `000300` |
| `dayRise5` / `dayRise20` / `dayRise60` / `dayRise120` | 近5/20/60/120日涨幅 | 数字 | 传小数（如20%传0.2） |
| `thisYearRise` | 今年以来涨幅 | 数字 | 传小数（如20%传0.2） |
| `oneYearRise` | 近一年涨跌幅 | 数字 | 传小数（如20%传0.2） |
| `pe` / `pb` | PE（市盈率）/ PB（市净率） | 数字 | 传百分数值，用户说`0.6%` 或`0.6`都传`0.6`，不要除以100 |
| `peFenWei` / `pbFenWei` | PE百分位 / PB百分位 | 数字 | 传小数（如20%传0.2） |
| `roe` | ROE | 数字 | 传小数（如20%传0.2） |
| `rsi` | RSI(N=6) | 数字 | 保留两位小数 |
| `scope` | 规模 | 数字 | 单位：元，如 5亿传 `500000000` |
| `foldingPremiunRates` | 折溢价率 | 数字 | 传小数（如1%传0.01） |
| `fundScale` | 规模最大标签 | 字符串 | value传`1`，配 `type:5` |
| `fundTarrif` | 费用最低标签 | 字符串 | value传`1`，配 `type:5` |
| `t0Trade` | 可T0交易标签 | 字符串 | value传`1`，配 `type:5` |
| `fundLoan` | 可融资融券标签 | 字符串 | value传`1`，配 `type:5` |
| `northBond` | 互联互通标签 | 字符串 | value传`1`，配 `type:5` |
| `lowValuation` | 估值低位标签 | 字符串 | value传`1`，配 `type:5` |
| `indexEnhance` | 指数增强标签 | 字符串 | value传`1`，配 `type:5` |
| `cost` | 费用 | 数字 | 托管费+管理费，传小数（如0.15%传0.0015） |
| `turnVolume20` | 近20日成交额 | 数字 | 单位：元 |
| `buy1W` | 近1周买入人数 | 数字 | — |
| `search1W` | 近1周搜索人数 | 数字 | — |
| `favoriteNum` | 自选人数 | 数字 | — |
| `scopeIncreaseM` / `scopeIncrease3M` | 近1月/3月规模增幅 | 数字 | 传百分数值，用户说`6%` 或`6`都传`6`，不要除以100 |
| `fundshareChangeM` / `fundshareChangeW` | 近一月/一周净申购份额 | 数字 | — |
| `marginFlowinM` | 近一月融资余额净增量 | 数字 | — |
| `yielD` | 股息率 | 数字 | 传百分数值，用户说`6%` 或`6`都传`6`，不要除以100 |
| `dividedNoSum` | 历史累计分红次数 | 数字 | — |
| `dividedNoThisYear` | 近1年分红次数 | 数字 | — |
| `upDayCnt` / `downDayCnt` | 连涨/连跌天数 | 数字 | — |
| `highestDay` | 创新高天数 | 数字 | — |
| `rank` | 排序用 |  数字 | 排名用 |

### 操作符（`type`）映射表

| 类型值 | 含义 | 说明 |
|:---:|---|---|
| `0` | `=`（等于） | 数值比较 |
| `1` | `>`（大于） | 数值比较 |
| `2` | `<`（小于） | 数值比较 |
| `3` | `>=`（大于等于） | 数值比较 |
| `4` | `<=`（小于等于） | 数值比较 |
| `5` | `=`（String 专用） | 字符串精确匹配 |
| `6` | `IN`（String） | 字符串集合匹配，`value` 传逗号分隔的字符串即可，如 `"规模宽基,行业主题"` |
| `7` | `LIKE` | 模糊匹配，包含关系 |
| `8` | `IN`（Number） | 数值集合匹配 ，逗号分隔|

### 常见意图到 `wheres` 的映射（拼条件时直接照抄改值即可）

| 用户意图 | `wheres` 条件 |
|---|---|
| 宽基ETF | `{"field":"fundType1","type":5,"value":"规模宽基"}` |
| 行业ETF | `{"field":"fundType1","type":5,"value":"行业主题"}` |
| 跨境/海外ETF | `{"field":"fundType1","type":5,"value":"全球市场"}` |
| 债券ETF | `{"field":"fundType1","type":5,"value":"债券资产"}` |
| 多类型（宽基+行业） | `{"field":"fundType1","type":6,"value":"规模宽基,行业主题"}` |
| 低估值 | `{"field":"peFenWei","type":4,"value":"0.3"}` |
| PE<20 | `{"field":"pe","type":2,"value":"20"}` |
| PB<1.5 | `{"field":"pb","type":2,"value":"1.5"}` |
| 高股息 | `{"field":"yielD","type":3,"value":"3"}` |
| 近期涨幅好 | `{"field":"dayRise5","type":3,"value":"0"}` |
| 近1月涨幅>10% | `{"field":"dayRise20","type":3,"value":"0.1"}` |
| 近1年涨幅>20% | `{"field":"oneYearRise","type":3,"value":"0.2"}` |
| 今年以来上涨 | `{"field":"thisYearRise","type":3,"value":"0"}` |
| 规模大（>10亿） | `{"field":"scope","type":3,"value":"1000000000"}` |
| 规模>5亿 | `{"field":"scope","type":3,"value":"500000000"}` |
| 流动性好 | `{"field":"turnVolume20","type":3,"value":"100000000"}` |
| 可T0交易 | `{"field":"t0Trade","type":5,"value":"1"}` |
| 可融资融券 | `{"field":"fundLoan","type":5,"value":"1"}` |
| 互联互通 | `{"field":"northBond","type":5,"value":"1"}` |
| 指数增强 | `{"field":"indexEnhance","type":5,"value":"1"}` |
| 低费率 | `{"field":"cost","type":4,"value":"0.003"}` |
| ROE高 | `{"field":"roe","type":3,"value":"0.15"}` |
| RSI超卖 | `{"field":"rsi","type":4,"value":"30"}` |
| RSI超买 | `{"field":"rsi","type":3,"value":"70"}` |
| 规模增长 | `{"field":"scopeIncreaseM","type":3,"value":"0"}` |
| 资金流入 | `{"field":"marginFlowinM","type":3,"value":"0"}` |
| 高分红 | `{"field":"dividedNoThisYear","type":3,"value":"1"}` |
| 沪深300/中证500/恒生科技/纳斯达克/半导体/红利/科技+ETF | `{"field":"indexName","type":7,"value":"沪深300"}`（把 value 换成对应指数名即可） |
| 热门搜索 | 不用加条件，直接 `"orderBy":"search1W","orderType":"D"` |

多个条件放进同一个 `wheres` 数组即为 AND 关系。例如「宽基ETF AND 规模>5亿 AND PE分位<50%」：

```bash
python scripts/get_data.py --payload '{
  "wheres": [
    {"field": "fundType1", "type": 5, "value": "规模宽基"},
    {"field": "scope", "type": 3, "value": "500000000"},
    {"field": "peFenWei", "type": 4, "value": "0.5"}
  ],
  "fields": "code,etfName,fundCompany,fundType2,indexName, scope, cost, pe,pb",
  "orderBy": "scope",
  "orderType": "D"
}'
```

热门搜索（不需要 `wheres`，直接靠排序），只要前10条：

```bash
python scripts/get_data.py --payload '{
  "orderBy": "search1W", 
  "orderType": "D", 
  "pageSize": 10,
  "fields": "code,etfName,fundCompany,fundType2,indexName, scope, cost, pe,pb"
}'
```

低估值行业ETF（低估值 AND 行业主题）：

```bash
python scripts/get_data.py --payload '{
  "wheres": [
    {"field": "fundType1", "type": 5, "value": "行业主题"},
    {"field": "peFenWei", "type": 4, "value": "0.3"}
  ],
  "fields": "code,etfName,fundCompany,fundType2,indexName, scope, cost, pe,pb"
}'
```

---


## 常见错误信息

| 触发条件 | 错误信息 |
|---|---|
| 未设置 `PINGAN_SKILL_APIKEY` | 缺少环境变量 PINGAN_SKILL_APIKEY |
| HTTP 401 | 缺少 API Key。 |
| HTTP 403 | API Key 无效或没有权限。 |
| HTTP 429 | 接口调用频率超限。 / 今日调用次数已达上限。 |
| HTTP 503 | 服务暂时不可用，请稍后重试。 |

遇到 429/配额类错误不要立即重试刷屏，如实告知用户当前限流状态；遇到 503 可以间隔几秒重试一次。


---

## 注意事项

1. **字段名精确匹配**：`fundType1` 的值是 `规模宽基`、`行业主题`、`风格策略`、`全球市场`、`债券资产`、`货币基金`，注意中文名称完全匹配
2. **数值字段传字符串**：`wheres` 的 `value` 值统一用字符串格式传递
3. **分页限制**：`pageSize` 最大100，默认10只
4. **模糊搜索**：`type=7` 支持模糊匹配，`indexName` 字段可以用它搜索特定指数
5. **多个条件为AND**：`wheres` 数组中的多个条件之间是 AND 关系
6. **type=6 用于多选**：需要匹配多个文本值时用 `type=6`，逗号分隔
7. **规模字段**：`scope` 单位为元，10亿=1000000000
8. **涨跌幅字段**：`oneYearRise`、`dayRise20`、`thisYearRise` 等字段值需传小数，如 `0.155` 表示15.5%
9. **费率字段**：`cost` 字段是托管费+管理费的总和，需传小数，如 `0.0015` 表示0.15%
10. **估值低位标签**：`lowValuation` 字段的值为 `1` 时表示该ETF被标记为低估值
11. **可T0ETF**：`t0Trade` 字段的值为 `1` 时表示支持T+0交易
12. **排序字段**：按用户最关心的维度排序，如按收益排序用 `oneYearRise` 或 `dayRise20`，按规模排序用 `scope`，按费率排序用 `cost`
13. **基金/指数代码带市场前缀**：`code`、`indexCode` 字段的 value 必须带市场前缀（`SH`=上交所，`SZ`=深交所），如华泰柏瑞沪深300ETF请传 `SH510300`，沪深300指数请传 `SH000300`，不要只传 `510300` / `000300`

---

## 参考字典

### 一级分类（`fundType1`）

规模宽基、行业主题、风格策略、全球市场、债券资产、商品资产、货币基金

### 二级分类（`fundType2`）

**二级分类字段要传入以下枚举值的完整内容，例如：`行业主题,基建地产`，不得只传`金融`或`基建地产`等**

| 字段名 |
|---|
|行业主题,基建地产|
|行业主题,金融|
|行业主题,军工|
|行业主题,科技|
|行业主题,消费|
|行业主题,新能源|
|行业主题,医药|
|行业主题,制造|
|行业主题,周期|
|风格策略,成长|
|风格策略,低波|
|风格策略,红利|
|风格策略,基本面|
|风格策略,价值|
|风格策略,其他风格|
|风格策略,质量|
|规模宽基,大盘|
|规模宽基,其他宽基|
|规模宽基,小盘|
|规模宽基,中盘|
|全球市场,港股|
|全球市场,美股|
|全球市场,其他市场|
|商品资产,黄金|
|商品资产,其他商品|
|债券资产,地方债|
|债券资产,国开债|
|债券资产,国债|
|债券资产,可转债|
|债券资产,其他债券|
|货币基金,货币基金|
