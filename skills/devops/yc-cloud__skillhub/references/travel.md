# travel 模块硬约束

## 模块合同

本文件的目标不是介绍旅游命令，而是约束 agent 在 `travel` 模块下的行为。

必须遵守：

1. 只处理当前 Go 版 CLI 已注册的 `travel` 命令。
2. 只使用当前模块明确指定的事实源。
3. 不得把相似业务、相似参数或历史命令当作可替代路径。
4. 如果请求超出允许命令范围，必须直接停止。

## 事实源

只按以下顺序取事实：

1. `internal/travel/travel.go`
2. `workbuddy/docs/COMMAND_SPEC.md`
3. `workbuddy/references/travel.md`

以下材料不是事实源：

- `dist/` 下副本
- 历史发布包说明
- 其他仓库的旅游命令
- 未在当前源码或 `COMMAND_SPEC.md` 中出现的参数、接口、枚举值

## Allowlist

当前允许以下 `travel` 命令：

```text
yc-cloud travel store permission-ids
yc-cloud travel store permission-level
yc-cloud travel store level-store-ids
yc-cloud travel store tree
yc-cloud travel store list
yc-cloud travel order list
yc-cloud travel order stats
yc-cloud travel order create
yc-cloud travel order delete
yc-cloud travel order cancel
yc-cloud travel order pay
yc-cloud travel order refund-result
yc-cloud travel order export
yc-cloud travel route create
yc-cloud travel route update
yc-cloud travel route status
yc-cloud travel route delete
yc-cloud travel route list
yc-cloud travel route detail
yc-cloud travel route stats
yc-cloud travel route status-stats
yc-cloud travel route home-list
yc-cloud travel route home-detail
yc-cloud travel route export
yc-cloud travel route offline-by-store
yc-cloud travel departure-date create
yc-cloud travel departure-date update
yc-cloud travel departure-date status
yc-cloud travel departure-date delete
yc-cloud travel departure-date list
yc-cloud travel departure-date detail
yc-cloud travel departure-date nearest-project
yc-cloud travel departure-date project-list
yc-cloud travel departure-date status-stats
yc-cloud travel departure-date review-stats
yc-cloud travel departure-date covered-province
yc-cloud travel departure-date export
yc-cloud travel group sync
yc-cloud travel group sync-status
yc-cloud travel group create
yc-cloud travel group update
yc-cloud travel group delete
yc-cloud travel group list
yc-cloud travel group tabs
yc-cloud travel group detail
yc-cloud travel group member-list
yc-cloud travel group member-export
yc-cloud travel group export
yc-cloud travel group-detail create
yc-cloud travel group-detail update
yc-cloud travel group-detail delete
yc-cloud travel group-detail list
yc-cloud travel group-detail detail
yc-cloud travel group-detail page-list
yc-cloud travel escort batch-create
yc-cloud travel escort update
yc-cloud travel escort delete
yc-cloud travel escort list
yc-cloud travel fellower create
yc-cloud travel fellower update
yc-cloud travel fellower delete
yc-cloud travel fellower list
yc-cloud travel fellower detail
yc-cloud travel fellower verify-id-card
yc-cloud travel charge-person create
yc-cloud travel charge-person update
yc-cloud travel charge-person delete
yc-cloud travel charge-person list
yc-cloud travel charge-person detail
yc-cloud travel charge-person employee-times
yc-cloud travel review create
yc-cloud travel review list
yc-cloud travel review batch-status
```

规则：

- allowlist 之外的任何 `travel` 子命令，一律视为不支持
- 不得把 `travel` 命令替换为 `collection`、`order`、`flash` 或其他模块命令
- 不得因为历史经验脑补新的旅游子命令

## 旅游角色与数据权限硬约束

本节用于替代旧的 `meetup apply` / `xuanlan permission get` 角色校验规则。旅游模块只允许使用当前 `travel` 权限命令做角色和数据范围判断。

### 前置权限校验（强制执行）

每个 `yc-cloud travel ...` 目标命令执行前，必须先完成以下校验：

1. 调用 `yc-cloud travel store permission-level --business-unit travel --is-deleted 0 --json` 获取当前用户旅游权限层级。
2. 解析返回数据中的旅游权限层级或角色标识，只允许归类为：
   - `总店权限`
   - `分店权限`
