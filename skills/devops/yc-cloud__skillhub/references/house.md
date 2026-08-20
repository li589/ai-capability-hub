# 客户房屋 CRM

房屋与租客管理：项目树、客户列表/详情、产权关系、业主/租客新增与客户信息编辑。

## CLI 调用硬规则

1. 执行前先读 `runtime.md`；CLI 只能通过 `sh ./scripts/yc-cloud.sh <命令>` 调用，禁止 `which/find/curl` 或直连 API。
2. 只走本文件 allowlist 内的 `yc-cloud house ...` 命令；接口路径、Controller 名、请求 DTO 都不是可执行命令。
3. 先确认 `apiKey` 再执行写链路；写操作前后用 `owner-renter-list` / `customer-detail` 检查与验证现状。
4. 不得凭记忆脑补任何业务 ID（`house-id`、客户 `id` 等）；`limit/offset` 用非负整数。

## 命令清单

```text
yc-cloud house project-tree
yc-cloud house customer-list
yc-cloud house relation-list
yc-cloud house customer-detail
yc-cloud house customer-update
yc-cloud house customer-create
yc-cloud house relation-create
yc-cloud house owner-renter-list
```

## Parameter Allowlist

### `house project-tree`

```text
yc-cloud house project-tree [--filters <json>] [--json] [--debug]
```

允许参数：`--filters --json --debug`

用途：查询租户项目树，从返回的 `result`（含 `children` 嵌套）中定位目标房屋的 `houseId`。

对应接口：`POST /saas/base/baseHouse/getTenantProjectTree`

### `house customer-list`

```text
yc-cloud house customer-list [--project-id <ids>] [--house-id <ids>] [--customer-name <name>] [--mobile <mobile>] [--filters <json>] [--params <json>] [--order-by <json>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --house-id --customer-name --mobile --filters --params --order-by --limit --offset --json --debug`

用途：按项目、房屋或姓名/手机号分页查询客户，获取 `id`（即 `userCustomerId`）。

对应接口：`POST /saas/base/queryUserCustomerPageList`

按项目查询示例：

```text
yc-cloud house customer-list --project-id 6070517275140001 --json
```

按姓名模糊查询示例：

```text
yc-cloud house customer-list --filters '{"logic":"and","filters":[{"field":"userName","op":"like","value":"张三"}]}' --json
```

### `house relation-list`

```text
yc-cloud house relation-list [--project-id <ids>] [--node-type <types>] [--real-short-name <name>] [--user-ids <ids>] [--property-type <n>] [--real-path <path>] [--filters <json>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --node-type --real-short-name --user-ids --property-type --real-path --filters --limit --offset --json --debug`

用途：分页查询房屋/车位产权关系列表。默认 `nodeType` 为 `5,9,10`（房屋/车位/虚拟车位）。

对应接口：`POST /saas/base/baseUserHouseRelation/getHouseUserRelationPage`

按项目查询示例：

```text
yc-cloud house relation-list --project-id 6070516463300001 --json
```

### `house customer-detail`

```text
yc-cloud house customer-detail --filters <json> [--limit <n>] [--json] [--debug]
```

必须参数：`--filters`（按客户 `id` 精确查询）

用途：按客户 ID 查询完整客户信息（姓名、手机号、证件、备注等），编辑前用于确认现状。

对应接口：`POST /saas/base/queryUserCustomerDetails`

按客户 ID 查询示例：

```text
yc-cloud house customer-detail --filters '{"logic":"and","filters":[{"field":"id","op":"=","value":6051815581990001}]}' --json
```

### `house customer-update`

```text
yc-cloud house customer-update --update <json> [--json] [--debug]
```

必须参数：`--update`（JSON 数组，外层由 CLI 自动包装为 `{"update":[...]}`）

`update` 单条常用字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 客户 ID（必填，用于定位待编辑客户） |
| `userName` | 客户姓名（可选，传则更新） |
| `mobile` | 手机号（可选，传则更新） |
| `idNumber` | 证件号码（可选） |
| `remark` | 备注（可选） |

对应接口：`POST /saas/base/setUserCustomer`

更新姓名与手机号示例：

```text
yc-cloud house customer-update --update '[{"id":6051815581990001,"userName":"李四","mobile":"13800138002"}]' --json
```

### `house customer-create`

```text
yc-cloud house customer-create --insert <json> [--json] [--debug]
```

必须参数：`--insert`（JSON 数组，外层由 CLI 自动包装为 `{"insert":[...]}`）

`insert` 单条常用字段：

| 字段 | 说明 |
| --- | --- |
| `userName` | 客户姓名（必填） |
| `userType` | `1`=个人，`2`=企业 |
| `idType` | 证件类型，`1`=身份证 |
| `idNumber` | 证件号码 |
| `mobile` | 手机号 |

对应接口：`POST /saas/base/createUserCustomer`

### `house relation-create`

```text
yc-cloud house relation-create --insert <json> [--json] [--debug]
```

必须参数：`--insert`（JSON 数组，外层由 CLI 自动包装为 `{"insert":[...]}`）

`insert` 单条常用字段：

| 字段 | 说明 |
| --- | --- |
| `houseId` | 房屋 ID（必填，来自项目树或客户列表） |
| `relationType` | `"1"`=业主，`"2"`=租客，`"3"`=亲属 |
| `parentId` | 业主/租客填 `0`；亲属填关联业主的客户 ID |
| `userName` | 客户姓名 |
| `userType` | `1`=个人，`2`=企业 |
| `idType` | 证件类型 |
| `idNumber` | 证件号码 |
| `mobile` | 手机号 |
| `baseUserCustomerId` | 可选；关联已有客户时传入其 `id` |

