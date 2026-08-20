# -*- coding: utf-8 -*-
"""
金融公告爬取模块
支持页面结构扫描、公告搜索、PDF下载
"""
from __future__ import annotations

import json
import re
import time
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 数据目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_DOWNLOAD_DIR = SKILL_DATA_DIR / "announcements"


@dataclass
class Announcement:
    """公告信息"""
    title: str
    url: str
    publish_date: str = ""
    announcement_type: str = ""  # 年报、季报、招募说明书、分红等
    fund_code: str = ""
    fund_name: str = ""
    file_type: str = ""  # pdf, html, doc
    file_size: int = 0
    local_path: str = ""  # 下载后本地路径
    is_downloaded: bool = False


@dataclass
class PageStructure:
    """页面结构"""
    url: str
    title: str
    links: List[Dict[str, str]] = field(default_factory=list)  # [{"text": "", "href": ""}]
    sections: List[str] = field(default_factory=list)
    nav_items: List[Dict[str, str]] = field(default_factory=list)
    breadcrumbs: List[str] = field(default_factory=list)
    hint: str = ""


class PageStructureScanner:
    """页面结构扫描器"""

    def __init__(self):
        self.fetcher = None
        if SCRAPLING_AVAILABLE:
            self.fetcher = DynamicFetcher()
        self.scanned_urls = set()

    def scan_page(self, url: str,
                  max_depth: int = 2,
                  max_links: int = 100) -> PageStructure:
        """
        扫描页面结构

        Args:
            url: 目标URL
            max_depth: 最大扫描深度
            max_links: 最大链接数

        Returns:
            PageStructure对象
        """
        result = PageStructure(url=url, title="")

        if self.fetcher is None:
            result.title = "Scrapling未安装"
            return result

        try:
            page = self.fetcher.fetch(url, headless=True)
            result.title = self._extract_title(page)

            # 提取面包屑
            result.breadcrumbs = self._extract_breadcrumbs(page)

            # 提取导航菜单
            result.nav_items = self._extract_nav_items(page)

            # 提取所有链接
            result.links = self._extract_links(page, url, max_links)

            # 提取页面分区
            result.sections = self._extract_sections(page)

        except Exception as e:
            result.title = "扫描失败"
            result.hint = "可能是网络连接问题或目标网站不可访问，请稍后重试"

        return result

    def _extract_title(self, page: Selector) -> str:
        """提取页面标题"""
        try:
            title_el = page.css_first("title")
            if title_el:
                return title_el.text().strip()
            h1 = page.css_first("h1")
            if h1:
                return h1.text().strip()
        except:
            pass
        return ""

    def _extract_breadcrumbs(self, page: Selector) -> List[str]:
        """提取面包屑导航"""
        breadcrumbs = []
        selectors = [
            ".breadcrumbs a",
            ".breadcrumb a",
            "[class*='breadcrumb'] a",
            ".nav-crumb a",
            "#crumb a",
            "nav[class*='path'] a"
        ]

        for sel in selectors:
            try:
                els = page.css(sel)
                if els:
                    for el in els:
                        text = el.text().strip()
                        if text:
                            breadcrumbs.append(text)
                    if breadcrumbs:
                        break
            except:
                continue

        return breadcrumbs

    def _extract_nav_items(self, page: Selector) -> List[Dict[str, str]]:
        """提取导航菜单项"""
        nav_items = []
        selectors = [
            "nav a",
            ".header-nav a",
            ".main-nav a",
            "[class*='nav'] a",
            ".menu a"
        ]

        for sel in selectors:
            try:
                els = page.css(sel)
                for el in els[:20]:  # 限制数量
                    text = el.text().strip()
                    href = el.get_attribute("href") or ""
                    if text and href and not href.startswith("#"):
                        nav_items.append({"text": text, "href": href})
                if nav_items:
                    break
            except:
                continue

        return nav_items[:20]

    def _extract_links(self, page: Selector, base_url: str, max_links: int) -> List[Dict[str, str]]:
        """提取页面所有链接"""
        links = []
        seen = set()

        try:
            all_links = page.css("a[href]")
            for link in all_links:
                if len(links) >= max_links:
                    break

                text = link.text().strip()
                href = link.get_attribute("href") or ""

                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue

                # 转换为绝对URL
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)

                # 只保留同域名的链接
                if parsed.netloc and text:
                    # 去重
                    if full_url not in seen:
                        seen.add(full_url)
                        links.append({
                            "text": text[:100],  # 限制长度
                            "href": full_url,
                            "domain": parsed.netloc
                        })

        except Exception as e:
            pass

        return links

    def _extract_sections(self, page: Selector) -> List[str]:
        """提取页面主要分区"""
        sections = []
        selectors = [
            "section h2",
            "section h3",
            ".section-title",
            "[class*='section'] h2",
            ".mod-title",
            ".box-title"
        ]

        for sel in selectors:
            try:
                els = page.css(sel)
                for el in els[:10]:
                    text = el.text().strip()
                    if text and text not in sections:
                        sections.append(text)
            except:
                continue

        return sections[:15]

    def scan_site_map(self, url: str, pattern: str = "") -> List[str]:
        """
        扫描站点地图

        Args:
            url: 站点URL
            pattern: URL过滤模式

        Returns:
            URL列表
        """
        urls = []

        # 尝试常见sitemap位置
        sitemap_urls = [
            urljoin(url, "/sitemap.xml"),
            urljoin(url, "/sitemap.xml.gz"),
            urljoin(url, "/sitemap/index.xml"),
            urljoin(url, "/sitemap/news.xml"),
        ]

        for sitemap_url in sitemap_urls:
            try:
                if REQUESTS_AVAILABLE:
                    resp = requests.get(sitemap_url, timeout=10)
                    if resp.status_code == 200:
                        # 解析XML
                        urls.extend(self._parse_sitemap_xml(resp.text))
            except:
                pass

        # 如果没找到sitemap，扫描页面
        if not urls:
            structure = self.scan_page(url, max_depth=1, max_links=200)
            for link in structure.links:
                href = link.get("href", "")
                if pattern and re.search(pattern, href):
                    urls.append(href)
                elif not pattern:
                    urls.append(href)

        return list(set(urls))

    def _parse_sitemap_xml(self, xml_content: str) -> List[str]:
        """解析sitemap XML"""
        urls = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            # 支持标准sitemap格式
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('sm:url', ns):
                loc = url_elem.find('sm:loc', ns)
                if loc is not None and loc.text:
                    urls.append(loc.text)

            # 也支持无命名空间的格式
            if not urls:
                for url_elem in root.findall('url'):
                    loc = url_elem.find('loc')
                    if loc is not None and loc.text:
                        urls.append(loc.text)

        except:
            # 尝试用正则提取
            urls = re.findall(r'<loc[^>]*>([^<]+)</loc>', xml_content)

        return urls


