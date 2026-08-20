# {{SYSTEM_NAME}} 运行说明

1. 启动入口会按顺序优先使用已构建 EXE、`portable_runtime`、`.venv_windows`，最后才使用系统 Python。若只有系统 Python，启动器会创建项目专属虚拟环境并按 `requirements.txt` 安装依赖。
2. 双击 `start_windows.bat` 启动；默认仅监听本机 `127.0.0.1`，浏览器访问启动器显示的地址。需要局域网共享时再显式设置 `APP_HOST`。
3. 首次管理员随机密码位于 `data/首次管理员凭据.txt`，登录后立即修改。
4. 双击 `stop_windows.bat` 安全停止；它通过本项目运行状态与 shutdown token 停止当前实例，不得全局结束 `python.exe`。
5. 数据库：`data/app.db`；备份：`python backup_restore.py backup`。恢复前必须先停止本项目服务。
6. 启动失败、端口冲突、数据库异常时，双击 `诊断_一键诊断.bat` 生成诊断结果。
7. 在目标 Windows 电脑交付前，双击 `验收_目标电脑.bat` 执行环境、启动、健康检查与安全停止验收；业务差异功能需在本项目测试中补充验收。
8. 测试与真机状态分别查看 `TEST_REPORT.md`、`RUNTIME_ACCEPTANCE.md` 和 `DELIVERY_STATUS.json`，未执行项不得写成已验证。

9. `portable_full` 模式下，普通填写用户不要进入服务端目录，使用根目录 `02_Windows填写客户端/` 设置并测试服务器地址。
10. 只有 DELIVERY_STATUS 明确验证通过时，才能把系统描述为“免 Python”或“首次安装完全离线”。
