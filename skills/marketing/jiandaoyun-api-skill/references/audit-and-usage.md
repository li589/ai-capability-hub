# 用量与审计

## 用量

- `jdy_get_corp_usage_overview`：企业维度汇总。
- `jdy_get_app_usage_metrics`：应用维度明细。
- `jdy_get_member_usage_metrics`：成员维度明细。

统计日期不能晚于前一天，并受接口可查询时间范围限制。分页查询时保留日期、筛选条件、`skip`和`limit`。

## 审计

1. 用 `jdy_get_audit_log_domains` 获取当前企业可查询的范围和事件类型。
2. 用 `jdy_list_audit_logs` 按 `domain`、事件、时间范围和操作人筛选。
3. 按返回游标继续分页，不要猜测事件类型。

审计可见性取决于企业版本、API权限和成员权限。API Key能列出应用不代表具备审计权限。
