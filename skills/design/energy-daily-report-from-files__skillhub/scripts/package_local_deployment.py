#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a clean single-root local deployment ZIP with full sources and user-facing navigation."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from validate_full_lan_delivery import validate

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", ".venv_windows", "build"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log", ".pid", ".db-shm", ".db-wal"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_include(path: Path, project: Path, include_dist: bool) -> bool:
    rel = path.relative_to(project)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if not include_dist and "dist" in rel.parts:
        return False
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    return path.is_file()


def _built_exes(staged: Path) -> list[str]:
    dist = staged / "01_服务端_完整程序" / "dist"
    if not dist.is_dir():
        return []
    return sorted(p.relative_to(staged).as_posix() for p in dist.rglob("*.exe") if p.is_file())


def _write_navigation(staged: Path, status: dict) -> None:
    exe_line = (
        "本包包含 Windows EXE 文件；是否经过 Windows 真机启动验证仍以 DELIVERY_STATUS.json 为准。"
        if status["built_exe_included"]
        else "本包未包含已构建 EXE；已提供 EXE 构建源码。脚本模式需要 Python 3.10+，也可由 IT 在 Windows 上构建 EXE。"
    )
    text = f"""# 能源日报系统交付导航

这个 ZIP 的主系统是**浏览器 Web 局域网系统**。第一次使用不要翻全部文件。

## 普通用户：只做三件事

1. 启动：双击根目录 `一键启动_Windows.bat`。
2. 打开：按启动后生成/更新的“当前服务器地址”在浏览器访问。
3. 结束：双击根目录 `一键停止_Windows.bat`，不要直接结束所有 Python 进程。

{exe_line}

如果启动失败，先看启动窗口/日志，再联系 IT；不要关闭整机防火墙或绕过企业安全策略。

## IT / 运维

- 部署说明：`01_服务端_完整程序/README_部署说明.txt`
- 启动与端口：`launcher.py`、`port_config.py`、`stop_server.py`
- 数据目录：`01_服务端_完整程序/data/`
- 备份恢复：`01_服务端_完整程序/backup_restore.py`
- EXE 构建：`build_exe_windows.py`、`energy_daily_report_exe.spec`
- 交付状态：`DELIVERY_STATUS.json`
- 全文件哈希：`FILES_SHA256.txt`

备份示例：

```text
cd 01_服务端_完整程序
python backup_restore.py backup
```

恢复前先停止服务，再按备份文件运行：

```text
python backup_restore.py restore <备份.sqlite3> --confirm-server-stopped
```

## 开发人员

优先看第一方代码：

- `server.py`：Web/API 路由
- `backend_core.py`：数据库、权限、计算、导出
- `energy_excel_import.py`：Excel 导入
- `backup_restore.py`：数据库备份/恢复
- `templates/`：页面
- `static/`：前端样式与交互
- `exe_entry.py` + `build_exe_windows.py`：EXE 入口/构建

`vendor/` 是第三方离线依赖源码，普通用户和大多数开发排查都不需要逐个阅读。

## 如何确认交付状态

`DELIVERY_STATUS.json` 只记录事实：是否包含源码、是否包含 EXE 二进制、是否完成 Windows 真机验证。存在构建脚本不等于已有 EXE。

`PY_SOURCE_MANIFEST.json` 将第一方源码与 `vendor/` 分开统计。当前第一方 Python 源码数：{status['first_party_python_source_count']}；第三方 vendor Python 源码数：{status['third_party_vendor_python_source_count']}。
"""
    (staged / "00_请先看_交付导航.md").write_text(text, encoding="utf-8")


