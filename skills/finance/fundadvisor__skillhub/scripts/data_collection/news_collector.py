#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财经新闻综合抓取 v1.0 — 零第三方依赖，适配fund-advisor独立运行
数据源：东方财富快讯、新浪财经、凤凰财经
"""
from __future__ import annotations
import sys, re, time, json, html as html_module
from pathlib import Path

# 路径推断：从 data_collection/ 到 fund-advisor/
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_COLLECTION_DIR = SCRIPT_DIR
FUND_ADVISOR_DIR = DATA_COLLECTION_DIR.parent.parent
sys.path.insert(0, str(DATA_COLLECTION_DIR))

try:
    from crawl_utils import safe_request
except ImportError:
    # 独立运行时内联工具函数
    import urllib.request, urllib.error
    def safe_request(url, timeout=10):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.eastmoney.com/'
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            return None


# ── 情感分析词库 ───────────────────────────────────────────────────
POSITIVE = [
    "上涨", "大涨", "飙升", "涨停", "创新高", "突破", "增长", "增持", "买入",
    "超预期", "首推", "强烈推荐", "积极", "看好", "推荐", "利好", "分红", "盈利",
    "牛市", "反弹", "上升", "强劲", "加码", "扩大", "支持", "促进", "开放",
    "扩张", "复苏", "回暖", "景气", "量价齐升", "业绩亮眼", "订单大增",
]
NEGATIVE = [
    "下跌", "大跌", "暴跌", "跌停", "创新低", "亏损", "减持", "卖出", "警示",
    "低于预期", "风险", "警示", "谨慎", "回避", "调查", "整改", "处罚",
    "熊市", "下滑", "疲软", "收紧", "加强监管", "严格", "控制", "抑制",
    "整顿", "违规", "警告", "减持", "爆雷", "造假", "退市", "清仓",
]

# ── 新闻分类词库 ───────────────────────────────────────────────────
MACRO_KWS = [
    "央行", "降准", "加息", "货币", "财政", "经济", "CPI", "PPI", "GDP", "M2",
    "美联储", "国务院", "发改委", "财政部", "商务部", "统计局", "社融", "LPR",
    "信贷", "外汇", "人民币", "汇率", "美债", "衰退", "通胀", "缩表",
]
INDUSTRY_KWS = {
    "新能源": ["新能源", "光伏", "风电", "储能", "电动车", "锂电", "电池", "新能源汽车", "氢能", "碳中和"],
    "医药": ["医药", "中药", "医疗器械", "创新药", "疫苗", "医保", "医疗", "生物医药", "CRO"],
    "科技": ["半导体", "芯片", "AI", "人工智能", "软件", "5G", "华为", "大模型", "算力", "算法"],
    "消费": ["白酒", "食品", "饮料", "家电", "汽车", "零售", "消费", "餐饮", "旅游", "免税"],
    "金融": ["银行", "保险", "券商", "证券", "信托", "基金", "私募", "公募"],
    "地产": ["房地产", "地产", "万科", "保利", "碧桂园", "楼市", "房价", "限购", "降息"],
    "军工": ["军工", "国防", "航天", "航空", "导弹", "舰船", "无人机"],
    "农业": ["农业", "粮食", "养猪", "种植", "农产品", "猪周期"],
}
MARKET_KWS = [
    "证监会", "IPO", "注册制", "退市", "量化", "做空", "涨停", "北向", "外资",
    "ETF", "融资", "融券", "做多", "建仓", "清仓", "加仓", "减仓",
]
OVERSEAS_KWS = [
    "美股", "港股", "欧股", "日经", "纳斯达克", "道琼斯", "标普", "亚太",
    "原油", "黄金", "美联储", "欧佩克", "OPEC", "美元", "日元", "英镑",
]


def sentiment_score(text):
    pos = sum(1 for w in POSITIVE if w in text)
    neg = sum(1 for w in NEGATIVE if w in text)
    t = pos + neg
    if t == 0:
        return 0
    return int((pos - neg) / t * 100)


def classify_news(text):
    cats = []
    if any(k in text for k in MACRO_KWS):
        cats.append("宏观")
    if any(k in text for k in OVERSEAS_KWS):
        cats.append("海外")
    if any(k in text for k in MARKET_KWS):
        cats.append("市场")
    for cat, kws in INDUSTRY_KWS.items():
        if any(k in text for k in kws):
            cats.append(cat)
    return cats if cats else ["其他"]


# ── 数据源 1：东方财富快讯 API ─────────────────────────────────────
def fetch_eastmoney_news():
    """东方财富快讯 — JSONP API，每页20条，实时更新"""
    news = []
    for page in range(1, 4):
        url = f"https://newsapi.eastmoney.com/kuaixun/v1/getlist_101_ajaxResult_20_{page}_.html"
        data = safe_request(url, timeout=8)
        if not data:
            break
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
        text = re.sub(r'^var ajaxResult=', '', text)
        try:
            obj = json.loads(text)
        except Exception:
            break
        items = obj.get("LivesList", [])
        if not items:
            break
        for it in items:
            title = it.get("title", "").strip()
            url_w = it.get("url_w", "")
            stime = it.get("showtime", "")
            if not title or len(title) < 4:
                continue
            cats = classify_news(title)
            score = sentiment_score(title)
            news.append({
                "title": title,
                "url": url_w,
                "source": "东方财富",
                "sentiment": score,
                "category": cats,
                "time": stime,
            })
        time.sleep(0.15)
    return news


# ── 数据源 2：新浪财经滚动页 ───────────────────────────────────────
def fetch_sina_news():
    """新浪财经滚动页"""
    data = safe_request("https://finance.sina.com.cn/roll/index.shtml", timeout=8)
    if not data:
        return []
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
    return _extract_links(text, "finance.sina.com.cn", "新浪财经", min_len=8, max_count=20)


# ── 数据源 3：凤凰财经 ──────────────────────────────────────────────
def fetch_phoenix_news():
    """凤凰财经"""
    data = safe_request("https://finance.ifeng.com/", timeout=8)
    if not data:
        return []
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
    return _extract_links(text, "finance.ifeng.com", "凤凰财经", min_len=8, max_count=15)


def _extract_links(data, domain, source, min_len=6, max_count=20):
    """从 HTML 提取 <a> 链接标题"""
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    news = []
    seen = set()
    chinese_re = re.compile(r"[一-鿿]")
    noise = ["洁丽雅", "豪门内斗", "热搜", "打骨折", "手机", "降价", "小米", "苹果",
             "肯德基", "网红", "八卦", "明星", "吃播", "带货", "-token"]
    pos = 0
    while len(news) < max_count * 3 and pos < len(data) - 50:
        idx_a = data.lower().find("<a href=", pos)
        if idx_a < 0:
            break
        q1 = data[idx_a + 9]
        end_q = data.find(q1, idx_a + 10)
        if end_q < 0:
            pos = idx_a + 1
            continue
        url = data[idx_a + 10:end_q]
        if not url or url.startswith(("javascript:", "#", "/")) or "://" not in url:
            pos = idx_a + 1
            continue
        if url.startswith("ttps://"):
            url = "h" + url
        elif url.startswith("tps://"):
            url = "ht" + url
        if domain not in url.lower():
            pos = idx_a + 1
            continue
        end_a = data.find("</a>", end_q)
        if end_a < 0:
            pos = idx_a + 1
            continue
        inner_start = data.find(">", end_q)
        if inner_start < 0 or inner_start >= end_a:
            pos = idx_a + 1
            continue
        raw = data[inner_start + 1:end_a]
        title = re.sub(r"<[^>]*>", "", raw)
        title = re.sub(r"[\s\n\r\t]+", " ", title).strip()
        title = html_module.unescape(title)
        pos = end_a + 4
        if len(title) < min_len or not chinese_re.search(title):
            continue
        if any(b in title for b in ["登录", "注册", "客户端", "下载", "app", "javascript", "广告"]):
            continue
        if any(b in title for b in noise):
            continue
        if title in seen:
            continue
        seen.add(title)
        cats = classify_news(title)
        score = sentiment_score(title)
        news.append({
            "title": title,
            "url": url,
            "source": source,
            "sentiment": score,
            "category": cats,
        })
    return news[:max_count]


# ── 主入口 ─────────────────────────────────────────────────────────
def crawl_all_news():
    """综合三大数据源，按时间/相关度去重"""
    all_news = []
    all_news.extend(fetch_eastmoney_news())
    time.sleep(0.2)
    all_news.extend(fetch_sina_news())
    time.sleep(0.2)
    all_news.extend(fetch_phoenix_news())
    seen, unique = set(), []
    for n in all_news:
        key = n["title"].strip()
        if key not in seen:
            seen.add(key)
            unique.append(n)
    return unique


def news_to_markdown(news_list):
    lines = ["| 来源 | 类别 | 情感 | 标题 |\n", "|------|------|------|------|\n"]
    for n in news_list[:30]:
        cats = "/".join(n.get("category", [])[:2])
        sent = n["sentiment"]
        sign = "+" if sent > 0 else "-" if sent < 0 else ""
        lines.append(f"| {n['source']} | {cats} | {sign}{sent} | [{n['title'][:40]}]({n['url']}) |\n")
    return "".join(lines)


if __name__ == "__main__":
    from datetime import datetime as dt
    _today = dt.now().strftime("%Y%m%d")
    data_dir = FUND_ADVISOR_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("抓取财经新闻...")
    news = crawl_all_news()
    print(f"共 {len(news)} 条")
    cats = {}
    for n in news:
        c = n.get("category", ["其他"])[0] if isinstance(n.get("category"), list) else "其他"
        cats[c] = cats.get(c, 0) + 1
    print("分类:", cats)

    _out = data_dir / f"news_{_today}.json"
    _out.write_text(json.dumps({"date": _today, "articles": news}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[保存] {_out.name}")

    out = data_dir / "news_latest.json"
    out.write_text(json.dumps(news, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存 news_latest.json ({len(news)} 条)")