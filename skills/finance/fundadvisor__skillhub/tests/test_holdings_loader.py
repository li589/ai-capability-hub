"""test_holdings_loader.py — 持仓数据统一解码与数据完整性

覆盖:
- normalize_holdings 对各历史格式的解码（v7.2 h/m 数组、f/m 并行数组、
  holdings 股票级、by_manager 基金级、裸列表）
- 真实 data/holdings_database.json 的可读性与占位数据检测
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fund_advisor_paths import load_holdings, normalize_holdings  # noqa: E402


# ── 格式解码 ────────────────────────────────────────────────────────


def test_normalize_h_m_array_format():
    """v7.2+ 紧凑格式: {"h":[{fc,fn,mg,co,ss:[[code,name,w],...]}]}"""
    data = {'h': [{'fc': '001924', 'fn': '测试基金', 'mg': '张三', 'co': '测试公司',
                   'ss': [['600519', '贵州茅台', 9.77], ['000333', '美的集团', 9.31]]}],
            'm': {'count': 1, 'quarter': '2026Q2'}}
    rows = normalize_holdings(data)
    assert len(rows) == 2
    assert rows[0]['fund_code'] == '001924'
    assert rows[0]['stock_code'] == '600519'
    assert rows[0]['stock_name'] == '贵州茅台'
    assert rows[0]['weight'] == 9.77
    assert rows[1]['manager_name'] == '张三'


def test_normalize_h_m_dict_ss_format():
    """兼容 v5.5 dict 形式 ss: [{c,n,w}]"""
    data = {'h': [{'fc': '110022', 'fn': 'x', 'ss': [{'c': '600519', 'n': '贵州茅台', 'w': 8.5}]}]}
    rows = normalize_holdings(data)
    assert len(rows) == 1
    assert rows[0]['stock_code'] == '600519'
    assert rows[0]['weight'] == 8.5


def test_normalize_f_m_format():
    """f/m 并行数组格式，基金代码需补零到 6 位"""
    data = {'f': [['1924', '华夏国企改革混合', '艾邦妮', '华夏基金',
                   ['300308', '688347'], [6.45, 5.57]]],
            'm': {'count': 1}}
    rows = normalize_holdings(data)
    assert len(rows) == 2
    assert rows[0]['fund_code'] == '001924'
    assert rows[1]['weight'] == 5.57


def test_normalize_stock_level_format():
    """旧版全量刷新格式: {"holdings": [股票级dict]}"""
    data = {'holdings': [{'fund_code': '000001', 'stock_code': '600519',
                          'stock_name': '贵州茅台', 'weight': 5.0}]}
    rows = normalize_holdings(data)
    assert len(rows) == 1
    assert rows[0]['fund_code'] == '000001'


def test_normalize_by_manager_format():
    """旧版全量刷新格式: {"by_manager": [基金级dict]}"""
    data = {'by_manager': [{'fund_code': '000001', 'fund_name': 'x',
                            'stocks': [{'stock_code': '600519', 'stock_name': '贵州茅台', 'weight': 5.0}]}]}
    rows = normalize_holdings(data)
    assert len(rows) == 1
    assert rows[0]['stock_code'] == '600519'


def test_normalize_empty_and_garbage():
    assert normalize_holdings(None) == []
    assert normalize_holdings({}) == []
    assert normalize_holdings({'x': 1}) == []
    assert normalize_holdings([]) == []


# ── 真实数据文件完整性 ──────────────────────────────────────────────


def test_real_holdings_file_decodable():
    """持仓文件必须能被 load_holdings 解码（占位骨架返回空不崩溃）。

    轻量化后 data/holdings_database.json 为占位骨架 {"h":[],"m":{}}，
    解码应返回空列表；重建真实数据后返回的行基金代码必须为 6 位。
    """
    path = ROOT / 'data' / 'holdings_database.json'
    if not path.exists():
        pytest.skip('holdings_database.json 不存在')
    rows = load_holdings()
    assert isinstance(rows, list), 'load_holdings 应返回列表'
    codes = {r['fund_code'] for r in rows}
    assert all(len(str(c)) == 6 for c in codes), '基金代码未统一为 6 位'


def test_real_holdings_not_placeholder():
    """占位数据检测：超过 20% 基金共享同一重仓清单即判定为合成数据。

    仅对带 quarter 元数据的新格式文件强制（旧文件无 quarter 键时跳过）。
    """
    path = ROOT / 'data' / 'holdings_database.json'
    if not path.exists():
        pytest.skip('holdings_database.json 不存在')
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    meta = raw.get('m', {}) if isinstance(raw, dict) else {}
    if not meta.get('quarter'):
        pytest.skip('旧格式文件（无 quarter 元数据），待重新采集后启用本校验')

    from collections import Counter
    fund_stocks = {}
    for r in load_holdings():
        fund_stocks.setdefault(r['fund_code'], []).append(r.get('stock_code', ''))
    sigs = Counter(tuple(v) for v in fund_stocks.values())
    top_count = sigs.most_common(1)[0][1]
    ratio = top_count / len(fund_stocks)
    assert ratio <= 0.20, (
        f'疑似占位数据: {top_count}/{len(fund_stocks)} ({ratio:.0%}) 只基金持仓完全相同')
