---
name: sloth-d2c-skills
description: 将Figma设计稿转换为前端组件代码（Design to Code）。通过MCP工具获取设计稿数据，分片处理并生成最终代码。当用户提到Figma转代码、设计稿转代码、D2C、design to code、生成页面时使用。
allowed-tools: null
disable: false
install_source: official
install_method: download
skill_id: official_KUe7GuY5
enabled_at: 1787232322122
version: 1.0.0
name_zh: Figma 设计稿转代码技能
---

# Figma 设计稿转代码（D2C）

> 仅支持在主Agent中使用该Skill，不要在命令行执行MCP Tool。

## 前置校验

### 必需参数

| 参数    | 说明           |
| ------- | -------------- |
| fileKey | Figma 文件 Key |
| nodeId  | Figma 节点 ID  |

缺少以上参数时，提示用户提供。

### 可选参数

depth（节点深度）、local（缓存）、update（更新模式）、silent（静默模式）、framework（框架）

### 环境检查

确认 `#d2c_figma` MCP Tool 可用。不可用则跳转[错误排除](#错误排除)。

## 执行流程

```
Task Progress:
- [ ] Step 1: 执行 MCP
- [ ] Step 2: 并行处理代码片段与聚合
- [ ] Step 3: 生成最终代码并写入文件
```

### Step 1：执行 MCP

使用Skills调用 `#d2c_figma` MCP Tool，使用本地数据缓存，非静默模式，传入 fileKey、nodeId 等参数。

### Step 2：并行处理代码片段与聚合

**路径变量**：将 nodeId 中的 `:` 替换为 `_`，得到 `convertedNodeId`。
启动多个 sloth-d2c-agent subagent，**并行执行**以下两类任务：

| 任务                 | 提示词路径                                                     |
| -------------------- | -------------------------------------------------------------- |
| 代码片段处理（多个） | `.sloth/{fileKey}/{convertedNodeId}/chunks/{index}.md`         |
| 聚合处理             | `.sloth/{fileKey}/{convertedNodeId}/chunks/codeAggregation.md` |

全部 Subagent 完成后进入下一步。

### Step 3：生成最终代码并写入文件

主Agent收集第2步执行完毕的结果，结合读取.sloth/{fileKey}/{convertedNodeId}/chunks/finalGenerate.md的内容作为提示词转换代码，写入项目文件中。

## 错误排除

| 错误类型                | 处理方式                                                                                           |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| 查不到 MCP Tool         | 提示用户检查 MCP Tool 是否可用                                                                     |
| 端口错误                | 执行 `sloth server restart` 后重试                                                                 |
| 文件不存在              | 提示用户检查路径，**停止执行**                                                                     |
| MCP Timeout             | 提示用户增加超时配置：TME-Continue 的 connectionTimeout / CodeBuddy 的 timeout                     |
| 403 错误                | 未配置有效 Token，提示用户配置                                                                     |
| 404 错误                | 设计稿未找到，提示用户核实 fileKey 和 nodeId                                                       |
| MCP Tool 未找到         | 执行 `sloth -v`：有版本号则提示配置 MCP Server；无版本号则执行 `npm install -g sloth-d2c-mcp` 安装 |
| 引入node internal包报错 | 检查用户node版本是否大于等于18                                                                     |
