---
name: westock-finsearch
description: 金融领域信息搜索工具，通过关键词列表搜索金融新闻、研报、公告正文、政策文本和事件证据，也支持文档 ID 精确查询。专为金融场景优化，用于补充新闻影响、研报观点、公告原文和政策证据；行情、估值、财报、资金等结构化数字转 westock-data，条件选股/排行转 westock screen，估值判断转 westock-valuation，财报分析转 westock-financials，盘面资金/事件转 westock-radar。
---

# Fin Search · 金融信息搜索

本文件是 Skill 使用说明，不要 `source` 本文件。

## 用法

**调用方式**：`node <本SKILL.md所在目录>/scripts/index.js query <关键词组或文档ID>...`

- `<本SKILL.md所在目录>` = 本文件所在目录（解析为绝对路径后直接执行）
- 下文 `westock-finsearch query ...` 是同一调用的简写
- **每个任务 `--help` 至多 1 次**（不确定参数时先查本文「高频命令速查」，再决定是否 `--help`）
- **唯一子命令**为 `query`；**禁止**臆造 `search`、`doc` 等变体
- nodejs ≥ 18，无需 `npm install`，需网络
- **禁止** `cd <目录> && node scripts/index.js ...`、`which`/`find`/`ls` 探路径

## 高频命令速查

```bash
node <本SKILL.md所在目录>/scripts/index.js query "doc id1" "doc id2"                          # 文档 ID 精确查
node <本SKILL.md所在目录>/scripts/index.js query "北向资金 净买入" "恒生科技指数 走势"          # 多角度同轮
```

- 每个引号参数是一组关键词，或一个文档 ID；关键词与文档 ID 可混在同一次 `query` 中。

## 路由规则

| 用户意图 | 处理方式 |
|---|---|
| 金融新闻、研报、公告正文、政策文本、事件证据搜索 | 使用 `westock-finsearch query` |
| 结果中出现需展开正文的资讯详情链接（`gu.qq.com` / `finance.qq.com`） | 转 `news-sharing` 提取正文，不要直接网页抓取 |
| 行情、估值、财务、资金等结构化数字 | 转 `westock-data`，禁止用搜索结果替代 |
| 条件选股、候选池构建 | 转 `westock screen condition` |
| 排行榜、TOP/评分榜 | 转 `westock screen ranking` |
| 单股估值判断 | 转 `westock-valuation`；本 Skill 只提供正文证据 |
| 财报分析 / 财报排雷 | 转 `westock-financials`；本 Skill 只提供正文证据 |
| 资金面 / 事件雷达 | 转 `westock-radar`；本 Skill 只提供正文证据 |

本 Skill 无外部 reference 文件；命令、关键词与返回格式均在本文件维护。

## 关键词与输出

- 一次传入 **1～5 组**关键词，每组 **2～5 个**核心词（空格分隔的自然语言短语），例如 `"腾讯控股 南向资金"`、`"贵州茅台 业绩 分红"`。
- **多角度**放在同一次 `query`：`westock-finsearch query "北向资金 净买入" "恒生科技指数 走势"`。
- 文档 ID 作为其中一组传入：`westock-finsearch query "doc id1"`。
- 首次结果为空或明显不足时，**最多换 1 次**角度重试；仍为空就如实说明「未检索到相关结果」。
- 多个关键词组**必须一次传入**，不要拆成多次串行；与其它不依赖检索结果的查询可在**同轮并发**。
- 每组只读前 **3～5 条**高相关摘要；输出只引用标题、来源、时间和核心事实，**不要复制大段正文**（避免上下文膨胀）。
- 初次检索可用 **1-5 组**覆盖主要角度；整理输出时**最后压缩至 1-3 组**核心结论，能用更少组数覆盖问题时优先减少组数。
- `WZQ_APIKEY` 由运行环境注入，不要在回复中要求用户提供或展示。

| 场景 | keywords 示例 |
|------|--------------|
| 个股新闻 | `["腾讯控股 最新消息"]` |
| 财报解读 | `["贵州茅台 业绩 分红"]` |
| 宏观数据 | `["中国 CPI 通胀"]` |
| 行业趋势 | `["人工智能 算力 芯片"]` |
| 资金流向 | `["北向资金 净买入"]` |
| 政策解读 | `["两会 政府工作报告 资本市场"]` |
| 热点事件 | `["地缘风险 原油 黄金 避险"]` |
| 多角度搜索 | `["腾讯控股 南向资金", "腾讯控股 业绩 增长"]` |
| 文档 ID 查询 | `["doc id1", "doc id2"]` |

## 返回格式

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "content": "<text_content>\n【文章 1/N】\n标题: ...\n来源: ...\n时间: ...\n相关性评分: ...\n内容: ...\n</text_content>\n\n<tool_content>\n【API工具 1/M】\n标题: ...\n相关性评分: ...\n内容: ...\n</tool_content>"
  }
}
```

- `code`: 0 表示成功
- `data.content`：`<text_content>` 为文章/资讯列表；`<tool_content>` 为 API 工具数据（不一定每次都有）
- `data.content` 为空表示无匹配；按上文规则最多换 1 次角度重试
