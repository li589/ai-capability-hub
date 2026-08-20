---
name: baobiao-find-sales-leads
description: "从招标、采购意向、中标和企业数据中发现潜在采购客户，补充项目主体、联系人和跟进理由，并形成销售线索清单。用于销售获客、采购线索挖掘、目标客户寻找、区域商机筛选、项目型销售拓客等需求。"
---

# 销售获客线索发现

## 目标

围绕用户的产品或服务，识别正在采购或可能采购的单位，形成有来源、可解释、可跟进的销售线索。把接口返回事实与销售分析判断分开呈现。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`，密钥只放在请求参数 `key` 中。
- 检查 HTTP 状态、`code`、`subCode`；失败时保留错误提示，不得生成模拟线索。
- 用户未指定时间时默认查询最近 30 天，并在结果中标明默认范围。
- 搜索列表每页不超过 50；只对候选度较高的项目追加详情和企业查询，避免无边界调用。

## 收集输入

提取目标产品或服务、行业、地区、理想客户类型、项目金额区间、时间范围、排除对象、期望线索数量。若用户只给产品名，先生成同义词和采购表达，但明确这些词属于搜索扩展词。

## 执行流程

1. 将产品能力转成采购关键词、必含词和排除词。
2. 调用标讯搜索接口，优先关注采购意向、公开招标、竞争性磋商、竞争性谈判等前置机会；用户另有要求时按其分类执行。
3. 从列表中提取甲方、项目金额、地区、发布时间、截止时间和附件状态。
4. 对高匹配项目调用结构化详情，补充项目编号、甲方联系人、代理机构和联系方式。
5. 对明确的目标企业调用企业画像与企业联系电话接口，补充企业背景和可公开使用的联系线索。
6. 根据产品匹配度、采购阶段、时效、金额、地域和联系方式完整度生成透明评分。评分是分析结果，不是接口原始字段。
7. 输出优先跟进、观察和低匹配三档线索，并为每条线索给出下一步动作。

## 接口

### 发现采购项目

`POST /outer-gateway/bid/searchProjectApi`

使用 `startDate`、`endDate`、`pageId`、`pageNumber`、`searchType`，结合 `keyword`、`excludeKW`、`inCludeKW`、`areaCode`、`industryCode`、`projectClassID`、`purchaseTypeID`、`projectMoneyMin`、`projectMoneyMax`、`partAName` 或 `companyName`。

### 补充项目事实

`POST /outer-gateway/bid/getZTBStructreDetail`

请求体：`{"id": 项目ID, "publishTime": "yyyy-MM-dd HH:mm:ss"}`。重点读取 `projectName`、`projectNumber`、`budgetMoney`、`bidMoney`、`siginUpStopDate`、`bidStartDate`、`partyAInfo`、`partyBInfo`、`agencyInfo` 和 `collectUrl`。

### 补充企业资料

- `POST /outer-gateway/bid/companyProfileSummary`：`{"companyName": "企业全称"}`。
- `POST /outer-gateway/bid/companyProfileContacts`：`{"companyName": "企业全称", "pageNo": 1, "pageSize": 5}`，每页最多 5 条。

项目详情中的联系人与企业画像联系人来源不同，分别标注来源，不得合并成未经证实的同一联系人。

## 线索评分

默认采用 100 分制：需求匹配 35、采购阶段 20、时效 15、金额匹配 10、区域匹配 10、联系信息完整度 10。缺失字段按 0 分处理，不得猜测。用户指定评分规则时以用户规则为准。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 招中标信息搜索列表(references/search-project-api.md)
- 招中标信息结构化数据详情(references/get-ztb-structure-detail.md)
- 企业基本信息(references/company-profile-summary.md)
- 企业联系电话(references/company-profile-contacts.md)
- 枚举值与码表(references/enums-and-code-tables.md)

## 输出格式

输出查询口径和评分规则，然后给出线索表：等级、采购单位、项目名称、采购内容、阶段、地区、预算或金额、发布时间、截止时间、联系人、电话、来源项目、匹配理由、建议动作。末尾列出“需人工核实事项”，尤其是联系人有效性、采购进度和预算真实性。