def package(project: Path, output_zip: Path, *, root_name: str | None = None, include_dist: bool = False) -> dict:
    project = project.resolve()
    check = validate(project)
    if not check["ok"]:
        return {"ok": False, "code": "FULL_LAN_VALIDATION_FAILED", "errors": check["errors"]}

    root_name = (root_name or project.name).strip() or "能源日报系统_本地部署包"
    output_zip = output_zip.resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / root_name
        shutil.copytree(project, staged, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".venv", ".venv_windows", "*.pyc", "*.pyo"))
        if not include_dist:
            shutil.rmtree(staged / "01_服务端_完整程序" / "dist", ignore_errors=True)
            shutil.rmtree(staged / "01_服务端_完整程序" / "build", ignore_errors=True)

        py_sources = sorted(p for p in staged.rglob("*.py") if "__pycache__" not in p.parts)
        first_party = []
        third_party = []
        for p in py_sources:
            rel = p.relative_to(staged).as_posix()
            item = {"path": rel, "sha256": sha256(p), "bytes": p.stat().st_size}
            if "/vendor/" in f"/{rel}/":
                third_party.append(item)
            else:
                first_party.append(item)
        source_manifest = {
            "schema_version": "1.1",
            "python_source_count": len(py_sources),
            "first_party_python_source_count": len(first_party),
            "third_party_vendor_python_source_count": len(third_party),
            "note": "完整 Python 源码已保留；普通用户通常只需查看 first_party_sources，vendor 为第三方离线依赖源码。",
            "first_party_sources": first_party,
            "third_party_vendor_sources": third_party,
        }
        (staged / "PY_SOURCE_MANIFEST.json").write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        built_exes = _built_exes(staged) if include_dist else []
        status = {
            "schema_version": "1.0",
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "primary_ui": "responsive_web",
            "optional_tkinter_is_primary_ui": False,
            "full_python_source_included": True,
            "first_party_python_source_count": len(first_party),
            "third_party_vendor_python_source_count": len(third_party),
            "backup_restore_tool": "01_服务端_完整程序/backup_restore.py",
            "backup_restore_self_test": check.get("checks", {}).get("backup_restore_self_test", "not_run"),
            "exe_build_source_included": True,
            "built_exe_included": bool(built_exes),
            "built_exe_files": built_exes,
            "windows_exe_runtime_verified": False,
            "windows_exe_runtime_note": "仅当有 Windows 真机构建与启动证据时才能改为 true；静态检查或存在 EXE 文件都不能代替真机验证。",
            "script_mode_requires_python": not bool(built_exes),
        }
        (staged / "DELIVERY_STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_navigation(staged, status)

        manifest_lines: list[str] = []
        files = sorted(p for p in staged.rglob("*") if p.is_file())
        for p in files:
            rel = p.relative_to(staged).as_posix()
            if rel == "FILES_SHA256.txt":
                continue
            manifest_lines.append(f"{sha256(p)}  {rel}")
        (staged / "FILES_SHA256.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        if output_zip.exists():
            output_zip.unlink()
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for p in sorted(staged.rglob("*")):
                if p.is_file():
                    arc = Path(root_name) / p.relative_to(staged)
                    zf.write(p, arc.as_posix())

    return {
        "ok": True,
        "zip": str(output_zip),
        "zip_sha256": sha256(output_zip),
        "python_source_count": check["python_source_count"],
        "first_party_python_source_count": check["first_party_python_source_count"],
        "third_party_vendor_python_source_count": check["third_party_vendor_python_source_count"],
        "includes_exe_build_source": True,
        "includes_built_exe": bool(built_exes),
        "backup_restore_self_test": check.get("checks", {}).get("backup_restore_self_test", "not_run"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成完整本地部署 ZIP")
    parser.add_argument("project_dir")
    parser.add_argument("output_zip")
    parser.add_argument("--root-name", default=None)
    parser.add_argument("--include-dist", action="store_true", help="仅在已有 Windows 构建产物时纳入 dist；不代表已完成真机运行验证")
    args = parser.parse_args()
    result = package(Path(args.project_dir), Path(args.output_zip), root_name=args.root_name, include_dist=args.include_dist)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
