# -*- coding: utf-8 -*-
"""
券商研报爬虫模块
支持爬取买方评级、估值模型、行业分析等研报
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

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
BROKER_REPORT_DIR = SKILL_DATA_DIR / "broker_reports"


@dataclass
class BrokerReport:
    """券商研报信息"""
    stock_code: str
    stock_name: str
    title: str
    broker_name: str  # 券商名称
    analyst: str = ""  # 分析师
    report_type: str = ""  # 行业分析/个股研报/策略报告/业绩点评
    rating: str = ""  # 买入/增持/中性/减持/卖出
    target_price: float = 0.0
    target_change_pct: float = 0.0  # 目标涨幅
    publish_date: str = ""
    url: str = ""
    file_type: str = "pdf"
    is_downloaded: bool = False
    local_path: str = ""


@dataclass
class BrokerReportStats:
    """研报统计"""
    total_count: int = 0
    buy_count: int = 0      # 买入
    increase_count: int = 0  # 增持
    neutral_count: int = 0   # 中性
    reduce_count: int = 0    # 减持
    sell_count: int = 0      # 卖出


class EastMoneyBrokerReportAPI:
    """东方财富研报API"""

    # 研报类型映射
    REPORT_TYPE_MAP = {
        "行业": "industry",
        "个股": "stock",
        "策略": "strategy",
        "业绩": "performance",
        "宏观": "macro",
        "债券": "bond",
        "海外": "overseas"
    }

    # 评级关键词
    RATING_KEYWORDS = {
        "买入": ["买入", "推荐", "强烈推荐", "增持", "超配", "推荐-A", "推荐-B"],
        "中性": ["中性", "持有", "观望", "标配", "中性-A", "中性-B", "同步大市"],
        "减持": ["减持", "回避", "卖出", "低配", "规避", "卖出-A", "卖出-B"]
    }

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
        self.base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    def get_stock_reports(self, stock_code: str,
                          start_date: str = "",
                          end_date: str = "",
                          max_results: int = 50) -> List[BrokerReport]:
        """
        获取个股研报

        Args:
            stock_code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            max_results: 最大结果数

        Returns:
            研报列表
        """
        if not self.session:
            return []

        reports = []
        code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')

        try:
            # 东方财富研报API
            url = "https://report.eastmoney.com/api/security/announcement"
            params = {
                "sr": -1,
                "page_size": max_results,
                "page_index": 1,
                "ann_type": "NOTICE",
                "client_source": "web",
                "stock_list": code
            }

            if start_date:
                params["begin_date"] = start_date.replace('-', '')
            if end_date:
                params["end_date"] = end_date.replace('-', '')

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    report = self._parse_report_item(item, code)
                    if report:
                        reports.append(report)

        except Exception as e:
            print(f"[错误] 获取研报失败: {e}")

        # 如果API失败，尝试备用方法：直接从搜索引擎数据
        if not reports:
            reports = self._search_reports_fallback(code, max_results)

        return reports

    def _search_reports_fallback(self, stock_code: str,
                                  max_results: int = 50) -> List[BrokerReport]:
        """备用搜索方法：从东方财富研报页面获取"""
        reports = []

        try:
            # 尝试东方财富研报中心API
            url = self.base_url
            params = {
                "reportName": "RPT_BROKER_NEWS",
                "columns": "ALL",
                "filter": f"(SECUCODE%3D%22{stock_code}.SH%22)",
                "pageNumber": 1,
                "pageSize": max_results,
                "source": "WEB",
                "client": "WEB"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('result') and data['result'].get('data'):
                for item in data['result']['data']:
                    report = self._parse_datacenter_item(item)
                    if report:
                        reports.append(report)

        except Exception:
            pass

        return reports

    def _parse_report_item(self, item: Dict, stock_code: str) -> Optional[BrokerReport]:
        """解析研报项"""
        try:
            title = item.get('title', '') or item.get('title_ch', '')
            if not title:
                return None

            # 跳过非研报类型的公告
            skip_keywords = ['上市', '发行', '审核', '批复', '决定', '通知']
            if any(kw in title for kw in skip_keywords):
                return None

            # 判断研报类型
            report_type = self._identify_report_type(title)

            # 提取券商名称
            broker_name = self._extract_broker_name(title)

            # 提取评级
            rating = self._extract_rating(title)

            # 提取分析师
            analyst = item.get('author', '') or item.get('analyst', '') or ""

            # 提取目标价
            target_price, target_change = self._extract_target_price(title)

            # 公告时间
            publish_date = item.get('notice_date', '') or item.get('display_time', '')
            if len(publish_date) >= 10:
                publish_date = publish_date[:10]

            # URL
            art_url = item.get('art_url', '') or item.get('globalId', '')
            if art_url and not art_url.startswith('http'):
                art_url = f"https://data.eastmoney.com{art_url}"

            return BrokerReport(
                stock_code=stock_code,
                stock_name=item.get('stock_name', '') or item.get('secuName', ''),
                title=title,
                broker_name=broker_name,
                analyst=analyst,
                report_type=report_type,
                rating=rating,
                target_price=target_price,
                target_change_pct=target_change,
                publish_date=publish_date,
                url=art_url,
                file_type='pdf' if '.pdf' in art_url.lower() else 'html'
            )

        except Exception:
            return None

    def _parse_datacenter_item(self, item: Dict) -> Optional[BrokerReport]:
        """解析数据中心研报项"""
        try:
            title = item.get('NOTICETITLE', '') or item.get('title', '')
            if not title or len(title) < 5:
                return None

            report_type = self._identify_report_type(title)
            broker_name = self._extract_broker_name(title)
            rating = self._extract_rating(title)

            # 目标价
            target_price = 0.0
            target_change = 0.0
            if 'TARGETPRICE' in item:
                try:
                    target_price = float(item['TARGETPRICE'])
                except (ValueError, TypeError):
                    pass

            publish_date = item.get('NOTICEDATE', '') or item.get('publish_date', '')
            if isinstance(publish_date, str) and len(publish_date) >= 10:
                publish_date = publish_date[:10]

            return BrokerReport(
                stock_code=item.get('SECUCODE', '').replace('.SH', '').replace('.SZ', ''),
                stock_name=item.get('SECUNAME', '') or item.get('stock_name', ''),
                title=title,
                broker_name=broker_name,
                analyst=item.get('ANALYST', '') or item.get('author', ''),
                report_type=report_type,
                rating=rating,
                target_price=target_price,
                publish_date=publish_date,
                url=item.get('URL', '') or item.get('art_url', ''),
                file_type='pdf'
            )

        except Exception:
            return None

    def _identify_report_type(self, title: str) -> str:
        """识别研报类型"""
        title_upper = title.upper()

        type_patterns = [
            (["行业", "INDUSTRY"], "行业分析"),
            (["个股", "STOCK", "公司研究"], "个股研报"),
            (["策略", "STRATEGY"], "策略报告"),
            (["业绩", "PERFORMANCE", "财报"], "业绩点评"),
            (["宏观", "MACRO", "经济"], "宏观研究"),
            (["债券", "BOND", "信用"], "债券研究"),
        ]

        for keywords, report_type in type_patterns:
            for kw in keywords:
                if kw in title_upper:
                    return report_type

        return "个股研报"  # 默认

    def _extract_broker_name(self, title: str) -> str:
        """提取券商名称"""
        # 常见券商简称模式
        broker_patterns = [
            r'^(.+?)\s*(?:研究|策略|行业|宏观)',
            r'^(.+?)\s*(?:证券|投行|银行)',
            r'\[(.+?)\]',
        ]

        for pattern in broker_patterns:
            match = re.search(pattern, title)
            if match:
                name = match.group(1).strip()
                if len(name) >= 2 and len(name) <= 10:
                    return name

        return "未知券商"

    def _extract_rating(self, title: str) -> str:
        """提取评级"""
        title_upper = title.upper()

        for rating, keywords in self.RATING_KEYWORDS.items():
            for kw in keywords:
                if kw in title_upper:
                    return rating

        return "未知"

    def _extract_target_price(self, title: str) -> tuple:
        """提取目标价和目标涨幅"""
        target_price = 0.0
        target_change = 0.0

        # 目标价模式：目标价XX元、target price XX
        price_match = re.search(r'(?:目标价|target\s*price|目标价格)\s*[:：]?\s*([\d.]+)\s*(?:元|RMB)?', title, re.I)
        if price_match:
            try:
                target_price = float(price_match.group(1))
            except ValueError:
                pass

        # 目标涨幅模式：上涨XX%、涨幅XX%
        change_match = re.search(r'(?:上涨|涨幅|上升|提升)\s*([\d.]+)%', title, re.I)
        if change_match:
            try:
                target_change = float(change_match.group(1))
            except ValueError:
                pass

        return target_price, target_change

    def search_reports_by_keyword(self, keyword: str,
                                    start_date: str = "",
                                    end_date: str = "",
                                    max_results: int = 50) -> List[BrokerReport]:
        """按关键词搜索研报"""
        if not self.session:
            return []

        reports = []

        try:
            # 使用东方财富搜索API
            url = "https://search-api.eastmoney.com/search/jsonp"
            params = {
                "cb": "callback",
                "param": json.dumps({
                    "uid": "",
                    "keyword": keyword,
                    "type": ["researchReport"],
                    "client": "web",
                    "param": {
                        "researchReport": {
                            "fields": ["title", "time", "url", "broker", "analyst", "rating"],
                            "pageSize": max_results,
                            "pageIndex": 1
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
                if data.get('result') and data['result'].get('researchReport'):
                    for item in data['result']['researchReport']:
                        report = self._parse_search_result(item)
                        if report:
                            reports.append(report)

        except Exception as e:
            print(f"[错误] 搜索研报失败: {e}")

        return reports

    def _parse_search_result(self, item: Dict) -> Optional[BrokerReport]:
        """解析搜索结果"""
        try:
            title = item.get('title', '')
            if not title:
                return None

            return BrokerReport(
                stock_code="",
                stock_name="",
                title=title,
                broker_name=item.get('broker', ''),
                analyst=item.get('analyst', ''),
                report_type=self._identify_report_type(title),
                rating=item.get('rating', ''),
                publish_date=item.get('time', '')[:10] if item.get('time') else '',
                url=item.get('url', ''),
                file_type='pdf'
            )

        except Exception:
            return None

    def get_top_reports(self, broker_name: str = "",
                        min_rating: str = "买入",
                        limit: int = 20) -> List[BrokerReport]:
        """
        获取热门研报

        Args:
            broker_name: 券商名称（空则所有）
            min_rating: 最低评级
            limit: 返回数量

        Returns:
            研报列表
        """
        if not self.session:
            return []

        reports = []

        try:
            url = self.base_url
            params = {
                "reportName": "RPT_BROKER_NEWS",
                "columns": "ALL",
                "pageNumber": 1,
                "pageSize": limit,
                "source": "WEB",
                "client": "WEB",
                "sortColumns": "NOTICEDATE",
                "sortTypes": "-1"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('result') and data['result'].get('data'):
                for item in data['result']['data']:
                    report = self._parse_datacenter_item(item)
                    if report:
                        # 过滤
                        # v4.4.0 修复：精确匹配而非子串匹配，避免 "中信" 误匹配 "中信建投"
                        if broker_name and broker_name != report.broker_name:
                            continue
                        if not self._rating_meets_threshold(report.rating, min_rating):
                            continue
                        reports.append(report)

        except Exception as e:
            print(f"[错误] 获取热门研报失败: {e}")

        return reports[:limit]

    def _rating_meets_threshold(self, rating: str, min_rating: str) -> bool:
        """判断评级是否满足阈值"""
        rating_order = {"买入": 3, "增持": 2, "中性": 1, "减持": 0, "卖出": -1}
        rating_val = rating_order.get(rating, 0)
        min_val = rating_order.get(min_rating, 0)
        return rating_val >= min_val


class BrokerReportDownloader:
    """研报下载器"""

    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir) if download_dir else BROKER_REPORT_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.session = None
        if REQUESTS_AVAILABLE:
            try:
                from .http_utils import RatelimitedSession
            except ImportError:
                from http_utils import RatelimitedSession  # type: ignore
            self.session = RatelimitedSession(requests.Session())
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

        self.downloaded_count = 0
        self.failed_count = 0

    def download_report(self, report: BrokerReport) -> str:
        """下载单条研报"""
        if not report.url:
            return ""

        save_dir = self.download_dir / report.stock_code
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(report)
        save_path = save_dir / filename

        if save_path.exists():
            self.downloaded_count += 1
            report.is_downloaded = True
            report.local_path = str(save_path)
            return str(save_path)

        try:
            if self.session:
                resp = self.session.get(report.url, timeout=60, stream=True)
                if resp.status_code == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    actual_name = self._get_filename_from_cd(resp.headers)
                    if actual_name:
                        save_path = save_dir / actual_name

                    with open(save_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)

                    self.downloaded_count += 1
                    report.is_downloaded = True
                    report.local_path = str(save_path)
                    return str(save_path)

        except Exception as e:
            print(f"[错误] 下载失败: {report.url}, {e}")

        self.failed_count += 1
        return ""

    def _get_filename_from_cd(self, headers) -> Optional[str]:
        """从Content-Disposition获取文件名"""
        cd = headers.get('Content-Disposition', '')
        match = re.search(r'filename[^=]*=\s*"?([^";]+)"?', cd)
        if match:
            return match.group(1).strip('" ')
        return None

    def _generate_filename(self, report: BrokerReport) -> str:
        """生成文件名"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '', report.title)
        safe_title = safe_title[:50]

        date_str = report.publish_date.replace("-", "") if report.publish_date else ""
        broker = re.sub(r'[<>:"/\\|?*]', '', report.broker_name)[:10]

        ext = ".pdf" if report.file_type == "pdf" else ".html"
        return f"{date_str}_{broker}_{safe_title}{ext}"

    def batch_download(self, reports: List[BrokerReport],
                      progress_callback: Callable = None) -> Dict[str, Any]:
        """批量下载"""
        self.downloaded_count = 0
        self.failed_count = 0
        results = []

        total = len(reports)
        for i, report in enumerate(reports):
            local_path = self.download_report(report)
            results.append({
                "report": report,
                "local_path": local_path,
                "success": bool(local_path)
            })

            if progress_callback:
                progress_callback(i + 1, total)

        return {
            "total": total,
            "downloaded": self.downloaded_count,
            "failed": self.failed_count,
            "results": results
        }


