# -*- coding: utf-8 -*-
"""紫微斗数命盘解读 Pay Skill - 主服务"""

import time
import secrets
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from app import config
from app import wxpay
from app import x402_signer
from app.store import OrderStore
from app import ziwei_engine

logger = logging.getLogger(__name__)

app = FastAPI(title="紫微斗数命盘解读 Pay Skill", version="1.0.0")
store = OrderStore()


class ZiweiRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    gender: str


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "紫微斗数命盘解读",
        "version": "1.0.0",
        "mode": config.MODE,
        "price": config.PRICE
    }


@app.get("/report/{order_id}", response_class=HTMLResponse)
async def get_report(order_id: str):
    """渲染报告页面"""
    order = store.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 读取报告模板
    template_path = Path(__file__).parent / "report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 替换模板中的订单ID
    html_content = html_content.replace("{{TASK_ID}}", order_id)
    
    return HTMLResponse(content=html_content)


@app.get("/api/report/{order_id}")
async def get_report_data(order_id: str):
    """获取报告数据（供前端轮询）"""
    order = store.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order["status"] == "SUCCESS":
        return {
            "code": "SUCCESS",
            "result": order["result"]
        }
    elif order["status"] in ["REFUNDED", "FULFILL_AND_REFUND_FAILED"]:
        return {
            "code": order["status"],
            "message": order.get("refund_reason", "服务异常")
        }
    else:
        return {
            "code": "PROCESSING",
            "status": order["status"]
        }


@app.post("/api/resource")
async def analyze_ziwei(
    req: ZiweiRequest,
    x_out_trade_no: Optional[str] = Header(None, alias="X-Out-Trade-No")
):
    """紫微斗数分析接口"""
    
    if x_out_trade_no:
        # 已支付，验证并生成解读
        return await _verify_and_fulfill(x_out_trade_no, req)
    else:
        # 未支付，创建订单
        return await _create_order(req)


async def _create_order(req: ZiweiRequest):
    """创建支付订单"""
    try:
        # 1. 生成订单号
        out_trade_no = f"ZW{int(time.time())}{secrets.token_hex(4).upper()}"
        
        # 2. 调用微信支付 Native 下单
        code_url = await wxpay.native_order(
            out_trade_no=out_trade_no,
            description="紫微斗数命盘解读",
            amount=config.PRICE
        )
        
        # 3. 调用 X402 预下单
        payment_code = await x402_signer.call_ai_preorder(code_url)
        
        # 4. 保存订单到数据库
        order_data = {
            "out_trade_no": out_trade_no,
            "amount": config.PRICE,
            "description": "紫微斗数命盘解读",
            "status": "PENDING",
            "payment_code": payment_code,
            "request_data": req.model_dump_json(),
            "created_at": int(time.time())
        }
        store.save(order_data)
        
        # 5. 返回 402
        return JSONResponse(
            status_code=402,
            content={
                "code": "PAYMENT_REQUIRED",
                "message": "请支付后获取紫微斗数命盘解读",
                "out_trade_no": out_trade_no,
                "WeixinPay": {
                    "WeixinPay-Required": payment_code,
                    "prompt": "请将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay"
                }
            },
            headers={
                "X-Out-Trade-No": out_trade_no,
                "WeixinPay-Required": payment_code
            }
        )
    
    except Exception as e:
        logger.error(f"创建订单失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


async def _verify_and_fulfill(out_trade_no: str, req: ZiweiRequest):
    """验证支付并生成解读"""
    try:
        # 1. 查询订单
        order = store.get(out_trade_no)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        # 2. 检查订单状态
        if order["status"] == "SUCCESS":
            # 已完成，直接返回缓存的结果
            return JSONResponse(
                status_code=200,
                content={
                    "code": "SUCCESS",
                    "message": "命盘解读生成完成",
                    "out_trade_no": out_trade_no,
                    "result": order["result_data"]
                }
            )
        
        if order["status"] == "FAILED":
            return JSONResponse(
                status_code=500,
                content={
                    "code": "FAILED",
                    "message": "订单处理失败",
                    "out_trade_no": out_trade_no
                }
            )
        
        # 3. 验证支付状态
        payment_verified = await wxpay.verify_payment(out_trade_no)
        if not payment_verified:
            return JSONResponse(
                status_code=402,
                content={
                    "code": "NOT_PAID",
                    "message": "支付尚未完成",
                    "out_trade_no": out_trade_no
                }
            )
        
        # 4. 调用紫微斗数引擎生成解读
        logger.info(f"开始生成紫微斗数解读: {out_trade_no}")
        chart_data = await ziwei_engine.calculate_ziwei_chart(
            year=req.year,
            month=req.month,
            day=req.day,
            hour=req.hour,
            gender=req.gender
        )
        
        # 5. 更新订单状态并保存结果
        store.update_status(
            out_trade_no=out_trade_no,
            status="SUCCESS",
            result=json.dumps(chart_data, ensure_ascii=False)
        )
        
        # 6. 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "命盘解读生成完成",
                "out_trade_no": out_trade_no,
                "report_url": f"{config.BASE_URL}/report/{out_trade_no}",
                "result": chart_data
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证或生成解读失败: {e}", exc_info=True)
        # 更新订单状态为失败
        try:
            store.update_status(out_trade_no, "FAILED", error=str(e))
        except:
            pass
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
