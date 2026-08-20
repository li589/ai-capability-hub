"""ViralLens Pay Skill 配置"""
import os

MODE = os.getenv("SKILLPAY_MODE", "live")
PRICE = 199  # ¥1.99 (199分)

BASE_URL = os.getenv("BASE_URL", "https://meihua.astrakairos.com/virallens")

# DashScope
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# Cookies file for yt-dlp (Douyin etc.)
# Auto-detect douyin cookies if exists
COOKIES_DIR = os.getenv("COOKIES_DIR", "/opt/virallens/cookies")
_cookies_path = os.path.join(COOKIES_DIR, "douyin.txt")
COOKIES_FILE = os.getenv("COOKIES_FILE", _cookies_path if os.path.exists(_cookies_path) else "")

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
SKILLHUB_DEVELOPER_ID = os.getenv("SKILLHUB_DEVELOPER_ID", "")
SKILLHUB_PUB_KEY_ID = os.getenv("SKILLHUB_PUB_KEY_ID", "")

# SkillHub 私钥 — 从文件读取
SKILLHUB_PRIVATE_KEY_PATH = os.getenv("SKILLHUB_PRIVATE_KEY_PATH", "")
SKILLHUB_PRIVATE_KEY = os.getenv("SKILLHUB_PRIVATE_KEY", "")
if SKILLHUB_PRIVATE_KEY_PATH and os.path.exists(SKILLHUB_PRIVATE_KEY_PATH):
    with open(SKILLHUB_PRIVATE_KEY_PATH) as f:
        SKILLHUB_PRIVATE_KEY = f.read()
