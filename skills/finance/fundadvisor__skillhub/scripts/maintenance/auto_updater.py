# -*- coding: utf-8 -*-
"""
自动化数据更新脚本
支持增量更新、全量更新、定时更新
"""
import json
import os
import sys
import time
from datetime import datetime, date, timedelta
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
DATA_DIR = SKILL_DIR / "data"


def _is_placeholder_holdings(path) -> bool:
    """v9.0: 判断持仓库是否为占位空骨架（{"h":[]} 或 {"holdings":[]}）。"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return True
    if isinstance(data, dict):
        rows = data.get("h") or data.get("holdings")
        return not rows
    return not data


class AutoUpdater:
    """自动化数据更新器"""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.meta_path = self.data_dir / "update_meta.json"
        self.load_meta()

    def load_meta(self):
        """加载更新元数据"""
        try:
            if self.meta_path.exists():
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    self.meta = json.load(f)
            else:
                self.meta = {}
        except Exception:
            self.meta = {}
        # 补齐缺省键（旧格式 meta 可能没有 history 等字段）
        self.meta.setdefault('last_update', None)
        self.meta.setdefault('last_check', None)
        self.meta.setdefault('update_count', 0)
        self.meta.setdefault('history', [])

    def save_meta(self):
        """保存更新元数据"""
        try:
            with open(self.meta_path, 'w', encoding='utf-8') as f:
                json.dump(self.meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存元数据失败: {e}")

    def check_data_freshness(self):
        """检查数据新鲜度"""
        results = {
            'managers': {'status': 'unknown', 'days_old': 0, 'count': 0},
            'companies': {'status': 'unknown', 'days_old': 0, 'count': 0},
            'products': {'status': 'unknown', 'days_old': 0, 'count': 0},
            'holdings': {'status': 'unknown', 'days_old': 0, 'count': 0},
            'views': {'status': 'unknown', 'days_old': 0, 'count': 0},
            'external': {'status': 'unknown', 'days_old': 0, 'count': 0}
        }

        files = {
            'managers': 'fund_managers_distilled.json',
            'companies': 'fund_companies_distilled.json',
            'products': 'fund_products.json',
            'holdings': 'holdings_database.json',
            'views': 'manager_views.json',
            'external': 'external_data.json'
        }

        for key, filename in files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 获取更新时间(支持压缩格式 top keys: _f/c/d/m)
                    meta = data.get('meta') or data.get('m') or {}
                    last_update = (meta.get('last_update') or meta.get('updated')
                                   or meta.get('fetched_at', '')[:10] or meta.get('data_freshness'))
                    if last_update:
                        days_old = (datetime.now() - datetime.strptime(last_update, '%Y-%m-%d')).days
                        results[key]['days_old'] = days_old
                        results[key]['status'] = '✅' if days_old <= 7 else '⚠️' if days_old <= 30 else '❌'

                    # 获取数据数量(total_count/count/d 行数/列存首列长度/h 基金数)
                    col_arrays = data.get('c')
                    results[key]['count'] = (
                        meta.get('total_count', 0)
                        or meta.get('count', 0)
                        or meta.get('total_views', 0)
                        or len(data.get('d') or [])
                        or (len(col_arrays[0]) if isinstance(col_arrays, list) and col_arrays
                            and isinstance(col_arrays[0], list) else 0)
                        or len(data.get('h') or [])
                        or len(data.get('views') or [])
                    )

                except Exception as e:
                    results[key]['status'] = '❌'
                    results[key]['error'] = str(e)

        return results

    def should_update(self, threshold_days=7):
        """判断是否需要更新（v9.0: 占位/空数据视为需要重建，避免误判"新鲜"）"""
        freshness = self.check_data_freshness()
        labels = {'managers': '经理数据', 'companies': '公司数据', 'products': '产品数据'}

        for key in ('managers', 'companies', 'products'):
            info = freshness[key]
            days = info['days_old']
            count = info['count']
            # v9.0: 占位骨架 count==0 → 必须重建
            if count == 0:
                return True, f"{labels[key]}为空(占位骨架)，需要重建"
            if days > threshold_days:
                return True, f"{labels[key]}已{days}天未更新"

        return False, "数据新鲜度正常"

    def run_incremental_update(self):
        """运行增量更新"""
        print("=" * 60)
        print("增量数据更新")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        start_time = time.time()

        try:
            # 导入更新器
            sys.path.append(str(SCRIPT_DIR.parent))
            from maintenance.monthly_updater import MonthlyUpdater

            updater = MonthlyUpdater(str(SKILL_DIR))

            # 运行更新
            updater.run(force=True)

            # 更新元数据
            self.meta['last_update'] = datetime.now().isoformat()
            self.meta['update_count'] += 1
            self.meta['history'].append({
                'time': datetime.now().isoformat(),
                'type': 'incremental',
                'duration': time.time() - start_time
            })
            self.meta['history'] = self.meta['history'][-100:]  # 保留最近100条
            self.save_meta()

            elapsed = time.time() - start_time
            print(f"\n✅ 增量更新完成! 耗时: {elapsed:.1f}秒")

            return True

        except Exception as e:
            print(f"\n❌ 增量更新失败: {e}")
            return False

    def run_full_update(self):
        """运行全量更新（v9.0: 走 stdlib full_data_refresh 链路，不再依赖 akshare/pandas）"""
        print("=" * 60)
        print("全量数据更新")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        start_time = time.time()

        try:
            sys.path.append(str(SCRIPT_DIR.parent))
            from data_collection.full_data_refresh import (
                fetch_all_managers, fetch_all_products, build_companies,
                fetch_all_holdings, distill_managers)
            from data_collection.db_format import update_meta_append

            # 1) 经理 + 产品 + 公司（纯 stdlib，零 pip 依赖）
            managers = fetch_all_managers() or []
            if not managers:
                print("[ERROR] 基金经理数据获取失败，终止。")
                return False
            products = fetch_all_products() or []
            companies = build_companies(managers) or []

            # 2) 持仓库保护：占位才重采（max_funds=300 增量），真实季度全量保留
            holdings_path = DATA_DIR / 'holdings_database.json'
            holdings = None
            if _is_placeholder_holdings(holdings_path):
                holdings = fetch_all_holdings(managers, max_funds=300, delay=0.3) or []
                print(f"  已重采持仓库（占位状态，{len(holdings)} 条）")
            else:
                print("  持仓库已有数据，保留（季度全量由 q2_holdings_driver 负责）")

            # 3) 蒸馏经理（内部写 fund_managers_distilled.json）
            distill_managers(managers, holdings)

            # 3.5) v10.0: 持仓季度快照归档（跟仓历史基线；同季度不覆写）
            try:
                from data_collection.holdings_history import archive_current_holdings
                qpath = archive_current_holdings()
                if qpath:
                    print(f"  持仓历史快照已归档: {qpath}")
            except Exception as e:
                print(f"  [WARN] 持仓历史归档跳过: {e}")

            # 3.6) v10.0: 产品档案增强（投资目标/范围/费率/业绩，受 FUND_ADVISOR_PROFILE_LIMIT 控制）
            profile_limit = os.environ.get('FUND_ADVISOR_PROFILE_LIMIT', '0')
            try:
                if str(profile_limit).strip() != '0' and products:
                    from data_collection.fund_profile_collector import FundProfileCollector
                    from data_collection.db_format import write_products
                    limit = int(str(profile_limit).strip()) or 500
                    mgr_codes = sorted({str(m.get('current_fund_code', '')).zfill(6)
                                        for m in managers
                                        if str(m.get('current_fund_code', '')).isdigit()})
                    collector = FundProfileCollector()
                    enriched = collector.enrich_products(
                        [{'code': c, 'name': '', 'type': '', 'pinyin': ''}
                         for c in mgr_codes[:limit]])
                    if enriched:
                        write_products(DATA_DIR / 'fund_products.json', enriched, meta={
                            'type': 'products',
                            'updated': datetime.now().strftime('%Y-%m-%d'),
                            'source': '天天基金 fundcode_search.js + fundf10 档案',
                            'profile_enriched': len(enriched),
                        })
                        print(f"  产品档案增强完成: {len(enriched)} 只")
            except Exception as e:
                print(f"  [WARN] 产品档案增强跳过: {e}")

            # 4) 元数据追加（不覆写 history）
            elapsed = round(time.time() - start_time, 1)
            update_meta_append(self.meta_path, {
                "time": datetime.now().isoformat(),
                "type": "full_stdlib",
                "duration": elapsed,
                "results": {"managers": len(managers), "products": len(products),
                            "companies": len(companies), "holdings": len(holdings or [])},
            })
            print(f"\n✅ 全量更新完成! 耗时: {elapsed}秒")
            return True

        except Exception as e:
            print(f"\n❌ 全量更新失败: {e}")
            return False

    def get_status(self):
        """获取更新状态"""
        freshness = self.check_data_freshness()

        return {
            'last_update': self.meta.get('last_update'),
            'update_count': self.meta.get('update_count', 0),
            'data_freshness': freshness,
            'should_update': self.should_update()
        }


def main():
    """CLI入口"""
    import argparse

    parser = argparse.ArgumentParser(description='自动化数据更新脚本')
    parser.add_argument('--check', action='store_true', help='检查数据状态')
    parser.add_argument('--incremental', action='store_true', help='增量更新')
    parser.add_argument('--full', action='store_true', help='全量更新')
    parser.add_argument('--threshold', type=int, default=7, help='更新阈值（天）')

    args = parser.parse_args()

    updater = AutoUpdater()

    if args.check:
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

    elif args.incremental:
        updater.run_incremental_update()

    elif args.full:
        updater.run_full_update()

    else:
        # 默认检查是否需要更新
        need_update, reason = updater.should_update(args.threshold)
        if need_update:
            print(f"🔄 {reason}")
            print("正在执行增量更新...")
            updater.run_incremental_update()
        else:
            print("✅ 数据新鲜度正常，无需更新")


if __name__ == "__main__":
    main()
