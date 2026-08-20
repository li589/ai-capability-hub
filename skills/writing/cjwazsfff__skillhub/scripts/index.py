#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爆款文案生成脚本。

接收关键词，调用后端 API 完成支付并生成爆款文案。

用法：
    python3 index.py <keyword> [--out PATH]

base url 默认 https://skills.yanxuegd.com（写死在脚本里）。

退出码：
    0   成功，文案已输出
    2   输入错误（未提供关键词）
    4   请求失败（API 返回错误）
    5   支付未完成（订单未支付或支付失败）
    6   网络错误

============================================================================
接口契约
----------------------------------------------------------------------------
1. POST /api/orders/skillhub - 创建订单
   请求体：{"skill_id": "yyj-video", "skill_version": "v1.0"}
   响应：HTTP 402 {"WeixinPay": {"WeixinPay-Required": "pay_code_xxx"}, "out_trade_no": "xxx"}

2. POST /api/orders/pay-status - 查询订单状态
   请求头：X-Out-Trade-No: <订单号>
   请求体：{"out_trade_no": "xxx"}
   响应：HTTP 200/402 {"code": "NOT_PAID|PAID_NOT_USED|ALREADY_USED"}

3. POST /api/analytics/wenan - 生成文案
   请求头：X-Out-Trade-No: <订单号>
   请求体：{"keyword": "xxx", "out_trade_no": "xxx"}
