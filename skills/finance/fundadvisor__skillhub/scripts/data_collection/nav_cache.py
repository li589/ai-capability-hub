# -*- coding: utf-8 -*-
"""基金净值历史缓存 (v8.0 新增)
================================
本地 SQLite 缓存基金日净值数据，为回测引擎提供数据基础。
纯标准库（sqlite3 + json），零外部依赖。

设计原则:
  - 先查缓存，未命中再请求在线源
  - 缓存过期策略: T+1 自动刷新最近净值
  - 批量预热: warm_cache(codes) 预加载一组基金净值
  - 优雅降级: 在线源不可用时返回缓存数据（可能陈旧）
"""
from __future__ import annotations

import json
import sqlite3
import sys
import threading
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from fund_advisor_paths import DATA_DIR  # noqa: E402

CACHE_DB_PATH = DATA_DIR / "nav_cache.db"
CACHE_TTL_HOURS = 24  # 缓存有效期（小时）


class NavCache:
    """基金日净值缓存数据库。

    表结构:
        nav_history(code TEXT, date TEXT, nav REAL, acc_nav REAL,
                    fetched_at TEXT, PRIMARY KEY(code, date))
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = Path(db_path) if db_path else CACHE_DB_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表。"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nav_history (
                    code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    nav REAL,
                    acc_nav REAL,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY (code, date)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nav_code_date
                ON nav_history(code, date)
            """)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接。"""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── 查询接口 ──────────────────────────────────────────────

    def get_nav_history(self, fund_code: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取基金历史净值列表（按日期升序）。

        Args:
            fund_code: 基金代码（6位字符串）
            start_date: 起始日期 "YYYY-MM-DD"，默认不限
            end_date: 结束日期 "YYYY-MM-DD"，默认不限

        Returns:
            [{"date": "2026-01-02", "nav": 1.2345, "acc_nav": 2.3456}, ...]
            缓存未命中时返回空列表（不抛异常）。
        """
        with self._lock:
            try:
                conn = self._get_conn()
                sql = "SELECT date, nav, acc_nav FROM nav_history WHERE code = ?"
                params = [fund_code]
                if start_date:
                    sql += " AND date >= ?"
                    params.append(start_date)
                if end_date:
                    sql += " AND date <= ?"
                    params.append(end_date)
                sql += " ORDER BY date ASC"
                rows = conn.execute(sql, params).fetchall()
                return [{"date": r["date"], "nav": r["nav"],
                         "acc_nav": r["acc_nav"]} for r in rows]
            except Exception:
                return []

    def get_latest_nav(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """获取基金最新净值。"""
        with self._lock:
            try:
                conn = self._get_conn()
                row = conn.execute(
                    "SELECT date, nav, acc_nav FROM nav_history "
                    "WHERE code = ? ORDER BY date DESC LIMIT 1",
                    (fund_code,)
                ).fetchone()
                if row:
                    return {"date": row["date"], "nav": row["nav"],
                            "acc_nav": row["acc_nav"]}
            except Exception:
                pass
        return None

    def get_nav_series(self, fund_code: str,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[float]:
        """获取净值序列（仅 nav 浮点数列表），方便直接计算指标。

        Returns:
            [1.234, 1.245, ...] 按日期升序排列
        """
        history = self.get_nav_history(fund_code, start_date, end_date)
        return [h["nav"] for h in history if h.get("nav")]

    def has_data(self, fund_code: str, min_days: int = 20) -> bool:
        """检查是否有足够的历史数据天数。"""
        with self._lock:
            try:
                conn = self._get_conn()
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM nav_history WHERE code = ?",
                    (fund_code,)
                ).fetchone()
                return (row["cnt"] or 0) >= min_days
            except Exception:
                return False

    def is_fresh(self, fund_code: str) -> bool:
        """检查缓存是否新鲜（最近抓取时间 < TTL）。"""
        with self._lock:
            try:
                conn = self._get_conn()
                row = conn.execute(
                    "SELECT MAX(fetched_at) as last_fetch FROM nav_history WHERE code = ?",
                    (fund_code,)
                ).fetchone()
                if row and row["last_fetch"]:
                    last = datetime.fromisoformat(row["last_fetch"])
                    return (datetime.now() - last).total_seconds() < CACHE_TTL_HOURS * 3600
            except Exception:
                pass
        return False

    # ── 写入接口 ──────────────────────────────────────────────

    def store_nav(self, fund_code: str, date_str: str,
                  nav: float, acc_nav: Optional[float] = None) -> None:
        """存储单条净值记录（INSERT OR REPLACE）。"""
        fetched_at = datetime.now().isoformat()
        with self._lock:
            try:
                conn = self._get_conn()
                conn.execute(
                    "INSERT OR REPLACE INTO nav_history "
                    "(code, date, nav, acc_nav, fetched_at) VALUES (?, ?, ?, ?, ?)",
                    (fund_code, date_str, nav, acc_nav, fetched_at)
                )
                conn.commit()
            except Exception:
                pass

    def store_nav_batch(self, fund_code: str,
                         records: List[Dict[str, Any]]) -> int:
        """批量存储净值记录。

        Args:
            fund_code: 基金代码
            records: [{"date": "2026-01-02", "nav": 1.234, "acc_nav": 2.345}, ...]

        Returns:
            成功写入的记录数
        """
        if not records:
            return 0
        fetched_at = datetime.now().isoformat()
        count = 0
        with self._lock:
            try:
                conn = self._get_conn()
                for r in records:
                    d = r.get("date", "")
                    nav = r.get("nav")
                    if not d or nav is None:
                        continue
                    acc = r.get("acc_nav") or r.get("accumulated_nav")
                    conn.execute(
                        "INSERT OR REPLACE INTO nav_history "
                        "(code, date, nav, acc_nav, fetched_at) VALUES (?, ?, ?, ?, ?)",
                        (fund_code, d, float(nav),
                         float(acc) if acc else None, fetched_at)
                    )
                    count += 1
                conn.commit()
            except Exception:
                pass
        return count

    def warm_cache(self, fund_codes: List[str], force_fetch: bool = False,
                   min_days: int = 30) -> Dict[str, int]:
        """v9.0: 批量预热缓存 — 缓存不足时在线拉取（urllib 天天基金 pingzhongdata，零依赖）。

        Args:
            fund_codes: 基金代码列表
            force_fetch: 是否强制在线拉取（默认仅在缓存天数不足时拉取）
            min_days: 缓存少于该天数视为需拉取

        Returns:
            {"000001": 120, "000002": 0}  代码->缓存天数
        """
        result = {}
        for code in fund_codes:
            days = self._count_days(code)
            if days < min_days or force_fetch:
                try:
                    fetched = self._fetch_nav_online(code)
                    if fetched:
                        days = len(fetched)
                except Exception:
                    pass
            result[code] = days
        return result

    def _fetch_nav_online(self, fund_code: str) -> List[float]:
        """v9.0: 在线拉取基金净值序列并写入缓存（天天基金 pingzhongdata.js）。"""
        import json as _json
        import re as _re
        import urllib.request
        from datetime import datetime
        url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0",
                     "Referer": "https://fund.eastmoney.com/"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
        m = _re.search(r"var Data_netWorthTrend = (\[.*?\]);", text, _re.DOTALL)
        if not m:
            return []
        try:
            trend = _json.loads(m.group(1))
        except Exception:
            return []
        navs = []
        for item in trend:
            nav = item.get("y")
            if nav is None:
                continue
            ts = item.get("x", 0) / 1000
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
            try:
                self.store_nav(fund_code, date_str, float(nav))
            except Exception:
                pass
            navs.append(float(nav))
        return navs

    def _count_days(self, fund_code: str) -> int:
        """统计某基金缓存天数。"""
        with self._lock:
            try:
                conn = self._get_conn()
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM nav_history WHERE code = ?",
                    (fund_code,)
                ).fetchone()
                return row["cnt"] if row else 0
            except Exception:
                return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息。"""
        with self._lock:
            try:
                conn = self._get_conn()
                total = conn.execute(
                    "SELECT COUNT(DISTINCT code) as funds, COUNT(*) as records "
                    "FROM nav_history"
                ).fetchone()
                latest = conn.execute(
                    "SELECT MAX(fetched_at) as last FROM nav_history"
                ).fetchone()
                return {
                    "total_funds": total["funds"] or 0,
                    "total_records": total["records"] or 0,
                    "last_update": latest["last"] or "",
                    "db_path": str(self._db_path),
                    "db_size_kb": round(
                        self._db_path.stat().st_size / 1024, 1
                    ) if self._db_path.exists() else 0,
                }
            except Exception:
                return {"error": "无法获取统计信息"}

    def cleanup_old(self, keep_days: int = 730) -> int:
        """清理超过 keep_days 天的旧数据，返回删除记录数。"""
        cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
        with self._lock:
            try:
                conn = self._get_conn()
                cur = conn.execute(
                    "DELETE FROM nav_history WHERE date < ?", (cutoff,)
                )
                conn.commit()
                return cur.rowcount
            except Exception:
                return 0


# 模块级单例
_cache_instance: Optional[NavCache] = None
_cache_lock = threading.Lock()


def get_nav_cache() -> NavCache:
    """获取 NavCache 单例。"""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = NavCache()
    return _cache_instance
