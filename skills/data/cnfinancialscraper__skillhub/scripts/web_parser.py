# -*- coding: utf-8 -*-
"""
网页操作与金融产品解析模块 v3.0
支持动态网页交互、元素操作、金融产品深度解析

v3.0 增强：
- 统一入口六级降级链：Playwright → Scrapling(隐身) → Scrapling(移动) → http_utils(桌面) → http_utils(移动) → API 备用端点
- JSON-LD 结构化数据提取作为解析 fallback
- 自适应选择器匹配：自动学习每个网站的有效选择器，缓存至本地
- 页面对比与差异检测
"""

from __future__ import annotations

import json
import re
import time

from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

# Scrapling导入
try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    from scrapling.parser import Selector, Element
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    if TYPE_CHECKING:
        Selector = Any  # type: ignore
        Element = Any   # type: ignore
    SCRAPLING_AVAILABLE = False

# Playwright导入（用于复杂交互）
try:
    from playwright.sync_api import sync_playwright, Page, Locator
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"

# http_utils 公共基础设施（v4.0）
try:
    from .http_utils import http_get, fetch_text, get_session, random_ua
    from .http_utils import report_request_result
    HAS_HTTP_UTILS = True
except ImportError:
    HAS_HTTP_UTILS = False

# ==================== JSON-LD 结构化数据提取（v3.0） ====================

_RE_JSONLD = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE
)


def extract_jsonld(html: str) -> List[Dict[str, Any]]:
    """从 HTML 提取 JSON-LD 结构化数据（所有金融网站的通用 fallback）"""
    results = []
    for match in _RE_JSONLD.finditer(html):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return results


def extract_product_from_jsonld(jsonld_list: List[Dict]) -> Dict[str, Any]:
    """从 JSON-LD 数据提取金融产品 / 文章信息"""
    result = {}
    for item in jsonld_list:
        item_type = item.get("@type", "")
        if isinstance(item_type, list):
            item_type = item_type[0] if item_type else ""
        item_type = str(item_type)
        # 通用 Product 类型
        if "Product" in item_type or "FinancialProduct" in item_type:
            result["product_name"] = item.get("name", "")
            result["product_code"] = item.get("sku", "") or item.get("productID", "")
            offers = item.get("offers", {})
            if isinstance(offers, dict):
                result["price"] = offers.get("price", "")
            result["description"] = item.get("description", "")[:500]
        # Organization（公司信息）
        elif "Organization" in item_type or "Corporation" in item_type:
            result["company"] = item.get("name", "")
            result["company_url"] = item.get("url", "")
            result["legal_name"] = item.get("legalName", "")
        # WebPage（页面元数据）
        elif "WebPage" in item_type:
            result["page_name"] = item.get("name", "")
            result["page_description"] = item.get("description", "")[:300]
        # NewsArticle / Article / BlogPosting（v6.0.0 新增：新闻正文结构化提取）
        elif any(t in item_type for t in ("NewsArticle", "Article", "BlogPosting")):
            result["article_title"] = item.get("headline", "") or item.get("name", "")
            result["article_date"] = (item.get("datePublished", "") or "")[:19]
            result["article_author"] = ""
            author = item.get("author", {})
            if isinstance(author, dict):
                result["article_author"] = author.get("name", "")
            elif isinstance(author, list) and author and isinstance(author[0], dict):
                result["article_author"] = author[0].get("name", "")
            result["article_image"] = ""
            image = item.get("image", {})
            if isinstance(image, dict):
                result["article_image"] = image.get("url", "")
            elif isinstance(image, str):
                result["article_image"] = image
            result["article_body"] = (item.get("articleBody", "") or "")[:2000]
    return result


def extract_main_content(html: str, min_text_len: int = 60) -> Dict[str, str]:
    """readability 风格正文抽取（v6.0.0 新增，零依赖文本密度打分）。

    通过遍历候选块级容器，按「正文文本密度 = 文本长度 / (文本+链接文本)」打分，
    选出最可能的正文节点。适合新闻/公告/研报类页面的正文提取。

    Args:
        html: 页面 HTML
        min_text_len: 候选正文最小文本长度

    Returns:
        {"title": str, "content": str, "text_len": int}
        抽取失败时 content 为空字符串。
    """
    result = {"title": "", "content": "", "text_len": 0}
    if not html:
        return result

    # 标题优先从 <title> / <h1> 提取
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    if m:
        result["title"] = m.group(1).strip()
    if not result["title"]:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
        if m:
            result["title"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    # 候选正文容器（按常见语义标签优先排序）
    candidates = []
    try:
        from bs4 import BeautifulSoup as _BS4
        _has_bs4 = True
    except ImportError:
        _has_bs4 = False
    try:
        if _has_bs4:
            soup = _BS4(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                             "form", "iframe", "noscript"]):
                tag.decompose()
            for node in soup.find_all(["article", "main", "section", "div"]):
                text = node.get_text(" ", strip=True)
                if len(text) < min_text_len:
                    continue
                link_text = sum(len(a.get_text(" ", strip=True)) for a in node.find_all("a"))
                total = len(text)
                density = (total - link_text) / max(total, 1)
                # 正文节点特征：文本密度高 + 段落数量多
                para_count = len(node.find_all("p"))
                score = density * (1 + min(para_count, 10) * 0.15)
                candidates.append((score, text, node.name, para_count))
        else:
            # 无 bs4 时的正则 fallback：按标签剥文本
            m = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL | re.IGNORECASE)
            if m:
                content = re.sub(r"<[^>]+>", " ", m.group(1))
                candidates.append((1.0, re.sub(r"\s{2,}", " ", content).strip(), "article", 1))
    except Exception:
        return result

    if not candidates:
        return result
    # 按分数排序取最优
    candidates.sort(key=lambda c: c[0], reverse=True)
    best_score, best_text, best_tag, best_paras = candidates[0]
    best_text = re.sub(r"\s{2,}", " ", best_text).strip()
    result["content"] = best_text[:20000]
    result["text_len"] = len(best_text)
    return result


# ==================== 自适应选择器匹配（v3.0） ====================

_SELECTOR_CACHE_DIR = SKILL_DATA_DIR / "selector_cache"
_SELECTOR_CACHE_DIR.mkdir(exist_ok=True, parents=True)
_SELECTOR_CACHE_TTL = 7 * 86400  # 7 天过期


def _load_selector_cache(domain: str) -> Dict[str, List[str]]:
    """加载某域名的选择器缓存"""
    cache_file = _SELECTOR_CACHE_DIR / f"{domain.replace('.', '_')}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            age = time.time() - data.get("updated", 0)
            if age < _SELECTOR_CACHE_TTL:
                return data.get("selectors", {})
        except Exception:
            pass
    return {}


def _save_selector_cache(domain: str, selectors: Dict[str, List[str]]):
    """保存选择器缓存（v7.0.0: 目录不存在时自动创建）"""
    cache_file = _SELECTOR_CACHE_DIR / f"{domain.replace('.', '_')}.json"
    try:
        _SELECTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "domain": domain,
            "selectors": selectors,
            "updated": time.time()
        }
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class AdaptiveSelectorMatcher:
    """自适应选择器匹配器

    对每个目标字段维护候选选择器列表 + 最近成功的选择器。
    自动学习每个网站当前有效的选择器，缓存至本地 JSON。
    """

    def __init__(self, domain: str, selectors: Optional[Dict[str, List[str]]] = None):
        self.domain = domain
        # 优先用缓存，其次用传入的选择器
        cached = _load_selector_cache(domain)
        self._selectors: Dict[str, List[str]] = {}
        if selectors:
            self._selectors.update(selectors)
        if cached:
            # 缓存的选择器放在前面优先尝试
            for field, sels in cached.items():
                existing = self._selectors.get(field, [])
                self._selectors[field] = sels + [s for s in existing if s not in sels]
        self._successful: Dict[str, str] = {}  # field → 最近成功的 selector
        self._failures: Dict[str, Dict[str, int]] = {}  # field → {selector: 连续失败次数}

    def css_first(self, page: Any, field: str,
                  selectors: Optional[List[str]] = None) -> Optional[Any]:
        """尝试多个选择器，返回第一个匹配的元素

        Args:
            page: Selector 对象
            field: 字段名
            selectors: 覆盖的选择器列表

        Returns:
            匹配的 Element 或 None
        """
        sels = selectors or self._selectors.get(field, [])
        if not sels:
            return None

        # 优先尝试上次成功的
        last_success = self._successful.get(field)
        if last_success:
            sels = [last_success] + [s for s in sels if s != last_success]

        field_failures = self._failures.setdefault(field, {})
        for sel in sels:
            try:
                el = page.css_first(sel)
                if el:
                    self._successful[field] = sel
                    field_failures.pop(sel, None)
                    return el
                else:
                    # v6.0.0：缓存选择器连续失败 → 置信度衰减，重学新选择器
                    field_failures[sel] = field_failures.get(sel, 0) + 1
            except Exception:
                field_failures[sel] = field_failures.get(sel, 0) + 1
                continue
        return None

    def css_first_text(self, page: Any, field: str,
                       selectors: Optional[List[str]] = None,
                       default: str = "") -> str:
        """安全获取第一个匹配的文本"""
        el = self.css_first(page, field, selectors)
        if el:
            try:
                text = el.text()
                if text:
                    return text.strip()
            except Exception:
                pass
        return default

    def flush(self):
        """持久化当前成功的选择器到缓存（v6.0.0：连续失败 ≥3 次的选择器淘汰重学）"""
        if self._successful:
            to_save = {}
            for field, sel in self._successful.items():
                all_sels = self._selectors.get(field, [])
                field_failures = self._failures.get(field, {})
                # 把成功的放在第一位；淘汰连续失败 ≥3 次的过时选择器
                fresh = [s for s in all_sels
                         if s != sel and field_failures.get(s, 0) < 3]
                to_save[field] = [sel] + fresh[:4]
            _save_selector_cache(self.domain, to_save)

# ==================== 预编译正则（性能优化，避免每次解析重复编译） ====================

