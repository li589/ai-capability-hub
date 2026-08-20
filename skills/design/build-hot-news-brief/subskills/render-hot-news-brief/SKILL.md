---
name: render-hot-news-brief
description: 将内存中的最终新闻、短总结和已启用专业提示直接渲染到当前对话，每条包含可点击标题和原文链接。仅由
  build-hot-news-brief 在 analyzed 阶段执行；不搜索、不运行脚本、不创建报告文件。
disable-model-invocation: true
---

# 推送热点快报

## Mission

在当前对话一次性交付客户可直接阅读的短快报。

## When to use

- 新闻选择、总结及可选专业分析完成后执行。
- `news_list` 不输出决策或选题段落。

## Hard constraints

- 只组合已验证的内存内容，不新增新闻、事实、指标或URL。
- 每条新闻固定为 `序号. [标题](HTTP(S)原文URL) — 来源 · YYYY-MM-DD`。
- 标题、链接、来源和日期必须来自同一真实记录。
- 不回复文件路径、附件位置或“报告已生成”。

## Core workflow

按标题、模式、短总结、关键新闻、可选专业提示和检索审计排序；发送前核对新闻数与标题链接数一致，然后直接回复。

## Output format

只输出当前对话Markdown。0条时明确写“近7天未发现合格新闻”。

## Done criteria

- 新闻最多10条，每条都有可点击标题和HTTP(S)原文链接。
- 回复简短、完整且不含凭证、文件引用或虚构指标。
- 最终状态为 `delivered`。
