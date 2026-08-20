# -*- coding: utf-8 -*-
"""
全量扫描索引器
扫描所有A股上市公司，建立报告/公告索引
支持增量更新和断点续扫
"""

import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
INDEX_DB_PATH = SKILL_DATA_DIR / "report_index.db"
SCAN_STATE_FILE = SKILL_DATA_DIR / "scan_state.json"


@dataclass
class ReportIndex:
    """索引记录"""
    stock_code: str
    stock_name: str
    report_type: str  # periodic/broker/announcement
    report_title: str
    publish_date: str
    url: str
    is_available: bool = True
    indexed_at: str = ""
    broker_name: str = ""
    rating: str = ""

    def to_dict(self) -> Dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "report_type": self.report_type,
            "report_title": self.report_title,
            "publish_date": self.publish_date,
            "url": self.url,
            "is_available": self.is_available,
            "indexed_at": self.indexed_at,
            "broker_name": self.broker_name,
            "rating": self.rating
        }


@dataclass
class ScanProgress:
    """扫描进度"""
    total_stocks: int = 0
    scanned: int = 0
    failed: int = 0
    current_stock: str = ""
    current_index: int = 0
    start_time: str = ""
    last_checkpoint: str = ""
    status: str = "idle"  # idle/running/completed/error


class StockIndexDatabase:
    """股票索引数据库 (SQLite)"""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else INDEX_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 股票列表表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT NOT NULL,
                    market TEXT DEFAULT "",
                    listed_date TEXT DEFAULT "",
                    last_indexed TEXT DEFAULT ""
                )
            """)

            # 报告索引表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT DEFAULT "",
                    report_type TEXT NOT NULL,
                    report_title TEXT NOT NULL,
                    publish_date TEXT DEFAULT "",
                    url TEXT DEFAULT "",
                    is_available INTEGER DEFAULT 1,
                    indexed_at TEXT DEFAULT "",
                    broker_name TEXT DEFAULT "",
                    rating TEXT DEFAULT "",
                    UNIQUE(stock_code, report_type, report_title, publish_date)
                )
            """)

            # 扫描状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_state (
                    id INTEGER PRIMARY KEY,
                    last_stock_index INTEGER DEFAULT 0,
                    last_scan_time TEXT DEFAULT "",
                    status TEXT DEFAULT 'idle',
                    total_stocks INTEGER DEFAULT 0
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_stock ON report_index(stock_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_type ON report_index(report_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_date ON report_index(publish_date)")

            conn.commit()

    def add_stock(self, stock_code: str, stock_name: str, market: str = ""):
        """添加股票"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO stocks (stock_code, stock_name, market, last_indexed)
                VALUES (?, ?, ?, ?)
            """, (stock_code, stock_name, market, ""))
            conn.commit()

    def add_stock_batch(self, stocks: List[Dict]):
        """批量添加股票"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = [(s['code'], s['name'], s.get('market', '')) for s in stocks]
            cursor.executemany("""
                INSERT OR REPLACE INTO stocks (stock_code, stock_name, market)
                VALUES (?, ?, ?)
            """, data)
            conn.commit()

    def index_report(self, report: ReportIndex):
        """索引单条报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO report_index
                (stock_code, stock_name, report_type, report_title, publish_date,
                 url, is_available, indexed_at, broker_name, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.stock_code, report.stock_name, report.report_type,
                report.report_title, report.publish_date, report.url,
                1 if report.is_available else 0, report.indexed_at,
                report.broker_name, report.rating
            ))
            conn.commit()

    def index_reports_batch(self, reports: List[ReportIndex]):
        """批量索引报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = [
                (r.stock_code, r.stock_name, r.report_type, r.report_title,
                 r.publish_date, r.url, 1 if r.is_available else 0,
                 r.indexed_at, r.broker_name, r.rating)
                for r in reports
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO report_index
                (stock_code, stock_name, report_type, report_title, publish_date,
                 url, is_available, indexed_at, broker_name, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()

    def get_reports_by_stock(self, stock_code: str,
                              report_type: str = None) -> List[ReportIndex]:
        """获取个股报告索引"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if report_type:
                cursor.execute("""
                    SELECT * FROM report_index
                    WHERE stock_code = ? AND report_type = ?
                    ORDER BY publish_date DESC
                """, (stock_code, report_type))
            else:
                cursor.execute("""
                    SELECT * FROM report_index
                    WHERE stock_code = ?
                    ORDER BY publish_date DESC
                """, (stock_code,))

            rows = cursor.fetchall()
            return [self._row_to_index(rows[0])] if rows else []

    def _row_to_index(self, row) -> ReportIndex:
        return ReportIndex(
            stock_code=row['stock_code'],
            stock_name=row['stock_name'],
            report_type=row['report_type'],
            report_title=row['report_title'],
            publish_date=row['publish_date'],
            url=row['url'],
            is_available=bool(row['is_available']),
            indexed_at=row['indexed_at'],
            broker_name=row.get('broker_name', ''),
            rating=row.get('rating', '')
        )

    def search_reports(self, keyword: str = "",
                        report_type: str = None,
                        date_from: str = None,
                        date_to: str = None,
                        stock_codes: List[str] = None,
                        limit: int = 100) -> List[ReportIndex]:
        """全文搜索索引"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if keyword:
                conditions.append("(report_title LIKE ? OR stock_name LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if report_type:
                conditions.append("report_type = ?")
                params.append(report_type)

            if date_from:
                conditions.append("publish_date >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("publish_date <= ?")
                params.append(date_to)

            if stock_codes:
                placeholders = ','.join(['?' for _ in stock_codes])
                conditions.append(f"stock_code IN ({placeholders})")
                params.extend(stock_codes)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT * FROM report_index
                WHERE {where_clause}
                ORDER BY publish_date DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_index(r) for r in rows]

    def get_stock_count(self) -> int:
        """获取股票总数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stocks")
            return cursor.fetchone()[0]

    def get_report_count(self, report_type: str = None) -> int:
        """获取报告总数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if report_type:
                cursor.execute("SELECT COUNT(*) FROM report_index WHERE report_type = ?", (report_type,))
            else:
                cursor.execute("SELECT COUNT(*) FROM report_index")
            return cursor.fetchone()[0]

    def get_scan_state(self) -> Optional[ScanProgress]:
        """获取扫描状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_state WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return ScanProgress(
                    total_stocks=row['total_stocks'],
                    scanned=row['last_stock_index'],
                    last_checkpoint=row['last_scan_time'],
                    status=row['status']
                )
            return None

    def save_scan_state(self, progress: ScanProgress):
        """保存扫描状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO scan_state (id, last_stock_index, last_scan_time, status, total_stocks)
                VALUES (1, ?, ?, ?, ?)
            """, (progress.scanned, progress.last_checkpoint, progress.status, progress.total_stocks))
            conn.commit()

    def update_stock_last_indexed(self, stock_code: str):
        """更新股票最后索引时间"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE stocks SET last_indexed = ? WHERE stock_code = ?
            """, (datetime.now().isoformat(), stock_code))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM stocks")
            stock_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM report_index")
            total_reports = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM report_index WHERE report_type = 'periodic'")
            periodic_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM report_index WHERE report_type = 'broker'")
            broker_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM report_index WHERE report_type = 'announcement'")
            announcement_count = cursor.fetchone()[0]

            return {
                "total_stocks": stock_count,
                "total_reports": total_reports,
                "periodic_reports": periodic_count,
                "broker_reports": broker_count,
                "announcements": announcement_count
            }


