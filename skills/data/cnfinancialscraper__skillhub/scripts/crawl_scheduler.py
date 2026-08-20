# -*- coding: utf-8 -*-
"""
定期自动爬取调度引擎 v4.0
基于 schedule 库 + 独立守护线程的定时任务引擎。

功能：
- 创建/编辑/删除定时爬取任务
- 支持频率：每N分钟、每小时、每天、每周、每月、自定义cron
- 任务持久化到 JSON，支持重启恢复
- 执行日志记录
- 任务执行后可自动触发后续动作（压缩、打包、发送）

推荐安装: pip install schedule croniter
无 schedule 时使用简易 time.sleep 循环作为 fallback。
"""

import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import traceback

# schedule 库（可选）
SCHEDULE_AVAILABLE = False
try:
    import schedule  # type: ignore
    SCHEDULE_AVAILABLE = True
except ImportError:
    pass

# croniter（可选，用于 cron 表达式验证）
CRONITER_AVAILABLE = False
try:
    from croniter import croniter  # type: ignore
    CRONITER_AVAILABLE = True
except ImportError:
    pass

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
TASKS_FILE = SKILL_DATA_DIR / "scheduled_tasks.json"
LOGS_DIR = SKILL_DATA_DIR / "scheduler_logs"
SKILL_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("crawl_scheduler")
logger.setLevel(logging.INFO)


# ==================== 数据结构 ====================

class TaskFrequency(str, Enum):
    """任务频率"""
    EVERY_MINUTE = "every_minute"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_10_MINUTES = "every_10_minutes"
    EVERY_30_MINUTES = "every_30_minutes"
    HOURLY = "hourly"
    EVERY_6_HOURS = "every_6_hours"
    EVERY_12_HOURS = "every_12_hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"  # 需要 cron 表达式


FREQUENCY_LABELS = {
    TaskFrequency.EVERY_MINUTE: "每分钟",
    TaskFrequency.EVERY_5_MINUTES: "每5分钟",
    TaskFrequency.EVERY_10_MINUTES: "每10分钟",
    TaskFrequency.EVERY_30_MINUTES: "每30分钟",
    TaskFrequency.HOURLY: "每小时",
    TaskFrequency.EVERY_6_HOURS: "每6小时",
    TaskFrequency.EVERY_12_HOURS: "每12小时",
    TaskFrequency.DAILY: "每天",
    TaskFrequency.WEEKLY: "每周",
    TaskFrequency.MONTHLY: "每月",
    TaskFrequency.CUSTOM_CRON: "自定义Cron",
}


class TaskStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class TaskAction(str, Enum):
    CRAWL_ONLY = "crawl_only"           # 仅爬取
    CRAWL_AND_COMPRESS = "crawl_and_compress"  # 爬取+压缩
    CRAWL_AND_PACKAGE = "crawl_and_package"    # 爬取+打包ZIP
    CRAWL_COMPRESS_PACKAGE = "crawl_compress_package"  # 全部
    CRAWL_SENTIMENT = "crawl_sentiment"        # 🆕 v4.3 全网舆情爬虫
    CRAWL_SENTIMENT_EXPORT = "crawl_sentiment_export"  # 🆕 舆情+导出


