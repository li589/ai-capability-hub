# 应收账务

应收欠费与入账、收款报表、数据中心报表、收费订单、账单缴款人变更、基础资料导入、多业态营收。

## CLI 调用硬规则

1. 执行前先读 `runtime.md`；CLI 只能通过 `sh ./scripts/yc-cloud.sh <命令>` 调用，禁止 `which/find/curl` 或直连 API。
2. 只走本文件 allowlist 内的 `yc-cloud collection ...` / `yc-cloud rebate ...` 命令；接口路径、Controller 名、请求 DTO 都不是可执行命令。
3. 先确认 `apiKey` 再执行收费链路；用户只给项目名称时先用 `sms-task list-projects` 或 `receivable project-tree` 解析 `project-id`。
4. 不得凭记忆脑补任何业务 ID（`project-id`、`house-id`、`subject-id`、`charge-id`、`receivable-account-detail-id`、`new-customer-id` 等）；`limit/offset` 用非负整数，`detail-type` / `payment-method` 只用当前实现支持的枚举。

## 命令清单

```text
yc-cloud collection receivable arrears-list
yc-cloud collection receivable create-account
yc-cloud collection receivable approve-account
yc-cloud collection receivable list-accounts
yc-cloud collection receivable account-details
yc-cloud collection receivable project-tree
yc-cloud collection receivable house-list
yc-cloud collection receivable subject-tree
yc-cloud collection receive-payment-report detail
yc-cloud collection receive-payment-report summary
yc-cloud collection receive-payment-report summary-by-pay-method
yc-cloud collection receive-payment-report summary-by-due-date
yc-cloud collection report arrears-detail
yc-cloud collection report collection-rate
yc-cloud collection report prepaid-balance
yc-cloud collection report deposit-balance
yc-cloud collection charge-order list
yc-cloud collection charge-order correct
yc-cloud collection charge-order cancel
yc-cloud collection charge-order refund-apply
yc-cloud collection charge-order refund-audit
yc-cloud collection charge-order refund-list
yc-cloud collection billing find-detail
yc-cloud collection billing list-customers
yc-cloud collection billing list-house-relations
yc-cloud collection billing list-changeable-payers
yc-cloud collection billing list-house-customers
yc-cloud collection billing list-customer-houses
yc-cloud collection billing change-payer
yc-cloud collection import house-relation
yc-cloud collection import parking-relation
yc-cloud collection import customer
yc-cloud rebate multi-business list
```

## Parameter Allowlist

### `receivable arrears-list`

```text
yc-cloud collection receivable arrears-list --project-id <ids> [--house-id <ids>] [--charge-subject-id <ids>] [--cost-date-from <date>] [--cost-date-to <date>] [--due-date-from <date>] [--due-date-to <date>] [--user-customer-id <id>] [--house-name <keyword>] [--user-name <keyword>] [--charge-subject-name <keyword>] [--cost-status <statuses>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`

跨域说明：查询单客户完整收银台欠费明细走 `checkout-desk list-arrears`（见 [collection.md](collection.md)）；欠费统计（筛选/汇总/排行）走 [list-query.md](list-query.md)。

### `receivable create-account`

```text
yc-cloud collection receivable create-account --input <path> [--json] [--debug]
yc-cloud collection receivable create-account --project-id <id> --house-ids <ids> --subject-ids <ids> --account-time <YYYY-MM~YYYY-MM> [--json] [--debug]
```

必须参数：`--input`（透传 JSON 文件），或全部结构化参数 `--project-id --house-ids --subject-ids --account-time`（二选一，不可混用）

结构化模式校验：`project-id`、`house-ids`、`subject-ids` 只接受大于 0 的整数；`account-time` 必须是合法且起始月份不晚于结束月份的 `YYYY-MM~YYYY-MM`。对应当前弹窗接口 `POST /saas/charge/receivable/receivableAccount`；不得改用场景资料中的旧入口 `/createReceivable`。

### `receivable approve-account`

```text
yc-cloud collection receivable approve-account --input <path> [--json] [--debug]
yc-cloud collection receivable approve-account --receivable-id <id> --audit-status <2|3> [--audit-opinion <text>] [--json] [--debug]
```