class AnnouncementSearcher:
    """金融公告搜索器"""

    # 常见公告类型
    ANNOUNCEMENT_TYPES = {
        "年报": ["annual_report", "年度报告", "年报"],
        "半年报": ["half_year_report", "半年报", "中期报告"],
        "季报": ["quarterly_report", "季报", "季度报告"],
        "招募说明书": ["prospectus", "招募说明书", "招募书"],
        "分红": ["dividend", "分红", "收益分配"],
        "净值公告": ["nav", "净值公告", "净值波动"],
        "基金经理变更": ["manager_change", "基金经理变更", "基金经理"],
        "暂停申购": ["suspend", "暂停申购", "限购"],
        "恢复申购": ["resume", "恢复申购", "开放申购"],
        "清算": ["liquidation", "清算", "终止"],
        "持有人大会": ["holder_meeting", "持有人大会", "股东大会"],
        "关联交易": ["related_party", "关联交易", "关联人"],
        "投资组合": ["portfolio", "投资组合", "持仓"],
        "分红预告": ["dividend_notice", "分红预告", "分配预告"],
        "审计报告": ["audit", "审计报告", "审计"],
        "法律意见": ["legal", "法律意见", "律师"]
    }

    def __init__(self):
        self.fetcher = None
        if SCRAPLING_AVAILABLE:
            self.fetcher = DynamicFetcher()
        self.base_urls = {
            "eastmoney": "https://fund.eastmoney.com",
            "cninfo": "https://www.cninfo.com.cn",
            "szse": "https://www.szse.cn",
            "sse": "https://www.sse.com.cn"
        }

    def search_announcements(self,
                           keyword: str,
                           fund_code: str = "",
                           ann_type: str = "",
                           date_from: str = "",
                           date_to: str = "",
                           max_results: int = 50) -> List[Announcement]:
        """
        搜索公告

        Args:
            keyword: 搜索关键词
            fund_code: 基金代码
            ann_type: 公告类型（年报、季报等）
            date_from: 开始日期 YYYY-MM-DD
            date_to: 结束日期 YYYY-MM-DD
            max_results: 最大结果数

        Returns:
            Announcement列表
        """
        results = []

        # 如果有基金代码，优先从天天基金搜索
        if fund_code:
            results.extend(self._search_eastmoney(fund_code, ann_type, max_results))

        # 从巨潮资讯搜索
        if not results or len(results) < max_results:
            results.extend(self._search_cninfo(keyword, fund_code, date_from, date_to, max_results - len(results)))

        return results[:max_results]

    def _search_eastmoney(self, fund_code: str,
                         ann_type: str = "",
                         max_results: int = 50) -> List[Announcement]:
        """从天天基金搜索公告"""
        results = []

        # 天天基金公告页面URL
        url = f"https://fundf10.eastmoney.com/jjgg_{fund_code}_1.html"

        if self.fetcher is None:
            return results

        try:
            page = self.fetcher.fetch(url, headless=True)
            announcements = self._parse_eastmoney_announcements(page.html_content, fund_code)

            # 按类型过滤
            if ann_type:
                type_keywords = self.ANNOUNCEMENT_TYPES.get(ann_type, [ann_type])
                announcements = [a for a in announcements
                               if any(kw in a.title for kw in type_keywords)]

            results.extend(announcements[:max_results])

        except Exception as e:
            pass

        return results

    def _parse_eastmoney_announcements(self, html_text: str, fund_code: str) -> List[Announcement]:
        """解析天天基金公告列表（正则版本，兼容JS渲染后的HTML）"""
        announcements = []

        # 查找 class="w782 comm jjgg" 的表格
        table_match = re.search(r'<table[^>]*class="w782 comm jjgg"[^>]*>(.*?)</table>', html_text, re.DOTALL)
        if not table_match:
            return announcements

        table_html = table_match.group(1)
        rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)

        for row in rows:
            try:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if not cells or len(cells) < 2:
                    continue

                # 提取标题和链接（第一个td）
                title_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', cells[0])
                if not title_match:
                    continue

                link = title_match.group(1).strip()
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()

                # 提取分类（第二个td）
                ann_type = re.sub(r'<[^>]+>', '', cells[1]).strip()

                # 构造完整URL
                if link.startswith('http'):
                    full_url = link
                elif ',' in link:
                    full_url = f"http://fund.eastmoney.com/gonggao/{fund_code},{link.split(',')[-1]}"
                else:
                    full_url = link

                if not title:
                    continue

                announcement = Announcement(
                    title=title,
                    url=full_url,
                    publish_date="",
                    announcement_type=ann_type,
                    fund_code=fund_code,
                    file_type=self._detect_file_type(link)
                )
                announcements.append(announcement)

            except Exception:
                continue

        return announcements

    def _search_cninfo(self, keyword: str,
                      fund_code: str = "",
                      date_from: str = "",
                      date_to: str = "",
                      max_results: int = 50) -> List[Announcement]:
        """从巨潮资讯搜索公告"""
        results = []

        # 巨潮资讯搜索URL
        if fund_code:
            url = f"https://www.cninfo.com.cn/new/disclosure/detail?stockCode={fund_code}"
        else:
            url = f"https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?searchkey={keyword}"

        if self.fetcher is None:
            return results

        try:
            page = self.fetcher.fetch(url, headless=True)
            results.extend(self._parse_cninfo_announcements(page))

        except Exception as e:
            pass

        return results

    def _parse_cninfo_announcements(self, page: Selector) -> List[Announcement]:
        """解析巨潮资讯公告"""
        announcements = []

        selectors = [
            ".notice-list .item",
            ".announcement-item",
            "[class*='notice'] .list-item",
            "table.announce tr"
        ]

        for sel in selectors:
            try:
                items = page.css(sel)
                for item in items:
                    link_el = item.css_first("a")
                    if link_el:
                        href = link_el.get_attribute("href") or ""
                        title = link_el.text().strip()
                        date = ""
                        date_el = item.css(".date, .time")
                        if date_el:
                            date = date_el[0].text().strip()

                        ann = Announcement(
                            title=title,
                            url=href if href.startswith("http") else f"https://www.cninfo.com.cn{href}",
                            publish_date=date,
                            file_type=self._detect_file_type(href)
                        )
                        announcements.append(ann)
                break
            except:
                continue

        return announcements

    def _detect_file_type(self, url: str) -> str:
        """检测附件类型"""
        url_lower = url.lower()
        if ".pdf" in url_lower or "pdf" in url_lower:
            return "pdf"
        elif ".doc" in url_lower or "docx" in url_lower:
            return "doc"
        elif ".xls" in url_lower or "xlsx" in url_lower:
            return "xls"
        elif ".html" in url_lower or "htm" in url_lower:
            return "html"
        return "unknown"

    def _guess_announcement_type(self, title: str) -> str:
        """猜测公告类型"""
        title_upper = title.upper()

        for ann_type, keywords in self.ANNOUNCEMENT_TYPES.items():
            for kw in keywords:
                if kw.upper() in title_upper:
                    return ann_type

        return "其他"

    def get_announcement_types(self) -> List[str]:
        """获取支持的公告类型"""
        return list(self.ANNOUNCEMENT_TYPES.keys())


