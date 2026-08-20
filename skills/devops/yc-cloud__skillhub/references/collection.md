# 收费催缴

催缴短信、收银台欠费、分享账单、催缴通知单、违约金减免、短信黑名单等催缴核心链路。含「单人催缴策略（按姓名定位业主）」端到端编排。

## CLI 调用硬规则

1. 执行前先读 `runtime.md`；CLI 只能通过 `sh ./scripts/yc-cloud.sh <命令>` 调用，禁止 `which/find/curl` 或直连 API。
2. 只走本文件 allowlist 内的 `yc-cloud collection ...` 命令；接口路径、Controller 名、请求 DTO 都不是可执行命令。
3. 先确认 `apiKey` 再执行收费链路；涉及项目权限时先预检 `sms-task list-projects`。
4. 不得凭记忆脑补任何业务 ID；`share-bill create-snapshot` 的 `app-id` 默认 `2512281028590000`，用户明确提供非空值时原样覆盖；`limit/offset` 用非负整数，枚举只用当前实现支持的值。

> **输出全局规则（关乎速度，与 SKILL.md「结果输出」一致）**：所有 list/preview/查询类命令**不加任何输出标志**（不加 `--json`、不加 `--output`），CLI 的 **stdout 本身就是排好的紧凑 markdown 表**——**把它原样贴给用户 + 一句话结论即可**。**严禁**：`--output` 写文件、`present_files`（会弹侧边栏并诱导模型乱编排文件而 botch）、`read_file` 读结果、加 `--json` 再自排表、把结果重定向到文件、合并多项目。`--json` 仅当把结果喂给下一条命令（如 `send`）时才用。

## 命令清单

```text
yc-cloud collection sms-task list-projects
yc-cloud collection sms-task list-fee-items
yc-cloud collection sms-task list-templates
yc-cloud collection sms-task preview
yc-cloud collection sms-task send
yc-cloud collection sms-task list
yc-cloud collection sms-task get
yc-cloud collection checkout-desk list-arrears
yc-cloud collection share-bill create-snapshot
yc-cloud collection payment-reminder create
yc-cloud collection payment-reminder list
yc-cloud collection payment-reminder print
yc-cloud collection late-fee reduce
yc-cloud collection late-fee list
yc-cloud collection late-fee revoked-list
yc-cloud collection late-fee revoke
yc-cloud collection sms-blacklist query
yc-cloud collection sms-blacklist create
yc-cloud collection sms-blacklist app-list
```

## Parameter Allowlist

### `sms-task list-projects`

```text
yc-cloud collection sms-task list-projects [--keyword <keyword>] [--json] [--debug]
```

允许参数：`--keyword --json --debug`

### `sms-task list-fee-items`

```text
yc-cloud collection sms-task list-fee-items [--keyword <keyword>] [--json] [--debug]
```

允许参数：`--keyword --json --debug`

### `sms-task list-templates`

```text
yc-cloud collection sms-task list-templates [--keyword <keyword>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--keyword --limit --offset --json --debug`

只返回收费应用 `resourceCode=evertro_pm_bill` 对应 `applicationId` 下的已启用模板；无法唯一解析收费应用时停止，不得使用其他子系统模板代替。

### `sms-task preview`

```text
yc-cloud collection sms-task preview --project-id <id> [--charge-subject-id <id>] [--charge-subject-ids <ids>] [--all-fee-items] [--keyword <keyword>] [--house-id <id>] [--building-name <name>] [--user-customer-id <id>] [--house-name <keyword>] [--user-name <keyword>] [--mobile <keyword>] [--cost-date-from <date>] [--cost-date-to <date>] [--require-page <bool>] [--limit <n>] [--offset <n>] [--output <path>] [--all-matched] [--query-plan <json>] [--json] [--debug]
```

必须参数：`--project-id`

允许参数：`--project-id --charge-subject-id --charge-subject-ids --all-fee-items --keyword --house-id --building-name --user-customer-id --house-name --user-name --mobile --cost-date-from --cost-date-to --require-page --limit --offset --output --all-matched --query-plan --json --debug`

范围约束：

