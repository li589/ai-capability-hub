#!/usr/bin/env python3
"""
send_report.py - 威胁情报日报邮件发送脚本
支持 AgentMail 和 SMTP 两种发送方式
从 config.json 读取配置，无任何硬编码个人信息
"""

import json
import os
import sys
import base64
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path


def load_config() -> dict:
    """加载邮件配置"""
    config_file = Path(__file__).parent.parent / "config.json"
    if not config_file.exists():
        print(f"[ERROR] 配置文件不存在: {config_file}", file=sys.stderr)
        print("[ERROR] 请先运行 setup_config.py 完成配置", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] 配置文件读取失败: {e}", file=sys.stderr)
        sys.exit(1)


def build_html_body(context: str, date_str: str) -> str:
    """构建 HTML 邮件正文"""
    date_cn = datetime.strptime(date_str, "%Y%m%d").strftime("%Y年%m月%d日")
    now_str = datetime.now().strftime("%H:%M")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  .card {{ background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #c0392b, #8e1a12); color: white; border-radius: 12px; padding: 25px 30px; margin-bottom: 20px; }}
  .header h1 {{ margin: 0 0 8px 0; font-size: 22px; }}
  .header .meta {{ opacity: 0.9; font-size: 13px; display: flex; gap: 16px; flex-wrap: wrap; }}
  .tlp {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
  .attachment-tip {{ background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 13px; color: #92400e; }}
  .summary {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }}
  .threat-level {{ display: inline-block; background: #fb923c; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
  h2 {{ color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0; }}
  h3 {{ color: #374151; margin-bottom: 12px; }}
  .content-box {{ background: #f9fafb; border-radius: 8px; padding: 15px; white-space: pre-wrap; font-size: 13px; line-height: 1.65; color: #374151; max-height: 400px; overflow-y: auto; }}
  .action-list {{ list-style: none; padding: 0; margin: 0; }}
  .action-list li {{ padding: 7px 0; border-bottom: 1px solid #f3f4f6; font-size: 14px; }}
  .action-list li:last-child {{ border-bottom: none; }}
  .immediate {{ color: #16a34a; }}
  .weekly {{ color: #2563eb; }}
  .monitor {{ color: #6b7280; }}
  .footer {{ text-align: center; color: #9ca3af; font-size: 12px; margin-top: 20px; }}
</style>
</head>
<body>
<div class="header">
  <h1>🔴 网络安全威胁情报日报</h1>
  <div class="meta">
    <span>📅 {date_cn}</span>
    <span class="tlp">TLP: WHITE</span>
    <span>⏱ {now_str} 生成</span>
  </div>
</div>
<div class="attachment-tip">
  📎 <strong>本邮件附有完整 HTML 格式报告</strong>，包含目录、表格、CVE 高亮等完整排版。请下载附件在浏览器中打开查阅完整版。
</div>
<div class="card">
  <div class="summary">
    <strong>📌 威胁态势评级</strong><br><br>
    <span class="threat-level">🟠 中高</span>
    <br><br>
    本报告由 AI 自动采集当日网络安全情报生成，涵盖高危漏洞、APT 活动、勒索软件、数据泄露等威胁态势。
  </div>
</div>
<div class="card">
  <h2>📊 今日情报摘要（节选）</h2>
  <div class="content-box">{context[:3000]}</div>
  <p style="color: #6b7280; margin-top: 12px; font-size: 12px;">
    * 完整报告请查看附件 HTML 文件
  </p>
</div>
<div class="card">
  <h2>✅ 防御建议摘要</h2>
  <h3>🕐 立即行动（24小时内）</h3>
  <ul class="action-list">
    <li class="immediate">✅ 检查系统是否存在已知高危漏洞，及时打补丁</li>
    <li class="immediate">✅ 审查第三方 SaaS 平台权限配置</li>
    <li class="immediate">✅ 排查可疑邮件和社交工程攻击</li>
  </ul>
  <h3 style="margin-top: 18px;">🗓️ 近期跟进（本周内）</h3>
  <ul class="action-list">
    <li class="weekly">🔄 更新安全策略和应急响应流程</li>
    <li class="weekly">🔄 检查供应链安全</li>
    <li class="weekly">🔄 进行员工安全意识培训</li>
  </ul>
  <h3 style="margin-top: 18px;">📡 持续监控</h3>
  <ul class="action-list">
    <li class="monitor">📡 关注厂商安全公告</li>
    <li class="monitor">📡 监控勒索组织动态</li>
    <li class="monitor">📡 跟踪 APT 活动趋势</li>
  </ul>
</div>
<div class="footer">
  <p>TLP: WHITE — 本报告可自由分享</p>
  <p>数据来源：自动化抓取 + AI 分析整合 | 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
</body>
</html>"""


def build_text_body(context: str, date_str: str) -> str:
    """构建纯文本备用正文"""
    date_cn = datetime.strptime(date_str, "%Y%m%d").strftime("%Y年%m月%d日")
    return f"""网络安全威胁情报日报 {date_cn}

威胁态势：🟠 中高

【附件说明】
本邮件附有完整 HTML 格式报告（网络安全威胁情报日报_{date_str}.html），
请下载附件在浏览器中打开查阅完整版。

---

今日情报摘要（节选）：
{context[:1500]}

---

防御建议摘要：

立即行动（24小时内）：
- 检查系统是否存在已知高危漏洞
- 审查第三方SaaS平台权限配置
- 排查可疑邮件和社交工程攻击

近期跟进（本周内）：
- 更新安全策略和应急响应流程
- 检查供应链安全
- 进行员工安全意识培训

持续监控：
- 关注厂商安全公告
- 监控勒索组织动态
- 跟踪APT活动趋势

---
TLP: WHITE | 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""


def send_via_agentmail(cfg: dict, to: str, subject: str, html: str, text: str,
                       attachment_path: str = None) -> bool:
    """通过 AgentMail API 发送邮件"""
    try:
        from agentmail import AgentMail
    except ImportError:
        print("[ERROR] 未安装 agentmail 包，请运行: pip3 install agentmail", file=sys.stderr)
        return False

    am_cfg = cfg.get("agentmail", {})
    api_key = am_cfg.get("api_key", "")
    inbox_id = am_cfg.get("inbox_id", "")

    if not api_key or not inbox_id:
        print("[ERROR] AgentMail 配置不完整，请重新运行 setup_config.py", file=sys.stderr)
        return False

    client = AgentMail(api_key=api_key)
    send_kwargs = dict(
        inbox_id=inbox_id,
        to=to,
        subject=subject,
        html=html,
        text=text,
    )

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            content = f.read()
        send_kwargs["attachments"] = [
            {
                "filename": os.path.basename(attachment_path),
                "content_type": "text/html; charset=utf-8",
                "content": base64.b64encode(content).decode("utf-8"),
            }
        ]
        print(f"[INFO] 附件: {os.path.basename(attachment_path)} ({len(content):,} bytes)")
    else:
        print("[WARN] 未找到 HTML 报告附件，将不附带附件发送")

    result = client.inboxes.messages.send(**send_kwargs)
    return True


def send_via_smtp(cfg: dict, to: str, subject: str, html: str, text: str,
                  attachment_path: str = None) -> bool:
    """通过 SMTP 发送邮件"""
    smtp_cfg = cfg.get("smtp", {})
    host = smtp_cfg.get("host", "")
    port = smtp_cfg.get("port", 587)
    use_tls = smtp_cfg.get("use_tls", True)
    username = smtp_cfg.get("username", "")
    password = smtp_cfg.get("password", "")
    sender_name = smtp_cfg.get("sender_name", "CTI 情报中心")

    if not host or not username:
        print("[ERROR] SMTP 配置不完整，请重新运行 setup_config.py", file=sys.stderr)
        return False

    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{username}>"
    msg["To"] = to
    msg["Subject"] = subject

    # 正文（HTML + 纯文本备用）
    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text, "plain", "utf-8"))
    alternative.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alternative)

    # 附件
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            attach_data = f.read()
        filename = os.path.basename(attachment_path)
        part = MIMEBase("text", "html")
        part.set_payload(attach_data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        part.add_header("Content-Type", "text/html; charset=utf-8")
        msg.attach(part)
        print(f"[INFO] 附件: {filename} ({len(attach_data):,} bytes)")
    else:
        print("[WARN] 未找到 HTML 报告附件，将不附带附件发送")

    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
            server.ehlo()

        server.login(username, password)
        server.sendmail(username, to, msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP 发送失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="发送威胁情报日报邮件")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"),
                        help="报告日期 YYYYMMDD（默认今天）")
    parser.add_argument("--context", required=True,
                        help="情报上下文 Markdown 文件路径")
    parser.add_argument("--html-report", default="",
                        help="HTML 报告附件路径（可选）")
    parser.add_argument("--to", default="",
                        help="收件人邮箱（留空则使用配置文件中的 recipient_email）")
    args = parser.parse_args()

    # 加载配置
    cfg = load_config()

    # 确定收件人
    to = args.to or cfg.get("recipient_email", "")
    if not to:
        print("[ERROR] 未指定收件人邮箱。请在 config.json 中设置 recipient_email，或使用 --to 参数。", file=sys.stderr)
        sys.exit(1)

    # 读取上下文
    try:
        context = Path(args.context).read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] 无法读取上下文文件: {e}", file=sys.stderr)
        sys.exit(1)

    date_str = args.date
    date_cn = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    subject = f"🔴 网络安全威胁情报日报 | {date_cn}"

    html_body = build_html_body(context, date_str)
    text_body = build_text_body(context, date_str)

    method = cfg.get("email_method", "")
    print(f"[send_report] 发送方式: {method}")
    print(f"[send_report] 收件人  : {to}")
    print(f"[send_report] 主题    : {subject}")

    if method == "agentmail":
        ok = send_via_agentmail(cfg, to, subject, html_body, text_body, args.html_report)
    elif method == "smtp":
        ok = send_via_smtp(cfg, to, subject, html_body, text_body, args.html_report)
    else:
        print(f"[ERROR] 未知发送方式: {method}，请重新运行 setup_config.py", file=sys.stderr)
        sys.exit(1)

    if ok:
        print(f"\n✅ 邮件发送成功！")
        print(f"   收件人: {to}")
        print(f"   主题  : {subject}")
        if args.html_report and os.path.exists(args.html_report):
            print(f"   附件  : {os.path.basename(args.html_report)}")
    else:
        print("[ERROR] 邮件发送失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
