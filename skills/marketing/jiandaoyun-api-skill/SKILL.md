---
name: jiandaoyun-api-skill
description: Use the official Jiandaoyun Open API from local Codex or Claude Code through 39 bundled operations for application and form discovery, schema inspection, record reads and writes, workflow actions, contacts, usage metrics, and audit logs. Trigger when the user asks to query, export, create, update, delete, approve, audit, or otherwise operate authorized 简道云 resources with their own API Key. Do not use for browser-only configuration or undocumented APIs.
---

# 简道云 API 工具包

通过本地脚本直接调用简道云官方API。不要依赖远程中转服务，不要把API Key传给模型或写进项目。

## 入口

将本目录记为 `SKILL_DIR`，统一运行：

```bash
python3 "$SKILL_DIR/scripts/jdy" <operation> [options]
```

列出工具或查看参数：

```bash
python3 "$SKILL_DIR/scripts/jdy" tools
python3 "$SKILL_DIR/scripts/jdy" tool-help jdy_list_data_2
python3 "$SKILL_DIR/scripts/jdy" docs tool jdy_transfer_flow_task
```

所有39项操作均通过统一入口 `scripts/jdy` 调用。

## 认证

按以下优先级读取凭据：

1. `JIANDAOYUN_CREDENTIAL_FILE` 明确指定的文件。
2. 进程环境变量 `JIANDAOYUN_API_KEY`。
3. `~/.config/jiandaoyun-agent/credentials.json`（为兼容旧版本保留的凭据路径）。

绝不要求用户把Key粘贴到聊天、命令参数或JSON输入中。需要首次配置时，让用户在自己的终端交互运行：

```bash
python3 "$SKILL_DIR/scripts/configure"
```

如果进程已有 `JIANDAOYUN_API_KEY`，普通配置会停止并报告凭据来源冲突，避免“文件已更新但仍使用旧环境变量”。
此时先取消旧环境变量，或明确设置 `JIANDAOYUN_CREDENTIAL_FILE` 后再配置。不得静默声称新Key已经生效。

配置文件必须为 `600`；权限不安全时停止。只检查本地状态可运行：

```bash
python3 "$SKILL_DIR/scripts/doctor" --offline
```

## 标准流程

1. 用 `jdy_list_apps` 精确确定应用。
2. 用 `jdy_list_forms` 精确确定表单。
3. 用 `jdy_get_form_widgets` 获取字段名、字段类型和系统字段。
4. 读取时优先选择窄字段和窄筛选。
5. 使用筛选时默认选 `jdy_list_data_2`，避免不兼容条件被静默忽略。
6. 在任何写入前读取当前记录和 `updateTime`。
7. 先运行写操作获取预览和确认令牌，把目标、当前值、拟修改值及触发器状态展示给用户。
8. 等待用户针对该预览明确批准；不要把最初的“帮我修改”当成最终执行批准。
9. 使用相同输入、确认令牌和 `--execute` 执行。破坏性操作还必须加 `--acknowledge-destructive`。
10. 检查脚本返回的写后回读；不要仅凭HTTP成功判断写入完成。

## 官方文档排错

遇到参数名、接口路径、请求格式、响应字段、错误码或权限含义不确定时，禁止凭经验修改Skill或猜测接口。

1. 运行 `python3 "$SKILL_DIR/scripts/jdy" docs tool <工具名>`，取得该工具对应的官方文档。
2. 不知道工具名时，运行 `python3 "$SKILL_DIR/scripts/jdy" docs search <关键词>` 离线搜索73项官方目录。
3. 需要正文时，运行 `python3 "$SKILL_DIR/scripts/jdy" docs fetch <文档ID>`，只从
   `https://hc.jiandaoyun.com/open/` 读取当前官方页面；此操作不使用或发送API Key。
4. 用官方页面核对 schema、endpoint 和参数。若文档与包不一致，先报告差异并征得用户同意；
   不得自行修改已安装Skill。
5. 官方页面无法读取或结构变化时，返回文档URL并明确说明未完成核验，不要编造答案。

## 输入输出

用JSON文件传参数，避免Shell转义和命令历史泄漏：

```bash
python3 "$SKILL_DIR/scripts/jdy" list-data-2 --input-file /absolute/path/request.json
```

所有结果均为JSON：

- `ok=true`：操作、数据、分页或预览成功。
- `ok=false`：读取 `error.type`、`error.code`、`error.message` 和 `retryable`。
- 即使HTTP状态为200，只要官方响应明确包含 `status="failure"`，也必须返回
  `ok=false` 和 `error.type="business_error"`，禁止把业务失败解释为成功。

当 `jdy_list_data` 或 `jdy_list_data_2` 使用 `limit=100` 且不传 `data_id` 时，脚本自动分页。大表应设置 `max_records`。

## 写入约束

- 写入默认只预览，不调用线上写接口。
- 新建数据默认必须提供查重过滤器；只有用户明确接受重复风险时才可设置 `allow_duplicate=true`，并重新预览确认。
- `jdy_update_data` 执行时必须传刚读取到的 `--expected-update-time`。
- 批量接口每次最多100条；不要把单条请求扩展为批量。
- 默认保留 `is_start_trigger=false`，除非用户明确要求触发。
- 工作流表单只有在用户明确要求时才设置 `is_start_workflow=true`。
- 修改子表单时保留每一条原有行 `_id`，并展示完整拟写入子表。
- 写操作遇到超时或限流时不要自动重试；先回读确认是否已生效。
- 删除、流程回退、流程终止和否决属于破坏性操作，必须再次核对精确ID。
- 加签必须由用户明确选择 `before` 或 `after`，不得使用默认值或替用户推断。
- `jdy_get_corp_user` 不能判断普通成员、管理员、企业创建者或数据权限；没有独立证据时必须说明无法判断。

## 按需读取参考

- 全部39项工具与风险等级：`references/tool-index.md`
- 应用、表单和字段：`references/apps-and-forms.md`
- 数据增删改查与文件上传：`references/data.md`
- 流程查询与审批动作：`references/workflow.md`
- 成员、部门和角色：`references/contacts.md`
- 用量统计和审计日志：`references/audit-and-usage.md`
- 字段值和筛选器格式：`references/field-values.md`
- 官方API完整目录：`references/official-api-index.json`
- 39项工具与官方文档映射：`references/tool-doc-map.json`

只读取当前任务相关的参考文件。完整参数以 `schemas/*.json` 和 `tool-help` 输出为准。
