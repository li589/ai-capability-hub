# 独立 PY 能源日报交付指南（按需附加）

## 什么时候使用

只有用户明确要求“独立桌面版 / 单文件 PY / 不启 Web 服务的桌面程序”时，才把 `standalone/energy_daily_report.py` 写入生成项目。默认“完整本地部署 / 局域网系统”主交付是浏览器 Web 系统，不强制附带 Tkinter，以减少文件数量和界面误解。

## 附带时的强制文件

使用技能模板写入项目：

```text
python scripts/ensure_energy_daily_standalone.py <项目目录> --overwrite
```

该文件必须是完整源码，不得只是导入 Web 项目的薄封装，也不得只交付 EXE。

## 必须验收

```text
python standalone/energy_daily_report.py --self-test
```

自检返回码必须为 0，且 JSON 中 `ok` 为 `true`。验收证据中记录命令、Python 版本、操作系统、执行时间和输出。

## 用户运行方式

```text
python standalone/energy_daily_report.py
```

指定数据库：

```text
python standalone/energy_daily_report.py --db ./data/energy_daily.db
```

## EXE

Windows 用户可运行 `standalone/build_exe_windows.py`。未完成 Windows 真机实际构建和运行时，只能说“提供 EXE 构建源码”，不得说“已包含可直接双击的已验证 EXE”。
