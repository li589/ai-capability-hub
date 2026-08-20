# 已知问题、回滚、FAQ 与版本演进

> 何时加载：排查故障、准备回滚、核对版本功能时。

## 已知问题

### DB 索引损坏导致 UNIQUE constraint failed

症状：
```
sqlite3.IntegrityError: UNIQUE constraint failed: sessions.id
```

根因：`workbuddy.db` 的 `sqlite_autoindex_sessions_1` 损坏。导出脚本内置了自动修复（`_dedup_duplicate_pks`），会在打包前对源 DB 副本执行 PK 去重 + REINDEX。正常情况下用户无需关心。

### macOS 上 Python 报 PermissionError

```
PermissionError: [Errno 1] Operation not permitted
```

若发生在 WorkBuddy agent 沙箱内 → 优先尝试系统 Python → 若无效则引导用户放开沙箱。若在终端手动执行 → 在系统设置中为该 Python 授予完全磁盘访问权限。

### 工作区路径含 `#` 字符

Windows / Linux / macOS 均允许文件名含 `#`，迁移按目录名原样复制不会丢失。但客户端 5.2.6 之前对含 `#` 的文件预览 / 链接存在乱码；若源端工作区路径含 `#`，导入后建议将客户端升级到 5.2.6+ 以正常预览。

### 专享版禁用 Memory 个性化

部分专享版套餐禁用了 Memory 个性化功能，源端可能不存在 `memory/` 目录。迁移助手对 `memory/` 为可选资产（skip-if-exists），源端无则跳过，不影响其他资产迁移。

### 对话消息含 reasoning-only / `@同事` 附件

5.2.6 起对话消息可能出现仅含推理过程、无正文的 `reasoning-only` 消息，以及 `/compact` 指令引用的 `@同事` 附件。迁移按 session 原样复制 `projects/*.jsonl`，结构兼容；跨机器后 `@同事` 附件若指向其他用户 / 会话可能失效，属预期行为，无需特殊处理。

### 连接器凭证实际存放于 `tokens/`

连接器凭证实际位于 `connectors/<uid>/tokens/` 目录，而非 `.credentials.json`。`--no-credentials` 仅排除 `.credentials.json`，**不会**排除 `tokens/`。跨机器迁移连接器建议导入后到连接器面板重新授权，或手动删除目标端 `tokens/` 再授权。

### MEMORY.md 与 memory/ 双轨记忆（5.3.3+）

5.3.3 起个性化页新增本地长期记忆展示与编辑，根级 `MEMORY.md` 与 `memory/{uid}_memory.md` 双轨并存。迁移助手两者均覆盖：`MEMORY.md` 用 `imported-suffix` 合并（目标端已有则写入 `MEMORY.imported.md`，不污染目标端记忆），`memory/{uid}_memory.md` 用 `append-with-separator`。若源端只有其一，另一轨自动跳过。

### 连接器技能包 connectors/skills/（5.3.11+）

5.3.11 起连接器附带的技能包（`connector-*`）存放于 `connectors/skills/`。迁移按目录 skip-if-exists：目标端已有同名连接器技能包则跳过整个目录，属预期行为（连接器版本可能不同）。该目录随连接器安装自动生成，源端无则跳过。

### 投递队列与 ORM 记录不迁移

`automation_delivery_outbox`（投递出站队列，含敏感 payload_json）与 `__workbuddy_drizzle_migrations`（ORM 迁移记录）为运行时/内部状态，**不迁移**。导出时白名单机制天然排除；若目标端 DB 已存在同名表，导入不会触碰。

## 回滚步骤

导入前脚本会自动备份目标端文件为 `<name>.bak-<timestamp>`：

```
~/.workbuddy/workbuddy.db.bak-20260615-092435
~/.workbuddy/settings.json.bak-20260615-092435
~/.workbuddy/mcp.json.bak-20260615-092435
~/.workbuddy/memory/<uid>_memory.md.bak-20260615-092435
...
```

回滚方法：
1. 退出 WorkBuddy
2. 在目标根目录下执行：
   ```bash
   cd ~/.workbuddy
   ts=20260615-092435  # 改成实际备份时间戳
   for f in *.bak-$ts memory/*.bak-$ts; do
     mv "$f" "${f%.bak-$ts}"
   done
   ```
3. 启动 WorkBuddy 验证

备份**不会自动清理**，确认无误后手动删除。

## FAQ

**Q: 国内版和海外版的 DB schema 一样吗？**
A: 完全一致。脚本用 `PRAGMA table_info` 做列交集 INSERT，即便未来一边加字段也能兼容（多余列丢弃并 warn）。

**Q: 包里多大？**
A: 不含对话时几 MB（skills 多可能更大）；含对话记录可能几百 MB 到几 GB。建议先 `--no-conversations` 试一次。

**Q: 迁移包里的 `.credentials.json` 安全吗？**
A: 含 access_token / refresh_token 明文。**不要传到不可信通道**。推荐用 `--no-credentials` 导出，到目标端重新授权。

**Q: 我有多个 user_id，怎么办？**
A: 使用 `--auto-map` 会自动将所有源 uid 映射到目标端当前 uid。如需手动控制，用 `--uid-map src=dst` 逐条指定。

**Q: 跨平台迁移后对话打不开？**
A: 使用 `--auto-map` 可自动处理路径映射。若仍有问题，检查恢复后校验报告中 workspace 目录不存在的条目。

## 版本演进说明

- **v0.4.0**：导出支持 `--format tar.gz` 输出格式
- **v0.3.0**：新增 `info.py` 检视命令；纳入 tasks/teams/sessions/local_storage/traces/file-history/experts 资产
- **v0.2.0**：新增 `--auto-map` 自动路径映射；新增恢复后自动校验
- **v1.0.4**（2026-07-20）：适配 WorkBuddy 5.2.6——修正连接器状态文件名为 `connector-states.v3.json`；修复 sessions 进行中态 `working` 漏排除的 P0 缺陷；补充已知问题（`#` 路径、专享版 Memory、reasoning-only/`@同事`、tokens/ 凭证位置）
- **v1.1.0**（2026-07-31）：渐进式披露重构——SKILL.md 精简至入口+关键约束，命令/流程/冲突/已知问题下沉 references/（本目录）
- **v1.2.0**（2026-08-11）：适配 WorkBuddy 5.3.11——白名单纳入 MEMORY.md/connectors/skills/automation-backups/brain/todos/plans/deliverables；DB 不迁表声明 automation_delivery_outbox/__workbuddy_drizzle_migrations；排除 blobs/backup/shell-snapshots/cache/edge-sync-mapping.db 等；补充双轨记忆与连接器技能包已知问题