@dataclass
class ScheduledTask:
    """定时任务定义"""
    task_id: str
    name: str
    frequency: TaskFrequency = TaskFrequency.DAILY
    custom_cron: str = ""  # cron 表达式（当 frequency=custom_cron 时）
    target_urls: List[str] = field(default_factory=list)
    target_keywords: List[str] = field(default_factory=list)
    target_institution_types: List[str] = field(default_factory=list)
    action: TaskAction = TaskAction.CRAWL_AND_COMPRESS
    focus_dimension: str = "全面"  # 财务/风险/行业/政策/事件/全面
    output_dir: str = ""
    max_runs: int = 0  # 0=无限
    status: TaskStatus = TaskStatus.ACTIVE
    created_at: str = ""
    updated_at: str = ""
    last_run_at: str = ""
    next_run_at: str = ""
    run_count: int = 0
    error_count: int = 0
    last_error: str = ""
    # 🆕 v4.3 舆情相关
    sentiment_targets: List[str] = field(default_factory=list)
    sentiment_categories: List[str] = field(default_factory=list)
    sentiment_source_categories: List[str] = field(default_factory=list)
    sentiment_days: int = 7
    sentiment_positive_only: bool = False
    sentiment_negative_only: bool = False
    sentiment_max: int = 60
    sentiment_export_format: str = "all"  # dialog/word/excel/csv/json/all/auto

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "frequency": self.frequency.value,
            "custom_cron": self.custom_cron,
            "target_urls": self.target_urls,
            "target_keywords": self.target_keywords,
            "target_institution_types": self.target_institution_types,
            "action": self.action.value,
            "focus_dimension": self.focus_dimension,
            "output_dir": self.output_dir,
            "max_runs": self.max_runs,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "sentiment_targets": self.sentiment_targets,
            "sentiment_categories": self.sentiment_categories,
            "sentiment_source_categories": self.sentiment_source_categories,
            "sentiment_days": self.sentiment_days,
            "sentiment_positive_only": self.sentiment_positive_only,
            "sentiment_negative_only": self.sentiment_negative_only,
            "sentiment_max": self.sentiment_max,
            "sentiment_export_format": self.sentiment_export_format,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        return cls(
            task_id=data.get("task_id", ""),
            name=data.get("name", ""),
            frequency=TaskFrequency(data.get("frequency", "daily")),
            custom_cron=data.get("custom_cron", ""),
            target_urls=data.get("target_urls", []),
            target_keywords=data.get("target_keywords", []),
            target_institution_types=data.get("target_institution_types", []),
            action=TaskAction(data.get("action", "crawl_and_compress")),
            focus_dimension=data.get("focus_dimension", "全面"),
            output_dir=data.get("output_dir", ""),
            max_runs=data.get("max_runs", 0),
            status=TaskStatus(data.get("status", "active")),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_run_at=data.get("last_run_at", ""),
            next_run_at=data.get("next_run_at", ""),
            run_count=data.get("run_count", 0),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error", ""),
            sentiment_targets=data.get("sentiment_targets", []),
            sentiment_categories=data.get("sentiment_categories", []),
            sentiment_source_categories=data.get("sentiment_source_categories", []),
            sentiment_days=data.get("sentiment_days", 7),
            sentiment_positive_only=data.get("sentiment_positive_only", False),
            sentiment_negative_only=data.get("sentiment_negative_only", False),
            sentiment_max=data.get("sentiment_max", 60),
            sentiment_export_format=data.get("sentiment_export_format", "all"),
        )


# ==================== 任务执行器 ====================