- `--all-fee-items` 表示使用收费配置树中所有 `nodeType=1` 科目节点，并兼容已确认参与页面催缴口径的非标准节点（仅当节点实际存在于当前树中才纳入）；它与 `--charge-subject-id`、`--charge-subject-ids` 互斥。科目缺少有效 ID，或未登记为已确认例外的树节点缺少可判定类型时停止。批量催缴必须明确选择具体科目或显式传 `--all-fee-items`，不得依赖接口默认科目范围。
- `--building-name` 在项目房屋树中精确匹配唯一楼栋并展开栋下全部房屋，与 `--house-id`、`--house-name` 互斥。零匹配或多匹配时停止，不得改用模糊 `--house-name` 猜测。
- `--all-matched` 是批量催缴的全量预览模式：必须且只能传一种收费科目范围（`--charge-subject-id`、`--charge-subject-ids` 或 `--all-fee-items`），必须传 `--output`，不能与 `--query-plan` 同用，不得显式传 `--limit`，`--offset` 必须为 `0`，对外 `--require-page` 保持默认 `false`。CLI 内部固定 `requirePage=true` 自动翻页，最多处理 `50000` 条。
- `--all-matched --json` 只在 stdout 返回前 `20` 条和全量 `summary`；`summary.feeScope.resolvedChargeSubjectIds` 是实际传给欠费接口的科目 ID，必须随预检结果一起展示。`--output` 文件保存全部命中记录。不得把终端中的前 `20` 条另存为发送输入。

`--query-plan` 只用于欠费统计分析，保持 `--require-page=false`，**不加 `--output`/`--json`**：stdout 就是排好的紧凑表，原样贴出 + 一句话结论即可（禁止写文件/`present_files`/`read_file`）。多项目就各项目一条命令、**同一轮并行发**、各自贴表，不合并成文件。`--json` 只在把结果喂给下一条命令时用。字段 schema、计划模板和展示规则见 [list-query.md](list-query.md)。

`collection sms-task preview` 的 `--query-plan` / `--all-matched` 模式均由 CLI 按 **每页 500** 自动翻页，最多处理 `50000` 条。禁止手动传 `--limit` 加大单页、禁止自己翻页。`count` 聚合不得带 `field`（见 list-query.md）。

### `sms-task send`

```text
yc-cloud collection sms-task send --template-id <id> [--project-id <id>] [--collection-method <0|2>] [--input <path>] [--charge-subject-id <id>] [--charge-subject-ids <ids>] [--house-id <id>] [--user-customer-id <id>] [--keyword <keyword>] [--house-name <keyword>] [--user-name <keyword>] [--mobile <keyword>] [--cost-date-from <date>] [--cost-date-to <date>] [--limit <n>] [--offset <n>] [--require-page <bool>] [--preflight] [--json] [--debug]
```

必须参数：

- `--template-id`
- 未传 `--input` 时还必须有 `--project-id`

`--preflight` 默认关闭；传入后会完整查询模板、读取输入、校验并组装发送数据，但不会调用创建催缴任务接口。预检成功后必须向用户展示项目、模板、输入数、可提交数、跳过数和欠费总额；只有取得用户对不可撤销发送的明确确认，才能使用完全相同参数去掉 `--preflight` 实际发送。未传 `--preflight` 时保留原有发送行为。

### `sms-task list`

```text
yc-cloud collection sms-task list [--project-id <id>] [--template-name <keyword>] [--execution-status <0|1>] [--collection-method <0|2>] [--task-no <taskNo>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --template-name --execution-status --collection-method --task-no --limit --offset --json --debug`

### `sms-task get`

```text
yc-cloud collection sms-task get --task-id <id> [--send-status <0|1>] [--house-name <keyword>] [--user-name <keyword>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--task-id`

### `checkout-desk list-arrears`

```text
yc-cloud collection checkout-desk list-arrears --user-customer-id <id> --project-id <id> [--house-id <id>] [--charge-subject-id <id>] [--cost-date-from <date>] [--cost-date-to <date>] [--due-date-from <date>] [--due-date-to <date>] [--output <path>] [--json] [--debug]
```

必须参数：`--user-customer-id --project-id`

参数与筛选约束：

