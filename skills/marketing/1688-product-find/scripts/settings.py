# -*- coding: utf-8 -*-
"""
Skill 配置模块

注意：不要在模块级强制校验外部依赖（API 密钥、文件权限等）
改为惰性校验，仅在真实调用前触发，避免 import 即崩溃
"""

import os
from typing import Optional


class Settings:
    """Skill 配置类"""
    
    # ========== 基础配置 ==========
    SKILL_NAME = "1688-product-find"
    SKILL_VERSION = "1.0.0"
    DEFAULT_PLATFORM = "1688"
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 20
    
    # ========== 浏览器配置 ==========
    BROWSER_TIMEOUT_MS = 5000
    BROWSER_WAIT_RENDER_MS = 4000
    HEADLESS_MODE = True  # 后台静默模式
    
    # ========== 图片搜索配置 ==========
    IMAGE_MAX_SIZE_MB = 5  # 上传图片最大体积
    IMAGE_STANDARD_SIZE = (800, 800)  # 标准尺寸
    SIMILARITY_THRESHOLD = 0.7  # 相似度阈值
    
    # ========== 1688 API 配置 (可选) ==========
    # 惰性加载，不强制要求配置
    @property
    def API_KEY(self) -> Optional[str]:
        return os.getenv("ALI1688_APP_KEY")
    
    @property
    def API_SECRET(self) -> Optional[str]:
        return os.getenv("ALI1688_APP_SECRET")
    
    @property
    def API_ENABLED(self) -> bool:
        """检查 API 是否可用（惰性校验）"""
        return bool(self.API_KEY and self.API_SECRET)
    
    # ========== API 端点 ==========
    API_BASE_URL = "https://api.1688.com"
    API_IMAGE_SEARCH_ENDPOINT = f"{API_BASE_URL}/search/image"
    API_TEXT_SEARCH_ENDPOINT = f"{API_BASE_URL}/search/text"
    API_PRODUCT_INFO_ENDPOINT = f"{API_BASE_URL}/product/info"
    
    # ========== 平台 URL 模板 ==========
    PLATFORM_URL_TEMPLATES = {
        "1688": "https://detail.1688.com/offer/{product_id}.html",
        "taobao": "https://item.taobao.com/item.htm?id={product_id}",
        "tmall": "https://detail.tmall.com/item.htm?id={product_id}"
    }
    
    # ========== 商品 ID 正则规则 ==========
    PRODUCT_ID_PATTERNS = {
        "1688": r"^\d{6,12}$",  # 6-12 位纯数字
        "taobao": r"^[a-zA-Z0-9]{8,12}$",  # 8-12 位字母数字
        "tmall": r"^[a-zA-Z0-9]{8,12}$"
    }
    
    def validate_api_config(self) -> bool:
        """
        验证 API 配置（在调用前使用）
        返回 True 表示可以使用真实 API，False 表示需要降级
        """
        if not self.API_KEY:
            print("[Warning] 未配置 ALI1688_APP_KEY，将使用降级方案")
            return False
        if not self.API_SECRET:
            print("[Warning] 未配置 ALI1688_APP_SECRET，将使用降级方案")
            return False
        return True


# 全局配置实例
settings = Settings()
