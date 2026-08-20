"""
fund_advisor_bootstrap.py — 自检

零依赖：core skill 只需 Python 3.8+ 标准库。
本模块只做两件事:
  1. 检查 Python 版本
  2. 检查本地 data/ 下的关键 JSON 是否就位

纯本地运行，无需联网，无需 API Key。
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Tuple
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

DATA_FILES = [
    # (文件名, 最小KB, 说明, 是否阻塞) — 可选增强层（观点/新闻/外部数据）仅提示不阻塞
    ("fund_managers_distilled.json", 200, "基金经理档案", True),
    ("fund_companies_distilled.json", 30, "公司档案", True),
    ("holdings_database.json", 50, "持仓明细（v10: 212+ 只基金的紧凑库约 80KB）", True),
    ("manager_views.json", 1, "经理观点（可选增强，view_collector 采集）", False),
    ("manager_news.json", 1, "经理新闻/采访（可选增强，v10.0）", False),
    ("style_profiles.json", 1, "风格画像", True),
    ("external_data.json", 1, "外部数据（多源，按需抓取）", False),
    ("fund_products.json", 100, "基金产品目录", True),
]

# v10.0: 新增模块导入自检（全部零依赖，失败仅提示不阻塞）
NEW_MODULES = [
    ("analysis.manager_persona", "经理人设卡"),
    ("analysis.manager_dialogue", "经理对话"),
    ("analysis.manager_follower", "跟仓引擎"),
    ("data_collection.holdings_history", "持仓历史"),
    ("data_collection.manager_news_collector", "经理新闻采集"),
    ("data_collection.fund_profile_collector", "产品档案采集"),
    ("client_manager.behavioral_profile", "行为偏差画像"),
    ("client_manager.report_scheduler", "报告订阅调度"),
    ("maintenance.manager_change_monitor", "经理变动监控"),
]

def _check_python() -> Tuple[bool, str]:
    """Python 版本 >= 3.8"""
    v = sys.version_info
    ok = v >= (3, 8)
    return ok, f"Python {v.major}.{v.minor}.{v.micro} (要求 >= 3.8)"


def _check_data() -> list[tuple]:
    """检查 data/ 下关键文件（含阻塞标记；可选增强层仅提示）"""
    results = []
    for item in DATA_FILES:
        fname, min_kb, note = item[0], item[1], item[2]
        blocking = item[3] if len(item) > 3 else True
        p = DATA_DIR / fname
        p_gz = DATA_DIR / (fname + ".gz")
        if p_gz.exists():
            size = p_gz.stat().st_size / 1024
            results.append((fname + ".gz", True, f"OK ({size:.1f} KB) — {note}", blocking))
        elif p.exists():
            size = p.stat().st_size / 1024
            ok = size >= min_kb
            tag = "OK" if ok else "TOO SMALL"
            results.append((fname, ok, f"{tag} ({size:.1f} KB) — {note}", blocking))
        else:
            results.append((fname, False, f"MISSING — {note}", blocking))
    return results


def run_check(verbose: bool = True) -> bool:
    """跑全量自检，返回是否全通过"""
    all_ok = True
    if verbose:
        print("=" * 60)
        print("  fund-advisor 自检（零依赖，纯本地）")
        print("=" * 60)

    ok, msg = _check_python()
    if verbose:
        print(f"  [{'OK' if ok else 'FAIL'}] Python: {msg}")
    all_ok = all_ok and ok

    if verbose:
        print(f"\n  数据文件:")
    for fname, ok, note, blocking in _check_data():
        if verbose:
            print(f"    [{'OK' if ok else 'FAIL'}] {fname}: {note}")
        if blocking:
            all_ok = all_ok and ok

    # v10.0: 新增模块导入自检（缺失只警告，不影响整体判定）
    if verbose:
        print(f"\n  新功能模块:")
    for mod_name, note in NEW_MODULES:
        try:
            __import__(mod_name)
            m_ok = True
        except Exception:
            m_ok = False
        if verbose:
            print(f"    [{'OK' if m_ok else 'SKIP'}] {note}（{mod_name}）")

    if verbose:
        print()
        print("=" * 60)
        if all_ok:
            print("  全部通过！无需配置，直接使用。")
        else:
            print("  有 FAIL 项目：数据缺失或 Python 版本太低。")
        print("=" * 60)

    return all_ok


if __name__ == '__main__':
    run_check(verbose=True)
