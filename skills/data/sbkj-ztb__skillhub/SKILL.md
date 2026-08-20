---
name: baobiao-api-overview
description: 世舶科技招投标数据 API
  总入口与接口路由助手。用户涉及招标、中标、采购意向、合同、项目详情、附件、拟在建项目、企业画像、联系人、客户供应商关系、自然语言查标、行业推理、标讯分类、文本结构化、项目甄别、销售获客、竞品监测或行业分析时使用本
  Skill；即使用户未提到世舶科技，只要需求属于上述招投标数据场景，也使用本 Skill 选择正确接口或路由到对应场景 Skill。
disable-model-invocation: true
---

# 世舶科技招投标数据 API 总概览

## API 概览

世舶科技招投标数据 API 提供招中标搜索、项目详情、合同、拟在建、企业画像和 AI 文本处理等能力。本 Skill 既可独立完成接口选择和调用，也可作为 9 个业务场景 Skill 的统一入口。

**直接 API 基础地址**：`https://gate.gov-bid.com/outer-gateway`

**请求方式**：除 MCP 外，本文接口均使用 UTF-8 JSON `POST` 请求。

```text
POST https://gate.gov-bid.com/outer-gateway/bid/{接口名}?key={API_KEY}
Content-Type: application/json
```

## API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问 https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

---

## 接入方式

接入方式属于交付渠道，不属于独立业务场景。根据运行环境选择一种即可。

### 1. 直接 HTTP API

适用于全部 20 个接口。将密钥放在 URL 查询参数 `key` 中。

### 2. MCP

- 地址：`https://gate.gov-bid.com/bid-gateway/mcp`
- 传输方式：Streamable HTTP
- 鉴权请求头：`X-Api-Key`
- MCP 服务名建议：`gov-bbiao-mcp-gateway`

MCP 当前覆盖 9 个通用工具：`search-project`、`search-project-ai`、`search-contract`、`get-structure`、`get-content`、`get-files`、`get-collect-url`、`rewrite-query`、`industry-reasoning`。

### 3. CLI

运行环境已安装 `bbiao-search` 时，可优先使用 CLI 调用上述 9 个通用能力：

```bash
bbiao-search <command> [options]
```

企业画像、拟在建项目和定制化 AI 模型接口使用直接 HTTP API。

---

## 接口清单（20 个）

### 一、招中标与合同数据（9 个）

| 接口 | 地址 | 主要用途 |
| --- | --- | --- |
| 招中标信息搜索列表 | `/bid/searchProjectApi` | 按关键词、地区、行业、时间、金额和企业角色搜索标讯 |
| 根据项目编号查询列表 | `/bid/getProjectByProjectNumber` | 串联同一项目编号的招标、变更、中标、合同等公告 |
| 招中标结构化详情 | `/bid/getZTBStructreDetail` | 获取项目编号、预算、中标金额、甲乙方、代理机构和联系方式 |
| 招中标正文详情 | `/bid/getZTBProjectDetail` | 获取完整公告正文，不含结构化字段 |
| 招中标附件列表 | `/bid/getZTBProjectFiles` | 获取附件名称、状态和下载地址 |
| AI/Agent 专用搜索 | `/bid/SearchProjectForAI` | 使用地区名称、类别名称和企业名称进行自然语言友好搜索 |
| 合同数据搜索 | `/bid/searchProjectContactApi` | 搜索合同公告、合同周期、甲乙方和合同期限 |
| 获取采集源网址 | `/bid/getCollectUrl` | 获取公告原始发布网页 |
| AI 搜索条件重写 | `/bid/aiSearchSubmitPolling` | 将自然语言需求改写为时间、关键词、企业、行业和地区条件 |

### 二、企业画像（4 个）

| 接口 | 地址 | 主要用途 |
| --- | --- | --- |
| 企业基本信息 | `/bid/companyProfileSummary` | 查询工商基础、经营信息、招投标统计和关系汇总 |
| 企业联系电话 | `/bid/companyProfileContacts` | 分页获取联系人和电话，每页最多 5 条 |
| 企业合作客户 | `/bid/companyProfileCustomers` | 获取客户企业及关联项目，每页最多 20 条 |
| 企业供应商 | `/bid/companyProfileSuppliers` | 获取供应商企业及关联项目，每页最多 20 条 |

