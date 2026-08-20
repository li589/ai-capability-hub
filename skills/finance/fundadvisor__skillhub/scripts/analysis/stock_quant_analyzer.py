# -*- coding: utf-8 -*-
"""
A股股票量化分析器 v1.0
基于A股市场特点和个股价格数据，提供技术分析和选股信号
适用于沪深A股（T+1交易、涨跌停板、题材炒作等）
"""
from __future__ import annotations
import json, math, random, re
from datetime import datetime, timedelta
from pathlib import Path

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


# ── 信号常量 ──────────────────────────────────────────────────────────
SIGNAL_BULL = 1    # 看多信号
SIGNAL_BEAR = -1   # 看空信号
SIGNAL_NEUTRAL = 0 # 中性信号

# 调仓阈值
ADJUST_THRESHOLD_BUY = 0.6   # 综合信号 > 0.6 → 建议买入/加仓
ADJUST_THRESHOLD_SELL = -0.6 # 综合信号 < -0.6 → 建议卖出/减仓
ADJUST_NEUTRAL_BAND = (-0.25, 0.25) # 中性区间


# ── 股票行情工具 ──────────────────────────────────────────────────────
class StockTools:
    """股票技术分析工具"""

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
        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0
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
    def calc_macd(prices, fast=12, slow=26, signal=9):
        """计算MACD"""
        if len(prices) < slow + signal:
            return None, None, None

        # 计算EMA
        ema_fast = StockTools.calc_ema(prices, fast)
        ema_slow = StockTools.calc_ema(prices, slow)

        if ema_fast is None or ema_slow is None:
            return None, None, None

        dif = ema_fast - ema_slow
        dea = StockTools.calc_ema([dif] * signal, signal) or dif * 0.9
        macd_bar = (dif - dea) * 2

        return round(dif, 3), round(dea, 3), round(macd_bar, 3)

    @staticmethod
    def calc_kdj(highs, lows, closes, period=9):
        """计算KDJ"""
        if len(highs) < period:
            return None, None, None

        # 计算RSV
        recent_high = max(highs[-period:])
        recent_low = min(lows[-period:])
        recent_close = closes[-1]

        if recent_high == recent_low:
            return 50, 50, 50

        rsv = (recent_close - recent_low) / (recent_high - recent_low) * 100

        # 计算K、D、J
        k = 2/3 * 50 + 1/3 * rsv
        d = 2/3 * 50 + 1/3 * k
        j = 3 * k - 2 * d

        return round(k, 2), round(d, 2), round(j, 2)

    @staticmethod
    def calc_bollinger_bands(prices, period=20, std_dev=2):
        """计算布林带"""
        if len(prices) < period:
            return None, None, None

        recent = prices[-period:]
        mid = sum(recent) / period
        std = StockTools.calc_std(prices, period)

        upper = mid + std_dev * std
        lower = mid - std_dev * std

        return round(upper, 2), round(mid, 2), round(lower, 2)

    @staticmethod
    def calc_volume_ratio(volumes, period=5):
        """计算量比（今日成交量/最近N日平均成交量）"""
        if len(volumes) < period + 1:
            return 1.0

        avg_vol = sum(volumes[-period:-1]) / period if len(volumes) > period else volumes[-1]
        if avg_vol == 0:
            return 1.0

        return round(volumes[-1] / avg_vol, 2)