- `--user-customer-id`、`--project-id` 以及可选的 `--house-id`、`--charge-subject-id` 只接受大于 0 的整数。
- 日期参数只接受有效的 `YYYY-MM-DD`，且起始日期不能晚于结束日期；`--cost-date-*`、`--due-date-*` 都是闭区间。
- 未知 flag 和多余位置参数会在请求后端前拒绝。
- `--output` 与 `--json` 的 `data` **都是拍平后的叶子明细数组**（每条含 `radId`），**不含**带 `children` 的月/科目分组节点。分享账单必须用 `--output` 文件，不得把手写/改写的树形 JSON 当作入参。

### `share-bill create-snapshot`

```text
yc-cloud collection share-bill create-snapshot --project-id <id> --customer-id <id> --input <arrears.json> [--app-id <id>] [--has-late-fee <0|1>] [--json] [--debug]
```

必须参数：`--project-id --customer-id --input`

参数与数据约束：

- `--app-id` 可选，默认 `2512281028590000`；为兼容已有调用，用户显式提供的非空值原样透传。
- `--input` 必须直接来自同一项目、同一客户的 `checkout-desk list-arrears --output`（推荐拍平叶子数组原样使用），不得使用 `sms-task preview` 或 `receivable arrears-list` 的精简/分页数据。
- 提交前对齐小程序分享账单口径：只保留含 `radId` 的叶子；若误传入带 `children` 的月/科目树，CLI 会拍平为叶子后再提交；并为每条叶子补齐 `subjectId=chargeSubjectId`，缺失 `costDate` 时用 `costEndDate` 回填。拍平后无叶子则停止。
- 每条明细必须满足：`radId/projectId/userCustomerId/chargeSubjectId` 为正整数；`subjectName` 非空；`costDate/costStartDate/costEndDate` 为非空日期字符串或正数时间戳；`accountAmountInclTax/arrearsAmount` 为非负数；`radId` 不重复。普通房屋费用的 `houseId/realShortName` 必须同时有效；项目级费用允许这两个字段同时为 `null`。
- 所有明细的 `projectId` 必须与 `--project-id` 一致，`userCustomerId` 必须与 `--customer-id` 一致；`arrearsLate` 如存在必须非负，`--has-late-fee 1` 时每条明细都必须包含该字段。
- 一次命令只生成一个快照。“最多 10 个快照”按工作流中的快照请求数计算，不是欠费明细条数限制。
- 文本成功输出必须包含完整缴费链接和固定分享话术；`--json` 保持顶层 `code/data`，在 `data` 原字段基础上增加 `billUrl/shareMessage`。

### `payment-reminder create`

```text
yc-cloud collection payment-reminder create --project-id <id> --project-name <name> --cost-date <period> [--app-id <id>] [--charge-subject-ids <ids>] [--charge-subject-names <names>] [--house-ids <ids>] [--house-names <names>] [--has-late-fee <0|1>] [--remark <text>] [--json] [--debug]
```

必须参数：`--project-id --project-name --cost-date`；`--app-id` 可选，写入 `appId`

### `payment-reminder list`

```text
yc-cloud collection payment-reminder list [--project-id <id>] [--project-name <keyword>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --project-name --limit --offset --json --debug`

### `payment-reminder print`

```text
yc-cloud collection payment-reminder print --reminder-id <id> [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--reminder-id`（对应接口筛选字段 `paymentReminderId`）

### `late-fee reduce`

```text
yc-cloud collection late-fee reduce --ids <receivable-ids> --reduction-type <1|2> [--reduction-amount <amount>] [--reduction-ratio <ratio>] [--tenant-id <id>] [--remark <text>] [--json] [--debug]
```

必须参数：`--ids`、`--reduction-type`；`--reduction-type=1` 时必填 `--reduction-amount`，`--reduction-type=2` 时必填 `--reduction-ratio`。

### `late-fee list`

```text
yc-cloud collection late-fee list [--project-id <id>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --limit --offset --json --debug`

### `late-fee revoked-list`

```text
yc-cloud collection late-fee revoked-list [--project-id <id>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--project-id --limit --offset --json --debug`

### `late-fee revoke`

```text
yc-cloud collection late-fee revoke --ids <ids> [--json] [--debug]
```

