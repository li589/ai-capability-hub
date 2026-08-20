# 员工管理

员工状态管理：列表、详情、角色、启用/关闭/离职。页面来源为 `internal-manage/staff-manage`。

## CLI 调用硬规则

1. 执行前先读 `runtime.md`；CLI 只能通过 `sh ./scripts/yc-cloud.sh <命令>` 调用，禁止 `which/find/curl` 或直连 API。
2. 只走本文件 allowlist 内的 `yc-cloud employee ...` 命令；接口路径、Controller 名、请求 DTO 都不是可执行命令。
3. 先确认 `apiKey`；读链路固定顺序 `list → detail → role-list`（写操作前必须完成）。
4. 不得凭记忆脑补任何业务 ID；`--update` 字段须来自 `detail` 响应，`roleId` 来自 `role-list` 的 `id`，不得编造。

## 命令清单

```text
yc-cloud employee list
yc-cloud employee detail
yc-cloud employee role-list
yc-cloud employee update-status
```

## Parameter Allowlist

### `employee list`

```text
yc-cloud employee list [--filters <json>] [--limit <n>] [--offset <n>] [--roles <json>] [--json] [--debug] [--quiet]
```

允许参数：`--filters --limit --offset --roles --json --debug --quiet`

接口：`POST /saas/base/baseEmployee/getEmployeeTimes`

列表关键字段：`employeeId`、`accountsId`、`employeeName`、`employeeStatus`、`accountsStatus`

### `employee detail`

```text
yc-cloud employee detail --employee-id <id> --account-id <id> [--json] [--debug] [--quiet]
```

必须参数：`--employee-id --account-id`

别名：`--employeeId`、`--accountId` 会自动归一为 kebab-case。

接口：`POST /saas/base/baseEmployee/getEmployeeInfoByIdOrAccount`

`getEmployeeById`：已废弃，禁用（生产 500）。

### `employee role-list`

```text
yc-cloud employee role-list [--filters <json>] [--limit <n>] [--offset <n>] [--order-by <json>] [--json] [--debug] [--quiet]
```

允许参数：`--filters --limit --offset --order-by --json --debug --quiet`

别名：`--order_by` → `--order-by`

默认筛选建议：`{"logic":"and","filters":[{"field":"isDeleted","op":"=","value":0}]}`

接口：`POST /saas/iam/role/getRoleList`

列表关键字段：`id`（角色 ID）、`roleCode`、`displayName`、`roleStatus`

`baseRole/getRolePage`：已废弃，禁用（生产 500）。

### `employee update-status`

```text
yc-cloud employee update-status --update <json-array> [--json] [--debug] [--quiet]
```

必须参数：`--update`（`updateEmployeeAndRole` 的 `update` 数组 JSON，不是整个 body）

接口：`POST /saas/base/baseEmployee/updateEmployeeAndRole`

`--update` 数组元素须来自 `detail` 响应，至少包含：`employeeId`、`accountsId`、`userId`（同 `userInfoId`）、`employeeName`、`employeeMobile`、`orgId`、`orgPosition`、`idType`、`idNumber`、`avatarUrl`、`accountsStatus`、`employeeStatus`、`set.userId`、`set.roleConfigs`、`where.ids`。

`set.roleConfigs` 每项：`{"roleId":<role-list.id>,"sortOrder":1,"dataScopes":[]}`；`where.ids` 无旧角色记录时可为 `[]`。

## Workflow 示例

### 员工状态管理

用户要「查员工状态」「启用/关闭员工账号」「办理离职」「查看员工角色」时，**必须**走本工作流。

**与收费网格的分工**：

- 收费网格查员工姓名：页面侧 `getEmployees` + filters（本模块无对应 CLI）
- 员工管理页查详情、改状态：**必须**用 `employee detail` / `employee update-status`
- 员工状态列表：**必须**用 `employee list`（`getEmployeeTimes`）

**状态字段口径**：

| 字段 | 值 | 含义 |
| --- | --- | --- |
| `employeeStatus` | 1 | 在职/启用 |
| `employeeStatus` | 0 | 停用 |
| `employeeStatus` | 3 | 离职/关闭 |
| `accountsStatus` | 0 | 账号停用（不可登录） |
| `accountsStatus` | 1 | 账号启用（可登录） |

「关闭账号登录」通常改 `accountsStatus`；「办理离职」通常改 `employeeStatus` 为 `3`。

**只读：查员工状态**：

1. `employee list --limit 20 --offset 0 --json` — 取 `employeeId`、`accountsId`
2. `employee detail --employee-id <id> --account-id <id> --json`

**写操作：启用/关闭/离职**（须用户明确授权）：

1. `employee list` — 定位目标员工
2. `employee detail` — 拉全量字段，作为 `--update` 来源
3. `employee role-list` — 取 `id` 填入 `roleConfigs[].roleId`
4. `employee update-status --update '[{...}]' --json` — 修改目标状态字段后提交
5. `employee detail` — 验证改前改后状态

**禁止**：

- 使用 `getEmployeeById`、`getRolePage`（已废弃，禁用）
- 省略 `roleConfigs` 或编造 `roleId`
- 用 `travel charge-person employee-times` 代替本工作流（后者属旅游模块）

## Module Guards

1. 员工状态相关链路先确认 `apiKey`；读链路固定顺序为 `list → detail → role-list`（写操作前必须完成）。
2. `employee detail` 必须同时提供 `--employee-id` 与 `--account-id`；`account-id` 来自列表字段 `accountsId`（列表无 s，详情入参无 s）。
3. `employee update-status` 的 `--update` 必须由 `detail` 响应组装，不得凭记忆拼字段；`role-list` 返回的角色主键是 `id`，写入 `roleConfigs[].roleId` 时使用该值。
4. 不得使用已废弃的 `getEmployeeById`、`getRolePage`；不得用收费网格 `getEmployees` 代替 `employee detail`。
5. 员工写操作默认高风险：无用户明确授权时只执行读命令；授权后改完须再查 `detail` 或 `list` 验证。
6. 所有操作只能通过 allowlist 内的 `yc-cloud employee ...` 命令执行。

## Stop Conditions

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中，或本地 CLI 未注册对应子命令。
2. 缺少 `employee-id`、`account-id` 等必填参数且无法可靠补齐。
3. 文档与当前源码冲突且无法以源码直接定论。
4. 员工写操作未获用户明确授权。

禁止：

- 把接口路径、Controller 名、请求 DTO 当作可执行命令。
- 用 `getEmployeeById` 代替 `employee detail`，或用相近命令硬替代未实现能力。