3. 若无法从接口结果明确识别为 `总店权限` 或 `分店权限`，立即终止，输出 `您当前没有权限`。
4. 根据下方命令权限矩阵判断当前角色是否允许执行目标命令。
5. 涉及店铺数据范围的命令，必须调用 `yc-cloud travel store permission-ids --business-unit travel --is-deleted 0 --json` 获取当前用户可见店铺 ID，并用结果约束目标命令。
6. 权限校验通过前，禁止执行目标命令。

例外：`yc-cloud travel store permission-level` 作为权限前置命令执行自身时，不需要递归执行权限层级校验，但仍必须通过模块、allowlist 和参数校验。

禁止：

- 不得继续使用 `xuanlan permission get`
- 不得读取或比对 `meetup`、`拜访中心`、`业主见面会` 等非旅游角色
- 不得跳过权限层级查询直接执行 `travel` 业务命令
- 不得假设当前用户是总店或分店

### 命令权限矩阵

| 命令范围 | 分店权限 | 总店权限 |
|---|---|---|
| 查询类命令 | 允许，仅限分店权限店铺数据 | 允许，可查总店权限范围数据 |
| 导出类命令 | 禁止 | 允许 |
| 新增、修改、删除、上下架、取消、支付、退款回调、同步、审核、身份证校验等变更或敏感命令 | 禁止 | 允许 |

查询类命令只包括：

```text
yc-cloud travel store permission-ids
yc-cloud travel store permission-level
yc-cloud travel store level-store-ids
yc-cloud travel store tree
yc-cloud travel store list
yc-cloud travel order list
yc-cloud travel order stats
yc-cloud travel route list
yc-cloud travel route detail
yc-cloud travel route stats
yc-cloud travel route status-stats
yc-cloud travel route home-list
yc-cloud travel route home-detail
yc-cloud travel departure-date list
yc-cloud travel departure-date detail
yc-cloud travel departure-date nearest-project
yc-cloud travel departure-date project-list
yc-cloud travel departure-date status-stats
yc-cloud travel departure-date review-stats
yc-cloud travel departure-date covered-province
yc-cloud travel group list
yc-cloud travel group tabs
yc-cloud travel group detail
yc-cloud travel group member-list
yc-cloud travel group-detail list
yc-cloud travel group-detail detail
yc-cloud travel group-detail page-list
yc-cloud travel escort list
yc-cloud travel fellower list
yc-cloud travel fellower detail
yc-cloud travel charge-person list
yc-cloud travel charge-person detail
yc-cloud travel charge-person employee-times
yc-cloud travel review list
```

除上述查询类命令外，allowlist 中其他 `travel` 命令均按总店权限命令处理。

如需新增角色或命令权限，按以下格式追加：

| 新命令或命令范围 | 分店权限 | 总店权限 |
|---|---|---|
| `yc-cloud travel ...` | 允许/禁止，并说明数据范围 | 允许/禁止，并说明数据范围 |

### 店铺数据范围规则

- 分店只能查阅 `permission-ids` 返回的分店权限店铺数据。
- 总店只能查阅总店权限范围内的数据，不得绕过权限接口脑补全量店铺。
- 用户显式传入 `--store-ids`、`--store-id`、`storeId`、`goodsStoreId` 或请求体中的店铺字段时，必须确认这些店铺 ID 是当前权限店铺 ID 的子集。
- 分店查询命令如果无法通过参数、过滤条件、请求体或返回结果确认数据属于权限店铺范围，必须终止，输出 `您当前没有权限`。
- 未传店铺参数时，只允许使用当前实现的自动权限店铺查询；自动查询失败时，禁止继续执行目标命令。

## Routing

用户请求命中以下关键词时，进入本模块：

- 旅游
- 店铺权限
- 店铺 ID
- 旅游订单
- 订单状态统计
- `travel`

如果请求同时涉及旅游和其他模块：

- 先完成模块判断
- 若核心目标是旅游订单或旅游店铺权限，优先进入本模块
- 不得在未完成路由前执行命令

## Refusal Rules

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中
2. 本地 CLI 未注册对应 `travel` 子命令
3. 缺少必要参数且当前上下文无法可靠补齐
4. 自动前置查询权限店铺失败
5. 文档与当前 Go 源码冲突且无法以源码直接定论
6. 权限层级查询失败或无法识别总店/分店权限
7. 当前角色不允许执行目标命令
8. 请求店铺范围不属于当前权限店铺

停止时只允许给出以下结论：

- 当前版本不支持
- 缺少必要条件
- 需要补充明确参数
- 需要先修复权限店铺查询
- 您当前没有权限

## Parameter Rules

以下参数必须保守处理：

