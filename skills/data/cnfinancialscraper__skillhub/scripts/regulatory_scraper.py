# -*- coding: utf-8 -*-
"""
金融监管与政策资讯爬虫 v2.0 (regulatory_scraper.py)

v6.0.0 起数据源全面切换为商业财经数据源（不依赖任何政府网站）：
  1. 东方财富资讯 API（宏观 / 政策 / 监管新闻）
  2. 新浪财经滚动新闻 API（财经要闻）
  3. 巨潮资讯公告查询 API（A股上市公司公告）

提取：政策动态、财经要闻、监管新闻、A股公告。

用法：
  from regulatory_scraper import RegulatoryScraper, get_regulatory_updates
  scraper = RegulatoryScraper()
  news = scraper.get_macro_policy_news(limit=10)
"""

import json
import re
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from bs4 import BeautifulSoup  # type: ignore
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from .http_utils import get_session
    HAS_HTTP_UTILS = True
except ImportError:
    try:
        from http_utils import get_session
        HAS_HTTP_UTILS = True
    except ImportError:
        HAS_HTTP_UTILS = False

logger = logging.getLogger("regulatory_scraper")

# ─── 商业数据源 API（v6.0.0 起）────────────────────────────────────────────

# 东方财富资讯列表（column 345=宏观/政策，344=财经导读）
EM_NEWS_API = ("https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
               "?client=web&biz=web_news_col&column={column}&order=1"
               "&needInteractData=0&page_index=1&page_size={size}&req_trace={ts}")
# 新浪财经滚动新闻（lid 2516=财经/宏观，2510=要闻）
SINA_ROLL_API = ("https://feed.mix.sina.com.cn/api/roll/get?pageid=153"
                 "&lid={lid}&k=&num={size}&page=1")
# 巨潮资讯公告查询（POST）
CNINFO_QUERY_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"


