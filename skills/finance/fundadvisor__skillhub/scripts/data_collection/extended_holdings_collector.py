"""
扩展持仓采集脚本
采集更多基金经理的股票和债券持仓数据
"""
import json
import time
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def _get_akshare():
    """延迟导入 akshare（可选依赖），不可用时抛出明确错误"""
    try:
        import akshare as ak
        return ak
    except ImportError:
        raise ImportError(
            "akshare 未安装，无法使用扩展持仓采集功能。\n"
            "安装方法: pip install akshare\n"
            "说明: akshare 是可选依赖，core skill 不需要它。"
        )

class ExtendedHoldingsCollector:
    """扩展持仓采集器"""

    def __init__(self):
        self.batch_size = 100
        self._ak = None  # 延迟加载

    def load_managers(self):
        """加载经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_managers(self, data):
        """保存经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def collect_holdings_for_batch(self, managers, start_idx, batch_size=100):
        """批量采集持仓"""
        updated = 0
        holdings_records = []

        end_idx = min(start_idx + batch_size, len(managers))

        for i in range(start_idx, end_idx):
            manager = managers[i]
            fund_code = str(manager.get('current_fund_code', ''))

            if not fund_code or len(fund_code) < 6:
                continue

            # 跳过已有持仓的经理
            if manager.get('top_stocks') and len(manager.get('top_stocks', [])) >= 5:
                continue

            if self._ak is None:
                self._ak = _get_akshare()

            # 采集股票持仓
            try:
                df_stocks = self._ak.fund_portfolio_hold_em(symbol=fund_code)
                if df_stocks is None or df_stocks.empty:
                    continue
                stocks = []
                for _, row in df_stocks.head(10).iterrows():
                    stock = {
                        'stock_code': str(row.get('股票代码', '')),
                        'stock_name': row.get('股票名称', ''),
                        'weight': row.get('占净值比例', 0),
                        'shares': row.get('持股数', 0),
                        'market_value': row.get('持仓市值', 0),
                        'quarter': row.get('季度', '')
                    }
                    stocks.append(stock)

                    holdings_records.append({
                        'manager_id': manager.get('manager_id'),
                        'manager_name': manager.get('name'),
                        'company': manager.get('company_name'),
                        'fund_code': fund_code,
                        'type': 'stock',
                        'code': stock['stock_code'],
                        'name': stock['stock_name'],
                        'weight': stock['weight'],
                        'quarter': stock['quarter']
                    })

                if stocks:
                    manager['top_stocks'] = stocks
                    updated += 1

            except Exception as e:
                pass

            # 采集债券持仓
            try:
                df_bonds = self._ak.fund_portfolio_bond_hold_em(symbol=fund_code)
                if df_bonds is None or df_bonds.empty:
                    continue
                bonds = []
                for _, row in df_bonds.head(10).iterrows():
                    bond = {
                        'bond_code': str(row.get('债券代码', '')),
                        'bond_name': row.get('债券名称', ''),
                        'weight': row.get('占净值比例', 0),
                        'market_value': row.get('持仓市值', 0),
                        'quarter': row.get('季度', '')
                    }
                    bonds.append(bond)

                    holdings_records.append({
                        'manager_id': manager.get('manager_id'),
                        'manager_name': manager.get('name'),
                        'company': manager.get('company_name'),
                        'fund_code': fund_code,
                        'type': 'bond',
                        'code': bond['bond_code'],
                        'name': bond['bond_name'],
                        'weight': bond['weight'],
                        'quarter': bond['quarter']
                    })

                if bonds:
                    manager['top_bonds'] = bonds

            except Exception as e:
                pass

            # 更新投资风格
            if manager.get('top_stocks') and not manager.get('investment_style'):
                # 根据持仓判断风格
                tech_keywords = ['科技', '新能源', '半导体', '芯片', '人工智能', '软件', '电子', '计算机']
                has_tech = any(any(kw in s.get('stock_name', '') for kw in tech_keywords) for s in manager['top_stocks'])
                manager['investment_style'] = '成长型' if has_tech else '均衡型'

            if (i - start_idx + 1) % 20 == 0:
                print(f"进度: {i - start_idx + 1}/{batch_size} (已更新{updated}个)")

            time.sleep(0.3)

        return updated, holdings_records

def main():
    collector = ExtendedHoldingsCollector()

    print("=" * 60)
    print("扩展持仓数据采集")
    print("目标：采集更多经理的股票和债券持仓")
    print("=" * 60)

    # 加载数据
    data = collector.load_managers()
    managers = data.get('managers', [])
    total = len(managers)

    # 统计已有持仓
    has_stocks = sum(1 for m in managers if m.get('top_stocks'))
    print(f"总数: {total}, 有持仓: {has_stocks}")

    # 计算需要采集的数量
    target_count = 2000  # 目标采集2000个经理的持仓
    start_idx = 0
    total_updated = 0
    all_holdings = []

    while start_idx < total and total_updated < target_count:
        print(f"\n采集批次: {start_idx} - {min(start_idx+100, total)}")

        updated, holdings = collector.collect_holdings_for_batch(
            managers, start_idx, batch_size=100
        )
        total_updated += updated
        all_holdings.extend(holdings)

        start_idx += 100

        print(f"本批次更新: {updated}, 累计: {total_updated}")

        # 每500个保存一次
        if total_updated % 500 == 0:
            collector.save_managers(data)
            print("已保存数据")

    # 最终保存
    collector.save_managers(data)

    # 更新持仓数据库
    holdings_file = os.path.join(DATA_DIR, 'holdings_database.json')
    with open(holdings_file, 'w', encoding='utf-8') as f:
        json.dump({
            'holdings': all_holdings,
            'meta': {
                'total_records': len(all_holdings),
                'updated_managers': total_updated,
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, f, ensure_ascii=False, indent=2)

    # 最终统计
    has_stocks_now = sum(1 for m in managers if m.get('top_stocks'))
    has_bonds_now = sum(1 for m in managers if m.get('top_bonds'))

    print("\n" + "=" * 60)
    print(f"采集完成!")
    print(f"新增持仓经理: {total_updated - has_stocks}")
    print(f"有股票持仓: {has_stocks_now}")
    print(f"有债券持仓: {has_bonds_now}")
    print(f"持仓记录: {len(all_holdings)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