必须参数：`--input`（请求体 JSON 文件），或 `--receivable-id --audit-status`（二选一，不可混用）。结构化模式中 `--receivable-id` 必须是大于 0 的整数，`--audit-status` 只接受 `2`（通过）或 `3`（驳回）；驳回时必须提供非空 `--audit-opinion`。

结构化请求体为 `{update:[{receivableAccountId, auditStatus, auditOpinion, receivableSource:3}]}`，其中 `--receivable-id` 映射 `receivableAccountId`，应收入账来源固定为 `3`。

### `receivable list-accounts`

```text
yc-cloud collection receivable list-accounts [--project-id <ids>] [--account-time <YYYY-MM|YYYY-MM~YYYY-MM>] [--subject-ids <ids>] [--audit-status <0|1|2|3>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --account-time --subject-ids --audit-status --limit --offset --json --debug`。`--project-id`、`--subject-ids` 支持逗号多值；月份必须合法，区间起始月份不得晚于结束月份；该命令固定查询 `type=1`（应收入账）。

### `receivable account-details`

```text
yc-cloud collection receivable account-details [--project-id <id>] [--receivable-id <id>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --receivable-id --limit --offset --json --debug`。两个 ID 均只接受大于 0 的整数；`--receivable-id` 映射明细接口筛选字段 `receivableSourceId`。

### `receivable project-tree`

```text
yc-cloud collection receivable project-tree [--level <n>] [--json] [--debug]
```

允许参数：`--level --json --debug`。应收入账弹窗「项目名称」下拉数据源，只返回 `granted != false` 的节点及真实 `projectId`（`--level` 默认 -1 表示全部）

### `receivable house-list`

```text
yc-cloud collection receivable house-list --project-id <ids> [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`（支持逗号多值）。应收入账弹窗「房屋/车位」下拉数据源，调用 `POST /saas/base/baseUserHouseRelation/getHouseUserRelationByContactpayer`，只输出 `nodeType=5/9/10`（房屋/车位/虚拟车位）并返回真实 `houseId`

### `receivable subject-tree`

```text
yc-cloud collection receivable subject-tree [--root-id <id>] [--json] [--debug]
```

允许参数：`--root-id --json --debug`。应收入账弹窗「收费科目」下拉数据源，接口仍为 `POST /saas/charge/select/ChargeConfigTree`；输出会排除“综合预收款”以及过滤后无子项的空分类，并返回真实 `subjectId`（`--root-id` 默认 0）

### `receive-payment-report detail`

```text
yc-cloud collection receive-payment-report detail [--project-id <id>] [--project-name <name>] [--payment-time-from <datetime>] [--payment-time-to <datetime>] [--subject-id <id>] [--charge-id <id>] [--house-id <id>] [--payment-method <enum>] [--detail-type <enum>] [--user-name <name>] [--real-short-name <name>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --project-name --payment-time-from --payment-time-to --subject-id --charge-id --house-id --payment-method --detail-type --user-name --real-short-name --limit --offset --json --debug`

### `receive-payment-report summary`

```text
yc-cloud collection receive-payment-report summary [--project-id <id>] [--project-name <name>] [--subject-id <id>] [--charge-id <id>] [--cost-date-from <date>] [--cost-date-to <date>] [--payment-time-from <datetime>] [--payment-time-to <datetime>] [--detail-type <enum>] [--house-id <id>] [--payment-method <enum>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --project-name --subject-id --charge-id --cost-date-from --cost-date-to --payment-time-from --payment-time-to --detail-type --house-id --payment-method --limit --offset --json --debug`

### `receive-payment-report summary-by-pay-method`

```text
yc-cloud collection receive-payment-report summary-by-pay-method [--project-id <id>] [--project-name <name>] [--receivable-date-from <date>] [--receivable-date-to <date>] [--payment-time-from <datetime>] [--payment-time-to <datetime>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --project-name --receivable-date-from --receivable-date-to --payment-time-from --payment-time-to --limit --offset --json --debug`