class BrokerReportManager:
    """研报管理器"""

    def __init__(self):
        self.api = EastMoneyBrokerReportAPI()
        self.downloader = BrokerReportDownloader()

    def get_reports_all(self, stock_code: str, max_results: int = 50) -> List[BrokerReport]:
        """获取个股所有研报"""
        return self.api.get_stock_reports(stock_code, max_results=max_results)

    def get_reports_by_broker(self, broker_name: str, limit: int = 20) -> List[BrokerReport]:
        """按券商筛选研报"""
        return self.api.get_top_reports(broker_name=broker_name, limit=limit)

    def download_reports(self, stock_code: str,
                         min_rating: str = "中性",
                         progress_callback: Callable = None) -> Dict[str, Any]:
        """下载研报"""
        reports = self.get_reports_all(stock_code)

        # 按评级过滤
        if min_rating:
            rating_order = {"买入": 3, "增持": 2, "中性": 1, "减持": 0, "卖出": -1}
            min_val = rating_order.get(min_rating, 0)
            reports = [r for r in reports if rating_order.get(r.rating, 0) >= min_val]

        return self.downloader.batch_download(reports, progress_callback)

    def generate_report_summary(self, stock_code: str) -> str:
        """生成研报摘要"""
        reports = self.get_reports_all(stock_code)

        if not reports:
            return f"未找到 {stock_code} 的研报记录"

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"【{stock_code} 券商研报】")
        lines.append(f"{'='*60}")

        # 统计
        stats = BrokerReportStats()
        stats.total_count = len(reports)

        for r in reports:
            if r.rating == "买入":
                stats.buy_count += 1
            elif r.rating == "增持":
                stats.increase_count += 1
            elif r.rating == "中性":
                stats.neutral_count += 1
            elif r.rating == "减持":
                stats.reduce_count += 1
            elif r.rating == "卖出":
                stats.sell_count += 1

        lines.append(f"\n总计: {stats.total_count}份")
        lines.append(f"  买入: {stats.buy_count} | 增持: {stats.increase_count} | 中性: {stats.neutral_count} | 减持: {stats.reduce_count}")

        # 按券商分组
        by_broker = {}
        for r in reports:
            broker = r.broker_name or "未知券商"
            if broker not in by_broker:
                by_broker[broker] = []
            by_broker[broker].append(r)

        lines.append(f"\n按券商 ({len(by_broker)}家):")
        for broker, broker_reports in sorted(by_broker.items(), key=lambda x: -len(x[1]))[:10]:
            lines.append(f"\n  {broker} ({len(broker_reports)}份):")
            for r in broker_reports[:3]:
                rating_icon = {"买入": "++", "增持": "+", "中性": "=", "减持": "-", "卖出": "--"}.get(r.rating, "?")
                lines.append(f"    [{rating_icon}] {r.publish_date[:10] if r.publish_date else 'N/A'} {r.title[:35]}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python research_report_scraper.py search <股票代码>  # 搜索研报")
        print("  python research_report_scraper.py top [券商]       # 热门研报")
        print("  python research_report_scraper.py broker <券商>    # 按券商筛选")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        manager = BrokerReportManager()
        print(manager.generate_report_summary(code))

    elif cmd == "top":
        broker = sys.argv[2] if len(sys.argv) > 2 else ""
        api = EastMoneyBrokerReportAPI()
        reports = api.get_top_reports(broker_name=broker, limit=20)
        print(f"\n{'='*60}")
        print(f"【热门研报】" + (f" - {broker}" if broker else ""))
        print(f"{'='*60}")
        for r in reports:
            rating_icon = {"买入": "++", "增持": "+", "中性": "=", "减持": "-", "卖出": "--"}.get(r.rating, "?")
            print(f"{rating_icon} {r.broker_name} | {r.publish_date[:10] if r.publish_date else 'N/A'} | {r.title[:40]}")
            if r.stock_code:
                print(f"    股票: {r.stock_code} {r.stock_name}")
        print(f"{'='*60}")

    elif cmd == "broker":
        if len(sys.argv) < 3:
            print("请提供券商名称")
            sys.exit(1)
        broker = sys.argv[2]
        manager = BrokerReportManager()
        reports = manager.get_reports_by_broker(broker, limit=20)
        print(f"\n{'='*60}")
        print(f"【{broker} 研报】")
        print(f"{'='*60}")
        for r in reports:
            print(f"  [{r.rating}] {r.publish_date[:10] if r.publish_date else 'N/A'} {r.title[:40]}")
        print(f"{'='*60}")

    else:
        print(f"未知命令: {cmd}")