# -*- coding: utf-8 -*-
"""
综合报告爬虫
统一接口获取定期报告 + 券商研报 + 所有公告
支持批量处理和按需下载
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_DOWNLOAD_DIR = SKILL_DATA_DIR / "comprehensive_reports"


@dataclass
class ReportSummary:
    """综合报告摘要"""
    stock_code: str
    stock_name: str
    periodic_count: int = 0
    broker_count: int = 0
    announcement_count: int = 0
    latest_periodic_date: str = ""
    latest_broker_date: str = ""
    latest_announcement_date: str = ""
    has_buy_rating: bool = False  # 是否有买入评级研报


class ComprehensiveDownloader:
    """统一下载器"""

    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir) if download_dir else DEFAULT_DOWNLOAD_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.periodic_dir = self.download_dir / "periodic"
        self.broker_dir = self.download_dir / "broker"
        self.announcement_dir = self.download_dir / "announcements"

        for d in [self.periodic_dir, self.broker_dir, self.announcement_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

        self.downloaded_count = 0
        self.failed_count = 0

    def download_periodic_report(self, report) -> str:
        """下载定期报告"""
        return self._download_generic(report, self.periodic_dir)

    def download_broker_report(self, report) -> str:
        """下载券商研报"""
        return self._download_generic(report, self.broker_dir)

    def download_announcement(self, report) -> str:
        """下载公告"""
        return self._download_generic(report, self.announcement_dir)

    def _download_generic(self, report, save_dir: Path) -> str:
        """通用下载方法"""
        if not report.url:
            return ""

        stock_dir = save_dir / report.stock_code
        stock_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(report)
        save_path = stock_dir / filename

        if save_path.exists():
            self.downloaded_count += 1
            return str(save_path)

        try:
            if self.session:
                resp = self.session.get(report.url, timeout=60, stream=True)
                if resp.status_code == 200:
                    actual_name = self._get_filename_from_cd(resp.headers)
                    if actual_name:
                        save_path = stock_dir / actual_name

                    with open(save_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)

                    self.downloaded_count += 1
                    return str(save_path)

        except Exception as e:
            print(f"[错误] 下载失败: {report.url}, {e}")

        self.failed_count += 1
        return ""

    def _get_filename_from_cd(self, headers) -> Optional[str]:
        """从Content-Disposition获取文件名"""
        import re
        cd = headers.get('Content-Disposition', '')
        match = re.search(r'filename[^=]*=\s*"?([^";]+)"?', cd)
        if match:
            return match.group(1).strip('" ')
        return None

    def _generate_filename(self, report) -> str:
        """生成文件名"""
        import re
        title = getattr(report, 'title', 'unknown') or 'unknown'
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        date_str = getattr(report, 'publish_date', '').replace("-", "") or ""
        ext = ".pdf"

        file_type = getattr(report, 'file_type', 'pdf') or 'pdf'
        if file_type == 'html':
            ext = ".html"
        elif file_type in ['doc', 'docx']:
            ext = ".docx"

        return f"{date_str}_{safe_title}{ext}"


class ComprehensiveReportManager:
    """
    综合报告管理器

    整合三种数据源的统一入口:
    - 定期报告 (年报/半年报/季报)
    - 券商研报 (买方评级/行业分析)
    - 所有公告 (临时公告/重大事项)
    """

    def __init__(self, download_dir: str = None):
        self.downloader = ComprehensiveDownloader(download_dir)

        # 延迟导入避免循环
        from .company_report_scraper import EastMoneyReportAPI, CompanyReport
        from .research_report_scraper import EastMoneyBrokerReportAPI, BrokerReport
        from .announcement_scraper import AnnouncementSearcher, Announcement

        self.periodic_api = EastMoneyReportAPI()
        self.broker_api = EastMoneyBrokerReportAPI()
        self.announcement_api = AnnouncementSearcher()

        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()

    def get_all_reports(self, stock_code: str,
                        start_date: str = "",
                        end_date: str = "",
                        report_types: List[str] = None) -> Dict[str, Any]:
        """
        获取指定股票所有类型的报告/公告

        Args:
            stock_code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            report_types: 筛选类型 ["periodic", "broker", "announcement"]
                         None = 所有类型

        Returns:
            {
                "periodic_reports": [...],
                "broker_reports": [...],
                "announcements": [...],
                "summary": {...}
            }
        """
        if report_types is None:
            report_types = ["periodic", "broker", "announcement"]

        result = {
            "stock_code": stock_code,
            "periodic_reports": [],
            "broker_reports": [],
            "announcements": [],
            "summary": ReportSummary(stock_code=stock_code, stock_name="")
        }

        # 获取股票名称
        stock_name = self._get_stock_name(stock_code)
        result["summary"].stock_name = stock_name

        # 定期报告
        if "periodic" in report_types:
            periodic = self._fetch_periodic_reports(stock_code, start_date, end_date)
            result["periodic_reports"] = periodic
            result["summary"].periodic_count = len(periodic)
            if periodic:
                dates = [getattr(p, 'publish_date', '') for p in periodic if hasattr(p, 'publish_date')]
                result["summary"].latest_periodic_date = max(dates)[:10] if dates else ""

        # 券商研报
        if "broker" in report_types:
            broker = self._fetch_broker_reports(stock_code, start_date, end_date)
            result["broker_reports"] = broker
            result["summary"].broker_count = len(broker)
            if broker:
                dates = [getattr(b, 'publish_date', '') for b in broker if hasattr(b, 'publish_date')]
                result["summary"].latest_broker_date = max(dates)[:10] if dates else ""
                # 检查是否有买入评级
                result["summary"].has_buy_rating = any(
                    getattr(b, 'rating', '') == "买入" for b in broker
                )

        # 公告
        if "announcement" in report_types:
            announcements = self._fetch_announcements(stock_code, start_date, end_date)
            result["announcements"] = announcements
            result["summary"].announcement_count = len(announcements)
            if announcements:
                dates = [getattr(a, 'publish_date', '') for a in announcements if hasattr(a, 'publish_date')]
                result["summary"].latest_announcement_date = max(dates)[:10] if dates else ""

        return result

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
        try:
            url = "https://80.push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": 1, "pz": 1, "np": 1, "fltt": 2, "invt": 2,
                "fid": "f3",
                "fs": f"m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
                "fields": "f12,f14"
            }
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    if item.get('f12') == code:
                        return item.get('f14', '')
        except Exception:
            pass
        return code

    def _fetch_periodic_reports(self, stock_code: str,
                                 start_date: str, end_date: str) -> List:
        """获取定期报告"""
        from .company_report_scraper import CompanyReport
        try:
            reports = self.periodic_api.search_reports(
                stock_code, "", start_date, end_date, 100
            )
            return reports
        except Exception as e:
            print(f"[错误] 获取定期报告失败: {e}")
            return []

    def _fetch_broker_reports(self, stock_code: str,
                               start_date: str, end_date: str) -> List:
        """获取券商研报"""
        from .research_report_scraper import BrokerReport
        try:
            reports = self.broker_api.get_stock_reports(
                stock_code, start_date, end_date, 100
            )
            return reports
        except Exception as e:
            print(f"[错误] 获取券商研报失败: {e}")
            return []

    def _fetch_announcements(self, stock_code: str,
                              start_date: str, end_date: str) -> List:
        """获取公告"""
        from .announcement_scraper import Announcement
        try:
            announcements = self.announcement_api.search_announcements(
                keyword="", fund_code=stock_code, date_from=start_date, date_to=end_date, max_results=100
            )
            return announcements
        except Exception as e:
            print(f"[错误] 获取公告失败: {e}")
            return []

    def download_all_reports(self, stock_code: str,
                              report_types: List[str] = None,
                              progress_callback: Callable = None) -> Dict[str, Any]:
        """下载所有类型报告"""
        data = self.get_all_reports(stock_code, report_types=report_types)

        results = {"periodic": [], "broker": [], "announcement": []}
        total = data["summary"].periodic_count + data["summary"].broker_count + data["summary"].announcement_count

        current = 0
        for report in data.get("periodic_reports", []):
            path = self.downloader.download_periodic_report(report)
            results["periodic"].append({"title": getattr(report, 'title', ''), "path": path})
            current += 1
            if progress_callback:
                progress_callback(current, total)

        for report in data.get("broker_reports", []):
            path = self.downloader.download_broker_report(report)
            results["broker"].append({"title": getattr(report, 'title', ''), "path": path})
            current += 1
            if progress_callback:
                progress_callback(current, total)

        for ann in data.get("announcements", []):
            path = self.downloader.download_announcement(ann)
            results["announcement"].append({"title": getattr(ann, 'title', ''), "path": path})
            current += 1
            if progress_callback:
                progress_callback(current, total)

        return {
            "stock_code": stock_code,
            "results": results,
            "total_downloaded": sum(len(v) for v in results.values())
        }

    def batch_process_stocks(self, stock_codes: List[str],
                               report_types: List[str] = None,
                               progress_callback: Callable = None) -> Dict[str, Any]:
        """批量处理多只股票"""
        results = []
        total = len(stock_codes)

        for i, code in enumerate(stock_codes):
            try:
                data = self.get_all_reports(code, report_types=report_types)
                results.append({
                    "stock_code": code,
                    "stock_name": data["summary"].stock_name,
                    "periodic": data["summary"].periodic_count,
                    "broker": data["summary"].broker_count,
                    "announcement": data["summary"].announcement_count,
                    "has_buy_rating": data["summary"].has_buy_rating
                })
            except Exception as e:
                results.append({
                    "stock_code": code,
                    "error": str(e)
                })

            if progress_callback:
                progress_callback(i + 1, total)

            # 避免请求过快
            time.sleep(0.3)

        return {
            "total_stocks": total,
            "processed": len(results),
            "results": results
        }

    def generate_report_summary(self, stock_code: str) -> str:
        """生成综合报告摘要"""
        data = self.get_all_reports(stock_code)
        summary = data["summary"]

        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"【{stock_code} {summary.stock_name} 综合报告】")
        lines.append(f"{'='*70}")

        lines.append(f"\n📊 报告统计:")
        lines.append(f"   定期报告: {summary.periodic_count}份" +
                    (f" (最新: {summary.latest_periodic_date})" if summary.latest_periodic_date else ""))
        lines.append(f"   券商研报: {summary.broker_count}份" +
                    (f" (最新: {summary.latest_broker_date})" if summary.latest_broker_date else ""))
        lines.append(f"   公告: {summary.announcement_count}份" +
                    (f" (最新: {summary.latest_announcement_date})" if summary.latest_announcement_date else ""))

        if summary.has_buy_rating:
            lines.append(f"\n✅ 有买入评级研报")

        # 定期报告列表
        periodic = data.get("periodic_reports", [])
        if periodic:
            lines.append(f"\n📄 定期报告 (最近5份):")
            for p in periodic[:5]:
                date = getattr(p, 'publish_date', '')[:10]
                title = getattr(p, 'title', '')[:45]
                ptype = getattr(p, 'report_type', '')
                lines.append(f"   [{date}] {ptype} {title}")

        # 券商研报列表
        broker = data.get("broker_reports", [])
        if broker:
            lines.append(f"\n📈 券商研报 (最近5份):")
            for b in broker[:5]:
                date = getattr(b, 'publish_date', '')[:10]
                title = getattr(b, 'title', '')[:40]
                rating = getattr(b, 'rating', '?')
                broker_name = getattr(b, 'broker_name', '')
                rating_icon = {"买入": "++", "增持": "+", "中性": "=", "减持": "-"}.get(rating, "?")
                lines.append(f"   {rating_icon} {broker_name} | {date} | {title}")

        # 公告列表
        announcements = data.get("announcements", [])
        if announcements:
            lines.append(f"\n📢 公告 (最近5份):")
            for a in announcements[:5]:
                date = getattr(a, 'publish_date', '')[:10]
                title = getattr(a, 'title', '')[:45]
                lines.append(f"   [{date}] {title}")

        lines.append(f"\n{'='*70}")
        return "\n".join(lines)


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python comprehensive_report_scraper.py get <股票代码>       # 获取所有报告")
        print("  python comprehensive_report_scraper.py download <代码>     # 下载所有报告")
        print("  python comprehensive_report_scraper.py batch <代码1,代码2>  # 批量处理")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "get":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        manager = ComprehensiveReportManager()
        print(manager.generate_report_summary(code))

    elif cmd == "download":
        if len(sys.argv) < 3:
            print("请提供股票代码")
            sys.exit(1)
        code = sys.argv[2]
        manager = ComprehensiveReportManager()
        result = manager.download_all_reports(code)
        print(f"\n下载完成:")
        print(f"  定期报告: {len(result['results']['periodic'])}份")
        print(f"  券商研报: {len(result['results']['broker'])}份")
        print(f"  公告: {len(result['results']['announcement'])}份")

    elif cmd == "batch":
        if len(sys.argv) < 3:
            print("请提供股票代码（逗号分隔）")
            sys.exit(1)
        codes = sys.argv[2].split(',')
        manager = ComprehensiveReportManager()
        result = manager.batch_process_stocks(codes)
        print(f"\n批量处理完成: {result['processed']}/{result['total_stocks']}只")
        for r in result['results']:
            if 'error' in r:
                print(f"  {r['stock_code']}: 错误 - {r['error']}")
            else:
                has_buy = "✅" if r.get('has_buy_rating') else ""
                print(f"  {r['stock_code']} {r.get('stock_name', '')}: 定期{r.get('periodic',0)} 研报{r.get('broker',0)} 公告{r.get('announcement',0)} {has_buy}")

    else:
        print(f"未知命令: {cmd}")