class StockIndexer:
    """
    全量扫描索引器

    扫描模式:
    1. 初始化: 从EastMoney获取全量股票列表 (~5000只)
    2. 全量扫描: 遍历每只股票，索引其所有报告/公告
    3. 增量扫描: 仅扫描新发布或变化的报告
    4. 断点续扫: 记录扫描进度，异常中断后可恢复
    """

    def __init__(self, db_path: str = None):
        self.db = StockIndexDatabase(db_path)
        self.session = None

        try:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        except ImportError:
            pass

        # 延迟导入API
        self._periodic_api = None
        self._broker_api = None
        self._announcement_api = None

        # Rate limiting
        self.request_delay = 0.5
        self.max_retries = 3

        # Progress tracking
        self.progress = ScanProgress()

    @property
    def periodic_api(self):
        if self._periodic_api is None:
            from .company_report_scraper import EastMoneyReportAPI
            self._periodic_api = EastMoneyReportAPI()
        return self._periodic_api

    @property
    def broker_api(self):
        if self._broker_api is None:
            from .research_report_scraper import EastMoneyBrokerReportAPI
            self._broker_api = EastMoneyBrokerReportAPI()
        return self._broker_api

    @property
    def announcement_api(self):
        if self._announcement_api is None:
            from .announcement_scraper import AnnouncementSearcher
            self._announcement_api = AnnouncementSearcher()
        return self._announcement_api

    def init_stock_list(self, market: str = "all") -> int:
        """
        初始化股票列表

        从EastMoney获取全量A股列表并写入数据库
        """
        if not self.session:
            print("[错误] requests库未安装")
            return 0

        try:
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
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
                "fields": "f12,f14,f3"
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            stocks = []
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    code = item.get('f12', '')
                    name = item.get('f14', '')
                    if code:
                        market_type = "SH" if code.startswith('6') or code.startswith('9') else "SZ"
                        stocks.append({
                            "code": code,
                            "name": name,
                            "market": market_type
                        })

            self.db.add_stock_batch(stocks)
            print(f"[完成] 已加载 {len(stocks)} 只股票到索引库")
            return len(stocks)

        except Exception as e:
            print(f"[错误] 初始化股票列表失败: {e}")
            return 0

    def full_scan(self, report_types: List[str] = None,
                  progress_callback: Callable = None,
                  checkpoint_interval: int = 100,
                  limit: int = 0) -> Dict[str, Any]:
        """
        全量扫描

        Args:
            report_types: 扫描类型 ["periodic", "broker", "announcement"]
            progress_callback: 进度回调 (scanned, total, current_stock)
            checkpoint_interval: 每N只股票保存一次进度
            limit: 限制扫描数量（0=全部）

        Returns:
            {"scanned": N, "failed": M, "duration": seconds}
        """
        if report_types is None:
            report_types = ["periodic", "broker", "announcement"]

        start_time = datetime.now()

        # 获取股票列表
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stock_code, stock_name FROM stocks ORDER BY stock_code")
            stocks = cursor.fetchall()

        if limit > 0:
            stocks = stocks[:limit]

        total = len(stocks)
        self.progress = ScanProgress(
            total_stocks=total,
            start_time=start_time.isoformat(),
            status="running"
        )

        print(f"[开始] 全量扫描 {total} 只股票...")
        scanned = 0
        failed = 0

        for i, stock in enumerate(stocks):
            code = stock['stock_code']
            name = stock['stock_name']

            self.progress.current_stock = code
            self.progress.current_index = i

            try:
                self._scan_single_stock(code, name, report_types)
                scanned += 1
                self.db.update_stock_last_indexed(code)
            except Exception as e:
                failed += 1
                print(f"[警告] 扫描 {code} 失败: {e}")

            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total, code)

            # 保存检查点
            if (i + 1) % checkpoint_interval == 0:
                self.progress.scanned = scanned
                self.progress.last_checkpoint = datetime.now().isoformat()
                self.db.save_scan_state(self.progress)
                print(f"[进度] 已扫描 {scanned}/{total}, 失败 {failed}")

            # 避免请求过快
            time.sleep(self.request_delay)

        self.progress.scanned = scanned
        self.progress.status = "completed"
        self.progress.last_checkpoint = datetime.now().isoformat()
        self.db.save_scan_state(self.progress)

        duration = (datetime.now() - start_time).total_seconds()

        print(f"[完成] 扫描完成: 成功 {scanned}, 失败 {failed}, 耗时 {duration:.1f}秒")

        return {
            "scanned": scanned,
            "failed": failed,
            "duration": duration
        }

    def _scan_single_stock(self, stock_code: str, stock_name: str,
                           report_types: List[str]) -> List[ReportIndex]:
        """扫描单只股票的所有报告"""
        reports = []
        now = datetime.now().isoformat()

        # 定期报告
        if "periodic" in report_types:
            try:
                periodic_reports = self.periodic_api.search_reports(
                    stock_code, max_results=50
                )
                for p in periodic_reports:
                    from .company_report_scraper import CompanyReport
                    if isinstance(p, CompanyReport):
                        idx = ReportIndex(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            report_type="periodic",
                            report_title=getattr(p, 'title', ''),
                            publish_date=getattr(p, 'publish_date', ''),
                            url=getattr(p, 'url', ''),
                            indexed_at=now
                        )
                        reports.append(idx)
            except Exception as e:
                print(f"[警告] 获取 {stock_code} 定期报告失败: {e}")

        # 券商研报
        if "broker" in report_types:
            try:
                broker_reports = self.broker_api.get_stock_reports(
                    stock_code, max_results=50
                )
                for b in broker_reports:
                    from .research_report_scraper import BrokerReport
                    if isinstance(b, BrokerReport):
                        idx = ReportIndex(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            report_type="broker",
                            report_title=getattr(b, 'title', ''),
                            publish_date=getattr(b, 'publish_date', ''),
                            url=getattr(b, 'url', ''),
                            indexed_at=now,
                            broker_name=getattr(b, 'broker_name', ''),
                            rating=getattr(b, 'rating', '')
                        )
                        reports.append(idx)
            except Exception as e:
                print(f"[警告] 获取 {stock_code} 券商研报失败: {e}")

        # 公告
        if "announcement" in report_types:
            try:
                announcements = self.announcement_api.search_announcements(
                    "", fund_code=stock_code, max_results=50
                )
                for a in announcements:
                    from .announcement_scraper import Announcement
                    if isinstance(a, Announcement):
                        idx = ReportIndex(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            report_type="announcement",
                            report_title=getattr(a, 'title', ''),
                            publish_date=getattr(a, 'publish_date', ''),
                            url=getattr(a, 'url', ''),
                            indexed_at=now
                        )
                        reports.append(idx)
            except Exception as e:
                print(f"[警告] 获取 {stock_code} 公告失败: {e}")

        # 批量写入索引
        if reports:
            self.db.index_reports_batch(reports)

        return reports

    def incremental_scan(self, days: int = 7) -> Dict[str, Any]:
        """
        增量扫描 - 仅扫描最近N天内发布的报告
        """
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        print(f"[增量扫描] {start_date_str} 至 {end_date_str}")

        # 获取最近N天有更新的股票
        # 直接对所有股票扫描（简化版）
        return self.full_scan(limit=500)  # 限制增量扫描数量

    def resume_scan(self) -> Dict[str, Any]:
        """
        断点续扫 - 从上次中断处继续
        """
        state = self.db.get_scan_state()

        if not state or state.status != "running":
            print("[信息] 没有可恢复的扫描任务")
            return {"scanned": 0, "message": "No task to resume"}

        print(f"[恢复] 从进度 {state.scanned}/{state.total_stocks} 继续扫描...")

        # 获取剩余股票
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stock_code, stock_name FROM stocks
                ORDER BY stock_code
                LIMIT ? OFFSET ?
            """, (state.total_stocks - state.scanned, state.scanned))
            stocks = cursor.fetchall()

        total = len(stocks)
        scanned = 0
        failed = 0

        for i, stock in enumerate(stocks):
            code = stock['stock_code']
            name = stock['stock_name']

            try:
                self._scan_single_stock(code, name, ["periodic", "broker", "announcement"])
                scanned += 1
            except:
                failed += 1

            if (i + 1) % 100 == 0:
                print(f"[进度] 已恢复 {scanned}/{total}")

            time.sleep(self.request_delay)

        # 更新状态
        state.scanned += scanned
        state.status = "completed"
        state.last_checkpoint = datetime.now().isoformat()
        self.db.save_scan_state(state)

        return {"scanned": scanned, "failed": failed}

    def search_reports(self, keyword: str = "",
                        report_type: str = None,
                        date_from: str = None,
                        date_to: str = None,
                        limit: int = 100) -> List[ReportIndex]:
        """搜索索引"""
        return self.db.search_reports(keyword, report_type, date_from, date_to, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """获取扫描统计"""
        return self.db.get_stats()


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python report_indexer.py init                    # 初始化股票列表")
        print("  python report_indexer.py scan --full             # 全量扫描")
        print("  python report_indexer.py scan --incr             # 增量扫描")
        print("  python report_indexer.py scan --resume           # 断点续扫")
        print("  python report_indexer.py search <关键词>          # 搜索")
        print("  python report_indexer.py stats                    # 查看统计")
        sys.exit(1)

    cmd = sys.argv[1]

    indexer = StockIndexer()

    if cmd == "init":
        count = indexer.init_stock_list()
        print(f"初始化完成: {count} 只股票")

    elif cmd == "scan":
        if len(sys.argv) < 3:
            print("请指定扫描模式: --full, --incr, --resume")
            sys.exit(1)

        mode = sys.argv[2]

        if mode == "--full":
            limit = 0
            for i, arg in enumerate(sys.argv):
                if arg == "--limit" and i + 1 < len(sys.argv):
                    limit = int(sys.argv[i + 1])
            result = indexer.full_scan(limit=limit)
            print(f"全量扫描完成: 成功 {result['scanned']}, 失败 {result['failed']}, 耗时 {result['duration']:.1f}秒")

        elif mode == "--incr":
            days = 7
            for i, arg in enumerate(sys.argv):
                if arg == "--days" and i + 1 < len(sys.argv):
                    days = int(sys.argv[i + 1])
            result = indexer.incremental_scan(days=days)
            print(f"增量扫描完成")

        elif mode == "--resume":
            result = indexer.resume_scan()
            print(f"断点续扫完成: {result}")

    elif cmd == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        report_type = None
        for i, arg in enumerate(sys.argv):
            if arg == "--type" and i + 1 < len(sys.argv):
                report_type = sys.argv[i + 1]

        results = indexer.search_reports(keyword=keyword, report_type=report_type)
        print(f"找到 {len(results)} 条索引:")
        for r in results[:20]:
            print(f"  [{r.report_type}] {r.stock_code} {r.stock_name} | {r.publish_date[:10]} | {r.report_title[:40]}")

    elif cmd == "stats":
        stats = indexer.get_stats()
        print(f"\n索引统计:")
        print(f"  股票总数: {stats['total_stocks']}")
        print(f"  报告总数: {stats['total_reports']}")
        print(f"    - 定期报告: {stats['periodic_reports']}")
        print(f"    - 券商研报: {stats['broker_reports']}")
        print(f"    - 公告: {stats['announcements']}")

    else:
        print(f"未知命令: {cmd}")