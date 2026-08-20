# -*- coding: utf-8 -*-
"""
网页操作深度增强模块 v7.0.0 (browser_pro.py)

在 browser_scraper.BrowserScraper（Playwright/Chromium，类人化）之上新增四大能力：

1. 网络拦截 / API 挖掘（intercept_network / discover_api）
   监听页面发出的 XHR/fetch 响应，自动捕获背后的 JSON 接口（URL/参数/分页规律/
   响应样本），沉淀到 data/api_registry.json 供降级链直连复用——对挖掘
   东财式"页面背后接口"价值最大，成功后无需浏览器即可高速直连接口。

2. 操作宏录制与回放（MacroPlayer / record_macro）
   宏 = JSON 操作序列（goto/click/fill/press/upload/download/drag/extract/…），
   支持 {{参数}} 占位符替换，一键重放；record_macro 注入 JS 捕获真实点击/输入
   事件生成宏草稿。

3. 文件上传 / 下载 / 拖拽（upload_file / download_file / drag_and_drop /
   type_contenteditable / press_keys）
   补齐真实网页交互所需的全部动词，并 monkey-patch 到 BrowserScraper。

4. 异步并发标签池（AsyncBrowserPool / async_batch_fetch）
   async_playwright + semaphore 多页并发，批量抓取提速；sync BrowserScraper
   保持不变，双模式并存。

依赖：与 browser_scraper 相同（可选 Playwright）。缺失时全部优雅降级：
返回 None / 空结果并打印安装提示，不影响其他模块（零 pip 依赖核心不受影响）。

用法：
  from scripts.browser_pro import discover_api, play_macro, async_batch_fetch
  api = discover_api("https://fund.eastmoney.com/company/")     # 挖接口
  out = play_macro("macros/demo.json", params={"keyword": "茅台"})
  res = async_batch_fetch(["https://a.com", "https://b.com"], concurrency=4)
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

try:
    from .browser_scraper import (
        BrowserScraper, PLAYWRIGHT_AVAILABLE, INSTALL_HINT,
        _get_browser_scraper, AD_BLOCK_DOMAINS, _should_block_url,
    )
except ImportError:  # 脚本直跑（python scripts/browser_pro.py）
    from browser_scraper import (  # type: ignore
        BrowserScraper, PLAYWRIGHT_AVAILABLE, INSTALL_HINT,
        _get_browser_scraper, AD_BLOCK_DOMAINS, _should_block_url,
    )

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
API_REGISTRY_FILE = DATA_DIR / "api_registry.json"
DOWNLOAD_DIR = DATA_DIR / "downloads"
MACRO_DIR = SKILL_DIR / "macros"
DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)
MACRO_DIR.mkdir(exist_ok=True, parents=True)

MAX_SAMPLE_LEN = 2000          # 响应样本最大保存字符数
MAX_BODY_CAPTURE = 60          # 单页最多捕获的响应条数


# ══════════════════════════════════════════════════════════════
# 一、网络拦截 / API 挖掘
# ══════════════════════════════════════════════════════════════

_NUM_PARAM_RE = re.compile(r"^(page|p|pn|pageIndex|pageNo|page_index|page_no|"
                           r"currentPage|current|offset|start|skip|from|begin)$", re.I)


def _truncate(obj: Any, limit: int = MAX_SAMPLE_LEN) -> str:
    """JSON 序列化并截断（响应样本持久化用）。"""
    try:
        s = json.dumps(obj, ensure_ascii=False)
    except Exception:
        s = str(obj)
    return s[:limit] + ("…[截断]" if len(s) > limit else "")


def _normalize_api_url(url: str) -> Tuple[str, Dict[str, str]]:
    """把 URL 拆成 (路径模板, 查询参数)，用于同接口归并去重。"""
    sp = urlsplit(url)
    query = dict(parse_qsl(sp.query, keep_blank_values=True))
    return (sp.scheme + "://" + sp.netloc + sp.path), query


def _detect_pagination(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从捕获的请求里识别分页规律：同路径模板下某数值参数递增。"""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for e in entries:
        tpl, q = _normalize_api_url(e["url"])
        groups.setdefault(tpl, []).append({**e, "_q": q})
    findings = []
    for tpl, es in groups.items():
        if len(es) < 2:
            continue
        param_names = set()
        for e in es:
            param_names.update(e["_q"].keys())
        for p in param_names:
            if not _NUM_PARAM_RE.match(p):
                continue
            vals = []
            ok = True
            for e in sorted(es, key=lambda x: x["ts"]):
                raw = e["_q"].get(p, "")
                try:
                    vals.append(int(raw))
                except (TypeError, ValueError):
                    ok = False
                    break
            if ok and len(vals) >= 2 and len(set(vals)) >= 2:
                step = None
                if len(vals) >= 2:
                    diffs = {vals[i + 1] - vals[i] for i in range(len(vals) - 1)}
                    step = diffs.pop() if len(diffs) == 1 else None
                findings.append({
                    "url_template": tpl + ("?" if param_names else ""),
                    "pagination_param": p,
                    "observed_values": vals[:10],
                    "step": step,
                    "times_seen": len(es),
                })
                break
    return findings


