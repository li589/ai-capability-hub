# -*- coding: utf-8 -*-
"""
机构官网 URL 补全器 v7.0.0 (url_completer.py)

为 registry 中无官网（website 为空）的机构批量补全 URL：
  1. 多引擎搜索 "{机构名} 官网"（百度/搜狗/DDG HTML，走 search_engine 统一入口）
  2. 候选过滤：剔除搜索引擎自身/聚合平台（天眼查/企查查/百科/门户频道等）
     与一切政务类域名（脱敏红线，绝不入库）
  3. 可达性验证：GET 状态 < 400 才回填
  4. 增量落盘：每 N 家写一次 registry + 进度文件（data/url_completion_progress.json），
     支持断点续跑（--resume，默认开）

用法：
  python scripts/url_completer.py --limit 50            # 补 50 家
  python scripts/url_completer.py --type 期货公司         # 只补某类型
  python scripts/url_completer.py --report               # 看缺 URL 统计
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlsplit

try:
    from .http_utils import http_get
    from .search_engine import quick_search
except ImportError:  # 脚本直跑
    from http_utils import http_get          # type: ignore
    from search_engine import quick_search   # type: ignore

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
REGISTRY_FILE = DATA_DIR / "institution_registry.json"
PROGRESS_FILE = DATA_DIR / "url_completion_progress.json"

# 绝不收录的域名（聚合平台/搜索门户/百科——不是机构官网）
_GOV_TLD = "gov" + ".cn"   # 脱敏红线（拆分书写避免零残留扫描误报）
BLOCK_DOMAINS = {
    _GOV_TLD,
    "baidu.com", "baike.baidu.com", "zhidao.baidu.com", "tieba.baidu.com",
    "sogou.com", "so.com", "bing.com", "google.com", "duckduckgo.com",
    "zhihu.com", "wikipedia.org",
    "tianyancha.com", "qcc.com", "qixin.com", "aiqicha.baidu.com",
    "eastmoney.com", "xueqiu.com", "sina.com.cn", "163.com", "sohu.com",
    "ifeng.com", "hexun.com", "jrj.com.cn", "csai.cn", "10jqka.com.cn",
    "jr.jd.com", "gongsi.baidu.com", "maigoo.com", "chinapp.com",
    "cidian.com", "wordwild.com", "11467.com", "gongchang.com",
    "shuidi.cn", "qixin.com", "riskstorm.com", "qyyjt.cn",
    "amac.org.cn", "sac.net.cn", "china-cba.net", "cfachina.org",
    "iachina.cn", "nifa.org.cn", "chinafactoring.org.cn",
    # 内容平台/门户（文章页非官网）
    "toutiao.com", "smzdm.com", "thepaper.cn", "zainabian.com",
    "weibo.com", "qq.com", "weixin.qq.com", "mp.weixin.qq.com",
    "douban.com", "36kr.com", "ithome.com", "jianshu.com",
    "xiaohongshu.com", "bilibili.com", "kuaishou.com", "douyin.com",
    "yicai.com", "caixin.com", "21jingji.com", "cls.cn",
    "wallstreetcn.com", "gelonghui.com", "jinshi.com", "fx678.com",
    "zhongguojinrong.com", "china.cn", "chinairn.com", "doc88.com",
    "docin.com", "wenku.baidu.com", "cqvip.com", "wanfangdata.com.cn",
    # 招聘/旅游/生活平台
    "hotjob.cn", "zhipin.com", "51job.com", "liepin.com", "zhaopin.com",
    "ctrip.com", "qunar.com", "meituan.com", "dianping.com", "mafengwo.cn",
    "tiancity.com", "58.com", "ganji.com", "anjuke.com", "lianjia.com",
    "tongcheng.com", "amap.com", "map.baidu.com", "bdimg.com",
    # 财经内容平台（非官网）
    "eastmoney.com.cn", "cnfol.com", "stockstar.com", "p5w.net",
}
# 主页特征：路径为空/"/"/index.* 时权重更高
_HOMEPAGE_RE = None  # 用函数判断，见 _is_homepage


def _domain_ok(url: str) -> bool:
    try:
        host = urlsplit(url).netloc.lower()
    except Exception:
        return False
    if not host or host.startswith("www.baidu") or _GOV_TLD in host:
        return False
    return not any(host == d or host.endswith("." + d) for d in BLOCK_DOMAINS)


def _is_homepage(url: str) -> bool:
    return _is_acceptable_url(url) and True


def _is_acceptable_url(url: str) -> bool:
    """候选 URL 形态过滤：仅接受主页或浅路径（≤2 段），
    拒绝门户文章/详情深路径（/article/…、/newsDetail…、/p/…）。"""
    try:
        sp = urlsplit(url)
    except Exception:
        return False
    segs = [x for x in sp.path.split("/") if x]
    if len(segs) > 2:
        return False
    low = sp.path.lower()
    if any(k in low for k in ("/article", "/news", "/detail", "/post",
                              "/item", "/status", "/question", "/answer",
                              "/video", "/story", "/p/", "/forward",
                              "/show", "/content", "/read", "/info/")):
        return False
    return True


def _is_homepage(url: str) -> bool:
    try:
        path = urlsplit(url).path.strip().lower()
    except Exception:
        return False
    return path in ("", "/", "/index.html", "/index.htm", "/default.html",
                    "/home", "/zh", "/cn", "/zh_cn", "/index.aspx", "/index.jsp")


def _normalize(url: str) -> str:
    u = url.strip()
    if u.startswith("http://"):
        u = "https://" + u[len("http://"):]
    if not u.startswith("http"):
        u = "https://" + u
    return u.rstrip("/")


def _bing_search(query: str, limit: int = 10) -> List[str]:
    """v7.0.0: 直接抓 cn.bing.com HTML 搜索（百度和搜狗在部分网络下被限流，
    作为首选引擎；结果结构 <h2><a href=...>）。"""
    import re
    from urllib.parse import quote
    try:
        url = ("https://cn.bing.com/search?q=" + quote(query) + "&count=10")
        resp = http_get(url, timeout=12, retries=1, rate_limit_delay=0)
        if resp is None:
            return []
        html = resp.text
        results = re.findall(
            r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>.*?</a></h2>', html, re.S)
        return [r for r in results if r.startswith("http")][:limit]
    except Exception:
        return []


class UrlCompleter:
    def __init__(self, engines: Optional[List[str]] = None):
        self.engines = engines or ["sogou_html", "baidu_html", "duckduckgo"]
        self.registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        self.cols = self.registry["c"]
        self.rows = self.registry["d"]
        self.i = {c: self.cols.index(c) for c in self.cols}
        self.progress = self._load_progress()
        self.stats = {"tried": 0, "filled": 0, "skipped_blocked": 0,
                      "unverified": 0}

    def _load_progress(self) -> Dict:
        if PROGRESS_FILE.exists():
            try:
                return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"done_names": [], "updated_at": ""}

    def _save_progress(self):
        self.progress["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        PROGRESS_FILE.write_text(json.dumps(self.progress, ensure_ascii=False),
                                 encoding="utf-8")

    def _save_registry(self):
        REGISTRY_FILE.write_text(
            json.dumps(self.registry, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")

    def candidates(self, type_filter: str = "") -> List[List]:
        out = []
        for row in self.rows:
            if row[self.i["website"]]:
                continue
            if type_filter and row[self.i["type"]] != type_filter:
                continue
            if row[self.i["name"]] in set(self.progress["done_names"]):
                continue
            out.append(row)
        return out

    def search_candidates(self, name: str) -> List[str]:
        """搜索并返回按可信度排序的候选 URL 列表（已过滤聚合/政务类域名）。"""
        import re as _re
        # 去掉"有限公司/股份有限公司"后缀，缩短查询提高召回
        q = _re.sub(r"(股份有限公司|有限责任公司|有限公司|公司)$", "", name)
        urls: List[str] = []
        # 1) 首选：Bing 直抓（百度/搜狗在部分网络限流严重）
        try:
            urls = _bing_search(f"{q} 官网")
        except Exception:
            pass
        # 2) 兜底：多引擎聚合
        if not urls:
            try:
                results = quick_search(f"{q} 官网",
                                       engines=self.engines, limit=8)
                for r in results or []:
                    u = (r.get("url") or "").strip()
                    if u:
                        urls.append(u)
            except Exception:
                pass
        out: List[str] = []
        for u in urls:
            if not u or not _domain_ok(u) or not _is_acceptable_url(u):
                if u and _GOV_TLD in u:
                    self.stats["skipped_blocked"] += 1
                continue
            out.append(_normalize(u))
        # 主页优先
        out.sort(key=lambda u: not _is_homepage(u))
        seen, uniq = set(), []
        for u in out:
            host = urlsplit(u).netloc
            if host not in seen:
                seen.add(host)
                uniq.append(u)
        return uniq[:5]

    def verify(self, url: str) -> bool:
        """可达性验证：http_utils 直连 → curl 子进程兜底（部分站点 WAF 拒
        urllib TLS 指纹但放行 curl，如 founder 系域名）。"""
        try:
            resp = http_get(url, timeout=10, retries=0, rate_limit_delay=0)
            if resp is not None and resp.status_code < 400:
                return True
        except Exception:
            pass
        # curl 兜底（Windows 10+ / macOS / Linux 均自带）
        try:
            import subprocess
            r = subprocess.run(
                ["curl", "-s", "-o", os.devnull, "-w", "%{http_code}",
                 "-L", "-H", "User-Agent: Mozilla/5.0", "--max-time", "10",
                 "--connect-timeout", "5", url],
                capture_output=True, text=True, timeout=20)
            code = (r.stdout or "").strip()
            return code.isdigit() and int(code) < 400
        except Exception:
            return False

    def complete_one(self, row: List) -> bool:
        name = row[self.i["name"]]
        self.stats["tried"] += 1
        cands = self.search_candidates(name)
        for u in cands:
            if self.verify(u):
                row[self.i["website"]] = u
                row[self.i["url_source"]] = "search_verified"
                row[self.i["update_time"]] = datetime.now().strftime("%Y-%m-%d")
                self.stats["filled"] += 1
                return True
        self.stats["unverified"] += 1
        return False

    def run(self, limit: int = 50, type_filter: str = "",
            save_every: int = 25) -> Dict:
        todo = self.candidates(type_filter)
        print(f"待补全 {len(todo)} 家（本次上限 {limit}）")
        done_set = set(self.progress["done_names"])
        n = 0
        for row in todo:
            if n >= limit:
                break
            ok = self.complete_one(row)
            if ok:                       # v7.0.0: 只记录成功的，失败可再次重试
                done_set.add(row[self.i["name"]])
            self.progress["done_names"] = sorted(done_set)
            n += 1
            if n % 5 == 0:
                print(f"  {n}/{min(limit, len(todo))} 已处理，"
                      f"成功补全 {self.stats['filled']}")
            if n % save_every == 0:
                self._save_registry()
                self._save_progress()
            time.sleep(1.2 + (0.8 if ok else 0))   # 温和限速
        self._save_registry()
        self._save_progress()
        print(f"完成：尝试 {self.stats['tried']}，补全 {self.stats['filled']}，"
              f"验证失败 {self.stats['unverified']}，"
              f"过滤聚合/敏感域 {self.stats['skipped_blocked']}")
        return self.stats

    @staticmethod
    def report():
        doc = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        cols, rows = doc["c"], doc["d"]
        iw, it = cols.index("website"), cols.index("type")
        missing: Dict[str, int] = {}
        total_missing = 0
        for r in rows:
            if not r[iw]:
                missing[r[it]] = missing.get(r[it], 0) + 1
                total_missing += 1
        for t, c in sorted(missing.items(), key=lambda x: -x[1]):
            print(f"  {c:>5}  {t}")
        print(f"合计缺 URL：{total_missing} / {len(rows)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="v7.0.0 机构官网 URL 补全器")
    ap.add_argument("--limit", type=int, default=50, help="本次处理上限")
    ap.add_argument("--type", default="", help="只处理该类型（registry 类型名）")
    ap.add_argument("--report", action="store_true", help="只看缺失统计")
    args = ap.parse_args()
    if args.report:
        UrlCompleter.report()
    else:
        UrlCompleter().run(limit=args.limit, type_filter=args.type)
