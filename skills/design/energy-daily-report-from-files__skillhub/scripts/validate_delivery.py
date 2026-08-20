#!/usr/bin/env python3
"""Validate the minimum delivery contract of a generated energy daily-report system."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sqlite3
import sys
from pathlib import Path

REQUIRED_PATHS = [
    "app.py", "src", "templates", "static", "data/paperless_business.db",
    "config/business-system-blueprint.json", "mapping/source-file-mapping.json",
    "mapping/import-report.md", "mapping/assumptions.md", ".build-state.json", "tests",
    "requirements.txt", "config/python-runtime.json", "scripts/install_python_windows.ps1",
    "scripts/install_python_macos.sh", "scripts/dependency_plan.py", "scripts/install_dependencies.py",
    "scripts/prepare_offline_dependencies.py", "scripts/preflight_check.py", "scripts/validate_business_blueprint.py",
    "start_windows.bat", "stop_windows.bat", "start_macos.command", "stop_macos.command", "start_macos.sh", "stop_macos.sh", "README_运行说明.md",
    "ELECTRONIC_FILE_ANALYSIS_REPORT.md", "TEST_REPORT.md", "ACCEPTANCE_EVIDENCE.json", "VERSION", "FILES_SHA256.txt",
    "COPYRIGHT.md", "PROPRIETARY_LICENSE.md", "THIRD_PARTY_NOTICES.md", "INTELLECTUAL_PROPERTY.json",
]
REQUIRED_TABLES = {
    "schema_migrations", "permissions", "roles", "role_permissions", "users", "user_permissions",
    "business_entities", "business_records", "record_versions", "workflow_definitions", "workflow_instances",
    "workflow_actions", "approval_records", "import_batches", "import_errors", "integration_endpoints",
    "integration_runs", "audit_log", "system_settings", "backups",
}
REQUIRED_EVIDENCE = {
    "database_init", "crud_roundtrip", "business_key_uniqueness", "data_scope_isolation",
    "permissions_403", "optimistic_lock_409", "workflow_transition", "approval_return",
    "audit_before_after", "dashboard_metrics", "responsive_layout", "file_import_roundtrip",
    "import_idempotency", "export_roundtrip", "integration_not_configured", "startup_preflight",
    "build_resume", "database_integrity", "backup_restore", "security_controls",
    "chinese_locale_utf8_gb18030", "offline_dependency_install", "office_wps_export_roundtrip",
    "personal_data_masking", "currency_decimal_rounding", "business_calendar_boundary",
    "external_resources_disabled", "value_added_reports_truthful",
}
FORBIDDEN_PLACEHOLDERS = ["todo: implement", "pass  # todo", "notimplementederror", "lorem ipsum", "伪代码", "此处省略"]


def validate(project: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (project / rel).exists():
            errors.append(f"缺少交付项: {rel}")

    py_files = [path for path in project.rglob("*.py") if not any(part in {".venv", "__pycache__"} for part in path.parts)]
    for py_file in py_files:
        try:
            ast.parse(py_file.read_text(encoding="utf-8-sig"), filename=str(py_file))
        except Exception as exc:
            errors.append(f"Python 源码有语法错误：{py_file.relative_to(project)}，请检查代码是否完整")
    source_text = "\n".join(path.read_text(encoding="utf-8-sig", errors="replace") for path in py_files).casefold()
    for marker in FORBIDDEN_PLACEHOLDERS:
        if marker in source_text:
            errors.append(f"源码包含空壳或占位内容: {marker}")
    if not py_files or len(source_text) < 1500:
        errors.append("后端源码规模不足，疑似空壳或仅静态页面")

    standalone = project / "standalone/energy_daily_report.py"
    if standalone.is_file():
        standalone_text = standalone.read_text(encoding="utf-8-sig", errors="replace")
        required_tokens = [
            "class EnergyRepository", "class EnergyDailyApp", "sqlite3", "tkinter",
            "def import_file", "def export_file", "def run_self_test", "--self-test",
            "Decimal", "energy_daily_records", "PRAGMA integrity_check",
        ]
        for token in required_tokens:
            if token not in standalone_text:
                errors.append(f"独立 PY 能源日报缺少完整能力标识: {token}")
        if len(standalone_text.strip()) < 2000:
            errors.append("standalone/energy_daily_report.py 内容过少，且需结合能力标识与自检判断是否为完整源码")
        for forbidden in ["requests.get(", "urllib.request.urlopen(", "eval(", "exec("]:
            if forbidden in standalone_text:
                errors.append(f"独立 PY 能源日报包含禁止行为: {forbidden}")

    standalone_manifest = project / "standalone/standalone-manifest.json"
    if standalone_manifest.is_file():
        try:
            manifest_data = json.loads(standalone_manifest.read_text(encoding="utf-8-sig"))
            if manifest_data.get("required_entry") != "standalone/energy_daily_report.py":
                errors.append("独立程序清单 required_entry 不正确")
            if "--self-test" not in str(manifest_data.get("self_test", "")):
                errors.append("独立程序清单缺少自检命令")
        except Exception as exc:
            errors.append("独立程序清单 standalone-manifest.json 内容无效，请重新生成")

    standalone_readme = project / "standalone/README_STANDALONE.md"
    if standalone_readme.is_file():
        standalone_guide = standalone_readme.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["python energy_daily_report.py", "--self-test", "EXE", "PyInstaller"]:
            if token not in standalone_guide:
                errors.append(f"独立程序说明缺少内容: {token}")

    standalone_builder = project / "standalone/build_exe_windows.py"
    if standalone_builder.is_file():
        builder_text = standalone_builder.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["PyInstaller", "--onefile", "energy_daily_report.py"]:
            if token.casefold() not in builder_text.casefold():
                errors.append(f"EXE 构建脚本缺少能力: {token}")

    templates = list((project / "templates").rglob("*.html")) if (project / "templates").is_dir() else []
    if not templates:
        errors.append("缺少可运行的服务端页面模板")
    if (project / "static").is_dir() and not list((project / "static").rglob("*.css")):
        errors.append("缺少正式样式文件，疑似未完成界面实现")

    sys.path.insert(0, str(project / "scripts"))
    blueprint = project / "config/business-system-blueprint.json"
    if blueprint.is_file():
        try:
            from validate_business_blueprint import validate_business_blueprint
            result = validate_business_blueprint(json.loads(blueprint.read_text(encoding="utf-8-sig")))
            errors.extend(f"业务蓝图校验失败 [{item['code']}]: {item['message']}" for item in result["errors"])
            warnings.extend(f"业务蓝图提示 [{item['code']}]: {item['message']}" for item in result["warnings"])
        except Exception as exc:
            errors.append("业务蓝图文件无法读取或格式有误，请确认 config/business-system-blueprint.json 存在且为有效 JSON")

    mapping = project / "mapping/source-file-mapping.json"
    if mapping.is_file():
        try:
            data = json.loads(mapping.read_text(encoding="utf-8-sig"))
            if not data.get("sources") or not data.get("mappings"):
                errors.append("字段映射缺少来源或映射记录")
        except Exception as exc:
            errors.append("字段映射文件格式有误，请确认 mapping/source-file-mapping.json 为有效 JSON 且包含来源和映射记录")

    evidence = project / "ACCEPTANCE_EVIDENCE.json"
    if evidence.is_file():
        try:
            data = json.loads(evidence.read_text(encoding="utf-8-sig"))
            cases = data.get("cases", [])
            case_map = {item.get("id"): item for item in cases if isinstance(item, dict)} if isinstance(cases, list) else {}
            required_evidence = set(REQUIRED_EVIDENCE)
            if (project / "standalone/energy_daily_report.py").is_file():
                required_evidence.add("standalone_energy_self_test")
            missing = sorted(required_evidence - set(case_map))
            if missing:
                errors.append("验收证据缺少用例: " + ", ".join(missing))
            failed = sorted(case_id for case_id, item in case_map.items() if item.get("status") != "passed")
            if failed:
                errors.append("验收证据存在未通过或未执行用例: " + ", ".join(failed))
            if data.get("template_notice"):
                errors.append("验收证据仍是模板，尚未由真实测试结果生成")
            if not isinstance(data.get("generated_at"), str) or not data["generated_at"].strip():
                errors.append("验收证据缺少实际生成时间")
            env = data.get("environment")
            if not isinstance(env, dict) or not env.get("python") or not env.get("os"):
                errors.append("验收证据缺少实际 Python 或操作系统环境")
            for case_id, item in case_map.items():
                if not item.get("command") or item.get("exit_code") != 0 or not item.get("executed_at") or not item.get("evidence"):
                    errors.append(f"验收用例缺少命令、退出码、执行时间或证据: {case_id}")
        except Exception as exc:
            errors.append("验收证据 ACCEPTANCE_EVIDENCE.json 格式无效，请重新运行测试生成")

    state = project / ".build-state.json"
    if state.is_file():
        try:
            from validate_build_state import validate_state
            state_data = json.loads(state.read_text(encoding="utf-8-sig"))
            result = validate_state(state_data, project)
            errors.extend(f"构建状态错误 [{item['code']}]: {item['message']}" for item in result["errors"])
            if state_data.get("current_stage") not in {"TESTED", "PACKAGED"}:
                errors.append("构建状态尚未达到 TESTED 或 PACKAGED")
        except Exception as exc:
            errors.append("构建状态文件 .build-state.json 无法读取，请确认文件完整且为有效 JSON")

    db = project / "data/paperless_business.db"
    if db.is_file():
        try:
            con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
            tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = sorted(REQUIRED_TABLES - tables)
            if missing:
                errors.append("数据库缺少通用安全与流程表: " + ", ".join(missing))
            integrity = con.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                errors.append("数据库完整性检查失败")
            foreign_keys = con.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_keys:
                errors.append(f"数据库外键检查失败，共 {len(foreign_keys)} 项")
            con.close()
        except Exception as exc:
            errors.append("数据库无法读取，文件可能已损坏或被占用，请从备份恢复")

    forbidden = [str(path.relative_to(project)) for path in project.rglob("*") if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in path.parts)]
    if forbidden:
        errors.append("交付包包含缓存或虚拟环境: " + ", ".join(forbidden[:10]))

    requirements = project / "requirements.txt"
    if requirements.is_file():
        text = requirements.read_text(encoding="utf-8-sig").casefold()
        for package in ["flask", "waitress"]:
            if package not in text:
                errors.append(f"requirements.txt 缺少依赖: {package}")

    report = project / "TEST_REPORT.md"
    if report.is_file():
        text = report.read_text(encoding="utf-8-sig")
        for heading in ["测试环境", "测试命令", "结果汇总", "数据库检查", "导入导出回读", "真机验证"]:
            if f"## {heading}" not in text:
                errors.append(f"TEST_REPORT.md 缺少标准章节: {heading}")

    for launcher in [project / "start_windows.bat", project / "start_macos.command", project / "start_macos.sh"]:
        if not launcher.is_file():
            continue
        text = launcher.read_text(encoding="utf-8-sig", errors="replace").casefold()
        if launcher.name == "start_macos.command":
            if "start_macos.sh" not in text:
                errors.append("macOS 双击入口未委托给 start_macos.sh")
            continue
        for required in ["preflight", "install_dependencies.py"]:
            if required not in text:
                errors.append(f"启动脚本缺少能力 {required}: {launcher.name}")
        for token in ["不会联网", "不会联网安装"]:
            if token not in text:
                errors.append(f"启动脚本未声明离线安全策略 {token}: {launcher.name}")
        for token in ["install_python_windows.ps1", "install_python_macos.sh", "--allow-online"]:
            if token in text:
                errors.append(f"启动脚本包含自动安装或联网入口 {token}: {launcher.name}")

    for stopper in [project / "stop_windows.bat", project / "stop_macos.command", project / "stop_macos.sh"]:
        if not stopper.is_file():
            continue
        text = stopper.read_text(encoding="utf-8-sig", errors="replace").casefold()
        if stopper.name == "stop_macos.command":
            if "stop_macos.sh" not in text:
                errors.append("macOS 双击停止入口未委托给 stop_macos.sh")
            continue
        if "stop_server.py" not in text:
            errors.append(f"停止脚本未调用项目级 stop_server.py: {stopper.name}")
        for token in ["taskkill /im python.exe", "taskkill /f /im python.exe", "killall python", "pkill -f python"]:
            if token in text:
                errors.append(f"停止脚本存在全局结束 Python 进程风险: {stopper.name}")

    runtime = project / "config/python-runtime.json"
    if runtime.is_file():
        try:
            data = json.loads(runtime.read_text(encoding="utf-8-sig"))
            for platform_name in ["windows", "macos"]:
                item = data.get(platform_name, {})
                file_name, sha = str(item.get("installer_file", "")), str(item.get("sha256", ""))
                expected_suffix = ".exe" if platform_name == "windows" else ".pkg"
                if Path(file_name).name != file_name or not file_name.casefold().endswith(expected_suffix):
                    errors.append(f"Python {platform_name} 安装包文件名不安全")
                if item.get("source_host") != "www.python.org" or item.get("manual_install_only") is not True:
                    errors.append(f"Python {platform_name} 必须标记官方来源和仅手动安装")
                if not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
                    errors.append(f"Python {platform_name} 安装包缺少固定 SHA-256")
            policy = data.get("policy", {})
            for key in ["allow_network_download", "allow_process_launch", "allow_admin_install"]:
                if policy.get(key) is not False:
                    errors.append(f"Python 运行时安全策略必须关闭 {key}")
        except Exception as exc:
            errors.append("Python 运行时配置无效，请确认 config/python-runtime.json 中 URL 和 SHA-256 完整")

    windows = project / "scripts/install_python_windows.ps1"
    if windows.is_file():
        text = windows.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["Get-AuthenticodeSignature", "Get-FileHash", "Python Software Foundation", "不会联网下载"]:
            if token not in text:
                errors.append(f"Windows Python 安装引导缺少安全能力: {token}")
        for token in ["Invoke-WebRequest", "Start-Process", "-Verb RunAs", "ExecutionPolicy Bypass", "Set-ExecutionPolicy", "-WindowStyle Hidden"]:
            if token in text:
                errors.append(f"Windows Python 安装引导包含禁止行为: {token}")

    macos = project / "scripts/install_python_macos.sh"
    if macos.is_file():
        text = macos.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["pkgutil --check-signature", "Python Software Foundation", "shasum -a 256", "不会下载"]:
            if token not in text:
                errors.append(f"macOS Python 安装引导缺少安全能力: {token}")
        for token in ["/usr/bin/curl", "/usr/bin/osascript", "/usr/sbin/installer", "with administrator privileges", "sudo -S", "NOPASSWD", "spctl --master-disable"]:
            if token in text:
                errors.append(f"macOS Python 安装引导包含禁止行为: {token}")

    rights_files = ["COPYRIGHT.md", "PROPRIETARY_LICENSE.md", "THIRD_PARTY_NOTICES.md", "INTELLECTUAL_PROPERTY.json"]
    rights_text: dict[str, str] = {}
    for name in rights_files:
        path = project / name
        if path.is_file():
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            rights_text[name] = text
            if "{{" in text or "}}" in text:
                errors.append(f"产权文件仍含模板占位符: {name}")
    if "COPYRIGHT.md" in rights_text:
        for token in ["版权所有", "权利人", "第三方"]:
            if token not in rights_text["COPYRIGHT.md"]:
                errors.append(f"版权声明缺少必要内容: {token}")
    if "PROPRIETARY_LICENSE.md" in rights_text:
        license_text = rights_text["PROPRIETARY_LICENSE.md"]
        for token in ["仅授权使用", "未经", "不得", "第三方", "用户"]:
            if token not in license_text:
                errors.append(f"专有使用许可缺少必要边界: {token}")
    if "THIRD_PARTY_NOTICES.md" in rights_text:
        third_party = rights_text["THIRD_PARTY_NOTICES.md"]
        for token in ["第三方", "许可证", "Python", "Flask"]:
            if token not in third_party:
                errors.append(f"第三方声明缺少必要内容: {token}")
    ip_path = project / "INTELLECTUAL_PROPERTY.json"
    if ip_path.is_file():
        try:
            ip_data = json.loads(ip_path.read_text(encoding="utf-8-sig"))
            holder = ip_data.get("rights_holder", {})
            if not isinstance(holder, dict) or not str(holder.get("display_name", "")).strip():
                errors.append("权利元数据缺少非空权利人")
            if ip_data.get("license_model") != "proprietary-use-only":
                errors.append("权利元数据许可模式必须为 proprietary-use-only")
            excluded = set(ip_data.get("excluded_scope", []))
            required_exclusions = {"user_source_files_and_data", "third_party_open_source_components", "third_party_trademarks"}
            if not required_exclusions.issubset(excluded):
                errors.append("权利元数据缺少用户数据、开源组件或第三方商标例外")
        except Exception as exc:
            errors.append("权利元数据 INTELLECTUAL_PROPERTY.json 无效，请确认文件格式正确")
    manifest = project / "FILES_SHA256.txt"
    if manifest.is_file():
        manifest_text = manifest.read_text(encoding="utf-8-sig", errors="replace")
        for name in rights_files:
            if name not in manifest_text:
                errors.append(f"文件哈希清单未覆盖产权文件: {name}")

    value_manifest = project / "reports/value-added-manifest.json"
    required_reports = [
        "reports/business_summary.json", "reports/chart_data_config.json",
        "reports/dashboard_config.json", "reports/data_quality_report.json",
    ]
    if not value_manifest.is_file():
        errors.append("缺少可复核的增值报告清单: reports/value-added-manifest.json")
    else:
        try:
            value_data = json.loads(value_manifest.read_text(encoding="utf-8-sig"))
            listed = {item.get("path") for item in value_data.get("files", []) if isinstance(item, dict)}
            for relative in required_reports:
                if relative not in listed or not (project / relative).is_file():
                    errors.append(f"增值报告清单缺少文件: {relative}")
            if value_data.get("all_reports_ready") is not True:
                errors.append("增值报告未基于有效业务蓝图生成")
            for relative in required_reports:
                report_path = project / relative
                if not report_path.is_file():
                    continue
                report_data = json.loads(report_path.read_text(encoding="utf-8-sig"))
                if report_data.get("status") != "ready":
                    errors.append(f"增值报告状态不是 ready: {relative}")
                serialized = json.dumps(report_data, ensure_ascii=False)
                for forbidden_value in ["自动生成", "示例业务数值", "伪造实时"]:
                    if forbidden_value in serialized:
                        errors.append(f"增值报告含不可核验固定表述: {relative}: {forbidden_value}")
        except Exception as exc:
            errors.append("增值报告清单无法读取，请确认 reports/value-added-manifest.json 存在且格式正确")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="验证能源日报系统最低交付合同")
    parser.add_argument("project_dir")
    args = parser.parse_args()
    result = validate(Path(args.project_dir).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
