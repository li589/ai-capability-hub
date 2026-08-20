# -*- coding: utf-8 -*-
"""
打包清理工具：skill 分发/打包前清空所有客户环境敏感配置。

功能：
  1. 清空 config.json 中的敏感字段（服务器 IP、登录账号密码、SSO 应用密钥、缓存 token）
  2. 保留非敏感结构（接口路径、字段定义、endpoint、枚举说明）
  3. 生成 config.template.json（模板，供新用户参考字段结构）
  4. 打印清理结果清单

用法：
  python clean_for_packaging.py            # 清理当前技能 config.json
  python clean_for_packaging.py --dry-run  # 预览将清空的字段，不实际修改

新用户安装后：运行 `python setup_config.py` 交互式填写本客户环境的 IP/端口/账号/密码。
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# config.json 可能在技能根目录或 scripts/ 下，自动探测
CONFIG = next((p for p in (ROOT / "config.json", ROOT / "scripts" / "config.json") if p.exists()), ROOT / "config.json")
TEMPLATE = CONFIG.parent / "config.template.json"

# 敏感字段路径定义（点分路径 → 字段名），清空时置 ""
# 兼容三类技能配置：server+auth（OpenAPI 类）、database（数据库类）、混合
SENSITIVE = [
    ("server", "host"),
    ("database", "host"),
    ("database", "user"),
    ("database", "password"),
    ("mysql", "host"),
    ("mysql", "user"),
    ("mysql", "password"),
    ("auth", "account", "user_name"),
    ("auth", "account", "password"),
    ("auth", "sso", "user_no"),
    ("auth", "sso", "app_id"),
    ("auth", "sso", "app_secret"),
    ("auth", "sso", "appNo"),
]

# 需要整体移除的字段（缓存/一次性凭证）
REMOVE_KEYS = [
    ("auth", "token"),
    ("auth", "refresh_token"),
    ("auth", "token_at"),
    ("auth", "refresh_at"),
]


def clean(cfg, dry_run=False):
    """就地清空敏感字段，返回 [(路径, 原值打码)]"""
    cleared = []

    def _get_path(obj, parts):
        for p in parts:
            if not isinstance(obj, dict) or p not in obj:
                return None
            obj = obj[p]
        return obj

    def _set_path(obj, parts, val):
        for p in parts[:-1]:
            obj = obj.setdefault(p, {})
        obj[parts[-1]] = val

    def _del_path(obj, parts):
        cur = obj
        for p in parts[:-1]:
            if not isinstance(cur, dict) or p not in cur:
                return False
            cur = cur[p]
        if isinstance(cur, dict) and parts[-1] in cur:
            del cur[parts[-1]]
            return True
        return False

    for parts in SENSITIVE:
        v = _get_path(cfg, parts)
        if v not in (None, ""):
            cleared.append((".".join(parts), str(v)))
            if not dry_run:
                _set_path(cfg, parts, "")
    for parts in REMOVE_KEYS:
        if _get_path(cfg, parts) is not None:
            cleared.append((".".join(parts), "<cached>"))
            if not dry_run:
                _del_path(cfg, parts)
    return cleared


def main():
    parser = argparse.ArgumentParser(description="打包前清理敏感配置")
    parser.add_argument("--dry-run", action="store_true", help="只预览不清空")
    args = parser.parse_args()

    if not CONFIG.exists():
        print(f"未找到 {CONFIG}")
        return 1
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cleared = clean(cfg, dry_run=args.dry_run)

    if not cleared:
        print("✅ 未发现敏感配置，config.json 可直接打包")
    else:
        print(f"{'预览' if args.dry_run else '已清理'} {len(cleared)} 项敏感配置：")
        for path, val in cleared:
            v = val if val == "<cached>" else (val[:2] + "***" if len(val) > 4 else "***")
            print(f"  - {path}  =  {v}")

    if not args.dry_run:
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        # 生成模板（只保留结构，敏感值已为空）
        TEMPLATE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ config.json 已清理；模板已生成: {TEMPLATE.name}")
        print("  新用户安装后运行: python scripts/setup_config.py 填写本环境 IP/端口/账号/密码")
    return 0


if __name__ == "__main__":
    sys.exit(main())
