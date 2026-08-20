"""梅花易数 Pay Skill — 主服务 (X402支付, ¥1.99/次)

接口:
- POST /api/resource  — X402 支付流程 (402→支付→200)
- GET  /api/health    — 健康检查
"""

import time
import secrets
import logging
import json
from typing import Optional, List

from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import MODE, PRICE, BASE_URL
from app.wxpay import native_order, query_order, refund
from app.x402_signer import call_ai_preorder
from app.store import OrderStore
from app.meihua_engine import divine
from app.llm_reading import ai_deep_reading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="梅花易数专业解卦 - Pay Skill", version="1.0.0")
store = OrderStore()


class DivinationRequest(BaseModel):
    query: str = Field(..., description="所问事项", min_length=1, max_length=200)
    tier: str = Field("detailed", description="深度: basic / detailed / premium")
    method: str = Field("time", description="起卦方式: time / number / char")
    numbers: Optional[List[int]] = Field(None, description="报数起卦的数字")
    text: Optional[str] = Field(None, description="字数起卦的文字")


@app.post("/api/resource")
async def handle_resource(
    req: DivinationRequest,
    x_out_trade_no: Optional[str] = Header(None, alias="X-Out-Trade-No"),
):
    if x_out_trade_no:
        return await _verify_and_fulfill(x_out_trade_no, req)
    return await _create_payment_order(req)


@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": MODE, "orders": store.count(), "price": f"¥{PRICE/100:.2f}"}


@app.get("/")
async def root():
    return {"name": "梅花易数专业解卦", "version": "1.0.0", "skill_id": "meihua-yishu"}


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