必须参数：`--ids`（减免记录 ID，逗号分隔）

### `sms-blacklist query`

```text
yc-cloud collection sms-blacklist query --mobile <mobile> [--limit <n>] [--offset <n>] [--json] [--debug]
```

必须参数：`--mobile`

### `sms-blacklist create`

```text
yc-cloud collection sms-blacklist create --mobile <mobile> (--application-name <name> | --application-id <id>) [--remark <text>] [--json] [--debug]
```

必须参数：`--mobile`（校验 `^1[3-9]\d{9}$`）；`--application-name` 与 `--application-id` 至少提供一个
说明：仅给应用名则经 `getUserApplicationList` 反查 ID；均缺失或匹配不到（含未上架）则报错并列出可选应用（不回退写死默认值）

### `sms-blacklist app-list`

```text
yc-cloud collection sms-blacklist app-list [--keyword <kw>] [--include-offline] [--json] [--debug]
```

允许参数：`--keyword --include-offline --json --debug`。短信黑名单「应用名称」下拉数据源，默认仅展示上架应用（`appStatus=1`）

## Workflow 示例

### 客户全部欠费

- **已知 `user-customer-id`**：优先 `checkout-desk list-arrears`
- **未知 `user-customer-id`、仅知业主姓名/房号**：先用 `receivable arrears-list --user-name` / `--house-name` 定位，或 `house customer-list` 按姓名查 `id`；定位后再走 `checkout-desk list-arrears` 取完整收银台明细
- 要跨项目、多房屋、多科目查更宽范围，用 `receivable arrears-list`（应收管理口径，见 [receivable.md](receivable.md)）
- 不得默认用 `sms-task preview` 代替「全部欠费查询」；已明确为欠费统计分析（以上/以下、大于/小于、分组、汇总、排行、Top N）时按 [list-query.md](list-query.md) 执行
- `list-arrears` 最多只能预览 `10` 个客户的明细；超过 `10` 个客户必须拆批执行
- 查询结果固定优先展示：房产、收费科目、费用期间、应收金额、欠费金额
- 若用户后续还要发催缴或分享账单，先完成欠费查询，再切到对应工作流

### 单人催缴策略（按姓名定位业主）

用户说「分析某业主，制定催缴策略」（例如「分析谢秉坤业主，制定催缴策略」）且**尚未提供** `user-customer-id` 时，**必须**走本编排；不得跳过预览直接发送。

**与分工作流的关系**：

- 定位阶段：`receivable arrears-list` 按姓名模糊检索，`checkout-desk list-arrears` 取完整收银台欠费明细
- 策略与发送：必须先 `preview` 并让用户确认范围，再 `send`
- 可选分享：`share-bill create-snapshot --input` 必须来自 `checkout-desk list-arrears`，不得用 `preview` 输出代替

**调用顺序**：

```text
list-projects → arrears-list(定位业主) → checkout-desk list-arrears(完整欠费)
    → list-fee-items → list-templates → preview → send --preflight → 用户确认 → send
    → [可选] share-bill create-snapshot
```

**标准步骤**：

| 阶段 | 命令 | 用途 | 关键参数 |
| --- | --- | --- | --- |
| ① 项目预检 | `sms-task list-projects` | 确认项目权限，解析 `projectId` | `--keyword`（可选） |
| ② 业主定位 | `receivable arrears-list` | 按姓名检索欠费，解析 `userCustomerId` | `--project-id`（必填）、`--user-name`；若无 `userCustomerId` 见下方「ID 解析回退」 |
| ③ 完整欠费 | `checkout-desk list-arrears` | 收银台拍平叶子欠费明细 | `--user-customer-id`、`--project-id`；必须 `--output` 留存叶子数组供分享账单 |
| ④ 费项确认 | `sms-task list-fee-items` | 查看可选费项，收窄催缴科目范围 | `--keyword`（可选） |
| ⑤ 模板选定 | `sms-task list-templates` | 查看可用催缴短信模板 | 无必填 |
| ⑥ 发送预览 | `sms-task preview` | 确认命中人数与欠费金额 | `--project-id`（必填）；定位后优先传 `--user-customer-id`，或继续用 `--user-name` |
| ⑦ 发送预检 | `sms-task send --preflight` | 完整校验并组装发送数据，但不创建任务 | `--template-id`、`--project-id`；可用 `--user-customer-id` 或 `--input`（读取 preview 输出） |
| ⑧ 执行发送 | `sms-task send` | 用户明确确认后发送催缴短信 | 与步骤⑦完全相同并去掉 `--preflight` |
| ⑨ 分享账单（可选） | `share-bill create-snapshot` | 生成缴费链接辅助催缴 | `--project-id`、`--customer-id`（同 `userCustomerId`）、`--input`（步骤③输出）；`--app-id` 可选，默认 `2512281028590000` |

