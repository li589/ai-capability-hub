# 工具索引

共39项操作。运行 `scripts/jdy tool-help <工具名>` 查看完整参数。

| 工具 | 名称 | 领域 | 风险 |
|---|---|---|---|
| `jdy_get_form_widgets` | 查询表单字段结构 | 应用与表单 | 只读 |
| `jdy_list_apps` | 查询应用列表 | 应用与表单 | 只读 |
| `jdy_list_forms` | 查询表单列表 | 应用与表单 | 只读 |
| `jdy_batch_create_data` | 批量新建数据 | 数据 | 写入 |
| `jdy_batch_delete_data` | 批量删除数据 | 数据 | 破坏性 |
| `jdy_batch_update_data` | 批量修改数据 | 数据 | 写入 |
| `jdy_create_data` | 新建单条数据 | 数据 | 写入 |
| `jdy_delete_data` | 删除单条数据 | 数据 | 破坏性 |
| `jdy_get_data` | 查询单条数据 | 数据 | 只读 |
| `jdy_get_upload_token` | 获取文件上传凭证 | 数据 | 只读 |
| `jdy_list_data` | 查询多条数据 | 数据 | 只读 |
| `jdy_list_data_2` | 查询表单数据（带 filter 校验版） | 数据 | 只读 |
| `jdy_update_data` | 修改单条数据 | 数据 | 写入 |
| `jdy_activate_flow_instance` | 激活流程实例 | 流程 | 写入 |
| `jdy_back_flow_task` | 流程待办回退 | 流程 | 破坏性 |
| `jdy_end_flow_instance` | 终止流程实例 | 流程 | 破坏性 |
| `jdy_get_flow_approval_comments` | 查询流程审批意见 | 流程 | 只读 |
| `jdy_get_flow_instance` | 查询流程实例信息 | 流程 | 只读 |
| `jdy_get_flow_logs` | 查询流程日志 | 流程 | 只读 |
| `jdy_query_cc_list` | 查询抄送列表 | 流程 | 只读 |
| `jdy_query_my_tasks` | 查询待办任务 | 流程 | 只读 |
| `jdy_sign_flow_task` | 流程待办加签 | 流程 | 写入 |
| `jdy_submit_flow_task` | 流程待办提交 | 流程 | 写入 |
| `jdy_transfer_flow_task` | 流程待办转交 | 流程 | 写入 |
| `jdy_veto_flow_task` | 流程待办否决 | 流程 | 破坏性 |
| `jdy_withdraw_flow_task` | 流程待办撤回 | 流程 | 写入 |
| `jdy_get_app_usage_metrics` | 获取应用资源用量统计 | 用量与审计 | 只读 |
| `jdy_get_audit_log_domains` | 获取审计日志类型定义 | 用量与审计 | 只读 |
| `jdy_get_corp_usage_overview` | 获取平台资源用量统计 | 用量与审计 | 只读 |
| `jdy_get_member_usage_metrics` | 获取成员资源用量统计 | 用量与审计 | 只读 |
| `jdy_list_audit_logs` | 获取审计日志明细 | 用量与审计 | 只读 |
| `jdy_add_corp_user` | 添加成员 | 通讯录 | 写入 |
| `jdy_create_department` | 创建部门 | 通讯录 | 写入 |
| `jdy_delete_corp_user` | 删除成员 | 通讯录 | 破坏性 |
| `jdy_get_corp_user` | 获取成员信息 | 通讯录 | 只读 |
| `jdy_list_departments` | 获取部门列表 | 通讯录 | 只读 |
| `jdy_list_dept_users` | 获取部门成员 | 通讯录 | 只读 |
| `jdy_list_roles` | 列出角色 | 通讯录 | 只读 |
| `jdy_update_corp_user` | 修改成员 | 通讯录 | 写入 |

写入操作默认只返回预览；破坏性操作还需要显式确认参数。
