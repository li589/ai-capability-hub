# 押金退款

押金退款：可退查询、退款申请、审核、记录查询。接口路径以 billing-system 为权威口径。

## CLI 调用硬规则

1. 执行前先读 `runtime.md`；CLI 只能通过 `sh ./scripts/yc-cloud.sh <命令>` 调用，禁止 `which/find/curl` 或直连 API。
2. 只走本文件 allowlist 内的 `yc-cloud deposit-refund ...` 命令；接口路径、Controller 名、请求 DTO 都不是可执行命令。
3. 先确认 `apiKey` 再执行退款写链路；`apply` 前必须先查 `list` 取真实 `orderDetailId`，不得编造。
4. 不得凭记忆脑补任何业务 ID；`limit/offset` 用非负整数，`paymentMethod` 只用当前实现支持的枚举（`8` 现金流 / `9` 押金转存）。

## 命令清单

```text
yc-cloud deposit-refund info
yc-cloud deposit-refund apply
yc-cloud deposit-refund apply-list
yc-cloud deposit-refund apply-detail
yc-cloud deposit-refund audit
yc-cloud deposit-refund list
yc-cloud deposit-refund detail
```

## Parameter Allowlist

### `deposit-refund info`

```text
yc-cloud deposit-refund info --user-customer-id <id> --project-id <id> [--limit <n>] [--offset <n>] [--json] [--debug] [--quiet]
```

必须参数：`--user-customer-id --project-id`（或改用 `--filters` 直传 billing-system body）

接口：`POST /saas/charge/checkOutDesk/getDepositRefInfo`

关键字段：`depositAmount`（未退押金汇总）；明细字段以接口返回为准

### `deposit-refund apply`

```text
yc-cloud deposit-refund apply --insert <json> [--json] [--debug] [--quiet]
```

必须参数：`--insert`（billing-system `IInsertApplyOrderRefundParams` 数组，外层包 `{ insert: [...] }`）

接口：`POST /saas/charge/refund/insertApplyOrderRefund`

### `deposit-refund apply-list`

```text
yc-cloud deposit-refund apply-list [--filters <json>] [--limit <n>] [--offset <n>] [--order-by <json>] [--json] [--debug] [--quiet]
```

接口：`POST /saas/charge/refund/queryApplyOrderRefundList`

### `deposit-refund apply-detail`

```text
yc-cloud deposit-refund apply-detail --filters <json> [--limit <n>] [--offset <n>] [--json] [--debug] [--quiet]
```

必须参数：`--filters`（按 `id` 精确查询）

实现：复用 `POST /saas/charge/refund/queryApplyOrderRefundList` 取单条（无独立 detail 接口）

### `deposit-refund audit`

```text
yc-cloud deposit-refund audit --update <json> [--json] [--debug] [--quiet]
```

必须参数：`--update`（billing-system `IUpdateOrderRefundAuditParams` 数组，`set.auditStatus` 2=通过、3=驳回）

接口：`POST /saas/charge/refund/updateOrderRefundAudit`

### `deposit-refund list`

```text
yc-cloud deposit-refund list [--filters <json>] [--limit <n>] [--offset <n>] [--order-by <json>] [--json] [--debug] [--quiet]
```

接口：`POST /saas/charge/refund/queryOrderRefundList`

列表关键字段：`id`、`orderDetailId`、`refundableAmount`、`houseId`、`userName`、`chargeSubject`

### `deposit-refund detail`

```text
yc-cloud deposit-refund detail --filters <json> [--limit <n>] [--offset <n>] [--json] [--debug] [--quiet]
```

必须参数：`--filters`

实现：复用 `POST /saas/charge/refund/queryOrderRefundList` 取单条（无独立 detail 接口）

## Workflow 示例

### 押金退款

用户要「对指定房产退押金」「查押金可退余额」「提交退款申请并审核」时，**必须**走本工作流；不得声称当前 CLI 不支持押金退款。

**与只读报表的分工**：

