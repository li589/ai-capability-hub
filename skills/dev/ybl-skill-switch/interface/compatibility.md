# 兼容性声明（ybl-skill-switch）

> 类型：命令式管理 Skill（**非管线型**，不串接其他 Skill 的产出）
> 可独立使用：是（本就是独立工具，无上游 / 下游依赖）

## 作用域边界
- 只扫描与管理 `~/.workbuddy/skills/`（**用户级** Skill）
- 不碰 `plugins/`、`connectors/`、平台内置 Skill
- 只改各 Skill 的 `disable` 字段，不删除文件、不改其他内容
- 永不禁用 ybl-skill-switch 自身（禁用了自己就无法再启用自己）

## 类别过滤
- 按各 Skill `SKILL.md` 的 `description` 关键词匹配，**不维护额外标签**

## 接口契约说明
- 本 Skill 为命令式：输入 = 用户自然语言指令，输出 = 给人看的文本报告，**无结构化 input/output 契约需求**
- 故按 A 方案仅保留 `compatibility.md`，不提供 `input.schema.json` / `output.schema.json`（避免空壳形式化文件）
- 若未来改为被管线调用的结构化组件，再补 schema
