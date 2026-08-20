# -*- coding: utf-8 -*-
"""
增强型基金经理数据更新器 v1.0
整合全量采集、费率采集、公司产品采集，统一更新数据
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = SKILL_DIR / "data"

# 导入采集器
from .manager_full_collector import ManagerFullCollector
from .fee_collector import FeeCollector
from .company_product_collector import CompanyProductCollector


class EnhancedManagerUpdater:
    """增强型基金经理数据更新器"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.manager_collector = ManagerFullCollector(data_dir)
        self.fee_collector = FeeCollector(data_dir)
        self.product_collector = CompanyProductCollector(data_dir)

    def update_all(self, options: Dict = None) -> Dict:
        """
        执行全量更新

        Args:
            options: {
                'managers': True,           # 更新基金经理
                'products': True,           # 更新公司产品
                'fees': True,                # 更新费率
                'limit': 0                   # 限制数量
            }

        Returns:
            更新结果统计
        """
        if options is None:
            options = {}

        results = {
            'start_time': datetime.now().isoformat(),
            'managers_updated': 0,
            'products_updated': 0,
            'fees_updated': 0,
            'errors': []
        }

        limit = options.get('limit', 0)

        # Step 1: 更新基金经理
        if options.get('managers', True):
            print("\n" + "=" * 60)
            print("[Step 1] 更新基金经理名单")
            print("=" * 60)

            try:
                managers = self.manager_collector.collect_all_managers(limit=limit)
                if managers:
                    self.manager_collector.merge_with_existing()
                    results['managers_updated'] = len(managers)
                    print(f"[完成] 更新 {len(managers)} 位基金经理")
                else:
                    print("[警告] 未获取到新基金经理")
            except Exception as e:
                results['errors'].append(f"基金经理更新失败: {e}")
                print(f"[错误] 基金经理更新失败: {e}")

        # Step 2: 更新公司产品
        if options.get('products', True):
            print("\n" + "=" * 60)
            print("[Step 2] 更新基金公司产品")
            print("=" * 60)

            try:
                products = self.product_collector.collect_all_companies_products(limit=limit)
                if products:
                    self.product_collector.merge_with_existing()
                    total_products = sum(len(p) for p in products.values())
                    results['products_updated'] = total_products
                    print(f"[完成] 更新 {len(products)} 家公司的 {total_products} 只产品")
                else:
                    print("[警告] 未获取到新产品")
            except Exception as e:
                results['errors'].append(f"产品更新失败: {e}")
                print(f"[错误] 产品更新失败: {e}")

        # Step 3: 更新费率
        if options.get('fees', True):
            print("\n" + "=" * 60)
            print("[Step 3] 更新基金费率")
            print("=" * 60)

            try:
                self.fee_collector.update_existing_companies()
                # 统计费率数量
                fees_file = self.data_dir / "fund_fees.json"
                if fees_file.exists():
                    with open(fees_file, 'r', encoding='utf-8') as f:
                        fees_data = json.load(f)
                    results['fees_updated'] = len(fees_data.get('fees', {}))
                print(f"[完成] 更新费率完成")
            except Exception as e:
                results['errors'].append(f"费率更新失败: {e}")
                print(f"[错误] 费率更新失败: {e}")

        results['end_time'] = datetime.now().isoformat()

        # 保存更新日志
        self._save_update_log(results)

        return results

    def update_managers_only(self, limit: int = 0) -> int:
        """仅更新基金经理"""
        managers = self.manager_collector.collect_all_managers(limit=limit)
        if managers:
            self.manager_collector.merge_with_existing()
        return len(managers)

    def update_companies_only(self, limit: int = 0) -> int:
        """仅更新公司产品"""
        products = self.product_collector.collect_all_companies_products(limit=limit)
        if products:
            self.product_collector.merge_with_existing()
            return sum(len(p) for p in products.values())
        return 0

    def update_fees_only(self) -> int:
        """仅更新费率"""
        self.fee_collector.update_existing_companies()
        fees_file = self.data_dir / "fund_fees.json"
        if fees_file.exists():
            with open(fees_file, 'r', encoding='utf-8') as f:
                fees_data = json.load(f)
            return len(fees_data.get('fees', {}))
        return 0

    def get_update_status(self) -> Dict:
        """获取更新状态"""
        status = {
            'last_update': None,
            'manager_count': 0,
            'company_count': 0,
            'fee_count': 0
        }

        # 基金经理数据
        managers_file = self.data_dir / "fund_managers_distilled.json"
        if managers_file.exists():
            try:
                with open(managers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                status['manager_count'] = len(data.get('managers', []))
                status['last_update'] = data.get('last_updated', None)
            except Exception:
                pass

        # 基金公司数据
        companies_file = self.data_dir / "fund_companies_distilled.json"
        if companies_file.exists():
            try:
                with open(companies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                status['company_count'] = len(data.get('companies', []))
            except Exception:
                pass

        # 费率数据
        fees_file = self.data_dir / "fund_fees.json"
        if fees_file.exists():
            try:
                with open(fees_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                status['fee_count'] = len(data.get('fees', {}))
            except Exception:
                pass

        return status

    def _save_update_log(self, results: Dict):
        """保存更新日志"""
        log_file = self.data_dir / "update_logs" / "enhanced_updater.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                logs = []

        logs.append(results)
        logs = logs[-100:]  # 保留最近100条

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)


def main():
    """CLI入口"""
    import sys

    print("=" * 60)
    print("增强型基金经理数据更新器")
    print("=" * 60)

    updater = EnhancedManagerUpdater()

    # 解析命令行参数
    mode = "all"
    limit = 0

    for i, arg in enumerate(sys.argv):
        if i == 0:
            continue
        if arg == '--managers-only':
            mode = "managers"
        elif arg == '--companies-only':
            mode = "companies"
        elif arg == '--fees-only':
            mode = "fees"
        elif arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    if mode == "all":
        print("\n执行全量更新（基金经理+公司产品+费率）...")
        results = updater.update_all({'limit': limit})
        print("\n" + "=" * 60)
        print("[更新完成]")
        print(f"  基金经理: {results['managers_updated']} 位")
        print(f"  产品: {results['products_updated']} 只")
        print(f"  费率: {results['fees_updated']} 条")
        if results['errors']:
            print(f"  错误: {len(results['errors'])} 条")
        print("=" * 60)

    elif mode == "managers":
        count = updater.update_managers_only(limit)
        print(f"\n[完成] 更新 {count} 位基金经理")

    elif mode == "companies":
        count = updater.update_companies_only(limit)
        print(f"\n[完成] 更新 {count} 只产品")

    elif mode == "fees":
        count = updater.update_fees_only()
        print(f"\n[完成] 更新 {count} 条费率")

    # 显示状态
    print("\n[当前状态]")
    status = updater.get_update_status()
    print(f"  基金经理: {status['manager_count']} 位")
    print(f"  基金公司: {status['company_count']} 家")
    print(f"  费率数据: {status['fee_count']} 条")
    print(f"  最后更新: {status['last_update'] or '未知'}")


if __name__ == "__main__":
    main()