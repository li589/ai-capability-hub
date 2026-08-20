# wecom-deep-op 变更日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-03-22

### 🎉 正式发布

**核心特性**:
- ✅ 基于企业微信官方插件 `@wecom/wecom-openclaw-plugin` v1.0.13+
- ✅ 一站式企业微信自动化解决方案
- ✅ 统一封装 5 大服务：文档、日历、会议、待办、通讯录
- ✅ 完整的 OpenClaw MCP 集成：`wecom_mcp call wecom-deep-op.<function>`
- ✅ 智能配置引导：每个 API 自动返回配置步骤
- ✅ 生产就绪：参数验证、错误重试、日志系统
- ✅ 安全设计：无数据存储、用户可控凭证、最小权限原则

**支持的 API** (27个接口):
- 📄 文档管理：`doc_get`, `doc_create`, `doc_edit`
- 📅 日程管理：`schedule_create`, `schedule_list`, `schedule_get`, `schedule_update`, `schedule_cancel`, `schedule_add_attendee`, `schedule_remove_attendee`
- 📹 会议管理：`meeting_create`, `meeting_list`, `meeting_get`, `meeting_cancel`, `meeting_update_attendees`
- ✅ 待办管理：`todo_create`, `todo_list`, `todo_get`, `todo_update_status`, `todo_update`, `todo_delete`, `todo_accept`, `todo_refuse`
- 👥 通讯录：`contact_get_userlist`, `contact_search`
- 🔧 系统：`ping`, `preflight_check`

**技术细节**:
- TypeScript 开发，Rollup 构建（CJS + ESM）
- 完整类型定义（.d.ts）
- 环境变量 + mcporter.json 双配置源
- 异步任务轮询（文档导出）
- 指数退避重试（网络错误）
- MIT 协议开源

**安全与合规**:
- 🔒 不存储任何企业微信凭证
- 📝 清晰的日志分级（debug/info/error）
- 🌐 数据流向透明：用户控制端点、用户提供文件
- ⚠️ 通讯录权限限制提示（仅返回可见范围成员）
- 📊 通过 OpenClaw 安全审计（5/5 生产就绪）

**文档**:
- 完整的 `SKILL.md` 技能说明
- 详细的 `README.md`（含快速开始、故障排除）
- 示例代码和调用指南
- 贡献指南和 MIT 协议

---

## [历史版本]

> **注意**：v1.0.0 之前的版本（1.0.1 - 1.0.5）已被重置，历史记录已清理。
> 这些版本包含的功能已全部整合到当前 v1.0.0 中。
