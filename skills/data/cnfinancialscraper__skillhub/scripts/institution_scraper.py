# -*- coding: utf-8 -*-
"""
金融机构网站爬取器
支持基金公司、券商、银行、第三方销售机构的金融产品爬取
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import concurrent.futures

try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright, Page, Locator
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 数据目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
INSTITUTIONS_FILE = SKILL_DATA_DIR / "institutions.json"

# 请求限流
DEFAULT_DELAY = 2  # 秒
MAX_RETRIES = 3


class InstitutionLoader:
    """机构信息加载器"""

    _instance = None
    _institutions = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if InstitutionLoader._institutions is None:
            self._load()

    def _load(self):
        """加载机构数据"""
        if INSTITUTIONS_FILE.exists():
            with open(INSTITUTIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                InstitutionLoader._institutions = data
        else:
            InstitutionLoader._institutions = {"error": "机构配置文件不存在"}

    def get_all_fund_companies(self) -> List[Dict]:
        """获取所有基金公司"""
        return InstitutionLoader._institutions.get("fund_companies", [])

    def get_all_securities(self) -> List[Dict]:
        """获取所有券商"""
        return InstitutionLoader._institutions.get("securities_companies", [])

    def get_all_banks(self) -> List[Dict]:
        """获取所有银行"""
        return InstitutionLoader._institutions.get("banks", [])

    def get_all_third_party(self) -> List[Dict]:
        """获取所有第三方销售机构"""
        return InstitutionLoader._institutions.get("third_party_platforms", [])

    def get_all_institutions(self) -> List[Tuple[str, List[Dict]]]:
        """获取所有机构（按类型分组）"""
        inst = InstitutionLoader._institutions
        return [
            ("基金公司", inst.get("fund_companies", [])),
            ("券商", inst.get("securities_companies", [])),
            ("银行", inst.get("banks", [])),
            ("第三方销售", inst.get("third_party_platforms", []))
        ]

    def get_platform_patterns(self) -> Dict:
        """获取URL匹配模式"""
        return InstitutionLoader._institutions.get("platform_patterns", {})

    def identify_platform(self, url: str) -> Tuple[str, str, str]:
        """
        识别URL所属平台

        Returns:
            (platform_name, platform_code, institution_type)
        """
        url_lower = url.lower()
        patterns = self.get_platform_patterns()

        # 检查是否为基金产品页面
        for pattern in patterns.get("fund_patterns", []):
            if re.search(pattern, url_lower):
                return ("天天基金", "TTF", "fund_platform")

        # 检查是否为ETF
        for pattern in patterns.get("etf_patterns", []):
            if re.search(pattern, url_lower):
                return ("ETF平台", "ETF", "etf_platform")

        # 检查是否为FOF
        for pattern in patterns.get("fof_patterns", []):
            if re.search(pattern, url_lower):
                return ("FOF平台", "FOF", "fof_platform")

        # 检查是否为组合
        for pattern in patterns.get("portfolio_patterns", []):
            if re.search(pattern, url_lower):
                return ("组合平台", "PORTFOLIO", "portfolio_platform")

        # 从机构URL匹配
        for inst_type, inst_list in self.get_all_institutions():
            for inst in inst_list:
                home = inst.get("home", "").lower()
                if home and home in url_lower:
                    return (inst["name"], inst["code"], inst_type)

        # 手动平台识别
        if "eastmoney" in url_lower:
            return ("东方财富", "EM", "comprehensive")
        elif "10jqka" in url_lower:
            return ("同花顺", "THS", "comprehensive")
        elif "xueqiu" in url_lower:
            return ("雪球", "XQ", "social")
        elif "qieman" in url_lower:
            return ("且慢", "QM", "advisor")
        elif "danjuan" in url_lower:
            return ("蛋卷基金", "DJ", "advisor")
        elif "fund123" in url_lower:
            return ("蚂蚁基金", "MYF", "third_party")

        return ("未知平台", "UNKNOWN", "unknown")


class InstitutionScraper:
    """金融机构产品爬取器"""

    def __init__(self):
        self.loader = InstitutionLoader()
        self.fetcher = None
        if SCRAPLING_AVAILABLE:
            self.fetcher = StealthyFetcher()
        self.last_request_time = 0
        self.request_delay = DEFAULT_DELAY

    def _rate_limit(self):
        """请求限流"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def scrape_institution_product_list(self, institution: Dict,
                                       product_type: str = "fund") -> Dict[str, Any]:
        """
        爬取机构的产品列表

        Args:
            institution: 机构信息
            product_type: 产品类型 (fund, etf, fof)

        Returns:
            产品列表
        """
        result = {
            "institution": institution.get("name", ""),
            "institution_code": institution.get("code", ""),
            "product_type": product_type,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "products": [],
            "error": None
        }

        fund_list_url = institution.get("fund_list", "")
        if not fund_list_url:
            result["error"] = "未提供产品列表URL"
            return result

        self._rate_limit()

        try:
            if self.fetcher:
                page = self.fetcher.fetch(fund_list_url, headless=True)
                # 提取产品代码和名称
                products = self._extract_product_list(page, institution, product_type)
                result["products"] = products
            else:
                result["error"] = "Scrapling未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _extract_product_list(self, page: Selector,
                             institution: Dict,
                             product_type: str) -> List[Dict]:
        """从页面提取产品列表"""
        products = []
        pattern = institution.get("product_pattern", r'/(\d{6})\.html')

        # 尝试提取所有链接
        links = page.css("a[href*='.html']")

        seen_codes = set()
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text().strip()

                # 匹配产品代码
                code_match = re.search(pattern, href)
                if code_match:
                    code = code_match.group(1)
                    if code not in seen_codes:
                        seen_codes.add(code)
                        products.append({
                            "code": code,
                            "name": text or code,
                            "url": href if href.startswith("http") else f"{institution.get('home', '')}{href}"
                        })
            except:
                continue

        return products

    def scrape_product_detail(self, url: str,
                             product_type: str = "fund") -> Dict[str, Any]:
        """
        爬取产品详情

        Args:
            url: 产品URL
            product_type: 产品类型

        Returns:
            产品详情
        """
        from web_parser import parse_financial_product
        return parse_financial_product(url, product_type)

    def batch_scrape_institution(self,
                                institution: Dict,
                                product_type: str = "fund",
                                max_products: int = 50,
                                delay: float = None) -> List[Dict]:
        """
        批量爬取机构产品

        Args:
            institution: 机构信息
            product_type: 产品类型
            max_products: 最大产品数
            delay: 请求间隔

        Returns:
            产品详情列表
        """
        if delay:
            self.request_delay = delay

        # 先获取产品列表
        list_result = self.scrape_institution_product_list(institution, product_type)
        if list_result.get("error"):
            return [{"error": list_result["error"]}]

        products = list_result.get("products", [])[:max_products]
        results = []

        for product in products:
            url = product.get("url", "")
            if url:
                try:
                    detail = self.scrape_product_detail(url, product_type)
                    results.append(detail)
                    time.sleep(self.request_delay)
                except Exception as e:
                    results.append({"error": str(e), "product": product})

        return results