class ApiRegistry:
    """API 注册表：挖掘到的接口持久化到 data/api_registry.json，可复用可去重。"""

    def __init__(self, path: Path = API_REGISTRY_FILE):
        self.path = path
        self._doc: Dict[str, Any] = {"_meta": {"version": "7.0.0",
                                               "updated": ""}, "endpoints": []}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                doc = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(doc, dict) and isinstance(doc.get("endpoints"), list):
                    self._doc = doc
            except Exception:
                pass

    def add(self, endpoint: Dict[str, Any]) -> bool:
        """新增/更新一个端点（按 url+参数名集合去重）。返回是否写入。"""
        tpl, q = _normalize_api_url(endpoint.get("url", ""))
        key = (tpl, tuple(sorted(q.keys())))
        for ep in self._doc["endpoints"]:
            etpl, eq = _normalize_api_url(ep.get("url", ""))
            if (etpl, tuple(sorted(eq.keys()))) == key:
                ep["hit_count"] = ep.get("hit_count", 1) + 1
                ep["last_seen"] = endpoint.get("discovered_at", "")
                if endpoint.get("sample_response"):
                    ep["sample_response"] = endpoint["sample_response"]
                return False
        endpoint.setdefault("hit_count", 1)
        self._doc["endpoints"].append(endpoint)
        return True

    def save(self):
        self._doc["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._doc["_meta"]["count"] = len(self._doc["endpoints"])
        self.path.write_text(json.dumps(self._doc, ensure_ascii=False, indent=1),
                             encoding="utf-8")

    def search(self, keyword: str = "", domain: str = "") -> List[Dict[str, Any]]:
        out = []
        for ep in self._doc["endpoints"]:
            if keyword and keyword.lower() not in json.dumps(ep, ensure_ascii=False).lower():
                continue
            if domain and domain not in ep.get("url", ""):
                continue
            out.append(ep)
        return out


def _intercept_network(self: BrowserScraper, url: str,
                       wait_seconds: float = 6.0,
                       scroll_times: int = 3,
                       resource_types: Tuple[str, ...] = ("xhr", "fetch"),
                       url_pattern: str = "",
                       save_to_registry: bool = True,
                       block_assets: bool = True,
                       extra_actions: Optional[List[Dict[str, Any]]] = None,
                       ) -> Optional[Dict[str, Any]]:
    """打开页面并监听网络层，捕获 XHR/fetch 的 JSON 接口。

    Args:
        url: 目标页面（SPA 优先，页面加载/滚动/交互时发出的接口都能抓到）
        wait_seconds: 页面就绪后的继续监听时长（触发懒加载请求）
        scroll_times: 滚动次数（触发滚动加载的接口，如 Infinite List）
        resource_types: 监听的资源类型（默认 xhr+fetch）
        url_pattern: 只保留匹配该正则的请求（空=不过滤）
        save_to_registry: 命中接口写入 data/api_registry.json（去重累积）
        block_assets: 拦截图片/字体/媒体请求提速
        extra_actions: 捕获前执行的操作序列（MacroPlayer 动词，
                       如 [{"action":"click","selector":".load-more"}]）

    Returns:
        {"url", "captured_count", "apis": [{url,method,status,content_type,
         params, sample_response…}], "pagination": [...], "registry_saved": int}
    """
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    captured: List[Dict[str, Any]] = []
    pattern_re = re.compile(url_pattern) if url_pattern else None

    def on_response(resp):
        try:
            if len(captured) >= MAX_BODY_CAPTURE:
                return
            req = resp.request
            rt = req.resource_type
            if rt not in resource_types:
                return
            u = resp.url
            if pattern_re and not pattern_re.search(u):
                return
            low = u.lower()
            if any(dom in low for dom in AD_BLOCK_DOMAINS):
                return
            ct = (resp.headers or {}).get("content-type", "")
            entry: Dict[str, Any] = {
                "url": u, "method": req.method, "status": resp.status,
                "resource_type": rt, "content_type": ct, "ts": time.time(),
                "params": dict(parse_qsl(urlsplit(u).query, keep_blank_values=True)),
            }
            if "json" in ct.lower() or u.endswith(".json"):
                try:
                    entry["sample_response"] = _truncate(resp.json())
                except Exception:
                    pass
            captured.append(entry)
        except Exception:
            pass

    page = None
    try:
        page = self.new_page()
        if block_assets:
            def _route(route):
                try:
                    if route.request.resource_type in ("image", "font", "media"):
                        return route.abort()
                    return route.continue_()
                except Exception:
                    pass
            page.route("**/*", _route)
        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        # 滚动触发懒加载接口
        for _ in range(max(0, scroll_times)):
            try:
                page.mouse.wheel(0, 1200)
            except Exception:
                pass
            time.sleep(0.8)

        # 可选交互（点加载更多/翻页等）再触发一批接口
        if extra_actions:
            try:
                MacroPlayer(scraper=self).play({"steps": extra_actions})
            except Exception:
                pass

        time.sleep(max(0.0, wait_seconds))
        pagination = _detect_pagination(captured)

        saved = 0
        if save_to_registry and captured:
            reg = ApiRegistry()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            domain = urlsplit(url).netloc
            for e in captured:
                if "sample_response" not in e:
                    continue
                if reg.add({
                    "url": e["url"], "method": e["method"],
                    "content_type": e["content_type"], "params": e["params"],
                    "sample_response": e["sample_response"],
                    "discovered_from": url, "domain": domain,
                    "discovered_at": now,
                }):
                    saved += 1
            if saved:
                reg.save()

        # 汇总输出（响应样本可能很长，条目里保留）
        return {
            "url": url,
            "captured_count": len(captured),
            "apis": captured,
            "pagination": pagination,
            "registry_saved": saved,
        }
    except Exception as e:
        print(f"[browser_pro] intercept_network 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


def discover_api(url: str, wait_seconds: float = 6.0,
                 url_pattern: str = "", headless: bool = True,
                 ) -> Optional[Dict[str, Any]]:
    """一行代码 API 挖掘（复用进程级单例浏览器）。"""
    bs = _get_browser_scraper(headless=headless)
    if bs is None:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    return bs.intercept_network(url, wait_seconds=wait_seconds,
                                url_pattern=url_pattern)


# ══════════════════════════════════════════════════════════════
# 二、文件上传 / 下载 / 拖拽 / 组合键 / 富文本（monkey-patch 到 BrowserScraper）
# ══════════════════════════════════════════════════════════════

def _upload_file(self: BrowserScraper, url: str, selector: str,
                 file_paths: List[str], wait_after: float = 2.0,
                 submit_selector: str = "") -> Optional[Dict[str, Any]]:
    """文件上传：打开 url → set_input_files → （可选）点提交，返回提交后 HTML。

    Args:
        selector: <input type=file> 的 CSS 选择器（可为数组输入 multiple）
        file_paths: 本地文件路径列表
        submit_selector: 上传按钮选择器（空=不点击）
    """
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    page = None
    try:
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        paths = [str(Path(p).resolve()) for p in file_paths]
        page.set_input_files(selector, paths if len(paths) > 1 else paths[0])
        time.sleep(wait_after)
        if submit_selector:
            page.click(submit_selector)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
        return {"ok": True, "url": url, "uploaded": len(paths),
                "html": page.content()}
    except Exception as e:
        print(f"[browser_pro] upload_file 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


def _download_file(self: BrowserScraper, url: str,
                   click_selector: str = "",
                   save_dir: str = str(DOWNLOAD_DIR),
                   filename: str = "", timeout_ms: int = 60000,
                   ) -> Optional[Dict[str, Any]]:
    """文件下载：打开 url → （可选）点击触发下载 → 等待下载完成并落盘。

    Args:
        click_selector: 触发下载的按钮/链接选择器；为空则直接从 url 导航下载
        filename: 保存文件名（空=用服务端建议名）
    Returns:
        {"ok", "path", "url"}；失败返回 None
    """
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    page = None
    try:
        Path(save_dir).mkdir(exist_ok=True, parents=True)
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        with page.expect_download(timeout=timeout_ms) as dl_info:
            if click_selector:
                page.click(click_selector)
            else:
                page.evaluate(
                    "u => { const a = document.createElement('a');"
                    " a.href = u; document.body.appendChild(a); a.click(); }",
                    url)
        download = dl_info.value
        name = filename or download.suggested_filename or "download.bin"
        dest = Path(save_dir) / name
        download.save_as(str(dest))
        return {"ok": True, "path": str(dest), "url": url}
    except Exception as e:
        print(f"[browser_pro] download_file 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


def _drag_and_drop(self: BrowserScraper, url: str, source_selector: str,
                   target_selector: str, humanlike: bool = True,
                   ) -> Optional[Dict[str, Any]]:
    """拖拽元素：source → target（滑块验证/排序/看板场景）。返回操作后 HTML。"""
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    page = None
    try:
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if humanlike and hasattr(self, "_human_delay"):
            # 类人模式：按下 → 缓慢移动 → 释放（抗行为检测）
            src = page.locator(source_selector).first
            tgt = page.locator(target_selector).first
            sb = src.bounding_box()
            tb = tgt.bounding_box()
            if sb and tb:
                import random as _r
                sx = sb["x"] + sb["width"] / 2
                sy = sb["y"] + sb["height"] / 2
                tx = tb["x"] + tb["width"] / 2
                ty = tb["y"] + tb["height"] / 2
                page.mouse.move(sx, sy)
                if hasattr(self, "_human_delay"):
                    self._human_delay(0.1, 0.3)
                page.mouse.down()
                steps = _r.randint(15, 30)
                for i in range(1, steps + 1):
                    page.mouse.move(sx + (tx - sx) * i / steps,
                                    sy + (ty - sy) * i / steps + _r.uniform(-2, 2))
                    time.sleep(_r.uniform(0.01, 0.05))
                page.mouse.up()
        else:
            page.drag_and_drop(source_selector, target_selector)
        time.sleep(0.5)
        return {"ok": True, "url": url, "html": page.content()}
    except Exception as e:
        print(f"[browser_pro] drag_and_drop 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


def _press_keys(self: BrowserScraper, url: str, keys: str,
                selector: str = "") -> Optional[str]:
    """在页面（或先聚焦某元素）按组合键，如 "Control+A"、"Control+C"、
    "Enter"、"ArrowDown"。返回操作后 HTML。"""
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    page = None
    try:
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if selector:
            page.locator(selector).first.click()
            time.sleep(0.2)
        page.keyboard.press(keys)
        time.sleep(0.3)
        return page.content()
    except Exception as e:
        print(f"[browser_pro] press_keys 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


def _type_contenteditable(self: BrowserScraper, url: str, selector: str,
                          text: str, submit: bool = False) -> Optional[str]:
    """富文本输入：contenteditable / textarea / 可编辑 div（逐字符带随机延迟）。"""
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    page = None
    try:
        import random as _r
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        loc = page.locator(selector).first
        loc.click()
        time.sleep(0.2)
        for ch in text:
            page.keyboard.type(ch, delay=_r.randint(30, 120))
        if submit:
            page.keyboard.press("Enter")
        time.sleep(0.5)
        return page.content()
    except Exception as e:
        print(f"[browser_pro] type_contenteditable 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════
# 三、操作宏：JSON 序列 → 参数化回放
# ══════════════════════════════════════════════════════════════

_VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][\w]*)\s*\}\}")


def _substitute(obj: Any, params: Dict[str, Any]) -> Any:
    """递归替换 {{var}} 占位符；整串恰为一个占位符时保留原类型。"""
    if isinstance(obj, str):
        m = _VAR_RE.fullmatch(obj.strip())
        if m and m.group(1) in params:
            return params[m.group(1)]
        return _VAR_RE.sub(lambda mm: str(params.get(mm.group(1), mm.group(0))), obj)
    if isinstance(obj, list):
        return [_substitute(x, params) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute(v, params) for k, v in obj.items()}
    return obj


class MacroPlayer:
    """网页操作宏回放器。

    宏格式（JSON 文件或 dict）：
        {
          "name": "search-and-extract",
          "params": {"keyword": "示例"},          # 默认参数
          "steps": [
            {"action": "goto",     "url": "https://…"},
            {"action": "fill",     "selector": "#kw", "text": "{{keyword}}"},
            {"action": "press",    "keys": "Enter"},
            {"action": "wait_for_selector", "selector": "#result"},
            {"action": "scroll",   "direction": "down", "amount": 800},
            {"action": "upload",   "selector": "input[type=file]",
                                   "files": ["{{csv_path}}"]},
            {"action": "download", "click_selector": ".btn-export",
                                   "filename": "out.xlsx"},
            {"action": "drag",     "source": "#a", "target": "#b"},
            {"action": "extract",  "as": "html"},          # 存入 outputs.html
            {"action": "extract",  "selector": "h1", "as": "title"},
            {"action": "screenshot", "path": "shot.png"},
            {"action": "intercept","as": "api", "wait_seconds": 5}
          ]
        }
    """

    def __init__(self, scraper: Optional[BrowserScraper] = None,
                 headless: bool = True):
        self._owns = scraper is None
        self.scraper = scraper or _get_browser_scraper(headless=headless)

    # ── 宏文件 I/O ──────────────────────────────────────────
    @staticmethod
    def save_macro(macro: Dict[str, Any], name: str) -> Path:
        path = MACRO_DIR / (name if name.endswith(".json") else name + ".json")
        path.write_text(json.dumps(macro, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        return path

    @staticmethod
    def load_macro(name: str) -> Dict[str, Any]:
        path = Path(name)
        if not path.exists():
            path = MACRO_DIR / (name if name.endswith(".json") else name + ".json")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def list_macros() -> List[str]:
        return sorted(p.name for p in MACRO_DIR.glob("*.json"))

    # ── 回放 ────────────────────────────────────────────────
    def play(self, macro: Dict[str, Any],
             params: Optional[Dict[str, Any]] = None,
             timeout_s: float = 180.0) -> Dict[str, Any]:
        """回放宏。返回 {"ok", "steps_done", "steps_total", "outputs", "error"}。"""
        if self.scraper is None:
            return {"ok": False, "error": INSTALL_HINT, "steps_done": 0,
                    "steps_total": 0, "outputs": {}}
        merged = dict(macro.get("params") or {})
        if params:
            merged.update(params)
        steps = _substitute(macro.get("steps") or [], merged)
        outputs: Dict[str, Any] = {}
        page = None
        t0 = time.time()
        try:
            page = self.scraper.new_page()
            for i, step in enumerate(steps):
                if time.time() - t0 > timeout_s:
                    raise TimeoutError(f"宏总时长超过 {timeout_s}s")
                self._exec(page, step, outputs)
            return {"ok": True, "steps_done": len(steps),
                    "steps_total": len(steps), "outputs": outputs, "error": ""}
        except Exception as e:
            return {"ok": False, "steps_done": len(outputs.get("_done", [])),
                    "steps_total": len(steps), "outputs": outputs, "error": str(e)}
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

    def _exec(self, page, step: Dict[str, Any], outputs: Dict[str, Any]):
        act = step.get("action", "")
        to_ms = self.scraper.timeout_ms
        if act == "goto":
            page.goto(step["url"], wait_until=step.get("wait", "domcontentloaded"),
                      timeout=to_ms)
        elif act == "click":
            page.click(step["selector"], timeout=step.get("timeout", to_ms))
        elif act in ("fill", "type"):
            if act == "fill":
                page.fill(step["selector"], str(step.get("text", "")))
            else:
                page.locator(step["selector"]).first.click()
                page.keyboard.type(str(step.get("text", "")), delay=45)
        elif act == "select":
            page.select_option(step["selector"], step["value"])
        elif act == "hover":
            page.hover(step["selector"])
        elif act == "press":
            page.keyboard.press(step["keys"])
        elif act == "scroll":
            amount = int(step.get("amount", 600))
            dy = -amount if step.get("direction") == "up" else amount
            page.mouse.wheel(0, dy)
        elif act == "wait":
            time.sleep(float(step.get("seconds", 1)))
        elif act == "wait_for_selector":
            page.wait_for_selector(step["selector"],
                                   timeout=step.get("timeout", to_ms))
        elif act == "upload":
            files = step.get("files") or []
            files = [str(Path(f).resolve()) for f in files]
            page.set_input_files(step["selector"],
                                 files if len(files) > 1 else (files[0] if files else ""))
        elif act == "download":
            with page.expect_download(timeout=step.get("timeout", 60000)) as dl:
                page.click(step["click_selector"])
            name = step.get("filename") or dl.value.suggested_filename or "download.bin"
            dest = Path(step.get("save_dir", str(DOWNLOAD_DIR))) / name
            dest.parent.mkdir(exist_ok=True, parents=True)
            dl.value.save_as(str(dest))
            if step.get("as"):
                outputs[step["as"]] = str(dest)
        elif act == "drag":
            page.drag_and_drop(step["source"], step["target"])
        elif act == "extract":
            key = step.get("as") or f"extract_{len(outputs)}"
            if step.get("selector"):
                el = page.locator(step["selector"]).first
                outputs[key] = el.text_content() if not step.get("attribute") \
                    else el.get_attribute(step["attribute"])
            else:
                outputs[key] = page.content()
        elif act == "screenshot":
            path = step.get("path") or str(
                DATA_DIR / "screenshots" /
                f"macro_{datetime.now():%Y%m%d_%H%M%S}.png")
            page.screenshot(path=path, full_page=bool(step.get("full_page", True)))
            if step.get("as"):
                outputs[step["as"]] = path
        elif act == "intercept":
            # 在当前页面临时挂监听再触发后续（简化：滚动 + 等待收集）
            found: List[Dict[str, Any]] = []
            def _on_resp(resp):
                try:
                    if resp.request.resource_type in ("xhr", "fetch"):
                        found.append({"url": resp.url, "status": resp.status,
                                      "method": resp.request.method})
                except Exception:
                    pass
            page.on("response", _on_resp)
            for _ in range(int(step.get("scroll_times", 2))):
                page.mouse.wheel(0, 1000)
                time.sleep(0.6)
            time.sleep(float(step.get("wait_seconds", 4)))
            page.remove_listener("response", _on_resp)
            outputs[step.get("as") or "api"] = found
        else:
            raise ValueError(f"未知宏动作: {act}")
        outputs.setdefault("_done", []).append(act)


def play_macro(name_or_macro, params: Optional[Dict[str, Any]] = None,
               headless: bool = True) -> Dict[str, Any]:
    """一行代码回放宏文件（macros/ 下名字或路径，或直接传 dict）。"""
    macro = MacroPlayer.load_macro(name_or_macro) if isinstance(name_or_macro, str) \
        else name_or_macro
    return MacroPlayer(headless=headless).play(macro, params=params)


# ── 宏录制（注入 JS 捕获真实交互，草稿生成）───────────────────

_RECORD_JS = r"""
(() => {
  if (window.__v7_recording) return;
  window.__v7_recording = true;
  window.__v7_macro_log = [];
  const sel = (el) => {
    if (!el || !el.tagName) return '';
    if (el.id) return '#' + el.id;
    const name = el.getAttribute('name');
    if (name) return `${el.tagName.toLowerCase()}[name="${name}"]`;
    const cls = (el.className && typeof el.className === 'string')
      ? el.className.trim().split(/\s+/).slice(0, 2).map(c => '.' + c).join('')
      : '';
    const base = el.tagName.toLowerCase() + cls;
    const sibs = Array.from(el.parentElement ? el.parentElement.children : []);
    return sibs.length > 1 ? base + `:nth-child(${sibs.indexOf(el) + 1})` : base;
  };
  document.addEventListener('click', (ev) => {
    window.__v7_macro_log.push({action: 'click', selector: sel(ev.target), ts: Date.now()});
  }, true);
  document.addEventListener('change', (ev) => {
    const t = ev.target;
    if (!t) return;
    if (t.tagName === 'SELECT') {
      window.__v7_macro_log.push({action: 'select', selector: sel(t), value: t.value, ts: Date.now()});
    } else if (t.type === 'file') {
      window.__v7_macro_log.push({action: 'upload', selector: sel(t), files: ['{{file}}'], ts: Date.now()});
    }
  }, true);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter') {
      window.__v7_macro_log.push({action: 'press', keys: 'Enter', ts: Date.now()});
    }
  }, true);
  let lastInput = 0;
  document.addEventListener('input', (ev) => {
    const t = ev.target;
    if (!t || (t.tagName !== 'INPUT' && t.tagName !== 'TEXTAREA' && !t.isContentEditable)) return;
    const now = Date.now();
    if (now - lastInput < 900) return;  // 合并连续输入
    lastInput = now;
    window.__v7_macro_log.push({action: 'fill', selector: sel(t), text: '{{input}}', ts: now});
  }, true);
})();
"""


def record_macro(url: str, record_seconds: float = 20.0,
                 headless: bool = False,
                 name: str = "") -> Optional[Dict[str, Any]]:
    """打开页面并录制真实交互（可见模式），生成可编辑的宏草稿。

    录制 = 注入事件监听（click/fill/select/upload/Enter）→ 观察期结束后
    收集 window.__v7_macro_log → 转为 MacroPlayer 宏格式（未识别的步骤用
    占位参数 {{input}}/{{file}}，回放前人工补全）。

    Returns:
        {"macro": {...}, "saved_to": path}；失败返回 None
    """
    if not PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    bs = None
    page = None
    try:
        bs = BrowserScraper(headless=headless)
        page = bs.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.evaluate(_RECORD_JS)
        print(f"[browser_pro] 录制中… 请在浏览器里操作（{record_seconds}s 后自动收集）")
        time.sleep(max(3.0, record_seconds))
        raw = page.evaluate("window.__v7_macro_log || []")
        steps = [{"action": "goto", "url": url}]
        for r in raw or []:
            steps.append({k: v for k, v in r.items() if k != "ts"})
        macro = {"name": name or f"recorded_{datetime.now():%Y%m%d_%H%M%S}",
                 "description": "record_macro 自动生成草稿，回放前请核对选择器与参数",
                 "params": {"input": "示例文本", "file": "C:/path/to/file"},
                 "steps": steps}
        path = MacroPlayer.save_macro(macro, macro["name"])
        return {"macro": macro, "saved_to": str(path)}
    except Exception as e:
        print(f"[browser_pro] record_macro 失败: {e}", file=sys.stderr)
        return None
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
        if bs is not None:
            try:
                bs.stop()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════
# 四、异步并发标签池（async_playwright）
# ══════════════════════════════════════════════════════════════

try:
    from playwright.async_api import async_playwright
    ASYNC_PLAYWRIGHT_AVAILABLE = True
except ImportError:
    ASYNC_PLAYWRIGHT_AVAILABLE = False


class AsyncBrowserPool:
    """异步并发标签池：一个浏览器 + semaphore 控制并发页，批量抓取提速。

    用法（同步调用方）：
        AsyncBrowserPool(concurrency=6).run(urls)   # → [(url, html|None), …]
    异步调用方：
        async with AsyncBrowserPool(concurrency=6) as pool:
            results = await pool.fetch_many(urls)
    """

    def __init__(self, concurrency: int = 4, headless: bool = True,
                 timeout_ms: int = 30000, proxy: Optional[Any] = None):
        if not ASYNC_PLAYWRIGHT_AVAILABLE:
            raise ImportError(INSTALL_HINT)
        self.concurrency = max(1, concurrency)
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.proxy = proxy
        self._pw = None
        self._browser = None
        self._context = None
        self._sem: Optional[asyncio.Semaphore] = None

    async def start(self):
        if self._browser is not None:
            return
        self._pw = await async_playwright().start()
        kwargs = dict(headless=self.headless, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox", "--disable-dev-shm-usage"])
        if self.proxy:
            from browser_scraper import BrowserScraper as _BS  # 复用解析逻辑
            kwargs["proxy"] = _BS._resolve_proxy(self.proxy)
        self._browser = await self._pw.chromium.launch(**kwargs)
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/133.0.0.0 Safari/537.36"),
            locale="zh-CN", timezone_id="Asia/Shanghai")
        self._sem = asyncio.Semaphore(self.concurrency)

    async def stop(self):
        for obj, closer in ((self._context, "close"), (self._browser, "close"),
                            (self._pw, "stop")):
            if obj is not None:
                try:
                    await getattr(obj, closer)()
                except Exception:
                    pass
        self._context = self._browser = self._pw = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    async def fetch(self, url: str, wait_until: str = "domcontentloaded",
                    wait_seconds: float = 0.0,
                    scroll_times: int = 0) -> Tuple[str, Optional[str]]:
        """抓单个 URL（受 semaphore 约束）。"""
        assert self._sem is not None, "先 await pool.start()"
        async with self._sem:
            page = await self._context.new_page()
            try:
                page.set_default_timeout(self.timeout_ms)
                await page.goto(url, wait_until=wait_until,
                                timeout=self.timeout_ms)
                for _ in range(max(0, scroll_times)):
                    await page.mouse.wheel(0, 1200)
                    await asyncio.sleep(0.5)
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                return url, await page.content()
            except Exception as e:
                print(f"[AsyncBrowserPool] {url} 失败: {e}", file=sys.stderr)
                return url, None
            finally:
                try:
                    await page.close()
                except Exception:
                    pass

    async def fetch_many(self, urls: List[str],
                         **kw) -> List[Tuple[str, Optional[str]]]:
        """并发抓取多个 URL，按输入序返回。"""
        await self.start()
        return list(await asyncio.gather(*(self.fetch(u, **kw) for u in urls)))

    def run(self, urls: List[str], **kw) -> List[Tuple[str, Optional[str]]]:
        """同步入口：自建事件循环跑完即关（调用方无 loop 时用这个）。"""
        async def _main():
            async with self:
                return await self.fetch_many(urls, **kw)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_main())
        # 已在异步上下文里被同步调用：另起线程跑，避免死锁
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(asyncio.run, _main()).result()


def async_batch_fetch(urls: List[str], concurrency: int = 4,
                      headless: bool = True, **kw) -> Optional[List[Tuple[str, Optional[str]]]]:
    """一行代码异步并发批量抓取。Playwright 缺失返回 None。"""
    if not ASYNC_PLAYWRIGHT_AVAILABLE:
        print(INSTALL_HINT, file=sys.stderr)
        return None
    return AsyncBrowserPool(concurrency=concurrency, headless=headless).run(urls, **kw)


# ══════════════════════════════════════════════════════════════
# monkey-patch：把 v7.0.0 新动词挂到 BrowserScraper
# ══════════════════════════════════════════════════════════════

BrowserScraper.intercept_network = _intercept_network
BrowserScraper.upload_file = _upload_file
BrowserScraper.download_file = _download_file
BrowserScraper.drag_and_drop = _drag_and_drop
BrowserScraper.press_keys = _press_keys
BrowserScraper.type_contenteditable = _type_contenteditable


def _selfcheck() -> int:
    """离线自检：宏参数替换 / API 归并 / 分页识别。"""
    ok = 0
    sub = _substitute({"a": "{{x}}", "b": ["{{x}}", "k{{y}}"], "c": 1},
                      {"x": 42, "y": "v"})
    assert sub["a"] == 42 and sub["b"][0] == 42 and sub["b"][1] == "kv" and sub["c"] == 1
    ok += 1
    pag = _detect_pagination([
        {"url": "https://a.com/api?pn=1&size=20", "ts": 1},
        {"url": "https://a.com/api?pn=2&size=20", "ts": 2},
        {"url": "https://a.com/api?pn=3&size=20", "ts": 3},
    ])
    assert pag and pag[0]["pagination_param"] == "pn" and pag[0]["step"] == 1
    ok += 1
    reg = ApiRegistry(DATA_DIR / "_selftest_api_registry.json")
    reg.add({"url": "https://a.com/api?pn=1", "sample_response": "{}",
             "discovered_at": "now"})
    assert not reg.add({"url": "https://a.com/api?pn=2", "sample_response": "{}",
                        "discovered_at": "now2"})
    reg.path.unlink(missing_ok=True)
    ok += 1
    print(f"browser_pro selfcheck: {ok}/3 OK")
    return ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="v7.0.0 网页操作深度增强")
    ap.add_argument("url", nargs="?", help="目标网址")
    ap.add_argument("--discover-api", action="store_true", help="网络拦截挖接口")
    ap.add_argument("--wait", type=float, default=6.0, help="拦截监听时长")
    ap.add_argument("--pattern", default="", help="接口 URL 过滤正则")
    ap.add_argument("--record", type=float, default=0, help="录制宏秒数")
    ap.add_argument("--macro", default="", help="回放宏文件")
    ap.add_argument("--params", default="", help='回放参数 JSON，如 {"k":"v"}')
    ap.add_argument("--selfcheck", action="store_true", help="离线自检")
    args = ap.parse_args()

    if args.selfcheck:
        sys.exit(0 if _selfcheck() == 3 else 1)
    if args.record and args.url:
        r = record_macro(args.url, record_seconds=args.record)
        print(json.dumps(r, ensure_ascii=False, indent=2) if r else "录制失败")
    elif args.macro:
        p = json.loads(args.params) if args.params else {}
        print(json.dumps(play_macro(args.macro, params=p), ensure_ascii=False,
                         default=str)[:3000])
    elif args.discover_api and args.url:
        r = discover_api(args.url, wait_seconds=args.wait, url_pattern=args.pattern)
        if r:
            print(f"捕获 {r['captured_count']} 个请求，"
                  f"分页规律 {len(r['pagination'])} 条，"
                  f"新入库接口 {r['registry_saved']} 个")
            for pg in r["pagination"]:
                print("  分页:", pg["url_template"], "参数", pg["pagination_param"],
                      "步长", pg["step"])
            for api in r["apis"][:10]:
                print("  接口:", api["method"], api["status"], api["url"][:120])
        else:
            print("挖掘失败（Playwright 未安装或页面打不开）")
    else:
        ap.print_help()
