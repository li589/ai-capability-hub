# -*- coding: utf-8 -*-
"""
批量机构/公司爬虫
Batch Institution/Company Crawler

功能：
1. 批量爬取多个机构或公司信息
2. 按类别爬取整个类别的机构
3. 爬取结果保存与分析
4. 支持机构名称、类型、列表导入

支持爬取模式：
- 单个机构爬取
- 多机构批量爬取
- 按类型爬取（所有基金管理公司、所有证券公司等）
- 从文件导入机构列表批量爬取
"""

import json
import time
import re
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

# 尝试导入crawl_utils
try:
    from crawl_utils import safe_request, detect_encoding
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)


@dataclass
class CrawlResult:
    """爬取结果"""
    name: str
    code: str
    url: str
    status: str  # success/failed/not_found
    content: str = ""
    error: str = ""
    crawl_time: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "url": self.url,
            "status": self.status,
            "content": self.content[:500] if self.content else "",
            "error": self.error,
            "crawl_time": self.crawl_time
        }


@dataclass
class BatchCrawlConfig:
    """批量爬取配置"""
    max_workers: int = 5  # 并发数
    timeout: int = 30  # 超时时间(秒)
    retry: int = 2  # 重试次数
    delay: float = 1.0  # 请求间隔(秒)
    save_intermediate: bool = True  # 保存中间结果