class UniversalScraper:
    """通用爬取器 - 适配所有金融机构"""

    def __init__(self):
        self.loader = InstitutionLoader()
        self.scraper = InstitutionScraper()

    def scrape_any(self, url: str,
                   product_type: str = "auto",
                   use_dynamic: bool = False) -> Dict[str, Any]:
        """
        通用爬取入口 - 自动识别平台

        Args:
            url: 目标URL
            product_type: 产品类型 (fund, etf, fof, stock, advisor, auto)
            use_dynamic: 是否使用动态渲染

        Returns:
            爬取结果
        """
        platform_name, platform_code, inst_type = self.loader.identify_platform(url)

        result = {
            "url": url,
            "platform": platform_name,
            "platform_code": platform_code,
            "institution_type": inst_type,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": {}
        }

        from web_parser import parse_financial_product
        data = parse_financial_product(url, product_type, use_dynamic)
        result["data"] = data

        return result

    def scrape_by_institution(self,
                            institution_type: str,
                            institution_code: str = None,
                            max_products: int = 20) -> List[Dict]:
        """
        按机构类型爬取

        Args:
            institution_type: 机构类型 (fund_company, securities, bank, third_party)
            institution_code: 机构代码（可选，指定特定机构）
            max_products: 每机构最大产品数

        Returns:
            爬取结果列表
        """
        all_inst = self.loader.get_all_institutions()
        results = []

        type_map = {
            "fund_company": "基金公司",
            "securities": "券商",
            "bank": "银行",
            "third_party": "第三方销售"
        }

        target_type = type_map.get(institution_type, institution_type)

        for inst_type, inst_list in all_inst:
            if inst_type != target_type:
                continue

            for inst in inst_list:
                if institution_code and inst.get("code") != institution_code:
                    continue

                result = self.scraper.batch_scrape_institution(
                    inst,
                    product_type="fund",
                    max_products=max_products
                )
                results.append({
                    "institution": inst,
                    "results": result
                })

                if institution_code:
                    break

        return results


