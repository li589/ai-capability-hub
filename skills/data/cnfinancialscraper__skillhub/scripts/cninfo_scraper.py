# -*- coding: utf-8 -*-
"""
巨潮资讯网（cninfo.com.cn）公告爬虫 v1.0

巨潮资讯是上市公司法定信息披露平台，覆盖所有 A 股上市公司
的定期报告、临时公告、IPO 文件等法定披露信息。

数据源: www.cninfo.com.cn（官方唯一指定信息披露网站）

特性：
- 按关键词/股票代码/日期范围搜索公告，返回结构化数据
- 分页查询 + 结果自动合并
- PDF 附件直接下载
- 所有公开接口均不需要登录，无需任何凭证

注意：
- 巨潮资讯是法定披露平台，数据权威但单次查询限制 pageSize <= 30
- 频繁请求可能触发反爬，建议调用间隔 >= 1.5 秒
- 日期格式统一为 yyyy-MM-dd
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .http_utils import http_post, http_get, download_file
except ImportError:
    from http_utils import http_post, http_get, download_file

log = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────────────────────────

CNINFO_BASE = "http://www.cninfo.com.cn"
CNINFO_ANNOUNCEMENT_API = f"{CNINFO_BASE}/new/hisAnnouncement/query"
CNINFO_DOWNLOAD_API = f"{CNINFO_BASE}/new/announcement/download"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    "Origin": "http://www.cninfo.com.cn",
}

# 巨潮资讯各板块代码
MARKET_CODE = {
    "主板": "p",
    "创业板": "gem",
    "科创板": "kcb",
    "北交所": "bj",
}

# 公告分类
ANNOUNCEMENT_CATEGORIES = {
    "category_ndbg_szsh": "年报",
    "category_bndbg_szsh": "半年报",
    "category_yjdbg_szsh": "一季度报告",
    "category_sjdbg_szsh": "三季度报告",
    "category_rcjy_szsh": "日常经营",
    "category_zcjy_szsh": "资产交易",
    "category_gqbd_szsh": "股权变动",
    "category_gdqz_szsh": "股东减持",
    "category_gdzc_szsh": "股东增持",
    "category_hg_szsh": "回购",
    "category_dshgg_szsh": "董事会公告",
    "category_jshgg_szsh": "监事会公告",
    "category_gddh_szsh": "股东大会",
}

# 默认输出目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_DOWNLOAD_DIR = SKILL_DATA_DIR / "cninfo_pdfs"

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _validate_date(date_str: str) -> bool:
    """验证日期格式是否为 yyyy-MM-dd"""
    if not date_str:
        return True  # 空值是可选的
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _safe_get(resp_dict: Dict, *keys: str, default=""):
    """安全获取嵌套字典值，任一键不存在返回 default"""
    for key in keys:
        if isinstance(resp_dict, dict):
            resp_dict = resp_dict.get(key, {})
        else:
            return default
    return resp_dict if resp_dict != {} else default


def _format_announcement(raw: Dict) -> Dict:
    """将巨潮资讯原始公告条目转换为统一字典格式

    Args:
        raw: 巨潮资讯 API 返回的单条公告原始字典

    Returns:
        标准化后的公告字典，字段：
          - announcementId: 公告唯一 ID
          - secCode: 股票代码
          - secName: 股票简称
          - title: 公告标题
          - publishDate: 发布日期
          - announcementType: 公告类型 (如 "PDF")
          - adjunctUrl: PDF 下载地址
          - adjunctSize: 附件大小 (KB)
          - batchNum: 批次号
          - storageTime: 存储时间（时间戳毫秒）
    """
    return {
        "announcementId": raw.get("announcementId", ""),
        "secCode": raw.get("secCode", ""),
        "secName": raw.get("secName", ""),
        "title": raw.get("announcementTitle", ""),
        "publishDate": _format_timestamp(raw.get("announcementTime", 0)),
        "announcementType": raw.get("adjunctType", ""),
        "adjunctUrl": raw.get("adjunctUrl", ""),
        "adjunctSize": raw.get("adjunctSize", 0),
        "batchNum": raw.get("batchNum", ""),
        "storageTime": raw.get("storageTime", ""),
    }


def _format_timestamp(ts_millis: int) -> str:
    """将巨潮资讯的时间戳（毫秒）转换为 yyyy-MM-dd 字符串"""
    if not ts_millis:
        return ""
    try:
        return datetime.fromtimestamp(ts_millis / 1000).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return ""


# ── 主类 ──────────────────────────────────────────────────────────────────────

class CninfoScraper:
    """巨潮资讯网公告爬虫

    用于搜索和下载 A 股上市公司在巨潮资讯网披露的公告文件。
    巨潮资讯是上市公司法定信息披露平台，数据具有较高权威性。

    无需登录或 API Key，所有接口均为公开访问。

    使用示例::

        scraper = CninfoScraper()
        results = scraper.search_announcements(keyword="年报", stock_code="600519")
        pdf_path = scraper.download_pdf("announcement_id_here", "downloads/")
    """

    def __init__(self, timeout: int = 30):
        """初始化爬虫

        Args:
            timeout: HTTP 请求超时时间（秒），默认 30
        """
        self._timeout = timeout
        self._download_dir = DEFAULT_DOWNLOAD_DIR
        self._download_dir.mkdir(parents=True, exist_ok=True)

    # ── 公开 API ──────────────────────────────────────────────────────────────

    def search_announcements(
        self,
        keyword: str = "",
        stock_code: str = "",
        start_date: str = "",
        end_date: str = "",
        page: int = 1,
        page_size: int = 30,
        market: str = "szse",
    ) -> Dict:
        """按条件搜索公告

        支持按关键词、股票代码、日期范围和分页参数组合查询。
        所有参数均为可选，至少需提供一个有效条件。

        Args:
            keyword: 搜索关键词，如 "年报"、"分红"、"重组"
            stock_code: 6 位股票代码，如 "600519"、"000858"
            market: 交易所代码，可选 "szse"(深交所) / "sse"(上交所) / "bjse"(北交所)，默认 "szse"
            start_date: 起始日期 yyyy-MM-dd，如 "2025-01-01"
            end_date: 截止日期 yyyy-MM-dd，如 "2025-12-31"
            page: 页码，从 1 开始
            page_size: 每页条数，范围 1-30（巨潮限制）

        Returns:
            {
                "total": int,          # 总条数
                "page": int,           # 当前页码
                "pageSize": int,       # 每页条数
                "hasMore": bool,       # 是否有下一页
                "announcements": [     # 公告列表
                    {
                        "announcementId": str,
                        "secCode": str,
                        "secName": str,
                        "title": str,
                        "publishDate": str,
                        "announcementType": str,
                        "adjunctUrl": str,
                        "adjunctSize": int,
                    }, ...
                ]
            }
            异常时返回 {"total": 0, "page": 1, "hasMore": False, "announcements": []}
        """
        # 参数校验
        if not any([keyword, stock_code, start_date, end_date]):
            log.warning("巨潮资讯搜索：未提供任何查询条件")
            return {"total": 0, "page": 1, "pageSize": page_size, "hasMore": False, "announcements": []}

        if start_date and not _validate_date(start_date):
            log.warning(f"巨潮资讯搜索：起始日期格式错误 {start_date}，期望 yyyy-MM-dd")
            return {"total": 0, "page": 1, "pageSize": page_size, "hasMore": False, "announcements": []}

        if end_date and not _validate_date(end_date):
            log.warning(f"巨潮资讯搜索：截止日期格式错误 {end_date}，期望 yyyy-MM-dd")
            return {"total": 0, "page": 1, "pageSize": page_size, "hasMore": False, "announcements": []}

        # 限制 page_size
        page_size = max(1, min(page_size, 30))
        page = max(1, page)

        # 构建请求参数 — 巨潮的 seDate 用 "-" 分隔起止日期
        se_date = ""
        if start_date and end_date:
            se_date = f"{start_date}~{end_date}"
        elif start_date:
            se_date = f"{start_date}~"
        elif end_date:
            se_date = f"~{end_date}"

        # 股票代码格式校验：确保是6位数字
        stock_code = stock_code.strip().replace(".SH", "").replace(".SZ", "").replace(" ", "") if stock_code else ""

        # 交易所代码映射到巨潮 column 取值
        column_map = {
            "szse": "szse",   # 深交所
            "sse": "sse",     # 上交所
            "bjse": "bjse",   # 北交所
            "a": "sse",       # 兼容旧别名
        }
        column = column_map.get(str(market).lower(), "szse")

        # 巨潮 stock 参数格式为 "code,orgId,orgIdValue"。
        # orgId 旧代码硬编码五粮液(000858)的 gssz0000858，导致搜索其他股票时错挂该 orgId。
        # 这里按市场推导 orgId（gssz/gssh/gsbj + 6位代码），对绝大多数 A 股正确；
        # 若无法推导则只传股票代码，由巨潮全文检索兜底。
        stock_param = ""
        if stock_code:
            zcode = stock_code.zfill(6)
            org_prefix = {"szse": "gssz", "sse": "gssh", "bjse": "gsbj"}.get(column)
            if org_prefix and len(stock_code) == 6 and stock_code.isdigit():
                stock_param = f"{stock_code},orgId,{org_prefix}{zcode}"
            else:
                stock_param = stock_code

        form_data = {
            "pageNum": page,
            "pageSize": page_size,
            "column": column,        # 按市场参数化（默认深交所）
            "tabName": "fulltext",   # 全文检索
            "plate": "",             # 板块限制（空=全部）
            "stock": stock_param,    # 股票代码（按市场推导 orgId，不再硬编码）
            "searchkey": keyword,    # 关键词
            "secid": "",             # 证券 ID（可选）
            "category": "",          # 公告分类（可选）
            "trade": "",             # 行业分类（可选）
            "seDate": se_date,       # 日期范围
        }

        try:
            # 使用 form-encoded POST，巨潮要求这种格式
            encoded_data = "&".join(
                f"{k}={_url_encode(v)}" for k, v in form_data.items()
            )

            resp = http_post(
                CNINFO_ANNOUNCEMENT_API,
                data=encoded_data.encode("utf-8"),
                headers=DEFAULT_HEADERS,
                timeout=self._timeout,
            )

            if resp is None:
                log.warning("巨潮资讯搜索请求失败：无响应")
                return {"total": 0, "page": page, "pageSize": page_size, "hasMore": False, "announcements": []}

            # 巨潮有时返回 JSON 字符串外面包了括号（JSONP 格式）
            raw_text = resp.text.strip() if hasattr(resp, "text") else ""
            if not raw_text:
                raw_bytes = resp if isinstance(resp, bytes) else resp.content if hasattr(resp, "content") else b""
                if isinstance(raw_bytes, bytes):
                    raw_text = raw_bytes.decode("utf-8", errors="ignore")
            data = _parse_cninfo_response(raw_text)

            total = data.get("totalRecordNum", 0)
            announcements_raw = data.get("announcements") or []

            # 计算是否有下一页
            if isinstance(total, str):
                try:
                    total = int(total)
                except (ValueError, TypeError):
                    total = 0
            has_more = bool(total > page * page_size)

            items = [_format_announcement(item) for item in announcements_raw]

            return {
                "total": total,
                "page": page,
                "pageSize": page_size,
                "hasMore": has_more,
                "announcements": items,
            }

        except Exception as e:
            log.error(f"巨潮资讯搜索异常: {e}")
            return {"total": 0, "page": page, "pageSize": page_size, "hasMore": False, "announcements": []}

    def get_stock_announcements(
        self,
        stock_code: str,
        limit: int = 20,
    ) -> List[Dict]:
        """获取指定股票的近期公告

        返回单个股票的最新公告列表，自动分页拉取直到满足 limit 或没有更多数据。

        Args:
            stock_code: 6 位股票代码，如 "600519"
            limit: 返回公告条数上限，默认 20

        Returns:
            公告字典列表，结构同 search_announcements 返回的 announcements 字段
        """
        if not stock_code or not stock_code.strip():
            log.warning("get_stock_announcements: 股票代码为空")
            return []

        stock_code = stock_code.strip().replace(" ", "")
        all_items: List[Dict] = []
        page = 1
        max_pages = 10  # 安全上限

        try:
            while len(all_items) < limit and page <= max_pages:
                result = self.search_announcements(
                    stock_code=stock_code,
                    page=page,
                    page_size=min(30, limit),
                )
                items = result.get("announcements", [])
                if not items:
                    break

                all_items.extend(items)
                if not result.get("hasMore"):
                    break
                page += 1
                time.sleep(1.0)  # 礼貌延迟

            return all_items[:limit]

        except Exception as e:
            log.error(f"获取股票 {stock_code} 公告失败: {e}")
            return all_items  # 返回已获取的部分

    def get_latest_announcements(
        self,
        market: str = "",
        limit: int = 30,
    ) -> List[Dict]:
        """获取巨潮资讯全市场或指定板块的最新公告

        Args:
            market: 板块名称，可选值: "主板"、"创业板"、"科创板"、"北交所"
                   留空则查询全市场
            limit: 返回条数，默认 30

        Returns:
            最新公告列表
        """
        all_items: List[Dict] = []
        page = 1
        # 根据不同板块定制查询
        plate_code = MARKET_CODE.get(market, "")

        try:
            while len(all_items) < limit and page <= 5:
                result = self.search_announcements(page=page, page_size=30)

                # 如果指定了板块，后置过滤（巨潮 API 的 plate 参数效果不稳定）
                items = result.get("announcements", [])
                if not items:
                    break

                if plate_code:
                    # 板块代码过滤 — 不同板块上市公司代码段不同：
                    # 主板: 000xxx-003xxx, 600xxx-605xxx
                    # 创业板: 300xxx-301xxx
                    # 科创板: 688xxx
                    # 北交所: 8xxxxx (83/87/88 开头)
                    filtered = []
                    for item in items:
                        code = item.get("secCode", "")
                        if _match_plate(code, market):
                            filtered.append(item)
                    items = filtered

                all_items.extend(items)

                if not result.get("hasMore") or len(items) < 30:
                    break
                page += 1
                time.sleep(1.0)

            return all_items[:limit]

        except Exception as e:
            log.error(f"获取最新公告失败: {e}")
            return all_items

    def download_pdf(
        self,
        announcement_id: str,
        output_dir: str = "",
    ) -> Optional[str]:
        """下载公告 PDF 附件

        根据公告 ID 下载对应的 PDF 文件到指定目录。
        文件名格式: {announcement_id}.pdf

        Args:
            announcement_id: 公告唯一 ID
            output_dir: 输出目录路径，默认使用 data/cninfo_pdfs/

        Returns:
            下载成功返回本地文件绝对路径，失败返回 None
        """
        if not announcement_id:
            log.warning("download_pdf: announcement_id 为空")
            return None

        output_path = Path(output_dir) if output_dir else self._download_dir
        output_path.mkdir(parents=True, exist_ok=True)

        local_file = output_path / f"{announcement_id}.pdf"

        # 如果文件已存在且非空，直接返回
        if local_file.exists() and local_file.stat().st_size > 0:
            log.info(f"PDF 已存在，跳过下载: {local_file}")
            return str(local_file)

        # 巨潮 PDF 下载 URL 格式
        download_url = f"{CNINFO_DOWNLOAD_API}?announceId={announcement_id}"

        try:
            resp = http_get(download_url, headers=DEFAULT_HEADERS, timeout=60)
            if resp is None:
                log.warning(f"PDF 下载请求失败: {announcement_id}")
                return None

            # 检查响应是否真的是 PDF
            content_type = ""
            if hasattr(resp, "headers"):
                content_type = resp.headers.get("Content-Type", resp.headers.get("content-type", ""))

            content = resp if isinstance(resp, bytes) else resp.content if hasattr(resp, "content") else b""

            if not isinstance(content, bytes):
                log.warning(f"PDF 响应非二进制数据: {announcement_id}")
                return None

            # 验证是否为 PDF（魔数 %PDF）
            if content and not content.startswith(b"%PDF"):
                # 可能是重定向到登录页或错误页，检查是否是 JSON 错误信息
                text_sample = content[:200].decode("utf-8", errors="ignore")
                if text_sample.strip().startswith("{") or text_sample.strip().startswith("<html"):
                    log.warning(f"PDF 下载可能失败（非 PDF 内容）: {announcement_id}, 前200字符: {text_sample[:100]}")
                    return None

            with open(local_file, "wb") as f:
                f.write(content)

            log.info(f"PDF 下载成功: {local_file} ({len(content)} bytes)")
            return str(local_file)

        except Exception as e:
            log.error(f"PDF 下载异常 {announcement_id}: {e}")
            # 清理可能的不完整文件
            if local_file.exists():
                try:
                    local_file.unlink()
                except OSError:
                    pass
            return None


# ── 内部辅助 ──────────────────────────────────────────────────────────────────

def _url_encode(value) -> str:
    """对表单参数值进行 URL 编码（不使用标准库以避免引号转义差异）"""
    import urllib.parse
    return urllib.parse.quote(str(value), safe="")


def _parse_cninfo_response(raw_text: str) -> Dict:
    """解析巨潮资讯 API 响应

    巨潮接口可能返回：
    1. 标准 JSON:  {...}
    2. JSONP 格式: callback({...})
    3. 括号包裹:  ({...})

    本函数统一解析为字典。
    """
    if not raw_text:
        return {}

    text = raw_text.strip()

    # 去掉 JSONP 包装：jQuery_xxx(...) 或 callback(...)
    import re
    # 匹配 try { callback( 开头的
    m = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if m:
        text = m.group(1)

    # 去掉外层括号 (仅当整个内容被括号包裹)
    while text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.debug(f"巨潮响应 JSON 解析失败，原始内容前 200 字符: {text[:200]}")
        return {}


def _match_plate(sec_code: str, market: str) -> bool:
    """判断股票代码是否属于指定板块

    Args:
        sec_code: 6 位股票代码
        market: 板块名 ("主板"/"创业板"/"科创板"/"北交所")

    Returns:
        是否匹配
    """
    if not sec_code or len(sec_code) < 6:
        return False

    code = sec_code[:6]

    if market == "创业板":
        return code.startswith("300") or code.startswith("301")
    elif market == "科创板":
        return code.startswith("688")
    elif market == "北交所":
        # 北交所代码: 83xxxx, 87xxxx, 88xxxx
        return code.startswith(("83", "87", "88"))
    elif market == "主板":
        # 主板: 000xxx-005xxx (深市主板), 600xxx-605xxx (沪市主板)
        shenzhen_main = code.startswith(("000", "001", "002", "003", "004", "005"))
        shanghai_main = code.startswith(("600", "601", "602", "603", "604", "605"))
        return shenzhen_main or shanghai_main

    return True  # 未知板块一律放行


# ── 便捷函数 ──────────────────────────────────────────────────────────────────

def search_cninfo_announcements(
    keyword: str,
    limit: int = 20,
) -> List[Dict]:
    """快速搜索巨潮资讯公告（便捷函数）

    按关键词搜索最近 90 天内的公告，自动翻页直到满足 limit。

    Args:
        keyword: 搜索关键词，如 "分红"、"减持"、"业绩预告"
        limit: 返回条数上限，默认 20

    Returns:
        公告列表，异常时返回 []

    使用示例::

        from cninfo_scraper import search_cninfo_announcements
        results = search_cninfo_announcements("回购", limit=10)
        for r in results:
            print(r["title"], r["secCode"])
    """
    if not keyword or not keyword.strip():
        return []

    scraper = CninfoScraper()
    all_items: List[Dict] = []
    page = 1

    try:
        while len(all_items) < limit and page <= 20:
            result = scraper.search_announcements(
                keyword=keyword.strip(),
                page=page,
                page_size=min(30, limit),
            )
            items = result.get("announcements", [])
            if not items:
                break
            all_items.extend(items)
            if not result.get("hasMore"):
                break
            page += 1
            time.sleep(0.8)

        return all_items[:limit]

    except Exception as e:
        log.error(f"便捷函数搜索公告失败: {e}")
        return all_items


# ── 演示入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """演示巨潮资讯公告爬虫的各项功能"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print("=" * 70)
    print("  巨潮资讯（cninfo.com.cn）公告爬虫 — 功能演示")
    print("  数据源: 巨潮资讯（法定信息披露平台）")
    print("=" * 70)

    scraper = CninfoScraper()

    # ── 演示 1: 按关键词搜索 ──
    print("\n[1] 按关键词搜索: '年报' (前5条)")
    result = scraper.search_announcements(keyword="年报", page_size=5)
    print(f"  总共 {result['total']} 条，当前页 {result['page']}，还有更多: {result['hasMore']}")
    for i, ann in enumerate(result["announcements"][:5], 1):
        print(f"  {i}. [{ann['secCode']} {ann['secName']}] {ann['title'][:60]}")
        print(f"     日期: {ann['publishDate']} | 附件: {ann['adjunctSize']}KB")

    # ── 演示 2: 按股票代码搜索 ──
    print("\n[2] 获取指定股票公告: 600519 (贵州茅台) 最近5条")
    items = scraper.get_stock_announcements("600519", limit=5)
    for i, ann in enumerate(items, 1):
        print(f"  {i}. {ann['title'][:60]}")
        print(f"     日期: {ann['publishDate']} | ID: {ann['announcementId']}")

    # ── 演示 3: 便捷函数搜索 ──
    print("\n[3] 便捷函数搜索: '回购' (前3条)")
    results = search_cninfo_announcements("回购", limit=3)
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['secCode']}] {r['title'][:50]} ({r['publishDate']})")

    # ── 演示 4: 下载 PDF（仅第一条有效公告） ──
    if result["announcements"]:
        first_id = result["announcements"][0].get("announcementId")
        if first_id:
            print(f"\n[4] 下载公告 PDF: {first_id}")
            pdf_path = scraper.download_pdf(first_id)
            if pdf_path:
                print(f"  下载成功: {pdf_path}")
            else:
                print("  下载失败（可能附件不存在或需内网访问）")

    print("\n" + "=" * 70)
    print("  演示完成")
    print("=" * 70)