- `store-ids`
- `order-id`
- `buyer-phone`
- `buyer-name`
- `status`
- `pay-status`
- `page`
- `page-size`
- `business-unit`
- `is-deleted`

规则：

- `store-ids` 不得凭记忆脑补
- `store-ids`、`store-id`、`storeId`、`goodsStoreId` 必须落在当前权限店铺 ID 范围内
- 未传 `--store-ids` 时，只允许走当前实现里的自动权限店铺查询
- `status` 只允许：`pendingPay` / `pendingTravel` / `traveling` / `traveled` / `completed` / `canceled` / `all`
- `pay-status` 只允许：`unpaid` / `paid` / `all`
- `business-unit` 只允许：`travel` / `flashSale`
- `is-deleted` 只允许：`0` / `1`
- `page` 从 1 开始，禁止写成 0 或负数

## Parameter Allowlist

AI 不得自己发明参数。每个命令只允许使用下面列出的参数。

### `travel store permission-ids`

命令形态：

```text
yc-cloud travel store permission-ids [--business-unit <travel|flashSale>] [--is-deleted <0|1>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--business-unit` | 业务单元 | `travel` / `flashSale`；默认 `travel` |
| `--is-deleted` | 逻辑删除标记 | `0` / `1`；默认 `0` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `travel store permission-level`

命令形态：

```text
yc-cloud travel store permission-level [--business-unit <travel|flashSale>] [--is-deleted <0|1>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--business-unit` | 业务单元 | `travel` / `flashSale`；默认 `travel` |
| `--is-deleted` | 逻辑删除标记 | `0` / `1`；默认 `0` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `travel store level-store-ids`

命令形态：

```text
yc-cloud travel store level-store-ids --level <level> [--business-unit <travel|flashSale>] [--is-deleted <0|1>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--level` | 组织层级 | 必填，不得脑补 |
| `--business-unit` | 业务单元 | `travel` / `flashSale`；默认 `travel` |
| `--is-deleted` | 逻辑删除标记 | `0` / `1`；默认 `0` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `travel order stats`

命令形态：

```text
yc-cloud travel order stats [--store-ids <id1,id2>] [--buyer-phone <phone>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--store-ids` | 店铺ID，多个用英文逗号分隔；未传时允许自动查权限店铺 | - |
| `--buyer-phone` | 下单人手机号 | - |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `travel order list`

命令形态：

```text
yc-cloud travel order list [--store-ids <id1,id2>] [--order-id <id>] [--status <enum>] [--pay-status <enum>] [--buyer-phone <phone>] [--buyer-name <name>] [--page <n>] [--page-size <n>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--store-ids` | 店铺ID，多个用英文逗号分隔；未传时允许自动查权限店铺 | - |
| `--order-id` | 订单号，支持模糊搜索 | - |
| `--status` | 订单状态 | `pendingPay` / `pendingTravel` / `traveling` / `traveled` / `completed` / `canceled` / `all`；默认 `all` |
| `--pay-status` | 支付状态 | `unpaid` / `paid` / `all`；默认 `all` |
| `--buyer-phone` | 下单人手机号 | - |
| `--buyer-name` | 下单人姓名 | - |
| `--page` | 页码 | 默认 `1` |
| `--page-size` | 每页数量 | 默认 `10` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### 通用新增命令参数

新增的 `travel` 命令只能使用源码已注册的参数，不得把一个命令的参数迁移到另一个命令使用。

body 型命令按源码注册情况可使用：

| 参数 | 说明 |
|---|---|
| `--body` | 完整请求体 JSON |
| `--body-file` | 从文件读取完整请求体 JSON |
| `--json` | JSON 输出 |
| `--debug` | 调试输出 |

列表、统计和导出型命令按源码注册情况支持分页、过滤、排序：

| 参数 | 说明 |
|---|---|
| `--page` | 页码，从 1 开始 |
| `--page-size` | 每页数量 |
| `--filter` | 过滤条件，格式 `field:op:value`，可重复 |
| `--order-by` | 排序，格式 `field:asc|desc`，可重复 |

导出命令按源码注册情况可额外使用：

| 参数 | 说明 |
|---|---|
| `--output` | 导出文件输出路径 |
| `--format` | 导出格式，默认 `excel` |
| `--mask-id-card` | 是否脱敏身份证，默认 `true` |

以下命令还有额外必填参数：

