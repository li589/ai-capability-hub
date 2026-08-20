# 完整局域网本地部署 ZIP 交付合同

当用户要求“本地部署”“局域网完整包”“源码 ZIP”“完整 PY”“打包 EXE”中的任一项，且未明确只分析或只要桌面版时，优先执行本合同。

## 1. 基准架构与生成前健康检查

技能内置 `resources/lan-energy-daily-report-reference.zip`，作为**完整代码架构基线**，保证生成系统不是空壳。它不是当前用户的业务事实来源。

正式展开前先执行只读健康检查：

```text
python scripts/ensure_full_lan_energy_system.py --check-only
```

必须检查：ZIP 可读、CRC、安全路径、重复规范化路径、符号链接样式成员和核心源码/前端/启停/备份/EXE 构建文件齐全。

通过后再写入：

```text
python scripts/ensure_full_lan_energy_system.py <项目目录> --overwrite
```

实际展开先进入临时 staging 目录并验证完整，再复制到目标项目。之后根据当前用户资料修改系统名、字段、业务规则、组织/产线、能源类型、目标、价格、展示文案、导入映射和初始化数据。用户资料与基线冲突时，以用户资料为准。

## 2. 强制源码

最终 ZIP 至少保留：

```text
01_服务端_完整程序/
├─ server.py
├─ backend_core.py
├─ energy_excel_import.py
├─ backup_restore.py
├─ port_config.py
├─ launcher.py
├─ stop_server.py
├─ app.py
├─ wsgi.py
├─ exe_entry.py
├─ build_exe_windows.py
├─ energy_daily_report_exe.spec
├─ requirements.txt
├─ seed_data.json（若使用）
├─ templates/
├─ static/
├─ vendor/（若采用离线内置依赖）
├─ data/
└─ logs/
```

默认主界面是 `templates/` + `static/` 驱动的浏览器 Web 界面。可选 Tkinter 独立版不能作为主交付。

不能用单一 HTML、伪代码、只有 `subprocess` 的启动壳、只有 EXE、只有数据库或简化桌面程序替代完整源码。

## 3. 一键启动/停止合同

- Windows 至少成对提供 `start_windows.bat` + `stop_windows.bat`；
- macOS 如提供可双击启动，则同时提供对应停止入口；
- 启动和停止共享端口配置、PID/状态记录；
- 停止脚本只停止本项目实例，不得全局结束其他 Python 进程；
- 缺 Python 时只提供已验证安装包/手工安装引导，不静默下载、不自动提权。

## 4. 备份与恢复合同

主 Web 系统必须有 `backup_restore.py`（或等价完整源码）：

- 使用 SQLite backup API 或等价一致性安全方式；
- 备份后执行 `PRAGMA integrity_check`；
- 恢复前校验备份并确认服务已停止；
- 覆盖当前数据库前先生成回滚副本；
- 出错时不删除现有数据库或最近备份。

## 5. EXE 构建合同

`exe_entry.py` 是完整 Web 系统 Windows EXE 入口；运行数据应持久化到 EXE 同级 `data/`。

`build_exe_windows.py` 使用用户/IT 已批准安装的 PyInstaller；不得静默联网、静默安装、提权或绕过系统安全策略。构建至少纳入：

- `templates/`
- `static/`
- `vendor/` 或等价依赖
- `seed_data.json` / 必要配置
- 完整 Python 模块依赖

默认推荐 `onedir`，可提供 `--onefile`。

## 6. 数据与隐私

基线不得把其他系统的生产数据库、日志、PID、缓存或 pyc 当作新项目数据。正式项目只导入当前用户明确提供的数据并保留来源映射。

若用户没有真实业务文件，只能生成明确标记为 `prototype/demo` 的评审原型；不能把样例数据写成真实生产事实。

## 7. 校验

先运行：

```text
python scripts/validate_full_lan_delivery.py <项目目录>
```

再生成 ZIP：

```text
python scripts/package_local_deployment.py <项目目录> <输出.zip> --root-name <系统名>
```

打包脚本生成：

- `00_请先看_交付导航.md`
- `DELIVERY_STATUS.json`
- `PY_SOURCE_MANIFEST.json`
- `FILES_SHA256.txt`
- 单根目录 ZIP

打包后新建临时目录独立解压，再检查核心 Python、Web 模板/静态资源、启停、备份和 EXE 构建源码仍存在。

## 8. 对用户的完整正式交付定义

只有同时满足以下条件才可以说“完整正式交付已完成”：

1. 用户能下载一个 ZIP；
2. ZIP 是完整本地部署目录，不是代码片段集合；
3. 真实业务文件已映射，或关键不确定项明确进入待确认；
4. ZIP 保留整个系统 Python 源码；
5. ZIP 有完整 EXE 构建源码；
6. 核心 Python 语法和关键本地功能自检通过；
7. 主 Web UI 完整且响应式；
8. 备份/恢复至少完成临时数据库自检；
9. ZIP 独立解包后结构完整；
10. 未在 Windows 真机测试 EXE 时明确标记“未真机验证”。

没有真实业务文件的 prototype 可以交付，但必须使用“原型/待确认”状态，不适用上述“生产正式验收完成”措辞。
