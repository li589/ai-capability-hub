"""Post-restore validation for WorkBuddy migration.

Inspired by wb-migrate v2.0.3's validate_restore feature.

Checks data integrity after import: sessions/workspace paths, projects dirs,
tasks-sessions associations, user_id consistency, skills count.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import pathmap as PM


@dataclass
class ValidationIssue:
    """A single issue found during validation."""
    severity: str       # "error" | "warning" | "info"
    category: str       # "sessions" | "workspaces" | "projects" | "tasks" | "uid" | "skills"
    count: int
    description: str
    remediation: str = ""
    samples: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report after restore."""
    passed: bool
    total_checks: int
    passed_checks: int
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)

    def to_json(self) -> dict:
        return {
            "passed": self.passed,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "count": i.count,
                    "description": i.description,
                    "remediation": i.remediation,
                    "samples": i.samples[:10],
                }
                for i in self.issues
            ],
            "summary": self.summary,
        }


def validate(wb_home: Path) -> ValidationReport:
    """Run all validation checks against the target WorkBuddy directory.

    Args:
        wb_home: Target .workbuddy directory path.
    """
    checks_total = 5
    checks_passed = 0
    report = ValidationReport(
        passed=True,
        total_checks=checks_total,
        passed_checks=0,
    )

    db_path = wb_home / "workbuddy.db"
    if not db_path.exists():
        report.add_issue(ValidationIssue(
            severity="error", category="database", count=1,
            description="workbuddy.db 不存在",
            remediation="数据库文件缺失，恢复可能失败。请检查恢复日志并重试。",
        ))
        report.passed = False
        return report

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    try:
        # --- Check 1: sessions ---------------------------------------------------
        sessions = conn.execute(
            "SELECT id, cwd, user_id FROM sessions WHERE deleted_at IS NULL"
        ).fetchall()
        report.summary["sessions"] = len(sessions)
        missing_cwd = [s for s in sessions if not s["cwd"]]
        if missing_cwd:
            report.add_issue(ValidationIssue(
                severity="warning", category="sessions", count=len(missing_cwd),
                description=f"{len(missing_cwd)} 条 session 缺少 cwd",
                remediation="缺少 cwd 的对话将无法在工作区打开。通常这是迁移前的源端数据问题，无需额外处理。",
                samples=[s["id"][:16] + "..." for s in missing_cwd[:5]],
            ))
        else:
            checks_passed += 1

        # Check workspace directories
        missing_workspaces = 0
        workspace_samples = []
        for s in sessions:
            if s["cwd"] and not Path(s["cwd"]).exists():
                missing_workspaces += 1
                if len(workspace_samples) < 5:
                    workspace_samples.append(s["cwd"])
        if missing_workspaces:
            report.add_issue(ValidationIssue(
                severity="warning", category="workspaces", count=missing_workspaces,
                description=f"{missing_workspaces} 条 session 的工作区目录不存在",
                remediation="这些对话无法在原目录打开。如果是跨机器迁移且不需要原路径，可忽略。"
                           "如需要，在目标机器上创建对应目录后对话可恢复正常。",
                samples=workspace_samples,
            ))
        else:
            checks_passed += 1

        # --- Check 2: projects ----------------------------------------------------
        projects_dir = wb_home / "projects"
        if projects_dir.is_dir():
            project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
            report.summary["projects"] = len(project_dirs)

            # Build expected project dir names from sessions
            expected = set()
            for s in sessions:
                if s["cwd"]:
                    encoded = PM.compress_workspace_path(s["cwd"])
                    expected.add(encoded)

            actual = {d.name for d in project_dirs}
            missing = expected - actual
            if missing:
                report.add_issue(ValidationIssue(
                    severity="warning", category="projects", count=len(missing),
                    description=f"{len(missing)} 条 session 缺少 project 目录",
                    remediation="project 目录可能未导入或路径映射不完整。"
                               "受影响的对话将无法打开历史记录。",
                    samples=list(missing)[:5],
                ))
            else:
                checks_passed += 1
        else:
            report.add_issue(ValidationIssue(
                severity="warning", category="projects", count=0,
                description="projects 目录不存在",
                remediation="对话历史目录不存在，可能是导出时使用了 --no-conversations 或恢复未完成。",
            ))

        # --- Check 3: tasks -------------------------------------------------------
        tasks_dir = wb_home / "tasks"
        if tasks_dir.is_dir():
            task_dirs = [d for d in tasks_dir.iterdir() if d.is_dir()]
            report.summary["tasks"] = len(task_dirs)
            session_ids = {s["id"] for s in sessions}
            orphans = [d for d in task_dirs if d.name not in session_ids]
            if orphans:
                report.add_issue(ValidationIssue(
                    severity="warning", category="tasks", count=len(orphans),
                    description=f"{len(orphans)} 个任务组无对应 session",
                    remediation="这些任务组属于已删除或未导入的 session。"
                               "如果不影响使用可以忽略，或手动清理 tasks/<session_id>/ 目录。",
                    samples=[d.name[:16] + "..." for d in orphans[:5]],
                ))
            else:
                checks_passed += 1
        else:
            # tasks dir not existing is normal for clean imports
            checks_passed += 1

        # --- Check 4: user_id consistency ----------------------------------------
        user_ids = conn.execute(
            "SELECT DISTINCT user_id FROM sessions WHERE user_id IS NOT NULL AND user_id != ''"
        ).fetchall()
        report.summary["user_ids"] = len(user_ids)
        if len(user_ids) > 1:
            report.add_issue(ValidationIssue(
                severity="warning", category="uid", count=len(user_ids),
                description=f"存在 {len(user_ids)} 个不同的 user_id",
                remediation="多个 user_id 可能导致部分对话在客户端中不可见。"
                           "使用 --uid-map 将所有源 uid 映射到目标 uid。",
                samples=[u["user_id"][:16] + "..." for u in user_ids],
            ))
        else:
            checks_passed += 1

        # --- Check 5: skills ------------------------------------------------------
        skills_dir = wb_home / "skills"
        if skills_dir.is_dir():
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
            report.summary["skills"] = len(skill_dirs)

            # Check for broken skills (no SKILL.md)
            broken = [d for d in skill_dirs if not (d / "SKILL.md").exists()]
            if broken:
                report.add_issue(ValidationIssue(
                    severity="warning", category="skills", count=len(broken),
                    description=f"{len(broken)} 个技能目录缺少 SKILL.md",
                    remediation="这些技能可能已损坏，建议卸载并重新安装。",
                    samples=[d.name for d in broken[:5]],
                ))
            else:
                checks_passed += 1
        else:
            checks_passed += 1

    finally:
        conn.close()

    report.passed_checks = checks_passed
    report.passed = len(report.issues) == 0 or all(
        i.severity != "error" for i in report.issues
    )

    return report