class PDFDownloader:
    """PDF文件下载器"""

    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir) if download_dir else DEFAULT_DOWNLOAD_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

        self.downloaded_files = []
        self.failed_files = []

    def download_announcement(self,
                             announcement: Announcement,
                             subfolder: str = "") -> str:
        """
        下载单条公告

        Args:
            announcement: Announcement对象
            subfolder: 子文件夹（如基金代码）

        Returns:
            本地文件路径
        """
        if not announcement.url:
            return ""

        # 确定保存路径
        save_dir = self.download_dir
        if subfolder:
            save_dir = save_dir / subfolder
        save_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        filename = self._generate_filename(announcement)
        save_path = save_dir / filename

        # 如果文件已存在，跳过
        if save_path.exists():
            announcement.is_downloaded = True
            announcement.local_path = str(save_path)
            return str(save_path)

        # 下载文件
        success = self._download_file(announcement.url, save_path)

        if success:
            announcement.is_downloaded = True
            announcement.local_path = str(save_path)
            self.downloaded_files.append(str(save_path))
        else:
            self.failed_files.append(announcement.url)

        return str(save_path) if success else ""

    def batch_download(self,
                      announcements: List[Announcement],
                      subfolder_template: str = "{fund_code}",
                      progress_callback: Callable = None) -> Dict[str, Any]:
        """
        批量下载公告

        Args:
            announcements: Announcement列表
            subfolder_template: 子文件夹模板，支持{type}, {fund_code}
            progress_callback: 进度回调函数

        Returns:
            下载结果统计
        """
        self.downloaded_files = []
        self.failed_files = []

        total = len(announcements)
        for i, ann in enumerate(announcements):
            # 生成子文件夹名
            subfolder = subfolder_template.format(
                type=ann.announcement_type or "其他",
                fund_code=ann.fund_code or "unknown",
                date=ann.publish_date or ""
            )

            self.download_announcement(ann, subfolder)

            if progress_callback:
                progress_callback(i + 1, total)

        return {
            "total": total,
            "downloaded": len(self.downloaded_files),
            "failed": len(self.failed_files),
            "downloaded_files": self.downloaded_files,
            "failed_urls": self.failed_files
        }

    def _download_file(self, url: str, save_path: Path) -> bool:
        """下载文件"""
        if self.session is None:
            return False

        try:
            resp = self.session.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                # 检测实际文件类型
                content_type = resp.headers.get('Content-Type', '')
                if 'pdf' not in content_type.lower() and not str(save_path).endswith('.pdf'):
                    # 从Content-Disposition获取文件名
                    cd = resp.headers.get('Content-Disposition', '')
                    fname_match = re.search(r'filename[^=]*=([^;]+)', cd)
                    if fname_match:
                        fname = fname_match.group(1).strip('" ')
                        save_path = save_path.parent / fname

                # 保存文件
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 更新文件权限（Windows 不支持 Unix 权限）
                import platform
                if platform.system() != 'Windows':
                    try:
                        save_path.chmod(0o644)
                    except (OSError, AttributeError):
                        pass
                return True

        except Exception as e:
            pass

        return False

    def _generate_filename(self, announcement: Announcement) -> str:
        """生成文件名"""
        # 清理标题
        safe_title = re.sub(r'[<>:"/\\|?*]', '', announcement.title)
        safe_title = safe_title[:50]  # 限制长度

        # 添加日期和类型
        date_str = announcement.publish_date.replace("-", "") if announcement.publish_date else ""
        ann_type = announcement.announcement_type or "其他"

        ext = self._get_extension(announcement)

        return f"{date_str}_{ann_type}_{safe_title}{ext}"

    def _get_extension(self, announcement: Announcement) -> str:
        """获取文件扩展名"""
        if announcement.file_type:
            return f".{announcement.file_type}"

        # 从URL推断
        url_lower = announcement.url.lower()
        if ".pdf" in url_lower:
            return ".pdf"
        elif ".doc" in url_lower:
            return ".doc"
        elif ".docx" in url_lower:
            return ".docx"
        elif ".xls" in url_lower:
            return ".xls"
        elif ".xlsx" in url_lower:
            return ".xlsx"

        return ".pdf"  # 默认PDF


