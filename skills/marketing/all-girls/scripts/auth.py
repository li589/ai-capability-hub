"""
Mini App Order - 微信扫码登录 + Token 管理
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error

try:
    from .common import BASE_URL, API_PREFIX, TIMEOUT, TOKEN_CACHE_FILE, _SKILL_DIR
except ImportError:
    from common import BASE_URL, API_PREFIX, TIMEOUT, TOKEN_CACHE_FILE, _SKILL_DIR


# =====================================================
# Token 持久化
# =====================================================

def _load_token_cache() -> dict:
    """从本地读取缓存的 token 信息。"""
    if TOKEN_CACHE_FILE.exists():
        try:
            return json.loads(TOKEN_CACHE_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {}


def _save_token_cache(data: dict):
    """将 token 信息写入本地缓存。"""
    TOKEN_CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    # 设置仅当前用户可读（保护 token 安全）
    TOKEN_CACHE_FILE.chmod(0o600)


def _clear_token_cache():
    """清除本地 token 缓存（登出）。"""
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()


# =====================================================
# HTTP 基础函数（内部使用，不导出）
# =====================================================

def _http_get(url: str, headers: dict = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post(url: str, payload: dict, headers: dict = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    _headers = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=_headers, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _check_api_result(resp: dict):
    """检查接口返回是否成功（code != "000" 或 success != true 视为异常）。"""
    if resp.get("code") != "000" or resp.get("success") is not True:
        raise RuntimeError(f"接口返回异常: {resp.get('message', '未知错误')}")


# =====================================================
# 微信扫码登录流程
# =====================================================

def get_qr_code() -> dict:
    """
    阶段 1：获取登录二维码，下载到本地文件。

    此函数只获取二维码并保存，不轮询。
    调用后会打印 JSON，WorkBuddy 应解析该 JSON，展示二维码图片供用户扫码。

    Returns:
        {"action": "show_qr", "pcKey": "...", "qr_file": "/path/to/qr.jpg"}

    输出到 stdout（JSON 格式），供 WorkBuddy 解析。
    """
    print("正在生成登录二维码...")
    resp = _http_get(f"{BASE_URL}{API_PREFIX}/identity/pc/getQrImg")
    _check_api_result(resp)

    data = resp.get("data", {})
    pc_key = data.get("pcKey")
    qr_img = data.get("qrImg")  # 相对路径，如 /wxqr/2026-06-05/xxx.jpg

    if not pc_key or not qr_img:
        raise RuntimeError(f"获取二维码失败: {resp}")

    # 二维码图片托管在 img.wawo.cc（腾讯云 COS），不能用 7.wawo.cc（会被 WAF 拦截）
    qr_url = f"https://img.wawo.cc{qr_img}"

    # 下载二维码图片到本地
    qr_file = str(_SKILL_DIR / ".qr_code.jpg")
    urllib.request.urlretrieve(qr_url, qr_file)

    result = {"action": "show_qr", "pcKey": pc_key, "qr_file": qr_file, "qr_url": qr_url}

    # 输出 pcKey 供后续轮询使用
    print(f"\npcKey: {pc_key}")

    # 输出可以原样复制到回复中的 Markdown 图片行
    print(f"\n--- 复制下面这行到回复中即可展示二维码 ---")
    print(f"![微信扫码登录]({qr_url})")
    print(f"--- 二维码图片地址 ---")

    return result


def poll_for_token(pc_key: str, timeout: int = 300) -> str:
    """
    阶段 2：轮询等待用户扫码确认，获取 access_token。

    Args:
        pc_key: 阶段 1 获取的 pcKey
        timeout: 轮询超时时间（秒），默认 300 秒（5 分钟）

    Returns:
        access_token 字符串

    Raises:
        RuntimeError: 超时未扫码
    """
    print(f"\n⏳ 等待扫码确认（最多 {timeout} 秒）...")
    deadline = time.time() + timeout

    while time.time() < deadline:
        time.sleep(2)
        try:
            poll_resp = _http_post(
                f"{BASE_URL}{API_PREFIX}/identity/pc/getAccessToken",
                {"pcKey": pc_key},
            )
        except Exception as e:
            print(f"轮询异常: {e}，继续重试...")
            continue

        if poll_resp.get("code") == "000":
            token = poll_resp.get("data", "")
            if token:
                cache = {
                    "token": token,
                    # 接口未返回过期时间，默认 24 小时
                    "expires_at": int(time.time()) + 86400,
                }
                _save_token_cache(cache)
                print("🎉 登录成功！Token 已保存")
                return token

    raise RuntimeError(f"登录超时（{timeout} 秒内未扫码确认），请重新尝试")


def login_with_qrcode() -> str:
    """
    微信扫码登录（兼容旧版单阶段流程）。

    保留此函数以兼容直接调用场景。
    新流程推荐使用 get_qr_code() + poll_for_token() 两阶段模式。
    """
    result = get_qr_code()
    print(f"\n📱 请用微信扫描二维码登录\n（二维码已保存至: {result['qr_file']}）")
    return poll_for_token(result["pcKey"])


def get_valid_token():
    """
    获取有效的 access_token。
    优先从缓存读取；已过期则清除缓存并返回 None。

    返回 None 时，调用者应：
    1. 调用 get_qr_code() 获取并展示二维码
    2. 用户扫码后调用 poll_for_token(pc_key) 获取 token
    3. 然后重新调用 get_valid_token() 获取缓存中的 token
    """
    cache = _load_token_cache()

    if cache.get("token"):
        expires_at = cache.get("expires_at", 0)
        # 提前 5 分钟判定为失效，避免刚好在请求时 401
        if time.time() < expires_at - 300:
            return cache["token"]

        print("⚠️ Token 已过期，需要重新扫码登录")
        _clear_token_cache()

    # 无有效 token → 返回 None，由调用者决定如何处理
    return None


def logout():
    """登出，清除本地 token 缓存。"""
    _clear_token_cache()
    print("已退出登录，Token 已清除。")
