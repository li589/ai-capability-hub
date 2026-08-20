#!/usr/bin/env python3
"""Inspect local optional dependencies without installing or changing anything."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Callable


PYTHON_MODULES = {
    "PIL": "marketing-image",
    "docx": "docx",
    "yaml": "structured-config",
    "pypdf": "pdf-processing",
}

FULL_ARTIFACTS = [
    "markdown", "docx", "pdf", "mermaid-source", "mermaid-svg",
    "mermaid-png", "report-cover", "recruitment-poster", "social-square",
]
DEGRADED_ARTIFACTS = [
    "markdown", "mermaid-source", "diagram-tables", "marketing-copy",
    "visual-briefs",
]


def _first_existing(candidates: list[str], path_exists: Callable[[str], bool]) -> str:
    return next((candidate for candidate in candidates if candidate and path_exists(candidate)), "")


def inspect_dependencies(
    *,
    which: Callable[[str], str | None] = shutil.which,
    find_spec: Callable[[str], object | None] = importlib.util.find_spec,
    platform_name: str = sys.platform,
    env: dict[str, str] | os._Environ[str] = os.environ,
    path_exists: Callable[[str], bool] = os.path.exists,
    scripts_dir: Path | None = None,
) -> dict:
    scripts = scripts_dir or Path(__file__).resolve().parent
    python_path = which("python3") or which("python")
    missing_core = [] if python_path else ["python3"]
    missing_optional: list[str] = []
    detected: dict[str, object] = {"python": python_path or ""}

    missing_modules = [name for name in PYTHON_MODULES if find_spec(name) is None]
    detected["python_modules"] = {
        name: name not in missing_modules for name in PYTHON_MODULES
    }
    for module in missing_modules:
        capability = PYTHON_MODULES[module]
        if capability not in missing_optional:
            missing_optional.append(capability)

    node_path = which("node")
    cli_path = scripts / "node_modules" / "@mermaid-js" / "mermaid-cli" / "src" / "cli.js"
    browsers = [
        env.get("PUPPETEER_EXECUTABLE_PATH", ""),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    ]
    browser_path = _first_existing(browsers, path_exists)
    detected.update({
        "node": node_path or "",
        "mermaid_cli": str(cli_path) if path_exists(str(cli_path)) else "",
        "browser": browser_path,
    })
    if not node_path or not path_exists(str(cli_path)) or not browser_path:
        missing_optional.append("mermaid-render")

    soffice = which("soffice") or which("libreoffice")
    pdftoppm = which("pdftoppm")
    detected.update({"libreoffice": soffice or "", "pdftoppm": pdftoppm or ""})
    if not soffice or "docx" in missing_optional:
        if "docx" not in missing_optional:
            missing_optional.append("docx")
    if not soffice or not pdftoppm or "pdf-processing" in missing_optional:
        if "pdf" not in missing_optional:
            missing_optional.append("pdf")

    fonts = [
        "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    font_path = _first_existing(fonts, path_exists)
    detected["cjk_font"] = font_path
    if not font_path or "marketing-image" in missing_optional:
        if "marketing-image" not in missing_optional:
            missing_optional.append("marketing-image")

    missing_optional = sorted(set(missing_optional))
    report = {
        "schema_version": "1.0",
        "platform": platform_name,
        "core_ready": not missing_core,
        "full_ready": not missing_core and not missing_optional,
        "missing_core": missing_core,
        "missing_optional": missing_optional,
        "detected": detected,
        "full_artifacts": FULL_ARTIFACTS,
        "degraded_artifacts": DEGRADED_ARTIFACTS,
        "install_commands": [
            "python -m pip install -r scripts/requirements.txt",
            "pnpm --dir scripts install --frozen-lockfile",
        ],
    }
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    report["report_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    report = inspect_dependencies()
    print(json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2))
    raise SystemExit(0 if report["core_ready"] else 2)


if __name__ == "__main__":
    main()
