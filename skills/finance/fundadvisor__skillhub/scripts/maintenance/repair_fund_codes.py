# -*- coding: utf-8 -*-
"""
修复经理数据中被剥离前导零的基金代码（如 1924 → 001924）。
策略：优先用 fund_products.json 的「基金名称→代码」权威映射，找不到再 zfill(6)。
修复文件：
  - data/fund_managers_distilled.json  ({managers:[...], meta}) 含 funds[].fund_code
  - data/全市场基金经理名录_天天基金.json ({raw:[[...]], meta})   第4/8列为基金代码
用法: python scripts/maintenance/repair_fund_codes.py
"""
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

from fund_advisor_paths import load_json_data  # noqa: E402


def build_name_code_map():
    """基金名称 → 6位代码（取第一个匹配）"""
    p = load_json_data('fund_products.json')
    items = p.get('items') or []
    m = {}
    for it in items:
        name = it.get('fund_name', '')
        code = str(it.get('fund_code', '')).zfill(6)
        if name and name not in m:
            m[name] = code
    return m


def make_fixer(name_map, stats):
    def fix_code(code, name):
        code = str(code or '').strip()
        if len(code) == 6 and code.isdigit():
            return code
        if name and name in name_map:
            stats['by_name'] += 1
            return name_map[name]
        if code.isdigit() and 0 < len(code) < 6:
            stats['by_zfill'] += 1
            return code.zfill(6)
        if code:
            stats['unfixed'] += 1
        return code
    return fix_code


def atomic_write(path, payload):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def repair_distilled(name_map):
    path = os.path.join(DATA_DIR, 'fund_managers_distilled.json')
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    managers = raw.get('managers') or []
    stats = {'by_name': 0, 'by_zfill': 0, 'unfixed': 0, 'fixed_main': 0, 'fixed_funds': 0}
    fix = make_fixer(name_map, stats)
    for m in managers:
        old = m.get('current_fund_code', '')
        new = fix(old, m.get('current_fund_name', ''))
        if new != old:
            m['current_fund_code'] = new
            stats['fixed_main'] += 1
        for fnd in m.get('funds') or []:
            old_fc = fnd.get('fund_code', '')
            new_fc = fix(old_fc, fnd.get('fund_name', ''))
            if new_fc != old_fc:
                fnd['fund_code'] = new_fc
                stats['fixed_funds'] += 1
    raw['meta']['last_update'] = datetime.now().strftime('%Y-%m-%d')
    raw['meta']['code_repair'] = (
        f"main={stats['fixed_main']}, funds={stats['fixed_funds']}, "
        f"by_name={stats['by_name']}, by_zfill={stats['by_zfill']}, unfixed={stats['unfixed']}")
    atomic_write(path, raw)
    print(f"fund_managers_distilled.json: 主代码修复 {stats['fixed_main']} 人, "
          f"funds 修复 {stats['fixed_funds']} 条 "
          f"(名称映射 {stats['by_name']}, 补零 {stats['by_zfill']}, 未修复 {stats['unfixed']})")


def repair_raw(name_map):
    path = os.path.join(DATA_DIR, '全市场基金经理名录_天天基金.json')
    if not os.path.exists(path):
        print('原始名录不存在，跳过')
        return
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    rows = raw.get('raw') or []
    if not rows:
        print('原始名录无 raw 行，跳过')
        return
    stats = {'by_name': 0, 'by_zfill': 0, 'unfixed': 0}
    fix = make_fixer(name_map, stats)
    fixed = 0
    for row in rows:
        if len(row) < 10:
            continue
        # 第8列 current_fund_code / 第9列 current_fund_name
        new_main = fix(row[8], row[9])
        if new_main != row[8]:
            row[8] = new_main
            fixed += 1
        # 第4/5列 funds 代码/名称 csv
        codes = str(row[4]).split(',') if row[4] else []
        names = str(row[5]).split(',') if row[5] else []
        if codes:
            new_codes = [fix(c, names[i] if i < len(names) else '') for i, c in enumerate(codes)]
            if new_codes != codes:
                row[4] = ','.join(new_codes)
    raw['meta']['last_update'] = datetime.now().strftime('%Y-%m-%d')
    atomic_write(path, raw)
    print(f"全市场基金经理名录: 主代码修复 {fixed} 行")


def main():
    name_map = build_name_code_map()
    print(f'名称映射: {len(name_map)} 条')
    repair_distilled(name_map)
    repair_raw(name_map)


if __name__ == '__main__':
    main()
