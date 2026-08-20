#!/usr/bin/env python3
"""
wechat-mp-suite 环境检测工具

纯只读检测，不动任何文件。
用法:
    python check.py              # 交互式终端输出
    python check.py --json       # JSON 输出 (CI 友好)
    python check.py --module spider  # 只检查指定模块
"""

import importlib
import json
import os
import shutil
import socket
import sys
import urllib.request
from pathlib import Path

# Windows GBK 终端兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
CONFIG_EXAMPLE = PROJECT_ROOT / ".env.example"

# ── 模块与凭证的映射 ──
MODULE_CREDENTIALS = {
    "search":            {"SOGOU_COOKIE"},
    "publisher":         {"WECHAT_APP_ID", "WECHAT_APP_SECRET"},
    "remote_publisher":  {"WECHAT_APP_ID", "WECHAT_APP_SECRET", "MCP_SERVER_URL"},
}
MODULE_REQUIRED_CONFIG = {
    "search":    ["search.max_results"],
    "spider":    ["spider.parallel_downloads"],
    "publisher": ["publisher.default_theme"],
    "typeset":   ["typeset.default_preset"],
}

ALL_MODULES = ["spider", "search", "downloader", "typeset", "publisher"]


class Checker:
    def __init__(self, target_modules=None, json_mode=False):
        self.json_mode = json_mode
        self.target = target_modules or ALL_MODULES
        self.results = []
        self.env_loaded = {}

    def ok(self, msg, detail=""):
        self.results.append({"status": "ok", "msg": msg, "detail": detail})
        if not self.json_mode:
            print(f"  ✅ {msg}")

    def warn(self, msg, detail=""):
        self.results.append({"status": "warn", "msg": msg, "detail": detail})
        if not self.json_mode:
            print(f"  ⚠️  {msg}")

    def fail(self, msg, detail=""):
        self.results.append({"status": "fail", "msg": msg, "detail": detail})
        if not self.json_mode:
            print(f"  ❌ {msg}")

    def info(self, msg):
        if not self.json_mode:
            print(f"     {msg}")

    def section(self, title):
        if not self.json_mode:
            print(f"\n{'─' * 36}")
            print(f"  {title}")

    # ── 核心检测 ──

    def check_python(self):
        v = sys.version_info
        ver_str = f"{v.major}.{v.minor}.{v.micro}"
        if v >= (3, 12):
            self.ok(f"Python {ver_str}")
        elif v >= (3, 9):
            self.warn(f"Python {ver_str}", "建议 ≥3.12")
        else:
            self.fail(f"Python {ver_str}", "需要 ≥3.9")

    def check_pip_packages(self):
        needed = self._parse_requirements()
        missing = []
        installed = {}
        for pkg, spec in needed.items():
            try:
                mod = importlib.import_module(pkg)
                ver = getattr(mod, "__version__", "?")
                installed[pkg] = ver
            except ImportError:
                missing.append(pkg)

        if missing:
            self.fail(f"pip 依赖缺失: {', '.join(missing)}",
                      "运行: pip install -r requirements.txt")
        else:
            names = [f"{k}=={v}" if v != "?" else k for k, v in installed.items()]
            self.ok(f"pip 依赖完整 ({len(installed)} 项)", ", ".join(names))

    def check_optional_packages(self):
        optional = {"pygments": "代码高亮增强"}
        for pkg, desc in optional.items():
            try:
                importlib.import_module(pkg)
                self.ok(f"{pkg} ({desc})")
            except ImportError:
                self.warn(f"{pkg} 未安装 ({desc})",
                          f"可选: pip install {pkg}")

    def check_config_yaml(self):
        if not CONFIG_PATH.exists():
            self.fail("config.yaml 不存在", f"默认已随项目提供，路径: {CONFIG_PATH}")
            return
        try:
            import yaml
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
        except Exception as e:
            self.fail(f"config.yaml 解析失败: {e}")
            return

        self.ok("config.yaml 格式正确")

        for mod in self.target:
            keys = MODULE_REQUIRED_CONFIG.get(mod)
            if not keys:
                continue
            for kp in keys:
                parts = kp.split(".")
                val = cfg
                for p in parts:
                    val = val.get(p, {})
                if val in (None, {}):
                    self.warn(f"config.yaml 缺少 {kp}")

    def check_dot_env(self):
        if (PROJECT_ROOT / ".env").exists():
            self.ok(".env 文件存在")
        else:
            self.fail(".env 不存在 — 搜索和发布功能需要",
                      "运行 python setup.py 引导创建，或手动 cp .env.example .env")

    def check_credentials(self):
        env = self._load_env_file()
        for mod in self.target:
            needed = MODULE_CREDENTIALS.get(mod)
            if not needed:
                continue
            missing = [k for k in needed if not env.get(k)]
            if missing:
                self.warn(f"[{mod}] 缺少凭证: {', '.join(missing)}",
                          "在 .env 中填写后生效")
            else:
                self.ok(f"[{mod}] 凭证完整")

    def check_network(self):
        checks = [
            ("微信 API (api.weixin.qq.com)", "api.weixin.qq.com", 443, 3),
            ("搜狗搜索 (weixin.sogou.com)", "weixin.sogou.com", 443, 3),
            ("排版服务 (edit.shiker.tech)", "edit.shiker.tech", 443, 3),
        ]
        for label, host, port, timeout in checks:
            try:
                sock = socket.create_connection((host, port), timeout=timeout)
                sock.close()
                self.ok(label)
            except Exception as e:
                self.warn(f"{label} 不通", str(e))

    def check_output_dir(self):
        default_dir = PROJECT_ROOT / "output"
        data_dir = "./output"
        if CONFIG_PATH.exists():
            try:
                import yaml
                with open(CONFIG_PATH, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                data_dir = cfg.get("app", {}).get("data_dir", "./output")
            except Exception:
                pass

        out = (PROJECT_ROOT / data_dir).resolve()
        if out.exists():
            try:
                test = out / ".write_test"
                test.write_text("x")
                test.unlink()
                self.ok(f"输出目录可写 ({out})")
            except PermissionError:
                self.fail(f"输出目录无写入权限 ({out})")
        else:
            try:
                out.mkdir(parents=True, exist_ok=True)
                test = out / ".write_test"
                test.write_text("x")
                test.unlink()
                self.ok(f"输出目录已创建并可写 ({out})")
            except Exception as e:
                self.fail(f"无法创建输出目录 ({out})", str(e))

    def check_module_files(self):
        scripts = {
            "spider":     "scripts/spider/main.py",
            "search":     "scripts/search/index.py",
            "downloader": "scripts/downloader/download.py",
            "typeset":    "scripts/typeset/cli.py",
            "publisher":  "scripts/publisher/publish.py",
        }
        for mod, path in scripts.items():
            if mod not in self.target:
                continue
            full = PROJECT_ROOT / path
            if full.exists():
                self.ok(f"[{mod}] 入口可用: {path}")
            else:
                self.fail(f"[{mod}] 入口缺失: {path}")

    # ── 汇总 ──

    def summary(self):
        ok = sum(1 for r in self.results if r["status"] == "ok")
        warn = sum(1 for r in self.results if r["status"] == "warn")
        fail = sum(1 for r in self.results if r["status"] == "fail")

        ready_modules = self._get_ready_modules()

        if self.json_mode:
            print(json.dumps({
                "summary": {"ok": ok, "warn": warn, "fail": fail},
                "ready_modules": ready_modules,
                "results": self.results,
            }, ensure_ascii=False, indent=2))
            return

        print(f"\n{'═' * 36}")
        print(f"  检测完毕:  {ok} 通过  |  {warn} 警告  |  {fail} 失败")
        print(f"{'─' * 36}")
        print(f"  立即可用模块:  {', '.join(ready_modules) if ready_modules else '无'}")
        if fail > 0:
            print(f"\n  建议: python setup.py  一键修复上述问题")

    # ── 内部 ──

    def _parse_requirements(self):
        mapping = {}
        if not REQUIREMENTS.exists():
            return mapping
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = line.split(">=")[0].split("==")[0].split("<")[0].strip()
            pkg = pkg.replace("-", "_")
            mapping[pkg] = line
        return mapping

    def _load_env_file(self):
        if self.env_loaded:
            return self.env_loaded
        env = PROJECT_ROOT / ".env"
        if not env.exists():
            return {}
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            self.env_loaded[k.strip()] = v.strip().strip('"').strip("'")
        return self.env_loaded

    def _get_ready_modules(self):
        ready = set(self.target)
        env = self._load_env_file()
        for mod, creds in MODULE_CREDENTIALS.items():
            missing = [k for k in creds if not env.get(k)]
            if missing:
                ready.discard(mod)
        # 检查入口文件
        scripts = {
            "spider":     "scripts/spider/main.py",
            "search":     "scripts/search/index.py",
            "downloader": "scripts/downloader/download.py",
            "typeset":    "scripts/typeset/cli.py",
            "publisher":  "scripts/publisher/publish.py",
        }
        for mod in list(ready):
            if not (PROJECT_ROOT / scripts.get(mod, "")).exists():
                ready.discard(mod)
        return sorted(ready)

    def run(self):
        self.section("Python 环境")
        self.check_python()
        self.check_pip_packages()
        self.check_optional_packages()

        self.section("配置文件")
        self.check_config_yaml()
        self.check_dot_env()

        self.section("凭证检查")
        self.check_credentials()

        self.section("网络连通性")
        self.check_network()

        self.section("运行环境")
        self.check_output_dir()
        self.check_module_files()

        self.summary()
        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="wechat-mp-suite 环境检测")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--module", "-m", action="append", choices=ALL_MODULES,
                        help="只检查指定模块")
    args = parser.parse_args()

    if not args.json:
        print("\n🔍 wechat-mp-suite 环境检测")
        print(f"   项目路径: {PROJECT_ROOT}")

    checker = Checker(target_modules=args.module, json_mode=args.json)
    checker.run()

    if args.json:
        return 0
    return 0


if __name__ == "__main__":
    main()