**示例命令**（将 `<project-id>`、`<user-customer-id>`、`<template-id>` 替换为前序步骤真实返回值）：

```text
yc-cloud collection sms-task list-projects --keyword 盈绰 --json

yc-cloud collection receivable arrears-list \
  --project-id <project-id> \
  --user-name 谢秉坤 \
  --json

yc-cloud collection checkout-desk list-arrears \
  --user-customer-id <user-customer-id> \
  --project-id <project-id> \
  --output arrears.json \
  --json

yc-cloud collection sms-task list-fee-items --json
yc-cloud collection sms-task list-templates --json

yc-cloud collection sms-task preview \
  --project-id <project-id> \
  --user-customer-id <user-customer-id> \
  --json

yc-cloud collection sms-task send \
  --template-id <template-id> \
  --project-id <project-id> \
  --user-customer-id <user-customer-id> \
  --preflight \
  --json

# 用户明确确认后，使用同一组参数去掉 --preflight 实际发送
yc-cloud collection sms-task send \
  --template-id <template-id> \
  --project-id <project-id> \
  --user-customer-id <user-customer-id> \
  --json

yc-cloud collection share-bill create-snapshot \
  --project-id <project-id> \
  --customer-id <user-customer-id> \
  --input arrears.json \
  --json
```

**字段与决策口径**：

- 步骤②须用 `--json` 读取 `userCustomerId`；CLI 表格输出不展示该字段，且 `arrears-list` 响应**不一定**每条都含 `userCustomerId`（以接口实际返回为准）。若缺失，**不得**臆造 ID，须走「ID 解析回退」后再进入步骤③
- 同名多人命中时停止并向用户确认房号/手机号，不得臆造 ID
- `share-bill create-snapshot` 的 `--customer-id` 与 `--user-customer-id` 为同一客户主键，不得混用不同来源的 ID
- 步骤④⑤为策略制定辅助：需按科目收窄催缴范围时，将 `list-fee-items` 返回的 `chargeSubjectId` 填入 `preview` / `send` 的 `--charge-subject-id` 或 `--charge-subject-ids`
- 步骤⑦只做发送预检；步骤⑧为不可撤销写操作，无用户明确授权时不得执行
- 发送前可选 `sms-blacklist query --mobile <mobile>` 排查黑名单；无手机号或手机号已脱敏的记录在短信方式（`collection-method=0`）下会被跳过

**ID 解析回退**（步骤② `arrears-list --json` 无 `userCustomerId` 时，按优先级择一）：

1. **客户主数据**（推荐）：`house customer-list` 按姓名查 `id`（即 `userCustomerId`）

```text
yc-cloud house customer-list \
  --project-id <project-id> \
  --customer-name 谢秉坤 \
  --json
```

2. **催缴聚合预览**：`sms-task preview` 按姓名聚合，从结果行读取 `userCustomerId`

```text
yc-cloud collection sms-task preview \
  --project-id <project-id> \
  --user-name 谢秉坤 \
  --json
```

回退路径只用于解析 `user-customer-id`；完整欠费明细仍必须在步骤③用 `checkout-desk list-arrears` 获取，不得用 `preview` 或 `arrears-list` 分页结果代替。

**禁止**：

- 在未知 `user-customer-id` 时直接调用 `checkout-desk list-arrears`
- 跳过 `preview` 直接 `send`
- 用 `preview` 输出或 `arrears-list` 分页结果代替 `checkout-desk list-arrears --output` 作为 `share-bill --input`
- 手工拼装/改写欠费 JSON（只留展示字段、篡改金额）；树形输入应交由 CLI 拍平，不要自行改字段硬凑

