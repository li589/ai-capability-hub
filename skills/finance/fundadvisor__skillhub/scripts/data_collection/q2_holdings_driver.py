# -*- coding: utf-8 -*-
"""
Q2 2026 持仓刷新驱动：从已蒸馏的经理数据出发采集全部唯一基金的十大重仓股。
用法: python scripts/data_collection/q2_holdings_driver.py
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
sys.path.insert(0, SCRIPT_DIR)

from fund_advisor_paths import load_json_data  # noqa: E402
from full_data_refresh import fetch_all_holdings  # noqa: E402


def validate_holdings(holdings):
    """采集结果质检：占位/合成数据检测。

    若超过 20% 的基金共享完全相同的重仓股清单，判定为占位数据。
    """
    from collections import Counter
    signatures = Counter(
        tuple(s.get('stock_code', '') for s in h.get('stocks', []))
        for h in holdings
    )
    if not signatures:
        return False, '未采集到任何持仓'
    top_sig, top_count = signatures.most_common(1)[0]
    ratio = top_count / len(holdings)
    if ratio > 0.20:
        return False, f'疑似占位数据: {top_count}/{len(holdings)} ({ratio:.0%}) 只基金持仓完全相同'
    return True, f'质检通过: {len(holdings)} 只基金, 最大重复清单占比 {ratio:.1%}'


def main():
    data = load_json_data('fund_managers_distilled.json')
    managers = data.get('items') or data.get('managers') or []
    print(f"经理数: {len(managers)}")
    holdings = fetch_all_holdings(managers, max_funds=None, delay=0.3)
    print(f"完成, 采集到 {len(holdings)} 只基金的持仓")
    ok, msg = validate_holdings(holdings)
    print(f"[质检] {msg}")
    if not ok:
        sys.exit(2)


if __name__ == '__main__':
    main()