class TaskExecutor:
    """任务执行器 — 在独立线程中执行爬取任务。"""

    def __init__(self):
        self._running = False
        self._current_task_id: Optional[str] = None

    def execute(self, task: ScheduledTask) -> Dict[str, Any]:
        """
        执行一个定时任务。

        返回: {"success": bool, "output_files": [], "error": str, "summary": str}
        """
        result = {
            "success": False,
            "task_id": task.task_id,
            "task_name": task.name,
            "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "output_files": [],
            "error": "",
            "summary": "",
        }

        try:
            self._current_task_id = task.task_id

            # 🆕 v4.3 舆情爬虫特殊 action
            if task.action in (TaskAction.CRAWL_SENTIMENT, TaskAction.CRAWL_SENTIMENT_EXPORT):
                sentiment_result = self._do_sentiment_crawl(task)
                if not sentiment_result:
                    result["error"] = "舆情爬取未获取到数据"
                    return result
                result["output_files"].extend(sentiment_result.get("files", []))
                result["summary"] = sentiment_result.get("summary", "舆情完成")
                result["success"] = sentiment_result.get("ok", False)
                if not result["success"]:
                    result["error"] = sentiment_result.get("error", "")
                return result

            # 1. 执行爬取
            scraped_data = self._do_crawl(task)

            if not scraped_data:
                result["error"] = "爬取未获取到有效数据"
                return result

            result["output_files"].extend(scraped_data.get("files", []))

            # 2. 根据 action 执行后续操作
            if task.action in (TaskAction.CRAWL_AND_COMPRESS, TaskAction.CRAWL_COMPRESS_PACKAGE):
                compressed = self._do_compress(scraped_data, task)
                if compressed:
                    result["output_files"].append(compressed)
                    result["summary"] = f"压缩报告已生成: {compressed}"

            if task.action in (TaskAction.CRAWL_AND_PACKAGE, TaskAction.CRAWL_COMPRESS_PACKAGE):
                packaged = self._do_package(scraped_data, task)
                if packaged:
                    result["output_files"].append(packaged)
                    result["summary"] += f"\nZIP 包已生成: {packaged}"

            if not result["summary"]:
                result["summary"] = f"爬取完成，获取 {scraped_data.get('count', 0)} 条数据"

            result["success"] = True

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
        finally:
            self._current_task_id = None

        return result

    def _do_crawl(self, task: ScheduledTask) -> Dict[str, Any]:
        """执行爬取。"""
        data: Dict[str, Any] = {"files": [], "count": 0, "items": []}

        # 按 URL 列表爬取
        if task.target_urls:
            try:
                from scraper import FinancialPageScraper
                scraper = FinancialPageScraper()
                for url in task.target_urls:
                    try:
                        content = scraper.scrape_url(url)
                        if content:
                            data["items"].append({"url": url, "content": str(content)[:2000]})
                            data["count"] += 1
                    except Exception:
                        pass
            except ImportError:
                pass

        # 按机构类型爬取
        if task.target_institution_types:
            try:
                from batch_institution_crawler import BatchInstitutionCrawler
                crawler = BatchInstitutionCrawler()
                for inst_type in task.target_institution_types:
                    results = crawler.crawl_by_type(inst_type)
                    for r in results:
                        data["items"].append({"type": inst_type, "name": r.get("name", ""),
                                             "content": str(r.get("content", ""))[:2000]})
                        data["count"] += 1
            except ImportError:
                pass

        # 按关键词搜索公告/新闻
        if task.target_keywords:
            try:
                from announcement_scraper import AnnouncementManager
                mgr = AnnouncementManager()
                for kw in task.target_keywords:
                    anns = mgr.search(kw, limit=10)
                    for a in anns:
                        data["items"].append({"keyword": kw, **a})
                        data["count"] += 1
            except ImportError:
                pass

        # 保存爬取结果到文件
        if data["items"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(SKILL_DATA_DIR / "scheduled_crawls" /
                             f"{task.task_id}_{timestamp}.json")
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            data["files"].append(output_file)

        return data

    def _do_compress(self, scraped_data: Dict[str, Any],
                     task: ScheduledTask) -> str:
        """执行内容压缩。"""
        try:
            from content_compressor import compress_content, CompressConfig

            # 合并所有爬取文本
            all_texts = []
            for item in scraped_data.get("items", []):
                if item.get("content"):
                    all_texts.append(item["content"])

            if not all_texts:
                return ""

            combined = "\n\n---\n\n".join(all_texts[:20])
            config = CompressConfig(focus=task.focus_dimension, max_pages=3)
            result = compress_content(combined, focus=task.focus_dimension)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(SKILL_DATA_DIR / "scheduled_crawls" /
                             f"{task.task_id}_compressed_{timestamp}.md")
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.structured_report)

            return output_file
        except ImportError:
            return ""
        except Exception:
            return ""

    def _do_package(self, scraped_data: Dict[str, Any],
                    task: ScheduledTask) -> str:
        """执行 ZIP 打包。"""
        try:
            from crawl_packager import CrawlPackager
            packager = CrawlPackager()

            items = scraped_data.get("items", [])
            if not items:
                return ""

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"scheduled_{task.task_id}_{timestamp}"
            zip_path = packager.package(items, zip_name=zip_name,
                                        output_dir=str(SKILL_DATA_DIR / "packages"))
            return zip_path
        except ImportError:
            return ""
        except Exception:
            return ""

    def _do_sentiment_crawl(self, task: ScheduledTask) -> Dict[str, Any]:
        """🆕 v4.3 舆情爬虫分支。结果落盘到 data/sentiment_snapshots。
        当 action=CRAWL_SENTIMENT_EXPORT 时额外按 sentiment_export_format 导出。"""
        result = {"ok": False, "files": [], "summary": "", "error": ""}
        try:
            from sentiment_crawler import crawl_sentiment  # type: ignore

            snapshot = crawl_sentiment(
                targets=task.sentiment_targets or None,
                categories=task.sentiment_categories or None,
                source_categories=task.sentiment_source_categories or None,
                days=task.sentiment_days,
                positive_only=task.sentiment_positive_only,
                negative_only=task.sentiment_negative_only,
                max_articles=task.sentiment_max,
            )
            if not snapshot or not snapshot.articles:
                result["error"] = "无结果"
                return result
            result["files"].append(getattr(snapshot, "extra_path", None) or
                                   str(SKILL_DATA_DIR / "sentiment_snapshots" / f"{snapshot.snapshot_id}.json"))

            # 导出
            if task.action == TaskAction.CRAWL_SENTIMENT_EXPORT:
                try:
                    from sentiment_exporter import export as export_sentiment  # type: ignore
                    outputs = export_sentiment(snapshot, fmt=task.sentiment_export_format)
                    for k, v in outputs.items():
                        if k != "dialog" and v:
                            result["files"].append(v)
                    dialog = outputs.get("dialog") or ""
                    # 也保存一份对话提示作为快速预览
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dl_path = SKILL_DATA_DIR / "sentiment_exports" / f"{snapshot.snapshot_id}_dialog.md"
                    dl_path.parent.mkdir(parents=True, exist_ok=True)
                    dl_path.write_text(dialog, encoding="utf-8")
                    result["files"].append(str(dl_path))
                except Exception as e:
                    logger.warning("导出舆情快照失败: %s", e)

            total = len(snapshot.articles)
            pos = snapshot.positive_count()
            neg = snapshot.negative_count()
            result["summary"] = (
                f"舆情完成 {total} 条 | 正面 {pos} | 舆情 {neg} | "
                f"快照={snapshot.snapshot_id}"
            )
            result["ok"] = True
        except ImportError as e:
            result["error"] = f"模块未安装: {e}"
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"
        return result