# ── 信号1：均线多头信号 ──────────────────────────────────────────────
class MaMultiSignal:
    """均线多头排列信号 — 个股短期、中期、长期趋势"""
    name = "ma_multi"
    description = "均线多头排列"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=60):
        """
        计算均线多头信号
        MA5 > MA10 > MA20 > MA60 → 多头 → 偏多
        MA5 < MA10 < MA20 < MA60 → 空头 → 偏空
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 60:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        prices = [d['close'] for d in data]

        ma5 = StockTools.calc_ema(prices, 5) or prices[-1]
        ma10 = StockTools.calc_ema(prices, 10) or prices[-1]
        ma20 = StockTools.calc_ema(prices, 20) or prices[-1]
        ma60 = StockTools.calc_ema(prices, 60) or prices[-1]

        current = prices[-1]

        # 判断多头/空头
        if ma5 > ma10 > ma20 > ma60:
            # 计算斜率
            slope = (ma5 - ma10) / ma10 * 100
            raw = 0.7 if slope > 0 else 0.4
        elif ma5 < ma10 < ma20 < ma60:
            slope = (ma10 - ma5) / ma10 * 100
            raw = -0.7 if slope > 0 else -0.4
        else:
            raw = 0.0

        # 偏离度
        deviation_pct = (current - ma20) / ma20 * 100 if ma20 > 0 else 0

        value = max(-1.0, min(1.0, raw))
        return value, {
            "ma5": round(ma5, 2), "ma10": round(ma10, 2),
            "ma20": round(ma20, 2), "ma60": round(ma60, 2),
            "current": round(current, 2),
            "deviation_pct": round(deviation_pct, 2),
            "trend": "多头" if raw > 0.3 else ("空头" if raw < -0.3 else "震荡")
        }

    def _get_stock_data(self, stock_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号2：MACD信号 ────────────────────────────────────────────────────
class MacdSignal:
    """MACD信号 — 趋势跟随指标"""
    name = "macd"
    description = "MACD金叉死叉"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=60):
        """
        MACD信号
        DIF > DEA 且 MACD柱翻红 → 金叉 → 偏多
        DIF < DEA 且 MACD柱翻绿 → 死叉 → 偏空
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 60:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        prices = [d['close'] for d in data]

        dif, dea, macd_bar = StockTools.calc_macd(prices)

        if dif is None:
            return SIGNAL_NEUTRAL, {"error": "计算失败"}

        raw = 0.0
        if dif > dea and macd_bar > 0:
            raw = 0.6  # 金叉偏多
        elif dif > dea and macd_bar < 0:
            raw = 0.3  # 即将死叉
        elif dif < dea and macd_bar < 0:
            raw = -0.6  # 死叉偏空
        elif dif < dea and macd_bar > 0:
            raw = -0.3  # 即将金叉

        value = max(-1.0, min(1.0, raw))
        return value, {
            "dif": dif, "dea": dea, "macd_bar": macd_bar,
            "signal": "金叉" if dif > dea else "死叉"
        }

    def _get_stock_data(self, stock_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号3：KDJ信号 ────────────────────────────────────────────────────
class KdjSignal:
    """KDJ信号 — 超买超卖指标"""
    name = "kdj"
    description = "KDJ超买超卖"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=30):
        """
        KDJ信号
        K < 20 且 J < 0 → 超卖 → 偏多
        K > 80 且 J > 100 → 超买 → 偏空
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 20:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        highs = [d.get('high', d['close']) for d in data]
        lows = [d.get('low', d['close']) for d in data]
        closes = [d['close'] for d in data]

        k, d, j = StockTools.calc_kdj(highs, lows, closes)

        if k is None:
            return SIGNAL_NEUTRAL, {"error": "计算失败"}

        raw = 0.0
        if k < 20 or j < 0:
            raw = 0.6  # 超卖偏多
        elif k > 80 or j > 100:
            raw = -0.6  # 超买偏空
        else:
            raw = (k - 50) / 50  # 标准化

        value = max(-1.0, min(1.0, raw))
        return value, {
            "k": k, "d": d, "j": j,
            "signal": "超卖" if k < 20 else ("超买" if k > 80 else "正常")
        }

    def _get_stock_data(self, stock_code, days=30):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号4：RSI信号 ────────────────────────────────────────────────────
class RsiSignal:
    """RSI信号 — 相对强弱指标"""
    name = "rsi"
    description = "RSI超买超卖"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=30):
        """
        RSI信号
        > 70: 超买 → 偏空
        < 30: 超卖 → 偏多
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 15:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        prices = [d['close'] for d in data]
        rsi = StockTools.calc_rsi(prices, period=14)

        if rsi is None:
            return SIGNAL_NEUTRAL, {"error": "计算失败"}

        raw = 0.0
        if rsi > 70:
            raw = (80 - rsi) / 10  # -1 ~ 0
        elif rsi < 30:
            raw = (30 - rsi) / 10  # 0 ~ +1
        else:
            raw = (rsi - 50) / 20  # 标准化

        value = max(-1.0, min(1.0, raw))
        return value, {"rsi": round(rsi, 2)}

    def _get_stock_data(self, stock_code, days=30):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号5：量价信号 ──────────────────────────────────────────────────
