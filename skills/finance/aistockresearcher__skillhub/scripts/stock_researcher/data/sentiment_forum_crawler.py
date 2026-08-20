#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富股吧、雪球股吧情绪爬虫
EastMoney Forum & Xueqiu (Snowball) Sentiment Crawler

数据来源：
1. 东方财富股吧：https://guba.eastmoney.com/list,code_讨论.html
2. 雪球股票讨论：https://xueqiu.com/S/{code}

功能：
- 爬取东方财富股吧帖子和评论
- 爬取雪球股票讨论
- 情感分析（正面/负面/中性）
- 情绪指标计算
"""

import json
import time
import ssl
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 尝试导入crawl_utils
try:
    from crawl_utils import safe_request, detect_encoding
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


class SentimentForumCrawler:
    """
    股吧/雪球情绪爬虫

    功能：
    1. 东方财富股吧帖子爬取
    2. 雪球股票讨论爬取
    3. 多维度情感分析
    4. 情绪指标计算
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 情感关键词
        self.positive_keywords = [
            "涨停", "大涨", "暴涨", "净流入", "业绩预增", "政策利好",
            "回购", "增持", "上调评级", "突破", "创新高", "国产替代",
            "中标", "订单", "合作", "扩张", "超预期", "大幅增长",
            "行业龙头", "技术突破", "产能扩张", "低估", "价值投资",
            "抄底", "加仓", "看好", "必涨", "牛", "赚", "盈利"
        ]

        self.negative_keywords = [
            "跌停", "大跌", "暴跌", "净流出", "业绩下滑", "被调查",
            "被处罚", "减持", "下调评级", "产能过剩", "黑天鹅",
            "诉讼", "亏损", "债务危机", "流动性紧张", "商誉减值",
            "业绩变脸", "大幅减少", "库存积压", "竞争加剧", "政策利空",
            "雷", "崩盘", "割肉", "清仓", "跑", "亏", "死", "凉"
        ]

        self.strong_positive = ["涨停", "大涨", "业绩预增", "回购", "增持", "突破"]
        self.strong_negative = ["跌停", "大跌", "被调查", "被处罚", "债务危机"]

    def fetch_eastmoney_guba(self, code: str, pages: int = 5) -> List[Dict]:
        """
        爬取东方财富股吧帖子

        Args:
            code: 股票代码
            pages: 爬取页数

        Returns:
            List[Dict]: 帖子列表
        """
        posts = []

        # 东方财富股吧API
        api_url = "https://guba.eastmoney.com/list"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://guba.eastmoney.com/"
        }

        for page in range(1, pages + 1):
            url = f"{api_url}/{code},2_{page}.html"

            try:
                if HAS_CRAWL_UTILS:
                    raw = safe_request(url, headers=headers, timeout=10)
                else:
                    req = urllib.request.Request(url, headers=headers)
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                        raw = resp.read()

                if not raw:
                    continue

                if isinstance(raw, bytes):
                    text = raw.decode("utf-8", errors="replace")
                else:
                    text = raw

                # 解析帖子列表
                # 东方财富股吧使用动态加载，这里尝试解析JSON数据
                items = re.findall(
                    r'<div class="listitem.*?".*?data-link="(.*?)".*?<span class="l1">(.*?)</span>.*?<span class="l2">(.*?)</span>.*?<span class="l3">(.*?)</span>',
                    text, re.DOTALL
                )

                for item in items:
                    link, title, author, reply_count = item
                    post = {
                        "code": code,
                        "platform": "eastmoney_guba",
                        "title": title.strip(),
                        "author": author.strip(),
                        "reply_count": int(reply_count) if reply_count.isdigit() else 0,
                        "sentiment_score": self._calc_sentiment(title),
                        "type": self._classify_post(title)
                    }
                    posts.append(post)

                # 备用解析：从JS变量中提取
                if not posts:
                    js_data = re.findall(r'var cmsList=(\{.*?\});', text, re.DOTALL)
                    if js_data:
                        try:
                            data = json.loads(js_data[0])
                            for item in data.get("cmsList", []):
                                posts.append({
                                    "code": code,
                                    "platform": "eastmoney_guba",
                                    "title": item.get("title", ""),
                                    "author": item.get("author", ""),
                                    "reply_count": item.get("replycount", 0),
                                    "sentiment_score": self._calc_sentiment(item.get("title", "")),
                                    "type": self._classify_post(item.get("title", ""))
                                })
                        except Exception:
                            pass

                time.sleep(0.5)

            except Exception as e:
                print(f"[东方财富股吧] 第{page}页出错: {e}")
                continue

        return posts

    def fetch_xueqiu_stock(self, code: str, pages: int = 5) -> List[Dict]:
        """
        爬取雪球股票讨论

        Args:
            code: 股票代码
            pages: 爬取页数

        Returns:
            List[Dict]: 讨论列表
        """
        discussions = []

        # 雪球股票讨论API（需要cookie）
        api_url = f"https://xueqiu.com/S/{code}"
        search_url = f"https://xueqiu.com/query/v1/search/status.json?q={code}&type=status"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://xueqiu.com/",
            "Accept": "application/json",
            "Cookie": "xq_a_token=placeholder"  # 雪球需要登录cookie，这里做占位
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(search_url, headers=headers, timeout=10)
            else:
                req = urllib.request.Request(search_url, headers=headers)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    raw = resp.read()

            if not raw:
                return []

            if isinstance(raw, bytes):
                text = raw.decode("utf-8", errors="replace")
            else:
                text = raw

            data = json.loads(text)
            items = data.get("list", [])

            for item in items:
                content = item.get("text", "")
                created_at = item.get("created_at", 0)

                discussion = {
                    "code": code,
                    "platform": "xueqiu",
                    "title": content[:100] if content else "",
                    "author": item.get("user", {}).get("screen_name", ""),
                    "reply_count": item.get("reply_count", 0),
                    "like_count": item.get("like_count", 0),
                    "created_at": datetime.fromtimestamp(created_at / 1000).isoformat() if created_at else "",
                    "sentiment_score": self._calc_sentiment(content),
                    "type": self._classify_post(content)
                }
                discussions.append(discussion)

        except Exception as e:
            print(f"[雪球] 爬取出错: {e}")

        return discussions

    def _calc_sentiment(self, text: str) -> float:
        """计算文本情感分数"""
        if not text:
            return 0

        score = 0

        # 强信号词（权重2）
        for kw in self.strong_positive:
            if kw in text:
                score += 2
        for kw in self.strong_negative:
            if kw in text:
                score -= 2

        # 普通关键词（权重1）
        for kw in self.positive_keywords:
            if kw in text:
                score += 1
        for kw in self.negative_keywords:
            if kw in text:
                score -= 1

        # 归一化到 -3 ~ +3
        return max(-3, min(3, score))

    def _classify_post(self, text: str) -> str:
        """分类帖子类型"""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["讨论", "问问", "求助", "不懂"]):
            return "讨论"
        elif any(kw in text_lower for kw in ["分享", "记录", "持仓"]):
            return "分享"
        elif any(kw in text_lower for kw in ["分析", "观点", "看法"]):
            return "分析"
        elif any(kw in text_lower for kw in ["资讯", "新闻", "公告"]):
            return "资讯"
        else:
            return "其他"

    def analyze_sentiment(self, posts: List[Dict]) -> Dict:
        """
        分析帖子情感

        Args:
            posts: 帖子列表

        Returns:
            Dict: 情感分析结果
        """
        if not posts:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "bullish_ratio": 50,
                "sentiment_score": 0,
                "sentiment_label": "中性",
                "dominant_type": "其他"
            }

        positive = 0
        negative = 0
        neutral = 0
        scores = []
        types = []

        for post in posts:
            score = post.get("sentiment_score", 0)
            scores.append(score)
            types.append(post.get("type", "其他"))

            if score >= 1:
                positive += 1
            elif score <= -1:
                negative += 1
            else:
                neutral += 1

        total = len(posts)
        bullish_ratio = (positive / total * 100) if total > 0 else 50
        avg_score = sum(scores) / total if total > 0 else 0

        # 情绪标签
        if bullish_ratio >= 70:
            label = "极度乐观"
        elif bullish_ratio >= 60:
            label = "乐观"
        elif bullish_ratio >= 40:
            label = "中性"
        elif bullish_ratio >= 30:
            label = "悲观"
        else:
            label = "极度悲观"

        # 主要帖子类型
        type_counter = Counter(types)
        dominant_type = type_counter.most_common(1)[0][0] if type_counter else "其他"

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "bullish_ratio": round(bullish_ratio, 1),
            "sentiment_score": round(avg_score, 2),
            "sentiment_label": label,
            "dominant_type": dominant_type,
            "type_distribution": dict(type_counter)
        }

    def analyze_stock_sentiment(self, code: str, days: int = 7) -> Dict:
        """
        综合分析股票情绪（东方财富+雪球）

        Args:
            code: 股票代码
            days: 分析天数

        Returns:
            Dict: 综合情绪分析结果
        """
        # 爬取东方财富股吧
        guba_posts = self.fetch_eastmoney_guba(code, pages=3)

        # 爬取雪球
        xueqiu_posts = self.fetch_xueqiu_stock(code, pages=3)

        # 合并分析
        all_posts = guba_posts + xueqiu_posts

        # 按时间过滤
        cutoff = datetime.now() - timedelta(days=days)
        recent_posts = []
        for post in all_posts:
            created = post.get("created_at", "")
            if not created:
                recent_posts.append(post)
                continue
            try:
                post_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if post_time >= cutoff:
                    recent_posts.append(post)
            except Exception:
                recent_posts.append(post)

        # 分别分析
        guba_sentiment = self.analyze_sentiment(guba_posts)
        xueqiu_sentiment = self.analyze_sentiment(xueqiu_posts)
        overall_sentiment = self.analyze_sentiment(recent_posts)

        # 综合评分（东方财富60% + 雪球40%）
        guba_weight = 0.6
        xueqiu_weight = 0.4

        combined_score = (
            guba_sentiment["sentiment_score"] * guba_weight +
            xueqiu_sentiment["sentiment_score"] * xueqiu_weight
        )

        combined_bullish = (
            guba_sentiment["bullish_ratio"] * guba_weight +
            xueqiu_sentiment["bullish_ratio"] * xueqiu_weight
        )

        # 综合标签
        if combined_bullish >= 65:
            label = "偏多"
        elif combined_bullish >= 55:
            label = "略偏多"
        elif combined_bullish >= 45:
            label = "中性"
        elif combined_bullish >= 35:
            label = "略偏空"
        else:
            label = "偏空"

        return {
            "code": code,
            "update_time": datetime.now().isoformat(),
            "guba": {
                "platform": "东方财富股吧",
                "post_count": len(guba_posts),
                "sentiment": guba_sentiment
            },
            "xueqiu": {
                "platform": "雪球",
                "post_count": len(xueqiu_posts),
                "sentiment": xueqiu_sentiment
            },
            "combined": {
                "total_posts": len(recent_posts),
                "bullish_ratio": round(combined_bullish, 1),
                "sentiment_score": round(combined_score, 2),
                "sentiment_label": label
            },
            "key_topics": self._extract_key_topics(recent_posts)
        }

    def _extract_key_topics(self, posts: List[Dict]) -> List[str]:
        """提取热门话题"""
        if not posts:
            return []

        # 简单统计标题中的高频词
        all_text = " ".join(p.get("title", "") for p in posts)

        # 统计关键词出现次数
        keyword_counts = {
            "涨停": all_text.count("涨停"),
            "业绩": all_text.count("业绩"),
            "增持": all_text.count("增持"),
            "减持": all_text.count("减持"),
            "回购": all_text.count("回购"),
            "政策": all_text.count("政策"),
            "科技": all_text.count("科技"),
            "消费": all_text.count("消费"),
            "医药": all_text.count("医药"),
            "新能源": all_text.count("新能源"),
        }

        # 返回前5个热门话题
        sorted_topics = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{topic}({count}次)" for topic, count in sorted_topics[:5] if count > 0]

    def get_recent_sentiment_trend(self, code: str, days: int = 30) -> List[Dict]:
        """
        获取近期情绪趋势（需要历史数据）

        Returns:
            List[Dict]: 每日情绪数据
        """
        # 从文件加载历史数据
        history_file = self.data_dir / f"sentiment_history_{code}.json"

        if not history_file.exists():
            return []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            cutoff = datetime.now() - timedelta(days=days)
            recent = [
                h for h in history
                if datetime.fromisoformat(h["date"]) >= cutoff
            ]

            return recent
        except Exception:
            return []

    def save_sentiment_history(self, code: str, sentiment_data: Dict):
        """保存情绪历史"""
        history_file = self.data_dir / f"sentiment_history_{code}.json"

        history = []
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass

        # 添加新记录
        record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "bullish_ratio": sentiment_data["combined"]["bullish_ratio"],
            "sentiment_score": sentiment_data["combined"]["sentiment_score"],
            "sentiment_label": sentiment_data["combined"]["sentiment_label"],
            "post_count": sentiment_data["combined"]["total_posts"]
        }

        history.append(record)

        # 保留30天
        cutoff = datetime.now() - timedelta(days=30)
        history = [
            h for h in history
            if datetime.fromisoformat(h["date"]) >= cutoff
        ]

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


