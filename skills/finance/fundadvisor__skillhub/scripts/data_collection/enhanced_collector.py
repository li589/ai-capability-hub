"""
增强数据采集脚本
补充债券持仓、基金风格、报告观点等数据
"""
import akshare as ak
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class EnhancedCollector:
    """增强数据采集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        })

    def load_managers(self):
        """加载经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_managers(self, data):
        """保存经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_fund_style(self, fund_code):
        """获取基金风格描述"""
        style = {
            'style_type': '',
            'benchmark': '',
            'investment_goal': ''
        }

        try:
            url = f"https://fund.eastmoney.com/fund/{fund_code}.html"
            response = self.session.get(url, timeout=10)
            text = response.text

            # 提取业绩比较基准
            benchmark_match = re.search(r'业绩比较基准[：:]*\s*(.+?)(?:\n|；)', text)
            if benchmark_match:
                style['benchmark'] = benchmark_match.group(1).strip()[:200]

            # 提取投资目标
            goal_match = re.search(r'投资目标[：:]*\s*(.+?)(?:\n|；)', text)
            if goal_match:
                style['investment_goal'] = goal_match.group(1).strip()[:200]

            # 判断风格类型
            benchmark = style['benchmark'].lower()
            if '指数' in benchmark or 'ETF' in benchmark:
                style['style_type'] = '指数型'
            elif '债券' in benchmark or '债' in benchmark:
                style['style_type'] = '债券型'
            elif '货币' in benchmark:
                style['style_type'] = '货币型'
            elif any(x in benchmark for x in ['股票', '沪深', '创业板', '科创']):
                style['style_type'] = '股票型'
            else:
                style['style_type'] = '混合型'

        except Exception as e:
            pass

        return style

    def collect_all_holdings(self, managers, sample_size=500):
        """采集所有持仓数据"""
        print(f"开始采集 {sample_size} 个经理的完整持仓...")

        updated = 0
        all_holdings = []

        for i, manager in enumerate(managers[:sample_size]):
            fund_code = str(manager.get('current_fund_code', ''))

            if not fund_code or len(fund_code) < 6:
                continue

            # 获取股票持仓
            try:
                df_stocks = ak.fund_portfolio_hold_em(symbol=fund_code)
                manager['top_stocks'] = []
                for _, row in df_stocks.head(10).iterrows():
                    stock = {
                        'stock_code': str(row.get('股票代码', '')),
                        'stock_name': row.get('股票名称', ''),
                        'weight': row.get('占净值比例', 0),
                        'shares': row.get('持股数', 0),
                        'market_value': row.get('持仓市值', 0),
                        'quarter': row.get('季度', '')
                    }
                    manager['top_stocks'].append(stock)

                    all_holdings.append({
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
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

            # 获取债券持仓
            try:
                df_bonds = ak.fund_portfolio_bond_hold_em(symbol=fund_code)
                manager['top_bonds'] = []
                for _, row in df_bonds.head(10).iterrows():
                    bond = {
                        'bond_code': str(row.get('债券代码', '')),
                        'bond_name': row.get('债券名称', ''),
                        'weight': row.get('占净值比例', 0),
                        'market_value': row.get('持仓市值', 0),
                        'quarter': row.get('季度', '')
                    }
                    manager['top_bonds'].append(bond)

                    all_holdings.append({
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
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

            # 获取基金风格
            style = self.get_fund_style(fund_code)
            manager['investment_style'] = style.get('style_type', '')
            manager['benchmark'] = style.get('benchmark', '')
            manager['investment_goal'] = style.get('investment_goal', '')

            updated += 1

            if (i + 1) % 50 == 0:
                print(f"进度: {i+1}/{sample_size} (已更新{updated}个)")

            time.sleep(0.3)

        return updated, all_holdings

    def collect_report_announcements(self, managers, sample_size=500):
        """采集基金公告（季报年报摘要）"""
        print(f"开始采集 {sample_size} 个经理的基金公告...")

        views_data = []
        updated = 0

        for i, manager in enumerate(managers[:sample_size]):
            fund_code = str(manager.get('current_fund_code', ''))

            if not fund_code or len(fund_code) < 6:
                continue

            try:
                # 获取最近4份报告
                df_ann = ak.fund_announcement_report_em(symbol=fund_code)

                manager['reports'] = []
                for _, row in df_ann.head(4).iterrows():
                    report = {
                        'title': row.get('公告标题', ''),
                        'date': row.get('公告日期', ''),
                        'fund_name': row.get('基金名称', '')
                    }
                    manager['reports'].append(report)

                    # 提取报告类型和日期
                    title = row.get('公告标题', '')
                    if any(x in title for x in ['季报', '半年报', '年报']):
                        views_data.append({
                            'manager_id': manager.get('manager_id'),
                            'manager_name': manager.get('name'),
                            'company': manager.get('company_name'),
                            'fund_code': fund_code,
                            'report_title': title,
                            'report_date': row.get('公告日期', '')
                        })

                updated += 1

            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

            if (i + 1) % 50 == 0:
                print(f"进度: {i+1}/{sample_size} (已更新{updated}个)")

            time.sleep(0.2)

        return updated, views_data

def main():
    collector = EnhancedCollector()

    print("=" * 60)
    print("增强数据采集")
    print("=" * 60)

    # 加载经理数据
    data = collector.load_managers()
    managers = data.get('managers', [])
    print(f"共 {len(managers)} 个基金经理")

    # 采集完整持仓
    print("\n[1/2] 采集股票和债券持仓...")
    updated1, all_holdings = collector.collect_all_holdings(managers, sample_size=1000)

    # 保存持仓数据
    holdings_file = os.path.join(DATA_DIR, 'holdings_database.json')
    with open(holdings_file, 'w', encoding='utf-8') as f:
        json.dump({
            'holdings': all_holdings,
            'meta': {
                'total_records': len(all_holdings),
                'updated_managers': updated1,
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"持仓记录: {len(all_holdings)} 条")

    # 采集报告公告
    print("\n[2/2] 采集基金公告...")
    updated2, views_data = collector.collect_report_announcements(managers, sample_size=1000)

    # 保存公告数据
    reports_file = os.path.join(DATA_DIR, 'manager_reports.json')
    with open(reports_file, 'w', encoding='utf-8') as f:
        json.dump({
            'reports': views_data,
            'meta': {
                'total_reports': len(views_data),
                'updated_managers': updated2,
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"报告记录: {len(views_data)} 条")

    # 保存更新后的经理数据
    collector.save_managers(data)

    print("\n" + "=" * 60)
    print(f"采集完成!")
    print(f"更新经理数: {updated1 + updated2}")
    print(f"持仓记录: {len(all_holdings)}")
    print(f"报告记录: {len(views_data)}")
    print("=" * 60)

if __name__ == "__main__":
    main()