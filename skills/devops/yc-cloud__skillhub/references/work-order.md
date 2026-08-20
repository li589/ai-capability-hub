# 工单模块硬约束

## 模块范围

本模块只覆盖当前 `order` 命令面。

## 事实源

只按以下顺序取事实：

1. `internal/order/order.go`
2. `workbuddy/docs/WORKORDER_API.md`
3. `workbuddy/docs/COMMAND_SPEC.md`
4. `workbuddy/references/workder-order.md`
5. 若涉及共享收费前置条件，再看 `workbuddy/references/billing-system.md`

以下材料不是事实源：

- `dist/`
- 历史发布包说明
- 其他仓库同名工单实现
- 未在当前源码或 `COMMAND_SPEC` 中出现的参数、接口、枚举值

## Allowlist

当前只允许以下 14 个命令：

```text
yc-cloud order create
yc-cloud order list
yc-cloud order list-templates
yc-cloud order detail
yc-cloud order count
yc-cloud order claim
yc-cloud order complete
yc-cloud order assign
yc-cloud order transfer
yc-cloud order cancel
yc-cloud order rollback nodes
yc-cloud order rollback submit
yc-cloud order evaluate
yc-cloud order attachment add
```

allowlist 之外的任何 `order` 子命令，一律视为不支持。

## Module Guards

1. 先确认 `apiKey`
2. 先做项目权限预检：`yc-cloud collection sms-task list-projects --json`
3. `order list` / `order count` 等支持项目过滤的查询命令，必须优先带 `--project-id`
4. `order detail` 只能使用已在授权项目范围内查到的 `workOrderId`
5. 涉及操作类命令时，必须确认当前用户具有对应 `WorkOrderOpGuard`

## Refusal Rules

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中
2. 本地 CLI 未注册对应 `order` 子命令
3. 缺少 `workOrderId`、`node-id`、`target-activity-id`、`next-assignee` 等必填参数且无法可靠补齐
4. 项目权限预检失败
5. 需要跨未授权项目查询工单
6. 文档与当前源码冲突且无法以源码直接定论

## Known Bugs And Downgrade Rules

以下是当前已确认的 CLI 已知问题：

1. `order assign` 可能报“任务不存在”，根因是 CLI 自动生成了错误 `taskId`

处理规则：

- 默认不要绕过 CLI
- 只有遇到以上已确认 bug，才允许进入降级判断
- 若用户未要求继续推进，可直接说明 CLI 已知问题并停止
- 若用户明确要求继续完成任务，可按已确认接口做 API 降级，不得临时猜接口

## Parameter Rules

以下参数必须保守处理：

- `project-id`
- `workOrderId`
- `deployment-id`
- `process-template-id`
- `source`
- `processing-time`
- `node-id`
- `task-id`
- `next-assignee`
- `target-assignee-id`
- `target-activity-id`
- `score`
- `file-type`
- `file-url`

规则：

- `workOrderId` 不得凭记忆脑补
- `processing-time` 是分钟，不是日期时间
- 时间参数统一使用 `yyyy-MM-dd HH:mm:ss`
- `file-url` 只允许已存在的 URL，不支持本地文件上传
- `score` 只允许 `1-5`
- `scope` 只允许 `all` / `todo` / `owner`

## Parameter Allowlist

### `order create`

```text
yc-cloud order create --deployment-id <id> --process-template-id <id> --source <source> --processing-time <minutes> [--project-id <id>] [--project-name <name>] [--house-id <id>] [--house-name <name>] [--type <n>] [--title <text>] [--contact-name <text>] [--contact-mobile <text>] [--problem-description <text>] [--scheduled-visit-time <datetime>] [--expected-completion-time <datetime>] [--detailed-address <text>] [--form-template-id <id>] [--workflow-template-id <id>] [--workflow-id <id>] [--priority <n>] [--partition-key <n>] [--user-name <name>] [--json] [--debug]
```

CLI 默认向请求体写入 `partitionKey: 0`。如需覆盖分区，可显式传 `--partition-key <n>`。