对应接口：`POST /saas/data/selectReceivePaymentSummary`（与 `summary` 相同；各结算方式金额在返回列中）。筛选窗口为收款时间：`--receivable-date-from/to`（`YYYY-MM-DD`）展开为当日起止；`--payment-time-from/to` 优先。

### `receive-payment-report summary-by-due-date`

```text
yc-cloud collection receive-payment-report summary-by-due-date [--project-id <id>] [--project-name <name>] [--receivable-date-from <date>] [--receivable-date-to <date>] [--payment-time-from <datetime>] [--payment-time-to <datetime>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --project-name --receivable-date-from --receivable-date-to --payment-time-from --payment-time-to --limit --offset --json --debug`

对应接口：`POST /saas/data/selectReceivePaymentDueDateSummary`。按应收日汇总收款趋势；筛选窗口同上。

### `report arrears-detail`

```text
yc-cloud collection report arrears-detail --project-id <ids> [--charge-subject-id <ids>] [--cost-date-from <date>] [--cost-date-to <date>] [--due-date-from <date>] [--due-date-to <date>] [--cost-status <statuses>] [--house-id <ids>] [--steward-name <name>] [--cutoff-time <datetime>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`

### `report collection-rate`

```text
yc-cloud collection report collection-rate --project-id <ids> [--by <project|steward>] [--charge-subject-id <ids>] [--cost-date-from <date>] [--cost-date-to <date>] [--due-date-from <date>] [--due-date-to <date>] [--house-id <ids>] [--steward-name <name>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`

### `report prepaid-balance`

```text
yc-cloud collection report prepaid-balance --project-id <ids> [--source <data|charge>] [--house-id <ids>] [--customer-id <ids>] [--customer-name <name>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`

说明：`--source` 默认 `data`（数据中心 `selectPrepaidBalance`）；`charge` 走收费预存管理页口径（`queryPrePaidSummaryList`），此时不支持 `--customer-name`。

### `report deposit-balance`

```text
yc-cloud collection report deposit-balance --project-id <ids> [--house-id <ids>] [--customer-id <ids>] [--customer-name <name>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--project-id`

### `charge-order list`

```text
yc-cloud collection charge-order list [--project-id <id>] [--house-id <id>] [--payment-time-from <datetime>] [--payment-time-to <datetime>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --house-id --payment-time-from --payment-time-to --limit --offset --json --debug`

### `charge-order correct`

```text
yc-cloud collection charge-order correct --id <id> --payment-method <enum> --payment-time <datetime> --reason <text> [--json] [--debug]
```

必须参数：`--id --payment-method --payment-time --reason`

### `charge-order cancel`

```text
yc-cloud collection charge-order cancel --id <id> [--reason <text>] [--json] [--debug]
```

必须参数：`--id`

说明：撤销已收款订单明细（作废收据），对应 `updateOrderDetailStatus`；`--reason` 可选，写入 `revokeReason`。与下方 `refund-*` 退款申请/审核链路不同。

### `charge-order refund-apply`

```text
yc-cloud collection charge-order refund-apply --order-detail-id <id> --payment-method <enum> --refund-amount <amount> [--refund-late-amount <amount>] [--remark <text>] [--json] [--debug]
```

必须参数：`--order-detail-id --payment-method --refund-amount`

对应接口：`POST /saas/charge/refund/insertApplyOrderRefund`（**不是** `orderRefund/*`）。

### `charge-order refund-audit`

```text
yc-cloud collection charge-order refund-audit --id <id> --audit-status <1|2|3|PENDING|APPROVED|REJECTED> [--audit-opinion <text>] [--json] [--debug]
```

必须参数：`--id --audit-status`

对应接口：`POST /saas/charge/refund/updateOrderRefundAudit`

### `charge-order refund-list`

```text
yc-cloud collection charge-order refund-list [--project-id <id>] [--audit-status <1|2|3|PENDING|APPROVED|REJECTED>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --audit-status --limit --offset --json --debug`

对应接口：`POST /saas/charge/refund/queryApplyOrderRefundList`

### `billing find-detail`

```text
yc-cloud collection billing find-detail --receivable-account-detail-id <id> [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--receivable-account-detail-id`

