"""scripts.scheduler 单元测试（v2.7.0 补全）

覆盖：
- 建表（v2.7.0 修复：此前缺 _init_db 导致 no such table）
- 任务列表空表 / 增删（无 APScheduler 时 add_job 优雅降级）
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.scheduler import SchedulerManager


class TestSchedulerManager(unittest.TestCase):
    """定时任务管理器测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.sm = SchedulerManager({"db_path": str(tmp / "test.db")})

    def test_init_creates_table(self):
        # v2.7.0 修复：此前 __init__ 从未建表，list_jobs 抛 no such table
        self.assertEqual(self.sm.list_jobs(), [])

    def test_list_jobs_empty(self):
        self.assertEqual(self.sm.list_jobs(), [])

    def test_add_job_without_scheduler_returns_false(self):
        # APScheduler 未安装时 scheduler 为 None，add_job 优雅降级返回 False
        if self.sm.scheduler is None:
            self.assertFalse(self.sm.add_job("每日报告", "daily"))

    def test_remove_job_nonexistent_returns_false(self):
        self.assertFalse(self.sm.remove_job("不存在的任务"))

    def test_remove_job_nonexistent_leaves_empty(self):
        self.sm.remove_job("不存在的任务")
        self.assertEqual(self.sm.list_jobs(), [])


if __name__ == "__main__":
    unittest.main()