async def _create_payment_order(req: DivinationRequest):
    """创建支付订单 → 返回 402"""
    out_trade_no = f"MH{time.strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4)}"
    amount = PRICE  # 1 分 = ¥0.01
    description = f"梅花易数: {req.query[:30]}"

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
            # 预授权令牌金额固定为 1（与 fleet 对齐），实际扣款由 code_url 承载，
            # 勿传 amount=PRICE 否则微信 302 拒绝
            payment_code = await call_ai_preorder(code_url, 1, description)
        except Exception as e:
            logger.error(f"AI预下单失败: {e}")
            return JSONResponse(status_code=500, content={"error": f"预下单失败: {e}"})

    store.save({
        "out_trade_no": out_trade_no,
        "payment_code": payment_code,
        "amount": amount,
        "description": description,
        "query": req.query,
        "method": req.method,
        "numbers": req.numbers,
        "status": "INIT",
        "created_at": int(time.time()),
    })

    return JSONResponse(
        status_code=402,
        headers={"WeixinPay-Required": payment_code, "X-Out-Trade-No": out_trade_no},
        content={
            "code": "PAYMENT_REQUIRED",
            "message": f"卦象已生成，支付¥{amount / 100:.2f}获取专业解读",
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


async def _verify_and_fulfill(out_trade_no: str, req: DivinationRequest):
    """验证支付 → 解卦 → 返回 200"""
    order = store.get(out_trade_no)
    if not order:
        return JSONResponse(status_code=404, content={"error": f"订单不存在: {out_trade_no}"})

    if order["status"] == "FULFILLED":
        return JSONResponse(status_code=200, content={
            "code": "SUCCESS",
            "message": "卦象解读（已缓存）",
            "out_trade_no": out_trade_no,
            "content": json.loads(order["result"]) if order.get("result") else {},
            "already_fulfilled": True,
        })

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

    try:
        result = await _execute_divination(req, order)
    except Exception as e:
        logger.error(f"解卦失败，退款: {out_trade_no}, {e}")
        try:
            await refund(out_trade_no, order["amount"], f"服务异常: {e}")
            store.update_status(out_trade_no, "REFUNDED", refund_reason=str(e))
            return JSONResponse(status_code=200, content={
                "code": "REFUNDED", "message": "服务异常，已自动退款", "out_trade_no": out_trade_no,
            })
        except Exception as re:
            logger.error(f"退款也失败: {re}")
            store.update_status(out_trade_no, "FULFILL_AND_REFUND_FAILED")
            return JSONResponse(status_code=500, content={
                "code": "FULFILL_AND_REFUND_FAILED",
                "message": "服务异常且退款失败，请联系客服",
                "out_trade_no": out_trade_no,
            })

    store.update_status(
        out_trade_no, "FULFILLED",
        result=json.dumps(result, ensure_ascii=False),
        transaction_id=transaction_id,
        fulfilled_at=int(time.time()),
    )
    logger.info(f"履约成功: {out_trade_no}")

    return JSONResponse(status_code=200, content={
        "code": "SUCCESS",
        "message": "卦象专业解读",
        "out_trade_no": out_trade_no,
        "transaction_id": transaction_id,
        "content": result,
        "already_fulfilled": False,
    })


def _generate_preview(req: DivinationRequest) -> dict:
    try:
        if req.method == "number" and req.numbers:
            r = divine(req.query, method="number", numbers=req.numbers)
        elif req.method == "char" and req.text:
            r = divine(req.query, method="char", text=req.text)
        else:
            r = divine(req.query, method="time")
        d = r
        return {
            "hex_name": d["ben_hex"]["name"],
            "hex_brief": d["ben_hex"]["brief"],
            "wuxing_level": d["wuxing"]["level"],
            "preview_text": f"已起得{d['ben_hex']['name']}，{d['wuxing']['level']}象",
        }
    except Exception:
        return {"preview_text": f"即将为您解读「{req.query}」的卦象..."}


async def _execute_divination(req: DivinationRequest, order: dict) -> dict:
    import datetime
    method = req.method or order.get("method", "time")
    numbers = req.numbers
    if not numbers and order.get("numbers"):
        numbers = json.loads(order["numbers"])

    if method == "number" and numbers:
        r = divine(req.query, method="number", numbers=numbers)
    elif method == "char" and req.text:
        r = divine(req.query, method="char", text=req.text)
    else:
        r = divine(req.query, method="time")

    data = r
    tier = req.tier

    if tier == "basic":
        return {
            "tier": "basic",
            "question": data["question"],
            "timestamp": data["timestamp"],
            "ben_hex": data["ben_hex"],
            "ti": data["ti"], "yong": data["yong"],
            "wuxing": data["wuxing"],
            "prediction": {"overall": data["prediction"]["overall"], "advice": data["prediction"]["advice"]},
        }
    elif tier == "premium":
        data["tier"] = "premium"
        data["yearly"] = _yearly(data)
        data["deep_advice"] = _deep_advice(data)
        # ¥1.99 版增值：AI 千字大师解读（LLM 失败回退 None，不影响交付）
        ai_text = await ai_deep_reading(data)
        if ai_text:
            data["ai_reading"] = ai_text
            logger.info(f"AI深度解读生成成功: {len(ai_text)}字")
        else:
            logger.warning("AI深度解读不可用，交付结构化内容（deep_advice）")
        return data
    else:
        data["tier"] = "detailed"
        return data


def _yearly(data: dict) -> dict:
    import datetime
    year = datetime.datetime.now().year
    DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    DIZHI_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
                '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    dizhi = DIZHI[(year-4)%12]
    ywx = DIZHI_WX[dizhi]
    twx = data["ti"]["element"]
    from app.meihua_engine import WUXING_SHENG, WUXING_KE
    if ywx == twx: s = f'{year}{dizhi}年，流年{ywx}与体卦{twx}比和，运势平稳。'
    elif WUXING_SHENG.get(ywx) == twx: s = f'{year}{dizhi}年，流年{ywx}生体卦{twx}，得岁运之助，运势上扬。'
    elif WUXING_SHENG.get(twx) == ywx: s = f'{year}{dizhi}年，体卦{twx}生流年{ywx}，泄气之年，付出多回报需等。'
    elif WUXING_KE.get(ywx) == twx: s = f'{year}{dizhi}年，流年{ywx}克体卦{twx}，受岁运压制，宜守不宜攻。'
    else: s = f'{year}{dizhi}年，体卦{twx}克流年{ywx}，虽可制之但需耗力。'
    return {"year":year, "dizhi":dizhi, "year_wuxing":ywx, "analysis":s}


def _deep_advice(data: dict) -> str:
    ti, yong, wx = data["ti"], data["yong"], data["wuxing"]
    ben, hu, bian = data["ben_hex"], data.get("hu_hex"), data.get("bian_hex")
    parts = []
    if wx["level"] == "吉":
        parts.append(f'【行动】{ti["gua"]}卦{ti["image"]}，宜主动出击。用卦{yong["gua"]}生助体卦，外部有利。')
    elif wx["level"] == "凶":
        parts.append(f'【行动】用卦{yong["gua"]}({yong["element"]})克体卦{ti["gua"]}({ti["element"]})，宜退守。')
    else:
        parts.append(f'【行动】体用平稳，按部就班。')
    if hu:
        parts.append(f'【过程】互卦{hu["name"]}（{hu["brief"]}）暗示过程中会经历{hu.get("upper_attr",{}).get("image","")}的阶段。')
    if bian:
        parts.append(f'【趋势】变卦{bian["name"]}（{bian["brief"]}）为最终走向。')
    ea = {'金':'宜穿白色银色，方位利西北','木':'宜穿绿色青色，方位利东方',
          '水':'宜穿黑色蓝色，方位利北方','火':'宜穿红色紫色，方位利南方',
          '土':'宜穿黄色棕色，方位利中央'}
    parts.append(f'【调理】体卦{ti["element"]}，{ea.get(ti["element"],"")}。')
    return '\n'.join(parts)
