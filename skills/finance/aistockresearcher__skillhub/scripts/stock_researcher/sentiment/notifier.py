#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多渠道通知器 (v6.0.0)
=====================
多通道预警通知：控制台/文件/Webhook/邮件。
纯 Python 标准库，零依赖。
"""

import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class Notifier:
    """
    多渠道通知器。

    支持渠道:
      - console: 打印到 stdout（默认）
      - file: 追加到日志文件
      - webhook: POST 到 DingTalk/WeChat Work/Feishu webhook
      - email: 通过 SMTP 发送邮件（stdlib smtplib）

    用法:
        n = Notifier()
        n.notify({"type": "sentiment_alert", "message": "舆情突变"}, channels=["console", "file"])
    """

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).resolve().parents[3] / "data" / "notifications"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def notify(self, alert: Dict, channels: List[str] = None) -> Dict[str, bool]:
        """
        发送通知到指定渠道。

        Args:
            alert: 预警字典，必须含 type/message/level
            channels: 渠道列表，默认 ["console"]

        Returns:
            {channel: success}
        """
        channels = channels or ["console"]
        results = {}

        if "console" in channels:
            results["console"] = self._notify_console(alert)
        if "file" in channels:
            results["file"] = self._notify_file(alert)
        if "webhook" in channels:
            results["webhook"] = self._notify_webhook(alert)
        if "email" in channels:
            results["email"] = self._notify_email(alert)

        return results

    def _notify_console(self, alert: Dict) -> bool:
        """控制台通知"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = alert.get("level", "INFO")
        emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(level, "⚪")
        print(f"{emoji} [{timestamp}] [{level}] {alert.get('type', 'alert')}: {alert.get('message', '')}")
        return True

    def _notify_file(self, alert: Dict) -> bool:
        """文件通知 — 追加到 alerts.log"""
        try:
            log_file = self.log_dir / "alerts.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "timestamp": timestamp,
                "type": alert.get("type", "alert"),
                "level": alert.get("level", "INFO"),
                "message": alert.get("message", ""),
                "data": alert.get("data", {}),
            }
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            print(f"[Notifier] 文件写入失败: {e}")
            return False

    def _notify_webhook(self, alert: Dict) -> bool:
        """
        Webhook 通知（DingTalk/WeChat Work/Feishu 通用格式）。

        通过环境变量 WEBHOOK_URL 或 alert 中的 webhook_url 字段获取 URL。
        """
        import os

        webhook_url = alert.get("webhook_url") or os.getenv("WEBHOOK_URL", "")
        if not webhook_url:
            print("[Notifier] 未配置 WEBHOOK_URL，跳过 webhook 通知")
            return False

        # 通用 Markdown 格式
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"[{alert.get('level', 'INFO')}] {alert.get('type', 'alert')}",
                "text": (
                    f"## {alert.get('type', 'alert')}\n\n"
                    f"- **时间**: {timestamp}\n"
                    f"- **级别**: {alert.get('level', 'INFO')}\n"
                    f"- **内容**: {alert.get('message', '')}\n\n"
                    f"{alert.get('detail', '')}"
                ),
            },
        }

        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[Notifier] Webhook 发送失败: {e}")
            return False

    def _notify_email(self, alert: Dict) -> bool:
        """
        邮件通知。

        通过环境变量配置 SMTP:
          SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
          EMAIL_FROM, EMAIL_TO
        """
        import os

        smtp_host = alert.get("smtp_host") or os.getenv("SMTP_HOST", "")
        if not smtp_host:
            print("[Notifier] 未配置 SMTP_HOST，跳过邮件通知")
            return False

        try:
            smtp_port = int(alert.get("smtp_port") or os.getenv("SMTP_PORT", "587"))
            smtp_user = alert.get("smtp_user") or os.getenv("SMTP_USER", "")
            smtp_pass = alert.get("smtp_pass") or os.getenv("SMTP_PASS", "")
            from_addr = alert.get("from_addr") or os.getenv("EMAIL_FROM", smtp_user)
            to_addr = alert.get("to_addr") or os.getenv("EMAIL_TO", "")

            if not all([smtp_host, smtp_user, to_addr]):
                print("[Notifier] SMTP 配置不完整")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"[stock-researcher] {alert.get('type', 'Alert')} - {timestamp}"
            body = alert.get("message", "")

            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"[Notifier] 邮件发送失败: {e}")
            return False
