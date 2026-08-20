# Editable procurement execution companion

Create this bonus `.md` file beside the HTML report for substantive procurement work. Treat it as a live operating sheet that the role owner can edit after the analysis changes.

## Purpose boundary

The HTML report is the decision record: it explains the evidence, normalization, economics, resilience, alternatives, and recommendation.

The Markdown companion is the execution record: it captures what changes next, who owns it, by when, under which release condition, and what happens if a gate fails.

Do not copy report sections, charts, long methodology, citations, or narrative into Markdown. Add a relative link to the report and summarize only what is necessary to execute.

## Route to the nearest role

| Role | Default working-file title | Role-specific core |
|---|---|---|
| Procurement manager / sourcing | `授标与谈判执行单` | allocation, target and walk-away, approval chain, negotiation package, award gates |
| Raw-material / category buyer | `采购窗口与量价行动表` | buying window, volume bands, benchmark trigger, basis risk, target and stop-loss |
| Supplier management / SQE | `供应商验证与CAPA跟踪表` | failure mode, evidence request, audit/test, CAPA, capacity proof, release gate |
| PMC / inventory | `补货与库存异常处置单` | exception item, coverage, action, quantity, required date, service-risk trigger |
| International logistics / trade | `履约方案与合规放行清单` | lane, quote validity, booking cutoff, documents, HS/origin/compliance, release gate |

When two roles are present, choose the person who owns the next irreversible action. Add one secondary view only when it changes execution.

## File contract

- Use plain Markdown only: headings, tables, checkboxes, and short notes.
- Prefer one screenful per section and a compact file over exhaustive prose.
- Use exact quantities, currencies, units, periods, tax basis, Incoterms, locations, and dates.
- Use ISO dates when possible.
- Carry `OBS`, `SRC`, `DRV`, `ASM`, and `UNK` tags from the report.
- Write `待确认` or `UNK` for missing fields. Never invent an owner, deadline, completion state, approval, or supplier commitment.
- Use `[ ]`, `[x]`, and `[!]` for pending, complete, and blocked only when supported.
- Put decision-changing assumptions in the gate table, not in a footnote.
- Link the report with a relative filename, for example `[查看完整分析](./采购分析报告.html)`.

## Required structure

```markdown
# {role-specific working-file title}

> 对应报告：[查看完整分析](./{report-filename}.html)
> 决策对象：{one line}
> 截止日期：{date or 待确认}
> 当前状态：{推进 / 有条件推进 / 暂缓 / 不推进}

## 1. 当前决策
- 建议动作：
- 生效范围：
- 关键依据：
- 最大不确定性：
- 反转条件：

## 2. 执行动作
| 状态 | 动作 | 责任人 | 截止日期 | 输入/依赖 | 完成标准 |
|---|---|---|---|---|---|
| [ ] |  | 待确认 | 待确认 |  |  |

## 3. 放行门槛
| 门槛 | 证据状态 | 责任人 | 到期 | 放行条件 | 未通过时的回退 |
|---|---|---|---|---|---|
|  | UNK | 待确认 | 待确认 |  |  |

## 4. {role-specific workboard}
{role-specific editable table}

## 5. 待确认事实
- [ ] {unknown that can change the decision}

## 6. 决策日志
| 日期 | 决策/变更 | 依据标签 | 责任人 | 下次复核 |
|---|---|---|---|---|
|  |  |  | 待确认 |  |
```

## Role-specific workboard

### Procurement manager / sourcing

`方案/供应商 | 建议份额 | 目标条件 | 退让边界 | 谈判筹码 | 审批/合同状态 | 下一动作`

### Raw-material / category buyer

`物料 | 采购窗口 | 数量区间 | 目标价/基差 | 触发指标 | 止损/改采条件 | 下一复核`

### Supplier management / SQE

`供应商/料号 | 失效模式 | 所需证据 | 验证动作 | CAPA节点 | 产能证明 | 放行状态`

### PMC / inventory

`物料/SKU | 当前覆盖 | 风险日期 | 建议动作 | 建议数量 | 到货要求 | 例外责任人`

### International logistics / trade

`方案/航线 | 报价有效期 | 订舱/截关 | 单证 | HS/原产地 | 合规门槛 | 备选方案`

## Acceptance

1. The file is materially editable and useful after the report is delivered.
2. It names actions, owners, dates, gates, triggers, fallbacks, and the next review where known.
3. It does not reproduce the report's prose, charts, or methods.
4. Every unknown remains visible.
5. Role-specific fields match the next decision owner.
6. Terms, figures, and evidence states agree with the HTML report and Dynamic UI.
