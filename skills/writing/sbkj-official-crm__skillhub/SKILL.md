---
name: baobiao-enrich-crm-opportunities
description: "使用企业画像、联系人、客户供应商关系、招中标项目和合同数据补全 CRM 客户与商机信息，输出字段来源和更新建议。用于 CRM 数据增强、客户档案补全、商机背景调查、客户最近采购动态和合作关系核验。"
---

# CRM 客户商机增强

## 目标

以企业名称为主键补充 CRM 客户档案，发现近期采购、中标、合同和上下游关系。只输出更新建议，不直接覆盖用户现有 CRM 数据，除非用户明确要求并提供可写入系统。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 对每个企业分别记录调用状态。单个企业失败不得导致整批结果被伪造成成功。
- 企业名称不确定时先返回候选与冲突，不得擅自把简称映射为某个法人主体。
- 联系人接口 `pageSize` 最大为 5；客户和供应商接口 `pageSize` 最大为 20。

## 收集输入

接收单个企业名或企业列表，可同时接收 CRM 原字段：统一社会信用代码、联系人、电话、地址、行业、客户阶段、负责人、最近跟进日期和商机名称。提取用户希望增强的字段和时间范围。

## 执行流程

1. 按企业逐条调用企业画像汇总，确认企业名称和基础信息命中状态。
2. 按需分页调用联系人、合作客户和供应商接口。
3. 调用招中标搜索列表，以 `companyName` 查询企业近期参与项目；需要区分角色时分别使用 `partAName`、`partBName`。
4. 调用合同搜索列表，补充合同开始、结束、金额和甲乙方信息。
5. 比较 CRM 原值与接口值，生成“新增、相同、冲突、接口缺失”四种状态。
6. 基于近期项目阶段和企业角色识别商机，但把商机判断标记为分析结论。
7. 输出可导入 CRM 的字段建议和完整来源，不自动删除原字段。

## 接口

- `POST /outer-gateway/bid/companyProfileSummary`：传 `companyName`，读取企业类型、行业、注册地区、法定代表人、成立日期、经营状态、信用代码、注册资本、经营范围、地址、官网、项目统计和关系汇总。
- `POST /outer-gateway/bid/companyProfileContacts`：传 `companyName`、`pageNo`、`pageSize`，读取联系人和电话。
- `POST /outer-gateway/bid/companyProfileCustomers`：传 `companyName`、`pageNo`、`pageSize`，读取客户企业和关联项目。
- `POST /outer-gateway/bid/companyProfileSuppliers`：传 `companyName`、`pageNo`、`pageSize`，读取供应商企业和关联项目。
- `POST /outer-gateway/bid/searchProjectApi`：按 `companyName`、`partAName` 或 `partBName` 查询近期招中标活动，每页不超过 50。
- `POST /outer-gateway/bid/searchProjectContactApi`：查询合同数据，每页不超过 100。

## 字段合并规则

- 以统一社会信用代码作为最高优先级身份标识；缺失时使用接口返回的企业全称，不用简称强行合并。
- 电话、邮箱、地址保留多值和来源时间，不覆盖为单一值。
- 客户与供应商接口返回的是项目关系，不等同于长期战略合作关系、股权关系或当前有效合同。
- 只有项目或合同原文明确支持时，才填写采购方、供应商、中标方等角色。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 企业基本信息(references/company-profile-summary.md)
- 企业联系电话(references/company-profile-contacts.md)
- 企业合作客户(references/company-profile-customers.md)
- 企业供应商(references/company-profile-suppliers.md)
- 招中标信息搜索列表(references/search-project-api.md)
- 招中标合同数据搜索列表(references/search-project-contact-api.md)

## 输出格式

先给出企业处理汇总，再按企业输出：基础画像、联系人、近期项目、合同动态、客户关系、供应商关系、潜在商机。最后给出 CRM 字段变更表：字段、原值、建议值、状态、来源接口、来源项目、核验建议。
