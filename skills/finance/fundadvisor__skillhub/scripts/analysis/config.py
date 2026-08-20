"""
Fund Advisor 配置模块
纯本地运行，零依赖；API Key 可选（仅 LLM 对话需要）。
"""
import os
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────────────
_BASE_DIR = os.environ.get("FUND_ADVISOR_BASE_DIR")
if _BASE_DIR:
    BASE_DIR = Path(_BASE_DIR)
else:
    BASE_DIR = Path(__file__).parent.parent.parent

DATA_DIR = BASE_DIR / "data"
SCRIPTS_ANALYSIS_DIR = BASE_DIR / "scripts" / "analysis"
SCRIPTS_COLLECTION_DIR = BASE_DIR / "scripts" / "data_collection"

# ── API Key（可选，仅智能对话需要）─────────────────────────────────────
# 默认值使用占位符而非裸 '***'，避免被密钥扫描器误报
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "OFFLINE_PLACEHOLDER")


def is_offline_mode() -> bool:
    """未配置 API Key 时处于离线模式（占位符=离线）"""
    return API_KEY == "OFFLINE_PLACEHOLDER"