CLI 校验必须：`--deployment-id --process-template-id --source --processing-time`

事实必须（后端 startProcess 依赖）：`--form-template-id --workflow-template-id`（缺少会返回 00099 内部错误）

### `order list`

```text
yc-cloud order list [--scope <all|todo|owner>] [--project-id <id>] [--type <n>] [--priority <n>] [--start-time <datetime>] [--end-time <datetime>] [--keyword <keyword>] [--limit <n>] [--offset <n>] [--json] [--debug]
```

允许参数：`--scope --project-id --type --priority --start-time --end-time --keyword --limit --offset --json --debug`

### `order list-templates`

```text
yc-cloud order list-templates --project-id <id> [--json] [--debug]
```

必须参数：`--project-id`

返回该项目可用的流程模板列表，包含 `deploymentId`、`processTemplateId`、`processingTime`、`formTemplateId`、`workflowTemplateId`、`templateTitle` 等。创建工单前必须先调此命令获取模板参数。

### `order detail`

```text
yc-cloud order detail <workOrderId> [--json] [--debug]
```

### `order count`

```text
yc-cloud order count [--project-id <id>] [--type <n>] [--priority <n>] [--start-time <datetime>] [--end-time <datetime>] [--json] [--debug]
```

### `order claim`

```text
yc-cloud order claim <workOrderId> --node-id <id> [--user-name <name>] [--json] [--debug]
```

必须参数：`workOrderId --node-id`

### `order complete`

```text
yc-cloud order complete <workOrderId> --assignee <name> --comment <text> --approved <true|false> [--reject-action <action>] [--rollback-service-task-id <id>] [--next-assignee <id>] [--node-id <id>] [--task-id <id>] [--json] [--debug]
```

必须参数：`workOrderId --assignee --comment --approved`

### `order assign`

```text
yc-cloud order assign <workOrderId> --assignee <name> --comment <text> --next-assignee <id> [--node-id <id>] [--task-id <id>] [--json] [--debug]
```

必须参数：`workOrderId --assignee --comment --next-assignee`

### `order transfer`

```text
yc-cloud order transfer <workOrderId> --target-assignee <name> --target-assignee-id <id> --node-id <id> [--user-name <name>] [--candidate-users <ids>] [--json] [--debug]
```

必须参数：`workOrderId --target-assignee --target-assignee-id --node-id`

### `order cancel`

```text
yc-cloud order cancel <workOrderId> [--user-name <name>] [--reason <text>] [--json] [--debug]
```

### `order rollback nodes`

```text
yc-cloud order rollback nodes <workOrderId> [--json] [--debug]
```

### `order rollback submit`

```text
yc-cloud order rollback submit <workOrderId> --target-activity-id <id> [--operator <name>] [--reason <text>] [--json] [--debug]
```

必须参数：`workOrderId --target-activity-id`

### `order evaluate`

```text
yc-cloud order evaluate <workOrderId> --score <1-5> [--user-name <name>] [--content <text>] [--json] [--debug]
```

必须参数：`workOrderId --score`

### `order attachment add`

```text
yc-cloud order attachment add <workOrderId> --file-type <type> --file-name <name> --file-url <url> [--json] [--debug]
```

必须参数：`workOrderId --file-type --file-name --file-url`

## Permission Rules

操作类命令的 Guard 要求：

- `order assign` -> `ALLOCATE`
- `order complete` -> `COMPLETE`
- `order cancel` -> `CANCEL`
- `order claim` -> `ACCEPT`
- `order transfer` -> `DELEGATE`

若权限错误，直接提示权限不足，不要靠换命令绕过。

## Create Discovery Workflow

`order create` 的 4 个必填参数 (`deployment-id`、`process-template-id`、`source`、`processing-time`) 来自后端流程引擎配置。使用 `order list-templates` 命令直接查询。

### 发现步骤（必须按顺序执行）