class RegulatoryScraper:
    """金融监管与政策资讯爬虫 — 东财 / 新浪 / 巨潮（商业数据源）"""

    def __init__(self):
        self.session = None
        self._init_session()

    def _init_session(self):
        """初始化请求会话"""
        if HAS_HTTP_UTILS:
            try:
                self.session = get_session()
            except Exception:
                pass
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json,text/html,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })

    def _fetch_html(self, url: str, timeout: int = 30) -> Optional[str]:
        """获取页面内容，自动检测编码"""
        try:
            resp = self.session.get(url, timeout=timeout)
            # 兼容 requests 和 stdlib response 的编码处理
            if hasattr(resp, 'apparent_encoding'):
                resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
            elif hasattr(resp, 'encoding') and resp.encoding:
                try:
                    resp.encoding = resp.encoding
                except Exception:
                    pass  # stdlib response 可能不支持设置 encoding
            return resp.text if hasattr(resp, 'text') else resp.content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"获取页面失败: {url}, {e}")
            return None

    def _fetch_json(self, url: str, timeout: int = 30) -> Optional[Any]:
        """GET 请求并解析 JSON"""
        try:
            resp = self.session.get(url, timeout=timeout)
            if hasattr(resp, "json"):
                return resp.json()
            return json.loads(resp.content.decode("utf-8", errors="replace"))
        except Exception as e:
            logger.warning(f"JSON 获取失败: {url}, {e}")
            return None

    def _fetch_json_post(self, url: str, payload: Dict[str, Any],
                         timeout: int = 30) -> Optional[Any]:
        """POST 请求并解析 JSON（巨潮公告接口需要）"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
            "Origin": "http://www.cninfo.com.cn",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            if hasattr(self.session, "post"):
                resp = self.session.post(url, data=payload, headers=headers, timeout=timeout)
            else:
                from urllib import request as ur
                req = ur.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
                with ur.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8", errors="replace"))
            if hasattr(resp, "json"):
                return resp.json()
            return json.loads(resp.content.decode("utf-8", errors="replace"))
        except Exception as e:
            logger.warning(f"POST JSON 失败: {url}, {e}")
            return None

    def _parse_html_links(self, html: str, base_url: str,
                          list_selector: str = "a") -> List[Dict[str, str]]:
        """从 HTML 中提取链接列表"""
        if not html or not HAS_BS4:
            return []
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for link in soup.select(list_selector):
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or len(title) < 4:
                continue
            if href and not href.startswith("http"):
                if href.startswith("/"):
                    href = base_url.rstrip("/") + href
                elif href.startswith("./"):
                    href = base_url.rstrip("/") + href[1:]
                else:
                    href = base_url.rstrip("/") + "/" + href
            results.append({"title": title, "url": href, "date": ""})
        return results

    # ==================== 东方财富资讯（宏观 / 政策） ====================

    def get_macro_policy_news(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取宏观政策 / 财经监管资讯（东方财富 column=345）。

        返回 [{title, url, source, date}, ...]，失败时返回空列表。
        """
        results: List[Dict[str, str]] = []
        url = EM_NEWS_API.format(column=345, size=limit, ts=int(time.time() * 1000))
        data = self._fetch_json(url)
        try:
            items = (data or {}).get("data", {}).get("list", []) or []
        except AttributeError:
            items = []
        for it in items:
            title = (it.get("title") or "").strip()
            href = it.get("url") or ""
            date = (it.get("showTime") or "")[:10]
            if title and href:
                results.append({"title": title, "url": href,
                                "source": "东方财富-宏观政策", "date": date})
            if len(results) >= limit:
                break
        return results[:limit]

    def get_market_news(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取财经要闻（东方财富 column=344）。"""
        results: List[Dict[str, str]] = []
        url = EM_NEWS_API.format(column=344, size=limit, ts=int(time.time() * 1000))
        data = self._fetch_json(url)
        try:
            items = (data or {}).get("data", {}).get("list", []) or []
        except AttributeError:
            items = []
        for it in items:
            title = (it.get("title") or "").strip()
            href = it.get("url") or ""
            date = (it.get("showTime") or "")[:10]
            if title and href:
                results.append({"title": title, "url": href,
                                "source": "东方财富-财经要闻", "date": date})
            if len(results) >= limit:
                break
        return results[:limit]

    # ==================== 新浪财经滚动新闻 ====================

    def get_sina_finance_news(self, limit: int = 20, lid: int = 2516) -> List[Dict[str, str]]:
        """获取新浪财经滚动新闻（lid=2516 财经/宏观，2510 要闻）。"""
        results: List[Dict[str, str]] = []
        url = SINA_ROLL_API.format(lid=lid, size=limit)
        data = self._fetch_json(url)
        try:
            items = (data or {}).get("result", {}).get("data", []) or []
        except AttributeError:
            items = []
        for it in items:
            title = (it.get("title") or "").strip()
            href = it.get("url") or ""
            ctime = it.get("ctime", "")
            date = ""
            if ctime:
                try:
                    date = datetime.fromtimestamp(int(ctime)).strftime("%Y-%m-%d")
                except (ValueError, OSError, OverflowError):
                    date = ""
            if title and href:
                results.append({"title": title, "url": href,
                                "source": "新浪财经-滚动", "date": date})
            if len(results) >= limit:
                break
        return results[:limit]

    # ==================== 巨潮资讯公告 ====================

    def get_announcements(self, limit: int = 20, market: str = "szse") -> List[Dict[str, str]]:
        """获取 A股上市公司公告（巨潮资讯查询 API）。"""
        results: List[Dict[str, str]] = []
        payload = {
            "pageNum": 1,
            "pageSize": min(limit, 30),
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": "",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        data = self._fetch_json_post(CNINFO_QUERY_API, payload)
        try:
            items = (data or {}).get("announcements") or []
        except AttributeError:
            items = []
        for it in items:
            title = (it.get("announcementTitle") or "").strip()
            adj = (it.get("adjunctUrl") or "").strip()
            href = f"http://static.cninfo.com.cn/{adj}" if adj else ""
            ts = it.get("announcementTime") or 0
            date = ""
            if ts:
                try:
                    date = datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d")
                except (ValueError, OSError, OverflowError):
                    date = ""
            if title and href:
                results.append({"title": title, "url": href,
                                "source": "巨潮资讯-公告", "date": date})
            if len(results) >= limit:
                break
        return results[:limit]

    # ==================== 跨源搜索 ====================

    def search_all(self, keyword: str, limit: int = 30) -> List[Dict[str, str]]:
        """跨东财 / 新浪 / 巨潮搜索关键词。"""
        results = []
        for source, func in [
            ("EM", self.get_macro_policy_news),
            ("SINA", self.get_sina_finance_news),
            ("CNINFO", self.get_announcements),
        ]:
            try:
                items = func(limit=limit)
                for item in items:
                    if keyword.lower() in item.get("title", "").lower():
                        item["source"] = f"{source} - {item.get('source', source)}"
                        results.append(item)
            except Exception as e:
                logger.warning(f"{source} 搜索失败: {e}")
        return results[:limit]

    # ==================== 政策文件下载与分析（保留） ====================

    def download_document(self, url: str, save_dir: Optional[str] = None) -> str:
        """下载政策文件/公告到本地。

        支持 PDF / DOC / DOCX / HTML / 纯文本附件。

        Args:
            url: 文件链接
            save_dir: 保存目录，默认 data/regulatory_docs/

        Returns:
            保存的文件路径；失败返回空字符串
        """
        if not url:
            return ""
        import os
        save_dir = save_dir or str(Path(__file__).resolve().parent.parent / "data" / "regulatory_docs")
        os.makedirs(save_dir, exist_ok=True)

        # 推断文件名
        path_part = url.split("?")[0].rstrip("/")
        fname = path_part.split("/")[-1] or f"doc_{int(time.time())}.html"
        fname = re.sub(r'[\\/:*?"<>|]', "_", fname)
        if "." not in fname:
            fname += ".html"
        save_path = os.path.join(save_dir, fname)

        try:
            resp = self.session.get(url, timeout=30, stream=True)
            content_type = (resp.headers.get("Content-Type", "") if hasattr(resp, "headers") else "") or ""
            # 若文件名无扩展名，根据 Content-Type 推断
            if fname.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".html", ".htm")):
                pass
            elif "pdf" in content_type.lower():
                save_path = os.path.splitext(save_path)[0] + ".pdf"
            elif "word" in content_type.lower() or "doc" in content_type.lower():
                save_path = os.path.splitext(save_path)[0] + ".doc"
            elif "html" in content_type.lower():
                save_path = os.path.splitext(save_path)[0] + ".html"

            if hasattr(resp, "iter_content"):
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                data = resp.content if hasattr(resp, "content") else resp.read()
                with open(save_path, "wb") as f:
                    f.write(data)
            logger.info(f"政策文件已下载: {save_path}")
            return save_path
        except Exception as e:
            logger.warning(f"政策文件下载失败: {url}, {e}")
            return ""

    def analyze_policy(self, url_or_path: str, keyword: str = "") -> Dict[str, Any]:
        """下载并分析政策文件/公告，提取关键信息。

        支持 PDF（pypdf）/ HTML / 纯文本。返回结构化分析结果，
        包括标题、发布时间、正文文本、关键词命中、内容摘要。

        Args:
            url_or_path: 政策文件 URL 或本地文件路径
            keyword: 关注关键词（如 "利率"、"风险"），命中时高亮

        Returns:
            {
                "title": str, "date": str, "source_url": str,
                "content_length": int, "content_preview": str,
                "keywords_hit": [...], "summary": str,
                "saved_path": str, "warning": str | None,
            }
        """
        import os
        # 判断是 URL 还是本地路径
        is_url = url_or_path.startswith("http://") or url_or_path.startswith("https://")
        local_path = ""
        html = ""
        text = ""

        if is_url:
            # 先尝试直接抓取 HTML 文本
            html = self._fetch_html(url_or_path, timeout=30) or ""
            # 下载附件（若页面是 PDF 链接则下载）
            local_path = self.download_document(url_or_path)
            file_text = self._extract_file_text(local_path) if local_path else ""
            if file_text and not html:
                text = file_text
        else:
            local_path = url_or_path
            if os.path.isfile(url_or_path):
                text = self._extract_file_text(url_or_path)

        # 从 HTML 提取正文
        if html and not text:
            text = self._html_to_text(html)

        if not text:
            return {
                "error": "无法提取文档内容", "source_url": url_or_path,
                "warning": "内容为空或文件格式不支持",
            }

        # 结构化
        title = ""
        if is_url and html:
            m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
            if m:
                title = m.group(1).strip()
        if not title:
            title = Path(url_or_path.split("?")[0]).name if is_url else Path(url_or_path).name

        date = ""
        # 从正文/URL 中提取日期
        for pat in [r"(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})", r"(\d{4})年(\d{1,2})月(\d{1,2})日"]:
            m = re.search(pat, url_or_path + " " + text[:3000])
            if m:
                date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                break

        # 关键词命中
        hits = []
        if keyword:
            for kw in re.split(r"[，,、/\s]+", keyword):
                kw = kw.strip()
                if kw and kw in text:
                    hits.append(kw)

        # 内容摘要：取开头 + 含关键词的句子
        summary = self._make_summary(text, hits)

        return {
            "title": title,
            "date": date,
            "source_url": url_or_path,
            "content_length": len(text),
            "content_preview": text[:500],
            "keywords_hit": hits,
            "summary": summary,
            "saved_path": local_path,
        }

    def _extract_file_text(self, path: str) -> str:
        """从本地文件提取文本（PDF/DOCX/TXT/HTML）。"""
        import os
        if not os.path.isfile(path):
            return ""
        lower = path.lower()
        try:
            if lower.endswith(".pdf"):
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    return "\n".join((pg.extract_text() or "") for pg in reader.pages)
                except ImportError:
                    return "[PDF 解析需要 pypdf 库: pip install pypdf]"
            elif lower.endswith(".docx"):
                try:
                    from docx import Document
                    doc = Document(path)
                    return "\n".join(p.text for p in doc.paragraphs)
                except ImportError:
                    return "[DOCX 解析需要 python-docx 库]"
            elif lower.endswith((".html", ".htm")):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return self._html_to_text(f.read())
            else:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"文件解析失败 {path}: {e}")
            return ""

    def _html_to_text(self, html: str) -> str:
        """HTML 转纯文本。"""
        if not html:
            return ""
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))
        return re.sub(r"<[^>]+>", "\n", html)

    def _make_summary(self, text: str, hits: List[str]) -> str:
        """生成政策文件摘要：开头段落 + 关键词相关句子。"""
        sentences = re.split(r"[。！？\n]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        summary = []
        # 开头 2 句
        summary.extend(sentences[:2])
        # 关键词相关句子（最多 3 句）
        if hits:
            added = 0
            for s in sentences:
                if added >= 3:
                    break
                if any(kw in s for kw in hits) and s not in summary:
                    summary.append(s)
                    added += 1
        if not summary:
            summary = sentences[:3]
        return "。".join(summary[:5]) + ("。" if summary and not summary[-1].endswith("。") else "")

    # ==================== 跨源检索 / 批量下载 ====================

    _AGENCY_SOURCES = {
        "pboc": [("EM", "macro")],
        "csrc": [("CNINFO", "announcements")],
        "nfra": [("SINA", "finance")],
        "all": [("EM", "macro"), ("SINA", "finance"), ("CNINFO", "announcements")],
    }

    def _agency_scrapers(self, agency: str = "all") -> List[tuple]:
        """按 agency 参数返回 (源名, 方法) 列表（兼容旧参数 pboc/csrc/nfra）。"""
        mapping = {
            "EM": ("EM", self.get_macro_policy_news),
            "SINA": ("SINA", self.get_sina_finance_news),
            "CNINFO": ("CNINFO", self.get_announcements),
        }
        keys = [k for k, _ in self._AGENCY_SOURCES.get(agency, self._AGENCY_SOURCES["all"])]
        return [mapping[k] for k in keys]

    def search_policy_documents(self, keyword: str, agency: str = "all",
                                limit: int = 20) -> List[Dict[str, Any]]:
        """跨数据源检索政策/公告，并标记可下载附件。

        对每个命中的条目尝试提取其正文链接与附件链接（PDF/DOC）。

        Args:
            keyword: 搜索关键词
            agency: all / pboc / csrc / nfra（兼容旧参数，映射到商业数据源）
            limit: 返回条数

        Returns:
            [
                {"title": str, "url": str, "date": str, "source": str,
                 "doc_url": str | None, "content_preview": str}, ...
            ]
        """
        from urllib.parse import urljoin
        results = []
        for source, func in self._agency_scrapers(agency):
            try:
                items = func(limit=max(limit * 3, 30))
            except Exception as e:
                logger.warning(f"{source} 检索失败: {e}")
                continue
            for it in items:
                if keyword.lower() not in it.get("title", "").lower():
                    continue
                entry = dict(it)
                entry["source"] = f"{source} - {entry.get('source', source)}"
                url = entry.get("url", "")
                # 标记附件链接（PDF/DOC/XLS）
                doc_url = None
                if url and re.search(r"\.(pdf|doc|docx|xls|xlsx)(\?|$)", url.lower()):
                    doc_url = url
                entry["doc_url"] = doc_url
                entry["content_preview"] = ""
                results.append(entry)
                if len(results) >= limit:
                    return results
        return results[:limit]

    def crawl_policy_documents(self, agency: str = "all", limit: int = 20,
                               save_dir: Optional[str] = None) -> Dict[str, Any]:
        """爬取并下载最新政策文件/公告。

        1. 拉取数据源最新公告列表
        2. 识别并下载 PDF/DOC 附件
        3. 对下载的文档做内容分析

        Args:
            agency: all / pboc / csrc / nfra（兼容旧参数，映射到商业数据源）
            limit: 下载数量上限
            save_dir: 保存目录

        Returns:
            {
                "total_found": int, "downloaded": int,
                "documents": [ {title, url, saved_path, analysis}, ... ],
                "warnings": [...],
            }
        """
        results: List[Dict[str, Any]] = []
        warnings: List[str] = []
        for source, func in self._agency_scrapers(agency):
            try:
                items = func(limit=max(limit * 3, 30))
            except Exception as e:
                warnings.append(f"{source} 列表获取失败: {e}")
                continue
            for it in items:
                if len(results) >= limit:
                    break
                url = it.get("url", "")
                if not url:
                    continue
                title = it.get("title", "")
                doc_url = url if re.search(r"\.(pdf|doc|docx|xls|xlsx)(\?|$)", url.lower()) else url
                saved = self.download_document(doc_url, save_dir)
                analysis = {}
                if saved:
                    analysis = self.analyze_policy(saved, keyword="")
                results.append({
                    "title": title,
                    "url": url,
                    "source": source,
                    "saved_path": saved,
                    "analysis": analysis,
                })
            if len(results) >= limit:
                break

        return {
            "total_found": len(results),
            "downloaded": sum(1 for r in results if r["saved_path"]),
            "documents": results,
            "warnings": warnings,
        }


# ==================== 便捷函数 ====================


def download_policy_document(url: str, save_dir: Optional[str] = None) -> str:
    """下载监管政策文件/公告到本地。"""
    return RegulatoryScraper().download_document(url, save_dir)


def analyze_policy_document(url_or_path: str, keyword: str = "") -> Dict[str, Any]:
    """下载并分析监管政策文件/公告，返回结构化分析。"""
    return RegulatoryScraper().analyze_policy(url_or_path, keyword)


def search_policy_documents(keyword: str, agency: str = "all",
                            limit: int = 20) -> List[Dict[str, Any]]:
    """跨数据源检索政策文件/公告。"""
    return RegulatoryScraper().search_policy_documents(keyword, agency, limit)


def crawl_policy_documents(agency: str = "all", limit: int = 20,
                           save_dir: Optional[str] = None) -> Dict[str, Any]:
    """爬取并下载最新政策文件/公告。"""
    return RegulatoryScraper().crawl_policy_documents(agency, limit, save_dir)


def get_regulatory_updates(agency: str = "all", limit: int = 20) -> List[Dict[str, str]]:
    """获取监管与政策资讯最新动态。

    Args:
        agency: all / pboc / csrc / nfra（兼容旧参数，映射到商业数据源：
                pboc→宏观政策资讯，csrc→A股公告，nfra→财经要闻）
        limit: 返回条数
    """
    scraper = RegulatoryScraper()
    if agency == "pboc":
        return scraper.get_macro_policy_news(limit)
    elif agency == "csrc":
        return scraper.get_announcements(limit)
    elif agency == "nfra":
        return scraper.get_sina_finance_news(limit)
    else:
        results = []
        results.extend(scraper.get_macro_policy_news(max(limit // 3, 5)))
        results.extend(scraper.get_sina_finance_news(max(limit // 3, 5)))
        results.extend(scraper.get_announcements(max(limit // 3, 5)))
        return results[:limit]


def get_monetary_policy() -> Dict[str, Any]:
    """获取最新货币政策/财经要闻摘要（LPR、公开市场、宏观资讯）。"""
    scraper = RegulatoryScraper()
    policy_news = scraper.get_macro_policy_news(limit=5)
    market_news = scraper.get_sina_finance_news(limit=5)
    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monetary_policy_count": len(policy_news),
        "monetary_policy": policy_news,
        "open_market_operations_count": len(market_news),
        "open_market_operations": market_news,
    }


# ==================== 自测入口 ====================

if __name__ == "__main__":
    print("=== 金融监管与政策资讯爬虫 v2.0 自测 ===\n")

    scraper = RegulatoryScraper()

    print("[EM] 宏观政策资讯:")
    for i, item in enumerate(scraper.get_macro_policy_news(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n[SINA] 财经要闻:")
    for i, item in enumerate(scraper.get_sina_finance_news(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n[CNINFO] A股公告:")
    for i, item in enumerate(scraper.get_announcements(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n=== 自测完成 ===")
