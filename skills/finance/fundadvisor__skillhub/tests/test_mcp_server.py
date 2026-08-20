"""test_mcp_server.py — 验证 mcp_server.py 工具注册与可调用"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _require_server():
    """mcp 包未安装时优雅跳过（mcp_server 设计上支持无 mcp 降级）"""
    import mcp_server
    if not hasattr(mcp_server, 'server'):
        pytest.skip("mcp 包未安装，server 对象不可用（优雅降级模式）")
    return mcp_server


def test_mcp_module_imports():
    """mcp_server 应当能干净地 import，不抛异常"""
    import mcp_server
    assert mcp_server is not None


def test_mcp_server_has_server():
    """mcp_server 应当暴露 server 对象（FastMCP 实例）"""
    mcp_server = _require_server()
    assert hasattr(mcp_server, 'server')


def test_mcp_tools_registered():
    """v9.0: MCP server 应注册 TOOL_COUNT 个工具（用常量，避免魔法数）"""
    mcp_server = _require_server()
    expected = getattr(mcp_server, 'TOOL_COUNT', 36)
    tools = list(mcp_server.server._tool_manager._tools.keys())
    assert len(tools) == expected, f"应注册 {expected} 个工具，实际 {len(tools)}"


def test_mcp_expected_tools():
    """MCP 工具名应与 SKILL.md / README 一致"""
    mcp_server = _require_server()
    tools = set(mcp_server.server._tool_manager._tools.keys())
    expected = {
        "import_holdings_screenshot", "import_holdings_docx", "import_holdings_pdf",
        "import_holdings_url", "export_holdings_excel", "export_holdings_csv",
        "list_clients", "get_client_holdings", "get_import_history",
        "auto_import_file",
        "query_fund", "query_manager",
        "get_advisor_report", "compare_managers",
        # v10.0 新增 12 工具
        "chat_with_manager", "get_manager_persona", "get_manager_news",
        "compare_holdings_change", "build_mirror_portfolio",
        "track_mirror_portfolio", "get_follow_signals",
        "assess_client_profile", "get_client_communication_guide",
        "generate_custom_report", "generate_batch_reports", "chat_with_client",
    }
    missing = expected - tools
    assert not missing, f"缺少工具: {missing}"


def test_v10_new_tools_callable(tmp_path, monkeypatch):
    """v10.0 新工具函数应能直接调用且返回字符串（占位数据下不崩溃）。

    v10.0.1: 报告类工具（generate_custom_report/batch）会写盘，隔离到临时目录，
    避免污染真实 data/（此前产生 data/reports/测试客户*.json 残留）。
    """
    import client_manager.report_generator as rg
    import client_manager.report_scheduler as rs
    monkeypatch.setattr(rg, "DATA_DIR", tmp_path)
    monkeypatch.setattr(rs, "DATA_DIR", tmp_path)
    import mcp_server
    assert isinstance(mcp_server.chat_with_manager("不存在的经理", "你好"), str)
    assert isinstance(mcp_server.get_manager_persona("不存在的经理"), str)
    assert isinstance(mcp_server.get_manager_news("不存在的经理"), str)
    assert isinstance(mcp_server.compare_holdings_change("999999"), str)
    assert isinstance(mcp_server.build_mirror_portfolio("999999"), str)
    assert isinstance(mcp_server.track_mirror_portfolio("999999"), str)
    assert isinstance(mcp_server.get_follow_signals(""), str)
    assert isinstance(mcp_server.assess_client_profile("测试客户"), str)
    assert isinstance(mcp_server.get_client_communication_guide("测试客户"), str)
    assert isinstance(mcp_server.generate_custom_report("测试客户", "weekly"), str)
    assert isinstance(mcp_server.generate_batch_reports("测试客户1,测试客户2"), str)
    assert isinstance(mcp_server.chat_with_client("测试客户", "你好"), str)
    # 隔离验证：报告写入 tmp_path，真实 data/ 无残留
    assert (tmp_path / "reports").exists(), "报告应写入 tmp_path"
    real_data = ROOT / "data" / "reports"
    assert not real_data.exists() or not list(real_data.glob("*.json")), \
        "真实 data/reports 不应产生测试残留"


def test_individual_tool_callable():
    """单个工具函数应能直接调用（不通过 MCP 协议）"""
    import mcp_server
    # list_clients 应该返回字符串
    out = mcp_server.list_clients()
    assert isinstance(out, str)
    # get_client_holdings 接受 client_id
    out = mcp_server.get_client_holdings("non_existent_user_zzz_9999")
    assert "non_existent_user_zzz_9999" in out
    # auto_import_file 接受任意路径，不崩
    out = mcp_server.auto_import_file("Z:/this/does/not/exist.png")
    assert isinstance(out, str)
    # auto_import_file 支持 .xlsx/.csv（v9.0: 外部绝对路径被沙箱拦截返回校验错误）
    out = mcp_server.auto_import_file("Z:/this/does/not/exist.xlsx")
    assert isinstance(out, str) and any(k in out for k in ("不支持", "Excel", "文件"))