1. **确认项目**：通过 `collection sms-task list-projects --json` 获取授权项目列表，取 `projectId`
2. **查模板配置**：`order list-templates --project-id <projectId> --json`，从返回的模板数组中提取以下 **5 个字段**（全部必须传入 `order create`）：
   - `deploymentId` → `--deployment-id`
   - `processTemplateId` → `--process-template-id`
   - `processingTime` → `--processing-time`
   - `formTemplateId` → `--form-template-id`
   - `workflowTemplateId` → `--workflow-template-id`
3. **`source` 取默认值 `1`**（后台/CLI 发起）

> **⚠ 重要：`--form-template-id` 和 `--workflow-template-id` 虽然 CLI 层面不做非空校验，但后端 `startProcess` 缺少它们会返回 `00099 系统内部错误`。必须从 `list-templates` 提取并传入。**

### 模板选择规则

`list-templates` 可能返回多个模板（不同工单类型各有模板）。选择规则：

- 优先选 `status` 为启用状态的模板
- 如果返回多个，按用户请求的工单类型（如"公区报事报修"）匹配 `templateTitle`
- 如果只有一个模板，直接使用

### source 枚举（已知值）

| 值 | 含义 |
|----|------|
| `1` | 后台 / CLI / 内部发起 |
| `4` | 小程序 |

Agent 通过 CLI 创建工单时，**一律使用 `--source 1`**。

### type 常见值

| 值 | 含义 |
|----|------|
| `1` | 住户报事报修 |
| `2` | 公区报事报修 |

用户说"报事报修"时，按对话上下文判断是住户还是公区。

### 如果 list-templates 返回空

说明该项目尚未部署流程模板，**停止并告知用户**："该项目尚未配置工单流程模板，请先在管理后台部署流程后再试。"

不得猜测 `deployment-id` 或 `process-template-id`。

### 完整创建示例

```bash
# 1. 查项目
yc-cloud collection sms-task list-projects --json

# 2. 查模板配置
yc-cloud order list-templates --project-id 6042010464200001 --json
# 从返回提取 deploymentId, processTemplateId, processingTime, formTemplateId, workflowTemplateId

# 3. 创建（5 个模板字段全部传入）
yc-cloud order create \
  --deployment-id <deploymentId> \
  --process-template-id <processTemplateId> \
  --form-template-id <formTemplateId> \
  --workflow-template-id <workflowTemplateId> \
  --source 1 \
  --processing-time <processingTime> \
  --project-id 6042010464200001 \
  --type 2 \
  --contact-name "谢秉坤" \
  --problem-description "走廊入户灯破损" \
  --user-name "刘泽浩" \
  --json
```

## Workflow Rules

### 查询

- `list` / `count` 优先带 `--project-id`
- `detail` 只用已在授权项目范围内查到的 `workOrderId`
- 不得把 `detail` 自动扩展成流转或附件补查

### 创建

- **必须先执行 Create Discovery Workflow**，不得跳过发现步骤直接问用户要技术参数
- 先确认模板、部署参数、项目上下文
- 若报 `partition_key` 错误，直接判定为 CLI 已知 bug
- 若需要继续完成，必须明确这是 API 降级，不得伪装成 CLI 正常成功

### 派单

- 先确认 `next-assignee`
- 若报“任务不存在”，直接判定为 CLI `taskId` 已知 bug
- 若需要继续完成，才允许使用已确认接口降级

### 退回

- 先 `rollback nodes`
- 再 `rollback submit`
- 不得跳过第一步直接猜 `target-activity-id`

## Output Rules

优先输出：

1. 实际执行的命令
2. 是否命中权限守卫
3. 是否命中已知 bug
4. 命中的事实源
5. 成功结果或失败原因
6. 下一步唯一建议

禁止：

- 长篇背景解释
- 未执行路径的猜测
- 把 API 降级伪装成 CLI 正常路径

## Non-Goals

本模块不负责：

- 推断未实现工单命令
- 用其他模块命令替代工单命令
- 绕过项目权限守卫
- 解释历史 TS/Bun 架构
