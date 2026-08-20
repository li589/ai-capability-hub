# -*- coding: utf-8 -*-
"""配置管理"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 加载 .env 文件
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# 环境模式
MODE = os.getenv("MODE", "mock")  # mock 或 live

# 服务地址
BASE_URL = os.getenv("BASE_URL", "https://meihua.astrakairos.com/wuyun")

# 支付配置
MCH_ID = os.getenv("MCH_ID", "")
APP_ID = os.getenv("APP_ID", "")
MCH_SERIAL = os.getenv("MCH_SERIAL", "")
MCH_APIV3_KEY = os.getenv("MCH_APIV3_KEY", "")

# 微信支付私钥
MCH_PRIVATE_KEY_PATH = os.getenv("MCH_PRIVATE_KEY_PATH", "")
MCH_PRIVATE_KEY = ""
if MCH_PRIVATE_KEY_PATH and os.path.exists(MCH_PRIVATE_KEY_PATH):
    with open(MCH_PRIVATE_KEY_PATH, "r") as f:
        MCH_PRIVATE_KEY = f.read()

# SkillHub 配置
SKILLHUB_DEVELOPER_ID = os.getenv("SKILLHUB_DEVELOPER_ID", "")
SKILLHUB_PUB_KEY_ID = os.getenv("SKILLHUB_PUB_KEY_ID", "")
SKILLHUB_PRIVATE_KEY_PATH = os.getenv("SKILLHUB_PRIVATE_KEY_PATH", "")
SKILLHUB_PRIVATE_KEY = ""
if SKILLHUB_PRIVATE_KEY_PATH and os.path.exists(SKILLHUB_PRIVATE_KEY_PATH):
    with open(SKILLHUB_PRIVATE_KEY_PATH, "r") as f:
        SKILLHUB_PRIVATE_KEY = f.read()

# 支付配置
PAYMENT_AMOUNT = 499  # 单位：分，即 4.99 元
PRODUCT_NAME = "五运六气年度运势"