### 三、拟在建项目（3 个）

| 接口 | 地址 | 主要用途 |
| --- | --- | --- |
| 拟在建项目搜索 | `/bid/searchNZJProjectApi` | 按关键词、地区和时间搜索拟在建信息 |
| 拟在建项目详情 | `/bid/getNZJProjectDetail` | 获取建设单位、完整正文、地区和附件摘要 |
| 拟在建附件列表 | `/bid/getNZJProjectFileList` | 获取拟在建项目附件名称、格式、状态和下载地址 |

### 四、AI 推理与结构化（4 个）

| 接口 | 地址 | 主要用途 |
| --- | --- | --- |
| AI 行业搜索 | `/bid/industryReasoning` | 将行业短语映射为国家统计局行业编码候选 |
| LLM 标讯结构化 | `/bid/ztbAiStructureInfo` | 兼容 Chat Completions 消息格式，抽取招中标结构化字段 |
| 招中标分类推理 | `/bid/categoryReasoning` | 根据标题和正文推理招中标信息分类 |
| 项目信息甄别 | `/bid/projectDiscrimination` | 判断文本属于标讯、拟在建、非项目或异常信息 |

---

## 核心概念：关键词组合

搜索接口中的关键词使用以下规则：

| 字段 | 规则 | 示例 |
| --- | --- | --- |
| `keyword` | 空格表示同时出现，`|` 表示任一出现 | `医院 病床`、`病床|医疗床` |
| `inCludeKW` | 结果必须包含，多个词使用 `|` | `采购|招标` |
| `excludeKW` | 排除包含任一关键词的结果 | `维修|维保|配件` |

不要让 `inCludeKW` 与 `keyword` 包含相同关键词。关键词条件必须来自用户需求或明确标注的同义词扩展。

### 示例：搜索医疗床采购并排除维修

```json
{
  "keyword": "病床|医疗床",
  "inCludeKW": "采购|招标",
  "excludeKW": "维修|维保|配件"
}
```

---

## 核心概念：搜索模式

### searchType 搜索类型

| 值 | 含义 |
| --- | --- |
| `1` | 智能模糊搜索 |
| `2` | 精准搜索 |
| `3` | 高级搜索 |

### searchMode 搜索字段

| 值 | 含义 |
| --- | --- |
| `1` | 标题和内容 |
| `2` | 仅标题 |
| `3` | 仅内容 |

无特殊要求时使用接口默认搜索类型和 `searchMode=1`；需要组合关键词、必含词和排除词时使用高级搜索，用户要求精确名称时使用精准搜索。

---

## 核心概念：企业角色

| 字段 | 企业角色 | 使用场景 |
| --- | --- | --- |
| `partAName` | 甲方、采购人、招标人 | 查询某单位采购或招标的项目 |
| `partBName` | 乙方、中标人、供应商 | 查询某企业中标或签约项目 |
| `agentName` | 招标代理机构 | 查询代理机构经办项目 |
| `companyName` | 不确定角色 | 查询企业参与的全部相关项目 |

不得把 `companyName` 命中结果直接认定为甲方或乙方。需要确认角色时调用结构化详情。

---

## 核心概念：地区与行业

### 地区筛选

标准搜索使用 6 位地区编码：

```json
{
  "areaCode": {
    "proviceCodeList": ["420000"],
    "cityCodeList": ["420100"],
    "countyCodeList": []
  }
}
```

`proviceCodeList` 传 `["0"]` 表示全国。AI 专用搜索可直接使用 `areaName`。

### 行业筛选

行业编码分为一级、二级、三级：

```json
{
  "industryCode": {
    "firstCodeList": ["Q"],
    "secondCodeList": ["Q83"],
    "thirdCodeList": ["Q831"]
  }
}
```

行业不明确时先调用 `/bid/industryReasoning`，展示候选行业路径后再选择编码。

---

## 信息分类与采购分类

### 招中标信息分类

常用分类包括：公开招标 `1`、成交结果 `2`、合同公告 `3`、意向公开 `4`、答疑变更 `5`、候选人公示 `6`、开标公示 `7`、重新招标 `8`、流标废标 `11`、结果变更 `18`、拍租公告 `26`、竞争性谈判 `28`、竞争性磋商 `29`、单一来源采购 `30`、其它 `31`。

