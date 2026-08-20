"""端到端入口点测试（v9.0 改造：0 断言打印脚本 → 真 test_* 函数 + assert）"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _run_entry(args):
    r = subprocess.run([sys.executable, '-m', 'fund_advisor'] + args,
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', cwd=str(ROOT))
    return r


def test_version_command():
    r = _run_entry(['version'])
    assert r.returncode == 0
    assert r.stdout.strip() or r.stderr.strip(), "version 命令无输出"


def test_help_command():
    r = _run_entry(['--help'])
    assert r.returncode == 0
    assert 'check' in r.stdout or 'mcp' in r.stdout or 'usage' in r.stdout.lower()


def test_bootstrap_run_check_returns_bool():
    sys.path.insert(0, str(ROOT))
    from fund_advisor.fund_advisor_bootstrap import run_check
    ok = run_check(verbose=False)
    assert isinstance(ok, bool)


def test_mcp_tool_callable():
    sys.path.insert(0, str(ROOT))
    import mcp_server
    out = mcp_server.list_clients()
    assert isinstance(out, str)


def test_mcp_tools_registered():
    sys.path.insert(0, str(ROOT))
    import mcp_server
    if hasattr(mcp_server, 'server') and hasattr(mcp_server.server, '_tool_manager'):
        tools = list(mcp_server.server._tool_manager._tools.keys())
        assert len(tools) >= 30, f"MCP 工具数不足: {len(tools)}"


def test_core_files_exist():
    for f in ['README.md', 'SKILL.md', 'pytest.ini', 'pyproject.toml', 'mcp_server.py']:
        assert (ROOT / f).exists(), f"缺 {f}"
