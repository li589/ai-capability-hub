"""AI Berkshire 四维投研分析 Pay Skill - 主服务"""
import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.config import MODE, PRICE, BASE_URL, ANALYSIS_DIMENSIONS
from app.wxpay import native_order, query_order, refund
from app.x402_signer import call_ai_preorder
from app.store import OrderStore
from app.analyst_engine import AnalystEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Berkshire 四维投研分析", version="1.0.0")

# 初始化组件
store = OrderStore()
engine = AnalystEngine()


class AnalysisRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码，如 AAPL, 600519.SH")
    company_name: str = Field(..., description="公司名称")


@app.get("/")
async def root():
    return {
        "name": "AI Berkshire 四维投研分析",
        "version": "1.0.0",
        "dimensions": [
            {"id": d['id'], "name": d['name'], "analyst": d['analyst']}
            for d in ANALYSIS_DIMENSIONS
        ]
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": MODE,
        "price": f"¥{PRICE/100:.2f}",
        "service": "berkshire-analyst"
    }


@app.post("/api/resource")
async def analyze_stock(
    req: AnalysisRequest,
    background_tasks: BackgroundTasks,
    x_out_trade_no: Optional[str] = Header(None, alias="X-Out-Trade-No"),
):
    """创建分析订单，返回 402 支付请求；支付后带订单号重试则验付并启动分析"""

    # 带订单号重试：验证支付状态，已支付则启动/交付分析
    if x_out_trade_no:
        return await _verify_and_fulfill(x_out_trade_no, background_tasks)

    # 首次请求：创建订单
    out_trade_no = f"BK{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

    order = {
        "out_trade_no": out_trade_no,
        "stock_code": req.stock_code,
        "company_name": req.company_name,
        "amount": PRICE,
        "status": "INIT",
        "created_at": int(time.time())
    }
    store.save(order)

    logger.info(f"订单创建: {out_trade_no} - {req.company_name} ({req.stock_code})")

    # 创建支付订单，返回 402 要求支付
    # 注意：mock 模式只模拟微信 API 调用，支付流程本身不可跳过（防白嫖）
    try:
        code_url = await native_order(
            out_trade_no=out_trade_no,
            description=f"AI Berkshire 四维投研分析: {req.company_name}",
            amount=PRICE
        )
        if not code_url:
            raise Exception("微信支付下单失败：未返回 code_url")

        if MODE == "mock":
            # 本地开发：跳过 X402 预下单（无 SkillHub 密钥），其余流程与 live 一致
            payment_code = f"MOCK_{out_trade_no}"
        else:
            # clawagentpay 预授权令牌金额固定为 1（与 ziwei 对齐），
            # 实际 ¥9.90 扣款由 code_url 承载，勿传 amount=PRICE 否则微信 302 拒绝
            payment_code = await call_ai_preorder(
                code_url=code_url,
                title=f"AI Berkshire: {req.company_name}"
            )

        return JSONResponse(
            status_code=402,
            content={
                "code": "PAYMENT_REQUIRED",
                "message": f"支付 ¥{PRICE/100:.2f} 获取专业四维投研分析报告",
                "out_trade_no": out_trade_no,
                "amount": f"¥{PRICE/100:.2f}",
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
        logger.error(f"创建支付订单失败: {e}")
        store.update_status(out_trade_no, "FAILED", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _verify_and_fulfill(out_trade_no: str, background_tasks: BackgroundTasks):
    """支付后重试入口：强制验付，未支付绝不放行"""

    order = store.get(out_trade_no)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    status = order["status"]

    # 已完成：直接交付结果
    if status == "FULFILLED":
        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "分析已完成",
                "out_trade_no": out_trade_no,
                "task_id": out_trade_no,
                "task_status": "completed",
                "report_url": f"{BASE_URL}/report/{out_trade_no}"
            }
        )

    # 分析中：告知进度
    if status == "PROCESSING":
        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "分析进行中，请稍后查询任务状态",
                "out_trade_no": out_trade_no,
                "task_id": out_trade_no,
                "task_status": "processing",
                "report_url": f"{BASE_URL}/report/{out_trade_no}"
            }
        )

    # FAILED 不再直接 500 死锁：已付款用户可重试（重新查单验证后重启分析）
    # 未付款订单重试会被 query_order 拦回 402，不会白送

    # INIT/PAID：主动向微信查单，验证通过才放行
    try:
        trade_state, transaction_id = await query_order(out_trade_no)
    except Exception as e:
        logger.error(f"查单失败: {out_trade_no} - {e}")
        raise HTTPException(status_code=502, detail=f"支付状态查询失败: {e}")

    if trade_state != "SUCCESS":
        return JSONResponse(
            status_code=402,
            content={
                "code": "NOT_PAID",
                "message": "支付尚未完成，请完成支付后携带订单号重试",
                "out_trade_no": out_trade_no,
                "trade_state": trade_state
            }
        )

    # 支付确认，启动分析
    store.update_status(out_trade_no, "PAID", transaction_id=transaction_id)
    store.update_status(out_trade_no, "PROCESSING")
    background_tasks.add_task(
        run_analysis_task,
        out_trade_no,
        order["stock_code"],
        order["company_name"]
    )
    logger.info(f"支付验证通过，分析任务启动: {out_trade_no} (transaction_id={transaction_id})")

    return JSONResponse(
        status_code=200,
        content={
            "code": "SUCCESS",
            "message": "支付成功，分析任务已启动，预计需要 3-5 分钟",
            "out_trade_no": out_trade_no,
            "task_id": out_trade_no,
            "task_status": "processing",
            "report_url": f"{BASE_URL}/report/{out_trade_no}"
        }
    )


