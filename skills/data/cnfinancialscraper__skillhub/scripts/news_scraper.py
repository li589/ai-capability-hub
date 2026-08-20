# -*- coding: utf-8 -*-
"""
金融新闻爬虫模块
支持爬取股票/基金相关新闻资讯
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from scrapling.fetchers import StealthyFetcher
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
NEWS_CACHE_DIR = SKILL_DATA_DIR / "news_cache"


@dataclass
class NewsArticle:
    """新闻文章"""
    title: str
    url: str
    publish_time: str
    source: str  # 来源媒体
    summary: str = ""
    content: str = ""
    stock_codes: List[str] = None  # 相关股票代码
    sentiment: str = ""  # 情感标签 (positive, negative, neutral)
    keywords: List[str] = None
    is_downloaded: bool = False


class EastMoneyNewsAPI:
    """东方财富新闻API"""

    def __init__(self):
        self.session = None
        if REQUESTS_AVAILABLE:
            try:
                from .http_utils import RatelimitedSession
            except ImportError:
                from http_utils import RatelimitedSession  # type: ignore
            self.session = RatelimitedSession(requests.Session())
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.eastmoney.com'
            })

    def get_stock_news(self, stock_code: str, page: int = 1, page_size: int = 20) -> List[NewsArticle]:
        """
        获取个股新闻

        Args:
            stock_code: 股票代码
            page: 页码
            page_size: 每页数量

        Returns:
            新闻列表
        """
        if not self.session:
            return []

        try:
            code = stock_code.replace('.SH', '').replace('.SZ', '')
            # 用东方财富公告API替代失效的新闻API
            # https://np-anotice-stock.eastmoney.com/api/security/ann 返回JSON格式的公告列表
            ann_url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            # 判断交易所
            if code.startswith('6') or code.startswith('9'):
                exchange = 'SH'
            else:
                exchange = 'SZ'
            params = {
                "sr": -1,
                "page_size": page_size,
                "page_index": page,
                "ann_type": "SHA,SZA,SZ",
                "client_source": "web",
                "stock_list": f"{code}",
            }
            if exchange == 'SH':
                params["ann_type"] = "SHA,SZ"
            elif exchange == 'SZ':
                params["ann_type"] = "SZA,SZ"

            resp = self.session.get(ann_url, params=params, timeout=30)
            data = resp.json()

            news_list = []
            if data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    article = self._parse_announcement_item(item)
                    if article:
                        news_list.append(article)

            return news_list

        except Exception as e:
            print(f"[错误] 获取个股新闻失败: {e}")
            return []

    def get_market_news(self, page: int = 1, page_size: int = 30) -> List[NewsArticle]:
        """
        获取市场新闻

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            新闻列表
        """
        if not self.session:
            return []

        try:
            url = "https://np-listapi.eastmoney.com/comm/web/getGeneralNews"
            params = {
                "client": "web",
                "page": page,
                "pageSize": page_size,
                "category": "category_stock",
                "endDate": int(time.time() * 1000),
                "startDate": int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            news_list = []
            if data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    article = self._parse_news_item(item)
                    if article:
                        news_list.append(article)

            return news_list

        except Exception as e:
            print(f"[错误] 获取市场新闻失败: {e}")
            return []

    def get_industry_news(self, industry: str, page: int = 1) -> List[NewsArticle]:
        """
        获取行业新闻

        Args:
            industry: 行业名称
            page: 页码

        Returns:
            新闻列表
        """
        if not self.session:
            return []

        try:
            url = "https://search-api.eastmoney.com/search/jsonp"
            params = {
                "cb": "callback",
                "param": json.dumps({
                    "uid": "",
                    "keyword": industry,
                    "type": ["cmsArticle"],
                    "client": "web",
                    "param": {
                        "cmsArticle": {
                            "fields": ["title", "time", "url", "media"],
                            "pageSize": 20,
                            "pageIndex": page
                        }
                    }
                }, ensure_ascii=False)
            }

            resp = self.session.get(url, params=params, timeout=30)
            text = resp.text

            # 解析JSONP
            json_match = re.search(r'callback\((.*)\)', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                news_list = []
                if data.get('result') and data['result'].get('cmsArticle'):
                    for item in data['result']['cmsArticle']:
                        article = self._parse_news_item(item)
                        if article:
                            news_list.append(article)
                return news_list

        except Exception as e:
            print(f"[错误] 获取行业新闻失败: {e}")

        return []

    def search_news(self, keyword: str, page: int = 1, page_size: int = 20) -> List[NewsArticle]:
        """
        搜索新闻

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            新闻列表
        """
        if not self.session:
            return []

        try:
            url = "https://search-api.eastmoney.com/search/jsonp"
            params = {
                "keyword": keyword,
                "type": ["cmsArticle"],
                "pageIndex": page,
                "pageSize": page_size
            }

            resp = self.session.get(url, params=params, timeout=30)
            text = resp.text

            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))

                news_list = []
                results = data.get('result', {})
                if isinstance(results, dict):
                    articles = results.get('cmsArticle', [])
                else:
                    articles = results

                for item in articles:
                    article = self._parse_news_item(item)
                    if article:
                        news_list.append(article)

                return news_list

        except Exception as e:
            print(f"[错误] 搜索新闻失败: {e}")

        return []

    def _parse_news_item(self, item: Dict) -> Optional[NewsArticle]:
        """解析新闻项"""
        try:
            title = item.get('title', '')
            if not title:
                return None

            # 发布时间
            publish_time = item.get('time', '') or item.get('showTime', '')
            if isinstance(publish_time, int):
                publish_time = datetime.fromtimestamp(publish_time / 1000).strftime('%Y-%m-%d %H:%M')

            # 来源
            source = item.get('media', '') or item.get('source', '')

            # 相关股票
            stock_codes = []
            if 'secuCodes' in item:
                stock_codes = item['secuCodes']
            elif 'relatedStocks' in item:
                stock_codes = item['relatedStocks'].split(',')

            # 关键词
            keywords = []
            if 'keywords' in item:
                keywords = item['keywords'].split(',') if isinstance(item['keywords'], str) else item['keywords']

            return NewsArticle(
                title=title,
                url=item.get('url', '') or item.get('artUrl', ''),
                publish_time=publish_time,
                source=source,
                summary=item.get('summary', '') or item.get('description', ''),
                stock_codes=stock_codes,
                keywords=keywords
            )

        except Exception:
            return None



    def _parse_announcement_item(self, item: Dict) -> Optional[NewsArticle]:
        """解析东方财富公告API返回的公告项（用于替代已失效的新闻API）"""
        try:
            title = item.get('title_ch', '') or item.get('title', '')
            if not title:
                return None

            # 公告时间
            publish_time = item.get('notice_date', '') or item.get('display_time', '')
            if not publish_time:
                publish_time = item.get('sort_date', '')

            # 来源（东方财富公告）
            source = "东方财富"

            # 相关股票
            stock_codes = []
            codes_list = item.get('codes', [])
            if codes_list:
                for code_info in codes_list:
                    if isinstance(code_info, dict) and 'stock_code' in code_info:
                        sc = code_info['stock_code']
                        if sc:
                            stock_codes.append(sc)
                    elif isinstance(code_info, str):
                        stock_codes.append(code_info)

            # 关键词（来自栏目名称）
            keywords = []
            columns = item.get('columns', [])
            if columns:
                for col in columns:
                    if isinstance(col, dict) and col.get('column_name'):
                        keywords.append(col['column_name'])
                    elif isinstance(col, str):
                        keywords.append(col)

            # 构造URL（东方财富公告详情页）
            art_code = item.get('art_code', '')
            url = f"https://np-anotice-stock.eastmoney.com/notice#announcement?art_code={art_code}" if art_code else ''

            return NewsArticle(
                title=title,
                url=url,
                publish_time=publish_time,
                source=source,
                summary="; ".join(keywords[:3]) if keywords else '',
                stock_codes=stock_codes,
                keywords=keywords
            )
        except Exception:
            return None

class NewsAggregator:
    """新闻聚合器 - 整合多源新闻"""

    def __init__(self):
        self.eastmoney = EastMoneyNewsAPI()
        self.session = None
        if REQUESTS_AVAILABLE:
            try:
                from .http_utils import RatelimitedSession
            except ImportError:
                from http_utils import RatelimitedSession  # type: ignore
            self.session = RatelimitedSession(requests.Session())

    def get_stock_news_all(self, stock_code: str, days: int = 30) -> List[Dict]:
        """
        获取个股全维度新闻

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            新闻列表
        """
        news_list = []

        # 东方财富新闻
        em_news = self.eastmoney.get_stock_news(stock_code, page_size=50)
        for article in em_news:
            news_list.append({
                "stock_code": stock_code,
                "title": article.title,
                "url": article.url,
                "publish_time": article.publish_time,
                "source": article.source,
                "summary": article.summary,
                "sentiment": self._analyze_sentiment(article.title + article.summary)
            })

        # 按时间排序
        news_list.sort(key=lambda x: x.get('publish_time', ''), reverse=True)

        return news_list

    def get_market_digest(self, date: str = None) -> str:
        """
        获取市场摘要

        Args:
            date: 日期 (默认今天)

        Returns:
            摘要文本
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        news = self.eastmoney.get_market_news(page=1, page_size=50)

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"【市场资讯摘要 {date}】")
        lines.append(f"{'='*60}")

        if not news:
            lines.append("\n暂无资讯")
            return "\n".join(lines)

        # 按来源分组
        by_source = {}
        for article in news:
            source = article.source or '未知'
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(article)

        # 输出各来源热门
        for source, articles in list(by_source.items())[:5]:
            lines.append(f"\n{source} ({len(articles)}条):")
            for article in articles[:3]:
                sentiment_icon = {"positive": "↑", "negative": "↓", "neutral": "→"}.get(article.sentiment, "")
                lines.append(f"  [{article.publish_time[:10]}] {sentiment_icon} {article.title[:40]}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)

    def get_stock_sentiment(self, stock_code: str) -> Dict[str, Any]:
        """
        分析个股舆情

        Args:
            stock_code: 股票代码

        Returns:
            舆情分析结果
        """
        news = self.get_stock_news_all(stock_code, days=7)

        if not news:
            return {"sentiment": "neutral", "summary": "暂无新闻"}

        # 统计情感
        sentiments = [n['sentiment'] for n in news]
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        neutral = sentiments.count('neutral')

        total = len(sentiments)
        sentiment_score = (positive - negative) / total if total > 0 else 0

        # 判断
        if sentiment_score > 0.2:
            sentiment = "positive"
            label = "偏正面"
        elif sentiment_score < -0.2:
            sentiment = "negative"
            label = "偏负面"
        else:
            sentiment = "neutral"
            label = "中性"

        return {
            "sentiment": sentiment,
            "label": label,
            "score": round(sentiment_score, 2),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "total_news": total,
            "latest_news": news[:3]
        }

    def _analyze_sentiment(self, text: str) -> str:
        """
        简单情感分析

        Args:
            text: 文本

        Returns:
            情感标签 (positive, negative, neutral)
        """
        text_lower = text.lower()

        positive_words = ['涨', '突破', '增长', '利好', '盈利', '增长', '创新高', '强势', '看涨', '买入', '推荐', '超额收益', '业绩预增']
        negative_words = ['跌', '亏损', '利空', '风险', '暴跌', '减持', '预警', '业绩预降', '问题', '调查', '违约', '造假']

        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"


class NewsDownloader:
    """新闻内容下载器"""

    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir) if download_dir else NEWS_CACHE_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_article(self, article: NewsArticle) -> NewsArticle:
        """下载文章内容"""
        if not article.url:
            return article

        save_path = self.download_dir / f"{article.publish_time[:10]}_{hash(article.url)}.json"
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                article.content = cached.get('content', '')
                article.is_downloaded = True
                return article

        try:
            if SCRAPLING_AVAILABLE:
                fetcher = StealthyFetcher()
                page = fetcher.fetch(article.url, headless=True)

                # 提取正文
                content_selectors = [
                    '.article-content p',
                    '.news-content p',
                    '[class*="content"] p',
                    '.detail-des p'
                ]

                content_parts = []
                for sel in content_selectors:
                    els = page.css(sel)
                    if els:
                        for el in els:
                            text = el.text().strip()
                            if text and len(text) > 20:
                                content_parts.append(text)

                if content_parts:
                    article.content = '\n\n'.join(content_parts)

                # 提取摘要
                if not article.summary:
                    summary_sel = page.css_first('.article-summary, .news-summary, [class*="summary"]')
                    if summary_sel:
                        article.summary = summary_sel.text().strip()

                article.is_downloaded = True

                # 缓存
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': article.title,
                        'url': article.url,
                        'publish_time': article.publish_time,
                        'source': article.source,
                        'summary': article.summary,
                        'content': article.content
                    }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[错误] 下载文章失败: {article.url}, {e}")

        return article


