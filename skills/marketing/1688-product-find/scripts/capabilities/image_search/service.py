# -*- coding: utf-8 -*-
"""
图片搜索能力实现
基于上传的商品图片搜索同款或相似商品
"""

import os
import io
import base64
import tempfile
import logging
from typing import Dict, List, Any
from pathlib import Path

from PIL import Image

from _http import api_post
from _errors import ServiceError
from _auth import get_ak_from_env
import settings

logger = logging.getLogger("1688_image_search")

# API 仅稳定支持 JPEG，非 JPEG 格式需在上传前转换
_JPEG_EXTENSIONS = {".jpg", ".jpeg"}


class ImagePreprocessor:
    """图片预处理器"""
    
    def preprocess(self, image_path: str) -> Dict[str, Any]:
        """
        预处理图片
        
        Args:
            image_path: 本地路径或 URL
            
        Returns:
            处理后的图片信息
        """
        # 检查是否是 URL
        if image_path.startswith("http"):
            return self._process_url(image_path)
        
        # 本地文件
        return self._process_local(image_path)
    
    def _process_local(self, path: str) -> Dict[str, Any]:
        """处理本地图片，非 JPEG 格式自动转换为 JPEG"""
        # 将相对路径转为绝对路径，避免因 cwd 不一致导致找不到文件
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"图片不存在：{path}")
        
        # 检查文件大小
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        if file_size_mb > settings.settings.IMAGE_MAX_SIZE_MB:
            raise ValueError(f"图片太大 ({file_size_mb:.1f}MB)，最大支持 {settings.settings.IMAGE_MAX_SIZE_MB}MB")
        
        ext = Path(path).suffix.lower()
        converted = False
        
        # 非 JPEG 格式自动转换（API 仅稳定支持 JPEG）
        if ext not in _JPEG_EXTENSIONS:
            path, converted = self._convert_to_jpeg(path)
            ext = ".jpg"
            logger.info("已将图片转换为 JPEG 格式: %s", path)
        
        return {
            "path": path,
            "type": "local",
            "size_bytes": os.path.getsize(path),
            "format": ext,
            "converted": converted,
        }
    
    @staticmethod
    def _convert_to_jpeg(src_path: str, quality: int = 90) -> tuple:
        """
        将任意格式的图片转换为 JPEG。
        
        Args:
            src_path: 原始图片路径
            quality: JPEG 压缩质量 (1-100)
            
        Returns:
            (转换后的临时文件路径, True)
        """
        try:
            img = Image.open(src_path)
        except Exception as e:
            raise ServiceError(f"无法打开图片文件: {e}")
        
        # 处理透明通道：RGBA / LA / P(带透明) → RGB 白色底
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            background = Image.new("RGB", img.size, (255, 255, 255))
            # P 模式先转 RGBA 再合成
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1])  # 用 alpha 通道作为 mask
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # 写入临时文件（后缀 .jpg 便于调试识别）
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        try:
            img.save(tmp, format="JPEG", quality=quality)
            tmp.close()
        except Exception as e:
            tmp.close()
            os.unlink(tmp.name)
            raise ServiceError(f"图片转换 JPEG 失败: {e}")
        
        return tmp.name, True
    
    def _process_url(self, url: str) -> Dict[str, Any]:
        """处理图片 URL"""
        return {
            "url": url,
            "type": "url"
        }


