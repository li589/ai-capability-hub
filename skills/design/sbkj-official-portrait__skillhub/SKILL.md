---
name: baobiao-analyze-company-network
description: "查询企业基本信息、联系方式、招投标统计、合作客户、供应商和关联项目，形成企业画像与上下游关系分析。用于客户尽调、供应商分析、渠道伙伴识别、企业关系网络、重点账户研究和合作机会判断。"
---

# 企业画像与上下游关系分析

## 目标

以企业全称为入口，形成包含工商基础、经营信息、项目表现、联系人、客户和供应商关系的企业画像。关系结论必须能追溯到接口返回的关联项目。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9  获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 企业名称必须尽量使用法人全称；名称不确定时先报告命中风险。
- 联系人每页最多 5 条，客户与供应商每页最多 20 条。只有用户需要完整关系时才继续翻页。
- 接口无结果时明确写“未命中”，不得等同于企业没有该类信息。

## 执行流程

1. 调用企业画像汇总，读取企业基本资料、项目统计、关系数量和数据命中状态。
2. 根据用户需求调用联系人、客户和供应商分页接口。
3. 对重要关联项目保留项目 ID、名称和发布时间，必要时调用项目详情核验企业角色。
4. 对企业的投标行业、中标行业、客户集中度和供应商集中度进行描述性分析。
5. 区分“接口事实”和“分析判断”。不得把项目合作关系推断为股权、控制、集团或排他合作关系。
6. 多企业对比时统一时间口径、页数和字段范围。

## 接口

### 企业画像汇总

`POST /outer-gateway/bid/companyProfileSummary`

请求体：`{"companyName": "企业全称"}`。读取企业类型、行业、注册地区、法定代表人、成立日期、经营状态、信用代码、资本、经营范围、地址、网站、联系方式、投标与中标统计、关系汇总和 `dataStatus`。

### 联系人与关系

- `POST /outer-gateway/bid/companyProfileContacts`：`{"companyName": "企业全称", "pageNo": 1, "pageSize": 5}`。
- `POST /outer-gateway/bid/companyProfileCustomers`：`{"companyName": "企业全称", "pageNo": 1, "pageSize": 20}`。
- `POST /outer-gateway/bid/companyProfileSuppliers`：`{"companyName": "企业全称", "pageNo": 1, "pageSize": 20}`。

客户和供应商记录重点读取 `partnerCompanyName`、`relatedProjectId`、`relatedProjectName`、`projectPublishTime` 和 `relationshipType`。

### 项目核验

需要确认某个关联项目时，调用 `POST /outer-gateway/bid/getZTBStructreDetail`，传 `id` 和 `publishTime`，核验甲方、乙方、投标企业及代理机构。

## 分析边界

- “合作客户”与“供应商”是招投标项目关系，不代表当前仍在合作。
- 项目数量和金额仅代表接口覆盖范围内的数据，不直接等同于企业全部经营规模。
- 联系方式属于接口返回信息，使用时提示用户遵守适用的隐私、营销和通信规则。
- 不计算未提供分母的市场份额，不根据公司名称猜测集团归属。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 企业基本信息(references/company-profile-summary.md)
- 企业联系电话(references/company-profile-contacts.md)
- 企业合作客户(references/company-profile-customers.md)
- 企业供应商(references/company-profile-suppliers.md)
- 招中标信息结构化数据详情(references/get-ztb-structure-detail.md)

## 输出格式

依次输出：企业概览、经营与注册信息、投标及中标表现、联系人、主要客户、主要供应商、关键关联项目、机会与风险判断。关系表包含合作方、关系类型、关联项目、项目时间、证据和备注。最后列出未命中字段与需要人工核验的结论。
