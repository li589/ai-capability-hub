"""
财经新闻汇总与组合调整提示 v1.0
基于财经新闻情感分析和基金量化信号，提示客户是否需要调仓
"""
from __future__ import annotations
import json, os, random
from datetime import datetime
from pathlib import Path

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


class NewsAdvisor:
    """财经新闻汇总与调仓提示"""

    # 调仓信号阈值
    STRONG_BUY_SIGNAL = 0.6   # 新闻整体偏多超过此值，建议加仓
    STRONG_SELL_SIGNAL = -0.6  # 新闻整体偏空超过此值，建议减仓
    NEUTRAL_BAND = (-0.2, 0.2)  # 中性区间，建议持有不调仓

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self._load_news()

    def _load_news(self):
        """加载最新新闻（v6.0: 文件缺失时自动调 multi_source 实时聚合）"""
        self.news = []
        news_path = self.data_dir / "news_latest.json"
        if news_path.exists():
            try:
                self.news = json.loads(news_path.read_text(encoding="utf-8"))
            except Exception:
                self.news = []
        # v6.0: 文件缺失或空时，自动从 multi_source 实时抓取（财联社/华尔街见闻/东财）
        if not self.news:
            try:
                import sys as _sys
                from pathlib import Path as _Path
                _scripts = _Path(__file__).resolve().parents[1]
                if str(_scripts) not in _sys.path:
                    _sys.path.insert(0, str(_scripts))
                _sys.path.insert(0, str(_scripts / "data_collection"))
                from multi_source import get_provider
                result = get_provider().get_news(limit=30)
                raw_news = result.get("news", [])
                # 归一化为 news_advisor 期望的结构（含 sentiment/category）
                self.news = [self._normalize_multi_source_news(n) for n in raw_news]
            except Exception:
                pass

    @staticmethod
    def _normalize_multi_source_news(n: dict) -> dict:
        """将 multi_source 新闻归一化为 news_advisor 结构"""
        title = n.get("title", "")
        # 简单关键词情感
        pos_kw = ["利好", "增长", "突破", "上涨", "超预期", "回购", "增持"]
        neg_kw = ["利空", "下滑", "下跌", "亏损", "处罚", "减持", "风险"]
        sent = 0
        for kw in pos_kw:
            if kw in title:
                sent += 25
        for kw in neg_kw:
            if kw in title:
                sent -= 25
        return {
            "title": title,
            "url": n.get("url", ""),
            "source": n.get("source", ""),
            "time": n.get("time", ""),
            "sentiment": max(-100, min(100, sent)),
            "category": [],  # multi_source 不做分类
        }

    def crawl_news(self):
        """抓取最新新闻"""
        try:
            # 先尝试直接导入（在同一包内）
            from data_collection.news_collector import crawl_all_news
            self.news = crawl_all_news()
            return len(self.news)
        except ImportError:
            try:
                # 再尝试向上查找
                import sys
                from pathlib import Path
                dc_path = Path(__file__).parent.parent / "data_collection"
                sys.path.insert(0, str(dc_path))
                from news_collector import crawl_all_news
                self.news = crawl_all_news()
                return len(self.news)
            except Exception:
                return 0

    def get_news_summary(self, limit=20):
        """获取新闻汇总"""
        if not self.news:
            return {"total": 0, "summary": "暂无新闻数据"}

        total = len(self.news)
        positive = sum(1 for n in self.news if n.get("sentiment", 0) > 20)
        negative = sum(1 for n in self.news if n.get("sentiment", 0) < -20)
        neutral = total - positive - negative

        # 按类别统计
        cat_counts = {}
        for n in self.news:
            for cat in n.get("category", []):
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

        # 计算综合情绪
        scores = [n.get("sentiment", 0) for n in self.news]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "category_counts": dict(sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)),
            "avg_sentiment": round(avg_score, 1),
            "overall": self._sentiment_label(avg_score),
        }

    def _sentiment_label(self, score):
        if score > 30:
            return "偏利好"
        elif score < -30:
            return "偏利空"
        return "中性"

    def get_portfolio_adjustment_signal(self, holdings_news_scores=None):
        """
        基于新闻情绪生成调仓信号

        参数:
            holdings_news_scores: 各持仓基金相关的新闻情绪得分列表
                                   如不提供，则使用整体新闻情绪

        返回:
            dict: 调仓信号和建议
        """
        summary = self.get_news_summary()
        if summary.get("total", 0) == 0:
            return {
                "signal": "未知",
                "action": "持有",
                "reason": "暂无新闻数据，无法判断",
                "news_summary": summary
            }

        # 计算综合情绪
        scores = [n.get("sentiment", 0) for n in self.news]
        avg_score = sum(scores) / len(scores) if scores else 0

        # 如果提供了持仓相关新闻，使用持仓相关新闻
        if holdings_news_scores:
            all_scores = scores + holdings_news_scores
            avg_score = sum(all_scores) / len(all_scores)

        # 生成信号
        if avg_score > self.STRONG_BUY_SIGNAL * 100:
            signal = "强烈买入"
            action = "加仓"
            reason = "财经情绪整体偏多，市场信心充足，可适度加仓"
        elif avg_score < self.STRONG_SELL_SIGNAL * 100:
            signal = "强烈卖出"
            action = "减仓"
            reason = "财经情绪整体偏空，风险偏好下降，建议减仓控制风险"
        elif avg_score > 20:
            signal = "温和买入"
            action = "持有/适度加仓"
            reason = "情绪略偏多，可以保持现有仓位，适度加仓"
        elif avg_score < -20:
            signal = "温和卖出"
            action = "持有/适度减仓"
            reason = "情绪略偏空，保持谨慎，不建议加仓"
        else:
            signal = "中性"
            action = "持有"
            reason = "情绪相对平衡，建议保持现有配置，不盲目调仓"

        return {
            "signal": signal,
            "action": action,
            "reason": reason,
            "avg_sentiment": round(avg_score, 1),
            "news_summary": summary
        }

    def format_news_report(self, limit=15):
        """格式化新闻报告"""
        if not self.news:
            return "暂无新闻数据，请先抓取新闻。"

        summary = self.get_news_summary(limit)
        signal_data = self.get_portfolio_adjustment_signal()

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  财经新闻汇总报告')
        lines.append('=' * 70)
        lines.append(f"\n【新闻概况】")
        lines.append(f"  总数: {summary['total']}条")
        lines.append(f"  利好: {summary['positive']}条 | 利空: {summary['negative']}条 | 中性: {summary['neutral']}条")
        lines.append(f"  综合情绪: {summary['overall']} ({signal_data['avg_sentiment']:+.1f})")

        lines.append(f"\n【类别分布】")
        for cat, cnt in list(summary.get('category_counts', {}).items())[:5]:
            lines.append(f"  {cat}: {cnt}条")

        lines.append(f"\n【调仓信号】")
        lines.append(f"  信号: {signal_data['signal']}")
        lines.append(f"  建议操作: {signal_data['action']}")
        lines.append(f"  理由: {signal_data['reason']}")

        lines.append(f"\n【最新新闻】")
        lines.append('-' * 70)
        for n in self.news[:limit]:
            sent = n.get('sentiment', 0)
            sign = "+" if sent > 0 else "" if sent < 0 else ""
            cats = "/".join(n.get('category', [])[:2])
            lines.append(f"[{n.get('source','')}][{cats}][{sign}{sent}] {n.get('title','')[:45]}")

        lines.append('\n' + '=' * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append('=' * 70 + '\n')
        return '\n'.join(lines)


def main():
    """测试"""
    advisor = NewsAdvisor()

    # 抓取新闻
    print("抓取财经新闻...")
    count = advisor.crawl_news()
    print(f"抓取到 {count} 条新闻")

    # 生成报告
    print(advisor.format_news_report())


if __name__ == '__main__':
    main()