class VolumePriceSignal:
    """量价信号 — 成交量与价格配合分析"""
    name = "volume_price"
    description = "量价配合"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=30):
        """
        量价信号
        上涨放量 + 下跌缩量 → 健康 → 偏多
        上涨缩量 + 下跌放量 → 背离 → 偏空
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 20:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        volumes = [d.get('volume', 0) for d in data]
        prices = [d['close'] for d in data]

        # 计算近期量比
        vol_ratio = StockTools.calc_volume_ratio(volumes)

        # 计算涨跌
        price_change = (prices[-1] - prices[-2]) / prices[-2] * 100 if len(prices) > 1 else 0

        # 放量上涨 vs 缩量下跌
        raw = 0.0

        if price_change > 0 and vol_ratio > 1.5:
            raw = 0.5  # 放量上涨，健康
        elif price_change > 0 and vol_ratio < 0.8:
            raw = -0.3  # 缩量上涨，背离
        elif price_change < 0 and vol_ratio > 1.5:
            raw = -0.5  # 放量下跌，压力
        elif price_change < 0 and vol_ratio < 0.8:
            raw = 0.3  # 缩量下跌，可能见底

        # 量比极端情况
        if vol_ratio > 3:
            raw = max(raw - 0.2, -0.8)  # 异常放量，可能是主力出货
        elif vol_ratio < 0.5:
            raw = min(raw + 0.2, 0.8)  # 极度缩量，可能见底

        value = max(-1.0, min(1.0, raw))
        return value, {
            "vol_ratio": vol_ratio,
            "price_change_pct": round(price_change, 2),
            "signal": "放量上涨" if price_change > 0 and vol_ratio > 1.5 else
                     "缩量上涨" if price_change > 0 and vol_ratio < 0.8 else
                     "放量下跌" if price_change < 0 and vol_ratio > 1.5 else
                     "缩量下跌" if price_change < 0 and vol_ratio < 0.8 else "正常"
        }

    def _get_stock_data(self, stock_code, days=30):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号6：突破信号 ──────────────────────────────────────────────────
class BreakoutSignal:
    """突破信号 — 价格突破关键位置"""
    name = "breakout"
    description = "突破关键位置"

    def __init__(self, data_source=None):
        self.data_source = data_source

    def compute(self, stock_code, days=60):
        """
        突破信号
        突破前高 → 偏多
        跌破前低 → 偏空
        """
        data = self._get_stock_data(stock_code, days=days)
        if len(data) < 30:
            return SIGNAL_NEUTRAL, {"error": "数据不足"}

        highs = [d.get('high', d['close']) for d in data]
        lows = [d.get('low', d['close']) for d in data]
        closes = [d['close'] for d in data]

        current = closes[-1]

        # 计算近期高点/低点（20日）
        recent_high_20 = max(highs[-20:])
        recent_low_20 = min(lows[-20:])
        support_level = recent_low_20
        resistance_level = recent_high_20

        # 检查是否突破
        if current > resistance_level * 1.02:
            raw = 0.7  # 突破阻力位
        elif current < support_level * 0.98:
            raw = -0.7  # 跌破支撑位
        elif current > resistance_level * 0.98:
            raw = 0.3  # 接近阻力位
        elif current < support_level * 1.02:
            raw = -0.3  # 接近支撑位
        else:
            raw = 0.0  # 震荡

        # 布林带位置
        upper, mid, lower = StockTools.calc_bollinger_bands(closes)
        if upper:
            bollinger_pos = (current - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
            if bollinger_pos > 0.95:
                raw = min(raw - 0.2, -0.3)  # 触及上轨，可能回调

        value = max(-1.0, min(1.0, raw))
        return value, {
            "current": round(current, 2),
            "resistance_20d": round(resistance_level, 2),
            "support_20d": round(support_level, 2),
            "breakout": "突破" if current > resistance_level * 1.02 else
                       "跌破" if current < support_level * 0.98 else
                       "接近阻力" if current > resistance_level * 0.98 else
                       "接近支撑" if current < support_level * 1.02 else "震荡"
        }

    def _get_stock_data(self, stock_code, days=60):
        if self.data_source is None:
            return []
        return self.data_source.get_stock_history(stock_code, days=days)


# ── 信号7：题材联动信号 ─────────────────────────────────────────────
class SectorMomentumSignal:
    """题材联动信号 — 板块涨跌对个股的影响"""
    name = "sector_momentum"
    description = "题材联动"

    def __init__(self, sector_data=None):
        self.sector_data = sector_data or {}  # 板块数据 {'板块名': {'change': %, 'hot': bool}}

    def compute(self, stock_code, sector=None):
        """
        题材联动信号
        所属板块强势 → 个股偏多
        所属板块弱势 → 个股承压
        """
        if not sector:
            # 尝试通过股票代码判断板块
            sector = self._guess_sector(stock_code)

        if not sector or sector not in self.sector_data:
            return SIGNAL_NEUTRAL, {"error": "板块数据不可用"}

        sector_info = self.sector_data.get(sector, {})
        change = sector_info.get('change', 0)

        raw = change / 5  # ±2%以上板块 → ±0.4信号

        # 热度加成
        if sector_info.get('hot'):
            raw *= 1.2

        value = max(-1.0, min(1.0, raw))
        return value, {
            "sector": sector,
            "sector_change_pct": round(change, 2),
            "hot": sector_info.get('hot', False),
            "signal": "强势" if change > 1 else ("弱势" if change < -1 else "平稳")
        }

    def _guess_sector(self, stock_code):
        """根据股票代码猜测板块（简化版）"""
        # 实际应该用股票的基本面数据
        return None


# ── 股票数据源 ────────────────────────────────────────────────────────
class StockDataSource:
    """
    股票数据源 — 从网络获取实时和历史行情
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

    def get_stock_history(self, stock_code, days=60):
        """
        获取股票历史行情
        返回: list[dict] 每个dict包含 date, open, high, low, close, volume
        """
        cache_key = f"{stock_code}_{days}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 尝试从本地读取
        data = self._load_from_local(stock_code, days)
        if data:
            self._cache[cache_key] = data
            return data

        # 从网络获取
        data = self._fetch_from_network(stock_code, days)
        if data:
            self._cache[cache_key] = data

        return data

    def _load_from_local(self, stock_code, days):
        """从本地数据库读取"""
        # 简化实现，实际可以从本地缓存读取
        return []

    def _fetch_from_network(self, stock_code, days):
        """从网络获取股票数据"""
        import re, json, urllib.request, urllib.error

        # 腾讯财经实时行情
        try:
            code = stock_code.zfill(6)
            prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
            url = f"https://qt.gtimg.cn/q={prefix}{code}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://finance.qq.com/'
            })

            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode('gbk', errors='replace')

            m = re.search(r'="([^"]+)"', text)
            if not m:
                return []

            parts = m.group(1).split('~')
            if len(parts) < 40:
                return []

            # 解析实时数据（只有当前价格，需要历史的话用东方财富）
            current_price = float(parts[3])
            yesterday_close = float(parts[4])
            open_price = float(parts[5])
            high_price = float(parts[33])
            low_price = float(parts[34])
            volume = float(parts[36]) * 100  # 手转股

            return [{
                'date': datetime.now().strftime('%Y-%m-%d'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': current_price,
                'volume': volume
            }]

        except Exception:
            pass

        # 东方财富历史数据
        try:
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&ut=7eea2edcaed734bea9c332c59c17d209&klt=101&fqt=1&secid={'1.' + stock_code if stock_code.startswith('6') else '0.' + stock_code}&beg=0&end=20500101"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://quote.eastmoney.com/'
            })

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            klines = data.get('data', {}).get('klines', [])
            result = []

            for line in klines[-days:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    result.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'high': float(parts[2]),
                        'low': float(parts[3]),
                        'close': float(parts[4]),
                        'volume': float(parts[5])
                    })

            return result

        except Exception:
            return []

    def get_realtime_quote(self, stock_code):
        """获取实时行情"""
        import re, urllib.request

        try:
            code = stock_code.zfill(6)
            prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
            url = f"https://qt.gtimg.cn/q={prefix}{code}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.qq.com/'
            })

            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode('gbk', errors='replace')

            m = re.search(r'="([^"]+)"', text)
            if not m:
                return None

            parts = m.group(1).split('~')
            if len(parts) < 40:
                return None

            return {
                'code': stock_code,
                'name': parts[1],
                'current': float(parts[3]),
                'yesterday_close': float(parts[4]),
                'open': float(parts[5]),
                'high': float(parts[33]),
                'low': float(parts[34]),
                'volume': float(parts[36]) * 100,
                'change_pct': round((float(parts[3]) - float(parts[4])) / float(parts[4]) * 100, 2)
            }

        except Exception:
            return None


