#!/usr/bin/env python3
"""Evaluate domestic deployment readiness without claiming legal compliance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PLACEHOLDERS = {"REPLACE_VERSION", "REPLACE_WITH_64_HEX_FROM_OFFICIAL_RELEASE", "TODO", "CHANGE_ME"}
TEXT_EXTENSIONS = {".html", ".css", ".js", ".md", ".json", ".py", ".txt", ".sh", ".bat", ".ps1"}
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
ALLOWED_RUNTIME_HOSTS = {"www.python.org", "registry.npmmirror.com", "mirrors.huaweicloud.com"}


def check_domestic_readiness(project: Path) -> dict:
    checks: list[dict] = []

    def add(check_id: str, status: str, message: str, action: str | None = None, evidence: object = None) -> None:
        checks.append({"id": check_id, "status": status, "message": message, "action": action, "evidence": evidence})

    blueprint_path = project / "config/business-system-blueprint.json"
    blueprint = None
    if blueprint_path.is_file():
        try:
            blueprint = json.loads(blueprint_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            add("blueprint_readable", "failed", "业务蓝图文件读取失败，请检查文件是否被占用或格式有误", "修复蓝图 JSON。")
    else:
        add("blueprint_readable", "failed", "缺少业务蓝图。", "生成 config/business-system-blueprint.json。")

    if blueprint is not None:
        add("blueprint_readable", "passed", "业务蓝图可读取。", evidence="config/business-system-blueprint.json")
        locale_ok = blueprint.get("locale") == "zh-CN" and blueprint.get("timezone") == "Asia/Shanghai"
        add("chinese_locale_timezone", "passed" if locale_ok else "failed", "已配置 zh-CN 与 Asia/Shanghai。" if locale_ok else "中文区域或中国标准时间未正确配置。", "设置 locale=zh-CN、timezone=Asia/Shanghai。")
        personal = blueprint.get("personal_info", {})
        personal_controls = ["data_classification", "id_card_masking", "phone_masking", "bank_card_masking", "export_requires_permission", "retention_review_required"]
        personal_ok = isinstance(personal, dict) and personal.get("enabled") is True and all(personal.get(key) is True for key in personal_controls)
        add("personal_data_controls", "passed" if personal_ok else "needs_confirmation", "个人信息分类、脱敏、导出权限和保留复核已配置。" if personal_ok else "个人信息控制未完整配置或尚未确认。", "根据真实业务和适用要求确认后配置。")
        tax = blueprint.get("tax_config", {})
        tax_safe = isinstance(tax, dict) and tax.get("currency") == "CNY" and tax.get("rounding") in {"ROUND_HALF_UP", "ROUND_HALF_EVEN", "ROUND_DOWN"} and tax.get("automatic_filing") is False and tax.get("automatic_payment") is False
        add("currency_tax_safety", "passed" if tax_safe else "failed", "人民币、Decimal 舍入和禁止自动报税/付款已配置。" if tax_safe else "金额、舍入或禁止自动财务动作配置不完整。", "补齐 CNY、舍入策略并关闭自动报税和自动付款。")
        fiscal = blueprint.get("fiscal_config", {})
        fiscal_ok = isinstance(fiscal, dict) and fiscal.get("period_type") in {"calendar", "business_month", "fiscal_year"} and isinstance(fiscal.get("business_month_start_day", 1), int) and 1 <= fiscal.get("business_month_start_day", 1) <= 28 and fiscal.get("holiday_calendar_status") in {"not_configured", "user_confirmed"}
        add("business_calendar", "passed" if fiscal_ok else "failed", "业务月和节假日配置状态有效。" if fiscal_ok else "业务月或节假日配置状态无效。", "使用 1-28 作为业务月起始日；未提供有效日历时标记 not_configured。")

    runtime_path = project / "config/python-runtime.json"
    if runtime_path.is_file():
        text = runtime_path.read_text(encoding="utf-8-sig", errors="replace")
        placeholders = sorted(token for token in PLACEHOLDERS if token in text)
        if placeholders:
            add("python_runtime_pinned", "failed", "Python 安装配置仍含占位符。", "替换为经核验的固定版本、URL 与 SHA-256。", placeholders)
        else:
            try:
                runtime = json.loads(text)
                items = [runtime.get("windows", {}), runtime.get("macos", {})]
                policy = runtime.get("policy", {})
                valid_items = all(
                    Path(str(item.get("installer_file", ""))).name == str(item.get("installer_file", ""))
                    and item.get("source_host") == "www.python.org"
                    and item.get("manual_install_only") is True
                    and re.fullmatch(r"[0-9a-fA-F]{64}", str(item.get("sha256", "")))
                    for item in items
                )
                safe_policy = all(policy.get(key) is False for key in ["allow_network_download", "allow_process_launch", "allow_admin_install"])
                valid = runtime.get("mode") == "verify-only" and valid_items and safe_policy
                add("python_runtime_pinned", "passed" if valid else "failed", "Python 安装包仅做离线验证，不自动下载、运行或提权。" if valid else "Python 运行时验证策略不完整。", "使用 verify-only、预置安装包、固定 SHA-256 和官方签名。")
            except json.JSONDecodeError as exc:
                add("python_runtime_pinned", "failed", "Python 运行时配置文件格式有误，请重新生成 config/python-runtime.json", "修复配置。")
    else:
        add("python_runtime_pinned", "failed", "缺少 Python 运行时配置。", "生成 config/python-runtime.json。")

    offline_manifest = project / "offline-wheels/OFFLINE_MANIFEST.json"
    if offline_manifest.is_file():
        try:
            data = json.loads(offline_manifest.read_text(encoding="utf-8-sig"))
            wheels = data.get("wheels", [])
            valid = bool(wheels) and all(isinstance(item, dict) and re.fullmatch(r"[0-9a-fA-F]{64}", str(item.get("sha256", ""))) for item in wheels)
            add("offline_dependencies", "passed" if valid else "failed", "离线依赖清单和哈希已准备。" if valid else "离线依赖清单为空或哈希不完整。", "重新准备离线 wheels 并生成哈希清单。")
        except (OSError, json.JSONDecodeError) as exc:
            add("offline_dependencies", "failed", "离线依赖清单文件格式有误，请重新运行 prepare_offline_dependencies.py", "重新生成清单。")
    else:
        add("offline_dependencies", "needs_confirmation", "未发现完整离线依赖清单。", "需要纯离线部署时，先运行离线依赖准备脚本。")

    external_urls: list[dict[str, str]] = []
    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_EXTENSIONS or any(part in {".venv", "__pycache__", "node_modules"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for url in URL_RE.findall(text):
            host = (urlparse(url).hostname or "").casefold()
            relative = path.relative_to(project).as_posix()
            if host in ALLOWED_RUNTIME_HOSTS and relative.endswith("python-runtime.json"):
                continue
            external_urls.append({"file": relative, "url": url[:240]})
    add("external_runtime_resources", "passed" if not external_urls else "needs_confirmation", "未发现默认运行依赖的外部 URL。" if not external_urls else f"发现 {len(external_urls)} 个外部 URL，需区分安装来源、文档链接和运行依赖。", "移除 CDN、在线字体、在线图标或未配置接口；合法安装来源单独记录。", external_urls[:20])

    failed = [item for item in checks if item["status"] == "failed"]
    pending = [item for item in checks if item["status"] == "needs_confirmation"]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "failed" if failed else "needs_confirmation" if pending else "ready",
        "legal_notice": "本报告是技术准备度检查，不构成法律、税务、会计或电子签名合规意见。",
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "passed" for item in checks), "failed": len(failed), "needs_confirmation": len(pending)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查国内部署准备度")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--out", default="DOMESTIC_READINESS.json")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    result = check_domestic_readiness(project)
    output = project / args.out
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"ready", "needs_confirmation"} else 2


if __name__ == "__main__":
    sys.exit(main())