class SentimentAlert:
    """
    情绪告警系统

    功能：
    1. 检测极度悲观/乐观情绪
    2. 情绪突变预警
    3. 生成操作建议
    """

    def __init__(self, crawler: SentimentForumCrawler = None):
        self.crawler = crawler or SentimentForumCrawler()

    def check_alerts(self, code: str) -> List[Dict]:
        """
        检查是否触发告警

        Returns:
            List[Dict]: 告警列表
        """
        sentiment = self.crawler.analyze_stock_sentiment(code)
        alerts = []

        bullish_ratio = sentiment["combined"]["bullish_ratio"]
        score = sentiment["combined"]["sentiment_score"]

        # 极度乐观告警
        if bullish_ratio >= 85:
            alerts.append({
                "type": "EXTREME_BULLISH",
                "level": "warning",
                "message": f"股吧情绪极度乐观({bullish_ratio:.0f}%)，警惕短期回调风险",
                "suggestion": "注意分批减仓，锁定利润"
            })

        # 极度悲观告警
        if bullish_ratio <= 15:
            alerts.append({
                "type": "EXTREME_BEARISH",
                "level": "warning",
                "message": f"股吧情绪极度悲观({bullish_ratio:.0f}%)，可能存在超跌机会",
                "suggestion": "可关注超跌优质股，但需谨慎加仓"
            })

        # 情绪突变预警
        history = self.crawler.get_recent_sentiment_trend(code, days=7)
        if len(history) >= 2:
            recent = history[-1]
            prev = history[-2]
            change = recent["bullish_ratio"] - prev["bullish_ratio"]

            if change >= 20:
                alerts.append({
                    "type": "SENTIMENT_SPIKE",
                    "level": "info",
                    "message": f"情绪大幅转暖(+{change:.0f}%)，市场关注度提升",
                    "suggestion": "可适当关注，但勿追高"
                })
            elif change <= -20:
                alerts.append({
                    "type": "SENTIMENT_DROP",
                    "level": "warning",
                    "message": f"情绪大幅下降({change:.0f}%)，市场信心不足",
                    "suggestion": "建议观望，控制仓位"
                })

        return alerts

    def get_trading_suggestion(self, sentiment_data: Dict, tech_signal: str = "neutral") -> str:
        """
        综合情绪和技术信号生成操作建议

        Args:
            sentiment_data: 情绪数据
            tech_signal: 技术信号（看多/中性/看空）

        Returns:
            str: 操作建议
        """
        bullish = sentiment_data["combined"]["bullish_ratio"]
        score = sentiment_data["combined"]["sentiment_score"]

        suggestions = []

        # 情绪维度
        if bullish >= 70:
            suggestions.append("情绪面偏多，但需警惕")
        elif bullish <= 30:
            suggestions.append("情绪面偏冷，可能是机会")

        # 技术维度
        if tech_signal == "看多":
            suggestions.append("技术面支持上涨")
        elif tech_signal == "看空":
            suggestions.append("技术面偏空，注意风险")

        # 综合建议
        if bullish >= 70 and tech_signal == "看多":
            return "做多情绪+技术看多共振，可以考虑顺势操作，但需控制仓位"
        elif bullish >= 70 and tech_signal == "看空":
            return "情绪过热但技术背离，谨慎追高，建议观望"
        elif bullish <= 30 and tech_signal == "看空":
            return "情绪+技术双杀，不建议抄底，等待企稳信号"
        elif bullish <= 30 and tech_signal == "看多":
            return "技术面企稳但情绪低迷，可能存在价值机会，可小仓位试探"
        else:
            return "情绪面中性，等待更多信号"


