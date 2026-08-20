# 数据与文件

## 读取

- `jdy_get_data`：按 `_id` 读取单条记录。
- `jdy_list_data`：无筛选或游标分页读取。
- `jdy_list_data_2`：带筛选校验的推荐查询入口。

`limit=100` 且首次不传 `data_id` 时自动全量分页；使用 `max_records` 控制大表规模。保留 `_id`、`updateTime` 和用户要求的业务字段。

## 写入

- `jdy_create_data`、`jdy_batch_create_data`
- `jdy_update_data`、`jdy_batch_update_data`
- `jdy_delete_data`、`jdy_batch_delete_data`

所有写入先预览。更新单条记录必须用刚读取到的 `updateTime` 执行并在成功后回读。批量修改不支持子表单。批量接口最多100条。

新建单条数据必须提供 `duplicate_check_filter`；批量新建必须提供与 `data_list`
一一对应的 `duplicate_check_filters`。脚本在实际创建前执行精确查重，发现已有记录即停止。
只有用户明确接受重复风险时，才能改用 `allow_duplicate=true` 重新预览和确认；禁止由 Agent
自行放宽。查重条件应优先使用表单的业务唯一键，不要用易变的显示字段代替。

删除属于破坏性操作，除确认令牌外还需要 `--acknowledge-destructive`。

## 文件

`jdy_get_upload_token` 获取上传URL和令牌。上传凭证与 `transaction_id` 有效期有限；创建或更新含附件记录时必须使用同一个UUID。

## 触发器

默认 `is_start_trigger=false`、`is_start_workflow=false`。只有用户明确要求时才启用。
