# -*- coding: utf-8 -*-
"""
文本搜索能力实现
解析用户自然语言描述，提取商品关键词，执行搜索
"""

import os
import re
from typing import Dict, List, Any, Optional

from _http import api_post
from _errors import ServiceError
from _auth import get_ak_from_env


class TextSearchExecutor:
    """文本搜索执行器"""
    
    def __init__(self, platform: str = "1688"):
        self.platform = platform
    
    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        执行文本搜索
        
        Args:
            query: 用户查询关键词
            limit: 返回数量
            
        Returns:
            搜索结果
        """
        # 执行 API 搜索
        results = self._search_via_api(query, limit)
        
        return {
            "success": True,
            "query": query,
            "similar_products": results,
            "search_type": "text_search",
            "total_results": len(results)
        }
    
    def _search_via_api(self, query: str, limit: int) -> List[Dict]:
        """通过 API 搜索"""
  
        # 1. 拼装请求 request（与 image_search 使用同一 API，增加 query 参数）
        request = {
            "request": {
                "query": query,
                "pageSize": limit
            }
        }
        
        # 3. 调用 api_post（使用同一 API path）
        resp = api_post("/api/findProduct/1.0.0", request)
        
        # 4. 解析返回信息
        data = resp.get("data")
        if not isinstance(data, list):
            raise ServiceError("格式异常，请稍后重试")
        
        # 转换为统一的商品结构
        # 注：文本搜索 API 只返回 itemId，需要自动生成 detail_url
        results = []
        for item in data:
            product_id = str(item.get("itemId", ""))
            # 自动生成 1688 商品详情链接
            detail_url = item.get("detailUrl") or (f"https://detail.1688.com/offer/{product_id}.html" if product_id else "")
            results.append({
                "product_id": product_id,
                "title": item.get("title", ""),
                "image_url": item.get("imageUrl", ""),
                "detail_url": detail_url,
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


def format_product_card(product: Dict) -> str:
    """格式化商品卡片（用于展示）"""
    template = """
🛍️ **{title}**
💰 价格：¥{price}
🔗 [查看详情]({detail_url})
""".strip()
    
    return template.format(
        title=product.get("title", "未知商品"),
        price=product.get("price", "暂无报价"),
        detail_url=product.get("detail_url", "#")
    )


# ========== 主入口函数 ==========

def text_search(query: str, platform: str = "1688", limit: int = 10) -> Dict[str, Any]:
    """
    文本搜索主函数
    
    Args:
        query: 用户搜索关键词
        platform: 目标平台
        limit: 返回数量
        
    Returns:
        搜索结果
    """
    executor = TextSearchExecutor(platform=platform)
    return executor.search(query, limit=limit)


if __name__ == "__main__":
    # 测试示例
    test_query = "黑色连帽卫衣"
    result = text_search(test_query)
    print(f"搜索：{test_query}")
    print(f"找到 {result['total_results']} 个商品")
