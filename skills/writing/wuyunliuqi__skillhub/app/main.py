# -*- coding: utf-8 -*-
"""五运六气年度运势 Pay Skill - FastAPI 主服务"""

import logging
import time
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.wuyun_engine import analyze_yearly_fortune, get_available_years
from app.store import OrderStore
from app.wxpay import native_order, query_order
from app.x402_signer import call_ai_preorder
from app.config import PAYMENT_AMOUNT, PRODUCT_NAME, MODE

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="五运六气年度运势 Pay Skill", version="1.0.0")

# 初始化订单存储
order_store = OrderStore()


class FortuneRequest(BaseModel):
    """运势分析请求"""
    year: int
    constitution_type: Optional[str] = None


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "service": "五运六气年度运势",
        "version": "1.0.0",
        "mode": MODE
    }


@app.get("/api/years")
async def get_years():
    """获取可分析的年份列表"""
    years = get_available_years()
    return {
        "years": years,
        "current_year": years[len(years) // 2]
    }


@app.post("/api/resource")
async def analyze_fortune(
    request: FortuneRequest,
    x_out_trade_no: Optional[str] = Header(None)
):
    """
    分析五运六气年度运势
    
    工作流程：
    1. 首次请求：返回 402，需要支付
    2. 支付后重试：验证支付状态，执行分析，返回结果
    """
    
    # 如果有订单号，说明是支付后的重试
    if x_out_trade_no:
        logger.info(f"收到重试请求，订单号: {x_out_trade_no}")
        
        # 查询订单
        order = order_store.get(x_out_trade_no)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        # 检查支付状态
        if order["status"] == "PENDING":
            # 查询微信支付状态
            trade_state = await query_order(x_out_trade_no)
            
            if trade_state == "SUCCESS":
                # 支付成功，更新订单状态
                order_store.update(x_out_trade_no, status="PAID")
                order["status"] = "PAID"
                logger.info(f"订单 {x_out_trade_no} 支付成功")
            elif trade_state == "NOTPAY":
                # 尚未支付
                raise HTTPException(status_code=402, detail="订单尚未支付")
            else:
                # 支付失败或退款
                order_store.update(x_out_trade_no, status=trade_state)
                raise HTTPException(status_code=402, detail=f"支付状态: {trade_state}")
        
        # 执行分析
        result = analyze_yearly_fortune(
            year=request.year,
            constitution_type=request.constitution_type
        )
        
        return {
            "code": "SUCCESS",
            "message": "分析完成",
            "out_trade_no": x_out_trade_no,
            "result": result
        }
    
    # 首次请求，创建订单并返回 402
    else:
        logger.info(f"收到新请求: {request.year}年运势分析")
        
        # 生成订单号
        out_trade_no = f"WY{int(time.time() * 1000)}"
        
        # 创建订单
        order_store.save({
            "out_trade_no": out_trade_no,
            "amount": PAYMENT_AMOUNT,
            "description": f"{request.year}年{PRODUCT_NAME}",
            "status": "INIT",
            "created_at": int(time.time())
        })
        
        # 调用微信支付下单
        code_url = await native_order(
            out_trade_no=out_trade_no,
            amount=PAYMENT_AMOUNT,
            description=f"{request.year}年{PRODUCT_NAME}"
        )
        
        # 生成 payment_code
        payment_code = await call_ai_preorder(
            code_url=code_url,
            amount=PAYMENT_AMOUNT,
            title=PRODUCT_NAME
        )
        
        logger.info(f"订单创建成功: {out_trade_no}, payment_code: {payment_code}")
        
        # 返回 402
        return {
            "code": "PAYMENT_REQUIRED",
            "message": f"支付 ¥{PAYMENT_AMOUNT/100:.2f} 获取{PRODUCT_NAME}",
            "out_trade_no": out_trade_no,
            "WeixinPay": {
                "WeixinPay-Required": payment_code,
                "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay"
            }
        }
