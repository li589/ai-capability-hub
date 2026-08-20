# 通讯录

## 只读

- `jdy_get_corp_user`
- `jdy_list_departments`
- `jdy_list_dept_users`
- `jdy_list_roles`

使用成员 `username` 和部门 `dept_no`，不要仅凭重名显示名称选择目标。根部门编号通常为1，但应以在线返回为准。

`jdy_get_corp_user` 只证明接口返回的成员基础资料，不能判断该成员是普通成员、管理员或企业创建者，
也不能证明应用管理、数据管理或接口权限。本工具包没有企业管理员/创建者校验接口；没有其他可靠证据时，
必须回答“当前接口无法判断”，禁止根据姓名、部门或是否能被查询到进行推断。

## 写入

- `jdy_add_corp_user`
- `jdy_update_corp_user`
- `jdy_create_department`

先读取当前成员或父部门，预览名称、成员编号、部门编号和联系方式变更，再等待批准。

## 删除

`jdy_delete_corp_user` 是破坏性操作。删除前读取成员信息并展示 `username`、姓名和全部部门；要求确认令牌与 `--acknowledge-destructive`。