class AnnouncementManager:
    """公告管理器 - 整合以上功能"""

    def __init__(self, download_dir: str = None):
        self.scanner = PageStructureScanner()
        self.searcher = AnnouncementSearcher()
        self.downloader = PDFDownloader(download_dir)

    # v4.4.0 新增：search() 便捷方法，供 research_report_generator 和 crawl_scheduler 调用
    def search(self, keyword: str = "", limit: int = 20,
               fund_code: str = "", ann_type: str = "",
               date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
        """搜索公告。委托给 AnnouncementSearcher.search_announcements()"""
        results = self.searcher.search_announcements(
            keyword=keyword, fund_code=fund_code, ann_type=ann_type,
            date_from=date_from, date_to=date_to, limit=limit
        )
        return [
            {"title": r.title, "date": getattr(r, 'publish_date', ''),
             "url": getattr(r, 'url', ''), "fund_code": getattr(r, 'fund_code', fund_code),
             "announcement_type": getattr(r, 'announcement_type', ann_type)}
            for r in results[:limit]
        ]

    def scan_page_structure(self, url: str) -> PageStructure:
        """扫描页面结构"""
        return self.scanner.scan_page(url)

    def search_and_download(self,
                           keyword: str = "",
                           fund_code: str = "",
                           ann_type: str = "",
                           date_from: str = "",
                           date_to: str = "",
                           download_dir: str = "",
                           subfolder_template: str = "{fund_code}") -> Dict[str, Any]:
        """
        搜索并下载公告

        Args:
            keyword: 搜索关键词
            fund_code: 基金代码
            ann_type: 公告类型
            date_from: 开始日期
            date_to: 结束日期
            download_dir: 下载目录
            subfolder_template: 子文件夹模板

        Returns:
            结果统计
        """
        # 设置下载目录
        if download_dir:
            self.downloader = PDFDownloader(download_dir)

        # 搜索公告
        announcements = self.searcher.search_announcements(
            keyword=keyword,
            fund_code=fund_code,
            ann_type=ann_type,
            date_from=date_from,
            date_to=date_to
        )

        # 过滤PDF
        pdf_announcements = [a for a in announcements if a.file_type == "pdf"]

        # 批量下载
        result = self.downloader.batch_download(
            pdf_announcements,
            subfolder_template=subfolder_template
        )

        result["announcements"] = announcements
        result["pdf_count"] = len(pdf_announcements)

        return result

    def download_fund_announcements(self,
                                   fund_code: str,
                                   ann_types: List[str] = None,
                                   download_dir: str = None) -> Dict[str, Any]:
        """
        下载指定基金的所有公告

        Args:
            fund_code: 基金代码
            ann_types: 公告类型列表（为空则下载所有）
            download_dir: 下载目录

        Returns:
            下载结果
        """
        if download_dir:
            self.downloader = PDFDownloader(download_dir)

        # 搜索所有公告
        announcements = self.searcher.search_announcements("", fund_code=fund_code)

        # 按类型过滤
        if ann_types:
            announcements = [a for a in announcements if a.announcement_type in ann_types]

        # 下载
        result = self.downloader.batch_download(announcements, "{fund_code}")

        result["announcements"] = announcements
        return result


# ============ CLI入口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python announcement_scraper.py scan <URL>                    # 扫描页面结构")
        print("  python announcement_scraper.py search <基金代码>             # 搜索公告")
        print("  python announcement_scraper.py download <基金代码>           # 下载公告PDF")
        print("  python announcement_scraper.py types                         # 列出公告类型")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        if len(sys.argv) < 3:
            print("请提供URL")
            sys.exit(1)
        url = sys.argv[2]
        manager = AnnouncementManager()
        structure = manager.scan_page_structure(url)
        print(f"标题: {structure.title}")
        print(f"\n面包屑: {' > '.join(structure.breadcrumbs)}")
        print(f"\n导航菜单 ({len(structure.nav_items)}项):")
        for item in structure.nav_items[:10]:
            print(f"  {item['text']}: {item['href']}")
        print(f"\n链接 ({len(structure.links)}个):")
        for link in structure.links[:20]:
            print(f"  {link['text'][:30]}: {link['href']}")

    elif cmd == "search":
        fund_code = sys.argv[2] if len(sys.argv) > 2 else ""
        manager = AnnouncementManager()
        announcements = manager.searcher.search_announcements("", fund_code=fund_code)
        print(f"找到 {len(announcements)} 条公告:\n")
        for ann in announcements[:20]:
            print(f"[{ann.announcement_type}] {ann.title}")
            print(f"  日期: {ann.publish_date} | 类型: {ann.file_type}")
            print(f"  链接: {ann.url}\n")

    elif cmd == "download":
        fund_code = sys.argv[2] if len(sys.argv) > 2 else input("请输入基金代码: ")
        download_dir = sys.argv[3] if len(sys.argv) > 3 else None

        manager = AnnouncementManager(download_dir)
        result = manager.download_fund_announcements(fund_code)

        print(f"下载完成:")
        print(f"  总数: {result['total']}")
        print(f"  成功: {result['downloaded']}")
        print(f"  失败: {result['failed']}")
        print(f"\n保存目录: {manager.downloader.download_dir}")

    elif cmd == "types":
        searcher = AnnouncementSearcher()
        types = searcher.get_announcement_types()
        print("支持的公告类型:")
        for t in types:
            print(f"  - {t}")

    else:
        print(f"未知命令: {cmd}")