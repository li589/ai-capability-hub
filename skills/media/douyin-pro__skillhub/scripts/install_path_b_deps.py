#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path B 依赖安装与环境校验 · 抖音短视频生产专家团
============================================================
一键把"免费端到端"路径需要的依赖装好并检查:

    Python >= 3.10   → edge-tts        (pip install edge-tts)
    Node.js >= 22    → hyperframes      (npm install -g hyperframes)
    ffmpeg + ffprobe                  (系统安装, 见下方按系统指引)
    Chrome            → npx hyperframes browser ensure

用法:
    python install_path_b_deps.py            # 检测 + 装 pip/npm 部分 + 指引系统部分
    python install_path_b_deps.py --auto     # 额外尝试自动装(npm 全局 / winget ffmpeg)
    python install_path_b_deps.py --check    # 只检查, 不安装

安全说明: pip / npm 部分会真的安装; ffmpeg / Chrome 这类系统级或较大下载,
默认只给安装指引, 加 --auto 才会尝试(winget 装 ffmpeg、npx 装 Chrome)。
"""

import argparse
import shutil
import subprocess
import sys


def log(msg):
    print(msg, flush=True)


def which(t):
    return shutil.which(t) or shutil.which(t + ".exe")


def run(cmd, check=True):
    """跨平台运行外部命令。

    ⚠️ 关键：Windows 下 npx/npm/hyperframes 是 .cmd 包装脚本，
    CreateProcess 不能直接启动，必须 shell=True + list2cmdline 走 cmd.exe。
    （Git Bash 里能直接跑 npx 是 bash 自己解析了，但用户用 python 在
    cmd/PowerShell 跑脚本时若不处理就会崩溃。）
    """
    if isinstance(cmd, str):
        cmd_list = cmd.split()
        display = cmd
    else:
        cmd_list = [str(c) for c in cmd]
        display = " ".join(cmd_list)
    log("  ▶ " + display)
    if sys.platform == "win32":
        s = subprocess.list2cmdline(cmd_list)
        r = subprocess.run(s, shell=True)
    else:
        r = subprocess.run(cmd_list)
    return r.returncode == 0


def py_exec(args, auto=False):
    """用当前 python 跑 pip 安装。"""
    return subprocess.run([sys.executable, "-m", "pip"] + args).returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Path B 依赖安装")
    ap.add_argument("--auto", action="store_true", help="尝试自动安装(npm全局/winget ffmpeg/Chrome)")
    ap.add_argument("--check", action="store_true", help="只检查不安装")
    args = ap.parse_args()

    log("=== Path B 依赖安装 / 校验 ===\n")

    # 1) Python
    log(f"[1/5] Python: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        log("  ❌ Python 过低, 需要 >= 3.10")
        return 1
    log("  ✅ 版本满足")

    # 2) edge-tts (pip)
    log("\n[2/5] edge-tts (配音, 免费)")
    try:
        import edge_tts  # noqa
        log("  ✅ 已安装")
    except ImportError:
        if args.check:
            log("  ⚠️ 未安装 (--check 模式不安装)")
        else:
            log("  → pip install edge-tts")
            if py_exec(["install", "--upgrade", "edge-tts"]):
                log("  ✅ 安装成功")
            else:
                log("  ❌ 安装失败, 请手动: python -m pip install edge-tts")
                return 1

    # 3) Node + hyperframes
    log("\n[3/5] Node.js >= 22 + hyperframes (渲染)")
    node = which("node")
    if node:
        ver = subprocess.check_output([node, "--version"]).decode().strip()
        maj = int(ver.lstrip("v").split(".")[0])
        log(f"  ✅ Node.js {ver}")
        if maj < 22:
            log("  ❌ 需要 >= 22, 请从 https://nodejs.org 升级")
            return 1
    else:
        log("  ❌ 未找到 node → 安装: https://nodejs.org (>=22)")
        if args.auto:
            log("  (--auto 不会自动装 Node, 请手动装后再跑本脚本)")
        return 1

    hf = which("hyperframes")
    if hf:
        log("  ✅ hyperframes 已全局安装")
    else:
        npm = which("npm")
        if not npm:
            log("  ❌ 未找到 npm (随 Node 一起装)")
            return 1
        if args.check:
            log("  ⚠️ 未安装 (--check 模式不安装)")
        else:
            log("  → npm install -g hyperframes")
            if run([npm, "install", "-g", "hyperframes"]):
                log("  ✅ 安装成功")
            else:
                log("  ❌ 全局安装失败, 可改用: npx hyperframes <命令> (无需全局装)")
                # 不算致命, npx 兜底

    # 4) ffmpeg
    log("\n[4/5] ffmpeg + ffprobe (合成与字幕)")
    if which("ffmpeg") and which("ffprobe"):
        log("  ✅ 已安装")
    else:
        log("  ❌ 未安装 ffmpeg。按你的系统装:")
        if sys.platform == "win32":
            log("     Windows:  winget install ffmpeg  或  choco install ffmpeg")
            log("              或下载 https://ffmpeg.org 解压并把 bin 加入 PATH")
            if args.auto:
                run("winget install -e --id Gyan.FFmpeg", check=True)
        elif sys.platform == "darwin":
            log("     macOS:    brew install ffmpeg")
            if args.auto:
                run(["brew", "install", "ffmpeg"])
        else:
            log("     Linux:    sudo apt-get install ffmpeg")
        if not args.auto:
            log("  (加 --auto 可让脚本尝试 winget/brew 安装)")

    # 5) Chrome for HyperFrames
    log("\n[5/5] Chrome (HyperFrames 渲染需要浏览器内核)")
    if which("npx"):
        log("  → npx hyperframes doctor  可看 Chrome 状态")
        if args.auto and not args.check:
            log("  → npx hyperframes browser ensure (下载 Chrome)")
            run(["npx", "-y", "hyperframes", "browser", "install"])
        else:
            log("  (渲染前首次会自动下载; 或手动: npx hyperframes browser ensure)")

    log("\n=== 校验环境 (hyperframes doctor) ===")
    if which("npx"):
        run(["npx", "-y", "hyperframes", "doctor"])

    log("\n下一步: 准备脚本文件, 运行")
    log("  python path_b_build.py --input 你的脚本.txt --output final.mp4")
    log("详见 references/path_b_runbook.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
