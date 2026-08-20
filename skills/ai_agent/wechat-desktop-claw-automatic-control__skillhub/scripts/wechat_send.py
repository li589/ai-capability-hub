#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信桌面端自动化脚本
功能：打开微信、搜索联系人、发送消息/图片/文件
依赖：pywinauto, pyperclip, pywin32
微信路径：D:/Tencent/Weixin/Weixin.exe（注意：是 Weixin 不是 WeChat）
发送方式：Enter 键发送
版本：1.0.1
"""

import sys
import io
import time
import subprocess
import argparse
from pathlib import Path

# 设置 stdout 为 UTF-8 编码，避免 Windows 控制台 GBK 编码错误
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from pywinauto import Application
    from pywinauto.keyboard import send_keys
    import pyperclip
except ImportError as e:
    print(f"缺少依赖库：{e}")
    print("请运行：pip install pywinauto pyperclip")
    sys.exit(1)


WECHAT_PATH = "D:/Tencent/Weixin/Weixin.exe"
TIMEOUT = 15


def launch_wechat():
    """启动微信，如果已运行则连接"""
    # 先尝试连接已运行的微信
    try:
        app = Application(backend='uia').connect(title_re="微信", timeout=2)
        print("微信已在运行，直接连接")
        return app
    except Exception:
        pass

    # 启动微信
    print("启动微信...")
    subprocess.Popen(WECHAT_PATH)
    time.sleep(6)

    # 等待微信窗口出现
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        try:
            app = Application(backend='uia').connect(title_re="微信", timeout=2)
            print("微信启动成功")
            return app
        except Exception:
            time.sleep(1)

    print("无法连接微信，可能需要在手机上扫码确认登录")
    print("请扫码后重新运行脚本")
    sys.exit(1)


def get_main_window(app):
    """获取微信主窗口（确保是可见的前台窗口）"""
    try:
        window = app.window(title_re="微信")
        # 确保窗口可见且激活
        if not window.is_visible():
            print("警告：微信窗口不可见，尝试显示窗口")
            window.restore()  # 如果最小化，恢复窗口
            time.sleep(0.5)
        window.set_focus()
        time.sleep(0.5)
        # 确认窗口已激活
        if window.is_active():
            print("✅ 微信窗口已激活")
        else:
            print("⚠️ 警告：微信窗口可能未在前台")
        return window
    except Exception as e:
        print(f"获取窗口失败：{e}")
        sys.exit(1)


def search_contact(window, name):
    """搜索并选中联系人"""
    print(f"搜索联系人：{name}")

    # Ctrl+F 打开搜索
    send_keys("^f")
    time.sleep(1)

    # 输入联系人名称
    pyperclip.copy(name)
    time.sleep(0.2)
    send_keys("^v")
    time.sleep(1.5)

    # 按 Enter 选中第一个搜索结果
    send_keys("{ENTER}")
    time.sleep(1)
    print(f"已选中联系人：{name}")


def send_text(window, text):
    """发送文本消息（Enter 发送）"""
    print(f"发送文本：{text[:60]}{'...' if len(text) > 60 else ''}")

    pyperclip.copy(text)
    time.sleep(0.2)
    send_keys("^v")  # 粘贴
    time.sleep(0.3)
    send_keys("{ENTER}")  # Enter 发送
    time.sleep(0.5)
    print("文本已发送")


def send_image(window, image_path):
    """发送图片（通过剪贴板 + Ctrl+V 粘贴到聊天框）"""
    import win32clipboard
    import win32con
    from PIL import Image

    print(f"发送图片：{image_path}")

    if not Path(image_path).exists():
        print(f"图片不存在：{image_path}")
        return False

    try:
        img = Image.open(image_path)
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # 去掉 BMP 文件头

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()

        time.sleep(0.3)
        send_keys("^v")  # Ctrl+V 粘贴图片
        time.sleep(1)
        send_keys("{ENTER}")  # Enter 发送
        print("图片已发送")
        return True
    except Exception as e:
        print(f"发送图片失败：{e}")
        print("请确保安装了 pywin32：pip install pywin32")
        return False


def send_file(window, file_path):
    """发送文件（通过 Ctrl+Alt+F 快捷键或点击 + 按钮）"""
    print(f"发送文件：{file_path}")

    if not Path(file_path).exists():
        print(f"文件不存在：{file_path}")
        return False

    try:
        # 尝试 Ctrl+Alt+F（微信发送文件快捷键）
        send_keys("^%f")  # Ctrl+Alt+F
        time.sleep(1.5)

        # 此时应出现文件选择对话框，输入文件路径
        pyperclip.copy(str(file_path))
        time.sleep(0.2)
        send_keys("^v")
        time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(1)
        print("文件已发送")
        return True
    except Exception as e:
        print(f"发送文件失败：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="微信桌面端自动化工具")
    parser.add_argument("--contact", help="联系人名称（昵称或备注名）")
    parser.add_argument("--message", help="要发送的文本内容")
    parser.add_argument("--message-file", help="从文件读取要发送的文本内容（适用于长消息）")
    parser.add_argument("--image", help="要发送的图片路径")
    parser.add_argument("--file", help="要发送的文件路径")
    parser.add_argument("--launch-only", action="store_true", help="仅启动微信，不发送内容")
    args = parser.parse_args()

    # 启动/连接微信
    app = launch_wechat()
    window = get_main_window(app)

    if args.launch_only:
        print("微信已启动，可以开始使用了")
        return

    if not args.contact:
        print("请指定 --contact 参数（联系人名称）")
        sys.exit(1)

    # 搜索并选中联系人
    search_contact(window, args.contact)

    # 发送内容
    if args.message_file:
        # 从文件读取消息内容
        try:
            with open(args.message_file, 'r', encoding='utf-8') as f:
                message = f.read()
            print(f"从文件读取消息：{args.message_file} ({len(message)} 字符)")
            send_text(window, message)
        except Exception as e:
            print(f"读取消息文件失败：{e}")
            sys.exit(1)
    elif args.message:
        send_text(window, args.message)

    if args.image:
        send_image(window, args.image)

    if args.file:
        send_file(window, args.file)

    if not any([args.message, args.message_file, args.image, args.file]):
        print("未指定要发送的内容，请使用 --message / --message-file / --image / --file 参数")


if __name__ == "__main__":
    main()
