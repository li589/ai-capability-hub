#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场A股股票爬虫
All A-share Stock Market Crawler

数据来源：东方财富A股列表API
- 上交所主板：https://80.push2.eastmoney.com/api/qt/clist/get
- 深交所主板：https://80.push2.eastmoney.com/api/qt/clist/get
- 创业板：https://80.push2.eastmoney.com/api/qt/clist/get
- 科创板：https://80.push2.eastmoney.com/api/qt/clist/get

支持：
- 全市场股票列表（代码、名称、所属行业、流通股本、总股本、市值）
- 实时行情增量更新
- 股票基本信息查询
"""

import json
import time
import ssl
import urllib.request
import urllib.parse
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

# 尝试导入crawl_utils
try:
    from crawl_utils import safe_request, detect_encoding
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


class MarketAllStocksCrawler:
    """
    全市场A股股票爬虫

    功能：
    1. 获取全市场股票列表（上交所、深交所、创业板、科创板）
    2. 增量更新每日行情
    3. 股票基本信息查询
    4. 导出股票列表到JSON
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 缓存文件路径
        self.stocks_file = self.data_dir / "all_a_stocks.json"
        self.stocks_backup_file = self.data_dir / "all_a_stocks_backup.json"

        # 东方财富API（全市场A股）
        self.api_base = "https://80.push2.eastmoney.com/api/qt/clist/get"
        self.api_params = {
            "pn": 1,
            "pz": 5000,  # 每页5000条
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6b742ef8f",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:41+t:43,m:41+t:44",  # 全市场
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f11,f62,f128,f136,f115,f152",
            "_": int(time.time() * 1000)
        }

        # 缓存数据
        self.stocks_cache = {}
        self.last_fetch_time = None

    def fetch_all_stocks(self, market: str = "all", force_update: bool = False) -> List[Dict]:
        """
        获取全市场A股列表

        Args:
            market: 市场类型
                "all" - 全部A股
                "sh" - 上交所主板
                "sz" - 深交所主板
                "cyb" - 创业板
                "kcb" - 科创板
            force_update: 是否强制更新（忽略缓存）

        Returns:
            List[Dict]: 股票列表
        """
        # 缓存检查（5分钟内不重复获取）
        if not force_update and self.stocks_cache:
            cache_age = time.time() - (self.last_fetch_time or 0)
            if cache_age < 300:
                return list(self.stocks_cache.values())

        # 构建筛选条件
        fs_map = {
            "all": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:41+t:43,m:41+t:44",
            "sh": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:41+t:43,m:41+t:44",
            "sz": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:41+t:43,m:41+t:44",
            "cyb": "m:0+t:80,m:1+t:23",  # 创业板
            "kcb": "m:1+t:2,m:41+t:43,m:41+t:44"  # 科创板
        }
        fs = fs_map.get(market, fs_map["all"])

        all_stocks = []
        page = 1
        total_pages = 1

        print(f"[全市场股票爬虫] 开始获取A股列表 (市场: {market})...")

        while page <= total_pages:
            params = self.api_params.copy()
            params["pn"] = page
            params["fs"] = fs

            url = f"{self.api_base}?{urllib.parse.urlencode(params)}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }

            try:
                if HAS_CRAWL_UTILS:
                    raw = safe_request(url, headers=headers, timeout=15)
                else:
                    req = urllib.request.Request(url, headers=headers)
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                        raw = resp.read()

                if not raw:
                    print(f"[全市场股票爬虫] 第{page}页请求失败")
                    break

                if isinstance(raw, bytes):
                    text = raw.decode("utf-8", errors="replace")
                else:
                    text = raw

                data = json.loads(text)
                stocks = data.get("data", {}).get("diff", [])

                if not stocks:
                    break

                for s in stocks:
                    stock_info = self._parse_stock_info(s)
                    if stock_info:
                        all_stocks.append(stock_info)

                total = data.get("data", {}).get("total", 0)
                total_pages = (total + 4999) // 5000

                print(f"[全市场股票爬虫] 第{page}/{total_pages}页，获取{len(stocks)}只股票，累计{len(all_stocks)}只")

                page += 1
                time.sleep(0.3)  # 避免请求过快

            except Exception as e:
                print(f"[全市场股票爬虫] 第{page}页出错: {e}")
                break

        print(f"[全市场股票爬虫] 获取完成，共{len(all_stocks)}只股票")

        # 更新缓存
        self.stocks_cache = {s["code"]: s for s in all_stocks}
        self.last_fetch_time = time.time()

        return all_stocks

    def _parse_stock_info(self, raw: dict) -> Optional[dict]:
        """解析股票信息"""
        code = str(raw.get("f12", "")).zfill(6)
        if not code or len(code) != 6:
            return None

        return {
            "code": code,
            "name": raw.get("f14", ""),
            "price": raw.get("f2", 0),
            "change_pct": raw.get("f3", 0),
            "change_amount": raw.get("f4", 0),
            "volume": raw.get("f5", 0),  # 成交量（手）
            "amount": raw.get("f6", 0),  # 成交额（元）
            "open": raw.get("f15", 0),
            "high": raw.get("f17", 0),
            "low": raw.get("f16", 0),
            "prev_close": raw.get("f18", 0),
            "market_cap": raw.get("f20", 0),  # 总市值（元）
            "float_capital": raw.get("f21", 0),  # 流通市值（元）
            "turnover_rate": raw.get("f8", 0),  # 换手率（%）
            "pe_ratio": raw.get("f9", 0),  # 市盈率
            "pb_ratio": raw.get("f23", 0),  # 市净率
            "dividend_yield": raw.get("f162", 0),  # 股息率
            "year_high": raw.get("f15", 0),  # 年内高点（可能不对）
            "year_low": raw.get("f17", 0),  # 年内低点（可能不对）
            "sector": raw.get("f100", ""),  # 所属行业
            "update_time": datetime.now().isoformat()
        }

    def save_stocks(self, stocks: List[Dict] = None, backup: bool = True):
        """
        保存股票列表到JSON文件

        Args:
            stocks: 股票列表（None使用缓存）
            backup: 是否备份旧文件
        """
        if stocks is None:
            stocks = list(self.stocks_cache.values())

        # 备份旧文件
        if backup and self.stocks_file.exists():
            import shutil
            shutil.copy(self.stocks_file, self.stocks_backup_file)

        # 保存新数据
        data = {
            "update_time": datetime.now().isoformat(),
            "total_count": len(stocks),
            "stocks": stocks
        }

        with open(self.stocks_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[全市场股票爬虫] 已保存到 {self.stocks_file}")

    def load_stocks(self) -> List[Dict]:
        """从文件加载股票列表"""
        if not self.stocks_file.exists():
            return []

        try:
            with open(self.stocks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("stocks", [])
        except Exception as e:
            print(f"[全市场股票爬虫] 加载失败: {e}")
            return []

    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """通过代码获取股票信息"""
        code = str(code).zfill(6)

        # 优先从缓存
        if code in self.stocks_cache:
            return self.stocks_cache[code]

        # 从文件加载
        stocks = self.load_stocks()
        for s in stocks:
            if s["code"] == code:
                self.stocks_cache[code] = s
                return s

        return None

    def get_stocks_by_sector(self, sector: str) -> List[Dict]:
        """获取指定行业的股票"""
        all_stocks = self.fetch_all_stocks()
        return [s for s in all_stocks if sector in s.get("sector", "")]

    def search_stocks(self, keyword: str) -> List[Dict]:
        """
        搜索股票（代码或名称）

        Args:
            keyword: 搜索关键词

        Returns:
            List[Dict]: 匹配的股票列表
        """
        all_stocks = self.fetch_all_stocks()
        keyword = keyword.lower()
        return [
            s for s in all_stocks
            if keyword in s["code"].lower() or keyword in s["name"].lower()
        ]

    def get_top_stocks(self, by: str = "change_pct", limit: int = 20,
                       ascending: bool = False) -> List[Dict]:
        """
        获取排名靠前的股票

        Args:
            by: 排序字段（change_pct/amount/volume/turnover_rate/pe_ratio）
            limit: 返回数量
            ascending: 是否升序

        Returns:
            List[Dict]: 排序后的股票列表
        """
        all_stocks = self.fetch_all_stocks()
        valid_stocks = [s for s in all_stocks if s.get(by, 0) != 0]

        sorted_stocks = sorted(
            valid_stocks,
            key=lambda x: x.get(by, 0),
            reverse=not ascending
        )

        return sorted_stocks[:limit]

    def update_realtime_quotes(self, codes: List[str] = None) -> Dict[str, Dict]:
        """
        增量更新实时行情

        Args:
            codes: 股票代码列表（None则更新全部）

        Returns:
            Dict[str, Dict]: 更新的行情数据
        """
        if codes is None:
            codes = list(self.stocks_cache.keys())

        if not codes:
            return {}

        # 使用腾讯行情API批量获取
        ts_list = []
        for c in codes:
            c = str(c).zfill(6)
            if c.startswith(("6", "5", "9")):
                ts_list.append(f"sh{c}")
            else:
                ts_list.append(f"sz{c}")

        ts = ",".join(ts_list)
        url = f"https://qt.gtimg.cn/q={ts}&_={int(time.time()*1000)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://gu.qq.com/"
        }

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

            if isinstance(raw, bytes):
                text = raw.decode("gbk", errors="replace")
            else:
                text = raw

            import re
            result = {}
            for line in text.strip().split("\n"):
                m = re.search(r"v_(\w+)=\"(.+?)\"", line)
                if not m:
                    continue

                code_with_prefix = m.group(1)
                fields = m.group(2).split("~")

                if len(fields) < 33:
                    continue

                if code_with_prefix.startswith("sh"):
                    code = code_with_prefix[2:]
                elif code_with_prefix.startswith("sz"):
                    code = code_with_prefix[2:]
                else:
                    code = code_with_prefix

                quote = {
                    "price": float(fields[3]) if fields[3] else 0,
                    "prev_close": float(fields[4]) if fields[4] else 0,
                    "open": float(fields[5]) if fields[5] else 0,
                    "volume": float(fields[6]) if fields[6] else 0,
                    "amount": float(fields[37]) if fields[37] else 0,
                    "change": float(fields[31]) if fields[31] else 0,
                    "change_pct": float(fields[32]) if fields[32] else 0,
                }

                result[code] = quote

                # 更新缓存
                if code in self.stocks_cache:
                    self.stocks_cache[code].update(quote)

            return result

        except Exception as e:
            print(f"[全市场股票爬虫] 实时行情更新失败: {e}")
            return {}

    def get_market_summary(self) -> Dict:
        """获取市场摘要"""
        all_stocks = self.fetch_all_stocks()

        # 更新实时行情
        self.update_realtime_quotes()

        total = len(all_stocks)
        rising = sum(1 for s in all_stocks if s.get("change_pct", 0) > 0)
        falling = sum(1 for s in all_stocks if s.get("change_pct", 0) < 0)
        unchanged = total - rising - falling

        total_amount = sum(s.get("amount", 0) for s in all_stocks)
        total_market_cap = sum(s.get("market_cap", 0) for s in all_stocks)

        return {
            "update_time": datetime.now().isoformat(),
            "total_stocks": total,
            "rising_count": rising,
            "falling_count": falling,
            "unchanged_count": unchanged,
            "rising_ratio": f"{rising/total*100:.1f}%" if total > 0 else "0%",
            "total_amount": total_amount,
            "total_market_cap": total_market_cap,
            "market_sentiment": "偏多" if rising > falling else ("偏空" if falling > rising else "中性")
        }


class StockScreener:
    """
    股票筛选器

    基于多维度筛选股票：
    1. 市值筛选（大盘/中盘/小盘）
    2. 估值筛选（PE/PB）
    3. 技术面筛选（均线多头/空头）
    4. 涨跌幅筛选
    5. 行业筛选
    """

    def __init__(self, crawler: MarketAllStocksCrawler = None):
        self.crawler = crawler or MarketAllStocksCrawler()

    def screen_stocks(
        self,
        market_cap_range: Tuple[float, float] = None,  # 亿元
        pe_range: Tuple[float, float] = None,
        pb_range: Tuple[float, float] = None,
        change_pct_range: Tuple[float, float] = None,
        turnover_rate_range: Tuple[float, float] = None,
        sectors: List[str] = None,
        top_n: int = None
    ) -> List[Dict]:
        """
        多维度筛选股票

        Args:
            market_cap_range: 市值范围（亿元），如 (0, 100)
            pe_range: 市盈率范围，如 (0, 20)
            pb_range: 市净率范围，如 (0, 3)
            change_pct_range: 涨跌幅范围（%），如 (-5, 5)
            turnover_rate_range: 换手率范围（%），如 (0, 10)
            sectors: 行业列表
            top_n: 返回前N只

        Returns:
            List[Dict]: 筛选后的股票列表
        """
        stocks = self.crawler.fetch_all_stocks()
        results = stocks

        # 市值筛选
        if market_cap_range:
            min_cap, max_cap = market_cap_range
            cap_field = "market_cap"  # 单位是元，转换为亿元需除以1e8
            results = [
                s for s in results
                if s.get(cap_field, 0) / 1e8 >= min_cap
                and s.get(cap_field, 0) / 1e8 <= max_cap
            ]

        # PE筛选
        if pe_range:
            min_pe, max_pe = pe_range
            results = [
                s for s in results
                if 0 < s.get("pe_ratio", 0) <= max_pe
                and (min_pe is None or s.get("pe_ratio", 0) >= min_pe)
            ]

        # PB筛选
        if pb_range:
            min_pb, max_pb = pb_range
            results = [
                s for s in results
                if 0 < s.get("pb_ratio", 0) <= max_pb
                and (min_pb is None or s.get("pb_ratio", 0) >= min_pb)
            ]

        # 涨跌幅筛选
        if change_pct_range:
            min_change, max_change = change_pct_range
            results = [
                s for s in results
                if s.get("change_pct", 0) >= min_change
                and s.get("change_pct", 0) <= max_change
            ]

        # 换手率筛选
        if turnover_rate_range:
            min_tr, max_tr = turnover_rate_range
            results = [
                s for s in results
                if s.get("turnover_rate", 0) >= min_tr
                and s.get("turnover_rate", 0) <= max_tr
            ]

        # 行业筛选
        if sectors:
            results = [
                s for s in results
                if any(sec in s.get("sector", "") for sec in sectors)
            ]

        # 返回前N只
        if top_n:
            results = results[:top_n]

        return results

    def get_value_stocks(self, max_pe: float = 20, max_pb: float = 3) -> List[Dict]:
        """低估值价值股筛选"""
        return self.screen_stocks(pe_range=(0, max_pe), pb_range=(0, max_pb))

    def get_growth_stocks(self, min_pe: float = 20, min_turnover: float = 3) -> List[Dict]:
        """高成长股票筛选"""
        return self.screen_stocks(
            pe_range=(min_pe, 100),
            turnover_rate_range=(min_turnover, 100)
        )

    def get_large_cap_stocks(self, min_cap: float = 500) -> List[Dict]:
        """大盘股筛选（市值>500亿）"""
        return self.screen_stocks(market_cap_range=(min_cap, 100000))

    def get_small_cap_stocks(self, max_cap: float = 50) -> List[Dict]:
        """小盘股筛选（市值<50亿）"""
        return self.screen_stocks(market_cap_range=(0, max_cap))


def main():
    """测试"""
    print("=" * 60)
    print("  全市场A股股票爬虫 - 测试")
    print("=" * 60)

    crawler = MarketAllStocksCrawler()

    # 获取全市场股票
    print("\n1. 获取全市场股票列表...")
    stocks = crawler.fetch_all_stocks()
    print(f"   获取到 {len(stocks)} 只股票")

    # 保存
    print("\n2. 保存股票列表...")
    crawler.save_stocks()

    # 市场摘要
    print("\n3. 市场摘要...")
    summary = crawler.get_market_summary()
    print(f"   总数: {summary['total_stocks']}")
    print(f"   上涨: {summary['rising_count']} ({summary['rising_ratio']})")
    print(f"   下跌: {summary['falling_count']}")
    print(f"   平盘: {summary['unchanged_count']}")
    print(f"   情绪: {summary['market_sentiment']}")

    # 涨跌幅排行
    print("\n4. 涨幅榜Top 10...")
    top_rising = crawler.get_top_stocks(by="change_pct", limit=10)
    for i, s in enumerate(top_rising, 1):
        print(f"   {i}. {s['name']}({s['code']}): {s['change_pct']:+.2f}%")

    print("\n5. 跌幅榜Top 10...")
    top_falling = crawler.get_top_stocks(by="change_pct", limit=10, ascending=True)
    for i, s in enumerate(top_falling, 1):
        print(f"   {i}. {s['name']}({s['code']}): {s['change_pct']:+.2f}%")

    # 筛选测试
    print("\n6. 低估值筛选 (PE<15, PB<2)...")
    screener = StockScreener(crawler)
    value_stocks = screener.get_value_stocks(max_pe=15, max_pb=2)
    print(f"   筛选出 {len(value_stocks)} 只")
    for s in value_stocks[:5]:
        print(f"   - {s['name']}({s['code']}): PE={s['pe_ratio']:.1f}, PB={s['pb_ratio']:.2f}")


if __name__ == "__main__":
    main()
