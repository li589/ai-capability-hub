#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据更新快捷脚本
支持多种更新模式
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.maintenance.auto_updater import AutoUpdater


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("""
📊 基金数据更新工具
==================

用法:
  python update_data.py check      # 检查数据状态
  python update_data.py update     # 增量更新（推荐）
  python update_data.py full       # 全量更新
  python update_data.py auto       # 自动判断是否需要更新
  python update_data.py products   # 更新基金产品

示例:
  python update_data.py check
  python update_data.py update
  python update_data.py products
        """)
        return

    command = sys.argv[1]
    updater = AutoUpdater()

    if command == 'check':
        status = updater.get_status()
        print("\n📊 数据状态:")
        print(f"  最后更新: {status['last_update'] or '未知'}")
        print(f"  更新次数: {status['update_count']}")

        print("\n📁 数据新鲜度:")
        for key, info in status['data_freshness'].items():
            print(f"  {info['status']} {key}: {info['days_old']}天前, {info['count']}条")

        need_update, reason = status['should_update']
        print(f"\n🔄 需要更新: {'是' if need_update else '否'}")
        if need_update:
            print(f"  原因: {reason}")

    elif command == 'update':
        print("🚀 开始增量更新...")
        success = updater.run_incremental_update()
        if success:
            print("\n✅ 更新完成!")
        else:
            print("\n❌ 更新失败!")
            sys.exit(1)

    elif command == 'full':
        print("🚀 开始全量更新...")
        success = updater.run_full_update()
        if success:
            print("\n✅ 更新完成!")
        else:
            print("\n❌ 更新失败!")
            sys.exit(1)

    elif command == 'auto':
        need_update, reason = updater.should_update()
        if need_update:
            print(f"🔄 {reason}")
            print("正在执行增量更新...")
            success = updater.run_incremental_update()
            if success:
                print("\n✅ 更新完成!")
            else:
                print("\n❌ 更新失败!")
                sys.exit(1)
        else:
            print("✅ 数据新鲜度正常，无需更新")

    elif command == 'products':
        print("🚀 开始更新基金产品数据...")
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_collection'))
            from fund_product_updater import FundProductUpdater

            product_updater = FundProductUpdater()
            funds = product_updater.collect_all_funds()
            if funds:
                product_updater.update_company_products(funds)
                print("\n✅ 基金产品更新完成!")
            else:
                print("\n❌ 基金产品更新失败!")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ 更新失败: {e}")
            sys.exit(1)

    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python update_data.py' 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    main()
