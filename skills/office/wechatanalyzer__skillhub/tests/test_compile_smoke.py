"""test_compile_smoke.py — 全覆盖编译烟囱测试（v2.8.0 新增）

任何 SyntaxError / 非法转义序列都会让模块导入失败或产生弃用警告。
本测试自动扫描全部 .py 文件做编译校验，并把警告升级为错误，
根治"手工导入清单漏覆盖"的盲区。
"""
import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _all_python_files():
    skip_dirs = {"__pycache__", ".git", ".pytest_cache", "data"}
    for path in ROOT.rglob("*.py"):
        if any(part in skip_dirs for part in path.parts):
            continue
        yield path


def test_all_modules_compile_without_warnings():
    """所有 .py 文件必须可编译，且无 SyntaxWarning/DeprecationWarning（如非法转义）"""
    failures = []
    count = 0
    for path in _all_python_files():
        count += 1
        try:
            source = path.read_text(encoding="utf-8")
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                compile(source, str(path), "exec")
        except Exception as e:  # noqa: BLE001 - 汇总所有失败一次性报告
            failures.append(f"{path.relative_to(ROOT)}: {e.__class__.__name__}: {e}")
    assert count > 50, f"扫描到的 .py 文件数量异常：{count}"
    assert not failures, "以下文件编译失败或有语法警告：\n" + "\n".join(failures)


def test_no_bare_except_in_active_code():
    """活跃代码禁止裸 except（会吞掉 KeyboardInterrupt/SystemExit）

    archive_v1 为历史归档，不在约束范围内。
    """
    pattern = re.compile(r"^\s*except\s*:", re.MULTILINE)
    offenders = []
    for path in _all_python_files():
        if "archive_v1" in path.parts:
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "以下文件存在裸 except：" + "; ".join(offenders)


def test_version_single_source_consistent():
    """版本号单一来源：core/version.py 与 config.json / SKILL.md frontmatter 一致"""
    import json
    sys.path.insert(0, str(ROOT))
    try:
        from core.version import __version__
        cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        assert cfg.get("version") == __version__, \
            f"config.json={cfg.get('version')} != core.version={__version__}"
        fm = (ROOT / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        m = re.search(r"^version:\s*([\d.]+)", fm, re.MULTILINE)
        assert m and m.group(1) == __version__, \
            f"SKILL.md frontmatter={m.group(1) if m else None} != core.version={__version__}"
    finally:
        sys.path.remove(str(ROOT))
