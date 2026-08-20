"""
更新调度脚本
每月第一个工作日自动更新，手动触发可选
"""
import json
import os
import sys
from datetime import datetime, date
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class UpdateScheduler:
    """更新调度器 - 每月第一个工作日执行"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.maintenance_dir = os.path.join(self.base_dir, 'scripts', 'maintenance')
        self.meta_path = os.path.join(self.base_dir, '_meta.json')
        self.load_meta()

    def load_meta(self):
        """加载元数据"""
        try:
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                self.meta = json.load(f)
        except Exception:
            self.meta = {'maintenance': {'lastUpdate': None}}

    def save_meta(self):
        """保存元数据"""
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def get_first_workday_of_month(self, year=None, month=None):
        """获取指定月份的第一个工作日"""
        if year is None:
            today = date.today()
        else:
            today = date(year, month, 1)

        first_day = date(today.year, today.month, 1)
        from dateutil.rrule import rrule, WEEKLY, MO, TU

        result = rrule(WEEKLY, dtstart=first_day, byweekday=MO)[0]
        if result.weekday() > 4:
            result = rrule(WEEKLY, dtstart=first_day, byweekday=TU)[0]

        return result.date()

    def is_first_workday(self):
        """检查今天是否是本月第一个工作日"""
        today = date.today()
        first_workday = self.get_first_workday_of_month(today.year, today.month)
        return today == first_workday

    def check_due(self):
        """检查是否需要更新"""
        today = date.today()
        first_workday = self.get_first_workday_of_month(today.year, today.month)
        return today == first_workday

    def run_update(self):
        """执行月度更新"""
        print("=" * 60)
        print("基金投顾Skill - 月度数据更新")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        updater_path = os.path.join(self.maintenance_dir, 'monthly_updater.py')
        if os.path.exists(updater_path):
            print("\n调用月度更新脚本...")
            try:
                subprocess.run([sys.executable, updater_path, '--force'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"月度更新失败: {e}")
                return False
        else:
            print(f"错误: monthly_updater.py 不存在")
            return False

        # 更新元数据
        self.meta['maintenance'] = self.meta.get('maintenance', {})
        self.meta['maintenance']['lastUpdate'] = datetime.now().strftime('%Y-%m-%d')
        self.meta['maintenance']['monthlyUpdate'] = datetime.now().strftime('%Y-%m-%d')
        self.save_meta()

        print(f"\n更新完成! 上次更新时间: {self.meta['maintenance'].get('lastUpdate')}")
        return True

    def show_status(self):
        """显示当前状态"""
        print("=" * 50)
        print("基金投顾Skill - 更新状态")
        print("=" * 50)

        today = date.today()
        first_workday = self.get_first_workday_of_month(today.year, today.month)

        print(f"\n当前日期: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})")
        print(f"本月第一个工作日: {first_workday}")

        if self.is_first_workday():
            print(f"\n⚠️  今天需要执行月度更新!")
        else:
            print(f"\n✓ 暂无强制更新任务")
            print(f"   下次更新日期: {first_workday}")

        print(f"\n上次更新时间: {self.meta.get('maintenance', {}).get('lastUpdate', '从未更新')}")

        # 检查数据文件
        print(f"\n数据库状态:")
        for filename in ['fund_companies_distilled.json', 'fund_managers_distilled.json',
                         'holdings_database.json', 'manager_views.json']:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath) // 1024
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
                print(f"  ✓ {filename} ({size}KB, {mtime})")
            else:
                print(f"  ✗ {filename} (不存在)")

        print("\n" + "=" * 50)

def main():
    scheduler = UpdateScheduler()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'status':
            scheduler.show_status()
        elif command == 'update':
            scheduler.run_update()
        else:
            print(f"未知命令: {command}")
            print("可用命令: status, update")
    else:
        scheduler.show_status()
        if scheduler.check_due():
            print(f"\n建议: 今天执行月度更新? (y/n)")
            # 实际使用时取消注释
            # answer = input()
            # if answer.lower() == 'y':
            #     scheduler.run_update()

if __name__ == "__main__":
    main()