---
name: analyze-decision-brief
description: 在内存中只基于最终入选新闻生成最多3条有真实证据的企业决策提示。仅由 build-hot-news-brief 在
  decision_brief 或 both 模式执行；不搜索、不运行脚本、不使用淘汰候选。
disable-model-invocation: true
---

# 分析企业决策信号

## Mission

把新闻事实转为保守、可追溯的影响、机会风险和建议动作。

## When to use

- 仅在 `decision_brief` 或 `both` 模式执行。
- 最终新闻集合确定后执行。

## Hard constraints

- 每项必须绑定最终新闻中的真实证据，重要事实优先使用官方或主流行业来源。
- 不虚构数字、因果、市场份额或确定性预测。
- 不建议不可逆动作；使用核验、评估、跟踪式动作。

## Core workflow

识别最多3个不同变化，说明影响对象、机会或风险，并给出可验证的下一步。

## Output format

每项包含变化、影响对象、机会或风险、建议动作及证据编号。

## Done criteria

- 最多3项，证据全部来自最终新闻。
- 证据不足时减少项目，不补写。
