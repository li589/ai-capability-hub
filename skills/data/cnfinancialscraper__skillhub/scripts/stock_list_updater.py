# -*- coding: utf-8 -*-
"""
A股上市公司全量名单更新器 v2.0 (v7.0.0 双源容灾版)
数据来源（自动容灾切换）：
  1. 东方财富 push2 clist 接口（多镜像轮换：push2 / 2.push2 / 3.push2 …，
     https→http 降级；对高频访问会临时软封禁 IP）
  2. 新浪财经 Market_Center 接口（node=hs_a 全量分页，独立域名互不影响）
输出：data/listed_companies.json

更新频率：每周一次（上市公司名单变动少）
"""
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from http_utils import http_get, http_get_json
    HTTP_UTILS = True
except ImportError:
    HTTP_UTILS = False

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "listed_companies.json"

_BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36"),
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json, text/plain, */*",
}

# 东财 push2 镜像池（WAF 会轮换封禁单域名/单 IP，多镜像 + 协议降级提高存活率）
_EASTMONEY_HOSTS = [
    "push2.eastmoney.com", "2.push2.eastmoney.com",
    "3.push2.eastmoney.com", "48.push2.eastmoney.com",
]
_EASTMONEY_PATH = (
    "/api/qt/clist/get?pn={page}&pz={pz}&po=1&np=1&fltt=2&invt=2"
    "&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
    "&fields=f2,f3,f5,f6,f9,f12,f13,f14,f20,f100"
)

# 新浪全量 A 股（独立域名，东财封禁时的兜底）
_SINA_COUNT_URL = ("http://vip.stock.finance.sina.com.cn/quotes_service/api/"
                   "json_v2.php/Market_Center.getHQNodeStockCount?node=hs_a")
_SINA_PAGE_URL = ("http://vip.stock.finance.sina.com.cn/quotes_service/api/"
                  "json_v2.php/Market_Center.getHQNodeData"
                  "?page={page}&num={num}&sort=symbol&asc=1&node=hs_a&symbol=&_s_r_a=page")
_SINA_HEADERS = {
    "User-Agent": _BROWSER_HEADERS["User-Agent"],
    "Referer": "https://finance.sina.com.cn/",
}


class StockListUpdater:
    """A股上市公司名单更新器（东财主源 + 新浪兜底）"""

    def __init__(self):
        self.session = None
        self.source_used = ""

    # ── 主源：东方财富（多镜像轮换）──────────────────────────
    def _eastmoney_page(self, page: int, pz: int = 500) -> Optional[Dict]:
        hosts = _EASTMONEY_HOSTS[:]
        random.shuffle(hosts)
        for host in hosts:
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}{_EASTMONEY_PATH.format(page=page, pz=pz)}"
                try:
                    if HTTP_UTILS:
                        resp = http_get(url, headers=_BROWSER_HEADERS,
                                        timeout=15, retries=0,
                                        rate_limit_delay=0.2)
                        if resp is None:
                            continue
                        data = resp.json()
                    else:
                        import requests
                        resp = requests.get(url, timeout=15, headers=_BROWSER_HEADERS)
                        data = resp.json()
                    if data.get("data") and data["data"].get("diff"):
                        return data
                except Exception:
                    continue
        return None

    @staticmethod
    def _mk_row_eastmoney(item: Dict) -> Dict:
        code = str(item.get('f12', ''))
        mkt_id = str(item.get('f13', ''))
        if mkt_id == '1' or (not mkt_id and code.startswith('6')):
            market = 'SH'
        elif mkt_id == '0':
            market = 'SZ'
        else:
            market = 'BJ'
        return {
            'code': code,
            'name': str(item.get('f14', '')),
            'market': market,
            'price': item.get('f2'),
            'change_pct': item.get('f3'),
            'volume': item.get('f5'),
            'amount': item.get('f6'),
            'market_cap': item.get('f20'),
            'pe_ttm': item.get('f9'),
            'industry': str(item.get('f100', '')),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def fetch_all_stocks_eastmoney(self) -> List[Dict]:
        all_stocks: List[Dict] = []
        page = 1
        while True:
            data = self._eastmoney_page(page)
            if data is None:
                if page == 1:
                    return []          # 首页即失败 → 整源不可用，交给新浪兜底
                break                  # 中途失败 → 返回已抓到的部分
            items = data['data']['diff']
            for item in items:
                row = self._mk_row_eastmoney(item)
                if row['code'] and row['name']:
                    all_stocks.append(row)
            total = data['data'].get('total', 0)
            print(f"  东财第 {page} 页 +{len(items)}（累计 {len(all_stocks)}/{total}）")
            if len(items) < 500 or page * 500 >= total:
                break
            page += 1
            time.sleep(0.3)
        return all_stocks

    # ── 兜底源：新浪财经（独立域名）──────────────────────────
    def _sina_count(self) -> Optional[int]:
        try:
            if HTTP_UTILS:
                resp = http_get(_SINA_COUNT_URL, headers=_SINA_HEADERS,
                                timeout=15, rate_limit_delay=0)
                return int(resp.text.strip()) if resp else None
            import requests
            r = requests.get(_SINA_COUNT_URL, timeout=15, headers=_SINA_HEADERS)
            return int(r.text.strip())
        except Exception:
            return None

    @staticmethod
    def _mk_row_sina(item: Dict) -> Dict:
        symbol = str(item.get('symbol', ''))     # 如 sh600519 / sz000001 / bj832566
        prefix = symbol[:2].lower()
        market = {'sh': 'SH', 'sz': 'SZ', 'bj': 'BJ'}.get(prefix, 'SZ')
        return {
            'code': symbol[2:],
            'name': str(item.get('name', '')),
            'market': market,
            'price': item.get('trade'),
            'change_pct': item.get('changepercent'),
            'volume': item.get('volume'),
            'amount': item.get('amount'),
            'market_cap': item.get('mktcap'),
            'pe_ttm': item.get('per'),
            'industry': '',
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def fetch_all_stocks_sina(self) -> List[Dict]:
        total = self._sina_count()
        num = 100
        # count 接口偶发不可用：改为翻页直到空页（多翻一页代价可忽略）
        pages = (total // num + 1) if total else 999
        all_stocks: List[Dict] = []
        seen = set()
        for page in range(1, pages + 1):
            try:
                if HTTP_UTILS:
                    resp = http_get(_SINA_PAGE_URL.format(page=page, num=num),
                                    headers=_SINA_HEADERS, timeout=15,
                                    rate_limit_delay=0.2)
                    if resp is None:
                        break
                    items = json.loads(resp.text.replace("var hq_str_", "")
                                       .strip())
                else:
                    import requests
                    r = requests.get(_SINA_PAGE_URL.format(page=page, num=num),
                                     timeout=15, headers=_SINA_HEADERS)
                    items = r.json()
                if not items:
                    break
                for item in items:
                    row = self._mk_row_sina(item)
                    if row['code'] and row['name'] and row['code'] not in seen:
                        seen.add(row['code'])
                        all_stocks.append(row)
                if page % 10 == 0:
                    print(f"  新浪第 {page} 页（累计 {len(all_stocks)}）")
                time.sleep(0.25)
            except Exception:
                break
        return all_stocks

    # ── 统一入口：东财 → 新浪 自动容灾 ────────────────────────
    def fetch_all_stocks(self) -> List[Dict]:
        print("主源：东方财富 push2（多镜像）…")
        stocks = self.fetch_all_stocks_eastmoney()
        if len(stocks) >= 4000:
            self.source_used = "东方财富公开API"
            return stocks
        print(f"东财仅取得 {len(stocks)} 条（疑似限流/封禁），切换新浪兜底…")
        sina = self.fetch_all_stocks_sina()
        if len(sina) > len(stocks):
            self.source_used = "新浪财经公开API"
            return sina
        self.source_used = "东方财富公开API(部分)"
        return stocks

    def save(self, stocks: List[Dict]):
        output = {
            'meta': {
                'total_count': len(stocks),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': self.source_used or '东方财富公开API',
                'markets': {
                    m: sum(1 for s in stocks if s['market'] == m)
                    for m in ('SH', 'SZ', 'BJ')
                }
            },
            'stocks': stocks
        }
        OUTPUT_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False)
        print(f"保存 {len(stocks)} 只股票到 {OUTPUT_FILE}")

    def run(self):
        print(f"[{datetime.now():%Y-%m-%d %H:%M}] 开始更新A股上市公司名单...")
        stocks = self.fetch_all_stocks()
        if stocks:
            self.save(stocks)
            print(f"完成: {len(stocks)} 只（来源: {self.source_used}）")
            return {'success': True, 'count': len(stocks), 'source': self.source_used}
        return {'success': False, 'count': 0, 'source': ''}


if __name__ == "__main__":
    updater = StockListUpdater()
    result = updater.run()
    print(json.dumps(result, ensure_ascii=False))
