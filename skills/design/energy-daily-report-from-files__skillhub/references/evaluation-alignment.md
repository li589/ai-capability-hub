# 评测口径对齐

用于避免外部评测把“存在能力模板”误判为“当前主交付已验证能力”，也避免因文档分散造成触发和边界扣分。

| 评测表述 | 正确判定依据 |
|---|---|
| 版本号一致 | `VERSION.txt`、`SKILL_VERSION.json`、`_meta.json`、构建状态模板和发布文档通过 `validate_version_consistency.py` |
| 触发方式清晰 | `START_HERE.md` + `trigger-and-mode-guide.md` 明确完整系统、旧系统修改、只分析、原型、桌面和指导六种模式及优先级 |
| 主界面现代/易用 | 完整局域网模式看 Web `templates/` + `static/`；可选 Tkinter 不代表主系统 UI |
| 文件数量可理解 | `delivery-file-map.md` 按普通用户 / IT / 开发 / 审计分层，manifest 区分第一方与 `vendor/` |
| 双击即用 | 只有已有 Python 的脚本启动，或 ZIP 实际带已构建 EXE 时成立；必须写明前置条件 |
| 已有 EXE | `DELIVERY_STATUS.json` 明确 `built_exe_included=true`，不能由 build 脚本存在推断 |
| EXE 已验证 | 必须有 Windows 真机构建与启动证据；静态检查不能代替 |
| 自动备份/恢复 | 主 Web 系统存在 `backup_restore.py`/等价工具，且有真实备份、校验、恢复测试证据 |
| 基线可靠性 | `ensure_full_lan_energy_system.py --check-only` 通过 ZIP/CRC/路径/核心文件健康检查；实际展开先 staging 验证 |
| 工作流完整 | 按用户业务蓝图评价；没有多人审批的真实业务不应被固定审批模板扣分 |
| 原型真实性 | 无真实业务文件时允许 prototype，但必须标记 demo/待确认，不能伪造真实历史数据和生产验收 |
| 能力边界集中 | `capability-boundaries.md` 统一说明可直接做、需确认、禁止自动化和证据等级 |
| FAQ/异常处理 | `faq-and-troubleshooting.md` + `reliability-runbook.md` 提供中文最短路径、恢复点和数据保护原则 |
