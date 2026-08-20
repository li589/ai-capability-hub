# -*- coding: utf-8 -*-
"""
A股基金量化分析器 v1.0
基于A股市场特点和基金净值数据，提供持仓分析和技术信号
适配中国公募基金市场（T+1交易、季度持仓披露、LOF/ETF/主动管理型）
"""
from __future__ import annotations
import json, math, random
from datetime import datetime, timedelta
from pathlib import Path

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR, load_json_data, normalize_holdings  # noqa: E402
import logging

logger = logging.getLogger(__name__)


# ── 信号常量 ──────────────────────────────────────────────────────────
SIGNAL_BULL = 1    # 看多信号
SIGNAL_BEAR = -1   # 看空信号
SIGNAL_NEUTRAL = 0 # 中性信号

# 调仓阈值
ADJUST_THRESHOLD_BUY = 0.6   # 综合信号 > 0.6 → 建议加仓
ADJUST_THRESHOLD_SELL = -0.6 # 综合信号 < -0.6 → 建议减仓
ADJUST_NEUTRAL_BAND = (-0.25, 0.25) # 中性区间


# ── 基金净值工具 ──────────────────────────────────────────────────────
class FundNavTools:
    """基金净值分析工具"""

    @staticmethod
    def calc_ema(data, period):
        if len(data) < period:
            return None
        k = 2.0 / (period + 1)
        ema = sum(data[:period]) / period
        for v in data[period:]:
            ema = v * k + ema * (1 - k)
        return ema

    @staticmethod
    def calc_rsi(prices, period=14):
        if len(prices) < period + 1:
            return None
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        # Wilder's exponential smoothing (industry standard RSI)
        # First average is SMA of the first `period` values
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        # Subsequent values use: avg = (prev_avg * (period-1) + current) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)

    @staticmethod
    def calc_std(prices, period=20):
        if len(prices) < period:
            return 0
        recent = prices[-period:]
        mean = sum(recent) / period
        variance = sum((p - mean) ** 2 for p in recent) / period
        return math.sqrt(variance)

    @staticmethod
    def calc_sharpe(prices, period=60, risk_free=0.03):
        """夏普比率（简化版，年化）"""
        if len(prices) < 20:
            return 0
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        if not returns:
            return 0
        avg_ret = sum(returns) / len(returns) * 252  # 年化
        std_ret = (sum((r - avg_ret/252)**2 for r in returns) / len(returns)) ** 0.5 * math.sqrt(252)
        if std_ret == 0:
            return 0
        return (avg_ret - risk_free) / std_ret


# ── 信号1：均线偏离信号 ──────────────────────────────────────────────
class MaDeviationSignal:
    """均线偏离信号 — 基金净值与均线的偏离程度"""
    name = "ma_deviation"
    description = "净值偏离均线程度"

    def __init__(self, data_source=None):
        self.data_source = data_source  # FundDataSource实例

    def compute(self, fund_code, days=60):
        """
        计算均线偏离信号
        返回: (signal_value, components)
        signal_value: [-1, +1], >0价格高于均线（偏多），<0价格低于均线（偏空）
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 30:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        # 计算均线
        ma5 = FundNavTools.calc_ema(prices[-20:] if len(prices) >= 20 else prices, 5) or prices[-1]
        ma10 = FundNavTools.calc_ema(prices[-20:] if len(prices) >= 20 else prices, 10) or prices[-1]
        ma20 = FundNavTools.calc_ema(prices, 20) or prices[-1]
        ma60 = FundNavTools.calc_ema(prices, 60) or prices[-1]

        current = prices[-1]

        # 多均线多头排列 → 偏多
        short_term_bull = ma5 > ma10 and ma10 > ma20
        short_term_bear = ma5 < ma10 and ma10 < ma20

        # 偏离度
        deviation_pct = (current - ma20) / ma20 if ma20 > 0 else 0

        raw = 0.0
        if short_term_bull and deviation_pct > 0.05:
            raw = min(deviation_pct * 5, 1.0)  # 强势偏多
        elif short_term_bear and deviation_pct < -0.05:
            raw = max(deviation_pct * 5, -1.0)  # 强势偏空
        elif deviation_pct > 0.10:
            raw = 0.5  # 偏离过大，可能回调
        elif deviation_pct < -0.10:
            raw = -0.5  # 偏离过大，可能反弹

        value = max(-1.0, min(1.0, raw))
        return value, {
            "ma5": round(ma5, 4), "ma10": round(ma10, 4),
            "ma20": round(ma20, 4), "ma60": round(ma60, 4),
            "current": round(current, 4),
            "deviation_pct": round(deviation_pct * 100, 2)
        }

    def _get_nav_prices(self, fund_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号2：RSI超买超卖信号 ────────────────────────────────────────────
class FundRsiSignal:
    """基金RSI信号 — 基于净值序列的RSI指标"""
    name = "rsi"
    description = "RSI超买超卖"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=30):
        """
        RSI信号
        > 70: 超买 → 看空
        < 30: 超卖 → 看多
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 15:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        rsi = FundNavTools.calc_rsi(prices, period=14)
        if rsi is None:
            return SIGNAL_NEUTRAL, {"error": "计算失败"}

        raw = 0.0
        if rsi > 70:
            raw = (80 - rsi) / 10  # -1 ~ 0 (超买偏空)
        elif rsi < 30:
            raw = (30 - rsi) / 10  # 0 ~ +1 (超卖偏多)
        else:
            raw = (rsi - 50) / 20  # 标准化

        value = max(-1.0, min(1.0, raw))
        return value, {"rsi": round(rsi, 2)}

    def _get_nav_prices(self, fund_code, days=30):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号3：布林带信号 ──────────────────────────────────────────────────
