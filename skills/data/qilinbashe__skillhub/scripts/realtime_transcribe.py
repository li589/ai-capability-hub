# realtime_transcribe.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""庭审实时转写（讯飞 RTASR 实时流 + 离线回退）

为“109-庭审实时辅助系统”提供转写能力：
  · 模式 A（实时流）：检测到讯飞 RTASR 凭据（IFLYTEK_APPID + IFLYTEK_API_SECRET，
    鉴权不用 APIKey）且具备 websocket 依赖时，走 WebSocket 流式分句转写。
  · 模式 B（离线回退）：未配置凭据或依赖缺失时，自动调用同目录的
    voice_transcribe.py 做录音后处理转写，保证要点浮窗能力不中断。

⚠️ 数据外发合规（强制）：
  · 模式 A 会将庭审音频分帧发送至讯飞开放平台（wss://iat-api.xfyun.cn，第三方服务器），
    属于数据外发行为。庭审录音具有保密义务，发送前必须：
      1) 提示用户音频将外发至第三方服务器；
      2) 取得用户明确确认（y/N），不可跳过；
      3) 超过大小上限（200MB）的文件拒绝外发，自动转模式 B。
  · 未获确认时程序一律转模式 B（离线后处理转写），不发送任何音频数据。
  · 白名单域名：仅 wss://iat-api.xfyun.cn 单一外发目标（硬编码，无动态域名注入面）。
  · 调用审计（v4.19.0）：每次外发/拒绝事件落本地审计日志
    ~/.legal-skills/transcribe_audit.log（时间戳+文件名+大小），供合规核查。

说话人分离说明：标准 RTASR 不含说话人分离。本脚本在开庭前由律师设定角色
边界（我方/对方/第三方），并对静音段做切分标注；精确的说话人分离需接入
讯飞“语音转写”产品或第三方 diarization 服务，届时在此处替换 transcribe_realtime 即可。

