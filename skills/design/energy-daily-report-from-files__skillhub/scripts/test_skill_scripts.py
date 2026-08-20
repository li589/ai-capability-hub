#!/usr/bin/env python3
"""Regression tests for the energy daily-report system generator skill."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from classify_scenario import classify
from select_mode import select_mode
from diagnose_and_resume import diagnose, explain_error
from generate_value_added import (
    create_business_dashboard_config,
    generate_chart_data_config,
    generate_data_quality_report,
    generate_summary_report,
    generate_value_added_bundle,
)
from validate_domestic_readiness import check_domestic_readiness
from validate_version_consistency import validate_version_consistency
from validate_security_posture import validate_security_posture
from inspect_business_files import analyze, inspect_file
from quick_check import quick_check
from validate_build_state import decide_retry, validate_state
from validate_business_blueprint import validate_business_blueprint
from validate_delivery import REQUIRED_EVIDENCE, REQUIRED_PATHS, REQUIRED_TABLES, validate
from friendly_error import describe_error, friendly_error
from install_dependencies import install, run_pip
from prepare_offline_dependencies import prepare
from ensure_full_lan_energy_system import ensure as ensure_full_lan
from validate_full_lan_delivery import validate as validate_full_lan
from package_local_deployment import package as package_local_deployment


def load_blueprint() -> dict:
    return json.loads((SKILL_DIR / "resources/config-templates/business-system-blueprint.example.json").read_text(encoding="utf-8"))


class ModeSelectionTests(unittest.TestCase):
    def test_only_analysis_wins_over_generic_analysis_word(self):
        result = select_mode("只分析这些文件，先不要生成系统", has_files=True)
        self.assertEqual(result["mode"], "analysis_only")

    def test_existing_system_is_incremental_mode(self):
        result = select_mode("在我上传的旧系统 ZIP 基础上增量修改", has_files=True, has_existing_system=True)
        self.assertEqual(result["mode"], "adapt_existing_system")

    def test_prototype_without_files(self):
        result = select_mode("暂时没有真实文件，先做评审原型", has_files=False)
        self.assertEqual(result["mode"], "prototype_from_description")

    def test_real_files_default_to_full_build(self):
        result = select_mode("分析后做成能源日报系统", has_files=True)
        self.assertEqual(result["mode"], "full_lan_build")


class InputInspectionTests(unittest.TestCase):
    def test_plain_text_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "需求.md"
            path.write_text("# 生产日报\n日期、班次、产量", encoding="utf-8")
            self.assertTrue(inspect_file(path)["valid"])

    def test_empty_text_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "empty.txt"
            path.write_text("", encoding="utf-8")
            self.assertFalse(inspect_file(path)["valid"])

    def test_corrupt_xlsx_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.xlsx"
            path.write_bytes(b"not a workbook")
            result = inspect_file(path)
            self.assertFalse(result["valid"])
            self.assertTrue(result["errors"])

    def test_corrupt_pdf_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.pdf"
            path.write_bytes(b"not a pdf")
            self.assertFalse(inspect_file(path)["valid"])

    def test_zip_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../escape.csv", "a,b\n1,2")
            result = inspect_file(path)
            self.assertFalse(result["valid"])

    def test_legacy_xls_is_recognized_with_conversion_guidance(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.xls"
            path.write_bytes(bytes.fromhex("D0CF11E0A1B11AE1") + b"placeholder")
            result = inspect_file(path)
            self.assertTrue(result["valid"])
            self.assertIn("XLS_CONVERSION_RECOMMENDED", {item["code"] for item in result["warnings"]})

    def test_error_messages_are_actionable_and_hide_paths(self):
        detail = describe_error(FileNotFoundError("C:\\private\\secret.xlsx"))
        self.assertEqual(detail["code"], "FILE_NOT_FOUND")
        self.assertNotIn("private", friendly_error(FileNotFoundError("C:\\private\\secret.xlsx")))

    def test_safe_zip_with_supported_member_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "safe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("data/report.csv", "a,b\n1,2")
            self.assertTrue(inspect_file(path)["valid"])

    def test_zip_with_corrupt_supported_member_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken-member.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("data/report.xlsx", b"not a workbook")
            result = inspect_file(path)
            self.assertFalse(result["valid"])
            self.assertIn("ZIP_MEMBER_CORRUPT", {item["code"] for item in result["errors"]})

    def test_invalid_only_does_not_continue(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.xlsx"
            path.write_bytes(b"broken")
            result = analyze([str(path)])
            self.assertEqual(result["valid_input_count"], 0)
            self.assertEqual(result["next_action"], "停止生成并修复输入")

    def test_mixed_input_is_partial_and_can_continue(self):
        with tempfile.TemporaryDirectory() as temp:
            good = Path(temp) / "good.csv"
            bad = Path(temp) / "bad.xlsx"
            good.write_text("日期,产量\n2026-08-01,10", encoding="utf-8")
            bad.write_bytes(b"broken")
            result = analyze([str(good), str(bad)])
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["valid_input_count"], 1)
            self.assertEqual(result["next_action"], "继续生成系统")


class BlueprintTests(unittest.TestCase):
    def test_example_blueprint_is_valid(self):
        result = validate_business_blueprint(load_blueprint())
        self.assertTrue(result["ok"], result["errors"])

    def test_business_key_reference_is_checked(self):
        data = load_blueprint()
        data["entities"][0]["business_key"] = ["missing"]
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_BUSINESS_KEY_REFERENCE", {item["code"] for item in result["errors"]})

    def test_optimistic_lock_is_required(self):
        data = load_blueprint()
        data["entities"][0]["fields"] = [item for item in data["entities"][0]["fields"] if item["key"] != "version"]
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_OPTIMISTIC_LOCK", {item["code"] for item in result["errors"]})

    def test_unknown_entity_reference_is_checked(self):
        data = load_blueprint()
        data["pages"][1]["entity"] = "missing"
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_ENTITY_REFERENCE", {item["code"] for item in result["errors"]})

    def test_workflow_state_is_checked(self):
        data = load_blueprint()
        data["workflows"][0]["transitions"][0]["to"] = "missing"
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_TRANSITION_STATE", {item["code"] for item in result["errors"]})

    def test_transition_permission_is_checked(self):
        data = load_blueprint()
        data["workflows"][0]["transitions"][0]["permission"] = "missing"
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_TRANSITION_PERMISSION", {item["code"] for item in result["errors"]})

    def test_metric_zero_denominator_is_checked(self):
        data = load_blueprint()
        metric = next(item for item in data["metrics"] if "/" in item["formula"])
        metric.pop("zero_denominator")
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_ZERO_DENOMINATOR", {item["code"] for item in result["errors"]})

    def test_integration_truth_policy_is_required(self):
        data = load_blueprint()
        data["integrations"]["not_configured_policy"] = "pretend_online"
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_INTEGRATION_TRUTH", {item["code"] for item in result["errors"]})

    def test_prohibited_financial_automation_is_rejected(self):
        data = load_blueprint()
        data["tax_config"]["automatic_payment"] = True
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_PROHIBITED_FINANCIAL_AUTOMATION", {item["code"] for item in result["errors"]})

    def test_invalid_business_month_is_rejected(self):
        data = load_blueprint()
        data["fiscal_config"]["business_month_start_day"] = 31
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_BUSINESS_MONTH_START", {item["code"] for item in result["errors"]})

    def test_personal_information_controls_are_required_when_enabled(self):
        data = load_blueprint()
        data["personal_info"]["export_requires_permission"] = False
        result = validate_business_blueprint(data)
        self.assertIn("BLUEPRINT_PERSONAL_INFO_CONTROL", {item["code"] for item in result["errors"]})

    def test_energy_scope_has_core_entities(self):
        data = load_blueprint()
        self.assertGreaterEqual(len(data["entities"]), 4)
        self.assertTrue({"energy_daily", "meter_reading", "energy_target", "energy_anomaly"}.issubset(set(data["scenario"])))
        entity_keys = {item["key"] for item in data["entities"]}
        self.assertTrue({"energy_daily_report", "energy_meter", "energy_target", "energy_anomaly"}.issubset(entity_keys))
        self.assertEqual(data["confirmation_status"], "confirmed")


class BuildStateTests(unittest.TestCase):
    def base_state(self) -> dict:
        return {
            "schema_version": "1.0", "skill_version": "1.7.0", "project_id": "demo",
            "input_fingerprint": "0" * 64, "business_blueprint_sha256": "1" * 64,
            "calculation_version": "1.0.0", "current_stage": "ANALYZED",
            "stages": {stage: {"status": "pending", "artifacts": []} for stage in ["ANALYZED", "MAPPED", "SCAFFOLDED", "IMPLEMENTED", "IMPORTED", "TESTED", "PACKAGED"]},
            "last_error": None,
        }

    def test_template_state_resumes_analyzed(self):
        with tempfile.TemporaryDirectory() as temp:
            result = validate_state(self.base_state(), Path(temp))
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["resume_from"], "ANALYZED")

    def test_unsafe_artifact_path_is_rejected(self):
        state = self.base_state()
        state["stages"]["ANALYZED"] = {"status": "completed", "artifacts": ["../escape.txt"]}
        with tempfile.TemporaryDirectory() as temp:
            result = validate_state(state, Path(temp))
            self.assertIn("STATE_ARTIFACT_UNSAFE_PATH", {item["code"] for item in result["errors"]})

    def test_blueprint_change_restarts_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            result = validate_state(self.base_state(), Path(temp), expected_profile_sha256="2" * 64)
            self.assertEqual(result["resume_from"], "ANALYZED")
            self.assertIn("STATE_BLUEPRINT_CHANGED", {item["code"] for item in result["errors"]})

    def test_retry_is_bounded(self):
        self.assertTrue(decide_retry("FILE_LOCKED", 0)["retry"])
        self.assertFalse(decide_retry("FILE_LOCKED", 2)["retry"])
        self.assertFalse(decide_retry("TEST_FAILURE", 0)["retry"])


class ScenarioClassificationTests(unittest.TestCase):
    def test_standard_scenario_is_supported(self):
        result = classify("根据能源日报生成本地系统")
        self.assertEqual(result["decision"], "supported_standard_scenario")
        self.assertIn("energy_daily", result["matched_scenarios"])
        self.assertTrue(result["first_call_gate"])

    def test_combined_scenario_is_unified(self):
        result = classify("生成能源日报、能源目标和能耗异常预警系统")
        self.assertEqual(result["decision"], "supported_combined_scenario")
        self.assertTrue({"energy_daily", "energy_target", "energy_anomaly"}.issubset(result["matched_scenarios"]))
        self.assertIn("共享组织", result["next_action"])

    def test_sensitive_boundary_requires_confirmation(self):
        result = classify("多公司能源成本系统，包含金额和跨部门审批")
        self.assertEqual(result["decision"], "supported_after_confirmation")
        topics = {item["topic"] for item in result["confirmation_items"]}
        self.assertTrue({"金额", "多公司", "跨部门审批"}.issubset(topics))

    def test_prohibited_automation_is_removed(self):
        result = classify("能源台账自动下单并自动付款")
        self.assertEqual(result["decision"], "supported_with_prohibited_automation_removed")
        self.assertFalse(result["first_call_gate"])
        self.assertEqual(len(result["prohibited_automation"]), 2)

    def test_ambiguous_request_asks_for_minimum_description(self):
        result = classify("帮我做一个系统")
        self.assertEqual(result["decision"], "needs_business_description")
        self.assertTrue(result["confirmation_items"])


class RecoveryExperienceTests(unittest.TestCase):
    def make_project(self, project: Path) -> None:
        for directory in ["src", "templates", "static", "data", "config"]:
            (project / directory).mkdir(parents=True, exist_ok=True)
        for name in ["app.py", "requirements.txt", "README_运行说明.md", "VERSION"]:
            (project / name).write_text("ok", encoding="utf-8")
        (project / "config/business-system-blueprint.json").write_text(json.dumps(load_blueprint()), encoding="utf-8")
        con = sqlite3.connect(project / "data/paperless_business.db")
        con.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()
        state = BuildStateTests().base_state()
        state["last_error"] = {"code": "TEST_FAILURE", "attempt": 0}
        (project / ".build-state.json").write_text(json.dumps(state), encoding="utf-8")

    def test_error_catalog_is_actionable(self):
        result = explain_error({"code": "DATABASE_INTEGRITY_FAILED"})
        self.assertFalse(result["automatic_retry"])
        self.assertIn("备份", result["action"])

    def test_diagnosis_preserves_data_and_reports_progress(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = diagnose(project, check_dependencies=False)
        self.assertEqual(result["resume_from"], "ANALYZED")
        self.assertEqual(result["progress"]["percent"], 0)
        self.assertIn("只读", result["data_safety"])
        self.assertEqual(result["last_error"]["code"], "TEST_FAILURE")

    def test_quick_check_has_single_user_facing_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = quick_check(project, check_dependencies=False)
        self.assertIn("headline", result)
        self.assertIn("resume_from", result)
        self.assertIn("next_action", result)
        self.assertIn("data_safety", result)

    def test_quick_check_hides_technical_codes_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            (project / "app.py").unlink()
            result = quick_check(project, check_dependencies=False)
            from quick_check import render_text
            text = render_text(result)
            self.assertNotIn("[STATE_FILE_NOT_FOUND]", text)
            self.assertIn("操作：", text)


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_and_trigger(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: energy-daily-report-from-files", text)
        self.assertNotIn("agent_created:", text)
        self.assertTrue((SKILL_DIR / "agents/openai.yaml").is_file())
        for extension in ["xlsx", "xlsm", "xls", "ods", "csv", "tsv", "docx", "pdf", "txt", "md", "zip"]:
            self.assertIn(extension, text)

    def test_optimized_description_covers_public_capabilities(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["能源日报", "表计抄表", "目标偏差", "能源成本", "异常整改", "生产日报与班报", "设备点检维修", "管理看板"]:
            self.assertIn(phrase, skill)
        for phrase in ["数据范围", "审批", "导入", "审计", "源码 ZIP", "standalone/energy_daily_report.py", "EXE"]:
            self.assertIn(phrase, skill)

    def test_first_call_gate_is_explicit(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["首次调用完成门禁", "同一次调用", "完整系统实现", "测试修复", "ZIP 交付", "只分析"]:
            self.assertIn(phrase, text)
        for unfinished in ["静态 HTML", "伪代码", "空数据库"]:
            self.assertIn(unfinished, text)

    def test_references_are_linked(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for name in ["business-blueprint-guide.md", "paperless-system-generation-guide.md", "generic-database-schema.md", "acceptance-checklist.md", "cross-platform-runtime.md", "china-localization-guide.md"]:
            self.assertIn(name, skill)
            self.assertTrue((SKILL_DIR / "references" / name).is_file())

    def test_acceptance_template_is_pending(self):
        data = json.loads((SKILL_DIR / "resources/mapping-templates/acceptance-evidence.example.json").read_text(encoding="utf-8"))
        self.assertTrue(data["template_notice"])
        self.assertEqual({item["status"] for item in data["cases"]}, {"pending"})
        ids = {item["id"] for item in data["cases"]}
        self.assertTrue(REQUIRED_EVIDENCE.issubset(ids))
        self.assertTrue({"personal_data_masking", "currency_decimal_rounding", "business_calendar_boundary", "value_added_reports_truthful"}.issubset(ids))

    def test_energy_identity_is_consistent(self):
        metadata = json.loads((SKILL_DIR / "SKILL_VERSION.json").read_text(encoding="utf-8"))
        registry = json.loads((SKILL_DIR / "_meta.json").read_text(encoding="utf-8"))
        ip = json.loads((SKILL_DIR / "INTELLECTUAL_PROPERTY.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["name"], "energy-daily-report-from-files")
        self.assertEqual(registry["slug"], metadata["name"])
        self.assertEqual(ip["work_id"], metadata["name"])
        self.assertEqual(metadata["display_name"], "能源日报本地系统生成器")
        self.assertEqual(ip["work_name"], metadata["display_name"])

    def test_security_forbidden_tokens_absent_from_launchers(self):
        launchers = SKILL_DIR / "resources/launcher-templates"
        windows = (launchers / "install_python_windows.txt").read_text(encoding="utf-8-sig", errors="replace")
        macos = (launchers / "install_python_macos.txt").read_text(encoding="utf-8-sig", errors="replace")
        for token in ["Invoke-WebRequest", "Start-Process", "-Verb RunAs", "ExecutionPolicy Bypass", "Set-ExecutionPolicy", "-WindowStyle Hidden"]:
            self.assertNotIn(token, windows)
        for token in ["/usr/bin/curl", "/usr/bin/osascript", "/usr/sbin/installer", "with administrator privileges", "sudo -S", "NOPASSWD", "spctl --master-disable"]:
            self.assertNotIn(token, macos)
        for token in ["Get-AuthenticodeSignature", "Get-FileHash", "Python Software Foundation", "不会联网下载"]:
            self.assertIn(token, windows)
        for token in ["pkgutil --check-signature", "Python Software Foundation", "不会下载", "shasum -a 256"]:
            self.assertIn(token, macos)

    def test_launch_and_stop_templates_are_paired(self):
        launchers = SKILL_DIR / "resources/launcher-templates"
        for name in ["start_windows.txt", "stop_windows.txt", "start_macos.txt", "stop_macos.txt", "start_macos.sh", "stop_macos.sh"]:
            self.assertTrue((launchers / name).is_file(), name)
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["start_windows.bat", "stop_windows.bat", "start_macos.command", "stop_macos.command", "一键启动", "一键停止"]:
            self.assertIn(phrase, skill)

    def test_build_script_never_installs_packages(self):
        text = (SKILL_DIR / "resources/standalone-energy-daily-report/build_exe_windows.py").read_text(encoding="utf-8")
        for token in ["pip\", \"install", "--upgrade", "shell=True", "os.system"]:
            self.assertNotIn(token, text)
        self.assertIn("importlib.util.find_spec", text)

    def test_ip_contract_is_complete_and_scoped(self):
        required = [
            "COPYRIGHT.md", "PROPRIETARY_LICENSE.md", "THIRD_PARTY_NOTICES.md", "INTELLECTUAL_PROPERTY.json",
            "references/intellectual-property-protection.md",
            "resources/legal-templates/COPYRIGHT.generated-system.md",
            "resources/legal-templates/PROPRIETARY_LICENSE.generated-system.md",
            "resources/legal-templates/THIRD_PARTY_NOTICES.generated-system.md",
            "resources/legal-templates/INTELLECTUAL_PROPERTY.generated-system.json",
        ]
        for relative in required:
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)
        copyright_text = (SKILL_DIR / "COPYRIGHT.md").read_text(encoding="utf-8")
        license_text = (SKILL_DIR / "PROPRIETARY_LICENSE.md").read_text(encoding="utf-8")
        metadata = json.loads((SKILL_DIR / "INTELLECTUAL_PROPERTY.json").read_text(encoding="utf-8"))
        for text in ["平台实名权利人", "用户上传", "第三方", "不构成已取得注册商标权"]:
            self.assertIn(text, copyright_text)
        for text in ["仅授权使用", "数据备份", "第三方开源组件", "不得加入远程锁机"]:
            self.assertIn(text, license_text)
        self.assertEqual(metadata["license_model"], "proprietary-use-only")
        self.assertFalse(metadata["technical_protection"]["destructive_drm_allowed"])

    def test_recovery_documents_and_tools_exist(self):
        required = [
            "scripts/classify_scenario.py", "scripts/diagnose_and_resume.py", "scripts/quick_check.py",
            "references/scenario-decision-matrix.md", "references/error-catalog-and-recovery.md",
            "references/complete-output-walkthrough.md",
        ]
        for relative in required:
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for text in ["classify_scenario.py", "quick_check.py", "组合", "增值报告"]:
            self.assertIn(text, skill)

    def test_complete_output_walkthrough_is_end_to_end(self):
        text = (SKILL_DIR / "references/complete-output-walkthrough.md").read_text(encoding="utf-8")
        for phrase in ["登录与首次使用", "首页管理看板", "能源日报主流程", "独立 PY 能源日报", "跨模块闭环", "历史导入", "导出与追溯", "构建恢复", "最终 ZIP 导航"]:
            self.assertIn(phrase, text)

    def test_python_files_compile(self):
        for path in SKILL_DIR.rglob("*.py"):
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")


class DeliveryGateTests(unittest.TestCase):
    def test_empty_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            result = validate(Path(temp))
            self.assertFalse(result["ok"])
            self.assertTrue(any("缺少交付项" in item for item in result["errors"]))

    def test_static_only_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "templates").mkdir()
            (project / "templates/index.html").write_text("<h1>Demo</h1>", encoding="utf-8")
            (project / "static").mkdir()
            result = validate(project)
            self.assertFalse(result["ok"])
            self.assertTrue(any("空壳" in item for item in result["errors"]))

    def test_template_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            source = SKILL_DIR / "resources/mapping-templates/acceptance-evidence.example.json"
            (project / "ACCEPTANCE_EVIDENCE.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            result = validate(project)
            self.assertTrue(any("仍是模板" in item for item in result["errors"]))

    def make_rights_only(self, project: Path) -> None:
        files = {
            "COPYRIGHT.md": "版权所有 © 2026 平台实名权利人。权利人原创内容受保护，第三方权利保留。",
            "PROPRIETARY_LICENSE.md": "仅授权使用。未经书面许可不得复制、发布或转售。用户数据归用户，第三方组件遵循原许可证。",
            "THIRD_PARTY_NOTICES.md": "第三方组件 Python、Flask、SQLite 和 Waitress 遵循各自许可证。",
            "INTELLECTUAL_PROPERTY.json": json.dumps({
                "rights_holder": {"display_name": "平台实名权利人"},
                "license_model": "proprietary-use-only",
                "excluded_scope": ["user_source_files_and_data", "third_party_open_source_components", "third_party_trademarks"],
            }),
            "FILES_SHA256.txt": "COPYRIGHT.md\nPROPRIETARY_LICENSE.md\nTHIRD_PARTY_NOTICES.md\nINTELLECTUAL_PROPERTY.json\n",
        }
        for name, content in files.items():
            (project / name).write_text(content, encoding="utf-8")

    def test_missing_rights_notice_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_rights_only(project)
            (project / "COPYRIGHT.md").unlink()
            result = validate(project)
            self.assertTrue(any("COPYRIGHT.md" in item for item in result["errors"]))

    def test_rights_template_placeholder_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_rights_only(project)
            (project / "PROPRIETARY_LICENSE.md").write_text("权利人：{{RIGHTS_HOLDER}}", encoding="utf-8")
            result = validate(project)
            self.assertTrue(any("模板占位符" in item for item in result["errors"]))

    def test_missing_third_party_exclusion_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_rights_only(project)
            path = project / "INTELLECTUAL_PROPERTY.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["excluded_scope"].remove("third_party_open_source_components")
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate(project)
            self.assertTrue(any("开源组件" in item for item in result["errors"]))

    def test_hash_manifest_must_cover_rights_files(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_rights_only(project)
            (project / "FILES_SHA256.txt").write_text("COPYRIGHT.md\n", encoding="utf-8")
            result = validate(project)
            self.assertTrue(any("未覆盖产权文件" in item for item in result["errors"]))

    def test_required_delivery_contract_keeps_standalone_optional(self):
        self.assertIn("data/paperless_business.db", REQUIRED_PATHS)
        self.assertIn("config/business-system-blueprint.json", REQUIRED_PATHS)
        self.assertNotIn("standalone/energy_daily_report.py", REQUIRED_PATHS)
        self.assertNotIn("standalone/build_exe_windows.py", REQUIRED_PATHS)
        self.assertIn("COPYRIGHT.md", REQUIRED_PATHS)
        self.assertIn("INTELLECTUAL_PROPERTY.json", REQUIRED_PATHS)
        self.assertIn("business_records", REQUIRED_TABLES)
        self.assertNotIn("standalone_energy_self_test", REQUIRED_EVIDENCE)


class ValueAddedTests(unittest.TestCase):
    def make_project(self, project: Path) -> None:
        (project / "config").mkdir(parents=True, exist_ok=True)
        (project / "config/business-system-blueprint.json").write_text(json.dumps(load_blueprint(), ensure_ascii=False), encoding="utf-8")
        (project / "data").mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(project / "data/paperless_business.db")
        for table in ["business_records", "import_batches", "import_errors", "workflow_instances", "audit_log"]:
            connection.execute(f"CREATE TABLE {table}(id INTEGER PRIMARY KEY)")
        connection.commit()
        connection.close()

    def test_missing_blueprint_blocks_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            result = generate_summary_report(Path(temp))
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(result["blocking_error"])

    def test_generate_summary_report_uses_blueprint_and_database(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = generate_summary_report(project)
            self.assertEqual(result["status"], "ready")
            self.assertIn("企业能源日报管理系统", result["report_title"])
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertIn("energy_daily_report", serialized)
            self.assertNotIn('"generated_at": "自动生成"', serialized)

    def test_chart_config_only_references_real_blueprint(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = generate_chart_data_config(project)
            self.assertEqual(result["status"], "ready")
            chart_ids = {c["id"] for c in result["charts"]}
            self.assertEqual(chart_ids, {"energy_consumption_trend", "unit_consumption_vs_target", "energy_anomaly_distribution"})
            self.assertTrue(all(item["value_status"] == "runtime_query_required" for item in result["charts"]))

    def test_dashboard_has_no_fake_values(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = create_business_dashboard_config(project)
            self.assertEqual(result["dashboard_title"], "管理驾驶舱")
            self.assertFalse(result["real_time_claims_allowed"])
            self.assertTrue(all("value" not in widget for widget in result["widgets"]))
            widget_types = {w["type"] for w in result["widgets"]}
            self.assertTrue({"kpi_card", "chart", "list"}.issubset(widget_types))

    def test_data_quality_report_controls_formal_import(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = generate_data_quality_report(project)
            self.assertTrue(result["candidate_fields"])
            self.assertTrue(result["formal_import_allowed"])

    def test_bundle_writes_manifest_and_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.make_project(project)
            result = generate_value_added_bundle(project)
            self.assertTrue(result["all_reports_ready"])
            self.assertEqual(len(result["files"]), 4)
            self.assertTrue((project / "reports/value-added-manifest.json").is_file())
            for item in result["files"]:
                self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")

    def test_generate_value_added_script_exists(self):
        script_path = SKILL_DIR / "scripts" / "generate_value_added.py"
        self.assertTrue(script_path.is_file())
        compile(script_path.read_text(encoding="utf-8-sig"), str(script_path), "exec")


class ChinaLocalizationTests(unittest.TestCase):
    def test_blueprint_has_china_config(self):
        data = load_blueprint()
        self.assertIn("personal_info", data)
        self.assertIn("tax_config", data)
        self.assertIn("fiscal_config", data)
        self.assertTrue(data["personal_info"]["id_card_masking"])
        self.assertTrue(data["personal_info"]["export_requires_permission"])
        self.assertFalse(data["tax_config"]["enabled"])
        self.assertFalse(data["tax_config"]["automatic_payment"])
        self.assertEqual(data["tax_config"]["currency"], "CNY")
        self.assertEqual(data["fiscal_config"]["period_type"], "calendar")
        self.assertEqual(data["fiscal_config"]["holiday_calendar_status"], "not_configured")

    def test_blueprint_has_energy_daily_entity(self):
        data = load_blueprint()
        entity_keys = {e["key"] for e in data["entities"]}
        self.assertIn("energy_daily_report", entity_keys)
        entity = next(e for e in data["entities"] if e["key"] == "energy_daily_report")
        field_keys = {f["key"] for f in entity["fields"]}
        for key in ["report_date", "energy_type", "opening_reading", "closing_reading", "consumption", "unit_consumption", "cost"]:
            self.assertIn(key, field_keys)

    def test_china_localization_guide_exists(self):
        guide_path = SKILL_DIR / "references" / "china-localization-guide.md"
        self.assertTrue(guide_path.is_file())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("个人信息保护", content)
        self.assertIn("税率由用户确认", content)
        self.assertIn("会计期间", content)
        self.assertIn("不构成法律、税务", content)

    def test_domestic_readiness_detects_runtime_placeholders(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "config").mkdir()
            (project / "config/business-system-blueprint.json").write_text(json.dumps(load_blueprint(), ensure_ascii=False), encoding="utf-8")
            runtime = (SKILL_DIR / "resources/config-templates/python-runtime.example.json").read_text(encoding="utf-8")
            (project / "config/python-runtime.json").write_text(runtime, encoding="utf-8")
            result = check_domestic_readiness(project)
            check = {item["id"]: item for item in result["checks"]}
            self.assertEqual(check["python_runtime_pinned"]["status"], "failed")
            self.assertEqual(result["status"], "failed")

    def test_domestic_readiness_reports_no_legal_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "config").mkdir()
            (project / "config/business-system-blueprint.json").write_text(json.dumps(load_blueprint(), ensure_ascii=False), encoding="utf-8")
            runtime = {
                "mode": "verify-only",
                "windows": {"installer_file": "python.exe", "source_host": "www.python.org", "manual_install_only": True, "sha256": "a" * 64},
                "macos": {"installer_file": "python.pkg", "source_host": "www.python.org", "manual_install_only": True, "sha256": "b" * 64},
                "policy": {"allow_network_download": False, "allow_process_launch": False, "allow_admin_install": False},
            }
            (project / "config/python-runtime.json").write_text(json.dumps(runtime), encoding="utf-8")
            result = check_domestic_readiness(project)
            self.assertIn("不构成法律", result["legal_notice"])
            check = {item["id"]: item for item in result["checks"]}
            self.assertEqual(check["chinese_locale_timezone"]["status"], "passed")
            self.assertEqual(check["currency_tax_safety"]["status"], "passed")


class StandaloneEnergyDailyTests(unittest.TestCase):
    def test_template_self_test_passes(self):
        script = SKILL_DIR / "resources/standalone-energy-daily-report/energy_daily_report.py"
        result = subprocess.run([sys.executable, str(script), "--self-test"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["checks"], 9)

    def test_ensure_script_copies_complete_bundle(self):
        module_path = SKILL_DIR / "scripts/ensure_energy_daily_standalone.py"
        spec = importlib.util.spec_from_file_location("ensure_energy_daily_standalone", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            result = module.ensure(project, overwrite=True)
            self.assertEqual(result["required_entry"], "standalone/energy_daily_report.py")
            for name in ["energy_daily_report.py", "README_STANDALONE.md", "requirements_standalone.txt", "build_exe_windows.py", "standalone-manifest.json"]:
                self.assertTrue((project / "standalone" / name).is_file(), name)
            copied_script = project / "standalone/energy_daily_report.py"
            run = subprocess.run([sys.executable, str(copied_script), "--self-test"], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)



class VersionConsistencyTests(unittest.TestCase):
    def test_version_consistency(self):
        result = validate_version_consistency(SKILL_DIR)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["expected_version"], "1.7.0")
        self.assertEqual(result["occurrences"], [])

    def test_version_validator_detects_stale_release(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            (skill / "resources/mapping-templates").mkdir(parents=True)
            (skill / "VERSION.txt").write_text("9.9.9\n", encoding="utf-8")
            (skill / "SKILL_VERSION.json").write_text(json.dumps({"version": "9.9.9"}), encoding="utf-8")
            (skill / "resources/mapping-templates/build-state.example.json").write_text(json.dumps({"skill_version": "9.9.9"}), encoding="utf-8")
            (skill / "README.md").write_text("V9.9.9\n版本：9.9.9\n旧版 V8.8.8", encoding="utf-8")
            (skill / "SKILL.md").write_text("V9.9.9", encoding="utf-8")
            (skill / "SECURITY_AUDIT.md").write_text("V9.9.9", encoding="utf-8")
            result = validate_version_consistency(skill)
            self.assertFalse(result["ok"])
            self.assertTrue(result["occurrences"])

    def test_current_release_tools_exist(self):
        required = [
            "scripts/generate_value_added.py", "scripts/validate_domestic_readiness.py",
            "scripts/validate_version_consistency.py", "scripts/ensure_energy_daily_standalone.py",
            "references/china-localization-guide.md", "references/standalone-energy-daily-report.md",
        ]
        for relative in required:
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for text in ["generate_value_added", "validate_domestic_readiness", "validate_version_consistency", "ensure_energy_daily_standalone", "增值报告", "管理驾驶舱", "energy_daily_report.py"]:
            self.assertIn(text, skill)


class DependencyInstallExperienceTests(unittest.TestCase):
    def test_pip_is_forced_offline(self):
        with patch("install_dependencies.subprocess.run") as mocked:
            mocked.return_value = subprocess.CompletedProcess([], 0, "", "")
            run_pip(["-r", "requirements.txt"], Path("."))
            command = mocked.call_args.args[0]
            self.assertEqual(command[:3], [sys.executable, "-m", "pip"])
            environment = mocked.call_args.kwargs["env"]
            self.assertEqual(environment["PIP_NO_INDEX"], "1")
            self.assertEqual(environment["PIP_DISABLE_PIP_VERSION_CHECK"], "1")

    def test_missing_offline_wheels_blocks_install(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "requirements.txt").write_text("openpyxl==3.1.5\n", encoding="utf-8")
            result = install(project)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "OFFLINE_DEPENDENCIES_UNAVAILABLE")

    def test_offline_preparation_requires_preprovided_wheels(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "requirements.txt").write_text("openpyxl==3.1.5\n", encoding="utf-8")
            result = prepare(project)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "WHEELS_NOT_PROVIDED")


class SecurityPostureTests(unittest.TestCase):
    def test_release_security_gate_passes(self):
        result = validate_security_posture(SKILL_DIR)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["policy"], "verify-only/offline-only/no-elevation")

    def test_security_gate_detects_launcher_elevation(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            launcher = skill / "resources/launcher-templates"
            launcher.mkdir(parents=True)
            (launcher / "bad.txt").write_text("Start-Process x -Verb RunAs", encoding="utf-8")
            result = validate_security_posture(skill)
            codes = {item["code"] for item in result["errors"]}
            self.assertIn("SECURITY_LAUNCHER_FORBIDDEN", codes)

    def test_security_gate_detects_non_ascii_archive_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp)
            (skill / "中文.txt").write_text("x", encoding="utf-8")
            result = validate_security_posture(skill)
            codes = {item["code"] for item in result["errors"]}
            self.assertIn("SECURITY_NON_ASCII_ARCHIVE_PATH", codes)


class FullLanDeliveryTests(unittest.TestCase):
    def test_reference_full_lan_has_web_backup_and_complete_source(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            manifest = ensure_full_lan(project, overwrite=True)
            self.assertTrue(manifest["ok"], manifest)
            result = validate_full_lan(project)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["checks"]["primary_ui"], "responsive_web")
            self.assertEqual(result["checks"]["backup_restore_self_test"], "passed")
            self.assertGreaterEqual(result["first_party_python_source_count"], 10)
            self.assertGreater(result["third_party_vendor_python_source_count"], 0)

    def test_packager_adds_navigation_truthful_status_and_split_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            project = temp / "project"
            ensure_full_lan(project, overwrite=True)
            output = temp / "delivery.zip"
            result = package_local_deployment(project, output, root_name="能源日报系统")
            self.assertTrue(result["ok"], result)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("能源日报系统/00_请先看_交付导航.md", names)
                self.assertIn("能源日报系统/DELIVERY_STATUS.json", names)
                self.assertIn("能源日报系统/PY_SOURCE_MANIFEST.json", names)
                status = json.loads(archive.read("能源日报系统/DELIVERY_STATUS.json").decode("utf-8"))
                source_manifest = json.loads(archive.read("能源日报系统/PY_SOURCE_MANIFEST.json").decode("utf-8"))
            self.assertEqual(status["primary_ui"], "responsive_web")
            self.assertFalse(status["built_exe_included"])
            self.assertFalse(status["windows_exe_runtime_verified"])
            self.assertTrue(status["exe_build_source_included"])
            self.assertGreater(source_manifest["first_party_python_source_count"], 0)
            self.assertGreater(source_manifest["third_party_vendor_python_source_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
