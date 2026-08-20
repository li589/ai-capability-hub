#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数分析
Index Analysis
上证指数、沪深300、创业板指、科创50
"""

import re
import ssl
import urllib.request
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..data.market import MarketData
from ..core.technical import TechnicalAnalyzer


@dataclass
class IndexResult:
    """指数分析结果"""
    code: str = ""
    name: str = ""
    price: float = 0
    change_pct: float = 0

    # 均线
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    ma60: float = 0

    # 技术指标
    rsi: float = 50
    macd_hist: float = 0
    adx: float = 0

    # 均线多空
    ma_status: str = "混乱"  # 多头排列/空头排列/混乱

    # 情绪
    market_sentiment: str = "中性"  # 积极/中性/谨慎

    # 综合评分
    score: float = 0
    signal: str = "中性"

    # v9.0 深度指数增量字段（默认空，向后兼容；由体制/结构/波动/估值分析器填充）
    regime: str = ""              # 牛市/熊市/震荡
    vol_regime: str = ""          # 低波动/扩张/高波动/压缩
    trend_structure: str = ""     # 上升/下降/震荡
    valuation_percentile: Optional[float] = None  # PE 历史分位 0-100

    def get(self, key, default=None):
        """兼容dict.get()的接口"""
        return getattr(self, key, default)

    def to_dict(self):
        return {k: getattr(self, k) for k in dir(self) if not k.startswith('_')}


class IndexAnalyzer:
    """
    指数分析器

    分析四大指数：
    - 上证指数: sh000001
    - 沪深300: sh000300
    - 创业板指: sz399006
    - 科创50: sh000688
    """

    INDEX_CODES = {
        "sh000001": "上证指数",
        "sh000300": "沪深300",
        "sz399006": "创业板指",
        "sh000688": "科创50"
    }

    def __init__(self):
        self.market = MarketData()
        self.tech_analyzer = TechnicalAnalyzer()

    def analyze_index(self, index_code: str) -> IndexResult:
        """
        分析单个指数

        Args:
            index_code: 指数代码，如 "sh000001"

        Returns:
            IndexResult
        """
        prefix = "sh" if index_code.startswith("sh") else "sz"
        stripped_code = index_code.replace("sh", "").replace("sz", "")

        # 直接请求腾讯行情 —— 用正确的前缀构造，避免 fetch_realtime 的前缀逻辑错误
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ts_code = f"{prefix}{stripped_code}"
        url = f"https://qt.gtimg.cn/q={ts_code}&_={int(time.time()*1000)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
        try:
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                raw = resp.read()
            text = raw.decode("gbk", errors="replace")
        except Exception as e:
            return IndexResult(code=index_code, name=self.INDEX_CODES.get(index_code, index_code))

        # 解析行情
        m = re.search(rf'v_{ts_code}="(.+?)"', text)
        if not m:
            return IndexResult(code=index_code, name=self.INDEX_CODES.get(index_code, index_code))

        fields = m.group(1).split("~")
        data = {
            "name": fields[1] if len(fields) > 1 else "",
            "price": float(fields[3]) if len(fields) > 3 and fields[3].replace(".", "").isdigit() else 0,
            "change_pct": float(fields[32]) if len(fields) > 32 and fields[32].replace(".", "-").replace("-", "").isdigit() else 0
        }

        name = self.INDEX_CODES.get(index_code, stripped_code)

        # 获取历史数据用于技术分析
        kline = self.market.fetch_history(stripped_code, days=120, prefix=prefix)
        closes = kline.get("closes", []) if kline else []

        # 计算技术指标
        tech = None
        if len(closes) >= 20:
            try:
                tech = self.tech_analyzer.analyze(stripped_code, closes)
            except Exception:
                pass

        # 构建结果
        result = IndexResult(
            code=index_code,
            name=name,
            price=data.get("price", 0),
            change_pct=data.get("change_pct", 0)
        )

        if tech:
            result.ma5 = tech.ma5
            result.ma10 = tech.ma10
            result.ma20 = tech.ma20
            result.ma60 = tech.ma60
            result.rsi = tech.rsi14
            result.macd_hist = tech.macd_hist
            result.adx = tech.adx
            result.ma_status = tech.ma_arrangement
            result.score = tech.tech_score
            result.signal = tech.tech_signal

            # 市场情绪判断
            result.market_sentiment = self._judge_sentiment(result)

        return result


    def _judge_sentiment(self, result: IndexResult) -> str:
        """判断市场情绪"""
        positive = 0
        negative = 0

        # 涨跌
        if result.change_pct > 1:
            positive += 1
        elif result.change_pct < -1:
            negative += 1

        # RSI
        if result.rsi < 40:
            positive += 1
        elif result.rsi > 70:
            negative += 1

        # 均线
        if result.ma_status == "多头排列":
            positive += 2
        elif result.ma_status == "空头排列":
            negative += 2

        # MACD
        if result.macd_hist > 0:
            positive += 1
        else:
            negative += 1

        if positive > negative + 2:
            return "积极"
        elif negative > positive + 2:
            return "谨慎"
        else:
            return "中性"

    def analyze_all(self) -> List[IndexResult]:
        """
        分析所有指数

        Returns:
            List[IndexResult]
        """
        results = []
        for code in self.INDEX_CODES.keys():
            result = self.analyze_index(code)
            results.append(result)
            time.sleep(0.3)
        return results

    def get_market_summary(self) -> Dict:
        """
        获取市场整体摘要

        Returns:
            Dict: 市场摘要
        """
        results = self.analyze_all()

        # 统计
        up_count = sum(1 for r in results if r.change_pct > 0)
        down_count = len(results) - up_count

        # 加权评分
        avg_score = sum(r.score for r in results) / len(results) if results else 0

        # 整体情绪
        sentiments = [r.market_sentiment for r in results]
        positive_count = sentiments.count("积极")
        negative_count = sentiments.count("谨慎")

        if positive_count >= 3:
            overall = "积极"
        elif negative_count >= 3:
            overall = "谨慎"
        else:
            overall = "中性"

        return {
            "date": time.strftime("%Y-%m-%d"),
            "indexes": [
                {
                    "code": r.code,
                    "name": r.name,
                    "price": r.price,
                    "change_pct": r.change_pct,
                    "ma_status": r.ma_status,
                    "rsi": r.rsi,
                    "signal": r.signal,
                    "sentiment": r.market_sentiment
                }
                for r in results
            ],
            "summary": {
                "up_count": up_count,
                "down_count": down_count,
                "avg_score": round(avg_score, 1),
                "overall_sentiment": overall
            }
        }

    def print_analysis(self, results: List[IndexResult] = None):
        """打印指数分析结果"""
        if results is None:
            results = self.analyze_all()

        print(f"\n{'='*70}")
        print(f"  指数分析报告  {time.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")
        print(f"{'指数':<12} {'价格':>10} {'涨跌幅':>8} {'MA状态':<10} {'RSI':>6} {'信号':<6} {'情绪'}")
        print(f"{'-'*70}")

        for r in results:
            arrow = "▲" if r.change_pct > 0 else "▼" if r.change_pct < 0 else "-"
            print(f"{r.name:<12} {r.price:>10.2f} {arrow}{abs(r.change_pct):>6.2f}% {r.ma_status:<10} {r.rsi:>6.1f} {r.signal:<6} {r.market_sentiment}")

        print(f"{'='*70}")

        # 市场情绪
        sentiments = [r.market_sentiment for r in results]
        pos = sentiments.count("积极")
        neg = sentiments.count("谨慎")

        if pos >= 3:
            print(f"市场情绪: 积极 ({pos}个指数看多)")
        elif neg >= 3:
            print(f"市场情绪: 谨慎 ({neg}个指数看空)")
        else:
            print(f"市场情绪: 中性")


# 便捷函数
def analyze_index(index_code: str) -> IndexResult:
    """分析单个指数"""
    analyzer = IndexAnalyzer()
    return analyzer.analyze_index(index_code)


def analyze_all_indexes() -> List[IndexResult]:
    """分析所有指数"""
    analyzer = IndexAnalyzer()
    return analyzer.analyze_all()


def get_market_summary() -> Dict:
    """获取市场摘要"""
    analyzer = IndexAnalyzer()
    return analyzer.get_market_summary()