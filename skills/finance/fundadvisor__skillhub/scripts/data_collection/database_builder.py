"""
数据库构建脚本
整合采集数据，构建完整的离线数据库
"""
import json
import os
from datetime import datetime

class DatabaseBuilder:
    """数据库构建器"""

    def __init__(self, data_dir='../data'):
        self.data_dir = data_dir
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def build_fund_companies(self, source_files):
        """构建基金公司数据库"""
        all_companies = []

        for filepath in source_files:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'companies' in data:
                        all_companies.extend(data['companies'])

        # 去重
        seen = {}
        unique = []
        for c in all_companies:
            cid = c.get('company_id', '')
            if cid and cid not in seen:
                seen[cid] = True
                unique.append(c)

        result = {
            'companies': unique,
            'meta': {
                'total_count': len(unique),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': ['基金业协会', '天天基金网']
            }
        }

        return result

    def build_fund_managers(self, source_files):
        """构建基金经理数据库"""
        all_managers = []

        for filepath in source_files:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'managers' in data:
                        all_managers.extend(data['managers'])

        # 去重
        seen = {}
        unique = []
        for m in all_managers:
            mid = m.get('manager_id', '')
            if mid and mid not in seen:
                seen[mid] = True
                unique.append(m)

        result = {
            'managers': unique,
            'meta': {
                'total_count': len(unique),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': ['天天基金网', '2025年报', '2026一季报']
            }
        }

        return result

    def build_holdings_database(self, fund_codes, holdings_by_quarter):
        """
        构建持仓数据库

        参数:
            fund_codes: 基金代码列表
            holdings_by_quarter: {quarter: [(code, name, weight), ...]}
        """
        holdings = []

        for quarter, records in holdings_by_quarter.items():
            for fund_code, stock_name, weight in records:
                holdings.append({
                    'fund_code': fund_code,
                    'quarter': quarter,
                    'report_date': self._quarter_to_date(quarter),
                    'stocks': [{'name': stock_name, 'weight': weight}]
                })

        result = {
            'holdings': holdings,
            'meta': {
                'total_records': len(holdings),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'quarters': list(holdings_by_quarter.keys())
            }
        }

        return result

    def _quarter_to_date(self, quarter):
        """季度转日期"""
        mapping = {
            '2024Q2': '2024-06-30',
            '2024Q4': '2024-12-31',
            '2025Q2': '2025-06-30',
            '2025Q4': '2025-12-31',
            '2026Q1': '2026-03-31'
        }
        return mapping.get(quarter, '')

    def build_style_profiles(self):
        """构建投资风格画像数据库"""
        styles = [
            {
                'style_id': 'S001',
                'name': '价值成长均衡型',
                'code': 'VALUE_BALANCED',
                'description': '兼顾价值与成长，仓位适中，追求稳健收益',
                'characteristics': {
                    'pe_range': [15, 30],
                    'position_range': [70, 85],
                    'turnover': '中等',
                    'sector_distribution': '分散'
                },
                'suitable_investors': ['稳健型', '保守型'],
                'typical_companies': []
            },
            {
                'style_id': 'S002',
                'name': '积极成长型',
                'code': 'AGGRESSIVE_GROWTH',
                'description': '高仓位高换手，专注成长赛道，追求超额收益',
                'characteristics': {
                    'pe_range': [25, 50],
                    'position_range': [85, 95],
                    'turnover': '高',
                    'sector_distribution': '集中'
                },
                'suitable_investors': ['积极型', '激进型'],
                'typical_companies': []
            },
            {
                'style_id': 'S003',
                'name': '深度价值型',
                'code': 'DEEP_VALUE',
                'description': '低估值、高分红、稳定ROE，追求安全边际',
                'characteristics': {
                    'pe_range': [5, 20],
                    'position_range': [75, 90],
                    'turnover': '低',
                    'sector_distribution': '均衡'
                },
                'suitable_investors': ['保守型'],
                'typical_companies': []
            },
            {
                'style_id': 'S004',
                'name': '灵活配置型',
                'code': 'FLEXIBLE_ALLOCATION',
                'description': '仓位灵活调整，行业配置分散，适应多变市场',
                'characteristics': {
                    'position_range': [40, 95],
                    'turnover': '中等偏高',
                    'sector_distribution': '高度分散'
                },
                'suitable_investors': ['稳健型', '积极型'],
                'typical_companies': []
            },
            {
                'style_id': 'S005',
                'name': '红利低波型',
                'code': 'DIVIDEND_LOW_VOL',
                'description': '高股息、低波动，追求稳健现金流',
                'characteristics': {
                    'pe_range': [10, 25],
                    'position_range': [80, 95],
                    'turnover': '低',
                    'dividend_yield': '>3%'
                },
                'suitable_investors': ['保守型', '稳健型'],
                'typical_companies': []
            }
        ]

        return {
            'styles': styles,
            'meta': {
                'total_styles': len(styles),
                'last_update': datetime.now().strftime('%Y-%m-%d')
            }
        }

    def save_database(self, data, filename):
        """保存数据库到文件"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据库已保存: {filepath}")

def main():
    builder = DatabaseBuilder()

    # 构建风格画像
    style_profiles = builder.build_style_profiles()
    builder.save_database(style_profiles, 'style_profiles.json')

    # 构建基金公司（如果有源数据）
    company_file = os.path.join(builder.data_dir, 'fund_companies_raw.json')
    if os.path.exists(company_file):
        companies = builder.build_fund_companies([company_file])
        builder.save_database(companies, 'fund_companies.json')

    # 构建基金经理（如果有源数据）
    manager_file = os.path.join(builder.data_dir, 'fund_managers_raw.json')
    if os.path.exists(manager_file):
        managers = builder.build_fund_managers([manager_file])
        builder.save_database(managers, 'fund_managers.json')

    print("\n数据库构建完成!")

if __name__ == "__main__":
    main()