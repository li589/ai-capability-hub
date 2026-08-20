# Quality Rubric

## Scoring

Every assessment must include `delivery_mode` (`full` or `degraded`), the confirmed `dependency_report_digest`, and `promised_artifacts`. Full mode requires every rich artifact. Degraded mode may omit only rich artifacts made unavailable by the confirmed dependency report; it must not reduce financial, evidence, compliance, or internal/external-separation standards.

| 维度 | 满分 |
|---|---:|
| 战略清晰度 | 10 |
| 产品与人群洞察 | 15 |
| 机制完整性 | 10 |
| 招募与运营可执行性 | 15 |
| 财务完整性 | 15 |
| Mermaid图表表达 | 10 |
| 数据可信性 | 10 |
| 合规安全 | 10 |
| 语言与阅读体验 | 5 |
| 合计 | 100 |

最低通过线为80分；原 n8n 样文基线为56分。升级输出必须同时满足：`total > 56`、`total >= 80`、`hard_failures` 为空。

## Hard failures

- `fabricated_source`：无法核实的来源、案例或统计被写成事实。
- `financial_non_closure`：价格分配不闭合。
- `incentive_over_budget`：直接佣金或总激励超过已确认预算。
- `level_count_safe_harbor`：把层级数量或货款来源表述为当然合规。
- `downline_or_recruitment_pay`：按招募、上下线关系或下线业绩计酬。
- `internal_external_leak`：外部稿泄露成本、利润、预算或内部阈值。
- `broken_or_inconsistent_diagram`：图表无法渲染或与正文数字、路径不一致。
- `delivery_contract_mismatch`：实际交付与付款前确认的 `delivery_mode` 或承诺文件清单不一致。

In degraded mode, an unavailable renderer is not a hard failure only when Mermaid source and an equivalent structured table are both delivered and the limitation is disclosed. Claiming a nonexistent rich artifact remains a hard failure.

任何硬失败均直接判定不通过，不得用总分抵消。
