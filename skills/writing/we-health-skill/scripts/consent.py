#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — 用户同意状态管理。

直接读写本地 JSON 文件，无外部依赖。

用法:
  python consent.py check      # 查询是否已同意
  python consent.py accept     # 标记为已同意
  python consent.py decline    # 撤销同意
  python consent.py status     # 本地状态详情
  python consent.py version    # 版本信息
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# ── 配置 ──────────────────────────────────────────────

VERSION = "1.0.10"
SKILL_ID = "we-health-skill"
CONSENT_FIELD = "consented"
HOMEPAGE = "https://wy.guahao.com/skill/introduce"

# Windows 下强制 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


def _data_path() -> Path:
    """返回同意状态文件路径。

    可通过环境变量 WY_HEALTH_SKILL_DATA 指定目录，默认 ~/.wy-health-skill。
    """
    directory = os.environ.get("WY_HEALTH_SKILL_DATA") or str(Path.home() / ".wy-health-skill")
    resolved = Path(directory).resolve()
    if not resolved.is_relative_to(Path.home().resolve()):
        raise ValueError("数据目录必须在用户主目录下")
    return resolved / "consent.json"


# ── 读写 ──────────────────────────────────────────────

def _read_all() -> dict[str, Any]:
    """读取完整 JSON（所有技能共享同一文件）。"""
    path = _data_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_all(data: dict[str, Any]) -> None:
    """写入完整 JSON，权限 0600。"""
    path = _data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass  # Windows 不支持 chmod


def _is_consented() -> bool:
    return _read_all().get(SKILL_ID, {}).get(CONSENT_FIELD, False)


def _set_consent(value: bool) -> None:
    data = _read_all()
    data.setdefault(SKILL_ID, {})[CONSENT_FIELD] = value
    _write_all(data)


# ── 输出工具 ──────────────────────────────────────────

def _emit(**fields: Any) -> None:
    print(json.dumps(fields, ensure_ascii=False))


# ── 子命令 ────────────────────────────────────────────

def cmd_check() -> None:
    ok = _is_consented()
    _emit(success=True, consented=ok,
          message="用户已同意服务条款" if ok else "用户尚未同意服务条款")


def cmd_accept() -> None:
    _set_consent(True)
    _emit(success=True, consented=True, message="已同意服务条款，可继续使用")


def cmd_decline() -> None:
    _set_consent(False)
    _emit(success=True, consented=False, message="已撤销同意，相关功能不可用")


def cmd_status() -> None:
    ok = _is_consented()
    _emit(success=True, consented=ok,
          message="用户已同意服务条款" if ok else "用户尚未同意服务条款",
          mode="local")


def cmd_version() -> None:
    _emit(version=VERSION, homepage=HOMEPAGE, message=f"当前版本 {VERSION}")


# ── 入口 ──────────────────────────────────────────────

COMMANDS = {
    "check": cmd_check,
    "accept": cmd_accept,
    "decline": cmd_decline,
    "status": cmd_status,
    "version": cmd_version,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="健康技能条款管理")
    parser.add_argument("command", choices=list(COMMANDS))
    args = parser.parse_args()
    COMMANDS[args.command]()


if __name__ == "__main__":
    main()
