#!/usr/bin/env python3
"""静态验收业务系统交付目录，不执行其中的任何代码。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
URL_RE = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|FIXME|LOREM\s+IPSUM)\b|仅供展示|空壳页面|mock\s*api",
    re.IGNORECASE,
)
SECRET_PATTERNS = {
    "疑似 OpenAI 密钥": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "疑似 AWS 访问密钥": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "私钥内容": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SCAN_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".env",
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
}
SKIP_PARTS = {"vendor", "node_modules", ".git", "dist", "build", "__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(raw: str) -> bool:
    if not raw or "\\" in raw or ":" in raw:
        return False
    parsed = PurePosixPath(raw)
    return not parsed.is_absolute() and ".." not in parsed.parts and "." not in parsed.parts


def is_local_or_private_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return True
    if host.startswith("10.") or host.startswith("192.168."):
        return True
    if host.startswith("172."):
        try:
            second = int(host.split(".")[1])
            return 16 <= second <= 31
        except (IndexError, ValueError):
            return False
    return host.endswith(".local") or host.endswith(".lan")


def text_for_scan(path: Path) -> str | None:
    if path.suffix.lower() not in SCAN_EXTENSIONS or path.stat().st_size > 2 * 1024 * 1024:
        return None
    if any(part in SKIP_PARTS for part in path.parts):
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


class Findings:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def error(self, code: str, message: str) -> None:
        self.errors.append({"code": code, "message": message})

    def warning(self, code: str, message: str) -> None:
        self.warnings.append({"code": code, "message": message})


def require_mapping(value: Any, label: str, findings: Findings) -> dict[str, Any]:
    if not isinstance(value, dict):
        findings.error("PB401", f"{label} 必须是对象。")
        return {}
    return value


def require_nonempty_list(value: Any, label: str, findings: Findings) -> list[Any]:
    if not isinstance(value, list) or not value:
        findings.error("PB401", f"{label} 必须是非空数组。")
        return []
    return value


def validate_manifest(project: Path, manifest: dict[str, Any], strict: bool) -> Findings:
    findings = Findings()

    if manifest.get("schema_version") != "1.0":
        findings.error("PB401", "delivery-manifest.json 的 schema_version 必须为 1.0。")

    system = require_mapping(manifest.get("system"), "system", findings)
    for field in ("name", "version", "locale", "timezone", "network_mode"):
        if not str(system.get(field, "")).strip():
            findings.error("PB401", f"system.{field} 不能为空。")
    if system.get("version") and not SEMVER_RE.fullmatch(str(system["version"])):
        findings.error("PB401", f"system.version 不是语义版本：{system['version']}")
    if system.get("locale") != "zh-CN":
        findings.warning("PB401", "system.locale 不是 zh-CN，请确认是否符合中文交付要求。")
    if system.get("timezone") != "Asia/Shanghai":
        findings.warning("PB401", "system.timezone 不是 Asia/Shanghai，请确认业务时区。")
    if system.get("network_mode") not in {"offline", "lan", "online_optional"}:
        findings.error("PB401", "system.network_mode 必须为 offline、lan 或 online_optional。")

    source_files = require_nonempty_list(manifest.get("source_files"), "source_files", findings)
    for index, item in enumerate(source_files):
        if not isinstance(item, dict):
            findings.error("PB401", f"source_files[{index}] 必须是对象。")
            continue
        if not str(item.get("name", "")).strip():
            findings.error("PB401", f"source_files[{index}].name 不能为空。")
        if not SHA256_RE.fullmatch(str(item.get("sha256", ""))):
            findings.error("PB401", f"source_files[{index}].sha256 必须是实际的 64 位 SHA-256。")

    starts = require_mapping(manifest.get("start_commands"), "start_commands", findings)
    if not any(str(value).strip() for value in starts.values()):
        findings.error("PB401", "start_commands 至少提供一个非空启动命令。")

    require_nonempty_list(manifest.get("modules"), "modules", findings)
    require_nonempty_list(manifest.get("roles"), "roles", findings)

    security = require_mapping(manifest.get("security"), "security", findings)
    for flag in ("rbac", "audit_log", "csrf", "no_cdn"):
        if security.get(flag) is not True:
            findings.error("PB301", f"security.{flag} 必须明确为 true。")
    password_hash = str(security.get("password_hash", "")).lower()
    if not any(name in password_hash for name in ("argon2", "scrypt", "pbkdf2")):
        findings.error("PB301", "security.password_hash 必须使用 Argon2、scrypt 或 PBKDF2。")

    tests = require_mapping(manifest.get("tests"), "tests", findings)
    if tests.get("status") != "passed":
        findings.error("PB401", "tests.status 必须为 passed；未运行和失败不能写成通过。")
    for field in ("command", "executed_at"):
        if not str(tests.get(field, "")).strip():
            findings.error("PB401", f"tests.{field} 不能为空。")

    if "known_limitations" not in manifest or not isinstance(manifest.get("known_limitations"), list):
        findings.error("PB401", "known_limitations 必须存在且为数组，允许为空数组。")

    listed_files = require_nonempty_list(manifest.get("files"), "files", findings)
    for index, item in enumerate(listed_files):
        if not isinstance(item, dict):
            findings.error("PB401", f"files[{index}] 必须是对象。")
            continue
        raw_path = str(item.get("path", ""))
        expected_hash = str(item.get("sha256", ""))
        if not safe_relative_path(raw_path):
            findings.error("PB301", f"files[{index}].path 不是安全相对路径：{raw_path!r}")
            continue
        file_path = project.joinpath(*PurePosixPath(raw_path).parts)
        try:
            resolved = file_path.resolve()
            resolved.relative_to(project.resolve())
        except (OSError, ValueError):
            findings.error("PB301", f"交付文件越过项目目录：{raw_path}")
            continue
        if not file_path.is_file():
            findings.error("PB401", f"清单中的交付文件不存在：{raw_path}")
            continue
        if not SHA256_RE.fullmatch(expected_hash):
            findings.error("PB401", f"{raw_path} 的 sha256 不是 64 位小写十六进制。")
        else:
            actual = sha256_file(file_path)
            if actual != expected_hash:
                findings.error("PB401", f"{raw_path} 的实际哈希与清单不一致。")

    offline = system.get("network_mode") == "offline"
    for path in project.rglob("*"):
        if not path.is_file() or path.name == "delivery-manifest.json":
            continue
        try:
            text = text_for_scan(path)
        except OSError as exc:
            findings.warning("PB401", f"无法静态读取 {path.relative_to(project)}：{exc}")
            continue
        if text is None:
            continue
        relative = str(path.relative_to(project)).replace("\\", "/")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.error("PB301", f"{relative} 中发现{label}。")
        if PLACEHOLDER_RE.search(text) and not any(part in {"tests", "examples"} for part in path.parts):
            message = f"{relative} 中存在 TODO、演示占位或 mock 标记。"
            findings.error("PB401", message) if strict else findings.warning("PB401", message)
        if offline:
            external_urls = [url for url in URL_RE.findall(text) if not is_local_or_private_url(url)]
            if external_urls:
                message = f"离线项目 {relative} 中发现外部 URL：{external_urls[0][:120]}"
                findings.error("PB201", message) if strict else findings.warning("PB201", message)

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="静态验收业务系统交付目录。")
    parser.add_argument("project", help="系统项目目录")
    parser.add_argument("--strict", action="store_true", help="把占位内容和离线外链作为阻断项")
    parser.add_argument("--json-report", help="可选的 JSON 检查报告路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).expanduser()
    if not project.is_dir():
        print("[PB001] 系统项目目录不存在")
        print("处理：选择包含 delivery-manifest.json 的项目目录。")
        return 1
    manifest_path = project / "delivery-manifest.json"
    if not manifest_path.is_file():
        print("[PB401] 缺少 delivery-manifest.json")
        print("处理：按验收清单生成交付清单后重新运行。")
        print("恢复点：交付验收。")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("根节点必须是 JSON 对象")
        findings = validate_manifest(project, manifest, args.strict)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[PB401] 无法读取交付清单：{exc}")
        return 1

    report = {
        "project": str(project.resolve()),
        "strict": args.strict,
        "passed": not findings.errors,
        "errors": findings.errors,
        "warnings": findings.warnings,
    }
    if args.json_report:
        report_path = Path(args.json_report).expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if findings.errors:
        print(f"[未通过] 发现 {len(findings.errors)} 个阻断项、{len(findings.warnings)} 个警告。")
        for item in findings.errors:
            print(f"- [{item['code']}] {item['message']}")
        for item in findings.warnings:
            print(f"- [警告/{item['code']}] {item['message']}")
        print("处理：修复阻断项后重新运行；不要在失败时宣称完整交付。")
        print("恢复点：交付验收。")
        return 1

    print(f"[通过] 交付静态验收通过；警告 {len(findings.warnings)} 个。")
    for item in findings.warnings:
        print(f"- [警告/{item['code']}] {item['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
