#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全量数据更新脚本 — 经理+公司+产品+style_code注入"""
import json
import os
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime

# 路径 — full_update.py 在 scripts/maintenance/ 下，需要回溯到项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))       # scripts/maintenance/
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)                     # scripts/
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)                      # 项目根
import sys as _sys; _sys.path.insert(0, SCRIPTS_DIR)
from fund_advisor_paths import DATA_DIR  # noqa: E402

sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SCRIPTS_DIR, 'data_collection'))
sys.path.insert(0, SCRIPT_DIR)

# style_code 映射
STYLE_MAP = {
    '成长型': 'GROWTH', '积极成长': 'AGGRESSIVE_GROWTH',
    '价值型': 'VALUE', '均衡型': 'BALANCED', '稳健型': 'STABLE',
    '平衡型': 'BALANCED', '灵活配置': 'FLEXIBLE_ALLOCATION',
    '被动型': 'INDEX', '指数型': 'INDEX', '债券型': 'BOND',
    '货币型': 'MONEY', '量化型': 'QUANT', 'FOF': 'FOF',
}
DEFAULT_STYLE = 'FLEXIBLE_ALLOCATION'


def inject_style_codes():
    """从经理数据推断公司 style_code 并注入（v9.0: 兼容新列式/旧行式/companies 格式）"""
    print("\n[style_code] 注入公司风格代码...")

    fm_path = os.path.join(DATA_DIR, 'fund_managers_distilled.json')
    fc_path = os.path.join(DATA_DIR, 'fund_companies_distilled.json')

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from fund_advisor_paths import is_columnar, _decode_columnar

    def _load_rows(path, default_key):
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        if is_columnar(data):
            return _decode_columnar(data).get('items', []), data
        if isinstance(data, list):
            return data, data
        rows = data.get(default_key) or data.get('d') or data.get('items') or []
        return rows, data

    managers, _fm = _load_rows(fm_path, 'managers')
    company_styles = defaultdict(list)
    for m in managers:
        if isinstance(m, dict):
            cn = m.get('company_name', '')
            st = m.get('investment_style', '')
            if cn and st:
                company_styles[cn].append(st)

    def infer(styles):
        codes = [STYLE_MAP.get(s, DEFAULT_STYLE) for s in styles]
        if not codes:
            return DEFAULT_STYLE, [DEFAULT_STYLE]
        counter = Counter(codes)
        primary = counter.most_common(1)[0][0]
        alt = list(set(codes))
        if len(alt) < 2:
            alt.append(DEFAULT_STYLE)
        return primary, alt[:3]

    companies, _fc = _load_rows(fc_path, 'companies')
    updated = 0
    for c in companies:
        if isinstance(c, dict):
            name = c.get('name', '')
            styles = company_styles.get(name, [])
            primary, alt = infer(styles)
            c['style_code'] = primary
            c['alt_style_codes'] = alt
            updated += 1

    # 写回：保持原格式（列式→新列式 / companies→companies / 裸 list）
    if isinstance(_fc, dict) and is_columnar(_fc):
        from data_collection.db_format import to_columnar
        cols = list(_fc.get('_f', [])) + ['style_code', 'alt_style_codes']
        out = to_columnar(companies, cols, _fc.get('m', {}))
    elif isinstance(_fc, dict) and 'companies' in _fc:
        out = {'companies': companies, 'm': _fc.get('m', {})}
    else:
        out = companies
    with open(fc_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"  style_code 注入完成: {updated} 家公司")


def main():
    total_start = time.time()
    print("=" * 60)
    print("  fund-advisor 全量数据更新")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # 1. 经理+公司更新
    print("\n" + "=" * 60)
    print("  Phase 1: 基金经理 + 基金公司")
    print("=" * 60)
    try:
        from monthly_updater import MonthlyUpdater
        updater = MonthlyUpdater(SKILL_DIR)
        updater.run(force=True)

        # 检查结果
        fm_path = os.path.join(DATA_DIR, 'fund_managers_distilled.json')
        fc_path = os.path.join(DATA_DIR, 'fund_companies_distilled.json')
        with open(fm_path, 'r', encoding='utf-8-sig') as f:
            fm = json.load(f)
        with open(fc_path, 'r', encoding='utf-8-sig') as f:
            fc = json.load(f)
        mgr_count = fm.get('m', {}).get('total_count', len(fm.get('d', [])))
        co_count = fc.get('m', {}).get('total_count', len(fc.get('d', [])))
        results['managers'] = mgr_count
        results['companies'] = co_count
        print(f"\n  Phase 1 完成: {mgr_count} 位经理, {co_count} 家公司")
    except Exception as e:
        print(f"\n  Phase 1 失败: {e}")
        traceback.print_exc()
        results['managers'] = 'FAILED'
        results['companies'] = 'FAILED'

    # 2. 注入 style_code
    try:
        inject_style_codes()
        results['style_code'] = 'OK'
    except Exception as e:
        print(f"\n  style_code 注入失败: {e}")
        traceback.print_exc()
        results['style_code'] = 'FAILED'

    # 3. 产品更新
    print("\n" + "=" * 60)
    print("  Phase 2: 基金产品")
    print("=" * 60)
    try:
        from fund_product_updater import FundProductUpdater
        product_updater = FundProductUpdater()
        funds = product_updater.collect_all_funds()
        if funds:
            product_updater.update_company_products(funds)
            results['products'] = len(funds)
            print(f"\n  Phase 2 完成: {len(funds)} 只基金产品")
        else:
            results['products'] = 0
            print("\n  Phase 2: 未采集到产品数据")
    except Exception as e:
        print(f"\n  Phase 2 失败: {e}")
        traceback.print_exc()
        results['products'] = 'FAILED'

    # 4. 更新 update_meta.json
    try:
        meta_path = os.path.join(DATA_DIR, 'update_meta.json')
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        meta = {'update_count': 0, 'history': []}

    meta['last_update'] = datetime.now().isoformat()
    meta['update_count'] = meta.get('update_count', 0) + 1
    meta['history'] = meta.get('history', [])[-99:]
    meta['history'].append({
        'type': 'full',
        'time': datetime.now().isoformat(),
        'duration': time.time() - total_start,
        'results': {k: v for k, v in results.items()}
    })
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 5. 汇总
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 60)
    print("  全量更新完成")
    print(f"  总耗时: {total_elapsed:.1f} 秒 ({total_elapsed/60:.1f} 分钟)")
    print(f"  基金经理: {results.get('managers', 'N/A')}")
    print(f"  基金公司: {results.get('companies', 'N/A')}")
    print(f"  基金产品: {results.get('products', 'N/A')}")
    print(f"  style_code: {results.get('style_code', 'N/A')}")
    print("=" * 60)


if __name__ == '__main__':
    main()
