#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局常量定义 (v6.0.0)
=====================
统一管理所有模块的常量、默认值和配置引用。
避免在多个模块中重复定义相同的值。
"""

# ── 版本 ──
VERSION = "9.3.0"
VERSION_DATE = "2026-08-17"

# ── 市场定义 ──
MARKET_CN = "cn"
MARKET_HK = "hk"
MARKET_US = "us"

MARKETS = {
    MARKET_CN: {"name": "A股", "currency": "CNY", "timezone": "Asia/Shanghai"},
    MARKET_HK: {"name": "港股", "currency": "HKD", "timezone": "Asia/Hong_Kong"},
    MARKET_US: {"name": "美股", "currency": "USD", "timezone": "America/New_York"},
}

# ── v7.0 全球市场定义 ──
GLOBAL_MARKETS = {
    "cn": {"name": "A股", "currency": "CNY", "timezone": "Asia/Shanghai",
           "trading_hours": "9:30-15:00", "index_code": "sh000001"},
    "hk": {"name": "港股", "currency": "HKD", "timezone": "Asia/Hong_Kong",
           "trading_hours": "9:30-16:00", "index_code": "100.HSI"},
    "us": {"name": "美股", "currency": "USD", "timezone": "America/New_York",
           "trading_hours": "9:30-16:00", "index_code": "100.SPX"},
    "jp": {"name": "日股", "currency": "JPY", "timezone": "Asia/Tokyo",
           "trading_hours": "9:00-15:00", "index_code": "100.N225"},
    "kr": {"name": "韩股", "currency": "KRW", "timezone": "Asia/Seoul",
           "trading_hours": "9:00-15:30", "index_code": "100.KS11"},
    "uk": {"name": "英股", "currency": "GBP", "timezone": "Europe/London",
           "trading_hours": "8:00-16:30", "index_code": "100.FTSE"},
    "de": {"name": "德股", "currency": "EUR", "timezone": "Europe/Berlin",
           "trading_hours": "9:00-17:30", "index_code": "100.GDAXI"},
    "fr": {"name": "法股", "currency": "EUR", "timezone": "Europe/Paris",
           "trading_hours": "9:00-17:30", "index_code": "100.FCHI"},
    "au": {"name": "澳股", "currency": "AUD", "timezone": "Australia/Sydney",
           "trading_hours": "10:00-16:00", "index_code": "100.AS51"},
    "in": {"name": "印度股", "currency": "INR", "timezone": "Asia/Kolkata",
           "trading_hours": "9:15-15:30", "index_code": "100.SENSEX"},
    "tw": {"name": "台股", "currency": "TWD", "timezone": "Asia/Taipei",
           "trading_hours": "9:00-13:30", "index_code": "100.TWII"},
    "ca": {"name": "加股", "currency": "CAD", "timezone": "America/Toronto",
           "trading_hours": "9:30-16:00", "index_code": "100.TSX"},
    "gold": {"name": "黄金", "currency": "USD", "timezone": "America/New_York",
             "trading_hours": "近乎24小时", "index_code": "101.GC00Y"},
    "silver": {"name": "白银", "currency": "USD", "timezone": "America/New_York",
               "trading_hours": "近乎24小时", "index_code": "101.SI00Y"},
    "crude": {"name": "原油", "currency": "USD", "timezone": "America/New_York",
              "trading_hours": "近乎24小时", "index_code": "102.CL00Y"},
}

# ── v7.0 全球指数代码映射 ──
GLOBAL_INDEX_CODES = {
    # A股三大指数
    "sh000001": {"name": "上证指数", "market": "cn", "currency": "CNY"},
    "sz399001": {"name": "深证成指", "market": "cn", "currency": "CNY"},
    "sz399006": {"name": "创业板指", "market": "cn", "currency": "CNY"},
    "sh000688": {"name": "科创50", "market": "cn", "currency": "CNY"},
    # 港股指数
    "100.HSI": {"name": "恒生指数", "market": "hk", "currency": "HKD"},
    "100.HSCEI": {"name": "国企指数", "market": "hk", "currency": "HKD"},
    # 美股三大指数
    "100.SPX": {"name": "标普500", "market": "us", "currency": "USD"},
    "100.NDX": {"name": "纳斯达克", "market": "us", "currency": "USD"},
    "100.DJIA": {"name": "道琼斯", "market": "us", "currency": "USD"},
    # 亚太市场
    "100.N225": {"name": "日经225", "market": "jp", "currency": "JPY"},
    "100.KS11": {"name": "韩国KOSPI", "market": "kr", "currency": "KRW"},
    "100.AS51": {"name": "澳洲ASX200", "market": "au", "currency": "AUD"},
    "100.SENSEX": {"name": "印度SENSEX", "market": "in", "currency": "INR"},
    "100.TWII": {"name": "台湾加权", "market": "tw", "currency": "TWD"},
    # 欧洲市场
    "100.FTSE": {"name": "英国富时100", "market": "uk", "currency": "GBP"},
    "100.GDAXI": {"name": "德国DAX", "market": "de", "currency": "EUR"},
    "100.FCHI": {"name": "法国CAC40", "market": "fr", "currency": "EUR"},
    # 北美其他
    "100.TSX": {"name": "加拿大TSX", "market": "ca", "currency": "CAD"},
    # 新兴市场
    "100.VN30": {"name": "越南VN30", "market": "idx", "currency": "VND"},
}

# ── v7.0 商品期货代码映射 ──
COMMODITY_CODES = {
    "gold:comex": {"name": "COMEX黄金", "market": "gold", "currency": "USD",
                   "secid": "101.GC00Y", "unit": "美元/盎司"},
    "gold:sh": {"name": "沪金主连", "market": "gold", "currency": "CNY",
                "secid": "113.aum", "unit": "元/克"},
    "silver:comex": {"name": "COMEX白银", "market": "silver", "currency": "USD",
                     "secid": "101.SI00Y", "unit": "美元/盎司"},
    "silver:sh": {"name": "沪银主连", "market": "silver", "currency": "CNY",
                  "secid": "113.agm", "unit": "元/千克"},
    "crude:wti": {"name": "WTI原油", "market": "crude", "currency": "USD",
                  "secid": "102.CL00Y", "unit": "美元/桶"},
}

# ── 腾讯行情 API 前缀 ──
TENCENT_PREFIX = {
    "cn_sh": "sh",
    "cn_sz": "sz",
    "hk": "r_hk",
    "us": "t_us",
}

# ── 网络请求默认值 ──
DEFAULT_TIMEOUT = 10          # 秒
DEFAULT_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 2     # 指数退避基数
CACHE_TTL_QUOTE = 5           # 实时行情缓存（秒）
CACHE_TTL_KLINE = 300         # K线数据缓存（秒）
CACHE_TTL_FINANCIAL = 86400   # 财务数据缓存（秒）

# ── K 线周期 ──
KLINEPERIOD_DAY = 250         # 默认日线数量
KLINEPERIOD_SHORT = 60        # 短期
KLINEPERIOD_MEDIUM = 120      # 中期
KLINEPERIOD_LONG = 250        # 长期

# ── 技术指标默认参数 ──
TECH_MA_PERIODS = [5, 10, 20, 60, 120, 250]
TECH_EMA_PERIODS = [12, 26]
TECH_RSI_PERIODS = [6, 14, 24]
TECH_MACD_PARAMS = (12, 26, 9)
TECH_KDJ_PERIOD = 9
TECH_BOLL_PERIOD = 20
TECH_BOLL_STD = 2.0
TECH_ADX_PERIOD = 14
TECH_ATR_PERIOD = 14
TECH_WR_PERIOD = 14
TECH_CCI_PERIOD = 20
TECH_MFI_PERIOD = 14

# ── 预测评分默认权重 ──
# v7.0 七维评分（新增黄金/商品维度）
PREDICT_WEIGHTS_V7 = {
    "trend": 0.22,          # 趋势面：均线排列 + ADX 趋势强度
    "momentum": 0.18,       # 动量面：RSI + MACD + KDJ + WR + CCI
    "volume": 0.12,         # 量价面：量比 + OBV + MFI
    "volatility": 0.08,     # 波动面：布林带位置 + ATR 风险
    "probability": 0.18,    # 概率面：蒙特卡洛模拟
    "market_context": 0.12, # 环境面：VIX/全球风险偏好/跨市场相关（v7.0 动态化）
    "gold_factor": 0.10,    # v7.0 新增：黄金专用（实际利率/美元强度/避险需求）
}

# v6.0 六维评分（保持向后兼容）
PREDICT_WEIGHTS_V6 = {
    "trend": 0.25,         # 趋势面：均线排列 + ADX 趋势强度
    "momentum": 0.20,      # 动量面：RSI + MACD + KDJ + WR + CCI
    "volume": 0.15,        # 量价面：量比 + OBV + MFI
    "volatility": 0.10,    # 波动面：布林带位置 + ATR 风险
    "probability": 0.20,   # 概率面：蒙特卡洛模拟
    "market_context": 0.10, # 环境面：牛/熊/震荡 + 宏观信号
}

# ── v7.0 短期预测权重（1d/3d/5d）──
SHORT_TERM_WEIGHTS_V7 = {
    "technical": 0.30,     # 技术面主导
    "sentiment": 0.25,     # 情绪面（新闻+论坛）
    "money_flow": 0.20,    # 资金面
    "quant_vol": 0.15,     # 量化波动率
    "news": 0.10,          # 新闻影响
}

# ── 价值投资权重 ──
VALUE_INVESTING_WEIGHTS = {
    "dcf": 0.25,
    "moat": 0.20,
    "financial_health": 0.15,
    "management": 0.15,
    "industry": 0.15,
    "factor": 0.10,
}

# ── 基金评分 v4 权重 ──
FUND_SCORE_V4_WEIGHTS = {
    "performance": 0.10,
    "style_stability": 0.12,
    "alpha": 0.16,
    "sharpe": 0.10,
    "sortino": 0.08,
    "drawdown_calmar": 0.10,
    "tracking_error": 0.08,
    "fee_efficiency": 0.06,
    "prediction": 0.10,
    "sentiment": 0.10,      # v4 新增：舆情维度
}

# ── 蒙特卡洛默认参数 ──
MC_DEFAULT_PATHS = 500      # 股票预测
MC_FUND_PATHS = 1000        # 基金预测

# ── 信号阈值 ──
SIGNAL_STRONG_BULLISH = 60
SIGNAL_BULLISH = 30
SIGNAL_NEUTRAL = -30
SIGNAL_BEARISH = -60
# >60 强势看涨, 30~60 看涨, -30~30 中性, -60~-30 看跌, <-60 强势看跌

# ── 预警默认值 ──
ALERT_STOP_LOSS_PCT = -10
ALERT_TAKE_PROFIT_PCT = 30
ALERT_RSI_OVERBOUGHT = 80
ALERT_RSI_OVERSOLD = 20
ALERT_SENTIMENT_SURGE = 30   # 24h 情绪变化阈值（%）
ALERT_SENTIMENT_EXTREME = 85 # 极端情绪比例（%）