说明：按 `receivableAccountDetailId` 定位待变更账单明细；返回结果中的 `receivableAccountDetailId`（缺失时用 `receivableId`）用于后续 `change-payer --detail-id`。

### `billing list-customers`

```text
yc-cloud collection billing list-customers [--project-id <ids>] [--house-id <ids>] [--customer-name <name>] [--mobile <mobile>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --house-id --customer-name --mobile --limit --offset --json --debug`

对应接口：`POST /saas/base/queryUserCustomerPageList`（`params.projectId` + `order_by updatedTime DESC`）

按项目查询示例：

```text
yc-cloud collection billing list-customers --project-id 6070517275140001 --json
```

### `billing list-house-relations`

```text
yc-cloud collection billing list-house-relations [--user-customer-id <id>] [--house-id <id>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--user-customer-id --house-id --limit --offset --json --debug`

### `billing list-changeable-payers`

```text
yc-cloud collection billing list-changeable-payers [--house-id <id>] [--parking-space-id <id>] [--json] [--debug]
```

必须参数：`--house-id` 与 `--parking-space-id` 至少提供一个

### `billing list-house-customers`

```text
yc-cloud collection billing list-house-customers --house-id <id> [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--house-id`

### `billing list-customer-houses`

```text
yc-cloud collection billing list-customer-houses --user-customer-id <id> [--json] [--debug]
```

必须参数：`--user-customer-id`

### `billing change-payer`

```text
yc-cloud collection billing change-payer --detail-id <ids> --new-customer-id <id> [--json] [--debug]
```

必须参数：`--detail-id --new-customer-id`

说明：`--detail-id` 支持逗号分隔多个 ID（同批变更到同一新缴款人）；值来自 `billing find-detail` 返回的 `receivableAccountDetailId`（缺失时用 `receivableId`）。

### `import house-relation`

```text
yc-cloud collection import house-relation --file <path> [--json] [--debug]
```

必须参数：`--file`

### `import parking-relation`

```text
yc-cloud collection import parking-relation --file <path> [--json] [--debug]
```

必须参数：`--file`

### `import customer`

```text
yc-cloud collection import customer --file <path> [--json] [--debug]
```

必须参数：`--file`

### `rebate multi-business list`

```text
yc-cloud rebate multi-business list --property-name <name> --project-name <name> --category-type <type> [--page <n>] [--page-size <n>] [--json] [--debug]
```

必须参数：`--property-name --project-name --category-type`

## Workflow 示例

### 收款报表

用户问「今日收款 / 指定日期收费金额 / 按收款时间查询」时，**必须**走本工作流；**不得**用 `collection report *`（收缴率、欠费明细等数据中心报表）代替，也不得声称「API 不支持按收款日期过滤」。

命令与接口：

- `receive-payment-report summary`：收款汇总，对应 `POST /saas/data/selectReceivePaymentSummary`
- `receive-payment-report detail`：收款明细（逐笔流水），对应 `POST /saas/data/selectReceivePaymentDetail`
- `receive-payment-report summary-by-pay-method`：按结算方式查看收款汇总，对应 `POST /saas/data/selectReceivePaymentSummary`（与 `summary` 同接口；「今天/指定日各渠道收了多少」）
- `receive-payment-report summary-by-due-date`：按应收日维度汇总结果，对应 `POST /saas/data/selectReceivePaymentDueDateSummary`

**费用日期 vs 收款时间 vs 应收日**（勿混淆）：

- `--cost-date-from` / `--cost-date-to`：按**费用账期**（`costDate`）筛选（仅 `summary`）
- `--payment-time-from` / `--payment-time-to`：按**收款时间**（`paymentTime`）筛选（`detail` / `summary` / 两个分组汇总）；查「今日 / 某日收费」**必须**传这一对参数，格式 `YYYY-MM-DD HH:mm:ss`
- `--receivable-date-from` / `--receivable-date-to`：`summary-by-pay-method` / `summary-by-due-date` 的日期快捷写法（`YYYY-MM-DD`），映射为当日 `paymentTimeStart/End`；与 `--payment-time-*` 同时传时后者优先

