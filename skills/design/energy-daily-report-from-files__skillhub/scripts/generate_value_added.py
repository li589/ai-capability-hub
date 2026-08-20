#!/usr/bin/env python3
"""Generate evidence-based value-added reports from a generated project."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from friendly_error import friendly_error


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_blueprint(project: Path) -> tuple[dict[str, Any] | None, str | None]:
    path = project / "config/business-system-blueprint.json"
    if not path.is_file():
        return None, "缺少 config/business-system-blueprint.json，不能生成有证据支撑的增值报告。"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, "业务蓝图文件格式有误或已损坏，JSON 解析失败，请重新生成模板后修正"
    return data, None


def database_evidence(project: Path) -> dict[str, Any]:
    path = project / "data/paperless_business.db"
    result: dict[str, Any] = {
        "available": False,
        "path": "data/paperless_business.db",
        "table_counts": {},
        "error": None,
    }
    if not path.is_file():
        result["error"] = "业务数据库不存在，报告只包含蓝图配置，不生成业务数值。"
        return result
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ["business_records", "import_batches", "import_errors", "workflow_instances", "audit_log"]:
            if table in tables:
                quoted = '"' + table.replace('"', '""') + '"'
                result["table_counts"][table] = connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        result["integrity"] = integrity[0] if integrity else "unknown"
        connection.close()
        result["available"] = True
    except sqlite3.Error as exc:
        result["error"] = "数据库访问失败，可能文件已损坏或被占用，请从备份恢复"
    return result


def blueprint_index(blueprint: dict[str, Any] | None) -> dict[str, Any]:
    if not blueprint:
        return {"entities": {}, "metrics": {}, "dashboards": []}
    entities = {
        item.get("key"): item
        for item in blueprint.get("entities", [])
        if isinstance(item, dict) and item.get("key")
    }
    metrics = {
        item.get("key"): item
        for item in blueprint.get("metrics", [])
        if isinstance(item, dict) and item.get("key")
    }
    return {"entities": entities, "metrics": metrics, "dashboards": blueprint.get("dashboards", [])}


def generate_summary_report(project: Path) -> dict[str, Any]:
    blueprint, error = load_blueprint(project)
    index = blueprint_index(blueprint)
    db = database_evidence(project)
    system_name = blueprint.get("system_name") if blueprint else project.name
    metric_names = [
        {"key": key, "display_name": item.get("display_name") or key}
        for key, item in index["metrics"].items()
    ]
    entity_names = [
        {"key": key, "display_name": item.get("display_name") or key}
        for key, item in index["entities"].items()
    ]
    status = "ready" if blueprint else "blocked"
    return {
        "schema_version": "1.0",
        "report_title": f"{system_name} 业务摘要报告",
        "generated_at": now_iso(),
        "status": status,
        "truth_policy": "只呈现蓝图和数据库可验证信息；无真实数据时不生成指标数值或趋势结论。",
        "evidence_sources": ["config/business-system-blueprint.json"] + (["data/paperless_business.db"] if db["available"] else []),
        "blocking_error": error,
        "sections": [
            {
                "title": "一、系统概览",
                "content": {
                    "system_name": system_name,
                    "scenarios": blueprint.get("scenario", []) if blueprint else [],
                    "entities": entity_names,
                    "confirmation_status": blueprint.get("confirmation_status") if blueprint else None,
                },
            },
            {
                "title": "二、核心指标",
                "content": {
                    "configured_metrics": metric_names,
                    "values_status": "由生成系统后端指标服务计算，本报告不伪造数值。",
                },
            },
            {
                "title": "三、数据与运行证据",
                "content": db,
            },
            {
                "title": "四、使用建议",
                "content": [
                    "先确认 candidate 和 unknown 字段，再执行正式导入。",
                    "通过系统后端指标服务生成真实看板数值。",
                    "发布前运行 quick_check.py --deep 并保存验收证据。",
                ],
            },
        ],
    }


def field_keys(entity: dict[str, Any]) -> set[str]:
    return {item.get("key") for item in entity.get("fields", []) if isinstance(item, dict) and item.get("key")}


def generate_chart_data_config(project: Path) -> dict[str, Any]:
    blueprint, error = load_blueprint(project)
    index = blueprint_index(blueprint)
    charts: list[dict[str, Any]] = []
    entities = index["entities"]
    metrics = index["metrics"]

    energy_daily = entities.get("energy_daily_report")
    if energy_daily and {"report_date", "consumption"}.issubset(field_keys(energy_daily)):
        series = [key for key in ["consumption", "cost"] if key in field_keys(energy_daily)]
        charts.append({
            "id": "energy_consumption_trend", "title": "能源消耗与成本趋势", "type": "line",
            "data_source": "energy_daily_report", "x_axis": "report_date",
            "series": series, "group_by": "energy_type" if "energy_type" in field_keys(energy_daily) else None,
            "value_status": "runtime_query_required",
        })
    if energy_daily and {"report_date", "unit_consumption", "target_unit_consumption"}.issubset(field_keys(energy_daily)):
        charts.append({
            "id": "unit_consumption_vs_target", "title": "单耗与目标对比", "type": "bar_line",
            "data_source": "energy_daily_report", "x_axis": "report_date",
            "series": ["unit_consumption", "target_unit_consumption"],
            "group_by": "energy_type" if "energy_type" in field_keys(energy_daily) else None,
            "value_status": "runtime_query_required",
        })
    anomaly = entities.get("energy_anomaly")
    if anomaly and "energy_type" in field_keys(anomaly):
        charts.append({
            "id": "energy_anomaly_distribution", "title": "能耗异常分布", "type": "pie",
            "data_source": "energy_anomaly", "group_by": "energy_type",
            "aggregation": "count", "value_status": "runtime_query_required",
        })

    production = entities.get("production_report")
    if production and {"report_date", "planned_qty", "actual_qty"}.issubset(field_keys(production)):
        charts.append({
            "id": "production_trend", "title": "生产趋势图", "type": "line",
            "data_source": "production_report", "x_axis": "report_date",
            "series": ["planned_qty", "actual_qty"], "value_status": "runtime_query_required",
        })
    quality = entities.get("quality_issue")
    if quality and "defect_type" in field_keys(quality):
        charts.append({
            "id": "quality_distribution", "title": "质量问题分布", "type": "pie",
            "data_source": "quality_issue", "group_by": "defect_type",
            "aggregation": "count", "value_status": "runtime_query_required",
        })
    attendance = entities.get("attendance")
    if attendance and "department_key" in field_keys(attendance):
        charts.append({
            "id": "attendance_summary", "title": "出勤统计", "type": "bar",
            "data_source": "attendance", "group_by": "department_key",
            "metric": "attendance_rate" if "attendance_rate" in metrics else None,
            "value_status": "runtime_query_required",
        })
    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "status": "ready" if blueprint else "blocked",
        "blocking_error": error,
        "truth_policy": "图表仅配置已存在的实体、字段和指标；不嵌入示例业务数值。",
        "charts": charts,
    }


def create_business_dashboard_config(project: Path) -> dict[str, Any]:
    blueprint, error = load_blueprint(project)
    index = blueprint_index(blueprint)
    metrics = index["metrics"]
    widgets: list[dict[str, Any]] = []
    dashboard_metrics: list[str] = []
    dashboards = index["dashboards"]
    if dashboards and isinstance(dashboards[0], dict):
        dashboard_metrics = [key for key in dashboards[0].get("metrics", []) if key in metrics]
    for key in dashboard_metrics:
        metric = metrics[key]
        widgets.append({
            "type": "kpi_card",
            "title": metric.get("display_name") or key,
            "metric": key,
            "unit": metric.get("unit"),
            "value_status": "runtime_metric_service_required",
        })
    chart_config = generate_chart_data_config(project)
    widgets.extend({"type": "chart", "chart_id": item["id"], "size": "large"} for item in chart_config["charts"][:2])
    widgets.append({
        "type": "list", "title": "待办事项", "data_source": "workflow_instances",
        "filter": "current_user_authorized_pending", "limit": 10,
        "value_status": "runtime_query_required",
    })
    return {
        "schema_version": "1.0",
        "dashboard_title": "管理驾驶舱",
        "generated_at": now_iso(),
        "status": "ready" if blueprint else "blocked",
        "blocking_error": error,
        "refresh_mode": "on_request",
        "real_time_claims_allowed": False,
        "widgets": widgets,
    }


def generate_data_quality_report(project: Path) -> dict[str, Any]:
    blueprint, error = load_blueprint(project)
    unknown_fields: list[dict[str, str]] = []
    candidate_fields: list[dict[str, str]] = []
    if blueprint:
        for entity in blueprint.get("entities", []):
            if not isinstance(entity, dict):
                continue
            for field in entity.get("fields", []):
                if not isinstance(field, dict):
                    continue
                item = {"entity": str(entity.get("key", "")), "field": str(field.get("key", ""))}
                if field.get("source_confidence") == "unknown":
                    unknown_fields.append(item)
                elif field.get("source_confidence") == "candidate":
                    candidate_fields.append(item)
    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "status": "ready" if blueprint else "blocked",
        "blocking_error": error,
        "confirmation_status": blueprint.get("confirmation_status") if blueprint else None,
        "unknown_fields": unknown_fields,
        "candidate_fields": candidate_fields,
        "formal_import_allowed": bool(blueprint) and not unknown_fields and blueprint.get("confirmation_status") == "confirmed",
        "next_action": "确认关键字段后再执行正式导入。" if unknown_fields or candidate_fields else "可继续执行测试与验收。",
    }


def generate_value_added_bundle(project: Path) -> dict[str, Any]:
    project = project.resolve()
    reports = {
        "business_summary.json": generate_summary_report(project),
        "chart_data_config.json": generate_chart_data_config(project),
        "dashboard_config.json": create_business_dashboard_config(project),
        "data_quality_report.json": generate_data_quality_report(project),
    }
    output_dir = project / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_files: list[dict[str, str]] = []
    for name, payload in reports.items():
        path = output_dir / name
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        path.write_text(content, encoding="utf-8")
        manifest_files.append({"path": f"reports/{name}", "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()})
    manifest = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "generator": "generate_value_added.py",
        "files": manifest_files,
        "all_reports_ready": all(payload.get("status") == "ready" for payload in reports.values()),
    }
    (output_dir / "value-added-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def render_markdown_report(project: Path) -> str:
    """生成人类可读的增值报告摘要（Markdown 格式）."""
    project = project.resolve()
    lines = ["# 增值报告摘要", "", f"项目：{project.name}", ""]

    summary_path = project / "reports/business_summary.json"
    if summary_path.is_file():
        data = json.loads(summary_path.read_text(encoding="utf-8-sig"))
        lines.append("## 业务概况")
        lines.append("")
        for section in data.get("sections", []):
            title = section.get("title", "")
            content = section.get("content", {})
            lines.append(f"### {title}")
            if isinstance(content, dict):
                for k, v in content.items():
                    if isinstance(v, (str, int, float)):
                        lines.append(f"- **{k}**：{v}")
            elif isinstance(content, list):
                for item in content:
                    lines.append(f"- {item}")
        lines.append("")

    chart_path = project / "reports/chart_data_config.json"
    if chart_path.is_file():
        data = json.loads(chart_path.read_text(encoding="utf-8-sig"))
        charts = data.get("charts", [])
        if charts:
            lines.append("## 图表配置")
            lines.append("")
            lines.append(f"共配置 {len(charts)} 个图表：")
            for chart in charts:
                lines.append(f"- **{chart.get('title')}**（{chart.get('type')}），数据来源：{chart.get('data_source')}")

    quality_path = project / "reports/data_quality_report.json"
    if quality_path.is_file():
        data = json.loads(quality_path.read_text(encoding="utf-8-sig"))
        unknown = data.get("unknown_fields", [])
        candidate = data.get("candidate_fields", [])
        lines.append("")
        lines.append("## 数据质量")
        lines.append("")
        if unknown:
            lines.append(f"⚠ 有 {len(unknown)} 个字段来源不明，需要确认：")
            for item in unknown:
                lines.append(f"  - {item.get('entity')}.{item.get('field')}")
        if candidate:
            lines.append(f"📋 有 {len(candidate)} 个候选字段待确认：")
            for item in candidate:
                lines.append(f"  - {item.get('entity')}.{item.get('field')}")
        if not unknown and not candidate:
            lines.append("✅ 所有字段来源已确认，数据质量良好。")

    lines.append("")
    lines.append("---")
    lines.append("*本报告基于真实蓝图与数据库证据生成，不含伪造数值。*")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="从真实蓝图和数据库证据生成增值报告")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    project = Path(args.project_dir)
    try:
        result = generate_value_added_bundle(project)
    except OSError as exc:
        result = {"ok": False, "code": "VALUE_ADDED_WRITE_FAILED", "message": "报告文件写入失败，请检查磁盘空间和目录写入权限", "action": "检查目录权限和磁盘空间后重试。"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result["ok"] = result["all_reports_ready"]
    if args.format == "markdown":
        md = render_markdown_report(project)
        print(md)
        (project / "reports/value-added-summary.md").write_text(md, encoding="utf-8")
    elif args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("增值报告已生成。" if result["ok"] else "报告文件已生成，但缺少业务蓝图，不能作为完成证据。")
        for item in result["files"]:
            print(f"- {item['path']}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
