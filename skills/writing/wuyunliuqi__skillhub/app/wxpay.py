"""微信支付客户端 - Native 下单 / 查单 / 退款

支持两种模式:
- mock: 本地测试，返回模拟数据
- live: 真实调用微信支付 V3 API
"""

import time
import secrets
import base64
import json
import logging
import httpx

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import MODE, MCH_ID, APP_ID, MCH_SERIAL, MCH_APIV3_KEY, MCH_PRIVATE_KEY

logger = logging.getLogger(__name__)

WX_BASE = "https://api.mch.weixin.qq.com"


def _load_mch_private_key():
    """加载微信支付商户私钥"""
    pem_data = MCH_PRIVATE_KEY.encode("utf-8") if isinstance(MCH_PRIVATE_KEY, str) else MCH_PRIVATE_KEY
    if b"\\n" in pem_data:
        pem_data = pem_data.replace(b"\\n", b"\n")
    return serialization.load_pem_private_key(pem_data, password=None)


def _sign_wechat_request(method: str, url_path: str, timestamp: str, nonce_str: str, body: str) -> str:
    """构造微信支付 V3 API 签名 (WECHATPAY2-SHA256-RSA2048)"""
    sign_string = f"{method}\n{url_path}\n{timestamp}\n{nonce_str}\n{body}\n"
    private_key = _load_mch_private_key()
    signature = private_key.sign(
        sign_string.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _build_auth_header(method: str, url_path: str, body: str = "") -> dict:
    """构造微信支付 Authorization header"""
    timestamp = str(int(time.time()))
    nonce_str = secrets.token_hex(16)
    signature = _sign_wechat_request(method, url_path, timestamp, nonce_str, body)

    auth = (
        f'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{MCH_ID}",'
        f'nonce_str="{nonce_str}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{MCH_SERIAL}",'
        f'signature="{signature}"'
    )
    return {
        "Authorization": auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ==================== Mock 模式 ====================

async def _mock_native_order(out_trade_no: str, description: str, amount: int) -> str:
    logger.info(f"[MOCK] Native下单: out_trade_no={out_trade_no}, amount={amount}分")
    return f"weixin://wxpay/bizpayurl?pr=mock_{out_trade_no}"


async def _mock_query_order(out_trade_no: str) -> tuple:
    logger.info(f"[MOCK] 查单: out_trade_no={out_trade_no}")
    return "SUCCESS", f"mock_tx_{out_trade_no}"


async def _mock_refund(out_trade_no: str, amount: int, reason: str) -> str:
    logger.info(f"[MOCK] 退款: out_trade_no={out_trade_no}")
    return f"RF_{out_trade_no}"


# ==================== Live 模式 ====================

async def _live_native_order(out_trade_no: str, description: str, amount: int) -> str:
    """真实调用微信 Native 下单接口"""
    from app.config import BASE_URL
    url_path = "/v3/pay/transactions/native"

    from datetime import datetime, timedelta, timezone
    tz = timezone(timedelta(hours=8))
    expire = datetime.now(tz) + timedelta(seconds=900)
    time_expire_str = expire.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    body_dict = {
        "appid": APP_ID,
        "mchid": MCH_ID,
        "description": description[:127],
        "out_trade_no": out_trade_no[:32],
        "notify_url": f"{BASE_URL}/api/pay/notify",
        "time_expire": time_expire_str,
        "amount": {"total": amount, "currency": "CNY"},
    }
    body = json.dumps(body_dict, ensure_ascii=False)
    headers = _build_auth_header("POST", url_path, body)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{WX_BASE}{url_path}", content=body, headers=headers)

    if resp.status_code != 200:
        raise Exception(f"Native下单失败, HTTP {resp.status_code}: {resp.text}")

    result = resp.json()
    return result["code_url"]


async def _live_query_order(out_trade_no: str) -> tuple:
    """真实调用微信查单接口"""
    url_path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={MCH_ID}"
    headers = _build_auth_header("GET", url_path)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{WX_BASE}{url_path}", headers=headers)

    if resp.status_code != 200:
        raise Exception(f"查单失败, HTTP {resp.status_code}: {resp.text}")

    result = resp.json()
    return result.get("trade_state", ""), result.get("transaction_id", "")


async def _live_refund(out_trade_no: str, amount: int, reason: str) -> str:
    """真实调用微信退款接口"""
    from app.config import BASE_URL
    url_path = "/v3/refund/domestic/refunds"
    out_refund_no = f"RF_{out_trade_no}"

    body_dict = {
        "out_trade_no": out_trade_no,
        "out_refund_no": out_refund_no,
        "reason": reason[:80],
        "notify_url": f"{BASE_URL}/api/refund/notify",
        "amount": {"refund": amount, "total": amount, "currency": "CNY"},
    }
    body = json.dumps(body_dict, ensure_ascii=False)
    headers = _build_auth_header("POST", url_path, body)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{WX_BASE}{url_path}", content=body, headers=headers)

    if resp.status_code != 200:
        raise Exception(f"退款请求失败, HTTP {resp.status_code}: {resp.text}")

    result = resp.json()
    logger.info(f"退款受理: out_trade_no={out_trade_no}, out_refund_no={out_refund_no}, status={result.get('status')}")
    return out_refund_no


# ==================== 统一入口 ====================

async def native_order(out_trade_no: str, description: str, amount: int) -> str:
    """Native 下单，返回 code_url"""
    if MODE == "mock":
        return await _mock_native_order(out_trade_no, description, amount)
    return await _live_native_order(out_trade_no, description, amount)


async def query_order(out_trade_no: str) -> tuple:
    """查单，返回 (trade_state, transaction_id)"""
    if MODE == "mock":
        return await _mock_query_order(out_trade_no)
    return await _live_query_order(out_trade_no)


async def refund(out_trade_no: str, amount: int, reason: str) -> str:
    """退款，返回 out_refund_no"""
    if MODE == "mock":
        return await _mock_refund(out_trade_no, amount, reason)
    return await _live_refund(out_trade_no, amount, reason)
