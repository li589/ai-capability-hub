#!/usr/bin/env python3
"""dataSupplement 数据层完整性验证脚本。

运行方式：
    bash scripts/run_data_supplement.sh "exec(open('scripts/verify_data_supplement.py').read())"
    或直接：
    PYTHONPATH=dataSupplement .venv/bin/python scripts/verify_data_supplement.py

验证内容：
    1. 所有 domain 模块可导入
    2. realtime_quote 实际取数成功
    3. key_metrics 实际取数成功
    4. get_kline 实际取数成功
"""

import sys
import json
import traceback

TESTS = []
PASSED = 0
FAILED = 0


def test(name):
    """装饰器，注册测试用例"""
    def decorator(func):
        TESTS.append((name, func))
        return func
    return decorator


@test("1. domain imports")
def test_imports():
    from domains.quotes import realtime_quote, batch_quotes
    from domains.kline import get_kline
    from domains.fundamentals import financial_statements, key_metrics, company_profile
    from domains.research import stock_reports, industry_reports, consensus_eps
    from domains.news import stock_news, market_flash
    from domains.announcements import search_announcements
    from domains.screener import multi_factor_screen, index_constituents
    from core.ticker import normalize, detect_market
    return "all 14 functions imported"


@test("2. realtime_quote('600519')")
def test_quote():
    from domains.quotes import realtime_quote
    r = realtime_quote("600519")
    assert isinstance(r, dict), f"expected dict, got {type(r)}"
    assert r.get("price") and r["price"] > 0, f"price invalid: {r.get('price')}"
    return f"price={r['price']}, pe={r.get('pe')}, market_cap={r.get('market_cap')}"


@test("3. key_metrics('600519')")
def test_metrics():
    from domains.fundamentals import key_metrics
    m = key_metrics("600519")
    assert isinstance(m, dict), f"expected dict, got {type(m)}"
    assert "roe" in m, "roe field missing from schema"
    assert m.get("pe") or m.get("pe_ttm"), "neither pe nor pe_ttm available"
    return f"pe_ttm={m.get('pe_ttm')}, pb={m.get('pb')}, market_cap={m.get('market_cap')}"


@test("4. get_kline('600519', freq='day', count=5)")
def test_kline():
    from domains.kline import get_kline
    bars = get_kline("600519", freq="day", count=5)
    assert isinstance(bars, list), f"expected list, got {type(bars)}"
    assert len(bars) >= 3, f"too few bars: {len(bars)}"
    return f"{len(bars)} bars, latest close={bars[-1].get('close')}"


@test("5. batch_quotes(['600519','000858'])")
def test_batch():
    from domains.quotes import batch_quotes
    r = batch_quotes(["600519", "000858"])
    assert isinstance(r, list), f"expected list, got {type(r)}"
    assert len(r) == 2, f"expected 2, got {len(r)}"
    return f"got {len(r)} quotes: {[x.get('name') for x in r]}"


# === Run ===
print("=" * 60)
print("dataSupplement 数据层验证")
print("=" * 60)

for name, func in TESTS:
    try:
        result = func()
        PASSED += 1
        print(f"  ✅ {name} — {result}")
    except Exception as e:
        FAILED += 1
        print(f"  ❌ {name} — {e}")
        traceback.print_exc()

print("-" * 60)
print(f"结果: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
print("=" * 60)

if FAILED:
    sys.exit(1)
else:
    print("\n🎉 dataSupplement 数据层完全可用！")
    sys.exit(0)
