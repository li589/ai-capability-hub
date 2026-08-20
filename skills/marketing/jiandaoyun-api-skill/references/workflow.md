# 流程

## 只读查询

- `jdy_query_my_tasks`：查询成员待办。
- `jdy_query_cc_list`：查询抄送。
- `jdy_get_flow_instance`：查询流程实例状态。
- `jdy_get_flow_logs`：查询流程日志。
- `jdy_get_flow_approval_comments`：查询审批意见。

先查询任务和实例，精确取得 `username`、`instance_id`、`task_id` 和节点信息。

## 状态变更

- `jdy_submit_flow_task`：审批通过。
- `jdy_transfer_flow_task`：转交。
- `jdy_sign_flow_task`：加签。
- `jdy_withdraw_flow_task`：撤回。
- `jdy_activate_flow_instance`：激活已终止实例。

这些操作必须先预览并等待用户针对具体实例批准。

转交参数必须使用官方字段 `transfer_username`。加签没有默认类型；必须先向用户说明
`before`（前加签）与 `after`（后加签）的流程差异，并取得明确选择，禁止代替用户推断。

## 破坏性流程操作

- `jdy_back_flow_task`：回退到此前节点。
- `jdy_end_flow_instance`：终止实例。
- `jdy_veto_flow_task`：否决并终止流程。

执行前同时核对操作人、实例、任务、目标节点和意见。除确认令牌外，还必须传 `--acknowledge-destructive`。超时后先查询实例与日志，不要自动重试。