# 金融数字提取
_RE_NUMBER = re.compile(r'(\d+\.?\d*)')
_RE_SIGNED_NUMBER = re.compile(r'([+-]?\d+\.?\d*)')
_RE_PERCENTAGE = re.compile(r'(\d+\.?\d*)\s*%')
_RE_FUND_CODE = re.compile(r'(\d{6})')
_RE_STOCK_CODE = re.compile(r'(?:s[hz]|sh|sz)\s*\.?\s*(\d{6})', re.IGNORECASE)
_RE_DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')

# 金融指标提取
_RE_PE = re.compile(r'市盈率[（(]?PE[）)]?\s*[：:]\s*(\d+\.?\d*)')
_RE_PB = re.compile(r'市净率[（(]?PB[）)]?\s*[：:]\s*(\d+\.?\d*)')
_RE_SHARPE = re.compile(r'夏普比率[（(]?Sharpe[）)]?\s*[：:]\s*([+-]?\d+\.?\d*)')
_RE_MAXDD = re.compile(r'最大回撤\s*[：:]\s*([+-]?\d+\.?\d*)\s*%?')
_RE_VOLATILITY = re.compile(r'波动率\s*[：:]\s*(\d+\.?\d*)\s*%?')

# 基金指标
_RE_FUND_NAV = re.compile(r'(?:单位)?净值[：:]\s*(\d+\.\d+)')
_RE_FUND_ACCU_NAV = re.compile(r'累计净值[：:]\s*(\d+\.\d+)')
_RE_FUND_SCALE = re.compile(r'基金规模[：:]\s*([\d.]+)\s*亿')
_RE_FUND_MANAGER = re.compile(r'基金经理[：:]\s*([^\s，,]+)')
_RE_FUND_COMPANY = re.compile(r'基金公司[：:]\s*([^\s，,]+)')
_RE_FUND_ESTABLISH = re.compile(r'成立日期[：:]\s*(\d{4}-\d{2}-\d{2})')