def get_institution_summary() -> str:
    """获取机构统计摘要"""
    loader = InstitutionLoader()
    lines = ["【支持的金融机构】\n"]

    total = 0
    for inst_type, inst_list in loader.get_all_institutions():
        count = len(inst_list)
        total += count
        lines.append(f"- {inst_type}: {count}家")

    lines.append(f"\n合计: {total}家")

    # 平台覆盖
    patterns = loader.get_platform_patterns()
    lines.append(f"\n【URL匹配模式】")
    lines.append(f"- 基金产品: {len(patterns.get('fund_patterns', []))}种")
    lines.append(f"- ETF产品: {len(patterns.get('etf_patterns', []))}种")
    lines.append(f"- FOF产品: {len(patterns.get('fof_patterns', []))}种")
    lines.append(f"- 组合产品: {len(patterns.get('portfolio_patterns', []))}种")

    return "\n".join(lines)


def list_all_institutions() -> Dict[str, List[Dict]]:
    """列出所有机构"""
    loader = InstitutionLoader()
    return {
        "fund_companies": loader.get_all_fund_companies(),
        "securities": loader.get_all_securities(),
        "banks": loader.get_all_banks(),
        "third_party": loader.get_all_third_party()
    }


def search_institution(keyword: str) -> List[Dict]:
    """搜索机构"""
    loader = InstitutionLoader()
    results = []
    keyword_lower = keyword.lower()

    for inst_type, inst_list in loader.get_all_institutions():
        for inst in inst_list:
            name = inst.get("name", "").lower()
            code = inst.get("code", "").lower()
            home = inst.get("home", "").lower()

            if keyword_lower in name or keyword_lower in code or keyword_lower in home:
                inst_copy = inst.copy()
                inst_copy["type"] = inst_type
                results.append(inst_copy)

    return results


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python institution_scraper.py list                    # 列出所有机构")
        print("  python institution_scraper.py summary               # 机构统计")
        print("  python institution_scraper.py search <关键词>        # 搜索机构")
        print("  python institution_scraper.py scrape <URL>           # 爬取产品")
        print("  python institution_scraper.py type <机构类型>         # 按类型爬取")
        print("\n机构类型: fund_company, securities, bank, third_party")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        all_inst = list_all_institutions()
        print(json.dumps(all_inst, ensure_ascii=False, indent=2))

    elif cmd == "summary":
        print(get_institution_summary())

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            sys.exit(1)
        keyword = sys.argv[2]
        results = search_institution(keyword)
        print(f"找到 {len(results)} 个匹配结果:")
        for r in results:
            print(f"  {r['name']} ({r.get('code', '')}) - {r.get('type', '')}")

    elif cmd == "scrape":
        if len(sys.argv) < 3:
            print("请提供URL")
            sys.exit(1)
        url = sys.argv[2]
        scraper = UniversalScraper()
        result = scraper.scrape_any(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "type":
        if len(sys.argv) < 3:
            print("请提供机构类型: fund_company, securities, bank, third_party")
            sys.exit(1)
        inst_type = sys.argv[2]
        scraper = UniversalScraper()
        results = scraper.scrape_by_institution(inst_type, max_products=10)
        print(f"爬取完成，共处理 {len(results)} 个机构")

    else:
        print(f"未知命令: {cmd}")