# ── 股票量化分析器 ───────────────────────────────────────────────────
class StockQuantAnalyzer:
    """
    股票量化分析器 — 综合所有信号
    支持沪深A股技术分析、题材炒作、突破选股等
    """

    def __init__(self, data_dir=None, sector_data=None):
        self.data_dir = data_dir or DATA_DIR
        self.data_source = StockDataSource(data_dir)
        self.sector_data = sector_data or {}
        self._init_signals()

    def _init_signals(self):
        """初始化各信号"""
        self.ma_signal = MaMultiSignal(self.data_source)
        self.macd_signal = MacdSignal(self.data_source)
        self.kdj_signal = KdjSignal(self.data_source)
        self.rsi_signal = RsiSignal(self.data_source)
        self.volume_signal = VolumePriceSignal(self.data_source)
        self.breakout_signal = BreakoutSignal(self.data_source)
        self.sector_signal = SectorMomentumSignal(self.sector_data)

    def analyze_stock(self, stock_code, sector=None, client_risk='稳健型'):
        """
        综合分析单只股票

        返回:
            dict: {
                "stock_code": str,
                "signals": {signal_name: (value, components)},
                "combined_signal": float,
                "action": str,
                "action_reason": str,
                "realtime_quote": dict or None,
            }
        """
        # 获取实时行情
        quote = self.get_realtime_quote(stock_code)

        # 计算各信号
        signals = {}

        # 1. 均线多头
        val, comp = self.ma_signal.compute(stock_code)
        signals['ma_multi'] = {'value': val, 'components': comp}

        # 2. MACD
        val, comp = self.macd_signal.compute(stock_code)
        signals['macd'] = {'value': val, 'components': comp}

        # 3. KDJ
        val, comp = self.kdj_signal.compute(stock_code)
        signals['kdj'] = {'value': val, 'components': comp}

        # 4. RSI
        val, comp = self.rsi_signal.compute(stock_code)
        signals['rsi'] = {'value': val, 'components': comp}

        # 5. 量价
        val, comp = self.volume_signal.compute(stock_code)
        signals['volume_price'] = {'value': val, 'components': comp}

        # 6. 突破
        val, comp = self.breakout_signal.compute(stock_code)
        signals['breakout'] = {'value': val, 'components': comp}

        # 7. 题材联动
        if sector:
            val, comp = self.sector_signal.compute(stock_code, sector)
            signals['sector_momentum'] = {'value': val, 'components': comp}

        # 计算综合信号
        weights = {
            'ma_multi': 0.15,
            'macd': 0.20,
            'kdj': 0.10,
            'rsi': 0.10,
            'volume_price': 0.15,
            'breakout': 0.15,
            'sector_momentum': 0.15,
        }

        combined = sum(signals[k]['value'] * weights.get(k, 0.1) for k in signals.keys())

        # 生成操作建议
        action, reason = self._generate_action(combined, signals, quote, client_risk)

        return {
            'stock_code': stock_code,
            'stock_name': quote.get('name', '') if quote else stock_code,
            'signals': signals,
            'combined_signal': round(combined, 3),
            'action': action,
            'action_reason': reason,
            'realtime_quote': quote,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def _generate_action(self, combined, signals, quote, client_risk):
        """根据信号生成操作建议"""
        action_map = {
            '激进型': {'buy': 0.4, 'sell': -0.4},
            '积极型': {'buy': 0.5, 'sell': -0.5},
            '平衡型': {'buy': 0.6, 'sell': -0.6},
            '稳健型': {'buy': 0.7, 'sell': -0.7},
            '保守型': {'buy': 0.8, 'sell': -0.8}
        }

        thresholds = action_map.get(client_risk, {'buy': 0.6, 'sell': -0.6})

        if combined > thresholds['buy']:
            action = "买入"
            reason = f"综合信号偏多({combined:+.2f})，技术面支持买入"
        elif combined < thresholds['sell']:
            action = "卖出"
            reason = f"综合信号偏空({combined:+.2f})，建议减仓回避"
        elif combined > 0.25:
            action = "持有/观望"
            reason = f"综合信号偏积极({combined:+.2f})，可继续持有"
        elif combined < -0.25:
            action = "持有/减仓"
            reason = f"综合信号偏谨慎({combined:+.2f})，建议适当减仓"
        else:
            action = "观望"
            reason = f"综合信号中性({combined:+.2f})，等待机会"

        # 结合涨跌停
        if quote:
            change_pct = quote.get('change_pct', 0)
            if change_pct > 9:
                action = "注意风险"
                reason = f"接近涨停，追高风险大"
            elif change_pct < -9:
                action = "观望"
                reason = f"接近跌停，不宜抄底"

        return action, reason

    def get_realtime_quote(self, stock_code):
        """获取实时行情"""
        return self.data_source.get_realtime_quote(stock_code)

    def analyze_portfolio(self, stocks, client_risk='稳健型'):
        """
        分析股票组合

        参数:
            stocks: list[dict], 每项包含 stock_code, shares, cost, sector
        """
        results = []
        for s in stocks:
            try:
                analysis = self.analyze_stock(s.get('stock_code'), s.get('sector'), client_risk)
            except Exception as e:
                analysis = {
                    'stock_code': s.get('stock_code'),
                    'stock_name': '',
                    'signals': {},
                    'combined_signal': 0.0,
                    'action': '观望',
                    'action_reason': '数据暂时无法获取',
                    'realtime_quote': None,
                    'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            analysis['shares'] = s.get('shares', 0)
            analysis['cost'] = s.get('cost', 0)
            results.append(analysis)

        # 组合整体信号
        combined_list = [r['combined_signal'] for r in results]
        portfolio_signal = sum(combined_list) / len(combined_list) if combined_list else 0

        return {
            'stocks_analysis': results,
            'portfolio_combined_signal': round(portfolio_signal, 3),
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def format_analysis_report(self, analysis):
        """格式化分析报告"""
        lines = []
        lines.append('\n' + '=' * 60)
        lines.append('  股票量化分析报告')
        lines.append('=' * 60)

        stock_code = analysis.get('stock_code', '')
        stock_name = analysis.get('stock_name', stock_code)

        # 实时行情
        quote = analysis.get('realtime_quote')
        if quote:
            change_pct = quote.get('change_pct', 0)
            sign = "+" if change_pct > 0 else ""
            lines.append(f"\n【{stock_name}({stock_code})】")
            lines.append(f"  现价: {quote.get('current', 0):.2f}")
            lines.append(f"  涨跌: {sign}{change_pct:.2f}%")
            lines.append(f"  最高: {quote.get('high', 0):.2f} | 最低: {quote.get('low', 0):.2f}")
        else:
            lines.append(f"\n【{stock_name}({stock_code})】")
            lines.append(f"  暂无实时数据")

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
            desc = str(comp.get('trend', comp.get('signal', comp.get('rsi', ''))))
            if isinstance(desc, float):
                desc = f"{desc:.2f}"
            lines.append(f"  {name}: {sign}{val:.2f} ({desc})")

        lines.append('\n' + '=' * 60)
        lines.append(f"分析时间: {analysis.get('analyzed_at', '')}")
        lines.append('=' * 60 + '\n')
        return '\n'.join(lines)


def main():
    """测试"""
    analyzer = StockQuantAnalyzer()
    print("股票量化分析器 v1.0")

    # 测试分析
    print("\n--- 测试: 分析 000858 (五粮液) ---")
    result = analyzer.analyze_stock('000858', sector='消费')
    print(analyzer.format_analysis_report(result))


if __name__ == '__main__':
    main()