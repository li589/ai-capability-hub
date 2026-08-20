"""梅花易数 Pay Skill 配置"""
import os
from pathlib import Path

# 加载 .env 文件（必须在读取环境变量之前）
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# fail-closed：配置缺失时默认 live，绝不允许免支付发货
MODE = os.getenv("SKILLPAY_MODE", "live") or os.getenv("MODE", "live")
PRICE = int(os.getenv("PRICE", "199"))  # ¥1.99

BASE_URL = os.getenv("BASE_URL", "https://meihua.astrakairos.com")

# DashScope LLM（premium 档 AI 大师点评；缺失时回退模板文字，不阻断交付）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")

# 微信支付
MCH_ID = os.getenv("MCH_ID", "") or os.getenv("WECHAT_MCH_ID", "")
APP_ID = os.getenv("APP_ID", "") or os.getenv("WECHAT_APP_ID", "")
MCH_SERIAL = os.getenv("MCH_SERIAL", "") or os.getenv("MCH_CERT_SERIAL", "") or os.getenv("WECHAT_MCH_CERT_SERIAL", "")
MCH_APIV3_KEY = os.getenv("MCH_APIV3_KEY", "") or os.getenv("MCH_API_V3_KEY", "") or os.getenv("WECHAT_MCH_API_V3_KEY", "")

# 微信支付私钥 — 从文件读取
MCH_PRIVATE_KEY_PATH = os.getenv("MCH_PRIVATE_KEY_PATH", "")
MCH_PRIVATE_KEY = os.getenv("MCH_PRIVATE_KEY", "")
if MCH_PRIVATE_KEY_PATH and os.path.exists(MCH_PRIVATE_KEY_PATH):
    with open(MCH_PRIVATE_KEY_PATH) as f:
        MCH_PRIVATE_KEY = f.read()

# SkillHub
SKILLHUB_DEVELOPER_ID = os.getenv("SKILLHUB_DEVELOPER_ID", "")  # 格式: sh-XXXXXXXX
SKILLHUB_PUB_KEY_ID = os.getenv("SKILLHUB_PUB_KEY_ID", "")

# SkillHub 私钥 — 从文件读取
SKILLHUB_PRIVATE_KEY_PATH = os.getenv("SKILLHUB_PRIVATE_KEY_PATH", "")
SKILLHUB_PRIVATE_KEY = os.getenv("SKILLHUB_PRIVATE_KEY", "")
if SKILLHUB_PRIVATE_KEY_PATH and os.path.exists(SKILLHUB_PRIVATE_KEY_PATH):
    with open(SKILLHUB_PRIVATE_KEY_PATH) as f:
        SKILLHUB_PRIVATE_KEY = f.read()