def print_report(report: ValidationReport):
    """Print a human-readable validation report."""
    print(f"\n{'='*60}")
    if report.passed:
        print(f"  ✓ 恢复校验通过 ({report.passed_checks}/{report.total_checks})")
    else:
        print(f"  ✗ 恢复校验未通过 ({report.passed_checks}/{report.total_checks})")

    print(f"  sessions: {report.summary.get('sessions', 0)}")
    if 'projects' in report.summary:
        print(f"  projects: {report.summary['projects']} 个目录")
    if 'tasks' in report.summary:
        print(f"  tasks: {report.summary['tasks']} 个任务组")
    if 'skills' in report.summary:
        print(f"  skills: {report.summary['skills']} 个")
    if 'user_ids' in report.summary:
        print(f"  user_id: {report.summary['user_ids']} 个")
    print(f"{'='*60}")

    if report.issues:
        print(f"\n  发现 {len(report.issues)} 个问题：")
        for i, issue in enumerate(report.issues, 1):
            tag = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue.severity, "?")
            print(f"\n  [{tag} #{i}] [{issue.category}] {issue.description}")
            if issue.remediation:
                print(f"       修复: {issue.remediation}")
            if issue.samples:
                print(f"       示例: {', '.join(issue.samples[:3])}")
    print()
