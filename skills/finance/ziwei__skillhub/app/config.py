"""中医体质辨识 Pay Skill 配置"""
import os
from pathlib import Path

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

MODE = os.getenv("MODE", "live")
PRICE = int(os.getenv("PRICE", "990"))  # ¥9.90

BASE_URL = os.getenv("BASE_URL", "https://meihua.astrakairos.com/ziwei")

# 微信支付
MCH_ID = os.getenv("MCH_ID", "")
APP_ID = os.getenv("APP_ID", "")
MCH_SERIAL = os.getenv("MCH_SERIAL", "")
MCH_APIV3_KEY = os.getenv("MCH_APIV3_KEY", "")

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