def main():
    """测试"""
    print("=" * 60)
    print("  股吧/雪球情绪爬虫 - 测试")
    print("=" * 60)

    crawler = SentimentForumCrawler()

    # 测试代码
    test_code = "600519"  # 贵州茅台

    print(f"\n1. 分析 {test_code} 情绪...")

    # 只爬取东方财富股吧（雪球需要登录）
    guba_posts = crawler.fetch_eastmoney_guba(test_code, pages=2)
    print(f"   东方财富股吧帖子: {len(guba_posts)}条")

    # 情感分析
    sentiment = crawler.analyze_sentiment(guba_posts)
    print(f"   情感分析:")
    print(f"   - 总帖子: {sentiment['total']}")
    print(f"   - 偏多: {sentiment['positive']} 偏空: {sentiment['negative']} 中性: {sentiment['neutral']}")
    print(f"   - 多头比例: {sentiment['bullish_ratio']:.1f}%")
    print(f"   - 情绪标签: {sentiment['sentiment_label']}")

    # 告警测试
    print(f"\n2. 告警测试...")
    # 模拟情绪数据
    mock_sentiment = {
        "combined": {
            "bullish_ratio": 75,
            "sentiment_score": 1.5,
            "sentiment_label": "偏多"
        }
    }
    alert = SentimentAlert(crawler)
    suggestion = alert.get_trading_suggestion(mock_sentiment, "中性")
    print(f"   建议: {suggestion}")


if __name__ == "__main__":
    main()