class BatchInstitutionCrawler:
    """
    批量机构/公司爬虫

    功能：
    1. 批量爬取多个机构信息
    2. 按类型爬取整类机构
    3. 并发加速
    4. 断点续爬
    5. 结果导出
    """

    # 机构类型到URL的映射
    INSTITUTION_TYPE_URLS = {
        "基金管理公司": "https://www.amac.org.cn/fund Industry/public list/",
        "证券公司": "https://www.sac.net.cn/association/member/member_public/",
        "保险公司": "data/insurance_list.json",
        "信托公司": "data/trust_company_list.json",
        "银行": "data/institution_registry.json",
        "私募基金": "https://www.amac.org.cn/Private Equity/private fund disclosure/public list/",
        "第三方销售": "https://www.eastmoney.com",
    }

    def __init__(self, data_dir=None, config: BatchCrawlConfig = None):
        self.data_dir = data_dir or DATA_DIR
        self.config = config or BatchCrawlConfig()
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        # 结果存储
        self.results: List[CrawlResult] = []
        self.failed: List[CrawlResult] = []

        # 加载已保存的结果（用于断点续爬）
        self._load_existing_results()

    def _load_existing_results(self):
        """加载已有结果"""
        results_file = self.data_dir / "batch_crawl_results.json"
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text(encoding="utf-8"))
                for r in data.get("results", []):
                    self.results.append(CrawlResult(**r))
            except Exception as e:
                print(f"加载已有结果失败: {e}")

    def _save_results(self):
        """保存结果"""
        results_file = self.data_dir / "batch_crawl_results.json"
        output = {
            "update_time": datetime.now().isoformat(),
            "total": len(self.results),
            "success": sum(1 for r in self.results if r.status == "success"),
            "failed": sum(1 for r in self.results if r.status == "failed"),
            "results": [r.to_dict() for r in self.results]
        }
        results_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    def _crawl_single(self, name: str, code: str = "", url: str = None) -> CrawlResult:
        """爬取单个机构"""
        result = CrawlResult(
            name=name,
            code=code,
            url=url or "",
            status="not_found",
            crawl_time=datetime.now().isoformat()
        )

        if not url:
            # 尝试从名称推导URL
            url = self._guess_url(name)

        if not url:
            result.error = "无法确定URL"
            return result

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, timeout=self.config.timeout)
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.google.com"
                }
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.config.timeout, context=self.ctx) as resp:
                    raw = resp.read()

            if raw:
                if isinstance(raw, bytes):
                    content = raw.decode("utf-8", errors="replace")
                else:
                    content = raw
                result.content = content
                result.status = "success"
                result.url = url
            else:
                result.status = "failed"
                result.error = "空响应"

        except Exception as e:
            result.status = "failed"
            result.error = str(e)

        return result

    def _guess_url(self, name: str) -> Optional[str]:
        """从名称推测URL"""
        # 常见基金公司URL模式
        name_lower = name.lower()

        # 基金公司URL猜测
        fund_patterns = {
            "易方达": "https://www.efunds.com.cn",
            "华夏": "https://www.chinaamc.com",
            "广发": "https://www.gffunds.com.cn",
            "嘉实": "https://www.jsfund.cn",
            "南方": "https://www.southernfund.com",
            "博时": "https://www.bosera.com",
            "招商": "https://www.cmfchina.com",
            "工银": "https://www.icbccs.com.cn",
            "建信": "https://www.ccbfund.cn",
            "富国": "https://www.fullgoal.com.cn",
            "鹏华": "https://www.phfund.com.cn",
            "汇添富": "https://www.htffund.com",
            "中欧": "https://www.zofund.com.cn",
            "兴证全球": "https://www.xingqiu.com",
            "华安": "https://www.huaan.com.cn",
            "银华": "https://www.yhfund.com.cn",
            "天弘": "https://www.thfund.com.cn",
            "平安": "https://fund.pingan.com",
        }

        for keyword, url in fund_patterns.items():
            if keyword in name:
                return url

        # 通用搜索URL
        if "基金" in name:
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(name)}"
            return search_url

        return None

    def crawl_by_names(self, names: List[Dict], progress_callback: Callable = None) -> List[CrawlResult]:
        """
        按名称批量爬取（并发执行）

        Args:
            names: 机构名称列表 [{"name": "xxx", "code": "xxx", "url": "xxx"}]
            progress_callback: 进度回调函数

        Returns:
            List[CrawlResult]: 爬取结果列表
        """
        print(f"[批量爬虫] 开始爬取 {len(names)} 个机构（并发数: {self.config.max_workers}）...")

        completed_count = 0

        def crawl_single_item(item):
            """爬取单个机构"""
            name = item.get("name", "")
            code = item.get("code", "")
            url = item.get("url")
            result = self._crawl_single(name, code, url)
            return result

        # 使用线程池并发爬取
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任务
            future_to_item = {
                executor.submit(crawl_single_item, item): item
                for item in names
            }

            # 收集结果
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                name = item.get("name", "")

                try:
                    result = future.result(timeout=self.config.timeout + 10)
                    self.results.append(result)

                    if result.status == "failed":
                        self.failed.append(result)
                        print(f"  ❌ {name}: {result.error}")
                    else:
                        print(f"  ✅ {name}")
                except Exception as e:
                    error_result = CrawlResult(
                        name=name,
                        code=item.get("code", ""),
                        url=item.get("url", ""),
                        status="failed",
                        error=f"执行异常: {str(e)}",
                        crawl_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    self.results.append(error_result)
                    self.failed.append(error_result)
                    print(f"  ❌ {name}: {str(e)}")

                completed_count += 1

                # 保存中间结果
                if self.config.save_intermediate and completed_count % 10 == 0:
                    self._save_results()
                    print(f"  已保存 {completed_count} 条中间结果")

                # 进度回调
                if progress_callback:
                    progress_callback(completed_count, len(names))

        self._save_results()
        success_count = len(self.results) - len(self.failed)
        print(f"[批量爬虫] 完成! 成功: {success_count}, 失败: {len(self.failed)}")

        return self.results

    def crawl_by_type(self, institution_type: str, progress_callback: Callable = None) -> List[CrawlResult]:
        """
        按类型爬取整类机构

        Args:
            institution_type: 机构类型（如"基金管理公司"、"证券公司"）
            progress_callback: 进度回调

        Returns:
            List[CrawlResult]: 爬取结果
        """
        # 从full_institution_crawler获取机构列表
        from full_institution_crawler import FullInstitutionCrawler

        full_crawler = FullInstitutionCrawler(data_dir=self.data_dir)

        # 根据类型获取对应方法
        type_method_map = {
            "基金管理公司": full_crawler.crawl_amac_fund_companies,
            "证券公司": full_crawler.crawl_sac_securities,
            "保险公司": full_crawler.crawl_cbirc_insurance,
            "信托公司": full_crawler.crawl_cbirc_banks,
            "银行": full_crawler.crawl_cbirc_banks,
            "私募基金": full_crawler.crawl_amac_private_funds,
            "第三方销售": full_crawler.crawl_third_party_sales,
            "外资金融机构": full_crawler.crawl_foreign_institutions,
        }

        method = type_method_map.get(institution_type)
        if not method:
            print(f"[批量爬虫] 未知类型: {institution_type}")
            return []

        institutions = method()
        print(f"[批量爬虫] 类型'{institution_type}'共有 {len(institutions)} 个机构")

        # 转换为名称列表
        names = [
            {"name": inst.get("name", ""), "code": inst.get("code", ""), "url": inst.get("home")}
            for inst in institutions
        ]

        return self.crawl_by_names(names, progress_callback)

    def crawl_all_types(self, progress_callback: Callable = None) -> Dict[str, List[CrawlResult]]:
        """
        爬取所有类型的机构

        Returns:
            Dict[str, List[CrawlResult]]: 按类型分类的结果
        """
        results_by_type = {}

        for inst_type in self.INSTITUTION_TYPE_URLS.keys():
            print(f"\n{'='*60}")
            print(f"开始爬取类型: {inst_type}")
            print('='*60)

            results = self.crawl_by_type(inst_type, progress_callback)
            results_by_type[inst_type] = results

            # 保存每种类型的结果
            type_file = self.data_dir / f"batch_{inst_type}_results.json"
            output = {
                "type": inst_type,
                "count": len(results),
                "success": sum(1 for r in results if r.status == "success"),
                "update_time": datetime.now().isoformat(),
                "results": [r.to_dict() for r in results]
            }
            type_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

        return results_by_type

    def export_results(self, output_file: str = None, format: str = "json") -> str:
        """
        导出结果

        Args:
            output_file: 输出文件路径
            format: 导出格式（json/txt/csv）

        Returns:
            str: 导出文件路径
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.data_dir / f"batch_crawl_export_{timestamp}.{format}")

        if format == "json":
            self._export_json(output_file)
        elif format == "txt":
            self._export_txt(output_file)
        elif format == "csv":
            self._export_csv(output_file)

        return output_file

    def _export_json(self, output_file: str):
        """导出JSON格式"""
        output = {
            "summary": {
                "total": len(self.results),
                "success": sum(1 for r in self.results if r.status == "success"),
                "failed": len(self.failed),
                "export_time": datetime.now().isoformat()
            },
            "results": [r.to_dict() for r in self.results]
        }
        Path(output_file).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    def _export_txt(self, output_file: str):
        """导出TXT格式"""
        lines = ["=" * 60, "批量爬取结果", "=" * 60, ""]
        lines.append(f"总数量: {len(self.results)}")
        lines.append(f"成功: {sum(1 for r in self.results if r.status == 'success')}")
        lines.append(f"失败: {len(self.failed)}")
        lines.append("")

        for r in self.results:
            lines.append(f"{r.name} ({r.code})")
            lines.append(f"  URL: {r.url}")
            lines.append(f"  状态: {r.status}")
            if r.error:
                lines.append(f"  错误: {r.error}")
            lines.append("")

        Path(output_file).write_text("\n".join(lines), encoding="utf-8")

    def _export_csv(self, output_file: str):
        """导出CSV格式"""
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["名称", "代码", "URL", "状态", "错误"])
            for r in self.results:
                writer.writerow([r.name, r.code, r.url, r.status, r.error])

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total": len(self.results),
            "success": sum(1 for r in self.results if r.status == "success"),
            "failed": len(self.failed),
            "not_found": sum(1 for r in self.results if r.status == "not_found"),
            "by_type": self._get_by_type_summary()
        }

    def _get_by_type_summary(self) -> Dict:
        """按类型统计"""
        summary = {}
        for r in self.results:
            key = r.name[:2] if len(r.name) >= 2 else r.name
            if key not in summary:
                summary[key] = {"total": 0, "success": 0}
            summary[key]["total"] += 1
            if r.status == "success":
                summary[key]["success"] += 1
        return summary


class StockBatchCrawler:
    """
    股票批量爬虫

    用于批量爬取多个上市公司的信息
    """

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.results = []

    def crawl_by_codes(self, codes: List[str], progress_callback: Callable = None) -> List[Dict]:
        """
        按股票代码批量爬取

        Args:
            codes: 股票代码列表
            progress_callback: 进度回调

        Returns:
            List[Dict]: 爬取结果
        """
        print(f"[股票批量爬虫] 开始爬取 {len(codes)} 只股票...")

        for i, code in enumerate(codes):
            code = str(code).zfill(6)
            print(f"  [{i+1}/{len(codes)}] 爬取: {code}")

            result = self._crawl_stock(code)
            self.results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(codes))

            time.sleep(0.5)  # 避免请求过快

        return self.results

    def _crawl_stock(self, code: str) -> Dict:
        """爬取单只股票信息"""
        result = {
            "code": code,
            "name": "",
            "status": "pending",
            "data": {}
        }

        try:
            # 尝试从东方财富获取股票信息
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={'1' if code.startswith(('6', '5', '9')) else '0'}.{code}&fields=f57,f58,f43,f44,f45,f46,f47,f48,f50,f170"

            if HAS_CRAWL_UTILS:
                raw = safe_request(url, timeout=10)
            else:
                req = urllib.request.Request(url)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    raw = resp.read()

            if raw:
                import json
                data = json.loads(raw)
                stock_data = data.get("data", {})

                result["name"] = stock_data.get("f58", "")
                result["status"] = "success"
                result["data"] = {
                    "price": stock_data.get("f43", 0),
                    "change_pct": stock_data.get("f170", 0),
                    "open": stock_data.get("f46", 0),  # v4.4.0 修复：f46 是开盘价，之前错误使用 f43
                    "high": stock_data.get("f44", 0),
                    "low": stock_data.get("f45", 0),
                    "volume": stock_data.get("f48", 0),
                }

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def export_to_json(self, output_file: str = None) -> str:
        """导出结果到JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.data_dir / f"stock_batch_results_{timestamp}.json")

        output = {
            "total": len(self.results),
            "success": sum(1 for r in self.results if r["status"] == "success"),
            "update_time": datetime.now().isoformat(),
            "results": self.results
        }

        Path(output_file).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[股票批量爬虫] 已导出到: {output_file}")

        return output_file


def main():
    """测试"""
    import sys
    sys.path.insert(0, str(SCRIPT_DIR.parent))

    print("=" * 60)
    print("批量机构/公司爬虫 - 测试")
    print("=" * 60)

    crawler = BatchInstitutionCrawler()

    # 测试按类型爬取
    print("\n1. 测试爬取基金管理公司...")
    institutions = [
        {"name": "易方达基金", "code": "EF"},
        {"name": "华夏基金", "code": "HX"},
        {"name": "广发基金", "code": "GF"},
    ]

    results = crawler.crawl_by_names(institutions)
    print(f"爬取完成: {len(results)} 条")

    # 统计
    stats = crawler.get_statistics()
    print(f"\n统计:")
    print(f"  总数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")


if __name__ == "__main__":
    main()