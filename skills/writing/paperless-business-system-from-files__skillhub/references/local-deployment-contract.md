# 完整本地部署交付契约
> **2.5.1 平台兼容说明**：本文件描述的是“最终业务系统 ZIP”的真实交付文件名。技能包本体不直接携带 `.bat/.spec`，而是使用 `_platform_templates/*.txt`，由 `create_project_scaffold.py` 在生成系统时还原。不得因为技能包内部模板改名而省略最终系统中的真实启停 BAT 或 PyInstaller spec。


## 默认交付类型

如果 `system.deployment_mode=portable_full`，还必须读取 `references/portable-full-contract.md` 并满足额外目录、客户端、局域网工具和运行时状态门禁。

用户说“生成系统”“做成本地系统”“做局域网系统”时，默认交付可运行项目 ZIP。只有用户明确说只要原型/方案时才允许不生成完整项目。

## 必须包含

- 完整第一方 Python 源码、`templates/`、`static/`、SQLite 初始化/迁移；
- 导入导出、服务端权限、审计、备份恢复；
- `start_windows.bat` + `stop_windows.bat`，成对且只控制本项目实例；
- `诊断_一键诊断.bat`（或 `diagnose_windows.bat`）及诊断代码；
- `验收_目标电脑.bat` + `target_pc_acceptance.py`（或等价入口）；
- `requirements.txt`、EXE 入口/构建脚本/PyInstaller `.spec`；
- `README_运行说明.md`、`README_EXE打包说明.md`、`RUNTIME_ACCEPTANCE.md`；
- `BUSINESS_RECOGNITION_REPORT.md`、`INPUT_COMPLETENESS_REPORT.md`、`VALUE_REPORT.md`；
- 测试、`00_请先看_交付导航.md`、`DELIVERY_STATUS.json`、`PY_SOURCE_MANIFEST.json`、`FILES_SHA256.txt`。

## 启停安全硬规则

1. 启动和停止脚本必须位于同一交付目录并共享 PID/状态文件或等价唯一实例标识。
2. 停止脚本禁止 `taskkill /IM python.exe`、`taskkill /F /IM pythonw.exe`、`killall python`、`pkill -f python` 等全局方式。
3. 启动失败必须保留窗口或写入可定位日志，用户不能只看到闪退。
4. 端口冲突、数据库锁定、依赖缺失等必须给出稳定错误码和修复动作。

## 一键诊断

诊断至少检查：Python/运行时、依赖完整性、配置可读性、端口、数据目录写权限、SQLite 完整性、templates/static、最近启动日志、PID 状态和离线外链。报告必须写清“检查项、结果、证据、错误码、处理、恢复点”。未知异常使用 `PB999`，同时保留管理员日志位置。

## 目标电脑验收

目标 Windows 电脑上至少执行：

1. 环境与依赖检查；
2. 启动并确认健康页/端口；
3. 登录或最小核心业务冒烟；
4. 写入一条测试数据并重启确认持久化（使用隔离测试库或可回滚数据）；
5. 导入/导出最小样例；
6. 备份完整性检查；
7. 正常停止并确认只结束本项目进程；
8. 生成 `RUNTIME_ACCEPTANCE.md/json`。

没有目标机时可以交付验收入口，但必须把 `target_pc_smoke_verified=false` 和未执行原因写入 `DELIVERY_STATUS.json`。静态代码检查不能替代真机稳定性结论。

## 源码与第三方依赖

`PY_SOURCE_MANIFEST.json` 分开统计 `first_party` 和 `vendor`。核心源码必须可定位到入口、数据库、业务计算、导入导出、权限、诊断、备份恢复。

## EXE 状态

有构建脚本 ≠ 已有 EXE；有 EXE ≠ Windows 真机验证通过。只有真机完成启动、核心流程、持久化、停止/重启后，才可设置 `windows_exe_runtime_verified=true`。

## 数据目录与恢复

数据库、上传、导出、备份、日志位于项目/EXE 同级可写目录。升级前备份；恢复前校验并生成当前库回滚副本；迁移失败必须回滚或给出恢复点。

## ZIP 二次验证

最终 ZIP 必须重新解压到全新目录，再执行清单哈希、源码、启停、诊断和目标机验收入口的静态检查。只有实际完成后才能标记 `zip_reextract_verified=true`。


## 2.2 安全生命周期补充

推荐写入项目专属运行状态：`app_id`、`pid`、`port`、`url`、`start_time`、随机 `shutdown_token`。停止脚本应优先调用本机项目专属 shutdown 入口并验证随机令牌；停止过程中写 `stopping` 状态。若用户在停止尚未完成时再次启动，启动器必须等待旧实例退出和端口释放，避免误判“仍在运行”或启动双实例。