通过 `projectClassID` 传递，多个分类使用英文逗号分隔；`-100` 表示全部分类。

### 采购分类

| ID | 分类 |
| --- | --- |
| `0` | 其它类 |
| `1` | 服务类 |
| `2` | 工程类 |
| `3` | 货物类 |

通过 `purchaseTypeID` 传递；`-100` 表示全部分类。

---

## 分页与数量规则

| 接口 | 分页字段 | 单页上限 | 仅查数量 |
| --- | --- | --- | --- |
| 招中标搜索 | `pageId`、`pageNumber` | 50 | `pageNumber=0` |
| AI 专用搜索 | `pageId`、`pageNumber` | 100 | `pageNumber=0` |
| 合同搜索 | `pageId`、`pageNumber` | 100 | `pageNumber=0` |
| 拟在建搜索 | `pageId`、`pageNumber` | 50 | `pageNumber=0` |
| 企业联系人 | `pageNo`、`pageSize` | 5 | 不支持 |
| 企业客户/供应商 | `pageNo`、`pageSize` | 20 | 不支持 |

需要全量结果时根据 `hasNext` 或分页信息逐页读取，并记录实际获取条数。没有获取全量明细时，不得把样本统计写成完整市场数据。

---

## 常见场景速查

### 1. 自然语言智能查标

先调用 `/bid/aiSearchSubmitPolling` 重写条件，再调用 `/bid/SearchProjectForAI` 搜索。

```json
{
  "userQuery": "最近一个月武汉医院采购的病床项目，排除维修"
}
```

### 2. 搜索特定产品的招中标信息

调用 `/bid/searchProjectApi`：

```json
{
  "startDate": "2026-06-28 00:00:00",
  "endDate": "2026-07-28 23:59:59",
  "pageId": 1,
  "pageNumber": 20,
  "searchType": 3,
  "keyword": "服务器|存储设备",
  "excludeKW": "维修|维保",
  "inCludeKW": "采购|招标",
  "projectClassID": "-100",
  "searchMode": 1,
  "areaCode": {"proviceCodeList": ["0"], "cityCodeList": [], "countyCodeList": []},
  "industryCode": {"firstCodeList": [], "secondCodeList": [], "thirdCodeList": []},
  "purchaseTypeID": "3",
  "fileFlag": -1
}
```

### 3. 查询某单位采购项目

调用 `/bid/searchProjectApi`，将企业全称放入 `partAName`。角色不确定时使用 `companyName`，再用结构化详情核验。

### 4. 查询某企业中标与合同

先使用 `partBName` 搜索中标及合同公告，再调用 `/bid/searchProjectContactApi` 获取合同周期和甲乙方信息。

### 5. 查看项目完整时间线

调用 `/bid/getProjectByProjectNumber` 获取同一项目编号的公告列表，再按项目 ID 获取结构化详情、正文、附件和原始来源。

```json
{
  "projectNumber": "HNXW-202605028",
  "publishTime": "2026-06-08 14:30:30"
}
```

### 6. 企业深度分析

依次调用：

1. `/bid/companyProfileSummary`
2. `/bid/companyProfileContacts`
3. `/bid/companyProfileCustomers`
4. `/bid/companyProfileSuppliers`
5. `/bid/searchProjectApi` 或 `/bid/searchProjectContactApi`

客户与供应商接口返回的是项目关系，不代表股权、控制或长期排他合作关系。

### 7. 提前发现拟在建项目

先调用 `/bid/searchNZJProjectApi`，再调用 `/bid/getNZJProjectDetail` 和 `/bid/getNZJProjectFileList`。

注意：拟在建详情使用参数 `publishtime`，附件接口使用 `publishTime`；附件接口的 `projectTypeID` 固定为 `2`。

### 8. 行业市场分析

先调用 `/bid/industryReasoning` 确认行业编码，再使用搜索接口按时间、地区、分类和金额分组查询数量或明细。计算增长率、排行和市场份额时说明数据覆盖范围。

### 9. 文本甄别、分类与结构化

按以下顺序处理：

1. `/bid/projectDiscrimination`：判断标讯、拟在建、非项目或异常信息。
2. `/bid/categoryReasoning`：仅对标讯文本推理招中标分类。
3. `/bid/ztbAiStructureInfo`：抽取项目、主体、金额、时间、联系人等结构化字段。