class FundBollingerSignal:
    """基金布林带信号 — 净值在布林带中的位置"""
    name = "bollinger"
    description = "布林带位置"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=30):
        """
        布林带信号
        价格突破上轨 → 超买 → 偏空
        价格突破下轨 → 超卖 → 偏多
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 20:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        recent = prices[-20:]
        mid = sum(recent) / 20
        std = FundNavTools.calc_std(prices, 20)
        upper = mid + 2 * std
        lower = mid - 2 * std
        current = prices[-1]

        if current > upper:
            raw = -0.7  # 超买
        elif current < lower:
            raw = 0.7   # 超卖
        else:
            pos = (current - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
            raw = (pos - 0.5) * 2 * 0.5  # -0.5 ~ +0.5

        value = max(-1.0, min(1.0, raw))
        return value, {
            "upper": round(upper, 4), "mid": round(mid, 4),
            "lower": round(lower, 4), "std": round(std, 4),
            "position": round((current - lower) / (upper - lower), 3) if (upper - lower) > 0 else 0.5
        }

    def _get_nav_prices(self, fund_code, days=30):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号4：动量信号 ──────────────────────────────────────────────────
class FundMomentumSignal:
    """基金动量信号 — N日累计涨幅"""
    name = "momentum"
    description = "价格动量"

    def __init__(self, data_source=None, period=20):
        self.data_source = data_source
        self.period = period

    def compute(self, fund_code, days=60):
        """
        动量信号
        近N日涨幅 > 10% → 动量过强，可能反转
        近N日涨幅 < -10% → 跌幅过大，可能反弹
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < self.period + 5:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        start_price = prices[-(self.period + 1)]
        end_price = prices[-1]
        if start_price == 0:
            return SIGNAL_NEUTRAL, {"error": "价格为零"}

        chg_pct = (end_price - start_price) / start_price * 100

        raw = chg_pct / 10.0  # ±10% → ±1
        value = max(-1.0, min(1.0, raw))
        return value, {
            "period": self.period, "chg_pct": round(chg_pct, 2),
            "start_price": start_price, "end_price": end_price
        }

    def _get_nav_prices(self, fund_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号5：波动率信号 ──────────────────────────────────────────────────
class FundVolatilitySignal:
    """基金波动率信号 — 历史波动率与同类比较"""
    name = "volatility"
    description = "波动率水平"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=60):
        """
        波动率信号
        波动率过高 → 高风险信号 → 偏空（对稳健型客户）
        波动率适中 → 正常
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 20:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        # 计算日波动率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])

        if len(returns) < 10:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        daily_std = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5
        annual_vol = daily_std * math.sqrt(252) * 100  # 年化波动率%

        # 主观阈值：A股主动基金波动率通常 15-30%
        raw = 0.0
        if annual_vol > 35:
            raw = -0.6  # 波动率过高
        elif annual_vol > 28:
            raw = -0.3  # 波动率偏高
        elif annual_vol < 12:
            raw = 0.3   # 波动率过低（可能过于稳健）
        else:
            raw = 0.0   # 正常

        value = max(-1.0, min(1.0, raw))
        return value, {
            "daily_std_pct": round(daily_std * 100, 3),
            "annual_vol_pct": round(annual_vol, 2),
            "assessment": "偏高" if annual_vol > 28 else ("偏低" if annual_vol < 12 else "正常")
        }

    def _get_nav_prices(self, fund_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号6：趋势跟踪信号 ──────────────────────────────────────────────
class FundTrendSignal:
    """基金趋势跟踪信号 — 基于均线多空排列"""
    name = "trend"
    description = "多空趋势"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=90):
        """
        趋势信号
        MA5 > MA10 > MA20 > MA60 → 多头趋势 → 偏多
        MA5 < MA10 < MA20 < MA60 → 空头趋势 → 偏空
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 60:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        ma5 = FundNavTools.calc_ema(prices, 5) or prices[-1]
        ma10 = FundNavTools.calc_ema(prices, 10) or prices[-1]
        ma20 = FundNavTools.calc_ema(prices, 20) or prices[-1]
        ma60 = FundNavTools.calc_ema(prices, 60) or prices[-1]

        # 计算均线斜率（趋势方向）
        slope_ma5 = (ma5 - (FundNavTools.calc_ema(prices[:-5], 5) or ma5)) / ma5 if len(prices) >= 10 else 0

        raw = 0.0
        if ma5 > ma10 > ma20 > ma60:
            raw = 0.7 if slope_ma5 > 0 else 0.4  # 多头排列
        elif ma5 < ma10 < ma20 < ma60:
            raw = -0.7 if slope_ma5 < 0 else -0.4  # 空头排列
        else:
            raw = 0.0  # 震荡

        value = max(-1.0, min(1.0, raw))
        return value, {
            "ma5": round(ma5, 4), "ma10": round(ma10, 4),
            "ma20": round(ma20, 4), "ma60": round(ma60, 4),
            "slope_ma5": round(slope_ma5 * 100, 4),
            "trend": "多头" if raw > 0.3 else ("空头" if raw < -0.3 else "震荡")
        }

    def _get_nav_prices(self, fund_code, days=90):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号7：最大回撤信号 ──────────────────────────────────────────────
