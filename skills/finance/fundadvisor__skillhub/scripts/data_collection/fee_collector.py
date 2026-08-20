# -*- coding: utf-8 -*-
"""
基金费率采集器 v1.0
采集基金的费率信息（管理费/托管费/申购费/赎回费）
"""

import json
import re
import time
import urllib.request
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


class FeeCollector:
    """基金费率采集器"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.session_cache = {}
        self.fees = {}
        self.request_delay = 0.3

    def collect_fees_batch(self, fund_codes: List[str]) -> Dict[str, Dict]:
        """
        批量采集基金费率

        Args:
            fund_codes: 基金代码列表

        Returns:
            费率数据字典 {fund_code: fee_info}
        """
        print(f"[采集开始] 批量采集 {len(fund_codes)} 只基金的费率")

        results = {}
        for i, code in enumerate(fund_codes):
            if not code or str(code) in ('None', '', 'nan'):
                continue

            fee_info = self.collect_single_fee(code)
            if fee_info:
                results[code] = fee_info

            if (i + 1) % 50 == 0:
                print(f"[进度] 已采集 {i + 1}/{len(fund_codes)}")

            time.sleep(self.request_delay)

        print(f"[完成] 成功采集 {len(results)} 只基金的费率")

        # 保存
        self._save_fees(results)

        return results

    def collect_single_fee(self, fund_code: str) -> Optional[Dict]:
        """采集单只基金费率"""
        try:
            url = f"https://fundf10.eastmoney.com/f10/jjfl_{fund_code}.html"
            html = fetch_url(url)

            if html.startswith("Error"):
                return None

            return self._parse_fee(html, fund_code)

        except Exception as e:
            return None

    def _parse_fee(self, html: str, fund_code: str) -> Dict:
        """解析费率页面"""
        fee_info = {
            'fund_code': fund_code,
            'management_fee': 0.0,      # 管理费率
            'custodian_fee': 0.0,        # 托管费率
            'subscription_fee': 0.0,        # 申购费率
            'redemption_fee': 0.0,        # 赎回费率
            'min_subscription': 0,        # 最低申购金额
            'max_redemption_rate': 0,     # 最高赎回费率
        }

        try:
            # 管理费率
            mg_pattern = r'管理费率[：:]*</td><td[^>]*>([^<]+)</td>'
            mg_match = re.search(mg_pattern, html)
            if mg_match:
                fee_info['management_fee'] = self._parse_percent(mg_match.group(1))

            # 托管费率
            cu_pattern = r'托管费率[：:]*</td><td[^>]*>([^<]+)</td>'
            cu_match = re.search(cu_pattern, html)
            if cu_match:
                fee_info['custodian_fee'] = self._parse_percent(cu_match.group(1))

            # 申购费率（前端展示多个，通常取第一个）
            sub_pattern = r'申购费率[：:]*</td><td[^>]*>([^<]+)</td>'
            sub_match = re.search(sub_pattern, html)
            if sub_match:
                fee_info['subscription_fee'] = self._parse_percent(sub_match.group(1))

            # 赎回费率
            red_pattern = r'赎回费率[：:]*</td><td[^>]*>([^<]+)</td>'
            red_match = re.search(red_pattern, html)
            if red_match:
                fee_info['redemption_fee'] = self._parse_percent(red_match.group(1))

            # 最低申购金额
            min_pattern = r'最低申购金额[：:]*</td><td[^>]*>(\d+)</td>'
            min_match = re.search(min_pattern, html)
            if min_match:
                fee_info['min_subscription'] = int(min_match.group(1))

        except Exception:
            pass

        return fee_info

    def _parse_percent(self, text: str) -> float:
        """解析百分比文本"""
        if not text:
            return 0.0

        text = text.strip()
        text = text.replace('%', '').replace('％', '')

        try:
            return float(text)
        except ValueError:
            # 可能包含范围，取第一个值
            match = re.search(r'[\d.]+', text)
            if match:
                return float(match.group())
            return 0.0

    def collect_from_company(self, company_name: str) -> Dict[str, Dict]:
        """采集指定基金公司的所有产品费率"""
        # 读取基金公司数据
        company_file = self.data_dir / "fund_companies_distilled.json"
        if not company_file.exists():
            print(f"[错误] 基金公司数据文件不存在")
            return {}

        try:
            with open(company_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 找到公司
            company = None
            for c in data.get('companies', []):
                if company_name in c.get('name', ''):
                    company = c
                    break

            if not company:
                print(f"[错误] 未找到基金公司: {company_name}")
                return {}

            # 采集所有产品费率
            fund_codes = []
            if 'products' in company:
                fund_codes = [p.get('fund_code', '') for p in company['products']]
            elif 'fund_codes' in company:
                fund_codes = company['fund_codes']

            return self.collect_fees_batch(fund_codes)

        except Exception as e:
            print(f"[错误] 采集失败: {e}")
            return {}

    def _save_fees(self, fees: Dict):
        """保存费率数据"""
        output_path = self.data_dir / "fund_fees.json"

        data = {
            "fees": fees,
            "total_count": len(fees),
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[保存] 费率数据已保存到 {output_path}")

    def merge_with_companies(self):
        """将费率数据合并到基金公司数据"""
        fees_path = self.data_dir / "fund_fees.json"
        company_path = self.data_dir / "fund_companies_distilled.json"

        if not fees_path.exists() or not company_path.exists():
            print("[错误] 数据文件不存在")
            return

        try:
            with open(fees_path, 'r', encoding='utf-8') as f:
                fees_data = json.load(f)
            fees = fees_data.get('fees', {})

            with open(company_path, 'r', encoding='utf-8') as f:
                company_data = json.load(f)

            # 合并费率到产品
            for company in company_data.get('companies', []):
                products = company.get('products', [])
                for product in products:
                    code = product.get('fund_code', '')
                    if code in fees:
                        product['fee'] = fees[code]
                        product['fee_source'] = 'eastmoney'
                        product['fee_updated'] = datetime.now().strftime('%Y-%m-%d')

            # 保存
            with open(company_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)

            print(f"[合并] 已将 {len(fees)} 条费率数据合并到基金公司")

        except Exception as e:
            print(f"[错误] 合并失败: {e}")

    def update_existing_companies(self):
        """更新现有基金公司数据中的费率"""
        company_path = self.data_dir / "fund_companies_distilled.json"

        if not company_path.exists():
            print("[错误] 基金公司数据文件不存在")
            return

        try:
            with open(company_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取所有基金代码
            all_codes = set()
            for company in data.get('companies', []):
                products = company.get('products', [])
                for p in products:
                    code = p.get('fund_code', '')
                    if code:
                        all_codes.add(code)

            print(f"[采集] 从 {len(data.get('companies', []))} 家公司提取到 {len(all_codes)} 只基金")

            # 批量采集费率
            fees = self.collect_fees_batch(list(all_codes))

            # 合并费率
            for company in data.get('companies', []):
                products = company.get('products', [])
                for product in products:
                    code = product.get('fund_code', '')
                    if code in fees:
                        product['fee'] = fees[code]

            # 保存
            with open(company_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[完成] 已更新 {len(fees)} 只基金的费率")

        except Exception as e:
            print(f"[错误] 更新失败: {e}")


def main():
    """CLI入口"""
    import sys

    print("=" * 60)
    print("基金费率采集器")
    print("=" * 60)

    collector = FeeCollector()

    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        # 更新现有数据
        collector.update_existing_companies()
    elif len(sys.argv) > 2 and sys.argv[1] == '--company':
        # 采集指定公司
        company_name = sys.argv[2]
        collector.collect_from_company(company_name)
    else:
        print("用法:")
        print("  python fee_collector.py --update              # 更新现有基金公司数据")
        print("  python fee_collector.py --company <公司名>     # 采集指定公司费率")
        print("  python fee_collector.py --codes 001924,000001  # 批量采集指定基金")


if __name__ == "__main__":
    main()