# ==================== 调度引擎 ====================

class CrawlScheduler:
    """
    定期自动爬取调度引擎。
    作为单例运行，在守护线程中持续调度任务。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self._tasks: Dict[str, ScheduledTask] = {}
        self._executor = TaskExecutor()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        self._load_tasks()

    # ---------- 任务管理 ----------

    def create_task(self, name: str, frequency: Union[str, TaskFrequency],
                    target_urls: Optional[List[str]] = None,
                    target_keywords: Optional[List[str]] = None,
                    target_institution_types: Optional[List[str]] = None,
                    action: Union[str, TaskAction] = TaskAction.CRAWL_AND_COMPRESS,
                    focus_dimension: str = "全面",
                    custom_cron: str = "",
                    max_runs: int = 0,
                    **kwargs) -> ScheduledTask:
        """
        创建定时任务。

        Args:
            name: 任务名称
            frequency: 频率 — 'daily'/'hourly'/'weekly'/'every_5_minutes' 等
            target_urls: 目标 URL 列表
            target_keywords: 目标关键词列表
            target_institution_types: 目标机构类型列表
            action: 执行动作
            focus_dimension: 压缩关注维度
            custom_cron: 自定义 cron 表达式
            max_runs: 最大执行次数（0=无限）

        返回: ScheduledTask
        """
        if isinstance(frequency, str):
            frequency = TaskFrequency(frequency)
        if isinstance(action, str):
            action = TaskAction(action)

        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._tasks)}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            frequency=frequency,
            custom_cron=custom_cron,
            target_urls=target_urls or [],
            target_keywords=target_keywords or [],
            target_institution_types=target_institution_types or [],
            action=action,
            focus_dimension=focus_dimension,
            output_dir=kwargs.get("output_dir", ""),
            max_runs=max_runs,
            status=TaskStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        # 计算首次执行时间
        task.next_run_at = self._calc_next_run(task)

        self._tasks[task_id] = task
        self._save_tasks()
        self._log_task_event(task_id, "created", f"任务已创建: {name}")

        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[ScheduledTask]:
        """更新任务配置。"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        for key, val in kwargs.items():
            if hasattr(task, key):
                if key == "frequency" and isinstance(val, str):
                    val = TaskFrequency(val)
                elif key == "action" and isinstance(val, str):
                    val = TaskAction(val)
                elif key == "status" and isinstance(val, str):
                    val = TaskStatus(val)
                setattr(task, key, val)

        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.next_run_at = self._calc_next_run(task)

        self._save_tasks()
        return task

    def delete_task(self, task_id: str) -> bool:
        """删除任务。"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            self._log_task_event(task_id, "deleted", "任务已删除")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务详情。"""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None) -> List[ScheduledTask]:
        """列出所有任务（可按状态筛选）。"""
        tasks = list(self._tasks.values())
        if status:
            st = TaskStatus(status) if isinstance(status, str) else status
            tasks = [t for t in tasks if t.status == st]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def pause_task(self, task_id: str) -> bool:
        """暂停任务。"""
        return self.update_task(task_id, status=TaskStatus.PAUSED) is not None

    def resume_task(self, task_id: str) -> bool:
        """恢复任务。"""
        return self.update_task(task_id, status=TaskStatus.ACTIVE) is not None

    # ---------- 调度控制 ----------

    def start(self):
        """启动调度器（守护线程）。"""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True, name="CrawlScheduler"
        )
        self._scheduler_thread.start()
        logger.info("调度器已启动")

    def stop(self):
        """停止调度器。"""
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=10)
        logger.info("调度器已停止")

    def run_once(self) -> Dict[str, Any]:
        """立即执行一次所有到期任务（不启动循环）。"""
        results = {}
        now = datetime.now()
        active_tasks = [t for t in self._tasks.values()
                       if t.status == TaskStatus.ACTIVE]

        for task in active_tasks:
            if not task.next_run_at:
                continue
            try:
                next_run = datetime.strptime(task.next_run_at, "%Y-%m-%d %H:%M:%S")
                if next_run <= now:
                    results[task.task_id] = self._execute_task(task)
            except ValueError:
                continue

        return results

    def is_running(self) -> bool:
        return self._running

    # ---------- 内部方法 ----------

    def _scheduler_loop(self):
        """调度主循环。"""
        # 使用 schedule 库
        if SCHEDULE_AVAILABLE:
            self._setup_schedule_jobs()

            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)

            schedule.clear()
        else:
            # fallback: 简易轮询
            while not self._stop_event.is_set():
                self.run_once()
                time.sleep(30)  # 每30秒检查一次

    def _setup_schedule_jobs(self):
        """使用 schedule 库注册任务。"""
        for task in self._tasks.values():
            if task.status != TaskStatus.ACTIVE:
                continue
            self._register_schedule_job(task)

    def _register_schedule_job(self, task: ScheduledTask):
        """在 schedule 库中注册单个任务。"""
        job_func = lambda t=task: self._execute_task(t)

        freq_map = {
            TaskFrequency.EVERY_MINUTE: lambda: schedule.every(1).minutes.do(job_func),
            TaskFrequency.EVERY_5_MINUTES: lambda: schedule.every(5).minutes.do(job_func),
            TaskFrequency.EVERY_10_MINUTES: lambda: schedule.every(10).minutes.do(job_func),
            TaskFrequency.EVERY_30_MINUTES: lambda: schedule.every(30).minutes.do(job_func),
            TaskFrequency.HOURLY: lambda: schedule.every(1).hours.do(job_func),
            TaskFrequency.EVERY_6_HOURS: lambda: schedule.every(6).hours.do(job_func),
            TaskFrequency.EVERY_12_HOURS: lambda: schedule.every(12).hours.do(job_func),
            TaskFrequency.DAILY: lambda: schedule.every().day.at("09:00").do(job_func),
            TaskFrequency.WEEKLY: lambda: schedule.every().monday.at("09:00").do(job_func),
            TaskFrequency.MONTHLY: lambda: schedule.every(30).days.at("09:00").do(job_func),
        }

        if task.frequency in freq_map:
            freq_map[task.frequency]()
        elif task.frequency == TaskFrequency.CUSTOM_CRON and task.custom_cron:
            # 自定义 cron 使用轮询方式
            pass

    def _execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """执行单个任务并更新状态。"""
        self._log_task_event(task.task_id, "running", f"开始执行: {task.name}")

        result = self._executor.execute(task)

        task.last_run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.run_count += 1

        if result["success"]:
            task.error_count = 0
            task.last_error = ""
            self._log_task_event(task.task_id, "completed",
                               f"执行成功: {result.get('summary', '')}")
        else:
            task.error_count += 1
            task.last_error = result.get("error", "未知错误")
            task.status = TaskStatus.ERROR if task.error_count >= 3 else task.status
            self._log_task_event(task.task_id, "error",
                               f"执行失败: {task.last_error}")

        # 检查最大执行次数
        if task.max_runs > 0 and task.run_count >= task.max_runs:
            task.status = TaskStatus.COMPLETED
            self._log_task_event(task.task_id, "completed",
                               f"已达最大执行次数 ({task.max_runs})")

        task.next_run_at = self._calc_next_run(task)
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._save_tasks()
        return result

    def _calc_next_run(self, task: ScheduledTask) -> str:
        """计算下次执行时间。"""
        now = datetime.now()

        deltas = {
            TaskFrequency.EVERY_MINUTE: timedelta(minutes=1),
            TaskFrequency.EVERY_5_MINUTES: timedelta(minutes=5),
            TaskFrequency.EVERY_10_MINUTES: timedelta(minutes=10),
            TaskFrequency.EVERY_30_MINUTES: timedelta(minutes=30),
            TaskFrequency.HOURLY: timedelta(hours=1),
            TaskFrequency.EVERY_6_HOURS: timedelta(hours=6),
            TaskFrequency.EVERY_12_HOURS: timedelta(hours=12),
            TaskFrequency.DAILY: timedelta(days=1),
            TaskFrequency.WEEKLY: timedelta(weeks=1),
            TaskFrequency.MONTHLY: timedelta(days=30),
        }

        delta = deltas.get(task.frequency, timedelta(days=1))
        next_run = now + delta

        # 对于每日/每周任务，默认在 09:00 执行
        if task.frequency in (TaskFrequency.DAILY, TaskFrequency.WEEKLY, TaskFrequency.MONTHLY):
            next_run = next_run.replace(hour=9, minute=0, second=0, microsecond=0)

        return next_run.strftime("%Y-%m-%d %H:%M:%S")

    # ---------- 持久化 ----------

    def _load_tasks(self):
        """从 JSON 文件加载任务。"""
        if TASKS_FILE.exists():
            try:
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = ScheduledTask.from_dict(task_data)
                    self._tasks[task.task_id] = task
                logger.info(f"已加载 {len(self._tasks)} 个定时任务")
            except Exception as e:
                logger.error(f"加载任务文件失败: {e}")

    def _save_tasks(self):
        """保存任务到 JSON 文件。"""
        try:
            data = {
                "version": "4.0",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "task_count": len(self._tasks),
                "tasks": [t.to_dict() for t in self._tasks.values()],
            }
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务文件失败: {e}")

    def _log_task_event(self, task_id: str, event: str, detail: str):
        """记录任务事件日志。"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{event.upper()}] task={task_id} {detail}"
        logger.info(log_entry)

        # 同时写入日志文件
        try:
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = LOGS_DIR / f"scheduler_{log_date}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception:
            pass


# ==================== 便捷函数 ====================

_scheduler = CrawlScheduler()


def get_scheduler() -> CrawlScheduler:
    """获取全局调度器实例。"""
    return _scheduler


def create_scheduled_task(name: str, frequency: str = "daily",
                          **kwargs) -> ScheduledTask:
    """快速创建定时任务。"""
    return _scheduler.create_task(name=name, frequency=frequency, **kwargs)


def list_all_tasks() -> List[ScheduledTask]:
    """列出所有定时任务。"""
    return _scheduler.list_tasks()


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python crawl_scheduler.py <命令> [参数]")
        print("命令:")
        print("  list                 — 列出所有任务")
        print("  create <名称> <频率>  — 创建任务")
        print("  delete <task_id>     — 删除任务")
        print("  pause <task_id>      — 暂停任务")
        print("  resume <task_id>     — 恢复任务")
        print("  run                  — 立即执行所有到期任务")
        print("  start                — 启动调度器守护线程")
        print("  stop                 — 停止调度器")
        print()
        print("频率: every_minute / every_5_minutes / hourly / daily / weekly / monthly")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        tasks = _scheduler.list_tasks()
        if not tasks:
            print("📋 暂无定时任务")
        else:
            print(f"📋 定时任务列表 ({len(tasks)} 个):\n")
            for t in tasks:
                freq = FREQUENCY_LABELS.get(t.frequency, t.frequency.value)
                status_icon = {"active": "🟢", "paused": "🟡",
                              "completed": "✅", "error": "🔴"}.get(t.status.value, "⚪")
                print(f"  {status_icon} [{t.task_id}] {t.name}")
                print(f"     频率: {freq} | 动作: {t.action.value} | 已执行: {t.run_count}次")
                if t.last_run_at:
                    print(f"     上次: {t.last_run_at}")
                if t.next_run_at:
                    print(f"     下次: {t.next_run_at}")
                print()

    elif cmd == "create":
        if len(sys.argv) < 4:
            print("用法: python crawl_scheduler.py create <名称> <频率> [urls...]")
            sys.exit(1)
        name = sys.argv[2]
        freq = sys.argv[3]
        urls = sys.argv[4:] if len(sys.argv) > 4 else []
        task = _scheduler.create_task(name=name, frequency=freq, target_urls=urls)
        print(f"✅ 任务已创建: {task.task_id}")

    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("用法: python crawl_scheduler.py delete <task_id>")
            sys.exit(1)
        ok = _scheduler.delete_task(sys.argv[2])
        print("✅ 已删除" if ok else "❌ 未找到该任务")

    elif cmd == "pause":
        if len(sys.argv) < 3:
            print("用法: python crawl_scheduler.py pause <task_id>")
            sys.exit(1)
        ok = _scheduler.pause_task(sys.argv[2])
        print("✅ 已暂停" if ok else "❌ 未找到该任务")

    elif cmd == "resume":
        if len(sys.argv) < 3:
            print("用法: python crawl_scheduler.py resume <task_id>")
            sys.exit(1)
        ok = _scheduler.resume_task(sys.argv[2])
        print("✅ 已恢复" if ok else "❌ 未找到该任务")

    elif cmd == "run":
        print("正在执行到期任务...")
        results = _scheduler.run_once()
        if results:
            for tid, res in results.items():
                status = "✅" if res.get("success") else "❌"
                print(f"  {status} {tid}: {res.get('summary', res.get('error', ''))}")
        else:
            print("没有到期的任务。")

    elif cmd == "start":
        _scheduler.start()
        print("✅ 调度器已启动（守护线程）")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            _scheduler.stop()
            print("\n调度器已停止")

    elif cmd == "stop":
        _scheduler.stop()
        print("✅ 调度器已停止")

    else:
        print(f"未知命令: {cmd}")
