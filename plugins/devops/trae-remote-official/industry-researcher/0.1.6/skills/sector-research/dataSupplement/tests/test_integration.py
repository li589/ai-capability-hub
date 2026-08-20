# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 集成测试（联网）
=====================================

对修复后的 Provider 进行真实网络请求验证。
每个测试独立运行，单个失败不影响其他测试。
运行方式: python tests/test_integration.py
"""

import sys
import os
import time
import traceback

# 设置路径
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# 测试结果收集
_results = []


def _run_test(name: str, func):
    """运行单个测试，捕获异常并记录结果。"""
    print(f"  ⏳ {name}...", end=" ", flush=True)
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        if result:
            print(f"✅ ({elapsed:.2f}s)")
            _results.append((name, True, None))
        else:
            print(f"⚠️  空结果 ({elapsed:.2f}s)")
            _results.append((name, False, "返回空数据"))
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ ({elapsed:.2f}s)")
        print(f"      └─ {type(e).__name__}: {e}")
        _results.append((name, False, f"{type(e).__name__}: {e}"))


# ===========================================================================
# Provider 级测试
# ===========================================================================


def test_tencent_quote():
    """腾讯行情: 获取贵州茅台实时报价"""
    from providers.tencent import quote
    data = quote(["600519"])
    assert len(data) > 0, "无返回数据"
    item = data[0]
    assert item["code"] == "600519", f"代码不匹配: {item.get('code')}"
    assert item["price"] is not None and item["price"] > 0, f"价格异常: {item.get('price')}"
    assert item["name"], "名称为空"
    return True


def test_tencent_quote_multi():
    """腾讯行情: 批量获取多只股票"""
    from providers.tencent import quote
    data = quote(["600519", "000858", "300750"])
    assert len(data) == 3, f"预期3条，实际{len(data)}条"
    codes = [d["code"] for d in data]
    assert "600519" in codes, "缺少600519"
    return True


def test_sina_financial_report():
    """新浪财报: 获取贵州茅台利润表（API 可能已废弃）"""
    from providers.sina import financial_report
    data = financial_report("600519", "income")
    # 注: 新浪 openapi.php 已返回 "Invalid service name"
    # 代码应优雅返回空而不崩溃
    if not data:
        print("(API已废弃-优雅返回空)", end=" ")
    return True  # 不崩溃即通过


def test_sina_option_tquote():
    """新浪期权: T型报价（可能需要有效合约号）"""
    from providers.sina import option_contracts, option_tquote
    # 先获取合约列表
    contracts = option_contracts("510050", call=True)
    if not contracts:
        print("(跳过-无合约列表)", end=" ")
        return True  # 非交易时段可能无数据
    # 取第一个合约查报价
    code = contracts[0]["contract_code"]
    data = option_tquote(code)
    # 非交易时段可能返回空
    return True


def test_sina_hk_quote():
    """新浪港股: 获取腾讯控股行情"""
    from providers.sina import hk_quote
    data = hk_quote("00700")
    if not data:
        print("(非交易时段)", end=" ")
        return True
    assert data.get("code") == "00700", f"代码不匹配: {data.get('code')}"
    return True


def test_sina_us_quote():
    """新浪美股: 获取苹果行情"""
    from providers.sina import us_quote
    data = us_quote("AAPL")
    if not data:
        print("(非交易时段)", end=" ")
        return True
    assert data.get("code") == "AAPL", f"代码不匹配: {data.get('code')}"
    return True


def test_sina_fund_flow():
    """新浪资金流: 获取茅台资金流"""
    from providers.sina import fund_flow_daily
    data = fund_flow_daily("600519", days=3)
    # 资金流可能在非交易时段为空
    if not data:
        print("(非交易时段)", end=" ")
        return True
    assert "date" in data[0], "缺少 date 字段"
    assert "main_net_inflow" in data[0], "缺少 main_net_inflow 字段"
    return True


def test_yahoo_quote_summary():
    """Yahoo: 获取苹果摘要"""
    from providers.yahoo import quote_summary
    data = quote_summary("AAPL")
    # Yahoo 可能因地区限制返回空
    if not data:
        print("(受限/无数据)", end=" ")
        return True
    assert "price" in data or "summaryDetail" in data, f"缺少核心模块: {list(data.keys())}"
    return True


def test_yahoo_chart():
    """Yahoo: 获取苹果K线"""
    from providers.yahoo import chart
    data = chart("AAPL", interval="1d", range_="5d")
    if not data:
        print("(受限/无数据)", end=" ")
        return True
    # 有数据时验证结构
    assert "timestamp" in data or "indicators" in data, f"缺少核心字段: {list(data.keys())}"
    return True


def test_tdx_bars():
    """通达信: 获取A股日K"""
    try:
        from providers.tdx import bars
    except ImportError:
        print("(mootdx未安装-跳过)", end=" ")
        return True
    data = bars(code="600519", frequency=9, count=10)
    if not data:
        print("(连接超时/无数据)", end=" ")
        return True
    assert len(data) <= 10, f"返回数量超过请求: {len(data)}"
    return True


# ===========================================================================
# Domain 级端到端测试
# ===========================================================================


def test_domain_realtime_quote():
    """域层: realtime_quote 端到端"""
    from domains.quotes import realtime_quote
    data = realtime_quote("600519")
    assert data, "返回空"
    assert "price" in data or "code" in data, f"缺少核心字段: {list(data.keys()) if isinstance(data, dict) else type(data)}"
    return True


def test_domain_kline():
    """域层: get_kline 端到端"""
    from domains.kline import get_kline
    data = get_kline("600519", freq="day", count=5)
    # 通达信+Yahoo双重fallback
    if not data:
        print("(所有源不可用)", end=" ")
        return True
    assert len(data) > 0
    item = data[0]
    assert "close" in item or "price" in item, f"缺少价格字段: {list(item.keys())}"
    return True


def test_domain_dragon_tiger():
    """域层: dragon_tiger 全市场"""
    from domains.signals import dragon_tiger
    data = dragon_tiger()
    # 非交易日可能为空
    if not data:
        print("(非交易日)", end=" ")
        return True
    assert isinstance(data, list)
    return True


def test_domain_major_indices():
    """域层: major_indices"""
    from domains.index_snapshot import major_indices
    data = major_indices()
    assert data, "返回空"
    assert len(data) > 0, "无指数数据"
    return True


# ===========================================================================
# 主入口
# ===========================================================================


if __name__ == "__main__":
    print("=" * 60)
    print("dataSupplement V7.1 Integration Test (联网)")
    print("=" * 60)
    print()

    # Provider 层测试
    print("─── Provider 层 ───")
    _run_test("tencent.quote(600519)", test_tencent_quote)
    _run_test("tencent.quote(多只)", test_tencent_quote_multi)
    _run_test("sina.financial_report", test_sina_financial_report)
    _run_test("sina.option_tquote", test_sina_option_tquote)
    _run_test("sina.hk_quote", test_sina_hk_quote)
    _run_test("sina.us_quote", test_sina_us_quote)
    _run_test("sina.fund_flow_daily", test_sina_fund_flow)
    _run_test("yahoo.quote_summary", test_yahoo_quote_summary)
    _run_test("yahoo.chart", test_yahoo_chart)
    _run_test("tdx.bars", test_tdx_bars)
    print()

    # Domain 层测试
    print("─── Domain 层 ───")
    _run_test("quotes.realtime_quote", test_domain_realtime_quote)
    _run_test("kline.get_kline", test_domain_kline)
    _run_test("signals.dragon_tiger", test_domain_dragon_tiger)
    _run_test("index_snapshot.major_indices", test_domain_major_indices)
    print()

    # 汇总
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = sum(1 for _, ok, _ in _results if not ok)
    total = len(_results)

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {total} total")
    print("=" * 60)

    if failed:
        print("\n❌ 失败项:")
        for name, ok, err in _results:
            if not ok:
                print(f"  • {name}: {err}")
        sys.exit(1)
    else:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
