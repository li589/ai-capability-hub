# -*- coding: utf-8 -*-
"""
语雀密码文档读取（依赖 playwright + 系统 Chrome）
- 语雀分享文档若有访问密码，API 直连会被 CSRF/captcha 拦截
- 有效路径：playwright 接管系统 Chrome → 打开页面 → 定位 input 输入密码 → Enter
- 用法: python yuque_read.py <url> <password> [输出.txt] [chrome路径]
"""
import sys
import time
from playwright.sync_api import sync_playwright


def read_yuque(url, password, chrome_path=None, out_txt=None):
    if chrome_path is None:
        import os
        candidates = [
            r"{{HOME}}/AppData/Local/Google/Chrome/Application/chrome.exe",
            r"C:/Program Files/Google/Chrome/Application/chrome.exe",
            r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        ]
        chrome_path = next((c for c in candidates if os.path.exists(c)), None)
        if chrome_path is None:
            raise RuntimeError("未找到系统 Chrome/Edge，请传入 chrome 路径")
    print("使用浏览器:", chrome_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)  # 等 SPA 渲染

        # 定位输入框（语雀密码框是 type=text 的 ant-input）
        inputs = page.locator("input")
        found = False
        for i in range(inputs.count()):
            info = inputs.nth(i).evaluate(
                """el => ({type: el.type, visible: el.offsetParent !== null})"""
            )
            if info["visible"]:
                inputs.nth(i).click()
                inputs.nth(i).fill(password)
                inputs.nth(i).press("Enter")
                found = True
                break
        if not found:
            print("未找到输入框，可能无需密码或页面结构变化")
        time.sleep(6)

        content = page.inner_text("body")
        if out_txt:
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(content)
        print("正文长度:", len(content))
        print(content[:1500])
        browser.close()
        return content


def main():
    if len(sys.argv) < 3:
        print("用法: python yuque_read.py <url> <password> [输出.txt] [chrome路径]")
        return 1
    url = sys.argv[1]
    pwd = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    chrome = sys.argv[4] if len(sys.argv) > 4 else None
    read_yuque(url, pwd, chrome, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
