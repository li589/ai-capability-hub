# -*- coding: utf-8 -*-
"""浏览器资讯获取引擎 v1.0 — 全球金融市场情绪聚合"""
import re, time, urllib.request, urllib.parse, ssl
from typing import List, Dict
from datetime import datetime

HAS_PLAYWRIGHT = False
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    pass


class GlobalSentimentEngine:
    SOURCES = {
        "cn_guba": "https://guba.eastmoney.com/list,zssh000001.html",
        "cn_xueqiu": "https://xueqiu.com/k?q={keyword}",
        "cn_cls": "https://www.cls.cn/searchPage?keyword={keyword}",
        "us_reddit": "https://www.reddit.com/r/wallstreetbets/search.json?q={keyword}",
        "us_yahoo": "https://finance.yahoo.com/quote/{symbol}",
        "global_reuters": "https://www.reuters.com/search/news?blob={keyword}",
        "policy_fed": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
        "policy_pboc": "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
        "policy_csrc": "http://www.csrc.gov.cn/csrc/c100028/common_list.shtml",
        "policy_sec": "https://www.sec.gov/news/pressreleases",
    }
    BULLISH_CN = ["暴涨","涨停","利好","买入","增持","突破","牛"]
    BEARISH_CN = ["暴跌","跌停","利空","卖出","减持","破位","熊"]
    BULLISH_EN = ["breakout","bullish","buy","upgrade","beat","strong","moon"]
    BEARISH_EN = ["crash","bearish","sell","downgrade","miss","weak","dump"]

    def __init__(self, use_browser=False, headless=True):
        self.use_browser = use_browser and HAS_PLAYWRIGHT
        self.headless = headless
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False; self.ctx.verify_mode = ssl.CERT_NONE
        self._cache = {}

    def crawl_market_sentiment(self, markets=None, keyword="", limit=30):
        if markets is None: markets = ["cn","us","global"]
        results = {"timestamp": datetime.now().isoformat(), "markets": {}}
        for market in markets:
            sources = self._src_for(market)
            articles = []
            for sid in sources[:3]:
                articles.extend(self._fetch(sid, keyword, max(5, limit//3)))
            results["markets"][market] = {"count":len(articles), "sentiment":self._agg(articles), "top":articles[:10]}
        all_arts = [a for m in results["markets"].values() for a in m.get("top",[])]
        results["overall"] = {"total":len(all_arts), "sentiment":self._agg(all_arts), "signal":self._sig(all_arts)}
        return results

    def _src_for(self, market):
        m = {"cn":["cn_guba","cn_xueqiu","cn_cls"], "us":["us_reddit","us_yahoo"],
             "global":["global_reuters"], "policy":["policy_fed","policy_pboc","policy_csrc","policy_sec"]}
        return m.get(market, m["global"])

    def _fetch(self, src_id, keyword, limit):
        if src_id in self._cache and time.time()-self._cache[src_id].get("_ts",0)<300:
            return self._cache[src_id]["articles"][:limit]
        url = self.SOURCES.get(src_id,"").format(keyword=urllib.parse.quote(keyword or ""), symbol=keyword or "SPY")
        articles = []
        try:
            articles = self._browser_fetch(url) if self.use_browser else self._http_fetch(url)
            tag = "guba" if "guba" in src_id else ("Reddit" if "reddit" in src_id else "")
            if tag:
                for a in articles: a["source"] = tag
        except Exception:
            pass
        self._cache[src_id] = {"articles":articles, "_ts":time.time()}
        return articles[:limit]

    def _http_fetch(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Accept-Language":"zh-CN,zh;q=0.9"})
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                raw = resp.read()
                text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        except Exception:
            return []
        return self._extract(text, url)

    def _browser_fetch(self, url):
        if not HAS_PLAYWRIGHT: return []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                text = page.content()
                browser.close()
        except Exception:
            return []
        return self._extract(text, url)

    def _extract(self, html, base_url):
        articles, seen = [], set()
        for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{5,150})</a>', html, re.I):
            href, title = m.group(1), re.sub(r"<[^>]+>","",m.group(2)).strip()
            if title and len(title)>5 and href not in seen:
                seen.add(href)
                if not href.startswith("http"): href = urllib.parse.urljoin(base_url, href)
                articles.append({"title":title,"url":href,"sentiment":self._cls(title)})
                if len(articles)>=50: break
        return articles

    def _cls(self, text):
        t = text.lower()
        bc = sum(1 for kw in self.BULLISH_CN if kw in text) + sum(1 for kw in self.BULLISH_EN if kw in t)
        br = sum(1 for kw in self.BEARISH_CN if kw in text) + sum(1 for kw in self.BEARISH_EN if kw in t)
        return "positive" if bc>br else ("negative" if br>bc else "neutral")

    def _agg(self, articles):
        p = sum(1 for a in articles if a.get("sentiment")=="positive")
        n = sum(1 for a in articles if a.get("sentiment")=="negative")
        t = len(articles)
        return {"positive":p,"negative":n,"positive_pct":round(p/t*100,1) if t else 0,"bullish_index":round((p-n)/t*100,1) if t else 0}

    def _sig(self, articles):
        idx = self._agg(articles).get("bullish_index",0)
        if idx>20: return "bullish"
        if idx<-20: return "bearish"
        if idx>5: return "cautiously_bullish"
        if idx<-5: return "cautiously_bearish"
        return "neutral"

    def get_policy_updates(self, regulators=None, limit=20):
        if regulators is None: regulators = ["fed","pboc","sec"]
        return {r.upper():{"count":len(a:=self._fetch("policy_"+r,"",limit)),"latest":a[:5]} for r in regulators}

    def crawl_stock_forum(self, code, limit=20):
        prefix = "sh" if code.startswith(("6","5","9")) else "sz"
        arts = self._http_fetch(f"https://guba.eastmoney.com/list,{prefix}{code}.html")[:limit*2]
        for a in arts: a["source"] = "guba"
        return {"code":code,"count":len(arts),"sentiment":self._agg(arts),"hot":arts[:10]}


def get_global_sentiment(keyword=""):
    return GlobalSentimentEngine().crawl_market_sentiment(keyword=keyword)

def get_policy_updates():
    return GlobalSentimentEngine().get_policy_updates()
