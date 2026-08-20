"""
dataSupplement V7.1 冒烟测试
验证所有模块可正常导入，关键函数签名正确
"""
import sys
import os
import ast
import importlib.util

# 将 skill 根目录加入 path
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_ROOT)


def test_all_files_syntax():
    """验证全部 Python 文件语法正确"""
    errors = []
    total = 0
    for root, dirs, files in os.walk(SKILL_ROOT):
        if '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                total += 1
                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        ast.parse(fh.read())
                except SyntaxError as e:
                    errors.append(f"{path}: line {e.lineno}: {e.msg}")
    
    assert len(errors) == 0, f"Syntax errors found:\n" + "\n".join(errors)
    print(f"  ✅ {total} files pass syntax check")


def test_core_imports():
    """验证 core 模块可导入"""
    from core.client import http_get, http_post, HttpResponse
    from core.cache import cache_get, cache_set, make_key
    from core.throttle import Throttle, throttled_get
    from core.ticker import (normalize, detect_market, cn_prefix,
                             to_eastmoney_secid, to_tencent_code,
                             to_sina_code, to_yahoo_symbol)
    print("  ✅ core modules import OK")


def test_ticker_logic():
    """验证代码归一化逻辑"""
    from core.ticker import normalize, detect_market, cn_prefix, to_eastmoney_secid
    
    # A股
    assert normalize("SH600519") == "600519"
    assert normalize("600519.SH") == "600519"
    assert normalize("600519") == "600519"
    assert detect_market("600519") == "CN"
    assert cn_prefix("600519") == "sh"
    assert cn_prefix("000001") == "sz"
    assert cn_prefix("830799") == "bj"
    assert to_eastmoney_secid("600519") == "1.600519"
    assert to_eastmoney_secid("000001") == "0.000001"
    
    # 港股
    assert detect_market("00700.HK") == "HK"
    assert normalize("00700.HK") == "00700"
    
    # 美股
    assert detect_market("AAPL") == "US"
    assert normalize("AAPL") == "AAPL"
    
    print("  ✅ ticker normalization logic OK")


def test_cache_logic():
    """验证缓存逻辑"""
    from core.cache import cache_get, cache_set, make_key
    
    key = make_key("test", "600519", "day")
    cache_set(key, {"price": 1800}, ttl=60)
    result = cache_get(key)
    assert result == {"price": 1800}
    
    # 未缓存的 key
    assert cache_get("nonexist") is None
    
    print("  ✅ cache logic OK")


def test_throttle_config():
    """验证限流配置"""
    from core.throttle import Throttle, DOMAIN_THROTTLE_REGISTRY
    
    # 东财应有更长间隔
    assert "eastmoney" in DOMAIN_THROTTLE_REGISTRY
    em_throttle = DOMAIN_THROTTLE_REGISTRY["eastmoney"]
    assert em_throttle.min_interval >= 1.0
    
    print("  ✅ throttle config OK")


def test_providers_importable():
    """验证 providers 模块结构（不实际请求网络）"""
    from providers import tencent, sina, tonghuashun, cninfo, cls
    from providers import eastmoney, exchange, yahoo, sec, tdx, akshare_bridge
    
    # 验证关键函数存在
    assert callable(tencent.quote)
    assert callable(sina.financial_report)
    assert callable(sina.option_contracts)
    assert callable(tonghuashun.hot_stocks)
    assert callable(tonghuashun.northbound_flow)
    assert callable(cninfo.announcements)
    assert callable(cls.telegraph)
    assert callable(eastmoney.datacenter_query)
    assert callable(eastmoney.dragon_tiger)
    assert callable(exchange.sse_dragon_tiger)
    assert callable(yahoo.chart)
    assert callable(sec.filings)
    assert callable(tdx.create_client)
    assert callable(akshare_bridge.zt_pool)
    
    print("  ✅ all 11 providers importable, key functions exist")


def test_domains_importable():
    """验证 domains 模块结构"""
    from domains.quotes import realtime_quote, batch_quotes
    from domains.kline import get_kline
    from domains.fundamentals import financial_statements, key_metrics, company_profile
    from domains.capital_flow import fund_flow, margin_data, block_trade, holder_count, dividend_records
    from domains.signals import dragon_tiger, hot_stocks, northbound, lockup_calendar, sector_ranking
    from domains.news import stock_news, market_flash, global_news
    from domains.announcements import search_announcements, sec_filings
    from domains.research import stock_reports, industry_reports, consensus_eps
    from domains.limit_board import zt_pool, zb_pool, dt_pool, yesterday_zt, sentiment_score
    from domains.options import option_chain, option_quote, option_greeks
    from domains.sentiment import hot_list, stock_popularity, investor_qa
    from domains.tech_indicators import compute_indicators, ma, macd, rsi, kdj, boll
    from domains.screener import multi_factor_screen
    from domains.index_snapshot import major_indices
    
    print("  ✅ all 11 domain modules importable, 40+ functions exist")


def test_tech_indicators_pure():
    """验证技术指标纯计算（不依赖网络）"""
    from domains.tech_indicators import ma, ema, macd, rsi, kdj, boll
    
    closes = [10, 11, 12, 11, 13, 14, 13, 15, 16, 14, 15, 16, 17, 18, 17, 16, 18, 19, 20, 19]
    
    # MA
    result = ma(closes, periods=[5])
    assert "MA5" in result
    assert len(result["MA5"]) == len(closes)
    
    # MACD
    result = macd(closes)
    assert "DIF" in result
    assert "DEA" in result
    assert "HIST" in result
    
    # RSI
    result = rsi(closes, periods=[6])
    assert "RSI6" in result
    
    # BOLL
    result = boll(closes, period=5)
    assert "upper" in result
    assert "mid" in result
    assert "lower" in result
    
    print("  ✅ tech indicators pure computation OK")


def run_all():
    """运行全部冒烟测试"""
    print("\n" + "=" * 60)
    print("dataSupplement V7.1 Smoke Test")
    print("=" * 60 + "\n")
    
    tests = [
        test_all_files_syntax,
        test_core_imports,
        test_ticker_logic,
        test_cache_logic,
        test_throttle_config,
        test_providers_importable,
        test_domains_importable,
        test_tech_indicators_pure,
    ]
    
    passed = 0
    failed = 0
    
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ {t.__name__}: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
