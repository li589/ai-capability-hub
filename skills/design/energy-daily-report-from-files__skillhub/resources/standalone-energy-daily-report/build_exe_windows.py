#!/usr/bin/env python3
"""Use already-installed, user-approved tools to build the standalone EXE.

This script never downloads packages, upgrades pip, executes a shell, or asks
for administrator privileges. Prepare and verify the build environment first.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PY_FILE = SCRIPT_DIR / "energy_daily_report.py"
REQ_FILE = SCRIPT_DIR / "requirements_standalone.txt"


def main() -> int:
    if sys.platform != "win32":
        print("[提示] 当前脚本主要用于 Windows；在 macOS/Linux 上可直接运行 energy_daily_report.py。")
    if not PY_FILE.is_file() or not REQ_FILE.is_file():
        print("[错误] 独立程序文件不完整，请重新解压完整技能包。")
        return 2
    missing = [name for name in ("openpyxl", "PyInstaller") if importlib.util.find_spec(name) is None]
    if missing:
        print("[BUILD_TOOL_MISSING] 缺少已批准的打包工具：" + ", ".join(missing))
        print("处理建议：由 IT 管理员准备带 SHA-256 清单的离线 wheels，完成安装后再运行本脚本。")
        return 2
    python = sys.executable
    if not shutil.which(python):
        print("[PYTHON_NOT_FOUND] 未找到当前 Python 解释器。")
        return 2
    command = [
        python, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "energy_daily_report",
        "--collect-all", "openpyxl",
        str(PY_FILE),
    ]
    print("[BUILD_START] 使用本机已安装的 PyInstaller 开始打包；不会联网或提权。")
    result = subprocess.run(command, cwd=SCRIPT_DIR, check=False)
    if result.returncode != 0:
        print("[BUILD_FAILED] EXE 打包失败；请保留输出并交给 IT 管理员处理。")
        return result.returncode or 2
    exe_path = SCRIPT_DIR / "dist" / "energy_daily_report.exe"
    if not exe_path.is_file():
        print("[BUILD_OUTPUT_MISSING] 打包命令结束，但没有找到预期 EXE。")
        return 2
    print(f"[BUILD_OK] EXE 已生成：{exe_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
