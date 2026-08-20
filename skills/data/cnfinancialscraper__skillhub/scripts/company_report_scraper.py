# -*- coding: utf-8 -*-
"""
上市公司定期报告爬虫
支持所有A股上市公司的年报、半年报、季报爬取
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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
REPORT_CACHE_DIR = SKILL_DATA_DIR / "company_reports"


@dataclass
class CompanyReport:
    """公司报告信息"""
    stock_code: str
    stock_name: str
    report_type: str  # 年报、半年报、季报、一季报、三季报
    report_year: int
    report_period: str  # 2024年报、2024一季报等
    publish_date: str
    url: str
    file_type: str  # pdf, html
    file_size: int = 0
    is_downloaded: bool = False
    local_path: str = ""


class EastMoneyReportAPI:
    """东方财富财报API"""

    # 财报时间安排
    REPORT_SCHEDULE = {
        "一季报": {"deadline": "04-30", "period": "03-31"},
        "半年报": {"deadline": "08-31", "period": "06-30"},
        "三季报": {"deadline": "10-31", "period": "09-30"},
        "年报": {"deadline": "04-30", "period": "12-31"}
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

    def get_stock_list(self, market: str = "all") -> List[Dict]:
        """
        获取股票列表

        Args:
            market: 市场筛选 (sh, sz, all)

        Returns:
            股票列表
        """
        if not self.session:
            return []

        try:
            # 东方财富A股列表API
            url = "https://80.push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": 1,
                "pz": 5000,
                "po": 1,
                "np": 1,
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2,
                "invt": 2,
                "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048" if market == "all" else "m:0+t:6,m:0+t:80",
                "fields": "f12,f14,f2,f3"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            stocks = []
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    stocks.append({
                        "code": item.get('f12', ''),
                        "name": item.get('f14', ''),
                        "price": item.get('f2', 0),
                        "change_pct": item.get('f3', 0)
                    })

            return stocks

        except Exception as e:
            print(f"[错误] 获取股票列表失败: {e}")
            return []

    def search_reports(self, stock_code: str, report_type: str = "",
                       start_date: str = "", end_date: str = "",
                       max_results: int = 50) -> List[CompanyReport]:
        """
        搜索公司报告

        Args:
            stock_code: 股票代码
            report_type: 报告类型 (年报, 半年报, 季报)
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            max_results: 最大结果数

        Returns:
            报告列表
        """
        if not self.session:
            return []

        reports = []
        code = stock_code.replace('.SH', '').replace('.SZ', '')  # v4.4.0: 删除冗余重复 replace

        # 东方财富公告搜索API
        try:
            url = "https://np-anotice-stock.eastmoney.com/api/security/announcement"
            params = {
                "sr": -1,
                "page_size": max_results,
                "page_index": 1,
                "ann_type": "A",
                "client_source": "web",
                "stock_list": code
            }

            if report_type:
                type_map = {"年报": "annual", "半年报": "halfyear", "季报": "quarter"}
                params["announcement_type"] = type_map.get(report_type, "")

            if start_date:
                params["begin_date"] = start_date.replace('-', '')
            if end_date:
                params["end_date"] = end_date.replace('-', '')

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    report = self._parse_announcement_item(item, code)
                    if report:
                        reports.append(report)

        except Exception as e:
            print(f"[错误] 搜索报告失败: {e}")

        return reports

    def _parse_announcement_item(self, item: Dict, stock_code: str) -> Optional[CompanyReport]:
        """解析公告项"""
        try:
            title = item.get('title', '')
            notice_date = item.get('notice_date', '')
            art_url = item.get('art_url', '')
            em_url = item.get('globalId', '')

            # 判断报告类型
            report_type = self._identify_report_type(title)
            if not report_type:
                return None

            # 提取年份
            year_match = re.search(r'(\d{4})', title)
            year = int(year_match.group(1)) if year_match else datetime.now().year

            # 报告URL
            report_url = art_url if art_url.startswith('http') else f"https://www.eastmoney.com{art_url}"

            return CompanyReport(
                stock_code=stock_code,
                stock_name=item.get('stock_name', ''),
                report_type=report_type,
                report_year=year,
                report_period=f"{year}{report_type}",
                publish_date=notice_date[:10] if len(notice_date) >= 10 else notice_date,
                url=report_url,
                file_type='pdf' if '.pdf' in art_url.lower() else 'html'
            )

        except Exception:
            return None

    def _identify_report_type(self, title: str) -> str:
        """识别报告类型"""
        title_upper = title.upper()

        if 'ANNUAL REPORT' in title_upper or '年度报告' in title or '年报' in title:
            if '摘要' not in title:
                return '年报'
        elif '半年度' in title or '中期报告' in title or '半年报' in title:
            return '半年报'
        elif '第一季度' in title or '一季报' in title or 'Q1' in title_upper:
            return '一季报'
        elif '第三季度' in title or '三季报' in title or 'Q3' in title_upper:
            return '三季报'

        return ''

    def get_financial_data(self, stock_code: str, page_size: int = 40) -> List[Dict]:
        """
        获取财务数据

        Args:
            stock_code: 股票代码 (如 600519.SH)
            page_size: 返回数量

        Returns:
            财务数据列表
        """
        if not self.session:
            return []

        try:
            # 东方财富财务数据API
            secucode = stock_code if '.' in stock_code else f"{stock_code}.SH"
            url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                "reportName": "RPT_LICO_FN_CPD",
                "columns": "ALL",
                "filter": f"(SECUCODE%3D%22{secucode}%22)",
                "pageNumber": 1,
                "pageSize": page_size,
                "source": "WEB",
                "client": "WEB"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('result') and data['result'].get('data'):
                return data['result']['data']

        except Exception as e:
            print(f"[错误] 获取财务数据失败: {e}")

        return []

    def compare_financials(self, stock_code: str, years: List[int] = None) -> Dict[str, Any]:
        """
        财务数据对比

        Args:
            stock_code: 股票代码
            years: 对比年份列表

        Returns:
            对比结果
        """
        data = self.get_financial_data(stock_code)
        if not data:
            return {}

        if years is None:
            years = [datetime.now().year - i for i in range(4)]

        result = {
            "stock_code": stock_code,
            "periods": [],
            "metrics": {}
        }

        # 关键指标
        key_metrics = [
            'BASIC_EPS',  # 每股收益
            'TOTAL_OPERATE_INCOME',  # 营业收入
            'PARENT_NETPROFIT',  # 净利润
            'WEIGHTAVG_ROE',  # 加权ROE
            'XSMLL',  # 销售毛利率
            'MGJYXJJE',  # 每股经营现金流
        ]

        for record in data:
            dtype = str(record.get('DATATYPE', ''))
            qdate = str(record.get('QDATE', ''))

            # 匹配年份
            matched_year = None
            for year in years:
                if str(year) in dtype:
                    matched_year = year
                    period_key = f"{year}年{dtype.replace(str(year), '').strip()}"
                    break

            if matched_year and period_key not in result["periods"]:
                result["periods"].append(period_key)

                for metric in key_metrics:
                    if metric not in result["metrics"]:
                        result["metrics"][metric] = {}
                    result["metrics"][metric][period_key] = record.get(metric)

        return result


class ReportDownloader:
    """报告下载器"""

    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir) if download_dir else REPORT_CACHE_DIR
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

    def download_report(self, report: CompanyReport) -> str:
        """
        下载单条报告

        Returns:
            本地文件路径
        """
        if not report.url:
            return ""

        # 生成保存路径
        save_dir = self.download_dir / report.stock_code
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{report.report_period}_{report.report_type}_{report.stock_name}.pdf"
        save_path = save_dir / filename

        if save_path.exists():
            self.downloaded_count += 1
            return str(save_path)

        # 下载文件
        try:
            if self.session:
                resp = self.session.get(report.url, timeout=60, stream=True)
                if resp.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.downloaded_count += 1
                    return str(save_path)
        except Exception as e:
            print(f"[错误] 下载失败: {report.url}, {e}")

        self.failed_count += 1
        return ""

    def batch_download(self, reports: List[CompanyReport],
                      progress_callback=None) -> Dict[str, Any]:
        """
        批量下载

        Args:
            reports: 报告列表
            progress_callback: 进度回调 (current, total)

        Returns:
            下载结果统计
        """
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


class CompanyReportManager:
    """公司报告管理器"""

    def __init__(self):
        self.api = EastMoneyReportAPI()
        self.downloader = ReportDownloader()

    def get_recent_reports(self, stock_code: str, count: int = 10) -> List[CompanyReport]:
        """
        获取最新报告

        Args:
            stock_code: 股票代码
            count: 返回数量

        Returns:
            报告列表
        """
        return self.api.search_reports(stock_code, max_results=count)

    def get_annual_reports(self, stock_code: str, year: int = None) -> List[CompanyReport]:
        """
        获取年报

        Args:
            stock_code: 股票代码
            year: 年份（默认近3年）

        Returns:
            年报列表
        """
        if year:
            start = f"{year}-01-01"
            end = f"{year}-12-31"
        else:
            current_year = datetime.now().year
            start = f"{current_year - 3}-01-01"
            end = f"{current_year}-12-31"

        return self.api.search_reports(stock_code, "年报", start, end)

    def download_reports(self, stock_code: str, report_types: List[str] = None,
                        year: int = None) -> Dict[str, Any]:
        """
        下载指定股票报告

        Args:
            stock_code: 股票代码
            report_types: 报告类型列表
            year: 年份

        Returns:
            下载结果
        """
        if year:
            start_date = f"{year - 1}-10-01"  # 从前一年10月开始（Q3季报）
            end_date = f"{year}-06-30"  # 到次年6月底（Q1季报）
        else:
            current = datetime.now()
            end_date = current.strftime('%Y-%m-%d')
            start_date = (current - timedelta(days=365)).strftime('%Y-%m-%d')

        reports = self.api.search_reports(stock_code, "", start_date, end_date, 100)

        # 过滤类型
        if report_types:
            reports = [r for r in reports if r.report_type in report_types]

        return self.downloader.batch_download(reports)

    def get_financial_comparison(self, stock_code: str, years: List[int] = None) -> Dict:
        """获取财务对比"""
        return self.api.compare_financials(stock_code, years)

    def generate_report_summary(self, stock_code: str) -> str:
        """
        生成报告摘要

        Args:
            stock_code: 股票代码

        Returns:
            摘要文本
        """
        reports = self.get_recent_reports(stock_code, 20)

        if not reports:
            return f"未找到 {stock_code} 的报告记录"

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"【{stock_code} 报告列表】")
        lines.append(f"{'='*60}")

        # 按类型分组
        by_type = {}
        for r in reports:
            if r.report_type not in by_type:
                by_type[r.report_type] = []
            by_type[r.report_type].append(r)

        for rtype, rlist in by_type.items():
            lines.append(f"\n{rtype} ({len(rlist)}份):")
            for r in rlist[:5]:
                lines.append(f"  {r.publish_date} - {r.report_period}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


def get_stock_financial_report(stock_code: str, report_type: str = "年报") -> str:
    """
    获取股票财务报告（便捷函数）

    Args:
        stock_code: 股票代码
        report_type: 报告类型

    Returns:
        报告分析文本
    """
    manager = CompanyReportManager()

    # 获取财务数据
    financials = manager.get_financial_comparison(stock_code)

    if not financials or not financials.get('metrics'):
        return f"未找到 {stock_code} 的财务数据"

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"【{stock_code} 财务数据对比】")
    lines.append(f"{'='*60}")

    # 周期
    periods = financials.get('periods', [])
    if periods:
        lines.append(f"\n报告期: {', '.join(periods[:5])}")

    # 关键指标
    metrics = financials.get('metrics', {})

    metric_names = {
        'BASIC_EPS': '每股收益',
        'TOTAL_OPERATE_INCOME': '营业收入',
        'PARENT_NETPROFIT': '净利润',
        'WEIGHTAVG_ROE': '加权ROE',
        'XSMLL': '销售毛利率',
        'MGJYXJJE': '每股经营现金流'
    }

    lines.append("\n【关键财务指标】")
    for metric_key, metric_name in metric_names.items():
        if metric_key in metrics:
            values = metrics[metric_key]
            vals_str = []
            for period in periods[:4]:
                val = values.get(period)
                if val is not None:
                    if metric_key in ['BASIC_EPS', 'MGJYXJJE']:
                        vals_str.append(f"¥{val:.2f}")
                    elif metric_key in ['WEIGHTAVG_ROE', 'XSMLL']:
                        vals_str.append(f"{val:.2f}%")
                    else:
                        vals_str.append(f"¥{val/1e8:.2f}亿")
                else:
                    vals_str.append("N/A")
            lines.append(f"  {metric_name}: {' vs '.join(vals_str)}")

    lines.append(f"\n{'='*60}")
    return "\n".join(lines)


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python company_report_scraper.py list [市场]     # 获取股票列表")
        print("  python company_report_scraper.py search <代码> # 搜索报告")
        print("  python company_report_scraper.py financial <代码> # 获取财务数据")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        market = sys.argv[2] if len(sys.argv) > 2 else "all"
        api = EastMoneyReportAPI()
        stocks = api.get_stock_list(market)
        print(f"获取到 {len(stocks)} 只股票")
        for s in stocks[:10]:
            print(f"  {s['code']} {s['name']} 现价:{s['price']} 涨跌:{s['change_pct']}%")

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        manager = CompanyReportManager()
        print(manager.generate_report_summary(code))

    elif cmd == "financial":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        print(get_stock_financial_report(code))

    else:
        print(f"未知命令: {cmd}")