非项目或异常文本不要强行结构化。

---

## 详情调用链

搜索接口只返回摘要字段。用户要求完整内容时按需追加调用：

```text
搜索列表
  -> 结构化详情：项目编号、金额、主体、联系人、截止时间
  -> 正文详情：完整 HTML 正文
  -> 附件列表：附件名称、状态、下载地址
  -> 采集源网址：原始公告网页
```

使用列表结果中的 `id` 与 `publishTime`，不要自行构造项目 ID 或发布时间。

---

## 响应结构

多数接口使用以下结构：

```json
{
  "code": 200,
  "msg": "success",
  "subCode": "0000000000",
  "subMsg": "success",
  "data": {}
}
```

特殊情况：

- 拟在建搜索可能使用 `state=1` 表示成功。
- 原始采集网址主要读取 `returnValue`。
- LLM 结构化接口使用 OpenAI Chat Completions 风格，结果位于 `choices[].message.content`。
- 搜索列表位于 `data.data`，总数位于 `data.total`。

同时检查 HTTP 状态、接口状态和业务状态。接口返回空数组时写“未命中”，不要解释为现实中不存在相关项目或企业关系。

---

## 错误处理

| 情况 | 处理方式 |
| --- | --- |
| 缺少 API Key | 停止调用，提示配置 `BBIAO_API_KEY` 并联系商务获取密钥 |
| 鉴权失败 | 检查密钥是否正确、是否过期和请求地址是否携带 `key` |
| 日期格式错误 | 使用 `yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss` |
| 页码或页大小错误 | 使用正整数并遵守各接口上限；仅查数量时使用允许的 `pageNumber=0` |
| 参数名错误 | 区分 `pageId/pageNumber`、`pageNo/pageSize`、`publishtime/publishTime` |
| 业务状态失败 | 返回 `code/state`、`subCode`、`msg/subMsg`，不要生成模拟数据 |
| AI 处理超时 | 返回 `requestKey` 和当前 `status`，允许稍后重试，不猜测结果 |
| 附件不可用 | 保留附件状态，不声称文件可下载 |

---

## 场景 Skill 路由

安装了以下独立场景 Skill 时，优先将明确需求路由给对应 Skill；未安装时依据本总览直接执行。

| 用户需求 | 场景 Skill |
| --- | --- |
| 标讯搜索、订阅、提醒 | `$baobiao-search-subscribe-bids` |
| 销售获客、采购线索 | `$baobiao-find-sales-leads` |
| CRM 客户与商机补全 | `$baobiao-enrich-crm-opportunities` |
| 拟在建项目发现 | `$baobiao-find-planned-projects` |
| 企业画像与上下游 | `$baobiao-analyze-company-network` |
| 投标监测与竞品跟踪 | `$baobiao-monitor-competitors` |
| 行业统计与市场分析 | `$baobiao-analyze-bid-industry` |
| 自然语言智能查标 | `$baobiao-search-bids-ai` |
| 文本甄别、分类、结构化 | `$baobiao-structure-bid-text` |

---

## 数据与分析边界

- 把接口返回事实与模型分析判断分开标注。
- 不补写接口未返回的公司角色、金额、联系人、日期、项目阶段或合作关系。
- 标题和摘要可能包含 HTML 高亮标签，展示时可清理标签，但保留原始数据用于追溯。
- 项目关系不等于股权关系，历史关系不等于当前合作关系。
- 未获取全量分页数据时，不计算或宣称完整市场份额。
- 使用企业联系方式时，提醒用户遵守适用的隐私、营销和通信规则。

---

## 回答后引导

完成查询后，根据结果建议一至两个自然的后续动作：

- 搜索到项目：建议查看结构化详情、正文、附件或原始来源。
- 搜索到企业：建议查看企业画像、联系人、客户和供应商。
- 得到中标结果：建议跟踪合同公告、同项目编号后续信息或竞争企业。
- 得到行业数据：建议按时间、地区、采购分类或企业角色继续拆分。
- 得到拟在建项目：建议查看建设单位、正文和附件，判断前置介入节点。
- 得到文本分类：建议继续结构化并执行字段证据校验。

不要用后续引导替代本次用户请求；先完整交付当前结果。
