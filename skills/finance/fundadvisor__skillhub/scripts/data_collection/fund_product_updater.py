# -*- coding: utf-8 -*-
"""
基金产品数据更新器
从akshare获取全量基金产品信息
"""
import json
import time
from datetime import datetime
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = SKILL_DIR / "data"


class FundProductUpdater:
    """基金产品数据更新器"""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR

    def collect_all_funds(self):
        """采集所有基金产品"""
        print("=" * 60)
        print("基金产品数据更新")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        try:
            import akshare as ak

            # 获取基金列表
            print("\n[1/3] 获取基金列表...")
            df = ak.fund_name_em()
            print(f"获取到 {len(df)} 只基金")

            # 转换数据格式
            funds = []
            for _, row in df.iterrows():
                fund = {
                    'fund_code': str(row.get('基金代码', '')),
                    'fund_name': str(row.get('基金简称', '')),
                    'fund_type': str(row.get('基金类型', '')),
                    'pinyin': str(row.get('拼音缩写', '')),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                funds.append(fund)

            # 按类型统计
            type_stats = {}
            for f in funds:
                ft = f['fund_type']
                type_stats[ft] = type_stats.get(ft, 0) + 1

            print("\n[2/3] 基金类型统计:")
            for ft, count in sorted(type_stats.items(), key=lambda x: -x[1])[:10]:
                print(f"  {ft}: {count}只")

            # 保存数据
            print("\n[3/3] 保存数据...")
            self.save_funds(funds)

            return funds

        except Exception as e:
            print(f"采集失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save_funds(self, funds):
        """保存基金数据（v6.1+ 新列存格式，与 fetch_all_products 一致，紧凑且可被 load_json_data 解码）"""
        output_path = self.data_dir / "fund_products.json"

        columns = ['code', 'name', 'type', 'pinyin', 'update']
        col_arrays = [
            [f.get('fund_code', '') for f in funds],
            [f.get('fund_name', '') for f in funds],
            [f.get('fund_type', '') for f in funds],
            [f.get('pinyin', '') for f in funds],
            [f.get('last_updated', '') for f in funds],
        ]
        data = {
            '_f': columns,
            'c': col_arrays,
            'm': {
                'count': len(funds),
                'source': '天天基金 fund_name_em (akshare)',
                'updated': datetime.now().strftime('%Y-%m-%d')
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

        print(f"已保存到 {output_path}")
        print(f"共 {len(funds)} 只基金")

    def update_company_products(self, funds):
        """更新公司产品关联"""
        print("\n更新公司产品关联...")

        # 加载公司数据
        company_path = self.data_dir / "fund_companies_distilled.json"
        if not company_path.exists():
            print("公司数据不存在，跳过")
            return

        with open(company_path, 'r', encoding='utf-8') as f:
            company_data = json.load(f)

        companies = company_data.get('companies', [])

        # 从基金经理数据获取公司-基金映射
        manager_path = self.data_dir / "fund_managers_distilled.json"
        if manager_path.exists():
            with open(manager_path, 'r', encoding='utf-8') as f:
                manager_data = json.load(f)

            managers = manager_data.get('managers', [])

            # 构建公司-基金映射
            company_funds = {}
            for m in managers:
                company = m.get('company_name', '')
                fund_code = m.get('current_fund_code', '')
                fund_name = m.get('current_fund_name', '')

                if company and fund_code:
                    if company not in company_funds:
                        company_funds[company] = []
                    company_funds[company].append({
                        'fund_code': fund_code,
                        'fund_name': fund_name
                    })

            # 更新公司数据
            for company in companies:
                name = company.get('name', '')
                if name in company_funds:
                    company['products'] = company_funds[name]
                    company['total_funds'] = len(company_funds[name])

            # 保存
            with open(company_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)

            print(f"已更新 {len(companies)} 家公司的产品关联")

    def generate_fund_type_summary(self, funds):
        """生成基金类型汇总"""
        type_summary = {}

        for fund in funds:
            fund_type = fund.get('fund_type', '未知')
            if fund_type not in type_summary:
                type_summary[fund_type] = {
                    'count': 0,
                    'examples': []
                }
            type_summary[fund_type]['count'] += 1
            if len(type_summary[fund_type]['examples']) < 3:
                type_summary[fund_type]['examples'].append({
                    'code': fund['fund_code'],
                    'name': fund['fund_name']
                })

        return type_summary


def main():
    """CLI入口"""
    import sys

    updater = FundProductUpdater()

    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        # 全量更新
        funds = updater.collect_all_funds()
        if funds:
            updater.update_company_products(funds)
    else:
        # 默认更新
        updater.collect_all_funds()


if __name__ == "__main__":
    main()
