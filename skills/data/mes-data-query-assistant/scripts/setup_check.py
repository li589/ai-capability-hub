# -*- coding: utf-8 -*-
"""
首次使用配置检查：验证数据库连接，引导填写 MySQL 参数，提供建账号脚本指引。

流程：
  1. 读取 config.json 的 database 配置（host/port/user/password/dbname）
  2. 尝试连接数据库
  3. 若连接成功 → 提示"连接正常"，并验证只读权限（尝试 SELECT）
  4. 若连接失败 → 输出诊断（缺参数 / 网络不通 / 账号密码错 / 账号不存在 / 权限不足），
     引导客户填写 MySQL IP/密码等参数，并提示建账号脚本（scripts/create_readonly_user.sql）

用法（必须用 venv python 跑，含 pymysql）：
  python setup_check.py            # 检查并诊断
  python setup_check.py --fill     # 交互式引导填写 config.json（host/port/dbname/password）
"""
import sys, os, json, getpass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(BASE, "config.json")
SQL_PATH = os.path.join(BASE, "scripts", "create_readonly_user.sql")

DEFAULT_USER = "mes_query"
DEFAULT_PORT = 3306


def load_cfg():
    if not os.path.exists(CFG_PATH):
        print(f"❌ 未找到配置文件: {CFG_PATH}")
        return None
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存: {CFG_PATH}")


def diagnose(db, e):
    """根据异常信息给出针对性诊断"""
    msg = str(e).lower()
    if not db.get("host"):
        return "❌ 缺少 MySQL 主机地址（host），请填写数据库服务器 IP"
    if not db.get("user"):
        return f"❌ 缺少用户名（user），默认为 {DEFAULT_USER}"
    if not db.get("password"):
        return "❌ 缺少密码（password），请填写 mes_query 账号的密码"
    if not db.get("dbname"):
        return "❌ 缺少数据库名（dbname），请填写 MES 数据库名"
    if "access denied" in msg:
        return ("❌ 账号密码错误或账号不存在。\n"
                "   请确认: ① 用户名/密码是否正确 ② 账号主机是否匹配客户端 IP（'%' 可任意主机）\n"
                "   若未建立 mes_query 账号，请执行 scripts/create_readonly_user.sql 建账号（见附录）")
    if "unknown database" in msg or "unknown database" in msg:
        return f"❌ 数据库名 {db.get('dbname')} 不存在，请确认库名"
    if "timeout" in msg or "timed out" in msg or "connect" in msg and "refused" in msg:
        return ("❌ 无法连接数据库服务器（网络不通或端口错误）。\n"
                "   请确认: ① IP 是否正确 ② 端口是否 3306 ③ 数据库是否内网可达")
    return f"❌ 连接失败: {e}"


def check():
    cfg = load_cfg()
    if not cfg:
        return
    db = cfg.get("database", {})
    missing = [k for k in ("host", "user", "password", "dbname") if not db.get(k)]
    if missing:
        print("⚠️ 数据库配置不完整，缺少字段:", ", ".join(missing))
        print("   请填写 config.json 的 database 段，或运行 setup_check.py --fill 引导填写")
        return

    import pymysql
    print(f"🔌 正在检查数据库连接: {db['user']}@{db['host']}:{db['port']}/{db['dbname']} …")
    try:
        conn = pymysql.connect(
            host=db["host"], port=int(db.get("port", DEFAULT_PORT)),
            user=db["user"], password=db["password"],
            database=db["dbname"], charset="utf8mb4",
            connect_timeout=10, read_timeout=30,
        )
    except Exception as e:
        print(diagnose(db, e))
        return

    # 连接成功，验证只读权限
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            ver = cur.fetchone()[0]
            cur.execute("SELECT 1")
            cur.fetchone()
        print(f"✅ 连接正常！MySQL {ver} / {db['dbname']} / 账号 {db['user']}")
        print("   只读校验: SELECT 通过（账号仅授 SELECT，DML/DDL 天然禁止）")
    except Exception as e:
        print(f"⚠️ 连接成功但查询失败: {e}")
    finally:
        conn.close()

    # 提示建账号脚本
    if os.path.exists(SQL_PATH):
        print(f"\n📄 若需重建只读账号，可用脚本: {SQL_PATH}")


def fill():
    """交互式引导填写数据库配置"""
    cfg = load_cfg() or {"database": {}}
    db = cfg.setdefault("database", {})
    print("🛠️  数据库配置引导（回车使用默认值）:")
    host = input(f"  MySQL 主机 IP（当前: {db.get('host', '未设置')}）: ").strip()
    if host:
        db["host"] = host
    port = input(f"  端口（默认 {DEFAULT_PORT}）: ").strip()
    db["port"] = int(port) if port else int(db.get("port", DEFAULT_PORT))
    user = input(f"  用户名（默认 {DEFAULT_USER}）: ").strip()
    db["user"] = user or db.get("user") or DEFAULT_USER
    pwd = getpass.getpass(f"  密码（当前: {'已设置' if db.get('password') else '未设置'}）: ").strip()
    if pwd:
        db["password"] = pwd
    dbname = input(f"  数据库名（当前: {db.get('dbname', '未设置')}）: ").strip()
    if dbname:
        db["dbname"] = dbname
    save_cfg(cfg)
    print("\n配置已更新，接下来运行 setup_check.py 验证连接:")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fill":
        fill()
    else:
        check()
