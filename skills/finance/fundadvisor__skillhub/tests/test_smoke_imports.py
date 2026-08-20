"""test_smoke_imports.py — 全模块 import 烟囱测试

任何 SyntaxError 或顶层 ImportError 都会让整个 skill 启动失败。
这个测试确保 skill 在干净环境下也能 import。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_import_llm_providers():
    import llm_providers
    assert hasattr(llm_providers, "LLMClient")


def test_import_conversation_engine():
    from client_manager.conversation_engine import ClientManager
    assert hasattr(ClientManager, "chat")


def test_import_holdings_importer():
    from client_manager.holdings_importer import HoldingsImporter
    assert hasattr(HoldingsImporter, "import_from_screenshot")


def test_import_alert_system():
    from client_manager.alert_system import AlertSystem
    assert hasattr(AlertSystem, "daily_check")


def test_import_emotional_tracker():
    from client_manager.emotional_tracker import EmotionalTracker
    assert hasattr(EmotionalTracker, "record_emotion")


def test_import_invitation_engine():
    from client_manager.invitation_engine import InvitationEngine
    assert hasattr(InvitationEngine, "invite_managers_for_products")


def test_import_user_profile_manager():
    from client_manager.user_profile_manager import UserQuantitativeAssessment
    assert hasattr(UserQuantitativeAssessment, "assess_investment_profile")


def test_import_fund_advisor_speech():
    from analysis.fund_advisor_speech import FundAdvisorSpeech
    assert hasattr(FundAdvisorSpeech, "ask")


def test_import_fund_quant_analyzer():
    from analysis.fund_quant_analyzer import FundQuantAnalyzer
    assert hasattr(FundQuantAnalyzer, "analyze_fund")


def test_import_portfolio_recommender():
    from analysis.portfolio_recommender_v2 import PortfolioRecommenderV2
    assert hasattr(PortfolioRecommenderV2, "recommend_portfolio_v2")


def test_import_comparison_engine():
    from analysis.comparison_engine import ComparisonEngine
    assert hasattr(ComparisonEngine, "compare_managers")


def test_import_news_advisor():
    from analysis.news_advisor import NewsAdvisor
    assert NewsAdvisor is not None


def test_import_macro_analyzer():
    from analysis.macro_analyzer import MacroAnalyzer
    assert MacroAnalyzer is not None


def test_import_performance_tracker():
    from analysis.performance_tracker import PerformanceTracker
    pt = PerformanceTracker()
    assert pt is not None


def test_import_stock_quant_analyzer():
    from analysis.stock_quant_analyzer import StockQuantAnalyzer
    assert StockQuantAnalyzer is not None


# ---------------------------------------------------------------------------
# 全覆盖编译烟囱测试：自动扫描所有 .py 文件，确保任何 SyntaxError 都会被捕获
# （历史上 ppt_report_generator.py 曾因缩进错误无法导入，但未被手工清单覆盖）
# ---------------------------------------------------------------------------

def _all_python_files():
    skip_dirs = {"__pycache__", ".git", ".pytest_cache", "node_modules", "logs"}
    for path in ROOT.rglob("*.py"):
        if any(part in skip_dirs for part in path.parts):
            continue
        yield path


def test_all_modules_compile():
    """所有 .py 文件必须可编译（捕获 SyntaxError/IndentationError）"""
    import py_compile
    failures = []
    count = 0
    for path in _all_python_files():
        count += 1
        try:
            py_compile.compile(str(path), doraise=True, cfile=str(path) + "c.check")
        except Exception as e:  # noqa: BLE001
            failures.append(f"{path.relative_to(ROOT)}: {e.__class__.__name__}")
        finally:
            try:
                Path(str(path) + "c.check").unlink(missing_ok=True)
            except OSError:
                pass
    assert count > 50, f"扫描到的 .py 文件数量异常：{count}"
    assert not failures, "以下文件无法编译：" + "; ".join(failures)


def test_key_client_manager_modules_importable():
    """client_manager 全部核心模块必须可导入（防止语法错误绕过手工清单）"""
    import importlib
    modules = [
        "client_manager.ppt_report_generator",
        "client_manager.report_generator",
        "client_manager.report_scheduler",
        "client_manager.behavioral_profile",
        "client_manager.fund_report_exporter",
        "client_manager.sector_predictor",
    ]
    failures = []
    for name in modules:
        try:
            importlib.import_module(name)
        except ImportError as e:
            # 可选第三方依赖缺失（如 python-pptx）属可接受降级，但语法错误不可接受
            if e.name and e.name.split(".")[0] in ("pptx", "openpyxl", "docx", "reportlab"):
                continue
            failures.append(f"{name}: {e}")
        except SyntaxError as e:
            failures.append(f"{name}: SyntaxError {e}")
    assert not failures, "以下模块导入失败：" + "; ".join(failures)
