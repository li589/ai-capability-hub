# 交付验收清单

> 本清单用于“完整正式 Web/LAN 交付”。如果用户明确要求 prototype，则真实业务文件映射、正式历史导入和生产验收应标记 not_run，而不是伪造通过。

- [ ] 完整正式模式至少有一个安全、可读且有效的真实输入文件；prototype 模式则明确标记没有真实业务映射。
- [ ] 分析报告、输入指纹、业务蓝图、字段映射和假设完整。
- [ ] 系统不是静态 HTML 或空壳；真实主流程可增删改查。
- [ ] 登录、首次改密、CSRF、403、409、数据范围和审计通过。
- [ ] 工作流按当前业务蓝图验证：若用户采用双确认流程，则验证双方确认与历史保留；只有资料明确存在审批/退回时才强制验证审批/退回。
- [ ] 导入幂等、逐行错误、导出回读和来源追溯通过。
- [ ] 数据库迁移、WAL、完整性、外键通过；`backup_restore.py` 至少完成临时数据库备份、完整性校验与显式恢复测试。
- [ ] 看板指标由后端统一计算，零分母和缺失值中性处理。
- [ ] 未配置接口显示“未配置”，没有虚构实时数据。
- [ ] Windows/macOS 启动、自检、离线依赖助手和 Python 安装包只读验证引导齐全。
- [ ] 验收证据来自真实命令，不是 pending 模板。
- [ ] ZIP 无虚拟环境、缓存、危险路径、凭据或无关源文件。
- [ ] `VERSION.txt`、`SKILL_VERSION.json`、README、安全审计、构建状态模板和测试夹具版本一致。
- [ ] 组合或非标准业务已由场景分类器给出明确判断，关键复杂边界进入待确认。
- [ ] 一键检查输出中文进度、恢复点、下一步和数据保护说明。
- [ ] 失败场景使用稳定错误码，自动重试只覆盖白名单且不超过两次。
- [ ] 完整输出示例覆盖登录、看板、主流程、跨模块闭环、导入、追溯、恢复和 ZIP 导航。
- [ ] 内置完整局域网基线已通过 `python scripts/ensure_full_lan_energy_system.py --check-only`，并记录基线 SHA-256。
- [ ] 触发模式与最终交付一致：完整系统/旧系统修改/只分析/prototype/桌面版没有相互混淆。
- [ ] 根目录入口与 `delivery-file-map.md` 一致，普通用户无需阅读 `vendor/` 或全部源码。
- [ ] ZIP 已在全新目录独立解包并再次通过测试和交付校验。
- [ ] `VERSION.txt` 作为唯一发布版本来源，`validate_version_consistency.py` 无旧版本残留。
- [ ] 增值报告来自真实蓝图和只读数据库证据；缺数据时没有伪造指标或趋势。
- [ ] `reports/value-added-manifest.json` 覆盖摘要、图表、驾驶舱和数据质量报告及其 SHA-256。
- [ ] `DOMESTIC_READINESS.json` 已检查中文区域、GB18030、离线依赖、外部资源、个人信息、CNY 舍入和业务月边界。
- [ ] Python 安装配置没有占位符；验证脚本不下载、不运行安装器、不提权，未完成核验时不得提示用户安装。
- [ ] 国内准备度报告没有被表述为法律、税务、会计或电子签名合规意见。
- [ ] `_meta.json.slug`、`SKILL_VERSION.json.name`、SKILL frontmatter、产权 `work_id` 和显示名一致。
- [ ] 若用户明确要求独立桌面版，才附带完整 `standalone/energy_daily_report.py`，且不得是启动壳。
- [ ] 若附带独立桌面版，`python standalone/energy_daily_report.py --self-test` 返回码为 0，验收证据包含真实输出。
- [ ] 若附带独立桌面版，同时附带其 EXE 构建脚本、独立运行说明、依赖文件和清单。
- [ ] EXE 未经 Windows 真机验证时明确标记 `not_run`，不推断打包或运行通过。

- [ ] ZIP 根目录包含 `00_请先看_交付导航.md` 与 `DELIVERY_STATUS.json`，普通用户无需浏览 `vendor/` 即可找到启动、备份和开发入口。
- [ ] `DELIVERY_STATUS.json` 不把“存在构建脚本”误报为“已包含/已验证 EXE”。
- [ ] Web 主界面包含 viewport 和响应式样式；Tkinter 可选工具未被描述为主界面。

- [ ] 一键启动/停止入口成对交付：Windows `start_windows.bat` + `stop_windows.bat`；macOS（如支持）`start_macos.command` + `stop_macos.command`，并确认停止脚本只停止本项目实例。
