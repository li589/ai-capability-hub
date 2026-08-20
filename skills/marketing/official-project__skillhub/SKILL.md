---
name: baobiao-find-planned-projects
description: "搜索拟在建项目，获取建设单位、项目地区、正文和附件，并按业务匹配度形成提前介入清单。用于拟在建项目发现、工程前期线索、项目立项跟踪、建设单位获客、设备材料前置销售等需求。"
---

# 拟在建项目提前发现

## 目标

从拟在建信息中发现尚处于规划、备案、环评、设计或建设准备阶段的项目，为工程、设备、材料和专业服务销售提供前置线索。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 用户未给日期时默认最近 30 天，并明确标注。
- 搜索接口 `pageNumber` 不超过 50；详情接口参数名为小写 `publishtime`，附件接口参数名为 `publishTime`，不得混用。
- 拟在建搜索成功字段可能使用 `state=1`，同时检查 `subCode=0000000000`。

## 收集输入

提取行业或项目类型、设备材料关键词、地区、投资或规模偏好、时间范围、排除词、建设单位、期望结果数。用户未给关键词时不得随意选择行业，可先要求提供产品或目标项目类型。

## 执行流程

1. 构造拟在建搜索条件，关键词同时关系用空格、或关系用 `|`。
2. 调用拟在建搜索列表，读取标题、摘要、发布时间、地区和附件状态。
3. 对高匹配结果调用拟在建项目详情，提取建设单位、正文、详细地区和项目附件信息。
4. 用户需要附件时调用拟在建附件列表，保留附件名称、格式、大小、状态和下载地址。
5. 只依据标题或正文中的明确表述判断项目阶段；没有明确阶段时标记“待核实”。
6. 按产品匹配、项目阶段、地区、发布时间、建设单位明确度和附件完整度排序。
7. 输出提前介入建议，例如联系建设单位、设计单位、咨询单位或持续观察，但不得编造未出现的单位。

## 接口

### 搜索拟在建项目

`POST /outer-gateway/bid/searchNZJProjectApi`

```json
{
  "startDate": "2026-06-28 00:00:00",
  "endDate": "2026-07-28 23:59:59",
  "pageId": 1,
  "pageNumber": 20,
  "searchType": 3,
  "keyword": "医院|医疗中心",
  "excludeKW": "",
  "inCludeKW": "建设",
  "searchMode": 1,
  "areaCode": {"proviceCodeList": ["0"], "cityCodeList": [], "countyCodeList": []}
}
```

### 获取详情

`POST /outer-gateway/bid/getNZJProjectDetail`

请求体：`{"id": 11748734, "publishtime": "2026-06-07 17:07:32"}`。读取 `title`、`content`、`constructionCompany`、地区名称、`publishTime` 和 `projectFiles`。

### 获取附件

`POST /outer-gateway/bid/getNZJProjectFileList`

请求体：`{"projectId": 11748734, "projectTypeID": 2, "publishTime": "2026-06-07 17:07:32"}`。`projectTypeID` 固定为 2。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- 拟在建项目信息搜索列表(references/search-nzj-project-api.md)
- 拟在建项目详情(references/get-nzj-project-detail.md)
- 拟在建项目信息附件列表(references/get-nzj-project-file-list.md)
- 枚举值与码表(references/enums-and-code-tables.md)

## 输出格式

输出查询口径后给出项目表：优先级、项目名称、判断阶段、建设单位、地区、发布时间、项目摘要、匹配产品或服务、附件、项目 ID、跟进建议、判断依据。末尾列出“待核实字段”和可能过期、缺失或附件不可用的情况。
