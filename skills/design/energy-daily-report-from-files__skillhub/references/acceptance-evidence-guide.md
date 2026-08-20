# 机器可读验收证据

`ACCEPTANCE_EVIDENCE.json` 必须由真实测试运行生成。模板保持 `pending`，含 `template_notice`，交付校验器必须拒绝把模板当作真实通过。

每个用例记录：ID、状态、命令、退出码、执行时间、环境和可复核证据。状态为 passed 时必须退出码为 0 且有证据路径或摘要。

完整 Web/LAN 系统至少覆盖数据库初始化、CRUD、业务主键、数据范围、403、409、流程/状态、审计前后值、看板指标、响应式布局、导入导出回读、幂等、接口未配置、自检、构建恢复、数据库完整性、备份恢复、安全控制、中文区域和离线依赖。是否存在“审批退回”应按真实业务蓝图判断，不得为了固定模板凭空增加多人审批。

Windows、macOS、WPS/Office、EXE 和外部接口真机状态独立记录；未执行写 null 或 not_run，不得推断通过。

## 独立桌面版证据是条件项

只有最终交付实际附带 `standalone/energy_daily_report.py` 时，才要求 `standalone_energy_self_test` 用例：

```text
python standalone/energy_daily_report.py --self-test
```

证据应记录 JSON 输出，确认数据库初始化、CRUD、计算、汇总、导出、备份和完整性检查由真实命令执行。

如果用户没有要求独立桌面版、最终完整 Web/LAN ZIP 也未附带 `standalone/`，则不应因缺少这条桌面自检证据判定 Web 系统不完整。

EXE 构建与运行证据必须与源码自检分开记录。
