"""ViralLens 视频分析 Pay Skill — 主服务 (X402支付, ¥1/次)

接口:
- POST /api/resource       — X402 支付流程 (402→支付→200+启动任务)
- GET  /api/task/{task_id} — 轮询任务状态
- GET  /api/health         — 健康检查
"""

import time
import secrets
import logging
import json
import asyncio
import tempfile
import shutil
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Request, Header, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.config import MODE, PRICE, BASE_URL, COOKIES_FILE, COOKIES_DIR
from app.wxpay import native_order, query_order, refund
from app.x402_signer import call_ai_preorder
from app.store import OrderStore
from app.analyzer import analyze_video
from app.report import REPORT_HTML_TEMPLATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ViralLens 爆款视频分析 - Pay Skill", version="1.0.0")
store = OrderStore()


class AnalyzeRequest(BaseModel):
    query: str = Field(..., description="视频URL或描述", min_length=1, max_length=500)
    video_url: Optional[str] = Field(None, description="视频URL (TikTok/YouTube/B站等)")
    proxy: Optional[str] = Field("", description="下载代理URL")
    threshold: Optional[float] = Field(15.0, description="场景检测阈值")
    cookies: Optional[str] = Field("", description="cookies文件路径")


@app.post("/api/resource")
async def handle_resource(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    x_out_trade_no: Optional[str] = Header(None, alias="X-Out-Trade-No"),
):
    if x_out_trade_no:
        return await _verify_and_fulfill(x_out_trade_no, req, background_tasks)
    return await _create_payment_order(req)


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """轮询任务状态"""
    order = store.get(task_id)
    if not order:
        return JSONResponse(status_code=404, content={"error": "任务不存在"})

    status = order["task_status"]
    resp = {
        "task_id": task_id,
        "status": status,
        "out_trade_no": order["out_trade_no"],
    }

    if status == "completed":
        try:
            resp["result"] = json.loads(order["result"]) if order.get("result") else {}
        except json.JSONDecodeError:
            resp["result"] = {"raw": order["result"]}
    elif status == "failed":
        resp["error"] = order.get("error", "未知错误")
    else:
        resp["message"] = f"分析中... 当前状态: {status}"

    return JSONResponse(content=resp)


@app.get("/report/{task_id}", response_class=HTMLResponse)
async def get_report_page(task_id: str):
    """HTML 报告页面"""
    html = REPORT_HTML_TEMPLATE.replace('{{TASK_ID}}', task_id)
    return HTMLResponse(content=html)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": MODE,
        "orders": store.count(),
        "price": f"¥{PRICE/100:.2f}",
        "skill": "virallens-analyzer",
    }


@app.get("/")
async def root():
    return {"name": "ViralLens 爆款视频分析", "version": "1.0.0", "skill_id": "virallens-analyzer"}


@app.post("/api/cookies/upload")
async def upload_cookies(platform: str = Form(...), file: UploadFile = File(...)):
    """上传 cookies 文件
    
    platform: 平台名称 (douyin, tiktok, xiaohongshu 等)
    file: Netscape 格式的 cookies 文件
    """
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "缺少文件"})
    
    cookies_dir = Path(COOKIES_DIR)
    cookies_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成安全的文件名
    safe_platform = platform.lower().replace("/", "_").replace("..", "")
    filename = f"{safe_platform}.txt"
    filepath = cookies_dir / filename
    
    # 保存文件
    content = await file.read()
    filepath.write_bytes(content)
    
    logger.info(f"[COOKIES] 上传成功: {filename} ({len(content)} bytes)")
    
    return {
        "status": "success",
        "platform": platform,
        "filename": filename,
        "size": len(content),
        "path": str(filepath),
        "usage": f'在请求中传入 cookies="{filepath}" 即可使用'
    }


@app.get("/api/cookies/list")
async def list_cookies():
    """列出已上传的 cookies 文件"""
    cookies_dir = Path(COOKIES_DIR)
    if not cookies_dir.exists():
        return {"cookies": []}
    
    files = []
    for f in cookies_dir.glob("*.txt"):
        files.append({
            "platform": f.stem,
            "filename": f.name,
            "size": f.stat().st_size,
            "path": str(f),
            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime))
        })
    
    return {"cookies": files}


