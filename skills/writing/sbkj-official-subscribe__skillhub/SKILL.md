---
name: baobiao-search-subscribe-bids
description: "搜索、筛选、去重并整理招标、中标、采购意向、合同等标讯，生成可重复执行的订阅条件和增量清单。用于用户提出查标讯、订阅标讯、每日商机、项目提醒、招标公告跟踪、按关键词或地区持续监测等需求。"
---

# 招投标搜索与标讯订阅

## 目标

把用户的业务描述转成可执行的标讯检索条件，返回本次命中结果，并生成下次可复用的订阅规则。订阅代表可重复执行的查询配置；只有运行环境具备定时任务或消息推送能力时，才执行自动推送。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9  获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 统一发送 UTF-8 JSON `POST` 请求，请求地址末尾增加 `?key=<BBIAO_API_KEY>`。
- 同时检查 HTTP 状态、`code` 或 `state`、`subCode`。接口失败时输出错误信息和可重试建议，不得伪造结果。
- 日期按用户时区解释；用户未指定时区时使用 `Asia/Shanghai`。用户未给时间范围时，默认查询最近 7 天并明确说明。
- 展示前清理标题和摘要中的 HTML 高亮标签，但保留项目 ID、发布时间和原始链接用于追溯。

## 收集输入

优先提取以下条件：关键词、排除词、必含词、地区、开始与结束日期、信息分类、采购分类、行业、甲方、乙方、代理机构、金额区间、是否有附件、推送频率和每次返回数量。

关键词规则：同时出现用空格分隔，任一出现用 `|` 分隔。不要让 `inCludeKW` 与 `keyword` 重复。

## 执行流程

1. 把自然语言需求整理为搜索条件；存在明显歧义时列出已采用的解释。
2. 调用“招中标信息搜索列表”获取列表。首次查询使用 `pageId=1`，`pageNumber` 不得超过 50。
3. 需要完整字段时，对高相关结果调用结构化详情；需要正文、附件或原始出处时再调用对应详情接口。
4. 以 `id + publishTime` 作为稳定去重键。用户提供历史结果时，标记新增、已存在和内容状态变化。
5. 按相关度、发布时间、金额匹配、地区匹配和截止时间给出优先级，并解释原因。
6. 输出本次结果和可复用订阅条件。不要声称已经创建后台定时任务，除非确实调用了相应工具并验证成功。

## 接口

### 搜索列表

`POST /outer-gateway/bid/searchProjectApi`

必填：`startDate`、`endDate`、`pageId`、`pageNumber`、`searchType`。常用可选字段：`keyword`、`excludeKW`、`inCludeKW`、`projectClassID`、`searchMode`、`areaCode`、`industryCode`、`purchaseTypeID`、`partAName`、`partBName`、`agentName`、`companyName`、`projectMoneyMin`、`projectMoneyMax`、`fileFlag`。

```json
{
  "startDate": "2026-07-21 00:00:00",
  "endDate": "2026-07-28 23:59:59",
  "pageId": 1,
  "pageNumber": 20,
  "searchType": 3,
  "keyword": "医疗设备|病床",
  "excludeKW": "维修",
  "inCludeKW": "采购",
  "projectClassID": "-100",
  "searchMode": 1,
  "areaCode": {"proviceCodeList": ["0"], "cityCodeList": [], "countyCodeList": []},
  "industryCode": {"firstCodeList": [], "secondCodeList": [], "thirdCodeList": []},
  "purchaseTypeID": "3",
  "partAName": "",
  "partBName": "",
  "agentName": "",
  "companyName": "",
  "fileFlag": -1
}
```

### 按需补充

- `POST /outer-gateway/bid/getZTBStructreDetail`：传 `id`、`publishTime`，获取项目编号、金额、截止时间、甲乙方、代理机构和联系方式。
- `POST /outer-gateway/bid/getZTBProjectDetail`：传 `id`、`publishTime`，获取完整正文。
- `POST /outer-gateway/bid/getZTBProjectFiles`：传 `projectId`、`publishTime`，获取附件。
- `POST /outer-gateway/bid/getCollectUrl`：传 `id`、`publishTime`，获取原始采集网址。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 招中标信息搜索列表(references/search-project-api.md)
- 招中标信息结构化数据详情(references/get-ztb-structure-detail.md)
- 招中标信息正文详情(references/get-ztb-project-detail.md)
- 招中标信息附件列表(references/get-ztb-project-files.md)
- 获取招中标信息采集源网址(references/get-collect-url.md)
- 枚举值与码表(references/enums-and-code-tables.md)

## 输出格式

先输出“订阅条件”，包含查询周期、关键词逻辑、地区、分类、金额、企业条件和去重键。再输出结果表：优先级、标题、信息类型、地区、金额、发布时间、报名或开标截止时间、甲方、乙方、项目 ID、附件、来源链接、推荐理由。最后列出数据缺失、接口限制和下次执行建议。

不得把相关性判断写成确定事实；不得补写接口未返回的联系人、金额、截止日期或企业角色。
