---
name: baobiao-monitor-competitors
description: "按企业名称持续跟踪招标、中标、候选人、合同和合作关系变化，形成竞品动态与项目时间线。用于竞争对手监测、客户采购动态、投标结果跟踪、中标企业分析、合同续期观察和重点企业预警。"
---

# 投标监测与竞品跟踪

## 目标

围绕目标企业或客户，监测其作为甲方、乙方、投标人或代理机构参与的项目变化，形成新增动态、关键事件和竞争态势。监测代表可重复执行的查询流程，不自动承诺后台运行。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问 https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 用户未给监测周期时默认最近 30 天；做增量监测时优先使用用户上次执行时间作为开始时间。
- 搜索列表每页不超过 50，合同列表每页不超过 100。
- 以 `id + publishTime` 去重；同一项目编号的多条公告按发布时间构建时间线，不直接互相覆盖。

## 收集输入

提取目标企业全称、常用简称、关注角色、地区、行业、关键词、时间范围、重点客户、重点竞品和基线数据。简称只用于搜索扩展，最终结论以接口返回主体名称为准。

## 执行流程

1. 分别以 `companyName`、`partAName`、`partBName`、`agentName` 搜索目标企业活动，避免角色混淆。
2. 对同一项目编号调用“根据项目编号查询列表”，串联招标、答疑、候选人、中标、结果变更和合同公告。
3. 对关键项目调用结构化详情，核验甲乙方、投标企业、金额、时间和联系方式。
4. 调用合同搜索接口，识别新签合同、合同期限和可能的续期观察点。
5. 按需调用企业客户、供应商关系接口，观察合作方变化。
6. 与用户提供的上次结果比较，标记新增、状态变化、金额变化和新合作方。
7. 不得仅因某企业出现在投标名单中就判定其落标；只有公告明确支持时才写中标、候选或未中标。

## 接口

- `POST /outer-gateway/bid/searchProjectApi`：按企业角色和关键词搜索项目。
- `POST /outer-gateway/bid/getProjectByProjectNumber`：传 `projectNumber`，可选 `publishTime`，获取同编号公告列表。
- `POST /outer-gateway/bid/getZTBStructreDetail`：传 `id`、`publishTime`，核验项目结构化信息。
- `POST /outer-gateway/bid/searchProjectContactApi`：按企业、行业、地区、日期和合同期限搜索合同。
- `POST /outer-gateway/bid/companyProfileCustomers`：查询企业客户项目关系，每页最多 20。
- `POST /outer-gateway/bid/companyProfileSuppliers`：查询企业供应商项目关系，每页最多 20。

## 事件分级

- 高：新中标、结果变更、大额合同、重点客户新采购、即将到期合同。
- 中：新招标、候选人公示、新合作方、重点地区活动。
- 低：重复公告、无角色证据的名称命中、缺少关键字段的弱相关结果。

分级属于分析规则，应展示触发原因。用户指定阈值时使用用户阈值。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 招中标信息搜索列表(references/search-project-api.md)
- 根据项目编号查询招中标信息列表(references/get-project-by-project-number.md)
- 招中标信息结构化数据详情(references/get-ztb-structure-detail.md)
- 招中标合同数据搜索列表(references/search-project-contact-api.md)
- 企业合作客户(references/company-profile-customers.md)
- 企业供应商(references/company-profile-suppliers.md)

## 输出格式

先输出监测对象和查询范围，再输出“新增与变化摘要”。项目时间线包含项目编号、事件类型、企业角色、标题、金额、发布时间、关键变化、证据来源和项目 ID。最后给出竞争动态判断、待核实事项和下次监测条件。
