# 交付文件地图：按角色找文件

文件多不代表用户要全部阅读。把文件按“谁需要看”分成四层。

## 第 1 层：普通使用者

只需要认识：

- `00_请先看_交付导航.md`：第一入口；
- `一键启动_Windows.bat`：启动；
- `一键停止_Windows.bat`：停止；
- 当前服务器地址文件：局域网访问地址；
- `DELIVERY_STATUS.json`：只有需要确认 EXE/测试状态时再看。

普通使用者**不需要**进入 `vendor/`，也不需要阅读后端源码。

## 第 2 层：IT / 运维

重点看：

- `01_服务端_完整程序/README_部署说明.txt`
- `01_服务端_完整程序/port_config.py`
- `01_服务端_完整程序/launcher.py`
- `01_服务端_完整程序/stop_server.py`
- `01_服务端_完整程序/backup_restore.py`
- `01_服务端_完整程序/README_BACKUP_RESTORE.md`
- `01_服务端_完整程序/README_EXE打包说明.md`
- `01_服务端_完整程序/requirements.txt`

目的：部署、端口、依赖、启停、备份、恢复、构建 EXE。

## 第 3 层：开发 / 二次开发

重点看：

- `server.py`：Web/API 路由；
- `backend_core.py`：数据库、业务计算、权限、汇总；
- `energy_excel_import.py`：Excel 导入；
- `templates/`：页面结构；
- `static/`：CSS/JS；
- `exe_entry.py`、`build_exe_windows.py`、`*.spec`：EXE 构建；
- `PY_SOURCE_MANIFEST.json`：第一方与第三方源码边界。

## 第 4 层：审计 / 验收

重点看：

- `FILES_SHA256.txt`：文件完整性；
- `DELIVERY_STATUS.json`：交付事实状态；
- 测试报告 / 验收证据；
- 字段映射与假设文件；
- 权利、第三方和安全声明。

## 为什么 `vendor/` 很大

`vendor/` 是为离线运行准备的第三方依赖源码/包内容。它通常占文件数量的大多数，但并不代表系统业务源码“杂乱”。`PY_SOURCE_MANIFEST.json` 应将第一方核心源码与第三方依赖分开统计。

## 找不到入口时的规则

1. 先回根目录；
2. 找 `00_请先看_交付导航.md`；
3. 只要是“怎么启动/怎么停/怎么备份”，不要先翻源码；
4. 只有二次开发才进入 `01_服务端_完整程序/` 深层目录。