# 收益提取
_RE_RETURN_PATTERNS = [
    (re.compile(r'近1月[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_1m'),
    (re.compile(r'近3月[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_3m'),
    (re.compile(r'近6月[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_6m'),
    (re.compile(r'近1年[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_1y'),
    (re.compile(r'近3年[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_3y'),
    (re.compile(r'今年来[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_ytd'),
    (re.compile(r'成立来[收益收益率]*[：:]\s*([+-]?\d+\.?\d*)\s*%?'), 'return_since_inception'),
]

# HTML 标签清理
_RE_HTML_TAG = re.compile(r'<[^>]+>')
_RE_HTML_SCRIPT = re.compile(r'<script[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
_RE_HTML_STYLE = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)
_RE_MULTI_SPACE = re.compile(r'\s+')

# ==================== 解析工具函数 ====================

def _safe_css_first(page, selectors, default=""):
    """安全获取第一个匹配的 CSS 选择器文本"""
    if not hasattr(page, 'css_first'):
        return default
    for sel in ([selectors] if isinstance(selectors, str) else selectors):
        try:
            el = page.css_first(sel)
            if el and el.text():
                return el.text().strip()
        except Exception:
            continue
    return default


def _safe_re_search(page, pattern, group=1, default=None):
    """安全执行正则搜索，提取分组"""
    try:
        if hasattr(page, 're_search'):
            match = page.re_search(pattern)
        else:
            match = re.search(pattern, str(page))
        if match:
            if group == 0:
                return match.group(0)
            return match.group(group) if match.groups() else match.group(0)
    except Exception:
        pass
    return default


def _clean_html(html: str) -> str:
    """清理 HTML 标签，提取纯文本"""
    text = _RE_HTML_SCRIPT.sub(' ', html)
    text = _RE_HTML_STYLE.sub(' ', text)
    text = _RE_HTML_TAG.sub(' ', text)
    text = _RE_MULTI_SPACE.sub(' ', text)
    return text.strip()


def _parse_percentage(text: str) -> float:
    """从文本解析百分比值"""
    match = _RE_SIGNED_NUMBER.search(text)
    return float(match.group(1)) if match else 0.0


def _match_first(text: str, patterns: list) -> str:
    """用多个正则模式匹配文本，返回第一个成功的"""
    for pattern in patterns:
        match = re.search(pattern, text) if isinstance(pattern, str) else pattern.search(text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return ""


@dataclass
class WebOperation:
    """网页操作描述"""
    op_type: str  # click, scroll, wait, fill, select, hover
    selector: str
    value: Optional[str] = None
    timeout: int = 10000
    wait_for: Optional[str] = None  # networkidle, domcontentloaded, load


class PageOperator:
    """页面操作器 - 支持复杂网页交互"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False

    def _ensure_playwright(self):
        """确保Playwright可用"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright未安装，请运行: pip install playwright && playwright install")

    def start(self):
        """启动浏览器。
        v5.0.0: 优先复用 browser_scraper 进程级单例的浏览器/上下文（避免每请求冷启动）；
        复用失败时回退到独立启动。"""
        self._ensure_playwright()
        if self.browser is None:
            # 尝试复用单例（共享模式下 self.playwright 保持 None，stop 不关闭共享资源）
            try:
                from browser_scraper import _get_browser_scraper
                bs = _get_browser_scraper(headless=self.headless)
                if bs is not None and bs._browser is not None:
                    self.browser = bs._browser
                    self.context = bs._context
                    self.page = self.context.new_page()
                    self._initialized = True
                    return self
            except Exception:
                pass
            # 回退：独立启动
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = self.context.new_page()
            self._initialized = True
        return self

    def stop(self):
        """关闭页面。v5.0.0: 共享单例时只关自己的 page，不关闭共享浏览器/上下文。"""
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
            self.page = None
        if self.playwright is not None:
            # 独立启动的才真正关闭整链
            if self.context:
                try:
                    self.context.close()
                except Exception:
                    pass
            if self.browser:
                try:
                    self.browser.close()
                except Exception:
                    pass
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        self.browser = None
        self.context = None
        self._initialized = False

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()

    def goto(self, url: str, wait: str = "networkidle") -> 'PageOperator':
        """导航到URL"""
        if not self._initialized:
            self.start()
        self.page.goto(url, wait_until=wait, timeout=30000)
        return self

    def click(self, selector: str, timeout: int = 10000) -> 'PageOperator':
        """点击元素"""
        self.page.click(selector, timeout=timeout)
        time.sleep(0.5)
        return self

    def fill(self, selector: str, value: str) -> 'PageOperator':
        """填写表单"""
        self.page.fill(selector, value)
        return self

    def select(self, selector: str, value: str) -> 'PageOperator':
        """选择下拉选项"""
        self.page.select_option(selector, value)
        return self

    def hover(self, selector: str) -> 'PageOperator':
        """悬停"""
        self.page.hover(selector)
        return self

    def scroll(self, direction: str = "down", amount: int = 500) -> 'PageOperator':
        """滚动页面"""
        if direction == "down":
            self.page.evaluate(f"window.scrollBy(0, {amount})")
        else:
            self.page.evaluate(f"window.scrollBy(0, -{amount})")
        time.sleep(0.3)
        return self

    def wait(self, seconds: float = 1) -> 'PageOperator':
        """等待"""
        time.sleep(seconds)
        return self

    def wait_for_selector(self, selector: str, timeout: int = 10000) -> 'PageOperator':
        """等待元素出现"""
        self.page.wait_for_selector(selector, timeout=timeout)
        return self

    def wait_for_navigation(self, timeout: int = 30000) -> 'PageOperator':
        """等待导航完成"""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self

    def execute_script(self, script: str) -> Any:
        """执行JavaScript"""
        return self.page.evaluate(script)

    def get_html(self) -> str:
        """获取页面HTML"""
        return self.page.content()

    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return self.page.locator(selector).text_content() or ""

    def get_attribute(self, selector: str, attr: str) -> str:
        """获取元素属性"""
        return self.page.locator(selector).get_attribute(attr) or ""

    def screenshot(self, path: str):
        """截图"""
        self.page.screenshot(path=path)

    # ── v4.5 类人翻页 / 链接提取 / 链接跟随 ─────────────────

    def paginate(self, next_selector: str, max_pages: int = 10,
                 wait_after_click: float = 1.0,
                 total_timeout: float = 60.0,
                 until_selector: str = None) -> List[Dict[str, Any]]:
        """类人翻页：点 next 翻页，累积每页 HTML。

        停止条件：
            1. 连续 2 轮新页面相同（去时间戳后 hash 比较）
            2. max_pages 到顶
            3. next_selector 不存在
            4. until_selector 出现
            5. 累计超过 total_timeout

        Returns:
            [{"url", "html", "page_num"}]
        """
        import hashlib as _hashlib
        import time as _time
        start = _time.time()
        pages: List[Dict[str, Any]] = []
        last_hash: Optional[str] = None
        no_change_count = 0
        for page_num in range(1, max_pages + 1):
            if (_time.time() - start) > total_timeout:
                break
            if until_selector:
                try:
                    if self.page.query_selector(until_selector):
                        break
                except Exception:
                    pass
            try:
                self.wait(0.5)
                html = self.get_html()
                # 简单 hash
                stripped = _strip_dynamic(html)
                h = _hashlib.md5(stripped.encode("utf-8", "ignore")).hexdigest()
                pages.append({"url": self.page.url, "html": html, "page_num": page_num})
                if h == last_hash:
                    no_change_count += 1
                    if no_change_count >= 2:
                        break
                else:
                    no_change_count = 0
                last_hash = h
            except Exception:
                break
            if page_num >= max_pages:
                break
            # 找 next
            try:
                next_btn = self.page.query_selector(next_selector)
            except Exception:
                next_btn = None
            if not next_btn:
                break
            try:
                next_btn.click(timeout=5000)
                self.wait(wait_after_click)
            except Exception:
                break
        return pages

    def extract_all_links(self, selector: str = "a[href]",
                          skip_javascript: bool = True) -> List[Dict[str, str]]:
        """提取所有链接。

        Returns:
            [{"href", "text", "type": "internal"|"external", "domain"}]
        """
        from urllib.parse import urljoin, urlparse
        base = self.page.url
        base_domain = urlparse(base).netloc
        results: List[Dict[str, str]] = []
        # Playwright 直接用 query_selector_all 更稳定
        try:
            els = self.page.query_selector_all(selector)
            for el in els:
                try:
                    href = el.get_attribute("href") or ""
                    text = (el.text_content() or "").strip()[:100]
                    if not href:
                        continue
                    if skip_javascript and href.startswith("javascript:"):
                        continue
                    if href.startswith("mailto:") or href.startswith("#"):
                        continue
                    full = urljoin(base, href)
                    dom = urlparse(full).netloc
                    link_type = "internal" if dom == base_domain else "external"
                    results.append({"href": full, "text": text,
                                    "type": link_type, "domain": dom})
                except Exception:
                    continue
        except Exception:
            pass
        return results

    def follow_links(self, link_selector: str,
                     content_selector: Optional[str] = None,
                     max_links: int = 20,
                     wait_after_goto: float = 1.0) -> List[Dict[str, Any]]:
        """列表页 → 逐条进入详情页 → 返回正文列表。"""
        results: List[Dict[str, Any]] = []
        try:
            hrefs = self.page.eval_on_selector_all(
                link_selector,
                "els => els.map(e => e.href).filter(h => h && !h.startsWith('javascript:'))"
            )
        except Exception:
            return results
        for href in hrefs[:max_links]:
            try:
                self.goto(href)
                self.wait(wait_after_goto)
                html = self.get_html()
                text = ""
                title = ""
                if content_selector:
                    el = self.page.query_selector(content_selector)
                    if el:
                        text = (el.text_content() or "").strip()
                else:
                    try:
                        text = self.get_text("body") or ""
                    except Exception:
                        text = ""
                try:
                    title_el = self.page.query_selector("title")
                    if title_el:
                        title = (title_el.text_content() or "").strip()[:200]
                except Exception:
                    pass
                results.append({"url": href, "html": html,
                                "text": text, "title": title})
            except Exception:
                continue
        return results

    def run_operations(self, operations: List[WebOperation]) -> 'PageOperator':
        """批量执行操作"""
        for op in operations:
            if op.op_type == "click":
                self.click(op.selector, op.timeout)
            elif op.op_type == "fill":
                self.fill(op.selector, op.value or "")
            elif op.op_type == "scroll":
                self.scroll("down", int(op.value or 500))
            elif op.op_type == "wait":
                self.wait(float(op.value or 1))
            elif op.op_type == "hover":
                self.hover(op.selector)
            elif op.op_type == "select":
                self.select(op.selector, op.value or "")
            elif op.op_type == "goto":
                self.goto(op.value or "")
            elif op.op_type == "wait_for":
                self.wait_for_selector(op.selector, op.timeout)
            elif op.op_type == "paginate":
                # 新增：批量翻页
                self.paginate(op.selector, max_pages=int(op.value or 5))

            if op.wait_for == "navigation":
                self.wait_for_navigation()

        return self


def _strip_dynamic(html: str) -> str:
    """去掉动态时间戳（辅助 paginate 停止判定）。"""
    import re as _re
    html = _re.sub(r"<script[\s\S]*?</script>", "", html, flags=_re.IGNORECASE)
    html = _re.sub(r"\b\d{10,13}\b", "TS", html)
    html = _re.sub(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "DT", html)
    return html


class FundParser:
    """基金产品解析器"""

    # 天天基金页面选择器
    TiantianSelectors = {
        "name": [".fundName", ".fund-title h1", "h1.fundName", "[class*='fund-name']"],
        "code": [".fundCode", ".fundcode", "#fundCode", "[class*='fund-code']"],
        "type": [".fundType", ".type", "#fundType", "[class*='fund-type']"],
        "company": [".company", ".management", "[class*='company']"],
        "manager": [".manager a", ".基金经理 a", "#manager a", "[class*='manager'] a"],
        "nav": [".nav", "#nav", "[class*='nav']"],
        "nav_change": [".navChange", ".nav_change", "[class*='change']"],
        "accu_nav": [".accuNav", "#accuNav", "[class*='accu']"],
        "establish_date": [".establishDate", "#establishDate", "[class*='establish']"],
        "scale": [".scale", "#scale", "[class*='scale']"],
        "risk_level": [".risk", "#risk", "[class*='risk']"],
    }

    # 东方财富选择器
    EastmoneySelectors = {
        "name": [".title", ".fund-name", "h1", "[class*='name']"],
        "code": [".code", "#fundCode", "[class*='code']"],
        "type": [".type", "[class*='type']"],
        "nav": ["#nav", ".nav", "[class*='nav']"],
        "features": ["[class*='feature']", ".tags", ".label"],
    }

    @staticmethod
    def parse_tiantian_fund(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析天天基金页面"""
        result = {
            "source": "tiantian",
            "product_name": "",
            "product_code": "",
            "product_type": "",
            "company": "",
            "manager": "",
            "risk_level": "",
            "nav": {},
            "fees": {},
            "holdings": {"stocks": [], "bonds": [], "top_industry": ""},
            "historical_nav": {},
            "risk_metrics": {},
            "basic_info": {},
            "raw_data": {}
        }

        try:
            if isinstance(page, str):
                # 如果是HTML字符串，用正则解析
                return FundParser._parse_fund_html(page, result)
            else:
                # 使用Scrapling Selector解析
                return FundParser._parse_fund_selector(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_fund_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """使用Selector解析基金"""
        # 尝试多个选择器
        for sel in FundParser.TiantianSelectors.get("name", []):
            try:
                el = page.css_first(sel)
                if el:
                    result["product_name"] = el.text().strip()
                    break
            except:
                continue

        # 基金代码
        for sel in FundParser.TiantianSelectors.get("code", []):
            try:
                el = page.css_first(sel)
                if el:
                    result["product_code"] = el.text().strip()
                    break
            except:
                continue

        # 净值信息
        for sel in FundParser.TiantianSelectors.get("nav", []):
            try:
                el = page.css_first(sel)
                if el:
                    text = el.text()
                    nav_match = re.search(r'(\d+\.\d+)', text)
                    if nav_match:
                        result["nav"]["current"] = float(nav_match.group(1))
                    break
            except:
                continue

        # 提取基本信息块
        info_patterns = [
            (r'基金规模[：:]\s*([\d.]+\s*亿元)', 'scale'),
            (r'成立日期[：:]\s*(\d{4}-\d{2}-\d{2})', 'establish_date'),
            (r'基金经理[：:]\s*([^\s，,]+)', 'manager'),
            (r'基金公司[：:]\s*([^\s，,]+)', 'company'),
        ]

        full_text = page.re_search(r'[一-龥]+[：:][^<>\n]+')
        if full_text:
            for pattern, key in info_patterns:
                match = re.search(pattern, full_text)
                if match:
                    result["basic_info"][key] = match.group(1).strip()

        return result

    @staticmethod
    def _parse_fund_html(html: str, result: Dict) -> Dict[str, Any]:
        """使用正则解析HTML（v5.0.0 选择器容错：类名容忍大小写/前后缀/连字符）"""
        # 基金名称：容忍 class="fundName" / "fund-name" / "xxx fundName xxx" 等
        name_match = re.search(r'class="[^"]*fund[-_ ]?name[^"]*"[^>]*>([^<]+)', html, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["product_name"] = name_match.group(1).strip()

        # 基金代码
        code_match = re.search(r'class="[^"]*fund[-_ ]?code[^"]*"[^>]*>([^<]+)', html, re.IGNORECASE)
        if not code_match:
            code_match = re.search(r'class="fundCode"[^>]*>([^<]+)', html)
        if code_match:
            result["product_code"] = code_match.group(1).strip()

        # 净值（容忍类名前后缀）
        nav_match = re.search(r'<td[^>]*class="[^"]*nav[^"]*"[^>]*>.*?(\d+\.\d+)', html, re.DOTALL)
        if nav_match:
            result["nav"]["current"] = float(nav_match.group(1))

        return result


class ETFParser:
    """ETF产品解析器"""

    @staticmethod
    def parse_etf_page(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析ETF详情页面"""
        result = {
            "source": "etf",
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": "",
            "product_code": "",
            "product_type": "ETF",
            "exchange": "",
            "跟踪指数": "",
            "nav": {},
            "premium": {},  # 溢价率、折价率
            "holdings": {
                "stocks": [],
                "top_10_weight": 0
            },
            "tracking_index": "",
            "fund_attributes": {},
            "risk_metrics": {}
        }

        try:
            if isinstance(page, Selector):
                result = ETFParser._parse_etf_selector(page, result)
            else:
                result = ETFParser._parse_etf_html(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_etf_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """Selector解析ETF"""
        # ETF名称
        for sel in ["h1", ".fund-name", "[class*='name']", ".title"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["product_name"] = el.text().strip()
                    break
            except:
                continue

        # ETF代码
        code_patterns = [
            r'(\d{6})',
            r'代码[：:]\s*(\d{6})',
            r'512[0-9]{3}',  # 上交所ETF
            r'159[0-9]{3}',  # 深交所ETF
        ]
        for pat in code_patterns:
            match = page.re_search(pat)
            if match:
                result["product_code"] = match.group(1) if match.groups() else match.group(0)
                break

        # 交易所
        if result["product_code"]:
            if result["product_code"].startswith("5"):
                result["exchange"] = "上交所"
            elif result["product_code"].startswith("1") or result["product_code"].startswith("15"):
                result["exchange"] = "深交所"

        # 净值数据
        nav_sel = page.re_search(r'单位净值[：:]\s*(\d+\.\d+)')
        if nav_sel:
            result["nav"]["unit"] = float(nav_sel.group(1))

        accu_nav_sel = page.re_search(r'累计净值[：:]\s*(\d+\.\d+)')
        if accu_nav_sel:
            result["nav"]["accumulated"] = float(accu_nav_sel.group(1))

        # 溢价率/折价率
        premium_sel = page.re_search(r'溢价率[：:]\s*([+-]?\d+\.?\d*)%')
        if premium_sel:
            result["premium"]["premium_rate"] = float(premium_sel.group(1))

        discount_sel = page.re_search(r'折价率[：:]\s*([+-]?\d+\.?\d*)%')
        if discount_sel:
            result["premium"]["discount_rate"] = float(discount_sel.group(1))

        # 跟踪指数
        index_sel = page.re_search(r'跟踪指数[：:]\s*([^\s\n，,]+[^\n，,]*)')
        if index_sel:
            result["tracking_index"] = index_sel.group(1).strip()

        return result

    @staticmethod
    def _parse_etf_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析ETF HTML"""
        # 名称
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["product_name"] = name_match.group(1).strip()

        # 代码
        code_match = re.search(r'(\d{6})', html)
        if code_match:
            result["product_code"] = code_match.group(1)

        # 净值
        nav_match = re.search(r'单位净值[^\d]*(\d+\.\d+)', html)
        if nav_match:
            result["nav"]["unit"] = float(nav_match.group(1))

        return result


class StockParser:
    """股票产品解析器"""

    @staticmethod
    def parse_stock_page(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析股票详情页面"""
        result = {
            "source": "stock",
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stock_name": "",
            "stock_code": "",
            "exchange": "",
            "price": {},
            "indicators": {},
            "financials": {},
            "main_indicators": {},  # 主要财务指标
            "dividend": {},  # 分红配送
            "holders": {}  # 股东情况
        }

        try:
            if isinstance(page, Selector):
                result = StockParser._parse_stock_selector(page, result)
            else:
                result = StockParser._parse_stock_html(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_stock_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """Selector解析股票"""
        # 股票名称
        for sel in ["h1", ".stock-name", "[class*='name']", ".title"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["stock_name"] = el.text().strip()
                    break
            except:
                continue

        # 价格信息
        price_patterns = [
            (r'现价[：:]\s*(\d+\.?\d*)', 'current'),
            (r'今开[：:]\s*(\d+\.?\d*)', 'open'),
            (r'最高[：:]\s*(\d+\.?\d*)', 'high'),
            (r'最低[：:]\s*(\d+\.?\d*)', 'low'),
            (r'成交量[：:]\s*([\d.]+\s*[万千手]+)', 'volume'),
            (r'成交额[：:]\s*([\d.]+\s*[万元]+)', 'amount'),
        ]

        text_content = page.re_search(r'[\d.]+')
        if text_content:
            for pattern, key in price_patterns:
                match = page.re_search(pattern)
                if match:
                    try:
                        result["price"][key] = float(re.search(r'[\d.]+', match.group(0)).group())
                    except:
                        pass

        # 市盈率、市净率
        pe_match = page.re_search(r'市盈率[（(]PE[）)][：:]\s*(\d+\.?\d*)')
        if pe_match:
            result["indicators"]["pe"] = float(pe_match.group(1))

        pb_match = page.re_search(r'市净率[（(]PB[）)][：:]\s*(\d+\.?\d*)')
        if pb_match:
            result["indicators"]["pb"] = float(pb_match.group(1))

        # 总市值、流通市值
        mktcap_match = page.re_search(r'总市值[：:]\s*([\d.]+\s*[万亿亿]?)')
        if mktcap_match:
            result["financials"]["market_cap"] = mktcap_match.group(1).strip()

        return result

    @staticmethod
    def _parse_stock_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析股票HTML"""
        # 名称
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["stock_name"] = name_match.group(1).strip()

        # 价格
        price_match = re.search(r'"price"\s*:\s*"?(\d+\.?\d*)"?', html)
        if price_match:
            result["price"]["current"] = float(price_match.group(1))

        return result


class InsurerParser:
    """保险公司解析器（万能险、年金险等）"""

    @staticmethod
    def parse_insurance_page(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析保险产品页面"""
        result = {
            "source": "insurance",
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": "",
            "product_code": "",
            "insurance_type": "",  # 万能险、年金险、健康险
            "company": "",
            "coverage_years": 0,
            "payment_years": [],
            "min_premium": 0,
            "Guaranteed_rate": 0,  # 保证利率
            "historical_rate": 0,  # 历史利率/结算利率
            "protection": {},  # 保障内容
            "cash_value": {},  # 现金价值
            "surrender_period": 0,  # 犹豫期/退保期间
            "risk_warnings": []
        }

        try:
            if isinstance(page, Selector):
                result = InsurerParser._parse_insurance_selector(page, result)
            else:
                result = InsurerParser._parse_insurance_html(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_insurance_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """Selector解析保险"""
        # 产品名称
        for sel in ["h1", ".product-name", "[class*='name']", ".title"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["product_name"] = el.text().strip()
                    break
            except:
                continue

        # 保证利率
        rate_patterns = [
            (r'保证利率[：:]\s*(\d+\.?\d*)%?', 'Guaranteed_rate'),
            (r'历史结算利率[：:]\s*(\d+\.?\d*)%?', 'historical_rate'),
            (r'预期收益率[：:]\s*(\d+\.?\d*)%?', 'expected_return'),
        ]
        for pat, key in rate_patterns:
            match = page.re_search(pat)
            if match:
                try:
                    result[key] = float(re.search(r'\d+\.?\d*', match.group(0)).group())
                except:
                    pass

        # 保障期限
        coverage_match = page.re_search(r'保障期限[：:]\s*(\d+)\s*年')
        if coverage_match:
            result["coverage_years"] = int(coverage_match.group(1))

        # 保费
        premium_match = page.re_search(r'最低保费[：:]\s*([\d,]+)\s*元')
        if premium_match:
            result["min_premium"] = int(premium_match.group(1).replace(',', ''))

        return result

    @staticmethod
    def _parse_insurance_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析保险HTML"""
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["product_name"] = name_match.group(1).strip()

        return result


class AdvisorPortfolioParser:
    """投资顾问组合方案解析器（基金组合、主理人组合）"""

    @staticmethod
    def parse_advisor_portfolio(url: str, page: Union[Selector, str] = None,
                                platform: str = "auto") -> Dict[str, Any]:
        """
        解析投资顾问组合页面

        支持平台:
        - 天天基金"基金组合"（顾工组合）
        - 且慢"长期主义"等组合
        - 蛋卷基金组合
        - 支付宝"投顾管家"
        - 微信"基金组合"
        """
        result = {
            "source": "advisor_portfolio",
            "source_url": url,
            "platform": platform,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),

            # 组合基本信息
            "portfolio_name": "",
            "portfolio_id": "",
            "advisor_name": "",  # 主理人/顾问
            "advisor_title": "",  # 顾问头衔
            "company": "",  # 所属机构
            "creation_date": "",
            "track_record_years": 0,

            # 组合特征
            "strategy_type": "",  # 稳健、平衡、进取
            "suitable_investor": "",  # 适合投资者类型
            "investment_horizon": "",  # 建议投资期限
            "risk_level": "",  # 风险等级
            "max_drawdown_control": "",  # 最大回撤控制目标

            # 业绩指标
            "cumulative_return": 0,  # 累计收益率
            "annualized_return": 0,  # 年化收益率
            "ytd_return": 0,  # 今年来收益
            "performance": {},  # 各周期收益

            # 组合配置 - 核心
            "allocations": [],  # 配置列表
            "allocation_summary": {  # 配置汇总
                "stocks": 0,
                "bonds": 0,
                "funds": 0,
                "cash": 0,
                "other": 0
            },
            "holdings": {
                "stocks": [],   # 穿透后股票持仓
                "funds": [],    # 基金持仓
                "bonds": []     # 债券持仓
            },
            "positions": [],  # 持仓明细（含权重）

            # 调仓记录
            "rebalance_records": [],
            "last_rebalance_date": "",

            # 跟投信息
            "follow_amount": 0,  # 最低跟投金额
            "follow_count": 0,  # 跟投人数
            "management_fee": 0,  # 打理费

            # 风险指标
            "risk_metrics": {
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "volatility": 0,
                "calmar_ratio": 0
            },

            # 分析建议
            "style_analysis": "",  # 风格分析
            "recommendation": ""  # 配置建议
        }

        try:
            if page is None and url:
                # 需要先爬取
                if SCRAPLING_AVAILABLE:
                    fetcher = StealthyFetcher()
                    page = fetcher.fetch(url, headless=True)
                else:
                    result["error"] = "需要安装scrapling才能爬取"
                    return result

            if isinstance(page, Selector):
                result = AdvisorPortfolioParser._parse_portfolio_selector(page, result)
            else:
                result = AdvisorPortfolioParser._parse_portfolio_html(page, result)

            # 自动检测平台
            if platform == "auto":
                url_lower = url.lower()
                if 'easmart' in url_lower or '1234567' in url_lower:
                    result["platform"] = "天天基金组合"
                elif 'qieman' in url_lower:
                    result["platform"] = "且慢"
                elif 'danjuan' in url_lower:
                    result["platform"] = "蛋卷基金"
                elif 'zhipu' in url_lower:
                    result["platform"] = "支付宝投顾"

        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_portfolio_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """Selector解析投资顾问组合"""

        # 组合名称
        for sel in ["h1", ".portfolio-name", "[class*='name']", ".title",
                    ".strategy-name", "[class*='portfolio']"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["portfolio_name"] = el.text().strip()
                    break
            except:
                continue

        # 主理人/顾问
        for sel in [".advisor", ".manager", "[class*='advisor']", ". Strategist",
                   "[class*='manager']", ".owner"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["advisor_name"] = el.text().strip()
                    break
            except:
                continue

        # 策略类型（稳健/平衡/进取）
        for sel in [".strategy", "[class*='strategy']", ".type", ".level"]:
            try:
                el = page.css_first(sel)
                if el:
                    text = el.text().strip()
                    if text:
                        result["strategy_type"] = text
                    break
            except:
                continue

        # 业绩数据提取
        # 累计收益
        cum_match = page.re_search(r'累计收益[：:]*\s*([+-]?\d+\.?\d*)%?')
        if cum_match:
            result["cumulative_return"] = float(cum_match.group(1))

        # 年化收益
        annual_match = page.re_search(r'年化收益[：:]*\s*([+-]?\d+\.?\d*)%?')
        if annual_match:
            result["annualized_return"] = float(annual_match.group(1))

        # 今年来
        ytd_match = page.re_search(r'今年来[：:]*\s*([+-]?\d+\.?\d*)%?')
        if ytd_match:
            result["ytd_return"] = float(ytd_match.group(1))

        # 各周期收益
        period_patterns = [
            (r'近1月[：:]*\s*([+-]?\d+\.?\d*)%?', '1month'),
            (r'近3月[：:]*\s*([+-]?\d+\.?\d*)%?', '3month'),
            (r'近6月[：:]*\s*([+-]?\d+\.?\d*)%?', '6month'),
            (r'近1年[：:]*\s*([+-]?\d+\.?\d*)%?', '1year'),
            (r'近3年[：:]*\s*([+-]?\d+\.?\d*)%?', '3year'),
        ]
        for pattern, key in period_patterns:
            match = page.re_search(pattern)
            if match:
                result["performance"][key] = float(match.group(1))

        # ============ 持仓配置解析（核心） ============
        positions = []

        # 尝试提取持仓表格
        table_selectors = [
            ".positions-table tr",
            ".holdings-table tr",
            ".allocation-table tr",
            ".portfolio-holdings tr",
            "[class*='position'] tr",
            "table[class*='position'] tr"
        ]

        for sel in table_selectors:
            try:
                rows = page.css(sel)
                if rows and len(rows) > 1:
                    for row in rows[1:]:  # 跳过表头
                        cells = row.css("td, th")
                        if len(cells) >= 2:
                            item = {
                                "name": "",
                                "code": "",
                                "weight": 0,
                                "change": "",  # 调仓变化
                                "type": ""     # stock/fund/bond
                            }

                            for i, cell in enumerate(cells):
                                cell_text = cell.text().strip()
                                if i == 0:
                                    # 名称列
                                    item["name"] = cell_text
                                    # 尝试提取代码
                                    code_match = re.search(r'(\d{6})', cell_text)
                                    if code_match:
                                        item["code"] = code_match.group(1)
                                elif i == 1:
                                    # 权重列
                                    w_match = re.search(r'(\d+\.?\d*)%?', cell_text)
                                    if w_match:
                                        item["weight"] = float(w_match.group(1))
                                    # 判断类型
                                    if 'ETF' in cell_text or '指数' in cell_text:
                                        item["type"] = "etf"
                                    elif re.search(r'\d{6}', cell_text):
                                        item["type"] = "stock"
                                    else:
                                        item["type"] = "fund"

                            if item["name"]:
                                positions.append(item)
                    break
            except:
                continue

        result["positions"] = positions

        # 计算配置汇总
        stocks_weight = 0
        bonds_weight = 0
        funds_weight = 0

        for p in positions:
            w = p.get("weight", 0)
            t = p.get("type", "")
            if t == "stock":
                stocks_weight += w
            elif t in ("fund", "etf"):
                funds_weight += w
            else:
                funds_weight += w  # 默认归为基金

        result["allocation_summary"] = {
            "stocks": stocks_weight,
            "bonds": bonds_weight,
            "funds": funds_weight,
            "cash": 100 - stocks_weight - bonds_weight - funds_weight,
            "other": 0
        }

        # 穿透后股票持仓（如果是基金组合，需要穿透到股票）
        # 简化处理：根据基金类型估算
        if funds_weight > 50:
            result["holdings"]["funds"] = positions
            # 估算穿透股票
            # 股票型基金按95%计, 混合型按70%计, 债券型按5%计
            estimated_stock = funds_weight * 0.5  # 简化估算
            stocks_weight += estimated_stock
            result["holdings"]["stocks"] = [{
                "name": "穿透估算股票持仓",
                "estimated_weight": estimated_stock,
                "note": "由基金持仓穿透估算"
            }]
        else:
            result["holdings"]["funds"] = positions

        # 风险指标
        sharpe_match = page.re_search(r'夏普比率[：:]*\s*([+-]?\d+\.?\d*)')
        if sharpe_match:
            result["risk_metrics"]["sharpe_ratio"] = float(sharpe_match.group(1))

        maxdd_match = page.re_search(r'最大回撤[：:]*\s*([+-]?\d+\.?\d*)%?')
        if maxdd_match:
            result["risk_metrics"]["max_drawdown"] = float(maxdd_match.group(1))

        # 适合投资者
        investor_match = page.re_search(r'适合[人群类型]*[：:]*\s*([^\n，,]+)')
        if investor_match:
            result["suitable_investor"] = investor_match.group(1).strip()

        # 建议持有期
        horizon_match = page.re_search(r'建议持有[期]*[：:]*\s*(\d+)\s*[年个月天]+')
        if horizon_match:
            result["investment_horizon"] = horizon_match.group(0)

        # 跟投信息
        follow_match = page.re_search(r'跟投[人数金额]*[：:]*\s*([\d,]+)')
        if follow_match:
            result["follow_count"] = int(follow_match.group(1).replace(',', ''))

        return result

    @staticmethod
    def _parse_portfolio_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析组合HTML"""
        # 组合名称
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["portfolio_name"] = name_match.group(1).strip()

        # 主理人
        advisor_match = re.search(r'主理人[：:]*\s*([^\s<]+)', html)
        if advisor_match:
            result["advisor_name"] = advisor_match.group(1).strip()

        # 累计收益
        cum_match = re.search(r'累计收益[：:]*\s*([+-]?\d+\.?\d*)%?', html)
        if cum_match:
            result["cumulative_return"] = float(cum_match.group(1))

        # 持仓表格
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
        positions = []
        for row in rows[1:]:  # 跳过表头
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 2:
                name_cell = re.sub(r'<[^>]+>', '', cells[0]).strip()
                weight_cell = re.sub(r'<[^>]+>', '', cells[1]).strip()

                weight_match = re.search(r'(\d+\.?\d*)%?', weight_cell)
                weight = float(weight_match.group(1)) if weight_match else 0

                code_match = re.search(r'(\d{6})', name_cell)

                positions.append({
                    "name": re.sub(r'\d{6}', '', name_cell).strip(),
                    "code": code_match.group(1) if code_match else "",
                    "weight": weight
                })

        result["positions"] = positions

        return result

    @staticmethod
    def format_portfolio_analysis(portfolio: Dict[str, Any]) -> str:
        """格式化投资顾问组合分析报告"""
        if "error" in portfolio:
            return f"解析错误: {portfolio['error']}"

        name = portfolio.get("portfolio_name", "未知组合")
        advisor = portfolio.get("advisor_name", "未知主理人")
        platform = portfolio.get("platform", "")
        strategy = portfolio.get("strategy_type", "")

        report = f"""
【投资顾问组合分析】

■ 基本信息
组合名称: {name}
主理人: {advisor}
平台: {platform}
策略类型: {strategy if strategy else '未识别'}
"""

        # 业绩表现
        perf = portfolio.get("performance", {})
        cum_return = portfolio.get("cumulative_return", 0)
        annual_return = portfolio.get("annualized_return", 0)

        if cum_return or annual_return:
            report += "\n■ 业绩表现\n"
            if cum_return:
                report += f"累计收益: {cum_return:+.2f}%\n"
            if annual_return:
                report += f"年化收益: {annual_return:+.2f}%\n"

            if perf:
                report += "各周期表现:\n"
                for period, value in list(perf.items())[:6]:
                    report += f"  近{period}: {value:+.2f}%\n"

        # 资产配置
        report += "\n■ 资产配置\n"
        summary = portfolio.get("allocation_summary", {})
        if summary:
            stocks = summary.get("stocks", 0)
            bonds = summary.get("bonds", 0)
            funds = summary.get("funds", 0)
            cash = summary.get("cash", 0)

            bar_len = 25
            total = stocks + bonds + funds + cash
            if total > 0:
                stocks_bar = int(stocks / 100 * bar_len)
                bonds_bar = int(bonds / 100 * bar_len)
                funds_bar = int(funds / 100 * bar_len)
                cash_bar = int(cash / 100 * bar_len)

                report += f"股票:   {stocks:5.1f}% | {'▓' * stocks_bar}{'░' * (bar_len - stocks_bar)}\n"
                report += f"债券:   {bonds:5.1f}% | {'▓' * bonds_bar}{'░' * (bar_len - bonds_bar)}\n"
                report += f"基金:   {funds:5.1f}% | {'▓' * funds_bar}{'░' * (bar_len - funds_bar)}\n"
                report += f"现金:   {cash:5.1f}% | {'▓' * cash_bar}{'░' * (bar_len - cash_bar)}\n"

        # 持仓明细
        positions = portfolio.get("positions", [])
        if positions:
            report += f"\n■ 持仓明细 (共{len(positions)}只)\n"
            report += f"{'名称':<20} {'代码':<8} {'权重':>8}\n"
            report += "-" * 40 + "\n"
            for p in positions[:15]:
                name = (p.get("name", "") or "")[:18]
                code = p.get("code", "") or "-"
                weight = p.get("weight", 0)
                report += f"{name:<20} {code:<8} {weight:>7.2f}%\n"

            if len(positions) > 15:
                report += f"... 还有{len(positions) - 15}只\n"

        # 风险指标
        risk = portfolio.get("risk_metrics", {})
        if risk:
            report += "\n■ 风险指标\n"
            if risk.get("sharpe_ratio"):
                report += f"夏普比率: {risk['sharpe_ratio']:.2f}\n"
            if risk.get("max_drawdown"):
                report += f"最大回撤: {risk['max_drawdown']:.2f}%\n"
            if risk.get("volatility"):
                report += f"波动率: {risk['volatility']:.2f}%\n"

        # 适合投资者
        suitable = portfolio.get("suitable_investor", "")
        horizon = portfolio.get("investment_horizon", "")
        if suitable or horizon:
            report += "\n■ 适合人群\n"
            if suitable:
                report += f"{suitable}\n"
            if horizon:
                report += f"建议持有: {horizon}\n"

        # 投资建议
        report += "\n■ 配置建议\n"
        if strategy:
            if "稳健" in strategy or "保守" in strategy:
                report += "该组合为稳健型，适合风险偏好较低的投资者，可作为养老或教育金规划。\n"
            elif "进取" in strategy or "积极" in strategy:
                report += "该组合为进取型，适合风险承受能力强的投资者，建议定投并长期持有。\n"
            else:
                report += "该组合为均衡型，适合大多数投资者，可作为核心配置。\n"

        return report


class FOFParser:
    """FOF（基金中基金）产品解析器"""

    @staticmethod
    def parse_fof_page(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析FOF产品页面 - 提取底层基金配置"""
        result = {
            "source": "fof",
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": "",
            "product_code": "",
            "product_type": "FOF",
            "company": "",
            "manager": "",
            "fof_category": "",  # 养老FOF、普通FOF
            "investment_style": "",  # 目标日期、目标风险、均衡型

            # FOF特有字段
            "asset_allocation": {  # 资产配置比例
                "stocks": 0,  # 股票比例
                "bonds": 0,    # 债券比例
                "funds": 0,    # 基金比例（自家产品）
                "cash": 0,     # 现金
                "other": 0     # 其他
            },
            "underlying_funds": [],  # 底层基金持仓
            "external_funds": [],    # 外部基金（非自家）
            "internal_funds": [],    # 内部基金（自家产品）
            "holdings": {
                "stocks": [],  # 直接股票持仓（如果有）
                "bonds": [],   # 直接债券持仓（如果有）
                "funds": []    # 基金持仓
            },
            "top_10_holdings_weight": 0,  # 前十持仓集中度
            "rebalance_history": [],  # 调仓历史
            "fee_structure": {},  # FOF费率（双层收费）
            "risk_metrics": {},
            "performance": {}
        }

        try:
            if isinstance(page, Selector):
                result = FOFParser._parse_fof_selector(page, result)
            else:
                result = FOFParser._parse_fof_html(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_fof_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """使用Selector解析FOF"""
        # 产品名称
        for sel in ["h1", ".fund-name", "[class*='name']", ".title", ".fof-name"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["product_name"] = el.text().strip()
                    break
            except:
                continue

        # 基金代码
        code_match = page.re_search(r'(\d{6})')
        if code_match:
            result["product_code"] = code_match.group(1)

        # 资产配置比例 - 关键解析
        # 格式1: 股票 20%、债券 60%、基金 15%、现金 5%
        # 格式2: 权益类 20%、固收类 75%、其他 5%
        allocation_patterns = [
            r'股票[仓位]*[：:]*\s*(\d+\.?\d*)\s*%',
            r'权益类[：:]*\s*(\d+\.?\d*)\s*%',
            r'股票仓位[：:]*\s*(\d+\.?\d*)\s*%',
            r'投资于基金[：:]*\s*(\d+\.?\d*)\s*%',
            r'基金投资比例[：:]*\s*(\d+\.?\d*)\s*%',
        ]
        for pat in allocation_patterns:
            match = page.re_search(pat)
            if match:
                result["asset_allocation"]["stocks"] = float(match.group(1))
                break

        # 债券配置
        bond_patterns = [
            r'债券[仓位]*[：:]*\s*(\d+\.?\d*)\s*%',
            r'固收类[：:]*\s*(\d+\.?\d*)\s*%',
        ]
        for pat in bond_patterns:
            match = page.re_search(pat)
            if match:
                result["asset_allocation"]["bonds"] = float(match.group(1))
                break

        # 现金配置
        cash_match = page.re_search(r'现金[：:]*\s*(\d+\.?\d*)\s*%')
        if cash_match:
            result["asset_allocation"]["cash"] = float(cash_match.group(1))

        # ============ 底层基金持仓解析（核心功能） ============
        # FOF的精髓是提取其持有的底层基金

        # 尝试提取基金持仓表格
        # 天天基金的FOF持仓通常在"基金持仓"或"持仓明细"tab下
        fund_holdings = []

        # 尝试CSS选择器
        holding_selectors = [
            ".holdings-table tr",  # 持仓表格行
            ".fund-holdings tr",
            "[class*='holding'] tr",
            ".positions tr",
            "table[class*='fund'] tr",
            ".fof-holdings tr"
        ]

        for sel in holding_selectors:
            try:
                rows = page.css(sel)
                if rows and len(rows) > 1:
                    # 解析持仓行
                    for row in rows[1:]:  # 跳过表头
                        cells = row.css("td, th")
                        if len(cells) >= 2:
                            fund_name = ""
                            fund_code = ""
                            weight = 0
                            change = ""

                            for i, cell in enumerate(cells):
                                cell_text = cell.text().strip()
                                # 第一列通常是基金名称或代码
                                if i == 0:
                                    # 尝试提取基金代码 (6位数字)
                                    code_in_cell = re.search(r'(\d{6})', cell_text)
                                    if code_in_cell:
                                        fund_code = code_in_cell.group(1)
                                    fund_name = re.sub(r'\d{6}', '', cell_text).strip()
                                elif i == 1:
                                    # 第二列通常是持仓比例
                                    w_match = re.search(r'(\d+\.?\d*)%?', cell_text)
                                    if w_match:
                                        weight = float(w_match.group(1))
                                    elif re.search(r'\d', cell_text):
                                        try:
                                            weight = float(re.search(r'[\d.]+', cell_text).group())
                                        except:
                                            pass

                            if fund_name or fund_code:
                                fund_holdings.append({
                                    "name": fund_name,
                                    "code": fund_code,
                                    "weight": weight,
                                    "change": change
                                })
                    break
            except:
                continue

        result["underlying_funds"] = fund_holdings

        # 区分内部基金和外部基金（通过名称匹配或平台判断）
        internal_companies = ["易方达", "华夏", "嘉实", "南方", "广发", "博时",
                             "招商", "工银", "建信", "富国", "鹏华", "汇添富",
                             "中欧", "兴全", "景林", "高毅", "淡水泉", "明汯"]

        internal_funds = []
        external_funds = []

        for f in fund_holdings:
            is_internal = any(co in f.get("name", "") for co in internal_companies)
            if is_internal:
                internal_funds.append(f)
            else:
                external_funds.append(f)

        result["internal_funds"] = internal_funds
        result["external_funds"] = external_funds

        # 计算前十持仓集中度
        if fund_holdings:
            top_10 = sum(f.get("weight", 0) for f in fund_holdings[:10])
            result["top_10_holdings_weight"] = top_10

        # FOF分类
        name_text = result.get("product_name", "")
        if "养老" in name_text or "目标日期" in name_text:
            result["fof_category"] = "养老FOF"
            result["investment_style"] = "目标日期"
        elif "目标风险" in name_text:
            result["fof_category"] = "普通FOF"
            result["investment_style"] = "目标风险"
        else:
            result["fof_category"] = "普通FOF"

        # FOF特有费率（通常有双重收费）
        fee_match = page.re_search(r'基金管理费[：:]\s*(\d+\.?\d*)%?')
        if fee_match:
            result["fee_structure"]["management_fee"] = float(fee_match.group(1))

        return result

    @staticmethod
    def _parse_fof_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析FOF HTML"""
        # 名称
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["product_name"] = name_match.group(1).strip()

        # 代码
        code_match = re.search(r'(\d{6})', html)
        if code_match:
            result["product_code"] = code_match.group(1)

        # 资产配置比例
        alloc_match = re.search(r'股票[：:]*\s*(\d+\.?\d*)%?', html)
        if alloc_match:
            result["asset_allocation"]["stocks"] = float(alloc_match.group(1))

        # 底层基金持仓 - 通过正则提取表格
        # 匹配基金持仓行: 基金名称 持仓比例
        fund_rows = re.findall(r'<tr[^>]*>.*?<td[^>]*>([^<]*(?:\d{6})?[^<]*)</td>.*?<td[^>]*>(\d+\.?\d*)%?</td>', html, re.DOTALL)
        funds = []
        for name_cell, weight_cell in fund_rows:
            fund_name = re.sub(r'\d{6}', '', name_cell).strip()
            fund_code = re.search(r'(\d{6})', name_cell)
            try:
                weight = float(re.search(r'(\d+\.?\d*)', weight_cell).group(1))
            except:
                weight = 0

            if fund_name:
                funds.append({
                    "name": fund_name,
                    "code": fund_code.group(1) if fund_code else "",
                    "weight": weight
                })

        result["underlying_funds"] = funds

        return result

    @staticmethod
    def extract_asset_allocation(text: str) -> Dict[str, float]:
        """从文本提取资产配置比例"""
        allocation = {"stocks": 0, "bonds": 0, "funds": 0, "cash": 0, "other": 0}

        # 股票/权益类
        stock_match = re.search(r'股票[仓位]*[：:]*\s*(\d+\.?\d*)\s*%', text)
        if stock_match:
            allocation["stocks"] = float(stock_match.group(1))
        else:
            equity_match = re.search(r'权益类[：:]*\s*(\d+\.?\d*)\s*%', text)
            if equity_match:
                allocation["stocks"] = float(equity_match.group(1))

        # 债券/固收类
        bond_match = re.search(r'债券[仓位]*[：:]*\s*(\d+\.?\d*)\s*%', text)
        if bond_match:
            allocation["bonds"] = float(bond_match.group(1))
        else:
            fixed_match = re.search(r'固收类[：:]*\s*(\d+\.?\d*)\s*%', text)
            if fixed_match:
                allocation["bonds"] = float(fixed_match.group(1))

        # 现金
        cash_match = re.search(r'现金[：:]*\s*(\d+\.?\d*)\s*%', text)
        if cash_match:
            allocation["cash"] = float(cash_match.group(1))

        # 基金
        fund_match = re.search(r'基金[：:]*\s*(\d+\.?\d*)\s*%', text)
        if fund_match:
            allocation["funds"] = float(fund_match.group(1))

        return allocation

    @staticmethod
    def format_fof_analysis(fof_info: Dict[str, Any]) -> str:
        """格式化FOF分析报告"""
        if "error" in fof_info:
            return f"解析错误: {fof_info['error']}"

        name = fof_info.get("product_name", "未知")
        code = fof_info.get("product_code", "")
        category = fof_info.get("fof_category", "FOF")
        style = fof_info.get("investment_style", "")

        report = f"""
【{category}产品分析】

■ 基本信息
名称: {name}
代码: {code}
类型: {category}
风格: {style if style else '未识别'}

■ 资产配置比例
"""
        alloc = fof_info.get("asset_allocation", {})
        if alloc:
            stocks = alloc.get("stocks", 0)
            bonds = alloc.get("bonds", 0)
            funds = alloc.get("funds", 0)
            cash = alloc.get("cash", 0)

            # 可视化
            total = stocks + bonds + funds + cash
            if total > 0:
                bar_len = 30
                stocks_bar = int(stocks / 100 * bar_len)
                bonds_bar = int(bonds / 100 * bar_len)
                funds_bar = int(funds / 100 * bar_len)
                cash_bar = int(cash / 100 * bar_len)

                report += f"股票/权益: {stocks:5.1f}% | {'█' * stocks_bar}{'░' * (bar_len - stocks_bar)}\n"
                report += f"债券/固收: {bonds:5.1f}% | {'█' * bonds_bar}{'░' * (bar_len - bonds_bar)}\n"
                report += f"基金:       {funds:5.1f}% | {'█' * funds_bar}{'░' * (bar_len - funds_bar)}\n"
                report += f"现金:       {cash:5.1f}% | {'█' * cash_bar}{'░' * (bar_len - cash_bar)}\n"

        report += f"""
■ 底层基金持仓 (共{len(fof_info.get('underlying_funds', []))}只)
"""
        underlying = fof_info.get("underlying_funds", [])
        if underlying:
            # 内部vs外部分类
            internal = fof_info.get("internal_funds", [])
            external = fof_info.get("external_funds", [])

            if internal:
                report += f"\n自家产品 ({len(internal)}只):\n"
                for f in internal[:5]:
                    report += f"  {f.get('name', '')}({f.get('code', '')}) - {f.get('weight', 0):.2f}%\n"

            if external:
                report += f"\n外部基金 ({len(external)}只):\n"
                for f in external[:10]:
                    report += f"  {f.get('name', '')}({f.get('code', '')}) - {f.get('weight', 0):.2f}%\n"

            top10_weight = fof_info.get("top_10_holdings_weight", 0)
            report += f"\n前十持仓集中度: {top10_weight:.1f}%\n"
        else:
            report += "暂无可用持仓数据\n"

        # 收益表现
        perf = fof_info.get("performance", {})
        if perf:
            report += "\n■ 收益表现\n"
            for period, value in list(perf.items())[:5]:
                report += f"  {period}: {value}%\n"

        return report


class BondParser:
    """债券产品解析器"""

    @staticmethod
    def parse_bond_page(page: Union[Selector, str], url: str = "") -> Dict[str, Any]:
        """解析债券产品页面"""
        result = {
            "source": "bond",
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": "",
            "product_code": "",
            "bond_type": "",  # 国债、企业债、可转债
            "par_value": 100,
            "coupon_rate": 0,  # 票面利率
            "issue_price": 0,
            "maturity_date": "",
            "term_to_maturity": 0,  # 剩余期限
            "rating": "",  # 信用评级
            "yield_to_maturity": 0,  # 到期收益率
            "clean_price": 0,  # 净价
            "dirty_price": 0,  # 全价
            "accrued_interest": 0,  # 应计利息
            "conversion_price": 0,  # 转股价（可转债）
            "conversion_ratio": 0,  # 转股比例（可转债）
        }

        try:
            if isinstance(page, Selector):
                result = BondParser._parse_bond_selector(page, result)
            else:
                result = BondParser._parse_bond_html(page, result)
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def _parse_bond_selector(page: Selector, result: Dict) -> Dict[str, Any]:
        """Selector解析债券"""
        for sel in ["h1", ".bond-name", "[class*='name']", ".title"]:
            try:
                el = page.css_first(sel)
                if el:
                    result["product_name"] = el.text().strip()
                    break
            except:
                continue

        # 票面利率
        coupon_match = page.re_search(r'票面利率[：:]\s*(\d+\.?\d*)%?')
        if coupon_match:
            result["coupon_rate"] = float(coupon_match.group(1))

        # 到期收益率
        ytm_match = page.re_search(r'到期收益率[：:]\s*(\d+\.?\d*)%?')
        if ytm_match:
            result["yield_to_maturity"] = float(ytm_match.group(1))

        return result

    @staticmethod
    def _parse_bond_html(html: str, result: Dict) -> Dict[str, Any]:
        """正则解析债券HTML"""
        name_match = re.search(r'<h1[^>]*>([^<]+)', html)
        if name_match:
            result["product_name"] = name_match.group(1).strip()

        return result


# ============ 统一解析入口（v3.0 增强降级链） ============

def parse_financial_product(url: str, product_type: str = "auto",
                            use_dynamic: bool = False,
                            operations: List[WebOperation] = None) -> Dict[str, Any]:
    """
    统一金融产品解析入口（v3.0 增强）

    降级链：
    1. Playwright（复杂交互）→
    2. Scrapling 隐身模式 →
    3. Scrapling 移动端 →
    4. http_utils 桌面 UA →
    5. http_utils 移动 UA →
    6. http_utils 直接 fetch（作为最后手段）→
    7. JSON-LD 提取 + URL 代码提取（始终返回部分数据）

    Args:
        url: 产品URL
        product_type: 产品类型 ("fund", "etf", "stock", "bond", "insurance", "p2p", "fof", "advisor", "auto")
        use_dynamic: 是否使用动态渲染
        operations: 页面操作列表（用于登录、点击等）

    Returns:
        产品信息字典（即使所有爬取失败也会包含 url 和从 URL 提取的信息）
    """
    result = {"source_url": url, "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    # 自动检测类型
    if product_type == "auto":
        product_type = _detect_product_type(url)

    # 从 URL 提取基本代码（最后手段）
    _extract_code_from_url(url, result, product_type)

    # ── 降级链 ──
    html_content = None
    page_obj = None

    # 级别 1: Playwright（复杂交互操作）
    if operations and PLAYWRIGHT_AVAILABLE:
        try:
            with PageOperator() as op:
                op.goto(url)
                op.run_operations(operations)
                html_content = op.get_html()
        except Exception:
            pass

    # 级别 2-3: Scrapling
    if html_content is None and SCRAPLING_AVAILABLE:
        for mode_desc, fetcher_cls, use_mobile in [
            ("隐身模式", StealthyFetcher, False),
            ("移动端模式", StealthyFetcher, True),
        ]:
            try:
                fetcher = fetcher_cls()
                page = fetcher.fetch(url, headless=True,
                                     solve_cloudflare=True if not use_mobile else False)
                if page:
                    page_obj = page
                    if hasattr(page, 'html'):
                        html_content = page.html
                    elif hasattr(page, 'html_content'):
                        html_content = page.html_content
                    elif hasattr(page, 'body') and isinstance(page.body, str):
                        html_content = page.body
                    if html_content:
                        break
            except Exception:
                continue

    # 级别 4-5: http_utils（标准库 HTTP）
    if html_content is None and HAS_HTTP_UTILS:
        for mobile in (False, True):
            try:
                s = get_session(mobile=mobile, rotate_ua=True, randomize_fingerprint=True)
                resp = http_get(url, timeout=30, session=s)
                if resp is not None:
                    html_content = resp.text
                    if html_content:
                        break
            except Exception:
                continue

    # 级别 6: http_utils fetch_text（最后同步手段）
    if html_content is None and HAS_HTTP_UTILS:
        try:
            html_content = fetch_text(url, timeout=30)
        except Exception:
            pass

    # ── 解析阶段 ──
    if page_obj is not None:
        # 优先用 Scrapling Selector
        result = _dispatch_parse(page_obj, product_type, url, result)
    elif html_content:
        # 用 HTML 字符串解析
        result = _dispatch_parse(html_content, product_type, url, result)
        # v3.0: JSON-LD fallback — 如果 CSS/正则解析结果不足，尝试 JSON-LD
        if _is_result_sparse(result):
            jsonld_data = extract_jsonld(html_content)
            if jsonld_data:
                product_info = extract_product_from_jsonld(jsonld_data)
                _merge_sparse_result(result, product_info)
    else:
        result["warning"] = "所有爬取引擎均失败，仅返回 URL 提取信息"
        result["solutions"] = [
            "检查网络连接", "确认 URL 可访问",
            "安装 scrapling: pip install scrapling",
            "安装 playwright: pip install playwright && playwright install chromium"
        ]

    return result


def _detect_product_type(url: str) -> str:
    """从 URL 自动检测产品类型"""
    url_lower = url.lower()
    if 'fof' in url_lower or 'FOF' in url:
        return "fof"
    elif 'portfolio' in url_lower or '组合' in url:
        return "advisor"
    elif 'fund.eastmoney' in url_lower or 'tiantian' in url_lower or '/fund/' in url_lower:
        return "fund"
    elif 'etf.' in url_lower or 'quotes.etf' in url_lower:
        return "etf"
    elif 'stock.eastmoney' in url_lower or 'quotes.stock' in url_lower or '10jqka' in url_lower:
        return "stock"
    elif 'bond.' in url_lower or 'cbond' in url_lower:
        return "bond"
    elif 'insurance' in url_lower or 'baodan' in url_lower:
        return "insurance"
    return "fund"


def _extract_code_from_url(url: str, result: Dict, product_type: str):
    """从 URL 中提取产品代码（即使爬取失败也能拿到基本信息）"""
    # 基金代码：6位数字
    fund_match = re.search(r'(?:fund|f|jj)[=/]*(\d{6})', url, re.IGNORECASE)
    if not fund_match:
        fund_match = re.search(r'/(\d{6})\.(?:html|shtml)', url)
    if fund_match:
        code = fund_match.group(1)
        if product_type in ("fund", "etf", "fof", "auto"):
            result["product_code"] = code
        elif product_type == "stock":
            result["stock_code"] = code

    # 股票代码：sh/sz + 6位数字
    stock_match = re.search(r'(?:sh|sz|SH|SZ)(\d{6})', url)
    if stock_match:
        result["stock_code"] = stock_match.group(1)


def _dispatch_parse(page_or_html, product_type: str, url: str,
                    result: Dict) -> Dict[str, Any]:
    """根据产品类型分派解析器"""
    try:
        if product_type == "fund":
            parsed = FundParser.parse_tiantian_fund(page_or_html, url)
        elif product_type == "etf":
            parsed = ETFParser.parse_etf_page(page_or_html, url)
        elif product_type == "stock":
            parsed = StockParser.parse_stock_page(page_or_html, url)
        elif product_type == "bond":
            parsed = BondParser.parse_bond_page(page_or_html, url)
        elif product_type == "fof":
            parsed = FOFParser.parse_fof_page(page_or_html, url)
        elif product_type == "advisor":
            parsed = AdvisorPortfolioParser.parse_advisor_portfolio(url, page_or_html)
        elif product_type == "insurance":
            parsed = InsurerParser.parse_insurance_page(page_or_html, url)
        else:
            parsed = FundParser.parse_tiantian_fund(page_or_html, url)
        result.update(parsed)
    except Exception as e:
        result["parse_error"] = str(e)[:200]
    return result


def _is_result_sparse(result: Dict) -> bool:
    """判断解析结果是否稀疏（缺少关键字段）"""
    name = result.get("product_name") or result.get("stock_name") or result.get("portfolio_name") or ""
    code = result.get("product_code") or result.get("stock_code") or ""
    nav = result.get("nav", {})
    price = result.get("price", {})
    return not name and not code and not nav and not price


def _merge_sparse_result(result: Dict, jsonld_info: Dict):
    """将 JSON-LD 提取的信息合并到稀疏结果中"""
    if not result.get("product_name") and jsonld_info.get("product_name"):
        result["product_name"] = jsonld_info["product_name"]
    if not result.get("product_code") and jsonld_info.get("product_code"):
        result["product_code"] = jsonld_info["product_code"]
    if not result.get("company") and jsonld_info.get("company"):
        result["company"] = jsonld_info["company"]
    if jsonld_info.get("description"):
        result["description"] = jsonld_info["description"]
    if jsonld_info.get("price"):
        if "price" not in result:
            result["price"] = {}
        result["price"]["jsonld_value"] = jsonld_info["price"]
    result["_jsonld_fallback"] = True


def parse_product_from_html(html: str, product_type: str, url: str = "") -> Dict[str, Any]:
    """
    从HTML内容解析金融产品（v3.0: 增加 JSON-LD fallback）

    Args:
        html: HTML内容
        product_type: 产品类型
        url: 原始URL（可选）

    Returns:
        产品信息
    """
    result = {"source_url": url, "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    # 主解析
    parsed = {}
    try:
        if product_type == "fund":
            parsed = FundParser.parse_tiantian_fund(html, url)
        elif product_type == "etf":
            parsed = ETFParser.parse_etf_page(html, url)
        elif product_type == "stock":
            parsed = StockParser.parse_stock_page(html, url)
        elif product_type == "bond":
            parsed = BondParser.parse_bond_page(html, url)
        elif product_type == "fof":
            parsed = FOFParser.parse_fof_page(html, url)
        elif product_type == "advisor":
            parsed = AdvisorPortfolioParser.parse_advisor_portfolio(url, html)
        else:
            return {"error": f"不支持的产品类型: {product_type}"}
    except Exception as e:
        parsed = {"parse_error": str(e)[:200]}

    result.update(parsed)

    # v3.0: JSON-LD fallback
    if _is_result_sparse(result):
        jsonld_data = extract_jsonld(html)
        if jsonld_data:
            product_info = extract_product_from_jsonld(jsonld_data)
            _merge_sparse_result(result, product_info)

    # 从 URL 提取代码
    if url:
        _extract_code_from_url(url, result, product_type)

    return result


def extract_financial_metrics(text: str) -> Dict[str, Any]:
    """
    从文本中提取金融指标

    Args:
        text: 文本内容

    Returns:
        金融指标字典
    """
    metrics = {}

    # 收益率
    return_patterns = [
        (r'近1月[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_1m'),
        (r'近3月[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_3m'),
        (r'近6月[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_6m'),
        (r'近1年[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_1y'),
        (r'近3年[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_3y'),
        (r'今年来[收益收益率]*[：:]*\s*([+-]?\d+\.?\d*)%?', 'return_ytd'),
    ]

    for pattern, key in return_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                metrics[key] = float(match.group(1))
            except (ValueError, TypeError):
                pass

    # 风险指标
    risk_patterns = [
        (r'夏普比率[（(]Sharpe[）)][：:]*\s*([+-]?\d+\.?\d*)', 'sharpe_ratio'),
        (r'最大回撤[：:]*\s*([+-]?\d+\.?\d*)%?', 'max_drawdown'),
        (r'波动率[：:]*\s*(\d+\.?\d*)%?', 'volatility'),
        (r'卡玛比率[：:]*\s*([+-]?\d+\.?\d*)', 'calmar_ratio'),
    ]

    for pattern, key in risk_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                metrics[key] = float(re.search(r'[+-]?\d+\.?\d*', match.group(0)).group())
            except:
                pass

    # 估值指标
    val_patterns = [
        (r'市盈率[（(]PE[）)][：:]*\s*(\d+\.?\d*)', 'pe'),
        (r'市净率[（(]PB[）)][：:]*\s*(\d+\.?\d*)', 'pb'),
        (r'市销率[（(]PS[）)][：:]*\s*(\d+\.?\d*)', 'ps'),
        (r'股息率[：:]*\s*(\d+\.?\d*)%?', 'dividend_yield'),
    ]

    for pattern, key in val_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                metrics[key] = float(re.search(r'\d+\.?\d*', match.group(0)).group())
            except:
                pass

    return metrics


def format_product_summary(product_info: Dict[str, Any]) -> str:
    """
    格式化产品信息为可读摘要

    Args:
        product_info: 产品信息字典

    Returns:
        格式化摘要文本
    """
    if "error" in product_info:
        return f"解析错误: {product_info['error']}"

    source = product_info.get("source", "unknown")
    summary = f"【{source.upper()} 产品解析结果】\n\n"

    # 基本信息
    name = product_info.get("product_name") or product_info.get("stock_name", "") or \
           product_info.get("portfolio_name", "未知")
    code = product_info.get("product_code") or product_info.get("stock_code", "")

    summary += f"名称: {name}\n"
    if code:
        summary += f"代码: {code}\n"

    ptype = product_info.get("product_type") or product_info.get("insurance_type", "") or \
            product_info.get("fof_category", "")
    if ptype:
        summary += f"类型: {ptype}\n"

    company = product_info.get("company") or product_info.get("platform", "")
    if company:
        summary += f"机构: {company}\n"

    # 净值/价格
    nav = product_info.get("nav", {})
    price = product_info.get("price", {})
    if nav:
        if "current" in nav:
            summary += f"\n单位净值: {nav['current']}\n"
        elif "unit" in nav:
            summary += f"\n单位净值: {nav['unit']}\n"
        if "accumulated" in nav:
            summary += f"累计净值: {nav['accumulated']}\n"

    if price:
        if "current" in price:
            summary += f"\n现价: {price['current']}\n"

    # 收益率
    hist = product_info.get("historical_nav", {})
    perf = product_info.get("performance", {})
    cum_return = product_info.get("cumulative_return", 0)

    if hist:
        summary += "\n历史收益:\n"
        for period, value in list(hist.items())[:5]:
            summary += f"  近{period}: {value}%\n"
    elif perf:
        summary += "\n收益表现:\n"
        for period, value in list(perf.items())[:5]:
            summary += f"  {period}: {value}%\n"
    elif cum_return:
        summary += f"\n累计收益: {cum_return:+.2f}%\n"

    # FOF特有 - 资产配置
    asset_alloc = product_info.get("asset_allocation", {})
    if asset_alloc:
        summary += "\n资产配置:\n"
        for k, v in asset_alloc.items():
            if v > 0:
                summary += f"  {k}: {v}%\n"

    # 投资顾问组合 - 配置汇总
    alloc_summary = product_info.get("allocation_summary", {})
    if alloc_summary:
        summary += "\n配置比例:\n"
        for k, v in alloc_summary.items():
            if v > 0:
                summary += f"  {k}: {v}%\n"

    # 风险指标
    metrics = product_info.get("risk_metrics", {})
    if metrics:
        summary += "\n风险指标:\n"
        for k, v in list(metrics.items())[:5]:
            summary += f"  {k}: {v}\n"

    # 持仓
    holdings = product_info.get("holdings", {})
    positions = product_info.get("positions", [])
    underlying = product_info.get("underlying_funds", [])

    if holdings.get("stocks"):
        summary += "\n重仓股:\n"
        for s in holdings["stocks"][:5]:
            summary += f"  {s.get('name', '')}({s.get('code', '')}) - {s.get('weight', 0)}%\n"
    elif underlying:
        summary += "\n底层基金持仓:\n"
        for f in underlying[:10]:
            summary += f"  {f.get('name', '')}({f.get('code', '')}) - {f.get('weight', 0):.2f}%\n"
    elif positions:
        summary += f"\n持仓明细 (共{len(positions)}只):\n"
        for p in positions[:10]:
            summary += f"  {p.get('name', '')}({p.get('code', '')}) - {p.get('weight', 0):.2f}%\n"

    return summary


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python web_parser.py <URL> [产品类型]")
        print("  python web_parser.py --html <HTML文件> [产品类型]")
        print("\n产品类型: fund, etf, stock, bond, insurance, auto")
        print("示例:")
        print("  python web_parser.py https://fund.eastmoney.com/000001.html fund")
        print("  python web_parser.py --html page.html fund")
        sys.exit(1)

    if sys.argv[1] == "--html":
        # 从HTML文件解析
        html_file = sys.argv[2]
        product_type = sys.argv[3] if len(sys.argv) > 3 else "fund"

        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()

        result = parse_product_from_html(html, product_type)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        url = sys.argv[1]
        product_type = sys.argv[2] if len(sys.argv) > 2 else "auto"

        print(f"正在解析: {url}")
        print(f"产品类型: {product_type}")

        result = parse_financial_product(url, product_type)
        print("\n" + format_product_summary(result))