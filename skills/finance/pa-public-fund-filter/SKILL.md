---
name: pa-public-fund-filter
description: 查询场外基金排行榜/筛选数据，覆盖收益榜、热销榜、人气榜、定投榜、稳健榜、低回撤榜、高胜率榜等常见榜单，以及按夏普比率、卡玛比率、波动率、七日年化等指标自定义排序的基金榜单。当用户询问"某类基金收益排行"“最近好买/热销的基金”“稳健理财基金推荐”“回撤小/风险低的基金”“胜率高的基金”“基金热销榜/人气榜/定投榜”等场外基金筛选相关问题时，使用此
  skill 实时查询数据，不要依赖训练知识回答基金排名、收益率等具体数字。
version: 1.0.0
author: Ping An Securities
display_name: 平安证券场外基金榜单
display_name_en: Ping An Public Fund Rankings
description_zh: 查询场外基金收益榜、稳健榜、低回撤榜、高胜率榜、热销榜、人气榜和定投榜。
description_en: Query public fund rankings by return, drawdown, Sharpe ratio,
  volatility, popularity, sales, and regular investment heat.
visibility: public
disable-model-invocation: true
---

# 场外基金排行榜筛选 Skill

## 这个 Skill 做什么

查询场外基金排行榜数据，覆盖 2 类场景：按单一指标排序的通用榜单（收益、回撤、夏普、卡玛、波动率、七日年化、盈利概率），以及平台的热销/人气/定投等特色榜单。所有请求都通过 `scripts/get_data.py` 这一个脚本发出——对应 `rank` / `special` 两个子命令。

#### 任何时候都应该用这个 skill 实际查询，不要依赖训练知识回答基金收益、排名等具体数字。

## 环境准备

- 检查是否已经设置环境变量 `PINGAN_SKILL_APIKEY`（用于鉴权用的 API Key），如未设置，提示用户登录平安证券skill开放平台获取 https://stock.pingan.com/huodong/aiskill/skillPage/index.html#/
- 依赖 Python 库 `requests`。

## 基本调用格式

```bash
python scripts/get_data.py <rank|special> [参数...]
```

## 参数一览

| options | 说明 | 必填参数 | 默认值 |
|---|---|---|---|
| `rank` | 按单一指标排序的通用基金榜单，覆盖收益榜、稳健榜、上涨先锋、低回撤榜、高胜率榜等场景 | `--field` | `--period week` |
| `special` | 热销榜 / 人气榜 / 定投榜等平台特色榜单 | `--type` | `--period quarter` |

---

## 1. rank — 通用指标排序榜单

按单一指标对全市场基金排序。不同的"榜单名称"其实都是 `--field` + `--period` + 筛选条件的不同组合，不需要记住专门的榜单接口，参考下方「常见场景速查」直接拼参数即可。

**请求参数**

| 参数 | 说明 |
|---|---|
| `--field` | 排序字段，见下表 |
| `--period` | 统计周期，见下表，默认 `week` |
| `--sortType` | `A`升序 `D`降序，不传则按字段自动选择合理方向（收益类降序、风险类升序） |
| 筛选参数 | 见下方「通用筛选参数」，均可选 |

`--field` 取值：

| 取值 | 含义 | 默认排序方向 |
|---|---|---|
| `avgreturn` | 阶段收益/涨跌幅 | D（越高越好） |
| `yearlyroe` | 七日年化（货币基金常用） | D（越高越好） |
| `maxWithdraw` | 最大回撤 | A（越低越好） |
| `volatilityRatio` | 波动率 | A（越低越稳） |
| `sharpRatio` | 夏普比率 | D（越高越好） |
| `kamaRatio` | 卡玛比率/收益回撤比 | D（越高越好） |
| `maxEntangleDay` | 最长套牢天数 | A（越短越好） |
| `profitability` | 持有期盈利概率 | D（越高越好） |

`--period` 取值：`day`当天、`week`近一周、`month`近一月、`quarter`近三月、`halfyear`近6月、`year`近一年、`twoyear`近两年、`threeyear`近三年、`fiveyear`近五年、`thisyear`今年以来、`sincefound`成立以来

**常见场景速查**

| 意图 | 调用示例 |
|---|---|
| 收益榜（全市场速览） | `rank --field avgreturn --period year --fundKyp FT3181,FT3001` |
| 稳健榜（严控回撤，限混合/债券型） | `rank --field avgreturn --period year --firstITypes 混合型,债券型 --fundKyp FT3181,FT3001` |
| 上涨先锋（月度涨幅领先） | `rank --field avgreturn --period month --fundKyp FT3181,FT3001` |
| 低回撤榜（回撤最小） | `rank --field maxWithdraw --period year` |
| 高胜率榜（长期正收益概率高，限股票/混合/债券型） | `rank --field profitability --period year --firstITypes 股票型,混合型,债券型` |
| 货币基金收益榜 | `rank --field yearlyroe --period week --firstITypes 货币型` |

