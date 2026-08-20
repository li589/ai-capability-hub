---
name: guyouquan-query
description: 查询"股友圈"社区数据，覆盖 3
  类场景：搜索相关圈子、查看圈子热点内容、查看圈子热门持仓股票。当用户询问"股友圈有哪些半导体圈子"、"某板块/概念有哪些热门圈子"、"XX圈子里在讨论什么"、"这个圈子热门持仓股票有哪些"、"XX圈子大家都在买什么"等与股友圈社区相关的问题时，使用此
  skill 获取实时数据，不要依赖训练知识编造圈子名称、帖子内容或持仓数据。用户提到"股友圈"、"圈子"、"社区热点"等字眼时，也应主动触发。
version: 1.0.0
author: Ping An Securities
display_name: 平安证券股友圈查询
display_name_en: Ping An Stock Friends Circle
description_zh: 查询平安证券股友圈相关圈子、圈内热点内容和授权聚合的热门持仓股票。
description_en: Search Stock Friends Circle communities, hot posts, and
  aggregated popular holdings.
visibility: public
disable-model-invocation: true
---

# 股友圈 Skill

## 这个 Skill 做什么

查询平安证券"股友圈"社区数据，覆盖 3 类场景：搜索圈子、圈子热点内容、圈子热门持仓股票。

#### 任何时候都应该用这个 skill 实际查询，不要依赖训练知识回答圈子名称、帖子内容、热门持仓等具体信息。

## 环境准备

- 检查是否已经设置环境变量 `PINGAN_SKILL_APIKEY`（用于鉴权用的 API Key），如未设置，提示用户登录平安证券skill开放平台获取 https://stock.pingan.com/huodong/aiskill/skillPage/index.html#/
- 依赖 Python 库 `requests`。

## 基本调用格式

```bash
python scripts/get_data.py <options> [参数...]
```

## 参数一览

| options | 说明 | 必填参数 | 限制 |
|---|---|---|---|
| `search_circle` | 搜索与问题相关的圈子 | `question`、`top_k` | — |
| `hot_posts` | 查看圈子热点内容 | `question`、`top_k` | — |
| `hot_holdings` | 查看指定圈子的热门持仓股票 | `circle_id` | - |

> 建议先用 `search_circle` 找到目标圈子及其 `circle_id`，再用 `hot_holdings` 查询该圈子的热门持仓。

---

## 1. search_circle — 搜索圈子

根据问题描述，检索相关的股友圈子（例如某行业、概念、股票对应的圈子）。

**请求参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `question` | string | 用户问题，例如「半导体有哪些热门圈子」 |
| `top_k` | int | 召回数量，必填，最大支持20条 |

**返回字段**（`chunks[]`，即 `total`/`chunks` 结构）

| 字段 | 说明 |
|---|---|
| `total` | 命中结果数量（顶层字段） |
| `content_with_weight` | 检索到的圈子/内容正文，是主要可用信息 |
| `docnm_kwd` | 文档名称 |
| `similarity` / `vector_similarity` / `term_similarity` | 综合 / 向量 / 关键词相似度，可用于筛选可信结果 |
| `chunk_id` / `doc_id` | 知识块 ID / 文档 ID |
| `url` | 原始链接（可能为空） |
| `title` | 标题（可能为空） |

**调用示例**

```bash
python scripts/get_data.py search_circle --question "半导体有哪些热门圈子" --top_k 10
```

### 如用户未明确要求返回的数量，优先返回相关度最高的3条内容

---

## 2. hot_posts — 圈子热点内容

根据问题描述，检索圈子内的热门话题/帖子内容。

**请求参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `question` | string | 用户问题，例如「今天股友圈都在聊什么」 |
| `top_k` | int | 召回数量，必填，最大支持20条 |

**返回字段**

与 `search_circle` 相同的 `total`/`chunks[]` 结构（见上表），`content_with_weight` 为帖子/话题正文。

**调用示例**

```bash
python scripts/get_data.py hot_posts --question "今天半导体相关圈子都在聊什么" --top_k 10
```

### 筛选逻辑
1.优先返回近一个月内的内容
2.如果有投票，优先筛选投票数据较多的内容

---

## 3. hot_holdings — 圈子热门持仓

查询指定股友圈的热门持仓股票列表。

**请求参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `circle_id` | int | 圈子 ID，需要先通过 `search_circle` 获取，取整数部分 |

**返回字段**（`results[]`）

| 字段 | 说明 |
|---|---|
| `stockCode` / `stockName` | 股票代码 / 名称 |
| `market` | 市场标识，如 `SZ`、`SH` |
| `holdNum` | 持仓人数 |
| `dt` | 数据日期 |
| `tradeDate` | 交易日期 |
| `rzrqFlag` | 标识，无意义 |

**调用示例**

```bash
python scripts/get_data.py hot_holdings --circle_id 118
```

---

每个子命令的参数和取值范围可以直接看帮助信息：

```bash
python scripts/get_data.py search_circle -h
python scripts/get_data.py hot_holdings -h
```