| 命令 | 额外参数 |
|---|---|
| `travel order pay` | `--payment-request-sn --app-id --external-pay-sub-type-code` |
| `travel store level-store-ids` | `--level`；可选 `--business-unit --is-deleted` |
| `travel route status` | `<id> --status` |
| `travel route offline-by-store` | `--store-id` |
| `travel departure-date status` | `<id> --status` |
| `travel departure-date nearest-project` | `--longitude --latitude`；可选 `--tenant-id` |

## 复杂请求体硬约束

创建、更新、批量创建、退款回调、审核批量状态等复杂 DTO 场景必须使用 `--body` 或 `--body-file` 提供完整 JSON。

必须遵守：

1. 不得根据业务经验拆解、补全或脑补字段。
2. 不得把复杂 DTO 的字段改写成未注册的 flag。
3. 不得从其他模块、历史命令或接口文档推断缺失字段。
4. 用户未提供完整 JSON 时，必须停止并要求补充明确请求体。

## Execution State Machine

所有 `travel` 请求必须按以下顺序执行：

1. 判断请求是否落在本模块范围
2. 校验目标命令是否在 allowlist 中
3. 执行 `travel store permission-level` 并识别为总店权限或分店权限；若目标命令本身就是 `permission-level`，只执行自身，不做递归校验
4. 按命令权限矩阵校验当前角色是否允许执行目标命令
5. 涉及店铺数据范围时，执行 `travel store permission-ids` 获取权限店铺 ID
6. 校验参数是否合法，并校验店铺参数属于权限店铺范围
7. 如果未传 `--store-ids`，允许当前实现自动前置查询权限店铺
8. 执行目标命令
9. 仅在失败时回看源码和 `COMMAND_SPEC.md`

禁止：

- 未完成参数校验就执行命令
- 未完成权限层级校验就执行命令
- 分店执行新增、修改、删除、导出或其他总店权限命令
- 分店查询超出权限店铺范围的数据
- 在权限店铺查询失败后继续执行 `order stats` 或 `order list`
- 为了“更完整”切换到其他模块命令继续查

## Per-Command Rules

### `travel store permission-ids`

只负责查询当前用户权限范围内的旅游店铺 ID。

必须遵守：

- 只把它当权限店铺来源
- 不得把结果写入配置文件
- 如果失败，直接停止，不要继续推测店铺 ID
- 只允许使用 `--business-unit --is-deleted --json --debug`

### `travel store permission-level`

只负责识别当前用户在旅游模块中的总店或分店权限。

必须遵守：

- 每个目标命令前都必须先执行本命令
- 目标命令就是本命令时，不递归执行自身
- 只把它当旅游角色校验来源
- 不能识别为总店或分店时，输出 `您当前没有权限`
- 不得把非旅游模块角色结果当成本命令结果
- 只允许使用 `--business-unit --is-deleted --json --debug`

### `travel order stats`

只负责统计旅游主订单状态数量。

必须遵守：

- 只统计主订单
- 分店只允许统计权限店铺范围内数据
- 若未传 `--store-ids`，只允许使用自动权限店铺查询结果
- 不得把统计结果当订单明细
- 只允许使用 `--store-ids --buyer-phone --json --debug`

### `travel order list`

只负责分页查询旅游订单列表。

必须遵守：

- 只使用当前实现支持的过滤参数
- 不得把列表查询自动扩大成“查全部店铺全部订单”
- 分店只允许查询权限店铺范围内订单
- 若未传 `--store-ids`，只允许使用自动权限店铺查询结果
- 只允许使用 `--store-ids --order-id --status --pay-status --buyer-phone --buyer-name --page --page-size --json --debug`

## Output Rules

优先输出：

1. 实际执行的命令
2. 权限校验结论（总店权限 / 分店权限 / 无权限）
3. 是否自动补了权限店铺查询
4. 命中的事实源
5. 成功结果或失败原因
6. 下一步唯一建议

禁止：

- 长篇背景解释
- 未执行路径的猜测
- 把不确定的店铺 ID、订单状态或过滤条件包装成确定事实

## Non-Goals

本模块不负责：

- 推断新的旅游命令
- 保存店铺 ID 到配置
- 把旅游命令改写成别的模块命令
- 解释历史架构

## 新增命令示例

以下示例只展示当前源码已注册命令的安全调用形态：

```bash
yc-cloud travel route list --filter status:=:1 --order-by createdTime:desc --json
yc-cloud travel route detail 10001 --json
yc-cloud travel route offline-by-store --store-id 5001 --json
yc-cloud travel departure-date nearest-project --longitude 113.32 --latitude 23.13 --json
yc-cloud travel group member-list 9001 --json
yc-cloud travel review batch-status --body-file review-batch.json --json
```
