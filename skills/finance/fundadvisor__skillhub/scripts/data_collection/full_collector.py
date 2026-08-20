"""
全量基金数据采集脚本
从天天基金网和基金业协会获取完整的基金经理和基金公司数据
"""
import akshare as ak
import json
import time
import pandas as pd
from datetime import datetime
import os

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class FullDataCollector:
    """全量数据采集器"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def collect_all_managers(self):
        """采集所有基金经理数据"""
        print("正在采集基金经理列表...")

        managers = []

        try:
            df = ak.fund_manager_em()
            print(f"获取到 {len(df)} 条基金经理记录")

            # 转换数据格式
            for _, row in df.iterrows():
                manager = {
                    'manager_id': str(row.get('序号', '')),
                    'name': row.get('姓名', ''),
                    'company_id': self._generate_company_id(row.get('所属公司', '')),
                    'company_name': row.get('所属公司', ''),
                    'current_fund_code': str(row.get('现任基金代码', '')),
                    'current_fund_name': row.get('现任基金', ''),
                    'tenure_days': row.get('累计从业时间', 0),
                    'total_scale': row.get('现任基金资产总规模', 0),
                    'best_return': row.get('现任基金最佳回报', ''),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                managers.append(manager)

            print(f"成功转换 {len(managers)} 条经理记录")

        except Exception as e:
            print(f"采集基金经理数据失败: {e}")

        return managers

    def _generate_company_id(self, name):
        """生成公司ID"""
        import hashlib
        return f"C{hashlib.md5(name.encode()).hexdigest()[:6].upper()}"

    def collect_fund_holdings(self, fund_code):
        """采集单只基金的持仓"""
        holdings = []

        try:
            df = ak.fund_portfolio_hold_em(symbol=fund_code)
            for _, row in df.iterrows():
                holding = {
                    'stock_code': str(row.get('股票代码', '')),
                    'stock_name': row.get('股票名称', ''),
                    'weight': row.get('占净值比例', 0),
                    'shares': row.get('持股数', 0),
                    'market_value': row.get('持仓市值', 0),
                    'quarter': row.get('季度', '')
                }
                holdings.append(holding)
        except Exception as e:
            pass

        return holdings

    def collect_companies(self, managers):
        """从经理数据提取基金公司"""
        print("正在提取基金公司数据...")

        companies = []
        seen = {}

        for m in managers:
            company_name = m.get('company_name', '')
            if company_name and company_name not in seen:
                seen[company_name] = True
                company = {
                    'company_id': m.get('company_id'),
                    'name': company_name,
                    'type': '公募',
                    'manager_count': sum(1 for x in managers if x.get('company_name') == company_name),
                    'total_scale': sum(x.get('total_scale', 0) for x in managers if x.get('company_name') == company_name),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                companies.append(company)

        print(f"获取到 {len(companies)} 家基金公司")
        return companies

    def save_data(self, data, filename):
        """保存数据到文件"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存: {filepath}")

    def run_full_collection(self):
        """执行全量数据采集"""
        print("=" * 60)
        print("基金数据全量采集")
        print(f"数据目录: {self.data_dir}")
        print("=" * 60)

        start_time = time.time()

        # 1. 采集所有基金经理基础信息
        print("\n[1/4] 采集基金经理基础信息...")
        managers = self.collect_all_managers()

        self.save_data({
            'managers': managers,
            'meta': {
                'total_count': len(managers),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, 'fund_managers.json')
        print(f"基金经理数据: {len(managers)} 条")

        # 2. 采集基金公司数据
        print("\n[2/4] 采集基金公司数据...")
        companies = self.collect_companies(managers)
        self.save_data({
            'companies': companies,
            'meta': {
                'total_count': len(companies),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, 'fund_companies.json')
        print(f"基金公司数据: {len(companies)} 条")

        # 3. 采集经理详细持仓
        print("\n[3/4] 采集经理详细持仓（前300个）...")
        updated_count = 0
        holdings_records = []

        for i, manager in enumerate(managers[:300]):
            fund_code = manager.get('current_fund_code', '')
            if not fund_code:
                continue

            # 获取持仓
            holdings = self.collect_fund_holdings(fund_code)
            manager['top_stocks'] = holdings[:10]

            for stock in holdings[:10]:
                holdings_records.append({
                    'manager_id': manager.get('manager_id'),
                    'manager_name': manager.get('name'),
                    'company_name': manager.get('company_name'),
                    'fund_code': fund_code,
                    'stock_code': stock.get('stock_code'),
                    'stock_name': stock.get('stock_name'),
                    'weight': stock.get('weight'),
                    'quarter': stock.get('quarter')
                })

            updated_count += 1

            if (i + 1) % 50 == 0:
                print(f"进度: {i+1}/300 (已更新{updated_count}个)")

            time.sleep(0.3)

        # 保存更新后的经理数据
        self.save_data({
            'managers': managers,
            'meta': {
                'total_count': len(managers),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, 'fund_managers.json')

        # 4. 保存持仓数据库
        print("\n[4/4] 生成持仓数据库...")
        self.save_data({
            'holdings': holdings_records,
            'meta': {
                'total_records': len(holdings_records),
                'updated_managers': updated_count,
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, 'holdings_database.json')
        print(f"持仓记录: {len(holdings_records)} 条")

        elapsed = time.time() - start_time
        print(f"\n采集完成! 耗时: {elapsed:.1f}秒")

def main():
    collector = FullDataCollector()
    collector.run_full_collection()

if __name__ == "__main__":
    main()