查「项目今日收费金额」标准步骤：

1. 预检项目：`sms-task list-projects --keyword <名称> --json` 解析 `project-id`（或用户直接给 ID）
2. 汇总查询：

```text
yc-cloud collection receive-payment-report summary \
  --project-id <id> \
  --payment-time-from "YYYY-MM-DD 00:00:00" \
  --payment-time-to "YYYY-MM-DD 23:59:59" \
  --json
```

3. 需要逐笔流水时再用 `detail`，同样传 `--payment-time-from` / `--payment-time-to`
4. 需要按结算方式看今日/指定日收款总额时，用 `summary-by-pay-method` 并传 `--receivable-date-from/to`（或 `--payment-time-from/to`）

读金额与结论：

- JSON 结果中 `projectName` 为 `合计` 的 `totalAmount` 即收款总额；无 `合计` 行时对各行 `paymentAmount` 求和
- `data` 为空表示当日收款 **¥0.00**，不得改说成「无法按收款日期查询」
- 不得在未传 `--payment-time-from/to` 时把累计或跨期汇总当成「今日收款」

其他规则：

- 可选 `--detail-type`、`--payment-method` 进一步收窄范围；不传表示不限
- 必须先落实到明确 `project-id`；用户只给项目名称时，先用 `sms-task list-projects` 解析
- 若本地 CLI 未注册这两个命令，直接说明当前版本不支持，不猜接口、不脑补替代命令

### 应收入账

- 欠费查询：`receivable arrears-list`（仅查询，不生成账单）
- **生成入账（结构化，推荐，等价于系统「应收入账」弹窗）**：依次联动四步——
  1. 查项目：`receivable project-tree` → 从 `granted != false` 的结果中选定目标 `projectId`
  2. 查房屋：`receivable house-list --project-id <id>` → 从 `nodeType=5/9/10` 的结果中选定 `houseId`（可多选）
  3. 查科目：`receivable subject-tree` → 选定 `subjectId`（可多选，但不得选择“综合预收款”）
  4. 提交：`receivable create-account --project-id <id> --house-ids <ids> --subject-ids <ids> --account-time <YYYY-MM~YYYY-MM>`
- 生成入账（透传方式）：`receivable create-account --input <json>`，请求体须来自业务确认后的 JSON 文件
- 审核入账：可用 `receivable approve-account --input <json>`，或结构化执行 `receivable approve-account --receivable-id <id> --audit-status <2|3> [--audit-opinion <text>]`；驳回（3）必须填写意见，结构化请求固定 `receivableSource=3`
- 入账列表：`receivable list-accounts [--project-id <ids>] [--account-time <YYYY-MM|YYYY-MM~YYYY-MM>] [--subject-ids <ids>] [--audit-status <0|1|2|3>]`，固定查询 `type=1`；入账明细：`receivable account-details [--project-id <id>] [--receivable-id <id>]`，其中 `receivable-id` 映射 `receivableSourceId`
- 创建命令的 `--account-time` 为入账年月区间，格式固定 `YYYY-MM~YYYY-MM`（如 `2026-06~2026-09`，单月则起止相同 `2026-06~2026-06`）；月份必须真实存在，起始月份不得晚于结束月份
- `--house-ids` / `--subject-ids` 为逗号分隔 ID 列表，须分别来自 `house-list` / `subject-tree` 的真实返回，不得臆造
- 提交前必须向用户确认「项目 + 房屋 + 科目 + 账期」四要素；创建成功只表示后端已受理，不臆测一定返回 `batch_no` 或 `receivableAccountId`，随后用 `list-accounts` 复核生成状态
- `--json` 成功输出继续沿用现有顶层 JSON 结构，不新增或替换顶层字段
- 不得用 `receivable arrears-list` 代替入账生成或审核

### 账单调整

