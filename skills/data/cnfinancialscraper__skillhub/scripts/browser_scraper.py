# -*- coding: utf-8 -*-
"""
浏览器自动化爬虫模块 v1.0 (browser_scraper.py)

当常规 HTTP 爬虫被反爬拦截时，自动启动真实浏览器模拟人工操作：
  - 可见窗口模式（非 headless），模拟真人浏览
  - 隐身上下文（Stealth），绕过反爬检测
  - Cookie / 弹窗自动处理
  - 等待特定元素出现后提取数据
  - 自动滚动加载懒加载内容
  - 截图保存用于人工验证
  - 登录流程支持（可选）
  - 与 http_utils 降级链无缝衔接

依赖：pip install playwright && playwright install chromium
缺失时所有方法返回 None 并提示安装命令，不影响其他模块。

用法：
  from browser_scraper import BrowserScraper
  bs = BrowserScraper(headless=False)  # 可见模式，便于观察
  html = bs.fetch("https://www.example.com")
  # 或提取特定数据
  data = bs.extract_text("https://www.example.com", selector=".content")
  # 截图留存
  bs.screenshot("https://www.example.com", "output/shot.png")
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None  # type: ignore
    Page = None     # type: ignore

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_CACHE_DIR = DATA_DIR / "browser_cache"
BROWSER_CACHE_DIR.mkdir(exist_ok=True, parents=True)
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)
# v6.0.0: 浏览器会话状态持久化（Cookie / localStorage 跨进程复用）
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_STATE_DIR.mkdir(exist_ok=True, parents=True)
BROWSER_STATE_FILE = BROWSER_STATE_DIR / "state.json"

INSTALL_HINT = (
    "浏览器自动化模块需要 Playwright。请安装：\n"
    "  pip install playwright\n"
    "  playwright install chromium\n"
    "Mac/Linux 用户可能还需要: playwright install-deps chromium"
)

# ── 反检测隐身脚本（v4.7 升级：12+ 项指纹）─────────────────────────────
STEALTH_JS = r"""
(function() {
    'use strict';
    // ===== 1. 隐藏 webdriver 标记 =====
    try { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); } catch (e) {}

    // ===== 2. 伪造 plugins（含 PluginArray 原型，返回真实结构）=====
    try {
        const makePlugins = () => {
            const ps = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
            ];
            ps.item = (i) => ps[i] || null;
            ps.namedItem = (n) => ps.find(p => p.name === n) || null;
            ps.refresh = () => {};
            return ps;
        };
        const ps = makePlugins();
        try { Object.setPrototypeOf(ps, PluginArray.prototype); } catch (e) {}
        Object.defineProperty(navigator, 'plugins', { get: () => ps });
    } catch (e) {}

    // ===== 3. 伪造 languages =====
    try { Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] }); } catch (e) {}

    // ===== 4. 伪造 platform =====
    try { Object.defineProperty(navigator, 'platform', { get: () => 'Win32' }); } catch (e) {}

    // ===== 5. 伪造 hardwareConcurrency / deviceMemory =====
    try { Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); } catch (e) {}
    try { Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 }); } catch (e) {}

    // ===== 6. 伪造 permissions API（notifications 用真实状态）=====
    try {
        const origQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters && parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : origQuery(parameters)
        );
    } catch (e) {}

    // ===== 7. 伪造 window.chrome / chrome.runtime（headless 检测关键）=====
    try {
        window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
    } catch (e) {}

    // ===== 8. WebGL vendor/renderer 伪造 =====
    try {
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Google Inc. (Intel)';
            if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            return getParameter.call(this, parameter);
        };
    } catch (e) {}

    // ===== 9. outerWidth / outerHeight 不为 0（headless 常为 0）=====
    try { Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth }); } catch (e) {}
    try { Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 100 }); } catch (e) {}

    // ===== 10. connection.rtt 伪造 =====
    try {
        if (navigator.connection) Object.defineProperty(navigator.connection, 'rtt', { get: () => 100 });
    } catch (e) {}

    // ===== 11. 移除 PhantomJS / headless 痕迹 =====
    delete window.callPhantom;
    delete window._phantom;
    delete window.__phantomas;
})();
"""

# ── 广告/跟踪域名黑名单（v5.0.0 网络拦截去广告用）─────────────────────
AD_BLOCK_DOMAINS = {
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "google-analytics.com", "googletagmanager.com", "googletagservices.com",
    "hm.baidu.com", "cnzz.com", "adsense", "adservice",
    "scorecardresearch.com", "criteo.com", "taboola.com", "outbrain.com",
    "adservice.google", "amazon-adsystem.com",
}


def _should_block_url(url: str, resource_type: str) -> bool:
    """v5.0.0: 判定资源是否应拦截（广告/跟踪域的大资源，正文域名放行）。"""
    if resource_type not in ("image", "media", "font"):
        return False
    low = url.lower()
    return any(dom in low for dom in AD_BLOCK_DOMAINS)

# ── 常见 Cookie 弹窗选择器 ─────────────────────────────────────
COOKIE_CONSENT_SELECTORS = [
    # 中文
    "button:has-text('同意')", "button:has-text('接受')", "button:has-text('确定')",
    "button:has-text('知道了')", "button:has-text('允许')",
    "a:has-text('同意')", "span:has-text('同意')",
    ".cookie-accept", ".cookie-consent button",
    # 英文
    "button:has-text('Accept')", "button:has-text('Accept All')",
    "button:has-text('Agree')", "button:has-text('OK')",
    "button:has-text('Got it')", "button:has-text('I agree')",
    "button:has-text('Allow All')", "button:has-text('Consent')",
    # 通用
    "[aria-label='Accept cookies']", "[data-testid='cookie-accept']",
    "#accept-cookies", ".accept-cookies", "[id*='cookie'] button",
    ".cc-btn", ".cc_btn", ".cookie-btn",
]


class BrowserScraper:
    """浏览器自动化爬虫 — 类人操作模式

    headless=False: 可见窗口，随机延迟，模拟真人体浏览行为
    headless=True:  后台运行，速度更快但部分网站会检测到
    stealth=True:   注入反检测脚本，隐藏 webdriver 标记
    """

    def __init__(self, headless: bool = False, stealth: bool = True,
                 timeout_ms: int = 30000, viewport: dict = None,
                 proxy: Optional[Any] = None, ad_block: bool = True,
                 channel: str = "chromium"):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(INSTALL_HINT)
        self.headless = headless
        self.stealth = stealth
        self.timeout_ms = timeout_ms
        self.viewport = viewport or {"width": 1920, "height": 1080}
        # v5.0.0: proxy 支持（"http://host:port" / "socks5://host:port" / dict）
        self.proxy = proxy
        # v5.0.0: 网络拦截去广告（拦截广告/跟踪域大资源请求）
        self.ad_block = ad_block
        self.channel = channel or "chromium"
        self._playwright = None
        self._browser = None
        self._context = None
        self._last_page = None

    # ── v6.0.0: 会话保持（storage_state 持久化）──────────────────────

    def _load_storage_state(self) -> Optional[dict]:
        """加载持久化会话状态（Cookie / localStorage）。"""
        if BROWSER_STATE_FILE.exists():
            try:
                return json.loads(BROWSER_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def _save_storage_state(self):
        """保存当前上下文会话状态到磁盘，供下次进程复用。"""
        try:
            if self._context is not None:
                state = self._context.storage_state()
                BROWSER_STATE_FILE.write_text(
                    json.dumps(state, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    # ── 生命周期 ─────────────────────────────────────────────

    @staticmethod
    def _resolve_proxy(proxy: Any) -> dict:
        """归一化 proxy 配置为 Playwright 需要的 {server, username?, password?}。"""
        if isinstance(proxy, dict):
            return proxy
        return {"server": proxy}

    def _install_ad_block(self, context):
        """v5.0.0: 网络拦截去广告 — 按 resource_type + 域名黑名单拦截，正文域名放行。"""

        def _route(route):
            try:
                if _should_block_url(route.request.url, route.request.resource_type):
                    route.abort()
                else:
                    route.continue_()
            except Exception:
                try:
                    route.abort()
                except Exception:
                    pass

        try:
            context.route("**/*", _route)
        except Exception:
            pass

    def start(self):
        """启动浏览器（单例复用）。"""
        if self._browser is not None:
            return
        self._playwright = sync_playwright().start()
        launch_kwargs = dict(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        if self.proxy:
            launch_kwargs["proxy"] = self._resolve_proxy(self.proxy)
        self._browser = self._playwright.chromium.launch(**launch_kwargs)
        context_kwargs = dict(
            viewport=self.viewport,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        # v6.0.0: 复用上次会话状态（Cookie / localStorage）
        saved_state = self._load_storage_state()
        if saved_state:
            context_kwargs["storage_state"] = saved_state
        self._context = self._browser.new_context(**context_kwargs)
        if self.stealth:
            self._context.add_init_script(STEALTH_JS)
        if self.ad_block:
            self._install_ad_block(self._context)

    def stop(self):
        """关闭浏览器释放资源（先持久化会话状态）。"""
        self._save_storage_state()
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def new_page(self) -> Page:
        """创建新页面（带隐身脚本）。"""
        self.start()
        page = self._context.new_page()
        page.set_default_timeout(self.timeout_ms)
        self._last_page = page
        return page

    # ── v5.0.0 增强：并发标签页 + 统一重试 ─────────────────────

    def _with_retry(self, fn: Callable, retries: int = 2,
                    name: str = "") -> Any:
        """统一重试包装（随机退避）。供各抓取方法复用。"""
        for attempt in range(retries + 1):
            try:
                return fn()
            except Exception as e:
                if attempt < retries:
                    time.sleep(random.uniform(0.5, 2.0))
                else:
                    print(f"[BrowserScraper] {name or getattr(fn, '__name__', 'op')} 失败: {e}",
                          file=sys.stderr)
        return None

    def extract_many(self, urls: List[str], max_workers: int = 4) -> List[Tuple[str, Optional[str]]]:
        """v5.0.0: 并发标签页抓取多个 URL（复用同一 context），按输入序返回。

        Returns:
            [(url, html_or_None), ...] — 单个失败不阻塞整体。
        """
        if not urls:
            return []
        if not PLAYWRIGHT_AVAILABLE:
            return [(u, None) for u in urls]
        self.start()
        max_workers = min(max(1, max_workers), 8)
        results: List[Tuple[str, Optional[str]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(self._fetch_one_new_page, u): u for u in urls}
            for fut in as_completed(futures):
                u = futures[fut]
                try:
                    results.append((u, fut.result()))
                except Exception:
                    results.append((u, None))
        order = {u: i for i, u in enumerate(urls)}
        results.sort(key=lambda x: order[x[0]])
        return results

    def _fetch_one_new_page(self, url: str) -> Optional[str]:
        """并发标签页单 URL 抓取（独立 page，finally 关闭）。"""
        page = None
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.2, 0.6)
            return page.content()
        except Exception:
            return None
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

    # ── 核心抓取 ─────────────────────────────────────────────

    def fetch(self, url: str, wait_until: str = "domcontentloaded",
              wait_selector: str = None, scroll: bool = False,
              dismiss_cookies: bool = True, retries: int = 2,
              captcha_handoff: bool = True,
              include_iframes: bool = False) -> Optional[str]:
        """打开网页并返回完整 HTML。

        wait_until: domcontentloaded / load / networkidle
        wait_selector: 等待该 CSS 选择器出现后再提取
        scroll: 是否滚动页面加载懒加载内容
        dismiss_cookies: 是否自动点击 Cookie 弹窗
        retries: 超时/失败后重试次数（默认 2，随机退避）
        captcha_handoff: v6.0.0 检测到验证码时截图保存并返回 None（人工接管）
        include_iframes: v6.0.0 是否合并内嵌 iframe 的内容
        """
        if not PLAYWRIGHT_AVAILABLE:
            print(INSTALL_HINT, file=sys.stderr)
            return None
        for attempt in range(retries + 1):
            page = None
            try:
                page = self.new_page()
                page.goto(url, wait_until=wait_until, timeout=self.timeout_ms)
                self._human_delay(0.5, 1.5)

                if dismiss_cookies:
                    self._dismiss_cookie_popup(page)

                # v6.0.0: 验证码检测 → 截图 + 人工接管（不自动破解）
                if captcha_handoff:
                    cap = self._detect_captcha(page, url)
                    if cap:
                        print(f"[BrowserScraper] 验证码接管: {cap.get('screenshot', '')}",
                              file=sys.stderr)
                        return None

                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=self.timeout_ms)
                    self._human_delay(0.3, 0.8)

                if scroll:
                    self._random_scroll(page, times=random.randint(3, 6))

                html = page.content()
                if include_iframes:
                    html = self._merge_iframes(html, page)
                return html
            except PlaywrightTimeout:
                if attempt < retries:
                    time.sleep(random.uniform(1, 3))
                    continue
                return None
            except Exception as e:
                # v6.0.0: 错误恢复 — 页面崩溃/目标关闭时重建页面重试
                msg = str(e).lower()
                if attempt < retries and (
                    "disconnected" in msg or "target closed" in msg
                    or "crash" in msg or "frame was detached" in msg
                ):
                    time.sleep(random.uniform(1, 2))
                    continue
                print(f"[BrowserScraper] fetch 失败: {e}", file=sys.stderr)
                return None
            finally:
                if page is not None:
                    try:
                        page.close()
                    except Exception:
                        pass
        return None

    def extract_text(self, url: str, selector: str = "body",
                     wait_selector: str = None, scroll: bool = False,
                     dismiss_cookies: bool = True) -> Optional[str]:
        """提取指定元素的文本内容。"""
        page = None
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.5, 1.5)

            if dismiss_cookies:
                self._dismiss_cookie_popup(page)

            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.timeout_ms)

            if scroll:
                self._auto_scroll(page)

            text = page.text_content(selector, timeout=self.timeout_ms)
            return text.strip() if text else None
        except PlaywrightTimeout:
            return None
        except Exception as e:
            print(f"[BrowserScraper] extract_text 失败: {e}", file=sys.stderr)
            return None
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

    def extract_multiple(self, url: str, selectors: Dict[str, str],
                         **kwargs) -> Dict[str, Optional[str]]:
        """批量提取多个选择器的文本。selectors: {key: css_selector}"""
        results = {}
        page = None
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.5, 1.5)
            if kwargs.get("dismiss_cookies", True):
                self._dismiss_cookie_popup(page)
            if kwargs.get("scroll", False):
                self._auto_scroll(page)

            for key, sel in selectors.items():
                try:
                    el = page.query_selector(sel)
                    results[key] = el.text_content().strip() if el else None
                except Exception:
                    results[key] = None
        except Exception as e:
            print(f"[BrowserScraper] extract_multiple 失败: {e}", file=sys.stderr)
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
        return results

    def extract_table(self, url: str, table_selector: str = "table",
                      **kwargs) -> List[Dict[str, str]]:
        """提取 HTML 表格为 dict 列表。"""
        rows_data = []
        page = None
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.5, 1.5)
            if kwargs.get("dismiss_cookies", True):
                self._dismiss_cookie_popup(page)
            if kwargs.get("scroll", False):
                self._auto_scroll(page)

            rows = page.query_selector_all(f"{table_selector} tr")
            if not rows:
                return rows_data

            # 第一行作表头
            headers = [th.text_content().strip()
                       for th in rows[0].query_selector_all("th,td")]

            for row in rows[1:]:
                cells = [td.text_content().strip()
                         for td in row.query_selector_all("td")]
                if cells:
                    row_dict = {}
                    for i, cell in enumerate(cells):
                        key = headers[i] if i < len(headers) else f"col_{i}"
                        row_dict[key] = cell
                    rows_data.append(row_dict)
        except Exception as e:
            print(f"[BrowserScraper] extract_table 失败: {e}", file=sys.stderr)
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
        return rows_data

    # ── 截图 ─────────────────────────────────────────────────

    def screenshot(self, url: str, output_path: str = None,
                   full_page: bool = True, **kwargs) -> Optional[str]:
        """打开网页并截图保存。返回保存路径。"""
        if not output_path:
            ts = time.strftime("%Y%m%d_%H%M%S")
            domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0][:30]
            output_path = str(SCREENSHOT_DIR / f"{domain}_{ts}.png")

        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.5, 1.5)
            if kwargs.get("dismiss_cookies", True):
                self._dismiss_cookie_popup(page)
            page.screenshot(path=output_path, full_page=full_page)
            page.close()
            return output_path
        except Exception as e:
            print(f"[BrowserScraper] screenshot 失败: {e}", file=sys.stderr)
            return None

    # ── 交互操作 ─────────────────────────────────────────────

    def click_and_wait(self, url: str, click_selector: str,
                       wait_selector: str = None) -> Optional[str]:
        """点击某元素后等待并返回新页面的 HTML。"""
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._dismiss_cookie_popup(page)
            page.click(click_selector, timeout=self.timeout_ms)
            self._human_delay(0.5, 1.5)
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.timeout_ms)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            print(f"[BrowserScraper] click_and_wait 失败: {e}", file=sys.stderr)
            return None

    def type_and_submit(self, url: str, input_selector: str, text: str,
                        submit_selector: str = None) -> Optional[str]:
        """在输入框中输入文本，可选提交。返回操作后页面 HTML。"""
        try:
            page = self.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._dismiss_cookie_popup(page)
            page.fill(input_selector, text, timeout=self.timeout_ms)
            self._human_delay(0.3, 0.8)
            if submit_selector:
                page.click(submit_selector, timeout=self.timeout_ms)
                page.wait_for_load_state("domcontentloaded")
            self._human_delay(0.5, 1.0)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            print(f"[BrowserScraper] type_and_submit 失败: {e}", file=sys.stderr)
            return None

    def login_and_fetch(self, url: str, login_url: str,
                        username_sel: str, password_sel: str,
                        submit_sel: str, username: str, password: str,
                        target_selector: str = None) -> Optional[str]:
        """登录流程：先访问登录页填入凭据，再跳转到目标页抓取。"""
        try:
            page = self.new_page()
            # 登录
            page.goto(login_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._human_delay(0.5, 1.0)
            page.fill(username_sel, username, timeout=self.timeout_ms)
            self._human_delay(0.2, 0.5)
            page.fill(password_sel, password, timeout=self.timeout_ms)
            self._human_delay(0.3, 0.8)
            page.click(submit_sel, timeout=self.timeout_ms)
            page.wait_for_load_state("domcontentloaded")
            self._human_delay(1.0, 2.0)
            # 跳转目标页
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            if target_selector:
                page.wait_for_selector(target_selector, timeout=self.timeout_ms)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            print(f"[BrowserScraper] login_and_fetch 失败: {e}", file=sys.stderr)
            return None

    # ── 智能回退 ─────────────────────────────────────────────

    def smart_fetch(self, url: str, html_text: Optional[str] = None,
                    **kwargs) -> Optional[str]:
        """智能抓取：优先用传入的 html_text；失败则启动浏览器。

        这是最推荐的使用方式——先尝试常规 http_utils 爬取，
        返回空时自动调用浏览器 fetch() 兜底。
        """
        if html_text and len(html_text) > 200:
            return html_text
        return self.fetch(url, **kwargs)

    # ── 便捷函数 ─────────────────────────────────────────────

    def fetch_with_screenshot(self, url: str) -> dict:
        """抓取+截图，返回 {html, screenshot_path}。"""
        html = self.fetch(url)
        shot = self.screenshot(url)
        return {"html": html, "screenshot_path": shot}

    # ── 内部辅助 ─────────────────────────────────────────────

    def _dismiss_cookie_popup(self, page: Page):
        """尝试点击页面上的 Cookie 同意按钮。"""
        for selector in COOKIE_CONSENT_SELECTORS:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click(timeout=3000)
                    return
            except Exception:
                continue

    def _auto_scroll(self, page: Page, times: int = 5):
        """模拟人工滚动，触发懒加载内容。"""
        for i in range(times):
            page.evaluate(f"window.scrollTo(0, {(i + 1) * 800})")
            self._human_delay(0.3, 0.8)
        # 滚回顶部
        page.evaluate("window.scrollTo(0, 0)")

    @staticmethod
    def _human_delay(min_s: float = 0.1, max_s: float = 0.5):
        """随机延迟，模拟人类浏览速度。"""
        time.sleep(random.uniform(min_s, max_s))

    # ── v6.0.0: 验证码检测 → 人工接管 ───────────────────────────

    CAPTCHA_TEXT_SIGNS = (
        "captcha", "recaptcha", "verify you are human", "verify you're a human",
        "unusual traffic", "人机验证", "安全验证", "滑动验证", "安全校验",
        "请输入验证码", "请完成验证", "拖动滑块", "点选验证",
    )

    def _detect_captcha(self, page: Page, url: str = "") -> Optional[Dict[str, Any]]:
        """检测验证码页面 → 截图保存 → 返回检测结果（不自动破解，等待人工）。

        Returns:
            {"captcha": 命中特征, "screenshot": 截图路径 | None}；未命中返回 None
        """
        try:
            body = (page.text_content("body") or "")[:4000].lower()
        except Exception:
            return None
        for sign in self.CAPTCHA_TEXT_SIGNS:
            if sign in body:
                shot = None
                try:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    domain = re.sub(r"https?://(www\.)?", "", url or "").split("/")[0][:20] or "unknown"
                    shot = str(SCREENSHOT_DIR / f"captcha_{domain}_{ts}.png")
                    page.screenshot(path=shot)
                    # v7.0.0: 空截图（<100B）是探测失败的产物，落盘即垃圾，直接删
                    if Path(shot).stat().st_size < 100:
                        Path(shot).unlink(missing_ok=True)
                        shot = None
                except Exception:
                    shot = None
                print(f"[BrowserScraper] ⚠️ 检测到验证码（{sign}）"
                      f"{f'，截图已保存: {shot}' if shot else ''} — 请人工处理或稍后重试",
                      file=sys.stderr)
                return {"captcha": sign, "screenshot": shot}
        return None

    # ── v6.0.0: iframe 内容合并 ────────────────────────────────

    def _merge_iframes(self, html: str, page: Page,
                       max_frames: int = 8) -> str:
        """提取页面内嵌 iframe 的 HTML 并合并到主文档（正文常在 iframe 中）。

        合并内容用 HTML 注释包裹，供下游解析器识别。
        """
        try:
            frames = page.frames
            parts = []
            for fr in frames[1:max_frames + 1]:  # frames[0] 是主 frame
                try:
                    content = fr.content()
                    if content and len(content) > 500:
                        parts.append(content)
                except Exception:
                    continue
            if parts:
                sep = "\n<!-- v6.0.0-iframe-content -->\n"
                html = html + sep + sep.join(parts)
        except Exception:
            pass
        return html

    # ── v6.0.0: 随机悬停 / 随机标签页切换 ─────────────────────────

    def _random_hover(self, page: Page, tries: int = 3):
        """随机悬停菜单/下拉元素，触发动态子菜单（模拟真人浏览）。"""
        for _ in range(tries):
            try:
                els = page.query_selector_all(
                    "nav a, .menu li, .dropdown, .nav-item, [class*='nav'] a")
                if not els:
                    return
                el = random.choice(els)
                if el.is_visible():
                    el.hover(timeout=3000)
                    self._human_delay(0.3, 0.8)
            except Exception:
                continue

    def _random_tab_switch(self, page: Page, prob: float = 0.1):
        """低频（默认 10%）开新标签页浏览后切回，模拟真人多标签行为。"""
        if random.random() >= prob:
            return
        try:
            ctx = page.context
            p2 = ctx.new_page()
            try:
                p2.goto("about:blank")
                self._human_delay(0.5, 1.5)
            except Exception:
                pass
            try:
                p2.close()
            except Exception:
                pass
            page.bring_to_front()
        except Exception:
            pass

    # ── v4.5 类人操作增强 ─────────────────────────────────────

    def _human_mouse_move(self, page: Page, target_x: float, target_y: float,
                          steps: int = 25):
        """模拟鼠标移动到目标位置（贝塞尔曲线 + 随机偏移 + 随机速度）。

        使用三次贝塞尔曲线生成平滑轨迹，中途加入微小随机抖动。
        """
        try:
            # 起点：随机在页面中上区域
            start_x = random.uniform(100, min(target_x + 200, 800))
            start_y = random.uniform(100, min(target_y + 200, 600))
            # 控制点：随机偏移形成弧线
            cp1_x = start_x + random.uniform(-150, 150)
            cp1_y = start_y + random.uniform(-100, 100)
            cp2_x = target_x + random.uniform(-100, 100)
            cp2_y = target_y + random.uniform(-100, 100)

            for i in range(steps + 1):
                t = i / steps
                # 三次贝塞尔曲线: B(t) = (1-t)³P0 + 3(1-t)²t·P1 + 3(1-t)t²·P2 + t³P3
                x = ((1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x +
                     3*(1-t)*t**2 * cp2_x + t**3 * target_x)
                y = ((1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y +
                     3*(1-t)*t**2 * cp2_y + t**3 * target_y)
                # 添加微小抖动
                x += random.uniform(-2, 2)
                y += random.uniform(-1, 1)
                page.mouse.move(x, y)
                # 随机速度：每步 5-25ms
                time.sleep(random.uniform(0.005, 0.025))
        except Exception:
            # 浏览器不可用时跳过
            pass

    def _human_type(self, page: Page, selector: str, text: str,
                    typo_rate: float = 0.03):
        """模拟人类打字：随机字符间隔 + 偶尔打错+退格修正。

        v6.0.0: 15% 概率走「粘贴」路径（insert_text 一次注入），
        模拟真人复制粘贴长文本，避免逐字输入的机械特征。

        Args:
            page: Playwright Page
            selector: 目标输入框 CSS 选择器
            text: 要输入的文本
            typo_rate: 打错概率（默认 3%）
        """
        try:
            page.click(selector)
            self._human_delay(0.1, 0.3)
            # v6.0.0: 低频粘贴模式（长文本更真实）
            if len(text) > 10 and random.random() < 0.15:
                page.keyboard.insert_text(text)
                self._human_delay(0.2, 0.6)
                return
            for ch in text:
                if random.random() < typo_rate and ch.isalpha():
                    # 模拟打错 — 输入相邻键位然后退格
                    typo = chr(ord(ch) + random.choice([-1, 1]))
                    page.keyboard.type(typo, delay=random.randint(30, 80))
                    self._human_delay(0.05, 0.15)
                    page.keyboard.press("Backspace")
                    self._human_delay(0.05, 0.1)
                # 正常输入当前字符
                page.keyboard.type(ch, delay=random.randint(50, 200))
                # 句子间额外停顿
                if ch in "。！？\n":
                    self._human_delay(0.2, 0.6)
        except Exception:
            pass

    def _human_dwell(self, min_s: float = 0.5, max_s: float = 2.0,
                     content_length: int = 0):
        """自适应停留时间：内容越长看得越久。"""
        # 基础随机停留
        base = random.uniform(min_s, max_s)
        # 内容长度加成：每 1000 字符增加 0.1-0.3 秒
        if content_length > 0:
            bonus = min(2.0, content_length / 1000 * random.uniform(0.1, 0.3))
            base += bonus
        time.sleep(base)

    # ── v6.0.0: 多样化滚动模式 ──────────────────────────────────

    SCROLL_MODES = ("fast_browse", "slow_read", "segmented", "rewind")

    def _random_scroll(self, page: Page, times: int = 5,
                       mode: Optional[str] = None):
        """随机滚动模式：4 种人类浏览行为随机切换。

        fast_browse: 快速扫读（大步长 + 短停顿）
        slow_read:   慢速精读（小步长 + 长停顿）
        segmented:   分段阅读（中步长 + 分段停顿）
        rewind:      扫读+回看（随机回滚，原 v4.5 行为）
        """
        mode = mode or random.choice(self.SCROLL_MODES)
        try:
            if mode == "fast_browse":
                for _ in range(times):
                    page.evaluate(f"window.scrollBy(0, {random.randint(500, 900)})")
                    time.sleep(random.uniform(0.1, 0.4))
            elif mode == "slow_read":
                for _ in range(times):
                    page.evaluate("window.scrollBy(0, 300)")
                    time.sleep(random.uniform(1.0, 2.5))
            elif mode == "segmented":
                for _ in range(times):
                    page.evaluate(f"window.scrollBy(0, {random.randint(200, 500)})")
                    time.sleep(random.uniform(0.4, 1.2))
                    time.sleep(random.uniform(0.5, 1.5))
            else:  # rewind
                for i in range(times):
                    distance = random.randint(200, 900)
                    if random.random() < 0.2 and i > 0:
                        distance = -random.randint(100, 300)
                    page.evaluate(f"window.scrollBy(0, {distance})")
                    time.sleep(random.uniform(0.2, 1.5))
        except Exception:
            pass
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        self._human_delay(0.3, 0.6)

    def _random_viewport(self, page: Page):
        """随机切换 viewport 尺寸，模拟不同设备分辨率。"""
        viewports = [
            {"width": 1920, "height": 1080},  # 标准桌面
            {"width": 1680, "height": 1050},  # 常见笔记本
            {"width": 1440, "height": 900},   # 小型桌面
            {"width": 1366, "height": 768},   # 常见笔记本
            {"width": 2560, "height": 1440},  # 2K 桌面
        ]
        vp = random.choice(viewports)
        try:
            page.set_viewport_size(vp)
        except Exception:
            pass

    def humanlike_fetch(self, url: str, scroll: bool = True,
                        dwell: bool = True, random_viewport: bool = True,
                        mouse_simulation: bool = True,
                        input_selector: str = None,
                        input_text: str = None,
                        think_time: bool = True,
                        hover: bool = True,
                        tab_switch: bool = True,
                        captcha_handoff: bool = True,
                        include_iframes: bool = False) -> Optional[str]:
        """类人模式抓取：随机 viewport → 打开 → 阅读停顿 → 鼠标移动 → 悬停 → 滚动 → (表单输入) → HTML。

        一键开启所有类人行为，适合高反爬网站。

        Args:
            url: 目标网址
            scroll: 是否随机滚动（默认 True）
            dwell: 是否自适应停留阅读（默认 True）
            random_viewport: 是否随机 viewport 尺寸（默认 True）
            mouse_simulation: 是否模拟贝塞尔鼠标移动（默认 True，v4.7 新增）
            input_selector: 表单输入框 CSS 选择器（配合 input_text）
            input_text: 需要模拟输入的文本（如搜索关键词）
            think_time: v6.0.0 阅读停顿 — 页面加载后随机停留 2-8s 模拟阅读
            hover: v6.0.0 随机悬停菜单触发下拉内容
            tab_switch: v6.0.0 低频开新标签页再切回（模拟多标签）
            captcha_handoff: v6.0.0 验证码检测 → 截图保存 + 返回 None（人工接管）
            include_iframes: v6.0.0 合并内嵌 iframe 内容
        """
        page = None
        try:
            page = self.new_page()
            if random_viewport:
                self._random_viewport(page)

            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            self._dismiss_cookie_popup(page)
            self._human_delay(0.5, 1.5)

            # v6.0.0: 验证码检测 → 截图 + 人工接管（不自动破解）
            if captcha_handoff:
                cap = self._detect_captcha(page, url)
                if cap:
                    return None

            # v6.0.0: 随机标签页切换（低频）
            if tab_switch:
                self._random_tab_switch(page)

            # ★ v4.7：贝塞尔鼠标移动 2-3 次（模拟真人在页面上移动光标）
            if mouse_simulation:
                try:
                    vp = page.viewport_size or {"width": 1920, "height": 1080}
                    for _ in range(random.randint(2, 4)):
                        self._human_mouse_move(
                            page,
                            random.uniform(100, vp["width"] - 100),
                            random.uniform(100, vp["height"] - 100),
                            steps=random.randint(20, 30),
                        )
                        self._human_delay(0.3, 0.8)
                except Exception:
                    pass

            if dwell:
                content_len = 0
                try:
                    body_text = page.text_content("body") or ""
                    content_len = len(body_text)
                except Exception:
                    pass
                self._human_dwell(0.5, 2.0, content_len)

            # v6.0.0: 阅读停顿 — 加载后停留 2-8 秒模拟真人阅读
            if think_time:
                time.sleep(random.uniform(2.0, 8.0))

            # v6.0.0: 随机悬停触发下拉菜单
            if hover:
                self._random_hover(page)

            if scroll:
                self._random_scroll(page, times=random.randint(3, 7))

            # ★ v4.7：表单输入（如搜索框）
            if input_selector and input_text:
                self._human_type(page, input_selector, input_text)
                self._human_delay(0.5, 1.5)

            html = page.content()
            if include_iframes:
                html = self._merge_iframes(html, page)
            return html
        except Exception as e:
            print(f"[BrowserScraper] humanlike_fetch 失败: {e}", file=sys.stderr)
            return None
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass


# ── 模块级便捷函数 ──────────────────────────────────────────

# v5.0.0: 进程级单例浏览器（供 sentiment / web_parser 复用，避免每源冷启动）
_BS_SINGLETON: Optional[BrowserScraper] = None
_BS_LOCK = threading.Lock()


def _get_browser_scraper(headless: bool = True, **kwargs) -> Optional["BrowserScraper"]:
    """获取进程级单例 BrowserScraper（惰性创建，跨源复用）。

    Args:
        headless: 默认后台运行（舆情兜底场景）。
        **kwargs: 透传给 BrowserScraper（proxy/ad_block 等）。

    Returns:
        BrowserScraper 单例；Playwright 不可用时返回 None。
    """
    global _BS_SINGLETON
    if not PLAYWRIGHT_AVAILABLE:
        return None
    with _BS_LOCK:
        if _BS_SINGLETON is None:
            try:
                _BS_SINGLETON = BrowserScraper(headless=headless, **kwargs)
                _BS_SINGLETON.start()
            except Exception:
                _BS_SINGLETON = None
        return _BS_SINGLETON


def release_browser():
    """关闭并释放进程级单例浏览器。"""
    global _BS_SINGLETON
    with _BS_LOCK:
        if _BS_SINGLETON is not None:
            try:
                _BS_SINGLETON.stop()
            except Exception:
                pass
            _BS_SINGLETON = None


def browser_fetch(url: str, headless: bool = False,
                  scroll: bool = False) -> Optional[str]:
    """一行代码启动浏览器抓取。"""
    with BrowserScraper(headless=headless) as bs:
        return bs.fetch(url, scroll=scroll)


def browser_screenshot(url: str, output_path: str = None) -> Optional[str]:
    """一行代码截图。"""
    with BrowserScraper(headless=True) as bs:
        return bs.screenshot(url, output_path)


def smart_fallback(url: str, http_html: Optional[str],
                   headless: bool = False) -> Optional[str]:
    """智能回退：HTTP 返回空 → 浏览器兜底。"""
    if http_html and len(http_html) > 200:
        return http_html
    return browser_fetch(url, headless=headless)


# ── v4.5 类人翻页 / 图文全抓（增强） ─────────────────────────
# 以下方法通过 monkey-patch 追加到 BrowserScraper 类（保持模块化）

_IMG_TAG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
def _paginate(self, url: str, next_selector: str,
              max_pages: int = 10,
              stop_when_no_change: bool = True,
              until_selector: str = None,
              wait_after_click: float = 1.0,
              total_timeout: float = 60.0,
              scroll_each: bool = True,
              dismiss_cookies: bool = True) -> Dict[str, Any]:
    """类人翻页：点 next → 等出现内容 → 抓全文 → 累积到 pages。

    停止条件（任一触发）：
        1. 连续 2 轮 next_selector 不存在
        2. 连续 2 轮新页面 hash 与上一轮相同（去除时间戳）
        3. 达到 max_pages
        4. 出现 until_selector
        5. 累计 > total_timeout 秒

    Returns:
        {"pages": [{"url", "html", "page_num"}], "total_pages": int,
         "stopped_reason": str, "elapsed_seconds": float}
    """
    start_time = time.time()
    pages: List[Dict[str, Any]] = []
    last_hashes: List[str] = []
    stopped_reason = "max_pages"
    current_url = url

    page_obj = self.new_page()
    try:
        page_obj.goto(current_url, wait_until="domcontentloaded",
                      timeout=self.timeout_ms)
        if dismiss_cookies:
            self._dismiss_cookie_popup(page_obj)
        self._human_delay(0.5, 1.5)

        for page_num in range(1, max_pages + 1):
            if total_timeout and (time.time() - start_time) > total_timeout:
                stopped_reason = "total_timeout"
                break

            # 检查 until_selector
            if until_selector:
                try:
                    el = page_obj.query_selector(until_selector)
                    if el:
                        stopped_reason = "until_selector_found"
                        break
                except Exception:
                    pass

            # 等内容稳定
            self._human_delay(0.3, 0.8)
            if scroll_each:
                self._auto_scroll(page_obj, times=3)
            html = page_obj.content()
            content_hash = hashlib.md5(
                _strip_dynamic_markers(html).encode("utf-8", "ignore")
            ).hexdigest()

            pages.append({
                "url": current_url,
                "html": html,
                "page_num": page_num,
            })

            # 检测重复（连续 2 轮相同）
            if stop_when_no_change and len(last_hashes) >= 1 \
                    and last_hashes[-1] == content_hash:
                stopped_reason = "no_change_2x"
                break
            last_hashes.append(content_hash)
            if len(last_hashes) > 3:
                last_hashes.pop(0)

            # 找"下一页"按钮
            if page_num >= max_pages:
                stopped_reason = "max_pages"
                break

            try:
                next_btn = page_obj.query_selector(next_selector)
            except Exception:
                next_btn = None
            if not next_btn:
                stopped_reason = "next_not_found"
                break
            try:
                if not next_btn.is_visible():
                    stopped_reason = "next_not_visible"
                    break
                next_btn.click(timeout=5000)
                page_obj.wait_for_load_state("domcontentloaded",
                                             timeout=self.timeout_ms)
                self._human_delay(wait_after_click, wait_after_click + 0.5)
                current_url = page_obj.url
            except Exception:
                stopped_reason = "next_click_failed"
                break
    finally:
        try:
            page_obj.close()
        except Exception:
            pass

    return {
        "pages": pages,
        "total_pages": len(pages),
        "stopped_reason": stopped_reason,
        "elapsed_seconds": round(time.time() - start_time, 2),
    }


def _extract_links(self, url: str, selector: str = "a[href]",
                   base: str = None,
                   dismiss_cookies: bool = True) -> List[Dict[str, str]]:
    """提取页面所有链接（href + 文本 + 内/外链标记）。

    Returns:
        [{"href", "text", "type": "internal"|"external", "domain"}]
    """
    out: List[Dict[str, str]] = []
    page = None
    try:
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if dismiss_cookies:
            self._dismiss_cookie_popup(page)
        self._human_delay(0.3, 0.8)
        base_domain = urlparse(base or url).netloc
        links = page.query_selector_all(selector)
        for el in links:
            try:
                href = el.get_attribute("href") or ""
                text = (el.text_content() or "").strip()[:100]
                if not href or href.startswith(("javascript:", "mailto:", "#")):
                    continue
                full_href = urljoin(base or url, href)
                link_domain = urlparse(full_href).netloc
                link_type = "internal" if link_domain == base_domain else "external"
                out.append({"href": full_href, "text": text,
                            "type": link_type, "domain": link_domain})
            except Exception:
                continue
    except Exception as e:
        print(f"[BrowserScraper] extract_links 失败: {e}", file=sys.stderr)
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
    return out


def _follow_links(self, list_url: str, link_selector: str,
                  content_selector: Optional[str] = None,
                  max_links: int = 20,
                  wait_after_goto: float = 1.0,
                  dismiss_cookies: bool = True) -> List[Dict[str, Any]]:
    """列表页 → 逐条进入详情页 → 返回正文列表。

    Returns:
        [{"url", "html", "text", "title"}]
    """
    results: List[Dict[str, Any]] = []
    page = None
    try:
        page = self.new_page()
        page.goto(list_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if dismiss_cookies:
            self._dismiss_cookie_popup(page)
        self._human_delay(0.5, 1.0)

        hrefs = page.eval_on_selector_all(
            link_selector,
            "els => els.map(e => e.href).filter(h => h && !h.startsWith('javascript:'))"
        )
        if not hrefs:
            return results

        for href in hrefs[:max_links]:
            try:
                page.goto(href, wait_until="domcontentloaded",
                          timeout=self.timeout_ms)
                self._human_delay(wait_after_goto, wait_after_goto + 0.5)
                html = page.content()
                text = ""
                title = ""
                if content_selector:
                    el = page.query_selector(content_selector)
                    if el:
                        text = (el.text_content() or "").strip()
                else:
                    text = page.text_content("body") or ""
                title_el = page.query_selector("title")
                if title_el:
                    title = (title_el.text_content() or "").strip()[:200]
                results.append({"url": href, "html": html,
                                "text": text, "title": title})
            except Exception as e:
                print(f"[BrowserScraper] follow_links 单条失败 {href}: {e}",
                      file=sys.stderr)
    except Exception as e:
        print(f"[BrowserScraper] follow_links 失败: {e}", file=sys.stderr)
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
    return results


def _download_images(self, html: str, base_url: str,
                     output_dir: str,
                     max_images: int = 10,
                     inline_svg: str = "preserve",
                     same_url_dedup: bool = True) -> Dict[str, Any]:
    """解析 HTML 中的 <img>/<source>/<image> → 下载到 output_dir → 返回替换映射。

    策略：
        - URL 标准化（去 ?v=xxx）作为 cache key
        - 同 URL 多处引用 → 只下载一次
        - 失败保留原 URL（不删 src）
        - 总量限制 max_images（默认 10）

    Args:
        html: HTML 字符串
        base_url: 用于相对 URL 转绝对
        output_dir: 图片输出目录
        max_images: 最大下载数
        inline_svg: "preserve" | "rasterize" | "skip"
        same_url_dedup: 是否对相同 URL 去重

    Returns:
        {"downloaded": [(local_path, original_url)], "image_map": {orig: local},
         "skipped": [orig_urls], "errors": [...]}
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_map: Dict[str, str] = {}
    downloaded: List[tuple] = []
    skipped: List[str] = []
    errors: List[str] = []

    # 提取所有 <img src>
    seen_urls: Dict[str, str] = {}  # normalized_url -> local_path
    matches = list(_IMG_TAG_RE.finditer(html))
    if len(matches) > max_images:
        skipped = [f"total {len(matches)} > max_images {max_images}"] \
            + [m.group(1) for m in matches[max_images:]]
        matches = matches[:max_images]

    import urllib.request
    for m in matches:
        raw_url = m.group(1)
        full_url = urljoin(base_url, raw_url)
        # URL 标准化
        parsed = urlparse(full_url)
        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if same_url_dedup and norm in seen_urls:
            image_map[full_url] = seen_urls[norm]
            continue

        # 推断扩展名
        ext = _guess_image_ext(full_url)
        # 文件名用 URL 哈希
        fname = hashlib.md5(norm.encode("utf-8")).hexdigest()[:16] + ext
        local_path = out_dir / fname

        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; cn-financial-scraper/4.5)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                if len(data) > 10 * 1024 * 1024:  # 单张 >10MB 跳过
                    skipped.append(full_url)
                    continue
                local_path.write_bytes(data)
            downloaded.append((str(local_path), full_url))
            seen_urls[norm] = str(local_path)
            image_map[full_url] = str(local_path)
        except Exception as e:
            errors.append(f"{full_url}: {e}")
            skipped.append(full_url)

    return {"downloaded": downloaded, "image_map": image_map,
            "skipped": skipped, "errors": errors,
            "total_found": len(_IMG_TAG_RE.findall(html))}


