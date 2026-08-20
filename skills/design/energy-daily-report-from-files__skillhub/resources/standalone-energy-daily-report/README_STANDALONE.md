# 独立 PY 能源日报

本目录必须随本地部署文件一起交付。`energy_daily_report.py` 是一份完整、可独立运行的桌面程序，不依赖 Web 系统即可使用。

## 直接运行

```bash
python energy_daily_report.py
```

默认数据库写入当前用户可写的数据目录，不会写入 Python 安装目录，也不会联网。

指定数据库：

```bash
python energy_daily_report.py --db ./data/energy_daily.db
```

## 自检

```bash
python energy_daily_report.py --self-test
```

自检覆盖数据库初始化、新增、修改、计算、汇总、CSV 导出、备份、完整性检查和删除。返回码为 0 才算通过。

## 导入与导出

```bash
python energy_daily_report.py --db ./data/energy_daily.db --import-file ./能源日报.csv --no-gui
python energy_daily_report.py --db ./data/energy_daily.db --export-file ./能源日报.xlsx --no-gui
```

CSV 无额外依赖；XLSX/XLSM 需要 `openpyxl`。

## 打包成 Windows EXE

1. 安装 Python 3.10 或更高版本。
2. 在本目录运行 `build_exe_windows.py`。
3. 成功后 EXE 位于 `dist/energy_daily_report.exe`。

构建脚本会在当前 Python 环境安装 `openpyxl` 和 `pyinstaller`。企业环境可先把依赖下载到离线目录，再按内部软件管理规则安装。

## 主要字段与计算

- 消耗量 =（期末读数 - 期初读数）× 倍率
- 单耗 = 消耗量 ÷ 产量；产量为 0 时显示 0
- 单耗偏差率 =（单耗 - 目标单耗）÷ 目标单耗 × 100%；目标为 0 时显示 0
- 成本 = 消耗量 × 单价

所有计算使用 `Decimal` 和四舍五入，避免浮点误差。
