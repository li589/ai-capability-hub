# -*- coding: utf-8 -*-
"""
服务器配置工具：首次使用配置 OpenAPI 服务器地址 + 登录账号。
不同客户环境 IP/端口/账号不同，**不预制任何账号**，由使用者首次运行时填写。

用法（AI 对话模式，用命令行参数；或直接跑交互式引导）:
  python setup_config.py                     # 交互式引导（问 IP/端口/账号/密码 → 测试登录 → 保存）
  python setup_config.py --check             # 检查配置是否完整可用（连通 + 登录）
  python setup_config.py --get               # 显示当前配置（密码打码）
  python setup_config.py --set-host <IP> --set-port <端口>           # 只改服务器
  python setup_config.py --set-user <账号> --set-pass <密码>          # 只改账号
  python setup_config.py --set-sso-appid <appId> --set-sso-secret <appSecret>  # 配置 SSO 应用（可选）

返回码: 0=可用  1=不可用/未配置  2=已修改保存
"""
import sys
import json
import argparse
import getpass
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
TEST_ENDPOINT = "/oapi-doc/v1/group"  # 文档分组接口（无需鉴权，返回 JSON 即连通）


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def test_connection(host, port, timeout=8):
    """测试 OpenAPI 连通性：GET 文档分组接口，能返回 JSON 即认为通"""
    url = f"http://{host}:{port}{TEST_ENDPOINT}"
    try:
        r = requests.get(url, timeout=timeout)
        try:
            r.json()
            return True, f"连接成功（HTTP {r.status_code}）"
        except Exception:
            return False, f"返回非 JSON（HTTP {r.status_code}）"
    except requests.exceptions.ConnectTimeout:
        return False, "连接超时，请检查 IP/端口/网络"
    except requests.exceptions.ConnectionError as e:
        return False, f"连接失败: {str(e)[:120]}"
    except Exception as e:
        return False, f"异常: {str(e)[:120]}"


def mask(s):
    """打码显示（保留首尾 2 字符）"""
    s = str(s or "")
    if len(s) <= 4:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def is_configured(cfg):
    """检查是否已配置完整（服务器 + 账号）"""
    server = cfg.get("server", {})
    account = cfg.get("auth", {}).get("account", {})
    host = server.get("host")
    user = account.get("user_name")
    return bool(host and user)


def interactive():
    """交互式引导配置（IP/端口/账号/密码，密码不回显）"""
    print("=" * 52)
    print("  OpenAPI 服务器 + 登录账号配置")
    print("  （不预制任何客户环境信息，首次使用请填写）")
    print("=" * 52)
    cfg = load_config()
    cur = cfg.get("server", {})
    acct = cfg.get("auth", {}).get("account", {})
    print(f"  当前服务器: {cur.get('host','未设置') or '未设置'}:{cur.get('port','20201') or '20201'}")
    print(f"  当前账号  : {acct.get('user_name','未设置') or '未设置'}")
    print("  直接回车 = 保持当前值（空则视为不修改）")
    print("-" * 52)

    host = input("  服务器 IP   [%s]: " % (cur.get("host") or "")).strip() or cur.get("host") or ""
    try:
        port = int(input("  端口        [%s]: " % (cur.get("port") or "20201")).strip() or cur.get("port") or 20201)
    except ValueError:
        print("端口格式错误，保持原值")
        port = cur.get("port") or 20201
    user = input("  登录账号   [%s]: " % (acct.get("user_name") or "")).strip() or acct.get("user_name") or ""
    # 密码不回显；已有密码时回车=保留
    if acct.get("password"):
        pwd = getpass.getpass("  登录密码   [已设置，回车保留]: ") or acct.get("password") or ""
    else:
        pwd = getpass.getpass("  登录密码   (输入，不回显): ")

    if not host or not user:
        print("IP 与账号不能为空")
        return 1

    ok, msg = test_connection(host, port)
    print(f"  [连通测试] {msg}")
    cfg["server"] = {"host": host, "port": port}
    cfg.setdefault("auth", {})["account"] = {
        "login_endpoint": "/account/v1/login",
        "user_name": user,
        "password": pwd,
        "language": "zh_CN",
        "platform": "PC",
    }
    # 配置变更后清除缓存的 token
    cfg["auth"].pop("token", None)
    cfg["auth"].pop("refresh_token", None)
    cfg["auth"].pop("token_at", None)
    save_config(cfg)
    if ok:
        print(f"  ✅ 已保存: {host}:{port} / {user}（密码已加密存储于本地 config.json）")
    else:
        print("  ⚠️ 已保存配置，但连通性测试失败，请检查后重试")
    return 0 if ok else 2


def main():
    parser = argparse.ArgumentParser(description="OpenAPI 服务器与账号配置工具（首次使用必配）")
    parser.add_argument("--check", action="store_true", help="检查配置是否完整可用")
    parser.add_argument("--get", action="store_true", help="显示当前配置（密码打码）")
    parser.add_argument("--set-host", help="服务器 IP")
    parser.add_argument("--set-port", type=int, help="端口")
    parser.add_argument("--set-user", help="登录账号")
    parser.add_argument("--set-pass", help="登录密码（命令行传入有泄漏风险，建议用交互式）")
    parser.add_argument("--set-sso-appid", help="SSO 应用 ID（可选）")
    parser.add_argument("--set-sso-secret", help="SSO 应用密钥（可选）")
    args = parser.parse_args()

    cfg = load_config()
    cur = cfg.get("server", {})
    acct = cfg.get("auth", {}).get("account", {})
    current = f"{cur.get('host') or '未设置'}:{cur.get('port') or '20201'}"
    account_str = acct.get("user_name") or "未设置"

    if args.get:
        print(f"服务器: {current}  |  账号: {account_str}  |  密码: {mask(acct.get('password')) if acct.get('password') else '未设置'}")
        return 0

    if args.set_host or args.set_port is not None or args.set_user or args.set_pass is not None \
            or args.set_sso_appid or args.set_sso_secret:
        if args.set_host:
            cfg["server"]["host"] = args.set_host
        if args.set_port is not None:
            cfg["server"]["port"] = args.set_port
        if args.set_user:
            cfg["auth"].setdefault("account", {})["user_name"] = args.set_user
        if args.set_pass is not None:
            cfg["auth"].setdefault("account", {})["password"] = args.set_pass
        if args.set_sso_appid:
            cfg["auth"].setdefault("sso", {})["app_id"] = args.set_sso_appid
        if args.set_sso_secret:
            cfg["auth"].setdefault("sso", {})["app_secret"] = args.set_sso_secret
        # 清除缓存 token
        cfg["auth"].pop("token", None)
        cfg["auth"].pop("refresh_token", None)
        cfg["auth"].pop("token_at", None)
        save_config(cfg)
        host = cfg["server"].get("host")
        port = cfg["server"].get("port")
        ok, msg = test_connection(host, port) if host else (False, "未配置 IP")
        print(f"[测试] {msg}")
        print(f"✅ 已保存。服务器: {host}:{port} ｜ 账号: {cfg['auth'].get('account', {}).get('user_name', '') or '未设置'}")
        return 0 if ok else 2

    if args.check:
        if not is_configured(cfg):
            print("❌ 未配置完整。请运行: python setup_config.py（交互式填写 IP/端口/账号/密码）")
            return 1
        host, port = cur.get("host"), cur.get("port") or 20201
        ok, msg = test_connection(host, port)
        print(f"服务器: {host}:{port} ｜ 账号: {account_str} ｜ {msg}")
        return 0 if ok else 1

    # 无参数 → 交互式
    return interactive()


if __name__ == "__main__":
    sys.exit(main())