def _capture_canvas(self, url: str, selector: str = "canvas",
                    output_dir: Optional[str] = None,
                    wait_seconds: float = 2.0,
                    dismiss_cookies: bool = True) -> List[str]:
    """对每个 <canvas> 元素等待 JS 渲染后截图保存为 PNG。

    Returns:
        保存的 PNG 文件路径列表
    """
    out_paths: List[str] = []
    if output_dir is None:
        output_dir = str(SCREENSHOT_DIR)
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    page = None
    try:
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if dismiss_cookies:
            self._dismiss_cookie_popup(page)
        self._human_delay(wait_seconds, wait_seconds + 1.0)
        canvases = page.query_selector_all(selector)
        ts = time.strftime("%Y%m%d_%H%M%S")
        for i, canvas in enumerate(canvases):
            try:
                png_path = out_p / f"canvas_{ts}_{i}.png"
                canvas.screenshot(path=str(png_path))
                out_paths.append(str(png_path))
            except Exception as e:
                print(f"[BrowserScraper] capture_canvas 单个失败: {e}",
                      file=sys.stderr)
    except Exception as e:
        print(f"[BrowserScraper] capture_canvas 失败: {e}", file=sys.stderr)
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
    return out_paths


def _fetch_full_article(self, url: str,
                        image_strategy: str = "download",
                        max_pages: int = 1,
                        paginate: bool = False,
                        next_selector: Optional[str] = None,
                        max_images: int = 10,
                        media_dir: Optional[str] = None,
                        dismiss_cookies: bool = True) -> Dict[str, Any]:
    """主入口：单页 fetch + 翻页 + 图片本地化 + 返回结构化结果。

    Args:
        url: 起始 URL
        image_strategy: "download" | "none"
        max_pages: 最多翻几页（paginate=True 时生效）
        paginate: 是否自动翻页
        next_selector: "下一页"选择器（paginate=True 时必需）
        max_images: 单篇最多下载图片数
        media_dir: 图片输出目录（默认 data/media/<domain>/<timestamp>/）

    Returns:
        {"pages": [{"url","html","page_num"}],
         "images": [(local_path, original_url)],
         "image_map": {orig: local},
         "canvases": [png_paths],
         "elapsed_seconds": float,
         "url": str}
    """
    start_time = time.time()
    domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0][:30]
    if media_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        media_dir = str(DATA_DIR / "media" / domain / ts)

    pages_data: List[Dict[str, Any]] = []
    images: List[tuple] = []
    image_map: Dict[str, str] = {}
    canvases: List[str] = []

    try:
        if paginate and next_selector:
            paginate_result = self.paginate(
                url, next_selector, max_pages=max_pages,
                dismiss_cookies=dismiss_cookies,
            )
            pages_data = paginate_result["pages"]
        else:
            html = self.fetch(url, scroll=True, dismiss_cookies=dismiss_cookies)
            if html:
                pages_data = [{"url": url, "html": html, "page_num": 1}]

        # 下载图片
        if image_strategy == "download" and pages_data:
            all_imgs: List[tuple] = []
            all_map: Dict[str, str] = {}
            for p in pages_data:
                result = self.download_images(
                    p["html"], p["url"], media_dir,
                    max_images=max_images,
                )
                all_imgs.extend(result["downloaded"])
                all_map.update(result["image_map"])
            images = all_imgs
            image_map = all_map

        # 截图 canvas（仅首页）
        if pages_data:
            canvases = self.capture_canvas(
                pages_data[0]["url"], output_dir=media_dir,
                dismiss_cookies=dismiss_cookies,
            )
    except Exception as e:
        print(f"[BrowserScraper] fetch_full_article 失败: {e}", file=sys.stderr)

    return {
        "url": url,
        "pages": pages_data,
        "images": images,
        "image_map": image_map,
        "canvases": canvases,
        "media_dir": media_dir,
        "elapsed_seconds": round(time.time() - start_time, 2),
    }


