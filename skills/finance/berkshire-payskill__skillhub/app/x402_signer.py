"""X402 AI 预下单签名模块 - SkillHub 开发者密钥签名"""

import json
import base64
import time
import secrets
import asyncio
import httpx
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import SKILLHUB_PUB_KEY_ID, SKILLHUB_PRIVATE_KEY, SKILLHUB_DEVELOPER_ID

logger = logging.getLogger(__name__)

AI_PREORDER_URL = "https://payapp.weixin.qq.com/palmpayminiapp/clawagentpay/preorder"


def _load_private_key():
    """加载 SkillHub 开发者私钥 (PEM 格式, RSA 2048)"""
    pem_data = SKILLHUB_PRIVATE_KEY.encode("utf-8")
    if b"\\n" in pem_data:
        pem_data = pem_data.replace(b"\\n", b"\n")
    return serialization.load_pem_private_key(pem_data, password=None)


def sign_x402(payment_required_b64: str) -> dict:
    """对 payment_required 做 SHA256withRSA 签名"""
    timestamp = str(int(time.time()))
    nonce_str = secrets.token_hex(16)

    sign_string = (
        f"POST\n"
        f"/palmpayminiapp/clawagentpay/preorder\n"
        f"{timestamp}\n"
        f"{nonce_str}\n"
        f"{payment_required_b64}\n"
    )

    private_key = _load_private_key()
    signature = private_key.sign(
        sign_string.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    sig_b64 = base64.b64encode(signature).decode("utf-8")

    return {
        "signature": sig_b64,
        "timestamp": timestamp,
        "nonce_str": nonce_str,
    }


def build_l2_payload(code_url: str, amount: int, title: str, expires_minutes: int = 15) -> dict:
    """构造 L2 业务 JSON"""
    return {
        "skill_info": {
            "skill_id": "berkshire-analyst",
            "skill_version": "1.0.0",
        },
        "pay_type": "SKILL_PAY",
        "pay_mode": "AUTH_AND_PAY",
        "pay_items": [
            {
                "product_id": f"MH{time.strftime('%y%m%d')}A001",
                "product_name": title,
                "amount": amount,
                "pay_data": {
                    "type": "code_url",
                    "value": code_url,
                },
            }
        ],
        "expires_at": str(int(time.time()) + expires_minutes * 60),
    }


async def call_ai_preorder(code_url: str, amount: int = 199, title: str = "ViralLens视频分析") -> str:
    """调用 X402 AI 预下单接口，返回 payment_code"""
    # 1. 构造 L2
    l2 = build_l2_payload(code_url, amount, title)

    # 2. Base64 编码 L2
    l2_bytes = json.dumps(l2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payment_required_b64 = base64.b64encode(l2_bytes).decode("utf-8")

    # 3. 签名
    sign_result = sign_x402(payment_required_b64)

    # 4. 组装 L1 请求体
    l1 = {
        "signature_type": "SKILLHUB-SHA256-RSA2048",
        "developer_platform": "SKILLHUB",
        "developer_id": SKILLHUB_DEVELOPER_ID,
        "pub_key_id": SKILLHUB_PUB_KEY_ID,
        "nonce_str": sign_result["nonce_str"],
        "timestamp": sign_result["timestamp"],
        "signature": sign_result["signature"],
        "payment_required": payment_required_b64,
    }

    logger.info(f"X402 L1 payload: {json.dumps({k: v[:30]+'...' if isinstance(v, str) and len(v) > 30 else v for k, v in l1.items()}, ensure_ascii=False)}")
    logger.info(f"X402 L2 decoded: {json.dumps(l2, ensure_ascii=False)}")

    # 5. POST 请求 (allow redirects for 302)
    # clawagentpay 网关间歇性故障(302→错误页/空响应)，自动重试最多3次
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False, follow_redirects=True) as client:
                resp = await client.post(
                    AI_PREORDER_URL,
                    json=l1,
                    headers={"Content-Type": "application/json"},
                )

            if resp.status_code != 200:
                raise Exception(f"AI预下单失败, HTTP {resp.status_code}: {resp.text[:200]}")

            result = resp.json()
            payment_code = result.get("payment_code", "")
            if not payment_code:
                raise Exception(f"AI预下单返回无 payment_code: {result}")

            if attempt > 0:
                logger.info(f"AI预下单第{attempt + 1}次尝试成功")
            logger.info(f"AI预下单成功: payment_code={payment_code[:20]}...")
            return payment_code
        except Exception as e:
            last_err = e
            logger.warning(f"AI预下单第{attempt + 1}次失败: {e}")
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise Exception(f"AI预下单3次重试均失败: {last_err}")
