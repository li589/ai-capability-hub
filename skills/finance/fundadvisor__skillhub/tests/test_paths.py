"""test_paths.py — scripts/fund_advisor_paths.py 测试"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fund_advisor_paths as fap


def test_base_dir_resolves():
    """BASE_DIR 应指向 skill 根目录"""
    assert (fap.BASE_DIR / "SKILL.md").exists(), \
        f"BASE_DIR={fap.BASE_DIR} 不含 SKILL.md"


def test_data_dir_resolves():
    """DATA_DIR 应含真实数据文件"""
    assert fap.DATA_DIR.exists()
    assert (fap.DATA_DIR / "fund_managers_distilled.json").exists(), \
        "fund_managers_distilled.json not found in DATA_DIR"


def test_assets_dir_exists():
    assert fap.ASSETS_DIR.exists()


def test_references_dir_exists():
    assert fap.REFERENCES_DIR.exists()


def test_ensure_dirs_idempotent():
    """ensure_dirs 多次调用不应抛异常"""
    fap.ensure_dirs()
    fap.ensure_dirs()
    assert fap.CLIENTS_DIR.exists()


def test_relative_to_skill():
    """relative_to_skill 应返回相对路径"""
    rel = fap.relative_to_skill(fap.DATA_DIR / "foo.json")
    assert rel is not None
    # Windows 路径分隔符兼容
    assert rel.as_posix().endswith("data/foo.json")


def test_relative_to_skill_outside():
    """路径在 skill 外应返回 None"""
    outside = Path("Z:/completely/different/path.json")
    rel = fap.relative_to_skill(outside)
    assert rel is None


def test_env_override(monkeypatch, tmp_path):
    """环境变量 FUND_ADVISOR_BASE_DIR 应覆盖默认推断"""
    monkeypatch.setenv("FUND_ADVISOR_BASE_DIR", str(tmp_path))
    # 重新跑推断逻辑
    import importlib
    importlib.reload(fap)
    try:
        assert fap.BASE_DIR == tmp_path.resolve()
    finally:
        # 恢复
        monkeypatch.delenv("FUND_ADVISOR_BASE_DIR", raising=False)
        importlib.reload(fap)