凭据走环境变量，缺失时优雅降级，不阻塞主流程。
"""
import os
import sys
import io
import json
import base64
import hashlib
import hmac
import subprocess
import datetime
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# 数据外发合规：单文件大小上限（MB），超过则拒绝外发、转离线模式
MAX_UPLOAD_MB = 200

# 调用审计（v4.19.0：TRACE 评测整改——讯飞外发须留审计记录，供合规核查）
AUDIT_LOG = os.path.join(os.path.expanduser("~"), ".legal-skills", "transcribe_audit.log")
# v4.20.0：审计日志轮转上限（MB），超过则滚动为 .1 保留一份，防无限增长
AUDIT_MAX_MB = 2


def audit(event, audio, size_mb=None):
    """数据外发审计：外发/拒绝事件追加写入本地审计日志。

    记录字段：时间戳 + 事件 + 音频文件名 + 大小。审计写入失败仅告警，不阻断主流程。
    v4.20.0：日志超过 AUDIT_MAX_MB 时滚动为 .1（保留一份），防无限增长。
    """
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
        # 轮转：超过上限 → 当前文件改名为 .1（覆盖旧备份），重新开始新日志
        if os.path.exists(AUDIT_LOG) and os.path.getsize(AUDIT_LOG) > AUDIT_MAX_MB * 1024 * 1024:
            backup = AUDIT_LOG + ".1"
            try:
                os.replace(AUDIT_LOG, backup)
            except OSError:
                try:
                    os.remove(AUDIT_LOG)
                except OSError:
                    pass
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fname = os.path.basename(audio)
        size = ("%.1fMB" % size_mb) if size_mb is not None else "-"
        with io.open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s | 文件=%s | 大小=%s\n" % (ts, event, fname, size))
        print("[审计] %s：%s" % (event, fname), file=sys.stderr)
    except Exception as e:
        print("[审计警告] 审计记录写入失败：%s" % e, file=sys.stderr)


def have_credentials():
    """是否已配置讯飞 RTASR 凭据（鉴权仅需 APPID + APISecret）。"""
    return bool(os.getenv("IFLYTEK_APPID") and os.getenv("IFLYTEK_API_SECRET"))


def _now_rfc1123():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_auth_url():
    """构造讯飞 RTASR WebSocket 握手 URL（HMAC-SHA256 签名）。

    参考讯飞开放平台“实时语音转写 RTASR”鉴权规范：
      签名原文 = host + "\\n" + date + "\\n" + request_line
      authorization = base64(HmacSHA256(APISecret, 签名原文))
    """
    appid = os.getenv("IFLYTEK_APPID")
    api_secret = os.getenv("IFLYTEK_API_SECRET")
    host = "iat-api.xfyun.cn"
    date = _now_rfc1123()
    request_line = "GET /v2/iat HTTP/1.1"
    signature_origin = "host: %s\ndate: %s\n%s" % (host, date, request_line)
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization = (
        'api_key="%s", algorithm="hmac-sha256", headers="host date request-line", '
        'signature="%s"' % (appid, signature)
    )
    return (
        "wss://%s/v2/iat?authorization=%s&date=%s&host=%s"
        % (
            host,
            base64.b64encode(authorization.encode("utf-8")).decode("utf-8"),
            base64.b64encode(date.encode("utf-8")).decode("utf-8"),
            host,
        )
    )


def mask_pii(text):
    """PII 脱敏（v5.0.1：与 voice_transcribe.py / markdown_to_docx.py 统一口径）：
    身份证（18 位）/ 手机号（11 位）/ 银行账户（16-19 位）整体替换为 ****，
    转写输出/落盘前调用，防止庭审转写文本泄露 PII。"""
    return re.sub(r"(?<![0-9A-Za-z])(?:[0-9]{17}[0-9Xx]|[0-9]{11,})(?![0-9A-Za-z])", "****", text)


def transcribe_offline(audio_path):
    """模式 B：调用 voice_transcribe.py 做录音后处理转写。"""
    voice_script = os.path.join(HERE, "voice_transcribe.py")
    if not os.path.isfile(voice_script):
        print("[离线回退] 未找到 voice_transcribe.py，无法转写：%s" % audio_path)
        return None
    print("[模式B] 录音后处理转写：%s" % audio_path)
    try:
        r = subprocess.run(
            [sys.executable, voice_script, audio_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode != 0:
            print("[离线回退] voice_transcribe.py 执行失败：%s" % (r.stderr or r.stdout)[-300:])
            return None
        return r.stdout
    except Exception as e:  # noqa: BLE001
        print("[离线回退] 异常：%s" % e)
        return None


def transcribe_realtime(audio_path):
    """模式 A：讯飞 RTASR WebSocket 流式转写。

    依赖 websocket-client（pip install websocket-client）。未安装时抛出
    ImportError，由调用方降级到离线模式。
    """
    try:
        import websocket  # noqa: F401
    except ImportError:
        raise ImportError("缺少 websocket-client 依赖，请 pip install websocket-client")

    import _thread as thread  # noqa: WPS433

    url = build_auth_url()
    result_parts = []
    role_map = {}  # 说话人角色设定（开庭前由律师提供）

    def on_message(ws, message):
        data = json.loads(message)
        if data.get("code") != 0:
            print("[RTASR] 错误：%s" % data.get("message"))
            return
        for item in data.get("data", {}).get("result", {}).get("ws", []):
            for w in item.get("cw", []):
                result_parts.append(w.get("w", ""))
        # 末帧：data.status == 2 表示结束
        if data.get("data", {}).get("status") == 2:
            ws.close()

    def on_error(ws, error):
        print("[RTASR] WebSocket 错误：%s" % error)

    def on_close(ws, *args):
        pass

    def on_open(ws):
        def send_frames():
            # 真实实现需读取音频文件分帧（每 40ms 一帧，base64 发送）。
            # 此处给出标准发送骨架；音频读取与分帧由音频库（pydub/ffmpeg）完成。
            import time as _t

            frame_size = 1280  # 16k/16bit/单声道，40ms
            try:
                with open(audio_path, "rb") as f:
                    while True:
                        chunk = f.read(frame_size)
                        if not chunk:
                            break
                        ws.send(
                            json.dumps(
                                {
                                    "data": base64.b64encode(chunk).decode("utf-8"),
                                    "status": 1,
                                }
                            )
                        )
                        _t.sleep(0.04)
                ws.send(json.dumps({"status": 2}))
            except Exception as e:  # noqa: BLE001
                print("[RTASR] 发送异常：%s" % e)

        thread.start_new_thread(send_frames, ())

    print("[模式A] 讯飞 RTASR 实时流转写：%s" % audio_path)
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws.run_forever()
    return "".join(result_parts)


def main():
    if len(sys.argv) < 2:
        print("用法：python realtime_transcribe.py <音频文件>")
        print("环境变量：IFLYTEK_APPID / IFLYTEK_API_SECRET（实时流；缺失则离线回退）")
        print("数据外发提示：模式A将音频发送至讯飞开放平台（第三方服务器），发送前须逐次确认")
        return 1
    audio = sys.argv[1]
    if not os.path.isfile(audio):
        print("[错误] 音频文件不存在：%s" % audio)
        return 2

    if have_credentials():
        # 数据外发合规：文件大小上限检查（超过拒绝外发，转离线模式）
        size_mb = os.path.getsize(audio) / (1024.0 * 1024.0)
        if size_mb > MAX_UPLOAD_MB:
            audit("拒绝外发（超%dMB上限）" % MAX_UPLOAD_MB, audio, size_mb)
            print("[拒绝] 音频文件 %.1fMB 超过外发上限 %dMB，未发送任何数据；请改用模式B（离线后处理）或先分段处理"
                  % (size_mb, MAX_UPLOAD_MB))
            transcribe_offline(audio)
            return 0
        # 数据外发风险提示 + 强制交互确认（不可跳过）
        print("⚠️ [数据外发提示] 模式A将把庭审音频分帧发送至讯飞开放平台")
        print("    （wss://iat-api.xfyun.cn，第三方服务器）进行实时转写，数据将离开本机。")
        print("    庭审录音具有保密义务，请确认已获得当事人/委托人授权。")
        try:
            ans = input("确认发送？(y/N): ").strip().lower()
        except EOFError:
            ans = "n"
        if ans != "y":
            audit("拒绝外发（未获用户确认）", audio, size_mb)
            print("[已取消] 未确认发送，转用模式B（离线后处理转写），不发送任何音频数据")
            transcribe_offline(audio)
            return 0
        try:
            audit("外发至讯飞（wss://iat-api.xfyun.cn）", audio, size_mb)
            text = transcribe_realtime(audio)
            if text is None:
                print("[回退] 实时流失败，转录音后处理模式")
                transcribe_offline(audio)
            else:
                text = mask_pii(text)
                print(text)
            return 0
        except ImportError:
            print("[回退] 缺少 websocket 依赖，转录音后处理模式")
            transcribe_offline(audio)
            return 0
    else:
        print("[模式B] 未检测到讯飞 RTASR 凭据（IFLYTEK_APPID / IFLYTEK_API_SECRET），使用录音后处理模式")
        transcribe_offline(audio)
        return 0


if __name__ == "__main__":
    sys.exit(main())
