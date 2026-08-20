#!/usr/bin/env python3
import json
import os
import sys

client_id = os.environ.get("CODEBUDDY_PLUGIN_OPTION_XUNPANYUN_CLIENT_ID")
client_secret = os.environ.get("CODEBUDDY_PLUGIN_OPTION_XUNPANYUN_CLIENT_SECRET")

def emit(code, message, configured=False, next_action=None):
    payload = {"ok": False, "code": code, "message": message, "configured": configured}
    if next_action:
        payload["nextAction"] = next_action
        payload["plugin"] = "xunpanyun-crm-runtime"
    print(json.dumps(payload, ensure_ascii=False))

if len(sys.argv) >= 3 and sys.argv[1:3] == ["auth", "status"]:
    if client_id and client_secret:
        print(json.dumps({"ok": True, "code": "AUTH_CONFIGURED", "configured": True}, ensure_ascii=False))
        raise SystemExit(0)
    emit("AUTH_REQUIRED", "请完成询盘云API授权；授权后将自动继续原任务。", next_action="OPEN_PLUGIN_CONFIG")
    raise SystemExit(2)

write_commands = {"create", "update", "pool", "opportunity-stage", "order-data"}
offline_allowed = (
    len(sys.argv) == 1
    or any(arg in {"-h", "--help"} for arg in sys.argv[1:])
    or "--dry-run" in sys.argv[1:]
    or (len(sys.argv) > 1 and sys.argv[1] in write_commands and "--confirm" not in sys.argv[1:])
)

if (not client_id or not client_secret) and not offline_allowed:
    emit("AUTH_REQUIRED", "请完成询盘云API授权；授权后将自动继续原任务。", next_action="OPEN_PLUGIN_CONFIG")
    raise SystemExit(2)

if client_id and client_secret:
    os.environ["XUNPANYUN_CLIENT_ID"] = client_id
    os.environ["XUNPANYUN_CLIENT_SECRET"] = client_secret

if len(sys.argv) >= 3 and sys.argv[1:3] == ["auth", "check"]:
    sys.argv = [sys.argv[0], "token"]

from xunpanyun_client import main
main()