def _strip_dynamic_markers(html: str) -> str:
    """去掉动态时间戳/计数器，便于翻页停止判定。"""
    # 去掉 <script> 内的动态内容
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    # 去掉常见时间戳
    html = re.sub(r"\b\d{10,13}\b", "TS", html)
    html = re.sub(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "DT", html)
    return html


def _guess_image_ext(url: str) -> str:
    """从 URL 推断图片扩展名。"""
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"  # 默认


# 把上述函数挂到 BrowserScraper 类
BrowserScraper.paginate = _paginate
BrowserScraper.extract_links = _extract_links
BrowserScraper.follow_links = _follow_links
BrowserScraper.download_images = _download_images
BrowserScraper.capture_canvas = _capture_canvas
BrowserScraper.fetch_full_article = _fetch_full_article


# ── CLI ──────────────────────────────────────────────────────

def main():
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT)
        return

    import argparse
    ap = argparse.ArgumentParser(description="浏览器自动化爬虫")
    ap.add_argument("url", help="目标网址")
    ap.add_argument("--visible", action="store_true", help="可见窗口模式")
    ap.add_argument("--screenshot", action="store_true", help="截图保存")
    ap.add_argument("--scroll", action="store_true", help="自动滚动加载")
    ap.add_argument("--selector", help="提取指定 CSS 选择器的文本")
    ap.add_argument("--wait", help="等待该选择器出现后再提取")
    ap.add_argument("--output", help="HTML 输出文件路径")
    args = ap.parse_args()

    with BrowserScraper(headless=not args.visible) as bs:
        if args.screenshot:
            path = bs.screenshot(args.url)
            print(f"截图: {path}")

        if args.selector:
            text = bs.extract_text(args.url, selector=args.selector,
                                   wait_selector=args.wait,
                                   scroll=args.scroll)
            if text:
                print(text[:2000])
        else:
            html = bs.fetch(args.url, wait_selector=args.wait,
                           scroll=args.scroll)
            if html:
                if args.output:
                    Path(args.output).write_text(html, encoding="utf-8")
                    print(f"已保存: {args.output} ({len(html)} 字符)")
                else:
                    print(f"成功: {len(html)} 字符")
                    # 提取 title
                    m = re.search(r"<title[^>]*>(.*?)</title>", html,
                                  re.IGNORECASE | re.DOTALL)
                    if m:
                        print(f"标题: {m.group(1).strip()[:100]}")
            else:
                print("抓取失败")


if __name__ == "__main__":
    main()