### 批量催缴（整个项目 / 精确楼栋）

用户提出“给整个项目发一轮催缴短信”“给某项目 3 栋的欠费业主发催缴短信”等批量请求时，必须严格按以下顺序执行：

```text
list-projects
→ 明确收费科目（具体科目 ID 或 --all-fee-items）
→ list-templates
→ preview --all-matched --output <本次临时文件>
→ send --input <同一文件> --preflight
→ 用户明确确认不可撤销发送
→ 使用同一参数去掉 --preflight 实际发送
```

标准命令：

```text
# 1. 解析真实项目 ID
yc-cloud collection sms-task list-projects --keyword <项目名称> --json

# 2. 查看并明确收费科目；若用户确认覆盖全部叶子科目，后续使用 --all-fee-items
yc-cloud collection sms-task list-fee-items --json

# 3. 查询并选择已启用模板
yc-cloud collection sms-task list-templates --json

# 4A. 整个项目全量预览
yc-cloud collection sms-task preview \
  --project-id <project-id> \
  --all-fee-items \
  --all-matched \
  --output <本次临时文件.json> \
  --json

# 4B. 指定楼栋全量预览（与 4A 二选一）
yc-cloud collection sms-task preview \
  --project-id <project-id> \
  --building-name "3栋" \
  --all-fee-items \
  --all-matched \
  --output <本次临时文件.json> \
  --json

# 5. 完整发送预检，不创建任务
yc-cloud collection sms-task send \
  --project-id <project-id> \
  --template-id <template-id> \
  --input <本次临时文件.json> \
  --preflight \
  --json

# 6. 用户明确确认不可撤销发送后，去掉 --preflight 实际发送
yc-cloud collection sms-task send \
  --project-id <project-id> \
  --template-id <template-id> \
  --input <本次临时文件.json> \
  --json
```

批量发送守卫：

- 必须先通过 `list-projects` 解析真实 `project-id`，不得按项目名称猜 ID。
- 必须明确具体收费科目，或由用户确认后显式使用 `--all-fee-items`；不得依赖接口默认科目范围。
- 指定楼栋必须使用 `--building-name` 精确解析；楼栋零匹配或多匹配时停止，不得降级成 `--house-name` 模糊发送。
- 必须使用 `--all-matched --output` 生成本次请求专用的全量文件；stdout 中最多 `20` 条预览不是完整发送输入。
- 预览超过 `50000` 条、任一页失败或结果不完整时停止，不得发送已取得的部分数据。
- `--input` 必须是本次请求刚生成并完成预检的文件，不得复用其他项目、其他楼栋或之前任务的预览文件。
- `send --preflight` 后必须把本次 `preview --all-matched` 的 `buildingName/feeScope` 摘要与预检结果合并展示，至少包含项目、楼栋/项目范围、收费科目、模板、输入数、可提交数、跳过数、欠费总额和输入文件路径。
- 批量短信发送是不可撤销写操作。没有用户对本次具体范围的明确确认时，只能停在预检结果，不得去掉 `--preflight`。

### 催缴发送

- 先预检项目权限：`sms-task list-projects`
- 项目权限只有一个时默认选中该项目；短信模板只有一个时默认选中该模板；模板有多个时让用户选择
- 发送前先 `sms-task preview`，并让用户确认发送范围
- 预览时优先展示前 `20` 条欠费信息，字段：姓名、房号、手机、欠费金额、欠费笔数；房号显示全称，手机号脱敏展示
- 单人或小范围发送也建议先用相同参数执行 `sms-task send --preflight`；批量发送必须预检
- 只有用户明确确认后，才可使用相同参数去掉 `--preflight` 实际发送
- `--input` 可读取 `preview --output` 的结果；批量场景必须读取本次 `--all-matched` 生成的完整文件
- 短信方式 `collection-method=0` 时，没有 `mobile` 或手机号已脱敏的记录必须跳过
- 微信方式 `collection-method=2` 时，没有 `openId` 的记录必须跳过
- 任务查询用 `sms-task list`；任务明细用 `sms-task get`

### 分享账单

