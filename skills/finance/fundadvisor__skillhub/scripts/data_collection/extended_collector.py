"""
扩展数据采集脚本
采集更多经理的详细持仓（扩展到500个）
"""
import akshare as ak
import json
import time
import os

class ExtendedCollector:
    """扩展数据采集器"""

    def __init__(self, data_dir='../data'):
        self.data_dir = data_dir

    def load_managers(self):
        """加载经理数据"""
        with open(f'{self.data_dir}/fund_managers.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_managers(self, data):
        """保存经理数据"""
        with open(f'{self.data_dir}/fund_managers.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def collect_fund_holdings(self, fund_code):
        """采集基金持仓"""
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

    def collect_bond_holdings(self, fund_code):
        """采集基金债券持仓"""
        holdings = []
        try:
            df = ak.fund_portfolio_bond_hold_em(symbol=fund_code)
            for _, row in df.iterrows():
                holding = {
                    'bond_code': str(row.get('债券代码', '')),
                    'bond_name': row.get('债券名称', ''),
                    'weight': row.get('占净值比例', 0),
                    'quarter': row.get('季度', '')
                }
                holdings.append(holding)
        except Exception as e:
            pass
        return holdings

    def run_extended_collection(self, sample_size=500):
        """执行扩展采集"""
        print("=" * 60)
        print(f"扩展持仓数据采集（{sample_size}个经理）")
        print("=" * 60)

        data = self.load_managers()
        managers = data.get('managers', [])
        total = len(managers)

        print(f"共 {total} 个经理，开始采集详细持仓...")

        updated_count = 0
        holdings_records = []

        for i, manager in enumerate(managers[:sample_size]):
            fund_code = manager.get('current_fund_code', '')
            if not fund_code:
                continue

            # 采集股票持仓
            stocks = self.collect_fund_holdings(fund_code)
            manager['top_stocks'] = stocks[:10]  # 前十大重仓股

            # 采集债券持仓
            bonds = self.collect_bond_holdings(fund_code)
            manager['top_bonds'] = bonds[:10]  # 前十大重仓债

            # 记录持仓明细
            for stock in stocks[:10]:
                holdings_records.append({
                    'manager_id': manager.get('manager_id'),
                    'manager_name': manager.get('name'),
                    'company_name': manager.get('company_name'),
                    'fund_code': fund_code,
                    'fund_name': manager.get('current_fund_name'),
                    'type': 'stock',
                    'code': stock.get('stock_code'),
                    'name': stock.get('stock_name'),
                    'weight': stock.get('weight'),
                    'quarter': stock.get('quarter')
                })

            for bond in bonds[:10]:
                holdings_records.append({
                    'manager_id': manager.get('manager_id'),
                    'manager_name': manager.get('name'),
                    'company_name': manager.get('company_name'),
                    'fund_code': fund_code,
                    'fund_name': manager.get('current_fund_name'),
                    'type': 'bond',
                    'code': bond.get('bond_code'),
                    'name': bond.get('bond_name'),
                    'weight': bond.get('weight'),
                    'quarter': bond.get('quarter')
                })

            updated_count += 1

            if (i + 1) % 50 == 0:
                print(f"进度: {i+1}/{sample_size} ({updated_count}个已更新持仓)")

            time.sleep(0.3)

        # 保存更新后的经理数据
        data['managers'] = managers
        self.save_managers(data)

        # 更新持仓数据库
        holdings_data = {
            'holdings': holdings_records,
            'meta': {
                'total_records': len(holdings_records),
                'updated_managers': updated_count,
                'last_update': time.strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }

        with open(f'{self.data_dir}/holdings_database.json', 'w', encoding='utf-8') as f:
            json.dump(holdings_data, f, ensure_ascii=False, indent=2)

        print(f"\n采集完成!")
        print(f"更新经理数: {updated_count}")
        print(f"持仓记录: {len(holdings_records)}")

def main():
    collector = ExtendedCollector()
    collector.run_extended_collection(sample_size=500)

if __name__ == "__main__":
    main()