class FundMaxDrawdownSignal:
    """基金最大回撤信号 — 滚动窗口最大回撤评估"""
    name = "max_drawdown"
    description = "最大回撤风险"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=120):
        """
        计算滚动最大回撤
        MDD过大 → 高风险信号 → 偏空
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 30:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        # 计算滚动最大回撤
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        mdd_pct = max_dd * 100

        # A股主动基金：MDD < 15%正常，15-25%偏高，> 25%高风险
        raw = 0.0
        if mdd_pct < 10:
            raw = 0.5  # 回撤控制好
        elif mdd_pct < 20:
            raw = 0.0  # 正常
        elif mdd_pct < 30:
            raw = -0.4  # 偏高
        else:
            raw = -0.7  # 高风险

        value = max(-1.0, min(1.0, raw))
        return value, {
            "max_drawdown_pct": round(mdd_pct, 2),
            "peak": round(peak, 4),
            "current": round(prices[-1], 4),
            "assessment": "优秀" if mdd_pct < 10 else ("正常" if mdd_pct < 20 else ("偏高" if mdd_pct < 30 else "高风险"))
        }

    def _get_nav_prices(self, fund_code, days=120):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 信号8：夏普比率信号 ──────────────────────────────────────────────
class FundSharpeSignal:
    """基金夏普比率信号 — 风险调整后收益评估"""
    name = "sharpe"
    description = "风险调整收益"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, fund_code, days=252):
        """
        计算年化夏普比率
        夏普 > 1.0 → 优秀
        夏普 < 0 → 偏空
        """
        prices = self._get_nav_prices(fund_code, days=days)
        if len(prices) < 60:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        sharpe = FundNavTools.calc_sharpe(prices, period=60, risk_free=0.03)

        raw = 0.0
        if sharpe > 2.0:
            raw = 0.8
        elif sharpe > 1.0:
            raw = 0.5
        elif sharpe > 0.5:
            raw = 0.2
        elif sharpe > 0:
            raw = 0.0
        elif sharpe > -0.5:
            raw = -0.3
        else:
            raw = -0.6

        value = max(-1.0, min(1.0, raw))
        return value, {
            "sharpe_ratio": round(sharpe, 2),
            "annual_risk_free": 0.03,
            "assessment": "优秀" if sharpe > 1.0 else ("良好" if sharpe > 0.5 else ("一般" if sharpe > 0 else "不佳"))
        }

    def _get_nav_prices(self, fund_code, days=252):
        if self.data_source is None:
            return []
        return self.data_source.get_nav_history(fund_code, days=days)


# ── 自适应权重 ──────────────────────────────────────────────────────
class AdaptiveWeights:
    """根据市场状态动态调整信号权重"""

    @staticmethod
    def get_weights(volatility_pct=None, trend_signal=None):
        """
        根据市场波动率和趋势信号返回动态权重

        牛市（低波动+上升趋势）：增加动量/趋势权重
        熊市（高波动+下降趋势）：增加回撤/波动率/集中度权重
        震荡（中等波动）：增加 RSI/布林带/均线偏离权重
        """
        # 默认权重（震荡市）
        weights = {
            'ma_deviation': 0.12,
            'rsi': 0.12,
            'bollinger': 0.08,
            'momentum': 0.12,
            'volatility': 0.08,
            'trend': 0.15,
            'concentration': 0.13,
            'max_drawdown': 0.10,
            'sharpe': 0.10,
        }

        if volatility_pct is None:
            return weights

        # 高波动 → 熊市模式
        if volatility_pct > 28:
            weights['max_drawdown'] = 0.15
            weights['volatility'] = 0.12
            weights['concentration'] = 0.15
            weights['momentum'] = 0.08
            weights['trend'] = 0.10
        # 低波动 → 牛市模式
        elif volatility_pct < 12:
            weights['momentum'] = 0.15
            weights['trend'] = 0.20
            weights['max_drawdown'] = 0.06
            weights['volatility'] = 0.05
            weights['concentration'] = 0.10

        # 如果趋势明确，增强趋势信号
        if trend_signal is not None and abs(trend_signal) > 0.5:
            weights['trend'] += 0.05
            # 从其他权重中减去
            for k in ['bollinger', 'volatility']:
                if weights[k] > 0.05:
                    weights[k] -= 0.025

        # 归一化
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    @staticmethod
    def detect_market_regime(volatility_pct):
        """检测市场状态"""
        if volatility_pct > 28:
            return "熊市/高波动"
        elif volatility_pct < 12:
            return "牛市/低波动"
        else:
            return "震荡/正常波动"


# ── 持仓分析信号 ──────────────────────────────────────────────────────
class HoldingConcentrationSignal:
    """持仓集中度信号 — 基于基金经理持仓风格分析"""
    name = "concentration"
    description = "持仓集中度风险"

    def __init__(self, holdings_db=None, managers_db=None):
        self.holdings_db = holdings_db or {}  # 持仓数据库
        self.managers_db = managers_db or {}  # 经理数据库

    def compute(self, fund_code, client_risk_tolerance='稳健型'):
        """
        持仓集中度风险信号
        单一行业集中度过高 → 高风险
        与客户风险偏好不匹配 → 建议调整
        """
        # 查找基金和经理信息
        manager = self._find_manager_by_fund(fund_code)
        if not manager:
            return SIGNAL_NEUTRAL, {"error": "未找到经理信息"}

        stock_pool = manager.get('stock_pool', [])
        sector = manager.get('sector_description', '')
        style = manager.get('investment_style', '')
        risk_warning = manager.get('risk_warning', '')

        # 行业集中度评估
        concentration_score = len(stock_pool)  # 持仓股票数量越少越集中

        raw = 0.0
        if concentration_score <= 5:
            raw = -0.5  # 持仓过于集中，高风险
        elif concentration_score >= 15:
            raw = 0.3  # 分散度好

        # 风格匹配评估
        risk_level_map = {'保守型': -1, '稳健型': 0, '平衡型': 0.5, '积极型': 1, '激进型': 1}
        client_level = risk_level_map.get(client_risk_tolerance, 0)
        style_level = 1 if style == '成长型' else (-1 if style == '价值型' else 0)

        style_mismatch = abs(client_level - style_level)
        if style_mismatch > 0.5:
            raw -= 0.3  # 风格不匹配

        # 高波动警告
        if '高波动' in risk_warning or '短期回撤' in risk_warning:
            if client_level < 0.5:
                raw -= 0.3  # 客户风险承受不足

        value = max(-1.0, min(1.0, raw))
        return value, {
            "stock_count": concentration_score,
            "style": style,
            "sector": sector,
            "risk_warning": risk_warning,
            "assessment": "集中度高" if concentration_score <= 5 else "分散度好"
        }

    def _find_manager_by_fund(self, fund_code):
        for m in self.managers_db.values():
            if m.get('current_fund_code') == str(fund_code):
                return m
        return None


# ── 基金数据源（适配天天基金网）───────────────────────────────────────
class FundDataSource:
    """
    基金数据源 — 从天天基金网获取净值数据
    数据路径: 相对于 DATA_DIR
    """

    def __init__(self, data_dir=None):
        from pathlib import Path
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._cache = {}
        self._session = None

    def _get_session(self):
        if self._session is None:
            import urllib.request
            self._session = urllib.request
        return self._session

    def get_nav_history(self, fund_code, days=60):
        """
        获取基金历史净值
        优先从本地缓存读取，否则从网络获取
        """
        cache_key = f"{fund_code}_{days}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 尝试从本地 holdings_database.json 读取
        navs = self._load_from_local(fund_code, days)
        if navs:
            self._cache[cache_key] = navs
            return navs

        # 从网络获取（天天基金净值接口）
        navs = self._fetch_from_network(fund_code, days)
        if navs:
            self._cache[cache_key] = navs

        return navs

    def _load_from_local(self, fund_code, days):
        """从本地持仓数据库读取净值历史（统一经 normalize_holdings 解码各历史格式）"""
        holdings_path = self.data_dir / "holdings_database.json"
        if not holdings_path.exists():
            return []

        try:
            with open(holdings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            return []

        holdings_list = normalize_holdings(data)

        # 查找该基金的净值历史
        navs = []
        for h in holdings_list:
            if str(h.get('fund_code', '')) == str(fund_code):
                # 尝试从持仓记录中提取净值历史
                nav_history = h.get('nav_history', [])
                if nav_history:
                    navs = nav_history[-days:]
                    break

        return navs

    def _fetch_from_network(self, fund_code, days):
        """
        从多个数据源获取净值历史
        优先级：腾讯财经 → 天天基金 → 同花顺 → 雪球
        """
        import re, urllib.request

        # 方案1：腾讯财经 API（GBK编码）
        navs = self._fetch_from_tx(fund_code, days)
        if navs and len(navs) >= 20:
            return navs

        # 方案2：天天基金网详情页 JS
        navs = self._fetch_from_eastmoney(fund_code, days)
        if navs and len(navs) >= 20:
            return navs

        return []

    def _fetch_from_tx(self, fund_code, days):
        """腾讯财经 API — GBK编码"""
        import re, urllib.request

        try:
            # 腾讯行情接口：sh=上海基金，sz=深圳基金
            code = fund_code.zfill(6)
            prefix = 'sh' if code.startswith(('5', '6', '7', '8', '9')) else 'sz'
            url = f"https://qt.gtimg.cn/q={prefix}{code}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://finance.qq.com/'
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode('gbk', errors='replace')

            # 解析格式: v="基金名称,代码,...,最新净值,日期,..."
            m = re.search(r'="([^"]+)"', text)
            if not m:
                return []

            parts = m.group(1).split('~')
            if len(parts) < 35:
                return []

            # 腾讯只提供当前净值，需要历史的话用其他接口
            # 这里返回空，让天天基金接口尝试
            return []
        except Exception:
            return []

    def _fetch_from_eastmoney(self, fund_code, days):
        """天天基金网详情页 JS — JSON格式"""
        import re, json, urllib.request

        try:
            url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://fund.eastmoney.com/'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode('utf-8', errors='replace')

            nav_match = re.search(r'Data_netWorthTrend\s*=\s*\[(.+?)\]', text, re.DOTALL)
            if not nav_match:
                return []

            array_str = '[' + nav_match.group(1) + ']'
            data = json.loads(array_str)

            navs = [float(d['y']) for d in data if d.get('y') and float(d['y']) > 0]
            return navs[-days:] if navs else []
        except Exception:
            return []

    def get_today_estimate(self, fund_code):
        """
        获取今日估值
        优先级：天天基金估值 → 腾讯财经实时 → 同花顺 → 雪球
        """
        import re, urllib.request

        # 方案1：天天基金估值（最常用）
        result = self._get_estimate_from_eastmoney(fund_code)
        if result[0] is not None:
            return result

        # 方案2：腾讯财经实时行情
        result = self._get_estimate_from_tx(fund_code)
        if result[0] is not None:
            return result

        return None, None

    def _get_estimate_from_eastmoney(self, fund_code):
        """天天基金估值接口"""
        import re, urllib.request
        try:
            url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt=0"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://fund.eastmoney.com/'
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode('utf-8', errors='replace')

            # jsonpgz回调格式: jQuery.getpz("{...}")
            m = re.search(r'\{.+?"gsz":\s*"?([^",]+)', text)
            gszz = re.search(r'"?gszz":\s*"?([^",]+)', text)
            if m:
                gsz = float(m.group(1))
                gszz_str = gszz.group(1) if gszz else "0"
                try:
                    gszz_pct = float(gszz_str)
                except Exception:
                    gszz_pct = 0
                return gsz, gszz_pct
        except Exception:
            pass
        return None, None

    def _get_estimate_from_tx(self, fund_code):
        """腾讯财经实时行情"""
        import re, urllib.request
        try:
            code = fund_code.zfill(6)
            prefix = 'sh' if code.startswith(('5', '6', '7', '8', '9')) else 'sz'
            url = f"https://qt.gtimg.cn/q={prefix}{code}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://finance.qq.com/'
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode('gbk', errors='replace')

            # 格式: v="基金名称,代码,...,当前净值,昨日净值,..."
            m = re.search(r'="([^"]+)"', text)
            if not m:
                return None, None

            parts = m.group(1).split('~')
            if len(parts) < 35:
                return None, None

            current_nav = float(parts[3])  # 当前净值
            yesterday_nav = float(parts[4])  # 昨日净值
            chg_pct = ((current_nav - yesterday_nav) / yesterday_nav * 100) if yesterday_nav > 0 else 0

            return current_nav, chg_pct
        except Exception:
            return None, None


# ── 基金量化分析器 ───────────────────────────────────────────────────
class FundQuantAnalyzer:
    """
    基金量化分析器 — 综合所有信号
    为客户持仓提供量化信号和调仓建议
    """

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.data_source = FundDataSource(data_dir)
        self.managers_db = {}
        self.holdings_db = {}
        self._load_data()

        # 初始化各信号
        self.ma_signal = MaDeviationSignal(self.data_source)
        self.rsi_signal = FundRsiSignal(self.data_source)
        self.bollinger_signal = FundBollingerSignal(self.data_source)
        self.momentum_signal = FundMomentumSignal(self.data_source)
        self.volatility_signal = FundVolatilitySignal(self.data_source)
        self.trend_signal = FundTrendSignal(self.data_source)
        self.concentration_signal = HoldingConcentrationSignal(self.holdings_db, self.managers_db)
        self.max_drawdown_signal = FundMaxDrawdownSignal(self.data_source)
        self.sharpe_signal = FundSharpeSignal(self.data_source)

    def _load_data(self):
        """加载本地数据库（列式压缩格式经 load_json_data 透明解码）"""
        try:
            path = self.data_dir / 'fund_managers_distilled.json'
            if path.exists():
                data = load_json_data(str(path))
                items = data.get('managers', data.get('items', []))
                for m in items:
                    # shipped 蒸馏数据可能缺少 current_fund_code 字段，
                    # 此时按 manager_id 建索引（按基金代码反查会落空并如实报"未找到"，不编造）
                    key = m.get('current_fund_code', '') or m.get('manager_id', '')
                    if key:
                        self.managers_db[key] = m
                if not self.managers_db:
                    logger.warning("fund_managers_distilled.json 加载为空（键名/格式不匹配？）")
        except Exception as e:
            logger.warning("加载经理数据失败: %s", e)

        try:
            path = self.data_dir / 'holdings_database.json'
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.holdings_db = json.load(f)
        except Exception:
            pass

    def analyze_fund(self, fund_code, client_risk='稳健型'):
        """
        综合分析单只基金

        返回:
            dict: {
                "fund_code": str,
                "signals": {signal_name: (value, components)},
                "combined_signal": float,  # 综合信号 [-1, +1]
                "action": str,  # "加仓"/"持有"/"减仓"/"观望"
                "action_reason": str,
                "today_estimate": (gsz, gszz_pct) or None,
            }
        """
        # 获取今日估值
        estimate = self.get_today_estimate(fund_code)

        # 计算各信号
        signals = {}

        # 1. 均线偏离
        val, comp = self.ma_signal.compute(fund_code)
        signals['ma_deviation'] = {'value': val, 'components': comp}

        # 2. RSI
        val, comp = self.rsi_signal.compute(fund_code)
        signals['rsi'] = {'value': val, 'components': comp}

        # 3. 布林带
        val, comp = self.bollinger_signal.compute(fund_code)
        signals['bollinger'] = {'value': val, 'components': comp}

        # 4. 动量
        val, comp = self.momentum_signal.compute(fund_code)
        signals['momentum'] = {'value': val, 'components': comp}

        # 5. 波动率
        val, comp = self.volatility_signal.compute(fund_code)
        signals['volatility'] = {'value': val, 'components': comp}

        # 6. 趋势
        val, comp = self.trend_signal.compute(fund_code)
        signals['trend'] = {'value': val, 'components': comp}

        # 7. 持仓集中度（需要经理信息）
        val, comp = self.concentration_signal.compute(fund_code, client_risk)
        signals['concentration'] = {'value': val, 'components': comp}

        # 8. 最大回撤
        val, comp = self.max_drawdown_signal.compute(fund_code)
        signals['max_drawdown'] = {'value': val, 'components': comp}

        # 9. 夏普比率
        val, comp = self.sharpe_signal.compute(fund_code)
        signals['sharpe'] = {'value': val, 'components': comp}

        # 获取波动率用于自适应权重
        vol_value = signals.get('volatility', {}).get('components', {}).get('annual_vol_pct')
        trend_value = signals.get('trend', {}).get('value')

        # 自适应权重（10 维信号）
        weights = AdaptiveWeights.get_weights(
            volatility_pct=vol_value,
            trend_signal=trend_value
        )
        combined = sum(signals[k]['value'] * w for k, w in weights.items())

        # 市场状态
        market_regime = AdaptiveWeights.detect_market_regime(vol_value) if vol_value else "未知"

        # 生成操作建议
        action, reason = self._generate_action(combined, signals, client_risk)

        return {
            'fund_code': fund_code,
            'signals': signals,
            'combined_signal': round(combined, 3),
            'action': action,
            'action_reason': reason,
            'market_regime': market_regime,
            'adaptive_weights': {k: round(v, 3) for k, v in weights.items()},
            'today_estimate': estimate,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def _generate_action(self, combined, signals, client_risk):
        """根据信号生成操作建议"""
        if combined > ADJUST_THRESHOLD_BUY:
            action = "加仓"
            reason = f"综合信号偏多({combined:+.2f})，技术面支持，可适度加仓"
        elif combined < ADJUST_THRESHOLD_SELL:
            action = "减仓"
            reason = f"综合信号偏空({combined:+.2f})，建议控制风险，适度减仓"
        elif combined > ADJUST_NEUTRAL_BAND[1]:
            action = "持有/适度加仓"
            reason = f"综合信号偏积极({combined:+.2f})，可保持仓位"
        elif combined < ADJUST_NEUTRAL_BAND[0]:
            action = "持有/适度减仓"
            reason = f"综合信号偏谨慎({combined:+.2f})，建议保持观望"
        else:
            action = "持有"
            reason = f"综合信号中性({combined:+.2f})，无明显调仓必要"

        # 结合客户风险偏好调整
        if client_risk == '保守型' and combined < -0.2:
            action = "减仓"
            reason = f"偏弱市场环境下，对保守型客户建议控制仓位"

        return action, reason

    def analyze_portfolio(self, holdings, client_risk='稳健型'):
        """
        分析客户整个基金持仓组合

        参数:
            holdings: list[dict], 每项包含 fund_code, shares, cost, purchase_date
            client_risk: 客户风险偏好

        返回:
            dict: 组合分析结果
        """
        results = []
        for h in holdings:
            fund_code = h.get('fund_code')
            try:
                analysis = self.analyze_fund(fund_code, client_risk)
            except Exception as e:
                # 网络或其他问题导致分析失败时，返回中性结果
                analysis = {
                    'fund_code': fund_code,
                    'signals': {},
                    'combined_signal': 0.0,
                    'action': '持有',
                    'action_reason': '数据暂时无法获取',
                    'today_estimate': None,
                    'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            analysis['shares'] = h.get('shares', 0)
            analysis['cost'] = h.get('cost', 0)
            analysis['purchase_date'] = h.get('purchase_date', '')
            results.append(analysis)

        # 组合整体信号
        combined_list = [r['combined_signal'] for r in results if 'error' not in r]
        portfolio_signal = sum(combined_list) / len(combined_list) if combined_list else 0

        # 调仓建议汇总
        actions = [r['action'] for r in results]
        buy_count = sum(1 for a in actions if '加仓' in a)
        sell_count = sum(1 for a in actions if '减仓' in a)

        return {
            'holdings_analysis': results,
            'portfolio_combined_signal': round(portfolio_signal, 3),
            'portfolio_action_summary': {
                'total': len(results),
                'buy': buy_count,
                'sell': sell_count,
                'hold': len(results) - buy_count - sell_count,
            },
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def get_today_estimate(self, fund_code):
        """获取今日估值"""
        return self.data_source.get_today_estimate(fund_code)

    def format_analysis_report(self, analysis):
        """格式化分析报告"""
        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  基金量化分析报告')
        lines.append('=' * 70)

        fund_code = analysis.get('fund_code', '')

        # 今日估值
        estimate = analysis.get('today_estimate')
        if estimate and estimate[0]:
            lines.append(f"\n【今日估值】")
            lines.append(f"  单位净值: {estimate[0]:.4f}")
            if estimate[1] is not None:
                sign = "+" if estimate[1] > 0 else ""
                lines.append(f"  估算涨幅: {sign}{estimate[1]:.2f}%")

        # 综合信号
        lines.append(f"\n【综合信号】")
        combined = analysis.get('combined_signal', 0)
        signal_bar = "█" * int(abs(combined) * 10) + "░" * (10 - int(abs(combined) * 10))
        sign_str = "+" if combined > 0 else ""
        lines.append(f"  {sign_str}{combined:.2f} [{signal_bar}]")
        lines.append(f"  建议操作: {analysis.get('action', '观望')}")
        lines.append(f"  操作理由: {analysis.get('action_reason', '')}")

        # 各信号详情
        lines.append(f"\n【信号明细】")
        signals = analysis.get('signals', {})
        for name, data in signals.items():
            val = data.get('value', 0)
            sign = "+" if val > 0 else ""
            comp = data.get('components', {})
            desc = comp.get('assessment', comp.get('trend', comp.get('rsi', comp.get('current', ''))))
            if isinstance(desc, float):
                desc = f"{desc:.2f}"
            lines.append(f"  {name}: {sign}{val:.2f} ({desc})")

        lines.append('\n' + '=' * 70)
        lines.append(f"分析时间: {analysis.get('analyzed_at', '')}")
        lines.append('=' * 70 + '\n')
        return '\n'.join(lines)

    def format_portfolio_analysis_report(self, portfolio_analysis):
        """格式化组合分析报告"""
        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  基金持仓组合量化分析报告')
        lines.append('=' * 70)

        summary = portfolio_analysis.get('portfolio_action_summary', {})
        combined = portfolio_analysis.get('portfolio_combined_signal', 0)

        lines.append(f"\n【组合概览】")
        lines.append(f"  总持仓: {summary.get('total', 0)}只")
        lines.append(f"  综合信号: {combined:+.2f}")
        lines.append(f"  建议操作: 加仓{summary.get('buy', 0)}只 / 减仓{summary.get('sell', 0)}只 / 持有{summary.get('hold', 0)}只")

        lines.append(f"\n【持仓明细】")
        lines.append('-' * 70)
        for h in portfolio_analysis.get('holdings_analysis', []):
            action = h.get('action', '观望')
            signal = h.get('combined_signal', 0)
            sign = "+" if signal > 0 else ""
            estimate = h.get('today_estimate')
            est_str = f"{estimate[0]:.3f}({estimate[1]:+.2f}%)" if estimate and estimate[0] else "暂无估值"
            lines.append(f"\n{h.get('fund_code', '')} {action} [{sign}{signal:.2f}]")
            lines.append(f"  估值: {est_str}")
            lines.append(f"  理由: {h.get('action_reason', '')}")

        lines.append('\n' + '=' * 70)
        lines.append(f"分析时间: {portfolio_analysis.get('analyzed_at', '')}")
        lines.append('=' * 70 + '\n')
        return '\n'.join(lines)


# ── v4.4 增强：基金绩效归因（Alpha/Beta/Sortino/Calmar/Information Ratio）───

class FundPerfMetrics:
    """基金绩效指标计算器 — Alpha/Beta/Sortino/Calmar/Info Ratio"""
    risk_free = 0.025  # 无风险利率 2.5%

    @classmethod
    def calc_all(cls, nav_prices, benchmark_prices=None):
        """一次性计算所有绩效指标。
        Args:
            nav_prices: 基金净值序列（日度）
            benchmark_prices: 基准价格序列（如沪深300），用于 Alpha/Beta
        Returns: dict with annual_return, sharpe, sortino, calmar, max_drawdown, alpha, beta, ir
        """
        if not nav_prices or len(nav_prices) < 60:
            return {"error": "数据不足（至少需要60个交易日）"}
        r = [(nav_prices[i] - nav_prices[i - 1]) / nav_prices[i - 1]
             for i in range(1, len(nav_prices))]
        n = len(r)
        rf_daily = cls.risk_free / 252
        excess = [d - rf_daily for d in r]
        avg_ex = sum(excess) / n
        std_ex = (sum((e - avg_ex) ** 2 for e in excess) / (n - 1)) ** 0.5
        annual_ret = ((nav_prices[-1] / nav_prices[0]) ** (252 / n) - 1) * 100
        annual_vol = std_ex * (252 ** 0.5) * 100
        sharpe = (avg_ex / std_ex * (252 ** 0.5)) if std_ex > 0 else 0
        downside = [min(0, e) ** 2 for e in excess]
        ds = (sum(downside) / n) ** 0.5
        sortino = (annual_ret / 100 - cls.risk_free) / ds if ds > 0 else 0
        peak = nav_prices[0]; mdd = 0
        for p in nav_prices:
            if p > peak: peak = p
            dd = (peak - p) / peak
            if dd > mdd: mdd = dd
        calmar = (annual_ret / 100) / mdd if mdd > 0 else 0
        alpha = beta = ir_val = 0
        if benchmark_prices and len(benchmark_prices) >= n + 1:
            bm_r = [(benchmark_prices[i] - benchmark_prices[i - 1]) / benchmark_prices[i - 1]
                    for i in range(1, len(benchmark_prices))]
            bm_n = min(n, len(bm_r))
            f_avg = sum(r[:bm_n]) / bm_n
            b_avg = sum(bm_r[:bm_n]) / bm_n
            cov = sum((r[i] - f_avg) * (bm_r[i] - b_avg) for i in range(bm_n)) / (bm_n - 1)
            var = sum((b - b_avg) ** 2 for b in bm_r[:bm_n]) / (bm_n - 1)
            beta = round(cov / var, 3) if var > 0 else 1
            alpha = (f_avg - (rf_daily + beta * (b_avg - rf_daily))) * 252 * 100
            diffs = [r[i] - bm_r[i] for i in range(bm_n)]
            avg_diff = sum(diffs) / bm_n
            std_diff = (sum((d - avg_diff) ** 2 for d in diffs) / (bm_n - 1)) ** 0.5
            ir_val = (avg_diff / std_diff * (252 ** 0.5)) if std_diff > 0 else 0
        return {"annual_return": round(annual_ret, 2), "annual_volatility": round(annual_vol, 2),
                "sharpe": round(sharpe, 2), "sortino": round(sortino, 2),
                "calmar": round(calmar, 2), "max_drawdown": round(mdd * 100, 2),
                "alpha": round(alpha, 2), "beta": beta, "information_ratio": round(ir_val, 2)}

    @classmethod
    def dca_backtest(cls, nav_prices, monthly=1000, months=36):
        """定投回测。"""
        if len(nav_prices) < months * 22: return {"error": "数据不足"}
        nav = nav_prices[-months * 22:]
        units = sum(monthly / nav[i] for i in range(0, len(nav), 22))
        invested = monthly * months
        final = units * nav[-1]
        return {"invested": invested, "final": round(final, 2),
                "return_pct": round((final / invested - 1) * 100, 2),
                "annualized": round(((final / invested) ** (12 / months) - 1) * 100, 2)}


# ── 入口点 ───────────────────────────────────────────────────────────
def main():
    """测试"""
    analyzer = FundQuantAnalyzer()
    print("基金量化分析器 v1.0")
    print(f"加载了 {len(analyzer.managers_db)} 只基金数据")

    # 测试单基金分析
    print("\n--- 测试: 分析 001924 ---")
    result = analyzer.analyze_fund('001924', client_risk='积极型')
    print(analyzer.format_analysis_report(result))


if __name__ == '__main__':
    main()