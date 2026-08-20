# 可选资源探索

模板和已保存方案文件只在能提高选型、保持既有约束或减少返工时读取。新建空方案、边界明确的修改以及缺少资源命令的环境都可以直接继续，不把探索当作 mutation 前置门禁。

## Shell 命令

LLM 可以写 shell 风格命令；运行时会把参数转换为工具 JSON。命令前缀固定为 `woscli wai-builder`。

```sh
woscli wai-builder list-templates
woscli wai-builder list-resource-files --resourceType template --resourceId template-9
woscli wai-builder read-resource-files --resourceType template --resourceId template-9 --snapshotId 456 --paths '["design/home.md"]'
```

读取已有方案时把 `resourceType` 换成 `scheme` 并使用实际方案 id。`snapshotId` 和 `paths` 必须来自同一次 list 结果；只读与当前任务有关的少量文本文件。

续改已有方案或基于模板创建新方案时，如果 list 结果存在以下文件，优先读取与当前任务有关的内容：

- `wai-context.md`：业务事实、页面职责、主行动、关键约束与未决缺口；
- `design/design-direction.md`：共享视觉系统和各页视觉意图；
- `review/site-review.md`：上一次全站视觉审查仍需关注的问题。

这些文件是角色交接和复用上下文，不替代实时画布 DSL、当前用户要求或最终截图。资源中没有这些文件时直接继续，不补造旧信息。

## 选择与归因

- 模板 metadata 只用于候选选型，不冒充文件内容。
- 当前用户陈述优先于方案文件，方案文件优先于模板参考。
- 引用文件事实时保留来源路径；没有成功 read 时只说明“资源文件不可用”。
- 模板不能覆盖已确认页面、人工修改或当前用户事实。

## 失败处理

- 明确的临时网络错误：原命令重试一次。
- 明确的参数错误：运行 `woscli wai-builder <command> --help`，修正一次。
- `cmd not found`：运行一次 `woscli wai-builder --help`。命令仍不存在时记录能力缺口并继续，不猜别名、不循环重试。
- 资源缺失、过期或截断：只在它会改变结果正确性时向用户说明；否则用实时画布和用户输入继续。

资源探索也可以由 Main Agent 直接完成或按需委派，不要求固定角色、固定 digest schema 或固定输出文件。
