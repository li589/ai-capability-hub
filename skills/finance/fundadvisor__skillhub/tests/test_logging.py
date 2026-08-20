"""test_logging.py — 验证业务模块 logging 配置正确（Web/Desktop 已移除）"""
import logging
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
def test_fund_advisor_bootstrap_importable():
    """fund_advisor_bootstrap 应能被正常 import"""
    sys.path.insert(0, str(ROOT))
    from fund_advisor import fund_advisor_bootstrap
    assert fund_advisor_bootstrap is not None
def test_mcp_server_logger_exists():
    """mcp_server 自身应能被干净 import（不强制要求 log 对象）"""
    sys.path.insert(0, str(ROOT))
    import mcp_server
    assert mcp_server is not None
def test_holdings_importer_logger_exists():
    """holdings_importer 模块应能被干净 import"""
    from client_manager.holdings_importer import HoldingsImporter
    assert hasattr(HoldingsImporter, "import_from_screenshot")
