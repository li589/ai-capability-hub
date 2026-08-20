"""test_bootstrap.py — 验证 fund_advisor_bootstrap 自检与安装"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Bootstrap 模块在 fund_advisor/ 子包中
from fund_advisor.fund_advisor_bootstrap import (
    run_check, _check_python, _check_data
)


def test_python_check_passes():
    ok, msg = _check_python()
    assert ok, f"Python check failed: {msg}"
    assert "Python" in msg


def test_data_check_returns_list():
    """_check_data 返回清单（v10: 四元组含阻塞标记）"""
    results = _check_data()
    assert isinstance(results, list)
    for row in results:
        fname, ok, note = row[0], row[1], row[2]
        blocking = row[3] if len(row) > 3 else True
        assert isinstance(fname, str)
        assert isinstance(ok, bool)
        assert isinstance(note, str)
        assert isinstance(blocking, bool)


def test_data_check_marks_placeholder_as_uninitialized(monkeypatch, tmp_path):
    """v9.0: 占位骨架标 TOO SMALL、真实数据标 OK（合成目录，不依赖仓库占位态）。"""
    import fund_advisor.fund_advisor_bootstrap as bootstrap
    # 小文件（占位骨架，远小于阈值 KB）
    for fname in ("fund_products.json", "fund_managers_distilled.json",
                  "holdings_database.json"):
        (tmp_path / fname).write_text('{"_f":[],"c":[],"m":{}}', encoding="utf-8")
    # style_profiles 阈值 1KB → 合成 2KB 应 OK
    (tmp_path / "style_profiles.json").write_text('x' * 2048, encoding="utf-8")
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)

    results = bootstrap._check_data()
    flags = {r[0]: r[1] for r in results}
    for big in ("fund_products.json", "fund_managers_distilled.json",
                "holdings_database.json"):
        assert flags.get(big) is False, f"{big} 小文件应 TOO SMALL"
    assert flags.get("style_profiles.json") is True, "2KB 文件应 OK"


def test_run_check_returns_bool():
    ok = run_check(verbose=False)
    assert isinstance(ok, bool)


