# -*- coding: utf-8 -*-
"""
海外金融机构爬虫模块 v1.0 (overseas_scraper.py)

支持 8 大类 200+ 全球金融机构网站爬取，复用 http_utils v4.0 的反爬基础设施。
分类：央行 | 投资银行 | 资产管理 | 对冲基金 | 评级机构 | 交易所 | 监管机构 | 数据提供商 | 国际组织

用法：
  python -m scripts.overseas_scraper search 高盛                # 搜索机构
  python -m scripts.overseas_scraper list central_banks         # 列出某类机构
  python -m scripts.overseas_scraper crawl "Goldman Sachs"     # 爬取指定机构官网
  python -m scripts.overseas_scraper batch investment_banks    # 批量爬取某类
  python -m scripts.overseas_scraper stat                      # 统计概览
  python -m scripts.overseas_scraper top                       # 优先爬取列表（Top50）
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
OVERSEAS_FILE = DATA_DIR / "overseas_institutions.json"
CACHE_DIR = DATA_DIR / "overseas_cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# 复用已有基础
try:
    from .http_utils import http_get, random_ua, get_best_ua_for_domain
except ImportError:
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from http_utils import http_get, random_ua, get_best_ua_for_domain

CATEGORY_LABELS = {
    "central_banks": "中央银行",
    "investment_banks": "投资银行",
    "asset_managers": "资产管理公司",
    "hedge_funds": "对冲基金",
    "rating_agencies": "评级机构",
    "exchanges": "交易所",
    "regulatory_bodies": "监管机构",
    "data_providers": "数据提供商/财经媒体",
    "international_orgs": "国际组织",
}

# 海外网站专属 Accept-Language（英文优先）
OVERSEAS_ACCEPT_LANG = "en-US,en;q=0.9,zh-CN;q=0.8"

# 各区域默认域名后缀的 TLD 友好国家标记
REGION_FLAGS = {
    "US": "🇺🇸", "UK": "🇬🇧", "EU": "🇪🇺", "JP": "🇯🇵",
    "CN": "🇨🇳", "HK": "🇭🇰", "CH": "🇨🇭", "DE": "🇩🇪",
    "FR": "🇫🇷", "CA": "🇨🇦", "AU": "🇦🇺", "SG": "🇸🇬",
    "IN": "🇮🇳", "KR": "🇰🇷", "BR": "🇧🇷", "RU": "🇷🇺",
    "TW": "🇹🇼", "NZ": "🇳🇿", "FI": "🇫🇮", "INTL": "🌐",
}


@dataclass
class OverseasInstitution:
    name: str
    code: str
    website: str
    country: str
    category: str
    priority: int

    @property
    def flag(self) -> str:
        return REGION_FLAGS.get(self.country, "🏳️")


class OverseasInstitutionLoader:
    """海外机构数据加载器（单例）"""
    _instance = None
    _data: Optional[Dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> Dict:
        if self._data is not None:
            return self._data
        with open(OVERSEAS_FILE, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    def all_institutions(self) -> List[OverseasInstitution]:
        data = self.load()
        results = []
        for cat_key, cat_label in CATEGORY_LABELS.items():
            for entry in data.get(cat_key, []):
                results.append(OverseasInstitution(
                    name=entry["name"], code=entry["code"],
                    website=entry["website"], country=entry.get("country", ""),
                    category=cat_label, priority=entry.get("priority", 3),
                ))
        return results

    def by_category(self, category_key: str) -> List[OverseasInstitution]:
        data = self.load()
        cat_label = CATEGORY_LABELS.get(category_key, category_key)
        results = []
        for entry in data.get(category_key, []):
            results.append(OverseasInstitution(
                name=entry["name"], code=entry["code"],
                website=entry["website"], country=entry.get("country", ""),
                category=cat_label, priority=entry.get("priority", 3),
            ))
        return results

    def search(self, keyword: str) -> List[OverseasInstitution]:
        kw = keyword.lower()
        results = []
        for inst in self.all_institutions():
            if kw in inst.name.lower() or kw in inst.code.lower():
                results.append(inst)
        return results

    def get_stats(self) -> Dict:
        data = self.load()
        stats = {}
        total = 0
        for cat_key in CATEGORY_LABELS:
            count = len(data.get(cat_key, []))
            stats[cat_key] = count
            total += count
        stats["total"] = total
        return stats

    def top_priority(self, n: int = 50) -> List[OverseasInstitution]:
        """返回优先级最高的 n 个机构（priority 1 和 2）。"""
        all_inst = self.all_institutions()
        all_inst.sort(key=lambda x: (x.priority, x.name))
        return all_inst[:n]


class OverseasScraper:
    """海外机构专用爬虫：利用 http_utils 的反爬基础设施，自动适配英文网站。"""

    def __init__(self, timeout: int = 30, use_cache: bool = True):
        self.timeout = timeout
        self.use_cache = use_cache
        self.loader = OverseasInstitutionLoader()

    def crawl_website(self, inst: OverseasInstitution,
                      translate: bool = False) -> Dict[str, Any]:
        """爬取单个海外机构官网首页，返回结构化结果。
        translate=True 时自动翻译 title/meta_description 为中文。"""
        cache_key = inst.code + ("_zh" if translate else "")
        cache_file = CACHE_DIR / f"{cache_key}.json"

        # 读缓存
        if self.use_cache and cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < 86400:  # 24小时
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        result = {
            "code": inst.code,
            "name": inst.name,
            "website": inst.website,
            "country": inst.country,
            "category": inst.category,
            "status": "unknown",
            "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "content_length": 0,
            "title": "",
            "meta_description": "",
            "title_zh": "",
            "meta_description_zh": "",
            "error": None,
        }

        try:
            text = http_get(
                inst.website,
                headers={
                    "User-Agent": random_ua(),
                    "Accept-Language": OVERSEAS_ACCEPT_LANG,
                },
                timeout=self.timeout,
            )
            if text:
                result["status"] = "success"
                result["content_length"] = len(text)
                result["title"] = self._extract_title(text)
                result["meta_description"] = self._extract_meta_desc(text)
                # 翻译
                if translate:
                    try:
                        from .translate_utils import translate_financial_terms
                    except ImportError:
                        sys.path.insert(0, str(SKILL_DIR / "scripts"))
                        from translate_utils import translate_financial_terms
                    if result["title"]:
                        result["title_zh"] = translate_financial_terms(result["title"])
                    if result["meta_description"]:
                        result["meta_description_zh"] = translate_financial_terms(
                            result["meta_description"])
            else:
                result["status"] = "empty_response"
                result["error"] = "HTTP 请求返回空内容"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)[:200]

        # 写缓存
        if self.use_cache:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def batch_crawl(self, institutions: List[OverseasInstitution],
                    max_concurrent: int = 5) -> Dict[str, Any]:
        """批量爬取，控制并发。"""
        import concurrent.futures
        results = {"total": len(institutions), "success": 0, "failed": 0,
                   "empty": 0, "details": []}

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(max_concurrent, len(institutions))
        ) as executor:
            futures = {executor.submit(self.crawl_website, inst): inst
                       for inst in institutions}
            for future in concurrent.futures.as_completed(futures):
                inst = futures[future]
                try:
                    r = future.result()
                    results["details"].append(r)
                    if r["status"] == "success":
                        results["success"] += 1
                    elif r["status"] == "empty_response":
                        results["empty"] += 1
                    else:
                        results["failed"] += 1
                    print(f"  [{r['status']:^7}] {inst.flag} {inst.name[:30]}")
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "code": inst.code, "name": inst.name,
                        "status": "failed", "error": str(e)[:200]
                    })

        return results

    @staticmethod
    def _extract_title(html: str) -> str:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip()[:200] if m else ""

    @staticmethod
    def _extract_meta_desc(html: str) -> str:
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                html, re.IGNORECASE
            )
        return m.group(1).strip()[:300] if m else ""


# ── CLI ──────────────────────────────────────────────────────────────────

def _print_stats():
    loader = OverseasInstitutionLoader()
    stats = loader.get_stats()
    print(f"\n{'='*60}")
    print(f"  全球金融机构数据 — {stats['total']} 家 / 9 大类")
    print(f"{'='*60}")
    for cat_key, label in CATEGORY_LABELS.items():
        count = stats.get(cat_key, 0)
        bar = "█" * min(count // 3, 20)
        print(f"  {label:<14} {count:>4} 家  {bar}")
    print(f"{'='*60}")
    print(f"\n  优先级分布（1=核心 2=重要 3=补充）:")
    priority_counts = {1: 0, 2: 0, 3: 0}
    for inst in loader.all_institutions():
        priority_counts[inst.priority] = priority_counts.get(inst.priority, 0) + 1
    print(f"    🔴 P1(核心): {priority_counts[1]} 家")
    print(f"    🟡 P2(重要): {priority_counts[2]} 家")
    print(f"    🟢 P3(补充): {priority_counts[3]} 家")


def _print_list(category_key: str):
    loader = OverseasInstitutionLoader()
    insts = loader.by_category(category_key)
    label = CATEGORY_LABELS.get(category_key, category_key)
    print(f"\n  {label}（{len(insts)} 家）")
    print(f"  {'─' * 50}")
    for i, inst in enumerate(insts, 1):
        p_icon = {1: "🔴", 2: "🟡", 3: "🟢"}.get(inst.priority, "⚪")
        print(f"  [{i:>3}] {p_icon} {inst.flag} {inst.name:<40} {inst.website}")


def _print_search(keyword: str):
    loader = OverseasInstitutionLoader()
    results = loader.search(keyword)
    if not results:
        print(f"  未找到匹配「{keyword}」的机构")
        return
    print(f"\n  搜索「{keyword}」— {len(results)} 条结果")
    print(f"  {'─' * 60}")
    for inst in results:
        cat_short = {v: k for k, v in CATEGORY_LABELS.items()}.get(inst.category, "?")
        print(f"  {inst.flag} {inst.name}")
        print(f"    分类: {inst.category} | 网站: {inst.website}")


def _print_top(n: int = 50):
    loader = OverseasInstitutionLoader()
    insts = loader.top_priority(n)
    print(f"\n  Top {len(insts)} 优先爬取机构（P1+P2）")
    print(f"  {'─' * 60}")
    for i, inst in enumerate(insts, 1):
        p_star = "★" if inst.priority == 1 else "☆"
        print(f"  [{i:>3}] {p_star} {inst.flag} {inst.name:<35} [{inst.category}]")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("help", "--help", "-h"):
        print("海外金融机构爬虫 v1.0")
        print("  用法:")
        print("    python -m scripts.overseas_scraper stat                    统计概览")
        print("    python -m scripts.overseas_scraper list <分类>              列出某类机构")
        print("    python -m scripts.overseas_scraper search <关键词>          搜索机构")
        print("    python -m scripts.overseas_scraper top [N]                  Top N 优先列表")
        print("    python -m scripts.overseas_scraper crawl <机构名>           爬取官网")
        print("    python -m scripts.overseas_scraper batch <分类>             批量爬取")
        print(f"  可用分类: {', '.join(CATEGORY_LABELS.keys())}")
        return

    cmd = argv[0]
    loader = OverseasInstitutionLoader()

    if cmd == "stat":
        _print_stats()

    elif cmd == "list":
        cat = argv[1] if len(argv) > 1 else None
        if cat and cat in CATEGORY_LABELS:
            _print_list(cat)
        else:
            print(f"  可用分类: {', '.join(CATEGORY_LABELS.keys())}")

    elif cmd == "search":
        if len(argv) < 2:
            print("  用法: python -m scripts.overseas_scraper search <关键词>")
            return
        _print_search(argv[1])

    elif cmd == "top":
        n = int(argv[1]) if len(argv) > 1 else 50
        _print_top(n)

    elif cmd == "crawl":
        if len(argv) < 2:
            print("  用法: python -m scripts.overseas_scraper crawl <机构名> [--translate]")
            return
        name = argv[1]
        do_translate = "--translate" in argv
        results = loader.search(name)
        if not results:
            print(f"  未找到「{name}」")
            return
        scraper = OverseasScraper()
        for inst in results[:3]:
            r = scraper.crawl_website(inst, translate=do_translate)
            status_icon = {"success": "✅", "empty_response": "⚠️", "failed": "❌"}
            print(f"  {status_icon.get(r['status'], '?')} {r['name']}")
            print(f"    网站: {r['website']} | 状态: {r['status']}")
            if r.get("title"):
                print(f"    标题: {r['title'][:80]}")
            if r.get("title_zh"):
                print(f"    翻译: {r['title_zh'][:80]}")
            if r.get("error"):
                print(f"    错误: {r['error'][:100]}")

    elif cmd == "batch":
        if len(argv) < 2:
            print("  用法: python -m scripts.overseas_scraper batch <分类>")
            return
        cat = argv[1]
        if cat not in CATEGORY_LABELS:
            print(f"  未知分类: {cat}")
            return
        insts = loader.by_category(cat)
        print(f"\n  批量爬取: {CATEGORY_LABELS[cat]}（{len(insts)} 家）")
        scraper = OverseasScraper()
        results = scraper.batch_crawl(insts)
        print(f"\n  完成: 成功 {results['success']} | 空 {results['empty']} | 失败 {results['failed']}")


if __name__ == "__main__":
    main()