@app.delete("/api/cookies/{platform}")
async def delete_cookies(platform: str):
    """删除指定平台的 cookies 文件"""
    cookies_dir = Path(COOKIES_DIR)
    filename = f"{platform.lower()}.txt"
    filepath = cookies_dir / filename
    
    if not filepath.exists():
        return JSONResponse(status_code=404, content={"error": f"未找到 {platform} 的 cookies"})
    
    filepath.unlink()
    logger.info(f"[COOKIES] 删除成功: {filename}")
    
    return {"status": "success", "deleted": filename}


@app.post("/api/pay/notify")
async def pay_notify(request: Request):
    body = await request.json()
    logger.info(f"[pay_notify] {body}")
    return {"code": "SUCCESS", "message": "成功"}


@app.post("/api/refund/notify")
async def refund_notify(request: Request):
    body = await request.json()
    logger.info(f"[refund_notify] {body}")
    return {"code": "SUCCESS", "message": "成功"}


async def _create_payment_order(req: AnalyzeRequest):
    """创建支付订单 → 返回 402"""
    out_trade_no = f"VL{time.strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4)}"
    amount = PRICE  # 199 分 = ¥1.99
    description = f"ViralLens视频分析: {req.video_url or req.query[:30]}"

    # 预览: 显示将要分析的视频信息
    preview = _generate_preview(req)

    try:
        code_url = await native_order(out_trade_no, description, amount)
    except Exception as e:
        logger.error(f"Native下单失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"下单失败: {e}"})

    if MODE == "mock":
        payment_code = f"mock_pc_{out_trade_no}"
    else:
        try:
            payment_code = await call_ai_preorder(code_url, amount, description)
        except Exception as e:
            logger.error(f"AI预下单失败: {e}")
            return JSONResponse(status_code=500, content={"error": f"预下单失败: {e}"})

    store.save({
        "out_trade_no": out_trade_no,
        "payment_code": payment_code,
        "amount": amount,
        "description": description,
        "video_url": req.video_url or req.query,
        "status": "INIT",
        "created_at": int(time.time()),
    })

    return JSONResponse(
        status_code=402,
        headers={"WeixinPay-Required": payment_code, "X-Out-Trade-No": out_trade_no},
        content={
            "code": "PAYMENT_REQUIRED",
            "message": f"支付¥1.99获取视频深度分析",
            "WeixinPay": {
                "WeixinPay-Required": payment_code,
                "prompt": "将 WeixinPay-Required 的值作为 paymentCode 交给 weixinpay_pay",
            },
            "out_trade_no": out_trade_no,
            "amount": f"{amount / 100:.2f}",
            "currency": "CNY",
            "description": description,
            "preview": preview,
        },
    )


async def _verify_and_fulfill(out_trade_no: str, req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """验证支付 → 启动分析任务 → 返回 200"""
    order = store.get(out_trade_no)
    if not order:
        return JSONResponse(status_code=404, content={"error": f"订单不存在: {out_trade_no}"})

    # 已完成的任务直接返回结果
    if order["status"] == "FULFILLED" and order["task_status"] == "completed":
        return JSONResponse(status_code=200, content={
            "code": "SUCCESS",
            "message": "视频分析（已完成）",
            "out_trade_no": out_trade_no,
            "task_id": out_trade_no,
            "task_status": "completed",
            "content": json.loads(order["result"]) if order.get("result") else {},
            "already_fulfilled": True,
        })

    # 已付款但任务还在运行中
    if order["status"] == "FULFILLED" and order["task_status"] in ("processing", "downloading"):
        return JSONResponse(status_code=200, content={
            "code": "SUCCESS",
            "message": "视频分析正在进行中",
            "out_trade_no": out_trade_no,
            "task_id": out_trade_no,
            "task_status": order["task_status"],
            "already_fulfilled": True,
        })

    # 验证支付
    try:
        trade_state, transaction_id = await query_order(out_trade_no)
    except Exception as e:
        logger.error(f"查单失败: {e}")
        return JSONResponse(status_code=402, content={
            "code": "NOT_PAID", "message": "支付验证中，请稍后重试", "out_trade_no": out_trade_no,
        })

    if trade_state != "SUCCESS":
        return JSONResponse(status_code=402, content={
            "code": "NOT_PAID", "message": "尚未完成支付", "out_trade_no": out_trade_no,
            "trade_state": trade_state,
        })

    # 支付成功 → 启动后台分析任务
    video_url = req.video_url or order.get("video_url") or req.query
    proxy = req.proxy or ""
    threshold = req.threshold or 15.0
    cookies = req.cookies or COOKIES_FILE

    store.update_status(out_trade_no, "FULFILLED", transaction_id=transaction_id, fulfilled_at=int(time.time()))
    store.update_task(out_trade_no, "processing")

    # 启动后台任务
    background_tasks.add_task(_run_analysis, out_trade_no, video_url, proxy, threshold, cookies)

    logger.info(f"支付成功，启动分析任务: {out_trade_no}, URL: {video_url}")

    return JSONResponse(status_code=200, content={
        "code": "SUCCESS",
        "message": "支付成功！视频分析已开始，通常需要2-5分钟完成",
        "out_trade_no": out_trade_no,
        "task_id": out_trade_no,
        "task_status": "processing",
        "transaction_id": transaction_id,
        "poll_url": f"{BASE_URL}/api/task/{out_trade_no}",
        "report_url": f"{BASE_URL}/report/{out_trade_no}",
        "estimated_time": "2-5分钟",
    })


async def _run_analysis(out_trade_no: str, video_url: str, proxy: str, threshold: float, cookies: str = ""):
    """后台运行视频分析"""
    work_dir = Path(tempfile.mkdtemp(prefix=f"vl_{out_trade_no}_"))
    logger.info(f"[TASK] 开始分析: {out_trade_no}, 工作目录: {work_dir}")

    try:
        store.update_task(out_trade_no, "downloading")

        # 在后台线程运行（CPU密集 + 网络IO）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: analyze_video(video_url, work_dir, proxy=proxy, threshold=threshold, cookies=cookies)
        )

        store.update_task(
            out_trade_no, "completed",
            result=json.dumps(result, ensure_ascii=False),
            completed_at=int(time.time()),
        )
        logger.info(f"[TASK] 分析完成: {out_trade_no}, viral_score={result.get('insights', {}).get('viral_score', 'N/A')}")

    except Exception as e:
        logger.error(f"[TASK] 分析失败: {out_trade_no}, {e}")
        store.update_task(out_trade_no, "failed", error=str(e))

        # 尝试退款
        order = store.get(out_trade_no)
        if order:
            try:
                await refund(out_trade_no, order["amount"], f"分析失败: {str(e)[:80]}")
                store.update_status(out_trade_no, "REFUNDED", refund_reason=str(e))
                logger.info(f"[TASK] 已退款: {out_trade_no}")
            except Exception as re:
                logger.error(f"[TASK] 退款也失败: {re}")
                store.update_status(out_trade_no, "FULFILL_AND_REFUND_FAILED")

    finally:
        # 清理临时文件
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


def _generate_preview(req: AnalyzeRequest) -> dict:
    """生成预览信息（免费展示部分）"""
    url = req.video_url or req.query
    platform = "unknown"
    if "tiktok" in url.lower():
        platform = "TikTok"
    elif "youtube" in url.lower() or "youtu.be" in url.lower():
        platform = "YouTube"
    elif "bilibili" in url.lower() or "b23.tv" in url.lower():
        platform = "B站"
    elif "douyin" in url.lower():
        platform = "抖音"
    elif "instagram" in url.lower():
        platform = "Instagram"
    elif "xiaohongshu" in url.lower() or "xhslink" in url.lower():
        platform = "小红书"

    return {
        "platform": platform,
        "video_url": url[:100],
        "features": [
            "🎬 场景切换检测 + 关键帧提取",
            "🎤 语音转文字 (中/英双语)",
            "👁️ AI视觉分析 (风格/色彩/构图)",
            "📊 病毒传播评分 + 可复用脚本模板",
            "💡 10+条可执行优化建议",
        ],
        "preview_text": f"即将为您深度分析{platform}视频，生成完整拆解报告...",
    }
