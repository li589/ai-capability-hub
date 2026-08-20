"""test_config_placeholder.py — 验证 analysis/config.py 的占位符常量"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_api_key_placeholder_is_safe(monkeypatch):
    """API_KEY 默认值不应是裸 '***'，避免被密钥扫描器误报"""
    # 隔离环境：本机可能配置了真实 DEEPSEEK_API_KEY
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    import importlib
    from analysis import config
    importlib.reload(config)
    assert config.API_KEY == "OFFLINE_PLACEHOLDER", \
        f"API_KEY 默认值应为 OFFLINE_PLACEHOLDER，实际={config.API_KEY!r}"


def test_is_offline_mode_true_by_default():
    """未配置环境变量时，应处于离线模式"""
    from analysis import config
    # 重新 import 一次确保是默认状态
    import os
    saved = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        # 强制重新加载以测试默认状态
        import importlib
        importlib.reload(config)
        assert config.is_offline_mode() is True
    finally:
        if saved:
            os.environ["DEEPSEEK_API_KEY"] = saved
        importlib.reload(config)


def test_is_offline_mode_false_when_configured(monkeypatch):
    """配置了环境变量后，离线模式应为 False"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-fake-key-for-test-only")
    import importlib
    from analysis import config
    importlib.reload(config)
    assert config.is_offline_mode() is False
    assert config.API_KEY == "sk-test-fake-key-for-test-only"


def test_base_dir_works_with_fund_advisor_paths():
    """analysis/config.py 与 fund_advisor_paths BASE_DIR 一致"""
    from analysis import config
    from fund_advisor_paths import BASE_DIR as paths_base
    assert config.BASE_DIR == paths_base
