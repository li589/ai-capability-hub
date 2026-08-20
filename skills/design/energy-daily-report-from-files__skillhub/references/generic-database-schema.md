# 通用数据库合同

## 平台必需表

- `schema_migrations`
- `users`、`roles`、`permissions`、`role_permissions`、`user_permissions`
- `business_entities`、`business_records`、`record_versions`
- `workflow_definitions`、`workflow_instances`、`workflow_actions`、`approval_records`
- `import_batches`、`import_errors`
- `integration_endpoints`、`integration_runs`
- `audit_log`、`system_settings`、`backups`

业务复杂时可按实体生成专用规范化表，但上述通用安全与流程表仍必须保留。业务记录至少携带组织范围、业务主键、状态、版本、创建/修改人和时间、来源批次。

## SQLite 约束

启用 WAL、`busy_timeout`、外键和参数化 SQL；使用短事务和唯一索引。迁移记录版本与校验和，迁移前备份，迁移后执行 `integrity_check` 与 `foreign_key_check`。不得静默删除字段或重算历史。

## 审计

关键修改记录实体、记录 ID、动作、前值、后值、理由、操作者、时间、来源 IP/会话和规则版本。应用层不得提供普通删除审计日志的入口。