============================================================================
"""

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

# 固定 base url
BASE_URL = "https://skills.yanxuegd.com"

# 接口路径
PATH_CREATE_ORDER = "/api/orders/skillhub"
PATH_QUERY_ORDER = "/api/orders/pay-status"
PATH_WENAN = "/api/analytics/wenan"

# SkillHub 配置
SKILL_ID = "yyj-video"
SKILL_VERSION = "v1.0"

# SSL 上下文（支持跳过验证）
SSL_CONTEXT = None


def init_ssl_context():
    """初始化 SSL 上下文，支持通过环境变量跳过 SSL 验证。"""
    global SSL_CONTEXT
    skip_verify = os.environ.get("LY_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes")
    if skip_verify:
        SSL_CONTEXT = ssl.create_default_context()
        SSL_CONTEXT.check_hostname = False
        SSL_CONTEXT.verify_mode = ssl.CERT_NONE
    else:
        SSL_CONTEXT = ssl.create_default_context()


def log(*args, **kwargs):
    """进度/错误信息打到 stderr，避免污染 stdout。"""
    print(*args, file=sys.stderr, flush=True, **kwargs)


def fail(code, message):
    log(message)
    sys.exit(code)


def order_headers(out_trade_no=None, with_json=False):
    """订单相关接口的请求头。"""
    headers = {}
    if out_trade_no:
        headers["X-Out-Trade-No"] = out_trade_no
    if with_json:
        headers["Content-Type"] = "application/json"
    return headers


def parse_json(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def http_request(method, url, headers=None, body=None, timeout=60):
    """发起一次 HTTP 请求，返回 (status, body_text)。"""
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def create_order(base_url):
    """步骤1：创建订单，返回订单号和支付授权码。"""
    url = base_url.rstrip("/") + PATH_CREATE_ORDER
    body = json.dumps({
        "skill_id": SKILL_ID,
        "skill_version": SKILL_VERSION,
        "product_id": 0
    }, ensure_ascii=False)

    log("正在创建订单...")

    try:
        status, text = http_request("POST", url, headers=order_headers(None, True),
                                    body=body, timeout=60)
    except urllib.error.URLError as e:
        fail(6, "网络错误：%s（请检查服务可达性：%s）" % (e, base_url))

    payload = parse_json(text)
    if payload is None:
        fail(4, "返回非 JSON（HTTP %d）：%s" % (status, text[:200]))

    # 创建订单成功返回 402
    if status == 402 and payload.get("code") == "PAYMENT_REQUIRED":
        weixin_pay = payload.get("WeixinPay", {})
        payment_code = weixin_pay.get("WeixinPay-Required", "")
        out_trade_no = payload.get("out_trade_no", "")

        if not payment_code or not out_trade_no:
            fail(4, "订单创建成功但缺少必要字段：%s" % text[:200])

        log("✅ 订单创建成功")
        log("   订单号：%s" % out_trade_no)
        log("   金额：%s %s" % (payload.get("amount"), payload.get("currency")))
        log("")
        log("⚠️  请使用微信支付完成支付：")
        log("   支付授权码：%s" % payment_code)
        log("")
        log("💡 提示：请在小程序中完成支付后，按回车继续...")

        # 等待用户完成支付（简单实现：等待用户按回车）
        try:
            input("支付完成后按回车继续...")
        except EOFError:
            pass

        return out_trade_no
    else:
        msg = payload.get("message") or payload.get("msg") or "未知错误"
        fail(4, "创建订单失败：HTTP %d，message=%s" % (status, msg))


def query_order_status(base_url, out_trade_no):
    """步骤2：查询订单状态，返回是否已支付可用。"""
    url = base_url.rstrip("/") + PATH_QUERY_ORDER
    body = json.dumps({"out_trade_no": out_trade_no}, ensure_ascii=False)

    try:
        status, text = http_request("POST", url, headers=order_headers(out_trade_no, True),
                                    body=body, timeout=60)
    except urllib.error.URLError as e:
        fail(6, "网络错误：%s" % e)

    payload = parse_json(text)
    if payload is None:
        fail(4, "返回非 JSON（HTTP %d）：%s" % (status, text[:200]))

    code = payload.get("code", "")

    # 已支付已使用
    if code == "ALREADY_USED":
        log("✅ 订单已使用过，返回缓存内容")
        return "ALREADY_USED"

    # 已支付未使用
    if code == "PAID_NOT_USED":
        log("✅ 订单已支付，可使用")
        return "PAID_NOT_USED"

    # 未支付
    if code == "NOT_PAID" or status == 402:
        return "NOT_PAID"

    # 其他错误
    msg = payload.get("message") or "未知错误"
    fail(4, "查询订单状态失败：%s" % msg)


def generate_wenan(base_url, keyword, out_trade_no):
    """步骤3：调用业务接口生成文案。"""
    url = base_url.rstrip("/") + PATH_WENAN
    body = json.dumps({
        "keyword": keyword,
        "out_trade_no": out_trade_no
    }, ensure_ascii=False)

    log("正在生成文案，关键词：%s" % keyword)

    try:
        status, text = http_request("POST", url, headers=order_headers(out_trade_no, True),
                                    body=body, timeout=60)
    except urllib.error.URLError as e:
        fail(6, "网络错误：%s" % e)

    payload = parse_json(text)
    if payload is None:
        fail(4, "返回非 JSON（HTTP %d）：%s" % (status, text[:200]))

    if status not in (200, 201):
        msg = payload.get("msg") or payload.get("message") or "未知错误"
        fail(4, "请求失败：HTTP %s，message=%s" % (status, msg))

    # 处理退款情况
    if payload.get("code") == "REFUNDED":
        reason = payload.get("refund_reason", "未知原因")
        fail(4, "服务无法提供付费内容，已发起全额退款。原因：%s" % reason)

    content = payload.get("content", "")
    if not content:
        fail(4, "返回数据中缺少 content 字段")

    already_fulfilled = payload.get("already_fulfilled", False)
    if already_fulfilled:
        log("✅ 返回缓存的文案内容")
    else:
        log("✅ 文案生成成功")

    return content


def wait_for_payment(base_url, out_trade_no, max_retries=30, interval=2):
    """轮询等待用户完成支付。"""
    log("等待支付完成...")
    for i in range(max_retries):
        time.sleep(interval)
        status = query_order_status(base_url, out_trade_no)
        if status == "PAID_NOT_USED" or status == "ALREADY_USED":
            return True
        if i % 5 == 0:
            log("  等待中... (%d/%d)" % (i + 1, max_retries))

    fail(5, "支付超时，请稍后重试或使用已支付的订单号")


def main():
    parser = argparse.ArgumentParser(description="爆款文案生成")
    parser.add_argument("keyword", help="文案关键词")
    parser.add_argument("--out", default=None, help="输出文件路径（可选）")
    parser.add_argument("--out-trade-no", default=None, help="已有订单号（可选，跳过创建订单步骤）")
    args = parser.parse_args()

    if not args.keyword:
        parser.error("请提供文案关键词")

    # 初始化 SSL
    init_ssl_context()

    base_url = BASE_URL

    out_trade_no = args.out_trade_no

    # 步骤1：如果没有订单号，创建新订单
    if not out_trade_no:
        out_trade_no = create_order(base_url)

    # 步骤2：查询订单状态，如果未支付则等待
    status = query_order_status(base_url, out_trade_no)
    if status == "NOT_PAID":
        wait_for_payment(base_url, out_trade_no)
    elif status == "ALREADY_USED":
        log("✅ 订单已使用过，将返回缓存内容")

    # 步骤3：生成文案
    content = generate_wenan(base_url, args.keyword, out_trade_no)

    # 输出结果
    output = json.dumps({
        "keyword": args.keyword,
        "out_trade_no": out_trade_no,
        "content": content
    }, ensure_ascii=False, indent=2)

    saved = None
    if args.out:
        try:
            out_path = args.out
            if os.path.isdir(args.out):
                safe_keyword = "".join(c if c.isalnum() or c in "._-" else "_" for c in args.keyword)
                out_path = os.path.join(args.out, "wenan-%s.json" % safe_keyword)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(output)
                if not output.endswith("\n"):
                    f.write("\n")
            saved = os.path.abspath(out_path)
        except OSError as e:
            log("⚠️ 写入文件失败：%s（仍会在对话中渲染）" % e)

    if saved:
        log("结果已保存到：%s" % saved)

    # 输出到 stdout
    print(output)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