@app.post("/api/resource/fulfill")
async def fulfill_order(
    out_trade_no: str,
    background_tasks: BackgroundTasks
):
    """支付完成后启动分析任务（强制验付：向微信查单确认 SUCCESS 才放行）"""
    return await _verify_and_fulfill(out_trade_no, background_tasks)


async def run_analysis_task(out_trade_no: str, stock_code: str, company_name: str):
    """后台执行四维分析"""
    
    logger.info(f"[TASK] 开始分析: {out_trade_no} - {company_name}")
    
    try:
        # 创建输出目录
        output_dir = Path(f"data/tasks/{out_trade_no}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 进度回调
        async def progress_callback(dim_id: str, message: str):
            store.update_progress(out_trade_no, dim_id, message)
        
        # 执行分析
        result = await engine.analyze(
            stock_code=stock_code,
            company_name=company_name,
            output_dir=output_dir,
            progress_callback=progress_callback
        )
        
        # 更新订单状态
        store.update_status(out_trade_no, "FULFILLED")
        store.save_result(out_trade_no, result)
        
        logger.info(f"[TASK] 分析完成: {out_trade_no}")
    
    except Exception as e:
        logger.error(f"[TASK] 分析失败: {out_trade_no} - {e}")
        store.update_status(out_trade_no, "FAILED", error=str(e))


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    
    order = store.get(task_id)
    if not order:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = order['status']
    
    if status == "FULFILLED":
        result = store.get_result(task_id)
        return {
            "task_id": task_id,
            "status": "completed",
            "report_url": f"{BASE_URL}/report/{task_id}",
            "result": result
        }
    elif status == "FAILED":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": order.get('error', '未知错误')
        }
    elif status == "PROCESSING":
        progress = store.get_progress(task_id)
        return {
            "task_id": task_id,
            "status": "processing",
            "progress": progress
        }
    else:
        return {
            "task_id": task_id,
            "status": status.lower()
        }


@app.get("/report/{task_id}", response_class=HTMLResponse)
async def get_report(task_id: str):
    """获取 HTML 报告页面"""
    
    order = store.get(task_id)
    if not order:
        return HTMLResponse(content="<h1>报告不存在</h1>", status_code=404)
    
    # 读取报告模板
    from app.report import REPORT_TEMPLATE
    
    # 替换变量
    html = REPORT_TEMPLATE.replace("{{TASK_ID}}", task_id)
    html = html.replace("{{COMPANY_NAME}}", order['company_name'])
    html = html.replace("{{STOCK_CODE}}", order['stock_code'])
    
    return HTMLResponse(content=html)
