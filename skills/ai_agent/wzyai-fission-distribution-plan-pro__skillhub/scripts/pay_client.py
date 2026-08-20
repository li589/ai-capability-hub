#!/usr/bin/env python3
"""Stateless Pay Skill HTTPS client; prints compact JSON and writes no secrets."""
import argparse, json, os, sys, urllib.error, urllib.request
from urllib.parse import urlparse

def base_url():
    value = os.environ.get("PAY_SKILL_SERVICE_URL", "https://pay.wzyai.com").rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SystemExit("PAY_SKILL_SERVICE_URL must be an absolute HTTPS URL")
    return value

def retry_headers(payment_code, out_trade_no):
    if bool(payment_code) != bool(out_trade_no):
        raise SystemExit("payment retry requires both WeixinPay-Required and X-Out-Trade-No")
    if not payment_code:
        return {}
    return {"WeixinPay-Required": payment_code, "X-Out-Trade-No": out_trade_no}

def post(path, payload, headers=None):
    request_headers = {"Content-Type":"application/json","Accept":"application/json"}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(base_url()+path, json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(), request_headers, method="POST")
    try: response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as exc: response = exc
    raw = response.read(65537)
    if len(raw) > 65536: raise SystemExit("payment response exceeded 64 KiB")
    body = json.loads(raw or b"{}")
    payment_code = response.headers.get("WeixinPay-Required")
    if payment_code:
        body["weixinpay_required"] = payment_code
        node = body.setdefault("WeixinPay", {})
        if isinstance(node, dict):
            node.setdefault("WeixinPay-Required", payment_code)
            node.setdefault("prompt", "请将 WeixinPay-Required 作为 paymentCode 调用 weixinpay_pay，并由用户本人确认支付。")
    if response.headers.get("X-Out-Trade-No"): body["out_trade_no"] = response.headers["X-Out-Trade-No"]
    print(json.dumps(body, ensure_ascii=False, separators=(",", ":")))
    return 0 if response.status in (200,402,409,410) else 1

def main():
    p=argparse.ArgumentParser(); subs=p.add_subparsers(dest="command",required=True)
    a=subs.add_parser("authorize")
    for n in ("request_id","skill_id","skill_version","input_hash"): a.add_argument("--"+n.replace("_","-"),required=True)
    a.add_argument("--out-trade-no")
    i=subs.add_parser("invoke")
    for n in ("request_id","skill_id","skill_version","input_hash"): i.add_argument("--"+n.replace("_","-"),required=True)
    i.add_argument("--payment-code")
    i.add_argument("--out-trade-no")
    f=subs.add_parser("fulfill")
    for n in ("entitlement_id","entitlement_token","skill_id","skill_version","input_hash","result_digest"): f.add_argument("--"+n.replace("_","-"),required=True)
    args=p.parse_args()
    values=vars(args)
    if args.command == "invoke":
        payload={k:values[k] for k in ("request_id","skill_id","skill_version","input_hash")}
        headers=retry_headers(values.get("payment_code"), values.get("out_trade_no"))
        return post("/api/v1/pay-skill/invoke", payload, headers=headers)
    payload={k:v for k,v in values.items() if k!="command" and v is not None}
    return post("/api/v1/pay-skill/authorize" if args.command=="authorize" else "/api/v1/pay-skill/fulfillments", payload)

if __name__ == "__main__": sys.exit(main())