对应接口：`POST /saas/base/createUserHouseRelation`

新增租客示例：

```text
yc-cloud house relation-create --insert '[{"parentId":0,"houseId":6061619070640002,"relationType":"2","userName":"张三","userType":1,"idType":1,"idNumber":"420000199001011234","mobile":"13800138000"}]' --json
```

### `house owner-renter-list`

```text
yc-cloud house owner-renter-list [--filters <json>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--filters --limit --offset --json --debug`

用途：查询指定房屋已有业主/租客；新增前后用于检查与验证。

按 `houseId` 查询示例：

```text
yc-cloud house owner-renter-list --filters '{"logic":"and","filters":[{"field":"houseId","op":"=","value":6061619070640002}]}' --json
```

对应接口：`POST /saas/base/queryHouseOwnerRenterList`

与 `collection billing list-changeable-payers` 的区别：后者仅用于**变更缴款人**场景下的只读查询，不能新增业主/租客。

## Workflow 示例

### 房屋与租客管理

用户要「为某房间添加租客 / 业主」「客户入住」「挂产权关系」时，**必须**走本工作流；**不得**声称只能后台手工添加，也不得用 `collection import house-relation`（批量 Excel 导入）代替单条新增。

**与只读查询命令的分工**：

- `house owner-renter-list`：查房屋已有业主/租客（写操作前后检查）
- `collection billing list-changeable-payers`：仅用于变更缴款人前的候选列表，**不能**新增关系
- `collection billing list-house-customers` / `list-house-relations`：账单调整场景的只读核对，**不能**新增关系

**标准步骤（客户已存在）**：

1. 定位房屋：`house project-tree --json`，从树形 `result.children` 递归找到目标房间 `houseId`；若用户给了房号全称，也可先用 `house customer-list` 按 `realShortName` 反查 `houseId`
2. 检查现状：`house owner-renter-list --filters '{"logic":"and","filters":[{"field":"houseId","op":"=","value":<houseId>}]}' --json`
3. 查客户：`house customer-list --filters '{"logic":"and","filters":[{"field":"userName","op":"like","value":"<姓名>"}]}' --json`，取 `id` 作为 `baseUserCustomerId`
4. 创建关系：`house relation-create --insert '[{...}]' --json`；关联已有客户时在 `insert` 中传 `baseUserCustomerId`，并补齐 `userName` / `mobile` 等字段
5. 验证：`house owner-renter-list` 再次查询，确认新租客/业主已出现

**标准步骤（客户不存在，先建客户再挂房）**：

1. 同上做步骤 1–2 定位房屋并检查现状
2. `house customer-create --insert '[{"userName":"...","userType":1,"idType":1,"idNumber":"...","mobile":"..."}]' --json`
3. `house relation-create --insert '[{"parentId":0,"houseId":<id>,"relationType":"2","userName":"...","userType":1,"idType":1,"idNumber":"...","mobile":"..."}]' --json`
4. `house owner-renter-list` 验证

**关系类型口径**：

| `relationType` | 含义 |
| --- | --- |
| `"1"` | 业主 |
| `"2"` | 租客 |
| `"3"` | 亲属/联系人 |

**失败处理**：

- 若返回 500 且提示权限不足，说明当前 `apiKey` 无客户/房屋关系写权限，应提示更换具备项目管理权限的 key，而不是改猜其他接口
- 不得回退到杜撰的 `createHouse` 仅房间节点接口冒充「添加业主/租客」

### 客户信息查询与编辑

用户要「查客户信息」「改客户姓名」「改手机号」「编辑业主资料」时，**必须**走本工作流；不得声称只能后台手工修改。

**标准步骤**：

1. 定位客户：`house customer-list --filters '{"logic":"and","filters":[{"field":"userName","op":"like","value":"<姓名>"}]}' --json`；已知手机号时可按 `mobile` 字段 `=` 精确过滤
2. 从列表取目标客户 `id`（即 `userCustomerId`）
3. 确认详情：`house customer-detail --filters '{"logic":"and","filters":[{"field":"id","op":"=","value":<id>}]}' --json`
4. 提交更新：`house customer-update --update '[{"id":<id>,"userName":"<新姓名>","mobile":"<新手机号>"}]' --json`；只传需要变更的字段
5. 验证：`house customer-detail` 再次查询，确认字段已更新

**与只读查询命令的分工**：

- `collection billing list-customers`：账单调整场景的轻量客户列表，**不能**编辑客户
- `house customer-list` / `customer-detail`：客户管理场景的查询入口
- `house customer-update`：客户基本信息写操作（姓名、手机号等）

## Module Guards

1. 先确认 `apiKey` 再执行写链路。
2. 用户要「添加租客 / 添加业主 / 新增客户并挂到房屋」时，必须走 `house` 模块；不得用 `collection import *` 或 `billing list-changeable-payers` 代替写操作。
3. `house relation-create` / `house customer-create` 的请求体必须使用 `insert` 数组包装；`relationType` 取值为字符串 `"1"`（业主）、`"2"`（租客）、`"3"`（亲属），不是 `OWNER` / `RENTER`。
4. 所有操作只能通过 allowlist 内的 `yc-cloud house ...` 命令执行。

## Stop Conditions

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中，或本地 CLI 未注册对应子命令。
2. 缺少 `house-id`、客户 `id` 等必填参数且无法可靠补齐。
3. 文档与当前源码冲突且无法以源码直接定论。

禁止：

- 把接口路径、Controller 名、请求 DTO 当作可执行命令。
- 用 `import house-relation` 代替单条新增租客，或用只读查询命令冒充写操作。
- 回退到杜撰的 `createHouse` 接口冒充「添加业主/租客」。
