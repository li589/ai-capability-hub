# -*- coding: utf-8 -*-
"""
Skillhub 网速测试技能
功能：下载测速 / 上传测速 / Ping延迟 / IP与运营商 / 文本图表 / 自定义节点
无第三方依赖，纯Python标准库
"""
import time
import socket
import random
import json
from urllib.request import Request, urlopen

CONFIG = {
    "test_nodes": [
        {"name": "Cloudflare 全球节点", "url": "http://speed.cloudflare.com/__down?bytes=10000000"},
        {"name": "CacheFly 国际节点", "url": "http://cachefly.cachefly.net/10mb.test"},
        {"name": "百度国内节点", "url": "https://www.baidu.com/favicon.ico"},
    ],
    "upload_url": "http://httpbin.org/post",
    "ping_host": "speed.cloudflare.com",
    "test_duration": 6,
    "ping_times": 4,
    "timeout": 7
}

def format_speed(bps):
    if bps < 1024:
        return f"{bps:.2f} bps"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.2f} Kbps"
    else:
        return f"{bps / (1024 * 1024):.2f} Mbps"

def get_ip_info():
    try:
        req = Request("https://ipinfo.io/json", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=5) as f:
            data = json.loads(f.read().decode())
        return {
            "ip": data.get("ip", "未知"),
            "city": data.get("city", "未知"),
            "region": data.get("region", "未知"),
            "isp": data.get("org", "未知运营商")
        }
    except:
        return {"ip": "获取失败", "city": "获取失败", "isp": "获取失败"}

def generate_ascii_chart(download, upload, ping):
    dv = min(download.get("speed", 0), 100)
    uv = min(upload.get("speed", 0), 100)
    pv = min(ping.get("avg", 9999) / 10, 100)
    db = "█" * int(dv) + "░" * (100 - int(dv))
    ub = "█" * int(uv) + "░" * (100 - int(uv))
    pb = "█" * int(pv) + "░" * (100 - int(pv))
    return f"""
📊 测速可视化图表
==================================================
下载速度：{download.get('text','0.00 Mbps'):>12} | {db}
上传速度：{upload.get('text','0.00 Mbps'):>12} | {ub}
网络延迟：{ping.get('avg','9999'):>9} ms    | {pb}
==================================================
说明：█=当前速度  ░=参考刻度 | 延迟越低越好
"""

def test_ping():
    lat = []
    for _ in range(CONFIG["ping_times"]):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(CONFIG["timeout"])
            t0 = time.time()
            s.connect((CONFIG["ping_host"], 80))
            s.close()
            lat.append(round((time.time() - t0) * 1000))
        except:
            lat.append(9999)
    valid = [x for x in lat if x < 9999]
    return {
        "avg": sum(valid)//len(valid) if valid else 9999,
        "min": min(valid) if valid else 9999,
        "max": max(valid) if valid else 9999
    }

def test_download(url):
    total = 0
    t0 = time.time()
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=CONFIG["timeout"]) as resp:
            while time.time() - t0 < CONFIG["test_duration"]:
                c = resp.read(65536)
                if not c: break
                total += len(c)
    except:
        return {"speed": 0, "text": "测试失败"}
    cost = time.time() - t0
    bps = (total * 8) / cost
    return {"speed": round(bps/(1024*1024),2), "text": format_speed(bps)}

def test_upload():
    data = bytes(''.join(random.choices("0123456789abcdef", k=4*1024*1024)), encoding="utf-8")
    t0 = time.time()
    try:
        req = Request(CONFIG["upload_url"], data=data)
        urlopen(req, timeout=CONFIG["timeout"])
        cost = time.time() - t0
        bps = (len(data)*8)/cost
        return {"speed": round(bps/(1024*1024),2), "text": format_speed(bps)}
    except:
        return {"speed": 0, "text": "测试失败"}

def run():
    return {
        "ip_info": get_ip_info(),
        "ping": test_ping(),
        "download": test_download(CONFIG["test_nodes"][0]["url"]),
        "upload": test_upload(),
        "chart": generate_ascii_chart(
            test_download(CONFIG["test_nodes"][0]["url"]),
            test_upload(),
            test_ping()
        ),
        "node": CONFIG["test_nodes"][0]["name"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def skillhub_main():
    return run()

if __name__ == "__main__":
    result = run()
    print(json.dumps(result, ensure_ascii=False, indent=2))