class ImageSearchExecutor:
    """图片搜索执行器"""
    
    def __init__(self, platform: str = "1688"):
        self.platform = platform
        self.preprocessor = ImagePreprocessor()
    
    def search(self, image_path: str, limit: int = 6, 
               similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        执行图片搜索
        
        Args:
            image_path: 图片路径或 URL
            limit: 返回数量
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果
        """
        # 预处理图片
        img_info = self.preprocessor.preprocess(image_path)
        
        # 执行搜索（直接使用 API）
        results = self._search_via_api(img_info, limit)
        
        return {
            "success": True,
            "source_image": image_path,
            "similar_products": results,
            "search_type": "image_similarity",
            "total_results": len(results)
        }
    
    def _search_via_api(self, img_info: Dict, limit: int) -> List[Dict]:
        """通过 API 搜索"""
        image_base64 = ""
        image_url = None
        converted_path = None
        
        # 根据图片类型处理
        if img_info.get("type") == "url":
            # URL 类型直接使用 imageUrl
            image_url = img_info.get("url")
        else:
            # 本地文件转 base64
            image_path = img_info.get("path")
            if not image_path or not os.path.exists(image_path):
                raise ServiceError("图片路径无效")
            
            # 记录转换后的临时文件，搜索结束后清理
            if img_info.get("converted"):
                converted_path = image_path
            
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        try:
            # 3. 拼装请求 request
            request = {
                "request": {
                    "imgBase64": image_base64,
                    "imageUrl": image_url,
                    "pageSize": limit
                }
            }
            
            # 4. 调用 api_post
            resp = api_post("/api/findProduct/1.0.0", request)
            
            # 5. 解析返回信息
            data = resp.get("data")
            if not isinstance(data, list):
                raise ServiceError("格式异常，请稍后重试")
            
            # 转换为统一的商品结构
            results = []
            for item in data:
                results.append({
                    "product_id": str(item.get("itemId", "")),
                    "title": item.get("title", ""),
                    "image_url": item.get("imageUrl", ""),
                    "detail_url": item.get("detailUrl", ""),
                    "similarity_score": float(item.get("score", 0)),
                    "price": item.get("currentPrice"),
                    "supplier": item.get("company", ""),
                    "sold_count": item.get("soldOut", 0),
                    "stock_amount": item.get("storeAmount", 0),
                    "user_id": str(item.get("userId", "")),
                    "member_id": item.get("memberId", ""),
                    "category_id": item.get("cateId"),
                    "promotion_tags": item.get("promotionTags", []),
                    "service_infos": item.get("serviceInfos", []),
                    "selling_points": item.get("sellingPoints", [])
                })
            
            return results
        finally:
            # 清理格式转换产生的临时文件
            if converted_path:
                try:
                    os.unlink(converted_path)
                except OSError:
                    pass
    
    def _search_via_browser(self, img_info: Dict, limit: int) -> List[Dict]:
        """
        浏览器渲染方案（降级）
        返回结构化信号，由 Agent 接管
        """
        image_path = img_info.get("path") or img_info.get("url")
        
        return [{
            "action": "browser_render",
            "url": "https://s.1688.com/selloffer/offer_search.htm",
            "upload_image": image_path,
            "message": "正在上传图片并搜索同款..."
        }]


def format_similar_product(product: Dict) -> str:
    """格式化相似商品卡片"""
    template = """
🔍 **相似度：{similarity}%**
🛍️ {title}
💰 ¥{price}
🏷️ {tags}
🔗 [查看详情]({detail_url})
""".strip()
    
    similarity = product.get("similarity_score", 0) * 100
    
    return template.format(
        similarity=f"{similarity:.0f}",
        title=product.get("title", "未知商品"),
        price=product.get("price", "暂无报价"),
        tags=", ".join(product.get("tags", [])),
        detail_url=product.get("detail_url", "#")
    )


# ========== 主入口函数 ==========

def image_search(image_path: str, platform: str = "1688", 
                 limit: int = 6, similarity_threshold: float = 0.7) -> Dict[str, Any]:
    """
    图片搜索主函数
    
    Args:
        image_path: 图片本地路径或 URL
        platform: 目标平台
        limit: 返回数量
        similarity_threshold: 相似度阈值
        
    Returns:
        搜索结果
    """
    executor = ImageSearchExecutor(platform=platform)
    return executor.search(
        image_path=image_path,
        limit=limit,
        similarity_threshold=similarity_threshold
    )


if __name__ == "__main__":
    # 测试示例
    test_image = "/workspace/test_product.jpg"
    if os.path.exists(test_image):
        result = image_search(test_image)
        print(f"找到 {result['total_results']} 个相似商品")
    else:
        print(f"测试图片不存在：{test_image}")
