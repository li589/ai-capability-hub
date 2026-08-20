# -*- coding: utf-8 -*-
"""
基金公司产品采集器 v1.0
采集基金公司的所有产品信息，包括代码、名称、类型、费率等
"""

import json
import re
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = SKILL_DIR / "data"


def fetch_url(url: str, headers: dict = None, timeout: int = 30) -> str:
    """通用URL抓取"""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://fund.eastmoney.com/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"


class CompanyProductCollector:
    """基金公司产品采集器"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.request_delay = 0.3

    def collect_all_companies_products(self, limit: int = 0) -> Dict[str, List]:
        """
        采集所有基金公司的产品

        Args:
            limit: 限制采集公司数量（0=不限）

        Returns:
            {company_name: [products]}
        """
        print(f"[采集开始] 采集所有基金公司产品 (限制: {limit if limit else '不限'})")

        # 读取现有公司数据
        company_file = self.data_dir / "fund_companies_distilled.json"
        if not company_file.exists():
            print(f"[错误] 基金公司数据文件不存在")
            return {}

        try:
            with open(company_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            companies = data.get('companies', [])
            print(f"[信息] 共 {len(companies)} 家公司")

            results = {}
            processed = 0

            for company in companies:
                if limit > 0 and processed >= limit:
                    break

                name = company.get('name', '')
                company_id = company.get('company_id', '')

                if not name:
                    continue

                print(f"\n[进度] 采集 {name} 的产品...")

                products = self.collect_company_products(name, company_id)
                results[name] = products

                print(f"[完成] {name}: {len(products)} 只产品")

                processed += 1
                time.sleep(self.request_delay)

                if processed % 10 == 0:
                    print(f"[进度] 已处理 {processed}/{len(companies)} 家公司")

            # 保存结果
            self._save_results(results)

            return results

        except Exception as e:
            print(f"[错误] 采集失败: {e}")
            return {}

    def collect_company_products(self, company_name: str, company_id: str = "") -> List[Dict]:
        """
        采集单家基金公司的产品

        Args:
            company_name: 公司名称
            company_id: 公司ID

        Returns:
            产品列表
        """
        products = []

        try:
            # 方法1: 通过东方财富搜索
            products = self._collect_via_search(company_name)

            # 方法2: 通过天天基金网公司页面
            if not products:
                products = self._collect_via_eastmoney(company_name)

        except Exception as e:
            print(f"[错误] 采集 {company_name} 失败: {e}")

        return products

    def _collect_via_search(self, company_name: str) -> List[Dict]:
        """通过搜索API采集"""
        products = []

        try:
            # 东方财富基金搜索API
            keyword = company_name.replace('基金', '')
            url = f"https://fund.eastmoney.com/data/rankhandler.aspx"

            # 尝试不同的搜索方式
            search_url = f"https://searchapi.eastmoney.com/api/suggest/get"
            params = {
                "input": f"{keyword}基金",
                "type": "14",  # 基金
                "token": "D43BF722C8E33BDC906FB84D85E326E8C",
                "count": "50"
            }

            full_url = f"{search_url}?{urllib.parse.urlencode(params)}"
            html = fetch_url(full_url)

            if html.startswith("Error"):
                return []

            # 解析搜索结果
            products = self._parse_search_results(html)

        except Exception:
            pass

        return products

    def _collect_via_eastmoney(self, company_name: str) -> List[Dict]:
        """通过天天基金网采集"""
        products = []

        try:
            # 天天基金基金公司页面
            url = f"https://fund.eastmoney.com/company/"

            # 搜索公司
            search_url = f"https://fund.eastmoney.com/CompanySearch.aspx?q={urllib.parse.quote(company_name)}"
            html = fetch_url(search_url)

            if html.startswith("Error"):
                return []

            # 解析公司基金
            products = self._parse_company_funds(html, company_name)

        except Exception:
            pass

        return products

    def _parse_search_results(self, html: str) -> List[Dict]:
        """解析搜索结果"""
        products = []

        try:
            # JSON格式解析
            data = json.loads(html)
            items = data.get('QuotationCodeArray', [])

            for item in items:
                products.append({
                    'fund_code': item.get('Code', ''),
                    'fund_name': item.get('Name', ''),
                    'fund_type': item.get('Type', ''),
                    'nav': item.get('NAV', ''),
                    'change_pct': item.get('ChangePercent', '')
                })

        except Exception:
            pass

        return products

    def _parse_company_funds(self, html: str, company_name: str) -> List[Dict]:
        """解析公司基金页面"""
        products = []

        try:
            # 提取基金代码和名称
            pattern = r'<a[^>]*href="/(\d{6})\.html"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)

            seen = set()
            for code, name in matches:
                if code not in seen and len(code) == 6:
                    seen.add(code)
                    products.append({
                        'fund_code': code,
                        'fund_name': name.strip()
                    })

        except Exception:
            pass

        return products

    def collect_product_detail(self, fund_code: str) -> Optional[Dict]:
        """采集产品详细信息"""
        try:
            url = f"https://fundf10.eastmoney.com/jjfl_{fund_code}.html"
            html = fetch_url(url)

            if html.startswith("Error"):
                return None

            return self._parse_product_detail(html, fund_code)

        except Exception:
            return None

    def _parse_product_detail(self, html: str, fund_code: str) -> Dict:
        """解析产品详情"""
        detail = {
            'fund_code': fund_code,
            'fund_name': '',
            'fund_type': '',
            'investment_style': '',
            'risk_level': '',
            ' inception_date': '',
            'management_fee': 0.0,
            'custodian_fee': 0.0,
            'subscription_fee': 0.0,
            'redemption_fee': 0.0,
            'min_subscription': 0,
            'scale': 0,
            'manager_name': '',
            'manager_tenure': ''
        }

        try:
            # 基金名称
            name_pattern = r'<div class="title"><h2>([^<]+)</h2></div>'
            name_match = re.search(name_pattern, html)
            if name_match:
                detail['fund_name'] = name_match.group(1).strip()

            # 基金类型
            type_pattern = r'基金类型[：:]*</td><td[^>]*>([^<]+)</td>'
            type_match = re.search(type_pattern, html)
            if type_match:
                detail['fund_type'] = type_match.group(1).strip()

            # 投资风格
            style_pattern = r'投资风格[：:]*</td><td[^>]*>([^<]+)</td>'
            style_match = re.search(style_pattern, html)
            if style_match:
                detail['investment_style'] = style_match.group(1).strip()

            # 风险等级
            risk_pattern = r'风险等级[：:]*</td><td[^>]*>([^<]+)</td>'
            risk_match = re.search(risk_pattern, html)
            if risk_match:
                detail['risk_level'] = risk_match.group(1).strip()

            # 成立日期
            date_pattern = r'成立日期[：:]*</td><td[^>]*>([^<]+)</td>'
            date_match = re.search(date_pattern, html)
            if date_match:
                detail['inception_date'] = date_match.group(1).strip()

            # 管理费率
            mg_pattern = r'管理费率[：:]*</td><td[^>]*>([^<]+)</td>'
            mg_match = re.search(mg_pattern, html)
            if mg_match:
                detail['management_fee'] = self._parse_percent(mg_match.group(1))

            # 托管费率
            cu_pattern = r'托管费率[：:]*</td><td[^>]*>([^<]+)</td>'
            cu_match = re.search(cu_pattern, html)
            if cu_match:
                detail['custodian_fee'] = self._parse_percent(cu_match.group(1))

            # 最低申购
            min_pattern = r'最低申购金额[：:]*</td><td[^>]*>(\d+)</td>'
            min_match = re.search(min_pattern, html)
            if min_match:
                detail['min_subscription'] = int(min_match.group(1))

            # 基金经理
            mgr_pattern = r'基金经理：</td><td[^>]*><a[^>]*>([^<]+)</a>'
            mgr_match = re.search(mgr_pattern, html)
            if mgr_match:
                detail['manager_name'] = mgr_match.group(1).strip()

        except Exception:
            pass

        return detail

    def _parse_percent(self, text: str) -> float:
        """解析百分比"""
        if not text:
            return 0.0
        text = text.strip().replace('%', '').replace('％', '')
        try:
            return float(text)
        except ValueError:
            match = re.search(r'[\d.]+', text)
            return float(match.group()) if match else 0.0

    def _save_results(self, results: Dict):
        """保存结果"""
        output_path = self.data_dir / "company_products.json"

        data = {
            "companies": [],
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        for company_name, products in results.items():
            data["companies"].append({
                "company_name": company_name,
                "products": products,
                "product_count": len(products)
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n[保存] 已保存到 {output_path}")

    def merge_with_existing(self):
        """合并到现有基金公司数据"""
        company_file = self.data_dir / "fund_companies_distilled.json"
        products_file = self.data_dir / "company_products.json"

        if not company_file.exists() or not products_file.exists():
            print("[错误] 数据文件不存在")
            return

        try:
            with open(company_file, 'r', encoding='utf-8') as f:
                company_data = json.load(f)

            with open(products_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)

            products_by_company = {
                c.get('company_name', ''): c.get('products', [])
                for c in products_data.get('companies', [])
            }

            # 合并
            for company in company_data.get('companies', []):
                name = company.get('name', '')
                if name in products_by_company:
                    company['products'] = products_by_company[name]
                    company['total_funds'] = len(products_by_company[name])

            # 保存
            with open(company_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)

            print(f"[合并] 已将产品数据合并到基金公司数据")

        except Exception as e:
            print(f"[错误] 合并失败: {e}")


def main():
    """CLI入口"""
    import sys

    print("=" * 60)
    print("基金公司产品采集器")
    print("=" * 60)

    collector = CompanyProductCollector()

    limit = 0
    merge = False

    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif arg == '--merge':
            merge = True

    results = collector.collect_all_companies_products(limit=limit)

    if merge and results:
        collector.merge_with_existing()

    print(f"\n[完成] 共采集 {len(results)} 家公司的产品")


if __name__ == "__main__":
    main()