- `collection report deposit-balance`：数据中心押金余额报表，**不能**提交退款或审核
- `deposit-refund info`：结账台口径的可退押金明细（含 `orderId` / `orderDetailId`）
- `deposit-refund apply` / `audit`：退款申请与审核写操作

**标准步骤（完整退款）**：

1. 定位房屋与客户：`collection report deposit-balance --project-id <ids> --json` 或 `house customer-list --filters '{"logic":"and","filters":[{"field":"userName","op":"like","value":"<姓名>"}]}' --json` — 取 `houseId`、`projectId`、`userCustomerId`
2. 查未退押金：`deposit-refund info --user-customer-id <id> --project-id <id> --json` — 取 `depositAmount`
3. 查可退明细：`deposit-refund list --filters '{"logic":"and","filters":[{"field":"houseId","op":"=","value":<houseId>}]}' --limit 20 --offset 0 --json` — 取 `orderDetailId`、`refundableAmount`
4. 确认退款金额不超过可退余额
5. 提交申请：`deposit-refund apply --insert '[{"orderDetailId":<列表行id>,"paymentMethod":8,"refundAmount":"<金额>","refundLateAmount":"0","refundAttributes":{...},"remark":"<备注>","applyBy":<员工id>}]' --json`（`orderDetailId` 取 `list` 的 `id`；`paymentMethod` 须为 `8` 现金流或 `9` 押金转存）
6. 查待审核：`deposit-refund apply-list --filters '{"logic":"and","filters":[{"field":"auditStatus","op":"=","value":1}]}' --limit 20 --offset 0 --json` — 取申请记录 `id`
7. 审核：`deposit-refund audit --update '[{"set":{"auditStatus":2,"auditOpinion":"审核通过","auditBy":<员工id>},"where":{"id":<申请id>}}]' --json`
8. 验证：`deposit-refund list --filters '{"logic":"and","filters":[{"field":"houseId","op":"=","value":<houseId>}]}' --limit 20 --offset 0 --json`

**只读：查已有退款记录**：

1. `deposit-refund list` — 按 `houseId` 等条件筛选
2. `deposit-refund detail --filters '{"logic":"and","filters":[{"field":"id","op":"=","value":<退款记录id>}]}' --json` — 单条明细

**接口路径口径**（billing-system 权威）：

| 命令 | 接口 |
| --- | --- |
| `info` | `POST /saas/charge/checkOutDesk/getDepositRefInfo` |
| `apply` | `POST /saas/charge/refund/insertApplyOrderRefund` |
| `apply-list` | `POST /saas/charge/refund/queryApplyOrderRefundList` |
| `apply-detail` | 复用 `queryApplyOrderRefundList`（单条） |
| `audit` | `POST /saas/charge/refund/updateOrderRefundAudit` |
| `list` | `POST /saas/charge/refund/queryOrderRefundList` |
| `detail` | 复用 `queryOrderRefundList`（单条） |

**禁止**：

- 使用 `/saas/charge/orderRefund/*`：已废弃，禁用（非 billing-system 路径，生产 500）
- 调用不存在的 `queryApplyOrderRefundDetail` / `queryOrderRefundDetail`
- 用 `report deposit-balance` 代替退款写操作
- 在未查 `list` 的情况下编造 `orderDetailId`

## Module Guards

1. 押金退款链路先确认 `apiKey`。
2. `collection report deposit-balance` 只读，**不能**提交退款或审核。
3. `apply` 前必须先查 `deposit-refund list` 取真实 `orderDetailId`，不得编造。
4. 所有操作只能通过 allowlist 内的 `yc-cloud deposit-refund ...` 命令执行。

## Stop Conditions

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中，或本地 CLI 未注册对应子命令。
2. 缺少 `user-customer-id`、`project-id`、`orderDetailId` 等必填参数且无法可靠补齐。
3. 文档与当前源码冲突且无法以源码直接定论。

禁止：

- 把接口路径、Controller 名、请求 DTO 当作可执行命令。
- 使用 `/saas/charge/orderRefund/*` 等废弃路径或不存在的 detail 接口。
- 用 `report deposit-balance` 代替退款写操作，或在未查 `list` 时编造 `orderDetailId`。
