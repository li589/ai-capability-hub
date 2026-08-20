---
name: baobiao-analyze-bid-industry
description: 按行业、地区、时间、项目分类、采购分类和金额分析招投标及合同数据，输出统计口径、趋势和结构。用于行业研究、区域市场分析、招投标趋势、市场容量观察、客户结构分析和经营决策支持。
disable-model-invocation: true
---

# 招投标行业数据分析

## 目标

用统一口径统计指定行业的招投标数量、金额、地区、信息类型、采购类型和参与企业，形成可复核的市场分析。明确区分完整统计、分页汇总和样本分析。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问 https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 先定义分析周期、地区、行业和分类口径，再调用数据；不同口径不得直接比较。
- 标讯搜索 `pageNumber=0` 时只返回 `total`，单页取数不得超过 50；合同搜索单页不得超过 100。
- 需要全量明细时按 `hasNext` 翻页并记录实际获取条数。未获取全量时必须标注“样本分析”，不得写成完整市场份额。

## 收集输入

提取行业名称或产品关键词、地区、开始与结束日期、比较周期、信息分类、采购分类、金额区间、企业范围和期望指标。用户只给行业名称时，先调用行业推理接口获取候选编码，并说明采用哪个候选。

## 执行流程

1. 调用 AI 行业搜索，将行业短语映射为一级、二级、三级行业编码。
2. 用 `pageNumber=0` 按总体及各分组条件查询数量，构建数量统计。
3. 需要金额、企业排行或项目结构时分页获取明细，去除 HTML 标签并按 `id + publishTime` 去重。
4. 按时间、地区、信息分类、采购分类、金额区间、甲方和乙方聚合。
5. 需要合同视角时调用合同搜索，分析合同周期、金额和企业关系。
6. 输出同比或环比前确认比较区间长度一致；无上期数据时不计算增长率。
7. 报告接口覆盖、缺失金额、分页范围和样本量，避免过度外推。

## 接口

### 行业编码推理

`POST /outer-gateway/bid/industryReasoning`

请求体：`{"keyword": "医疗器械"}`。读取候选的 `fullTitle`、`minTitle`、`firstCodeList`、`secondCodeList` 和 `thirdCodeList`。

### 招中标统计与明细

`POST /outer-gateway/bid/searchProjectApi`

使用 `startDate`、`endDate`、`pageId`、`pageNumber`、`searchType`，结合 `industryCode`、`areaCode`、`keyword`、`projectClassID`、`purchaseTypeID`、`projectMoneyMin` 和 `projectMoneyMax`。数量统计使用 `pageNumber=0`；明细抓取使用 1 至 50。

### 合同分析

`POST /outer-gateway/bid/searchProjectContactApi`

除常规筛选外可使用 `contractEndMin`、`contractEndMax`、`partAName`、`partBName` 和 `companyName`。读取合同开始、结束、项目周期、甲方和乙方信息。

## 指标规则

- 项目数量：按去重后的 `id + publishTime` 计数。
- 金额合计：只汇总可解析的明确金额，并同时报告有金额项目数和缺失率。
- 企业排行：说明按项目数、预算金额、中标金额或合同金额中的哪一个指标排序。
- 增长率：`(本期 - 上期) / 上期`；上期为 0 时只报告绝对变化。
- 市场份额：仅在分母覆盖范围明确且明细完整时计算。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- AI 行业搜索(references/industry-reasoning.md)
- 招中标信息搜索列表(references/search-project-api.md)
- 招中标合同数据搜索列表(references/search-project-contact-api.md)
- 枚举值与码表(references/enums-and-code-tables.md)

## 输出格式

依次输出分析口径、数据覆盖、核心结论、趋势表、地区结构、分类结构、金额结构、甲乙方排行、代表项目和风险提示。每个结论附数据依据；样本结果必须标注样本量、页数和截止时间。