- 输入优先来自 `checkout-desk list-arrears --output` 的拍平叶子数组（每条含 `radId`）；对齐小程序：CLI 提交前只保留叶子，误传带 `children` 的树时会拍平为全部叶子，并补齐 `subjectId` / `costDate`
- 一次 `share-bill create-snapshot` 只生成一个快照；一个工作流最多生成 `10` 个快照且不拆分执行。该上限不是 `arrearsList` 明细条数限制，单个客户超过 `10` 条合法欠费明细仍作为一个快照提交
- `--app-id` 默认 `2512281028590000`，无需向用户追问；仅当用户明确提供非空值时原样覆盖
- 若后端返回金额校验错误（如「勾选的金额有误」），重新执行 `checkout-desk list-arrears --output` 后再提交，不得继续改字段硬凑
- `--input` 必须保留叶子对象的业务字段，不能只留展示字段；核心字段缺失、`radId` 重复、金额非法，或明细项目/客户与命令参数不一致时停止
- 返回账单 ID 后，必须使用 CLI 返回的 `billUrl/shareMessage` 展示完整分享文案，不要只回 billId，也不要把「保存 JSON 文件」作为对用户的推荐步骤

固定分享文案：

```text
您的缴费账单已生成，请点击链接：weixin://dl/business/?appid=wx872bce03cac54358&path=packages/fee/userPayWeb/index&query=billId%3D【账单ID】完成缴费，如对费用金额有疑问可随时与我联系，如您已缴费请忽略此信息，感谢您的支持，谢您生活愉快！
```

### 催缴通知单

- 生成：`payment-reminder create`，必须提供 `--project-id`、`--project-name`、`--cost-date`；可选 `--app-id`
- 查询历史：`payment-reminder list`，可按 `--project-id` 或 `--project-name` 筛选
- 打印/导出：`payment-reminder print --reminder-id <id>`（映射 `paymentReminderId`），完整内容用 `--json`
- 不得用 `sms-task preview` 或 `sms-task send` 代替纸质/打印通知单

### 短信黑名单

- 查询：`sms-blacklist query --mobile <mobile>`
- 查可选应用：`sms-blacklist app-list`（拿 applicationId 与应用名，默认仅上架应用）
- 加入：`sms-blacklist create --mobile <mobile> --application-name <name>`（应用名自动反查 ID；或直接 `--application-id <id>`）
- 手机号须为 11 位大陆号（`^1[3-9]\d{9}$`）；未指定应用或应用不存在会报错，先用 `app-list` 查
- 不得用跳过 `sms-task send` 代替黑名单管理

### 违约金减免

- 提交减免：`late-fee reduce --ids <receivable-ids> --reduction-type <1|2>`，按应收明细 ID 精确减免
- 减免记录列表：`late-fee list`
- 已减免列表：`late-fee revoked-list`
- 撤销减免：`late-fee revoke --ids <ids>`
- 不得用 `share-bill --has-late-fee` 代替减免操作

## Module Guards

1. 先确认 `apiKey` 再执行收费链路。
2. 涉及项目权限时，优先预检 `sms-task list-projects`。
3. 「客户全部欠费查询」优先 `checkout-desk list-arrears` 或 `receivable arrears-list`，不得默认用 `sms-task preview` 代替；欠费统计（筛选/汇总/排行）例外，按 [list-query.md](list-query.md) 执行。
4. `share-bill create-snapshot` 的输入必须来自更完整的收银台欠费明细，不得用不完整预览数据代替。
5. 所有收费操作只能通过 allowlist 内的 `yc-cloud` 命令执行。

## Stop Conditions

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中，或本地 CLI 未注册对应子命令。
2. 缺少 `project-id`、`template-id`、`task-id`、`customer-id` 等必填参数且无法可靠补齐。
3. 项目预检失败。
4. 账单快照输入数据不完整。
5. 文档与当前源码冲突且无法以源码直接定论。

禁止：

- 把接口路径、Controller 名、请求 DTO 当作可执行命令。
- 用相近但不等价的 CLI 命令硬替代未实现能力（例如用 `sms-task preview` 代替催缴通知单）。
- 长篇背景解释；用不完整预览数据冒充完整账单输入。
