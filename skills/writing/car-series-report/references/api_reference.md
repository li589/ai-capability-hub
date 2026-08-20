# 汽车之家 API 参考文档

## 概述

车系详解报告所需数据的 API 接口说明。共 3 个接口，分 2 步调用（接口1串行 → 接口2&3并行）。

## 接口总览

| 序号 | 接口名称 | 用途 | 调用时机 |
|---|---|---|---|
| 1 | 车系基础接口 | 根据车系名搜索，获取车系ID、基础信息、车型LIST、竞品车LIST | 第一步 |
| 2 | 车系口碑接口 | 获取口碑分、品牌、口碑标签、雷达维度分 | 第二步（并行） |
| 3 | 车系价格接口 | 获取厂商优惠标签、国家补贴标签 | 第二步（并行） |

---

## 1. 车系基础接口

- **端点**：`GET https://sou.api.autohome.com.cn/v1/search?&pid=90300023&ext={"q":"${车系名}"}`

- **入参**：`ext` 里的 `q` 字段传入提取到的车系名

- **识别判断**：
  - `result-itemlist-iteminfo-id` **不等于 144** → 无法识别车系，请用户确认车系全称
  - `result-itemlist-iteminfo-id` **等于 144** → 提取以下字段

- **返回字段**：

| 字段 | 路径 | 说明 |
|---|---|---|
| 车系ID | `result-itemlist-iteminfo-data-seriesid` | 后续接口入参 |
| 车系名 | `result-itemlist-iteminfo-data-seriesname` | 报告标题 |
| 级别 | `result-itemlist-iteminfo-data-levelname` | 如"紧凑型轿车" |
| 指导价最低价 | `result-itemlist-iteminfo-data-seriesminprice` | 数值，需转万保留2位小数 |
| 指导价最高价 | `result-itemlist-iteminfo-data-seriesmaxprice` | 数值，需转万保留2位小数 |
| 经销商最低价 | `result-itemlist-iteminfo-data-dealer_minOriginalPrice` | 数值，需转万保留2位小数 |
| 销售状态 | `result-itemlist-iteminfo-data-state` | 数值：0=未售，10=待售，20/30=在售，40=停售 |
| 车系头图 | `result-itemlist-iteminfo-data-pnglogo` | URL |
| 车型LIST | `result-itemlist-iteminfo-data-tags` 中 `type=specs` 的 list 下第一个 list | 取前3个车型 |
| 竞品车LIST | `result-itemlist-iteminfo-data-tags` 中 `type=competing` 的 `car_list` | 取前5个竞品 |

**车型LIST字段**（每个车型）：

| 字段 | 说明 |
|---|---|
| `name` | 车型名 |
| `id` | 车型ID |
| `minprice` | 指导价（数值） |
| `price` | 经销商价（数值） |

**竞品车LIST字段**（每个竞品）：

| 字段 | 说明 |
|---|---|
| `seriesName` | 竞品车系名 |
| `seriesId` | 竞品车系ID |
| `minPrice` | 最低指导价 |
| `maxPrice` | 最高指导价 |
| `url` | 竞品车头图 URL |

---

## 2. 车系口碑接口

- **端点**：`GET https://koubeiipv6.app.autohome.com.cn/pc/series/list?seriesId=${车系ID}`

- **入参**：`seriesId` 填车系ID

- **返回字段**：

| 字段 | 路径 | 说明 |
|---|---|---|
| 口碑分 | `result-seriesAverage` | 数值，满分5，保留2位小数 |
| 品牌 | `result-brandName` | 品牌名 |
| 口碑标签LIST | `result-structuredlist` 中 `name="全部"` 的 Summary | 过滤 `Combination="全部"`，取前6个 |
| 雷达分LIST | `result-seriesScoreList` | 取前7个维度 |

**口碑标签LIST字段**（每个标签）：

| 字段 | 说明 |
|---|---|
| `Combination` | 标签名（过滤值为"全部"的数据） |
| `Volume` | 评价人数 |

**雷达分LIST字段**（每个维度）：

| 字段 | 说明 |
|---|---|
| `typeName` | 维度名（空间、配置、性价比、内饰、外观、油耗、驾驶感受） |
| `score` | 得分（满分5） |

---

## 3. 车系价格接口

- **端点**：`GET https://www.autohome.com.cn/web-main/car/web/spec/getPriceInfo?seriesid=${车系ID}&specid=${车型ID}&cityid=110100`

- **入参**：
  - `seriesid`：车系ID
  - `specid`：车型LIST里第一个车型的ID
  - `cityid`：固定 `110100`（北京）

- **返回字段**：

| 字段 | 路径 | 说明 |
|---|---|---|
| 厂商优惠标签LIST | `result-butie-factory-labels` | 取前3个 |
| 国家补贴标签LIST | `result-butie-local-items` | 取前3条 |

**国家补贴标签字段**（每条）：

| 字段 | 说明 |
|---|---|
| `subtitle` | 补贴类型 |
| `amount` | 补贴金额 |

- 拼接格式：`"${subtitle}，至高${amount}元"`

---

## 鉴权方式

公开接口，无需鉴权。

## 数据获取策略

1. 从用户问题提取车系名，调用 **接口1（车系基础接口）** 获取车系ID及基础数据
2. 拿到车系ID和第一个车型ID后，**并行**调用接口2和接口3
3. 将数据填充到脚本内嵌的 HTML_TEMPLATE 模板中，生成最终 HTML 报告
4. 各模块按 SKILL.md 中的显示规则判断是否渲染