- 定位待变更明细：`billing find-detail --receivable-account-detail-id <id>`
- 可选定位客户：`billing list-customers [--customer-name <name>] [--mobile <mobile>]`
- 可选定位房屋客户关系：`billing list-house-relations [--user-customer-id <id>] [--house-id <id>]`
- 查询可变更缴款人：`billing list-changeable-payers --house-id <id> [--parking-space-id <id>]`
- 可选核对房屋关联客户：`billing list-house-customers --house-id <id>`
- 可选核对客户关联房屋：`billing list-customer-houses --user-customer-id <id>`
- 提交变更：`billing change-payer --detail-id <id>[,<id>...] --new-customer-id <id>`
- `--detail-id` 必须使用 `find-detail` 返回的 `receivableAccountDetailId`（缺失时用 `receivableId`）
- 新缴款人必须来自 `list-changeable-payers` 返回列表
- `billing list-customers` / `list-house-customers` / `list-house-relations` 均为只读核对，不能编辑客户或新增关系（新增业主/租客走 [house.md](house.md)）
- 不得用欠费查询或分享账单代替缴款人变更

### 数据中心报表

- 欠费明细表：`report arrears-detail --project-id <ids>`
- 收缴率：`report collection-rate --project-id <ids> [--by project|steward]`
- 预收余额：`report prepaid-balance --project-id <ids>`（默认 `data`）；收费预存页口径加 `--source charge`
- 押金余额：`report deposit-balance --project-id <ids>`
- 不得用 `receive-payment-report` 代替数据中心报表；欠费查询仍走 `checkout-desk list-arrears`（见 [collection.md](collection.md)）或 `receivable arrears-list`
- 按收款时间查今日 / 指定日期收费金额不得用 `report *`；应走 `receive-payment-report summary` 或 `detail`，并传 `--payment-time-from` / `--payment-time-to`

### 收费订单

- 订单列表：`charge-order list [--project-id <id> --house-id <id> --payment-time-from <datetime> --payment-time-to <datetime>]`
- 票据更正：`charge-order correct --id <id> --payment-method <enum> --payment-time <datetime> --reason <text>`
- **撤销收据（作废收款）**：`charge-order cancel --id <id> [--reason <text>]` — 主路径对应手机端「撤销收费订单」
- **退款申请/审核**：`charge-order refund-apply` → `refund-audit` → `refund-list`（`POST /saas/charge/refund/*`，与 `cancel` 不同链路；押金退款走 `deposit-refund`，勿混用）
- 不要把 `order` 工单模块当作收费订单管理

### 基础资料导入

- 产权导入：`import house-relation --file <path>`
- 车位导入：`import parking-relation --file <path>`
- 客户导入：`import customer --file <path>`
- 导入前确认文件格式与模板一致；结果用 `--json` 查看详情
- 单条新增租客/业主不得走导入命令，应走 [house.md](house.md) 的房屋与租客管理工作流

### 多业态营收

- 查询：`rebate multi-business list --property-name <name> --project-name <name> --category-type <type>`

## Module Guards

1. 先确认 `apiKey` 再执行收费链路。
2. 「客户全部欠费查询」优先 `checkout-desk list-arrears` 或 `receivable arrears-list`，不得默认用 `sms-task preview` 代替；欠费统计例外，按 [list-query.md](list-query.md) 执行。
3. `receive-payment-report` 若本地 CLI 未注册，对外直接判定当前版本不支持，不自行猜替代命令。
4. 问「今日收款 / 指定日期收费金额」时，必须用 `receive-payment-report summary` 或 `detail` 并传 `--payment-time-from/to`；不得用 `collection report *` 代替，也不得声称接口不支持按收款日期过滤。
5. 所有收费操作只能通过 allowlist 内的 `yc-cloud` 命令执行。

## Stop Conditions

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中，或本地 CLI 未注册对应子命令。
2. 缺少 `project-id`、`house-id`、`subject-id`、`receivable-account-detail-id` 等必填参数且无法可靠补齐。
3. 项目预检失败。
4. 文档与当前源码冲突且无法以源码直接定论。

禁止：

- 把接口路径、Controller 名、请求 DTO 当作可执行命令。
- 用相近但不等价的 CLI 命令硬替代未实现能力（例如用 `receivable arrears-list` 代替应收入账生成）。
- 长篇背景解释；未执行路径的猜测。
