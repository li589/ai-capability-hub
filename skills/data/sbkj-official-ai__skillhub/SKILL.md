---
name: baobiao-search-bids-ai
description: "把用户的自然语言招投标需求改写为时间、关键词、企业、地区和行业条件，再调用 AI 专用搜索接口返回高相关项目。用于不会写检索式、复杂自然语言找标、智能查招标、按业务描述搜索项目和解释搜索条件。"
---

# AI 招投标智能搜索

## 目标

允许用户直接用自然语言描述需求，先获得结构化搜索条件，再执行招投标搜索并解释结果为何匹配。

## ⭐ API Key 获取与使用

按以下顺序处理：

1. 从环境变量 `BBIAO_API_KEY` 读取密钥，命中后直接使用。
2. 使用环境变量 `BBIAO_SERVER_URL` 覆盖服务地址；未配置时使用 `https://gate.gov-bid.com`。
3. 未找到 `BBIAO_API_KEY` 时停止接口调用，提示用户访问https://apiyx.gov-bid.com/?share=eyJjb2RlIjoic2Jrai0wMG1ibGJlZyJ9 获取 Key，也可联系世舶科技商务人员获取并配置密钥。
4. ☎️ **商务联系方式：张瑛 18986107388**

不得自动注册、自动创建账号或猜测密钥。不得在回答、日志摘要、错误信息和示例中回显真实密钥。

## 调用约定

- 使用 UTF-8 JSON `POST`。
- 用户未给日期且 AI 改写结果也无日期时，默认最近 30 天并明确说明。
- AI 专用搜索 `pageNumber` 不超过 100。
- AI 推理结果是搜索辅助条件，不是事实。向用户展示最终采用的时间、关键词、地区、企业和行业条件。

## 执行流程

1. 接收用户自然语言查询，保留原句。
2. 调用“AI 重写招中标信息搜索条件”，获取搜索短语、同义词、甲方、乙方、代理机构、发布机构、行业编码和地区编码。
3. 如果运行环境已安装 `bbiao-search` CLI，优先执行 `bbiao-search rewrite-query --query "<原始查询>" --wait --json`，由 CLI 处理轮询。
4. 如果直接 HTTP 调用只返回 `processing` 和 `requestKey`，但当前运行环境没有已定义的轮询方式，不得猜测轮询请求体；返回当前状态，或改用可直接执行的 AI 专用搜索条件。
5. 将人类可读的条件映射到 AI 专用搜索接口：日期、关键词、排除词、必含词、信息类别、地区名称和企业名称。
6. 调用 AI 专用搜索，按相关度和时效排序；用户要求完整字段时再调用结构化详情。
7. 输出“原始需求、AI 解析、最终条件、搜索结果、调整建议”。结果过少时放宽一项条件，结果过多时收紧一项条件，并明确调整内容。

## 接口

### 自然语言改写

`POST /outer-gateway/bid/aiSearchSubmitPolling`

首次提交请求体：`{"userQuery": "最近一个月武汉医院采购的病床项目"}`。关注 `requestKey`、`status`、`searchCondition`、`industryCodes`、`areaCode` 和 `errorMsg`。完成状态为 `completed`，失败状态为 `failed`。

### AI 专用搜索

`POST /outer-gateway/bid/SearchProjectForAI`

```json
{
  "startDate": "2026-06-28",
  "endDate": "2026-07-28",
  "pageId": 1,
  "pageNumber": 20,
  "keyword": "病床|医疗床",
  "excludeKW": "维修",
  "inCludeKW": "采购",
  "className": "招标信息,采购意向",
  "areaName": "武汉",
  "companyName": ""
}
```

读取标题、信息类别、发布时间、正文摘要、地区、相关度、金额、项目分类、采购分类、甲乙方、代理机构、报名截止、开标时间、原始采集网址和世舶项目地址。

### 详情补充

`POST /outer-gateway/bid/getZTBStructreDetail`，传 `id` 与 `publishTime`，补充项目编号、预算、中标金额、联系人和截止时间。

## 搜索调整规则

- 结果为 0：先移除排除词，再放宽地区，再减少必含词；每次只调整一类条件。
- 结果过多：增加必含词、缩短日期、限定信息类别或企业名称。
- 同义词扩展必须与用户业务语义一致，并在条件摘要中展示。
- 不把 AI 生成的公司名、地区或行业编码当成用户已确认信息。

## 详细接口参数

执行对应接口前按需读取：

- 完整接口总说明(references/Parameter-Description.md)
- AI 重写招中标信息搜索条件(references/ai-search-submit-polling.md)
- AI/Agent 专用招中标搜索(references/search-project-for-ai.md)
- AI 行业搜索(references/industry-reasoning.md)
- 招中标信息结构化数据详情(references/get-ztb-structure-detail.md)

## 输出格式

先输出 AI 解析条件表，再输出结果表：相关度、标题、类型、地区、金额、甲方、乙方、发布时间、截止时间、来源链接、匹配解释。最后提供可直接复用的搜索语句和一至三条精炼建议。