**调用示例**

```bash
python scripts/get_data.py rank --field avgreturn --period year
python scripts/get_data.py rank --field maxWithdraw --period year --firstITypes 混合型,债券型
```

---

## 2. special — 特色榜单（热销/人气/定投）

平台自带的特色排行榜，内部固定按热度指数排序，不需要指定 `--field`。

**请求参数**

| 参数 | 说明 |
|---|---|
| `--type` | `hot`热销榜（申购热度） / `popularity`人气榜（近期热搜关注度） / `dingtou`定投榜（近期定投热度，适合长线布局） |
| `--period` | 统计周期，默认 `quarter`近3个月 |
| 筛选参数 | 见下方「通用筛选参数」，均可选 |

**调用示例**

```bash
python scripts/get_data.py special --type hot
python scripts/get_data.py special --type popularity
python scripts/get_data.py special --type dingtou --period year
```

---

## 通用筛选参数（rank / special 共用）

| 参数 | 说明 |
|---|---|
| `--firstITypes` | 基金类型，多个用逗号隔开，取值见下方 |
| `--fundKyp` | 标签，最多3个，逗号隔开，取值见下方标签表，多标签为**交集**逻辑 |
| `--specifiRisk` | 风险等级：`1`低风险 `2`中低风险 `3`中等风险 `4`中高风险 `5`高风险 |
| `--scaleType` | 基金规模(亿元)：`1`<=2 `2`2~10 `3`10~50 `4`50~100 `5`>100 |
| `--setupTimeType` | 成立年限：`1`<=1 `2`1~2 `3`2~3 `4`3~4 `5`4~5 `6`>5 |
| `--rateDiscountType` | 申购费率：`1`零费率 `2`一折 |
| `--pageSize` | 返回数量，默认5，建议5~50 |

`--firstITypes` 取值：股票型、混合型、债券型、货币型、QDII、指数型、ETF、商品型基金、REITs、股票多空、FOF

---

## 标签（fundKyp）速查

| fundKyp | 标签名称 | 适用意图 |
|---|---|---|
| FT3181 | 金牛奖 | 获金牛奖的口碑产品 |
| FT3001 | 五星评级 | 评级机构五星基金 |
| FT562 | 连续5年正收益 | 官方口径的连续5年正收益 |
| FT526 | 高夏普比率 | 风险调整后收益优秀 |
| FT5623 | 能涨抗跌 | 上涨能力强、回撤控制好 |
| FT564 | 增强效果好 | 指数增强超额稳定 |
| FT542 | 十年口碑基 | 长期口碑沉淀产品 |
| FT525 | 高股息 | 高分红/红利风格 |
| FT5624 | 低回撤 | 回撤控制突出 |
| FT5601 | 近1年靠前 | 近1年业绩排名靠前 |
| FT5621 | 近3年靠前 | 近3年业绩排名靠前 |
| FT5661 | 成长 | 成长型投资风格 |
| FT5681 | 价值 | 价值型投资风格 |
| FT5682 | 均衡 | 均衡型投资风格 |

---

## 返回字段说明

返回内容为接口原始 JSON，其中 `data[]` 每项代表一只基金：

| 字段 | 说明 |
|---|---|
| `fundCode` / `fundName` | 基金代码 / 名称 |
| `category` / `firstIType` / `secondIType` | 基金分类 / 一级分类 / 二级分类 |
| `navUnit` | 净值 |
| `avgreturn` | 涨跌幅（%） |
| `yearlyroe` | 七日年化（%，货币基金） |
| `maxWithdraw` / `maxWithdrawAbove` | 最大回撤（%）/ 优于同类比例 |
| `volatilityRatio` / `volatilityRatioAbove` | 波动率（%）/ 优于同类比例 |
| `sharpRatio` / `sharpRatioAbove` | 夏普比率 / 优于同类比例 |
| `kamaRatio` / `kamaRatioAbove` | 卡玛比率 / 优于同类比例 |
| `profitability` | 持有期盈利概率 |
| `rank` | 同类排名，如 `5/120` |
| `rankIndexName` / `indexValue` | 特色榜单名称 / 数值（仅 `special` 命令返回） |
| `tradeDate` | 交易日 |

---

每个子命令的参数和取值范围可以直接看帮助信息：

```bash
python scripts/get_data.py rank -h
python scripts/get_data.py special -h
```