def format_news_report(news_list: List[Dict], stock_code: str = "") -> str:
    """
    格式化新闻报告

    Args:
        news_list: 新闻列表
        stock_code: 股票代码

    Returns:
        格式化的报告文本
    """
    if not news_list:
        return "暂无相关新闻"

    lines = []
    title = f"{stock_code} 新闻" if stock_code else "新闻"
    lines.append(f"\n{'='*60}")
    lines.append(f"【{title}】")
    lines.append(f"{'='*60}")

    # 统计
    sentiments = [n.get('sentiment', 'neutral') for n in news_list]
    pos = sentiments.count('positive')
    neg = sentiments.count('negative')
    lines.append(f"共{len(news_list)}条 | 正面{pos} | 负面{neg} | 中性{len(news_list)-pos-neg}")

    lines.append("")

    for i, news in enumerate(news_list[:20], 1):
        sentiment_icon = {"positive": "↑", "negative": "↓", "neutral": "→"}.get(news.get('sentiment', 'neutral'), "")

        title_text = news.get('title', '')[:45]
        source = news.get('source', '')
        time_str = news.get('publish_time', '')[:16]

        lines.append(f"{i:2d}. {sentiment_icon} {title_text}")

        if source or time_str:
            meta = f"    {source} {time_str}"
            lines.append(meta)

        if news.get('summary'):
            summary = news['summary'][:60]
            lines.append(f"    摘要: {summary}...")

        lines.append("")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python news_scraper.py market                    # 市场新闻")
        print("  python news_scraper.py stock <代码>            # 个股新闻")
        print("  python news_scraper.py search <关键词>        # 搜索新闻")
        print("  python news_scraper.py sentiment <代码>        # 舆情分析")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "market":
        aggregator = NewsAggregator()
        print(aggregator.get_market_digest())

    elif cmd == "stock":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        aggregator = NewsAggregator()
        news = aggregator.get_stock_news_all(code)
        print(format_news_report(news, code))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("请提供关键词")
            sys.exit(1)
        keyword = sys.argv[2]
        api = EastMoneyNewsAPI()
        news = api.search_news(keyword)
        print(format_news_report([{
            'title': a.title,
            'url': a.url,
            'publish_time': a.publish_time,
            'source': a.source,
            'sentiment': 'neutral'
        } for a in news], keyword))

    elif cmd == "sentiment":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        aggregator = NewsAggregator()
        result = aggregator.get_stock_sentiment(code)
        print(f"\n【{code} 舆情分析】")
        print(f"情感倾向: {result['label']} (评分: {result['score']})")
        print(f"正面新闻: {result['positive_count']}条")
        print(f"负面新闻: {result['negative_count']}条")
        print(f"中性新闻: {result['neutral_count']}条")

    else:
        print(f"未知命令: {cmd}")
