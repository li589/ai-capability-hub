"""v2.2.0 友好错误消息测试。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from friendly_errors import friendly_error


def test_jieba_missing():
    e = ModuleNotFoundError("No module named 'jieba'")
    result = friendly_error(e)
    assert "jieba" in result
    assert "pip install jieba" in result
    print(f"  ✓ jieba 缺失提示正确")


def test_flask_missing():
    e = ModuleNotFoundError("No module named 'flask'")
    result = friendly_error(e)
    assert "flask" in result
    assert "Web" in result or "可选" in result
    print(f"  ✓ flask 缺失提示正确")


def test_file_not_found():
    e = FileNotFoundError("chat.txt not found")
    result = friendly_error(e)
    assert "文件未找到" in result
    print(f"  ✓ 文件未找到提示正确")


def test_permission_denied():
    e = PermissionError("Permission denied: 'output/x.html'")
    result = friendly_error(e)
    assert "权限" in result or "占用" in result
    print(f"  ✓ 权限错误提示正确")


def test_unicode_error():
    e = UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte")
    result = friendly_error(e)
    assert "编码" in result
    print(f"  ✓ 编码错误提示正确")


def test_unknown_error():
    class WeirdError(Exception):
        pass
    e = WeirdError("some super weird failure 12345")
    result = friendly_error(e)
    assert "未知错误" in result or "WeirdError" in result
    assert "doctor" in result
    print(f"  ✓ 未知错误提示也有用")


def test_keyboard_interrupt():
    e = KeyboardInterrupt()
    result = friendly_error(e)
    assert "Ctrl+C" in result or "取消" in result
    print(f"  ✓ Ctrl+C 提示正确")


def test_results_no_traceback_exposure():
    """友好提示不应向用户暴露完整 traceback。"""
    e = ModuleNotFoundError("No module named 'jieba'")
    result = friendly_error(e)
    # 不应包含 "Traceback" 或 frame 信息
    assert "Traceback" not in result
    assert "site-packages" not in result
    print(f"  ✓ 不暴露 traceback")


# ----------------------------------------------------------------
# v2.5.0 新增：可选依赖模式 + JSON 遮蔽修复
# ----------------------------------------------------------------

def test_docx_missing():
    e = ModuleNotFoundError("No module named 'docx'")
    result = friendly_error(e)
    assert "docx" in result
    assert "pip install python-docx" in result
    print(f"  ✓ docx 缺失提示正确")


def test_pptx_missing():
    e = ModuleNotFoundError("No module named 'pptx'")
    result = friendly_error(e)
    assert "python-pptx" in result
    print(f"  ✓ pptx 缺失提示正确")


def test_openpyxl_missing():
    e = ModuleNotFoundError("No module named 'openpyxl'")
    result = friendly_error(e)
    assert "openpyxl" in result
    print(f"  ✓ openpyxl 缺失提示正确")


def test_jinja2_missing():
    e = ModuleNotFoundError("No module named 'jinja2'")
    result = friendly_error(e)
    assert "jinja2" in result
    print(f"  ✓ jinja2 缺失提示正确")


def test_jsondecodeerror_is_cache_corruption():
    """v2.5.0 bugfix：JSONDecodeError 曾命中前一条 'Expecting value' 模式，
    '缓存文件损坏' 条目永远不可达。现在按异常类型名优先匹配。"""
    import json
    e = json.decoder.JSONDecodeError("Expecting value: line 1 column 1 (char 0)", "x.json", 0)
    result = friendly_error(e)
    assert "缓存" in result or "损坏" in result, f"应命中缓存损坏条目: {result}"
    print(f"  ✓ JSONDecodeError 命中缓存损坏条目")


def test_unknown_json_like_error():
    """非 JSONDecodeError 的 'Expecting value' 文本仍命中 JSON 解析失败条目"""
    e = ValueError("Expecting value: line 1 column 1 (char 0)")
    result = friendly_error(e)
    assert "JSON" in result
    print(f"  ✓ 通用 JSON 解析失败提示正确")


def main():
    tests = [
        (name, obj)
        for name, obj in globals().items()
        if name.startswith("test_") and callable(obj)
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}\n友好错误测试: {passed} 通过, {failed} 失败\n{'='*60}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
