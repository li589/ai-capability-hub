---
name: trae-ai-passport-diy
description: 把图片或 RTTTL 铃声直接推送到 TRAE World AI 通行证——校验内容是否符合通行证要求（图片必须竖向 3:4、≤5MB；RTTTL 三段式），然后调用 trae-world-admin 的接口入队，由观众的小程序在蓝牙连接时下发到通行证。当需要给 AI 通行证推送图片、播放铃声，或查询内容是否已同步到通行证时使用。
---

# 推内容到 TRAE World AI 通行证

现场每位观众佩戴一张 AI 通行证（小屏 + 蜂鸣器 + 蓝牙 + NFC）。这个 skill 把内容推入对应通行证的待同步队列。

```
skill 调接口 → 后端校验/限流/入队（status=pending）
观众的小程序连着蓝牙时轮询到 → 下载/转换 → 蓝牙分片下发到通行证 → 回写结果
```

> **推送成功 ≠ 通行证上已经显示了。**后端只负责入队，真正下发要等观众的小程序连上蓝牙来拉。
> 要确认是否已到达通行证，用 `--status <id>` 查询。

## 收到请求后怎么做

1. **确认要推什么**：图片路径或 RTTTL 曲谱。用户说“推张图”但没给文件，就问要哪张。
2. **拿凭证。跑脚本之前就要确认拿到了，不要先跑再看报错。**按这个顺序找：
   1. 环境变量 `BADGE_SN` / `BADGE_KEY` —— 设了就直接用，**别再问**
   2. 用户在本轮对话里给过的 —— 给过就一直用，别每条内容问一遍
   3. 两样都没有 → **停下来问用户**，拿到之前不要执行脚本

   问的时候要说清楚去哪儿找，别只甩一句"请提供凭证"：

   > 推送前需要目标 AI 通行证的凭证：**SN**（通行证编号，正面印有）和 **KEY**（只编码在背面二维码里，
   > 正面没有）。扫描通行证背面的二维码即可同时获取这两项信息。
   > 也可以设成环境变量 `BADGE_SN` / `BADGE_KEY`，以后就不用每次给了。

   只给了 SN 没给 KEY（或反过来）**也算没有**，缺哪个问哪个——两个都得有才能调用。

   传 KEY 时优先用环境变量，别放命令行参数里，免得它留在 shell 历史和终端回显里。
3. **图片不是竖向 3:4 时先问，别擅自裁。**告诉用户当前尺寸，问是用 `--fit cover` 居中裁、
   `--fit contain` 补边，还是自己重裁一张。裁图会改变画面内容，不该默认替用户决定。
4. 把「脚本」一节那段 Python 写到临时文件，跑。
5. **回报结果**：每条的 item id，以及一句「内容不会实时显示在 AI 通行证上，需要等待观众的小程序连接蓝牙后拉取」。
   用户问"到了没"就用 `--status <id>` 查。

不确定要推到哪张 AI 通行证时**必须询问**，不要猜测，避免把内容推送到错误设备。

## 支持的内容

| 类型 | 参数 | 说明 |
| --- | --- | --- |
| 图片 | `--image PATH` | **必须竖向 3:4**，≤5MB。推荐 240×320 / 480×640 / 750×1000 |
| 铃声 | `--rtttl TUNE` | RTTTL 曲谱字符串。**不是音频文件**——AI 通行证使用蜂鸣器，只能播放 RTTTL |

## 凭证

凭证是**一张具体 AI 通行证的 SN + KEY**，不是后台账号：

- `SN` 通行证编号，正面印有，也编码在背面二维码里
- `KEY` **只编码在通行证背面二维码里，不印在正面**

扫描通行证背面的二维码即可获取这两项信息。示例中统一使用 `YOUR_BADGE_SN` / `YOUR_BADGE_KEY` 占位符。

**传法优先用环境变量** `BADGE_SN` / `BADGE_KEY`——设一次就不用再给，KEY 也不会留在
shell 历史和终端回显里。临时用也可以走命令行 `--sn` / `--key`。

用户没给、环境变量也没有时，**问用户要，别猜也别跳过**（见上面「收到请求后怎么做」第 2 条）。

## 用法

把下面「脚本」一节里那段以 `#!/usr/bin/env python3` 开头的 Python 原样写到一个临时文件再运行
（例如 `%TEMP%\push_badge.py` 或 `/tmp/push_badge.py`）。只用 Python 3 标准库；
装了 Pillow 的话可以自动把图裁成 3:4、缩到 1024 以内。

```bash
# 凭证放环境变量，之后所有命令都不用再带（KEY 不进 shell 历史）
export BADGE_SN=YOUR_BADGE_SN BADGE_KEY=YOUR_BADGE_KEY        # PowerShell: $env:BADGE_SN="YOUR_BADGE_SN"

# 推送一张图片和一段铃声
python push_badge.py \
  --image ./avatar-480x640.png \
  --rtttl "trae:d=4,o=5,b=125:16e6,16e6,32p,8e6"

# 图不是 3:4？让它居中裁成 3:4（需要 Pillow）
python push_badge.py --image ./photo.jpg --fit cover

# 先看要发什么，不真发（不需要凭证）
python push_badge.py --image ./a.png --dry-run

# 查询某条内容是否已同步到 AI 通行证
python push_badge.py --status 130

# 临时切换目标 AI 通行证，也可以通过命令行传入凭证
python push_badge.py --image ./avatar.png --sn YOUR_BADGE_SN --key YOUR_BADGE_KEY
```

| 参数 | 说明 |
| --- | --- |
| `--image PATH` | 图片，可重复 |
| `--rtttl TUNE` | RTTTL 曲谱，可重复 |
| `--sn` / `--key` | AI 通行证凭证；也可用环境变量 `BADGE_SN` / `BADGE_KEY` |
| `--base-url` | 服务地址，默认 `https://trae-dev.siliconpear.cn`；也可用 `BADGE_BASE_URL` |
| `--fit cover\|contain\|none` | 图不是 3:4 时怎么办：`cover` 居中裁、`contain` 补边、`none` 直接报错（默认）。需要 Pillow |
| `--pad-color` | `--fit contain` 补边的颜色，默认黑色（AI 通行证屏幕为深色） |
| `--max-edge N` | 最长边超过 N 就缩，默认 1024（服务器本来也会缩，缩了只是省上传） |
| `--request-id-prefix` | 幂等标识前缀，默认按时间生成 |
| `--dry-run` | 只打印将要发什么，不真发 |
| `--status ID` | 查询某条推送的同步状态，不推新内容 |
| `--timeout` | 单条请求超时秒数，默认 30 |

## 幂等

每条内容都会自动带 `request_id`（`前缀-序号`）。后端按「**同一张 AI 通行证 + 同一 request_id = 同一条**」做幂等：

- 网络抖动重试、手滑跑两次，队列里都不会长出重复内容
- **同一个 `request_id` 就是同一条，哪怕内容变了**——第二次的新内容不会覆盖进去，返回的还是第一条。想推新内容就换个前缀
- 不传 `--request-id-prefix` 时按时间生成，所以两次独立运行天然是两条

## 脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把图片或 RTTTL 铃声推送到 TRAE World AI 通行证。

打的是 trae-world-admin 的 HTTP 接口（backend/apps/mcp/views.py 的 McpBadgeContentView）：
    POST {base}/api/v1/mcp/badge/content     图片走 multipart，铃声走 JSON
    GET  {base}/api/v1/mcp/badge/content/{id}  查同步状态
凭证是 AI 通行证的 SN + KEY，走 X-Badge-Sn / X-Badge-Key 请求头。

推之前先在本地校验一遍，错误文案与后端一字不差——省一个来回，也省掉限流额度
（限流按调用次数算，凭证错、参数错的请求一样占额度）。

只用 Python 3 标准库；装了 Pillow 可以自动裁/缩图。
"""

import argparse
import base64
import binascii
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime

DEFAULT_BASE_URL = "https://trae-dev.siliconpear.cn"
PUSH_PATH = "/api/v1/mcp/badge/content"

# —— 与 backend/apps/mcp/service.py 保持一致 ——
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_EDGE = 1024
BADGE_ASPECT_W, BADGE_ASPECT_H = 3, 4
ASPECT_TOLERANCE = 0.01
BADGE_ASPECT = BADGE_ASPECT_W / BADGE_ASPECT_H


class Rejected(Exception):
    """本地校验就没过，不用浪费一次调用。"""


# ---------------------------------------------------------------- 图片

def _pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


def _png_size(data):
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _jpeg_size(data):
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    i, n = 2, len(data)
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xFF, 0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seglen = int.from_bytes(data[i + 2:i + 4], "big")
        if seglen < 2:
            return None
        # SOFn 段带尺寸；排掉 DHT(C4) / JPG(C8) / DAC(CC)
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return (int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"))
        i += 2 + seglen
    return None


def image_size(data):
    Image = _pillow()
    if Image is not None:
        try:
            with Image.open(io.BytesIO(data)) as im:
                return im.size
        except Exception:
            return None
    for reader in (_png_size, _jpeg_size):
        try:
            size = reader(data)
        except (IndexError, ValueError):
            size = None
        if size and size[0] > 0 and size[1] > 0:
            return size
    return None


def _save(im, fmt):
    if fmt not in ("JPEG", "PNG", "WEBP"):
        fmt = "PNG"
    if fmt == "JPEG" and im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format=fmt)
    return buf.getvalue()


def fit_aspect(data, mode, pad_color):
    """把图弄成竖向 3:4。cover=居中裁，contain=补边。返回 (新字节, 说明)。"""
    Image = _pillow()
    if Image is None:
        raise Rejected("--fit 需要 Pillow（pip install Pillow）；或者自己先把图裁成 3:4。")
    with Image.open(io.BytesIO(data)) as im:
        fmt = (im.format or "PNG").upper()
        w, h = im.size
        if mode == "cover":
            # 目标框铺满原图，多出来的部分居中裁掉
            if w / h > BADGE_ASPECT:
                new_w = round(h * BADGE_ASPECT)
                box = ((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h)
            else:
                new_h = round(w / BADGE_ASPECT)
                box = (0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h)
            out = im.crop(box)
            note = "已从 %dx%d 居中裁成 %dx%d" % (w, h, out.width, out.height)
        else:
            # 原图完整放进目标框，空出来的补边
            if w / h > BADGE_ASPECT:
                canvas = (w, round(w / BADGE_ASPECT))
            else:
                canvas = (round(h * BADGE_ASPECT), h)
            base = Image.new("RGB", canvas, pad_color)
            base.paste(im.convert("RGB"), ((canvas[0] - w) // 2, (canvas[1] - h) // 2))
            out = base
            note = "已从 %dx%d 补边成 %dx%d（补 %s）" % (w, h, canvas[0], canvas[1], pad_color)
        return _save(out, fmt), note


def shrink(data, max_edge):
    size = image_size(data)
    if not size or max(size) <= max_edge:
        return data, ""
    Image = _pillow()
    if Image is None:
        return data, ("最长边 %dpx 超过 %dpx；没装 Pillow 缩不了，服务器会自己缩，只是上传大一点。"
                      % (max(size), max_edge))
    with Image.open(io.BytesIO(data)) as im:
        fmt = (im.format or "PNG").upper()
        scale = max_edge / max(im.size)
        out = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))))
        note = "已从 %dx%d 缩到 %dx%d" % (im.width, im.height, out.width, out.height)
        return _save(out, fmt), note


def prepare_image(path, fit, pad_color, max_edge):
    if not os.path.isfile(path):
        raise Rejected("图片文件不存在：%s" % path)
    with open(path, "rb") as fh:
        data = fh.read()
    filename = os.path.basename(path)
    notes = []

    size = image_size(data)
    if size is None:
        notes.append("认不出图片尺寸，比例校验跳过——以服务器为准。")
    else:
        w, h = size
        if abs(w / h - BADGE_ASPECT) > BADGE_ASPECT * ASPECT_TOLERANCE:
            if fit == "none":
                # 文案与 service.validate_image_aspect() 一字不差
                raise Rejected("AI 通行证屏幕为竖向 3:4，当前图片是 %dx%d（约 %.2f:1），"
                               "请裁成 3:4 后再推送，例如 240x320、480x640、750x1000。"
                               "（加 --fit cover 可以自动裁）" % (w, h, w / h))
            data, note = fit_aspect(data, fit, pad_color)
            notes.append(note)

    data, note = shrink(data, max_edge)
    if note:
        notes.append(note)
    if len(data) > MAX_IMAGE_BYTES:
        raise Rejected("图片过大，请压缩到 5MB 以内再推送。")

    mime = mimetypes.guess_type(filename)[0] or "image/png"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif data[:2] == b"\xff\xd8":
        mime = "image/jpeg"
    return data, filename, mime, notes


# ---------------------------------------------------------------- 请求

def encode_multipart(fields, file_field, filename, file_bytes, content_type):
    """手搓 multipart/form-data，省得为一个上传引 requests。"""
    boundary = "----traeBadge" + uuid.uuid4().hex
    crlf, body = b"\r\n", []
    for name, value in fields.items():
        body += [b"--" + boundary.encode(),
                 ('Content-Disposition: form-data; name="%s"' % name).encode(),
                 b"", str(value).encode("utf-8")]
    body += [b"--" + boundary.encode(),
             ('Content-Disposition: form-data; name="%s"; filename="%s"'
              % (file_field, filename)).encode("utf-8"),
             ("Content-Type: %s" % content_type).encode(), b"", file_bytes,
             b"--" + boundary.encode() + b"--", b""]
    return crlf.join(body), "multipart/form-data; boundary=%s" % boundary


def request(url, headers, body=None, content_type=None, method="POST", timeout=30):
    req = urllib.request.Request(url, data=body, method=method)
    if content_type:
        req.add_header("Content-Type", content_type)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        # 后端的错误体本身就是给人看的 {code, detail}，原样带回去
        return exc.code, exc.read().decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        raise ConnectionError("连不上 %s：%s" % (url, exc.reason))


def explain(status, text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:300], {}
    detail = data.get("detail") or data.get("message") or ""
    code = data.get("code") or ""
    hint = {
        401: "SN 或 KEY 不正确。KEY 只在 AI 通行证背面二维码中，正面没有。",
        403: "这张 AI 通行证不可用（停用/遗失），或后台已停用这个调用方。",
        429: "超过限流（默认每分钟 30 次，按调用次数算，失败的也计数）。等 60 秒。",
    }.get(status, "")
    line = " ".join(x for x in ("HTTP %d" % status, code, detail, hint) if x)
    return line, data


# ---------------------------------------------------------------- 主流程

def main(argv=None):
    p = argparse.ArgumentParser(description="推内容到 TRAE World AI 通行证")
    p.add_argument("--image", action="append", metavar="PATH")
    p.add_argument("--rtttl", action="append", metavar="TUNE")
    p.add_argument("--sn", default=os.environ.get("BADGE_SN", ""))
    p.add_argument("--key", default=os.environ.get("BADGE_KEY", ""))
    p.add_argument("--base-url", default=os.environ.get("BADGE_BASE_URL", DEFAULT_BASE_URL))
    p.add_argument("--fit", choices=("none", "cover", "contain"), default="none")
    p.add_argument("--pad-color", default="#000000")
    p.add_argument("--max-edge", type=int, default=MAX_IMAGE_EDGE)
    p.add_argument("--request-id-prefix", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--status", type=int, default=None, metavar="ID")
    p.add_argument("--timeout", type=float, default=30.0)
    args = p.parse_args(argv)

    base = args.base_url.rstrip("/")
    headers = {"X-Badge-Sn": args.sn, "X-Badge-Key": args.key}

    # 查同步状态
    if args.status is not None:
        if not (args.sn and args.key):
            print("缺少凭证：--sn / --key，或环境变量 BADGE_SN / BADGE_KEY。", file=sys.stderr)
            return 2
        status, text = request("%s%s/%d" % (base, PUSH_PATH, args.status), headers,
                               method="GET", timeout=args.timeout)
        line, data = explain(status, text)
        if status != 200:
            print("✕ %s" % line)
            return 1
        mark = {"pending": "待同步（等小程序连上蓝牙来拉）", "synced": "已同步到 AI 通行证",
                "failed": "同步失败", "canceled": "已取消"}.get(data.get("status"), data.get("status"))
        print("item %s  %s  %s" % (data.get("id"), data.get("kind"), mark))
        if data.get("synced_at"):
            print("  同步时间 %s" % data["synced_at"])
        if data.get("error_message"):
            print("  失败原因 %s" % data["error_message"])
        return 0

    if not (args.image or args.rtttl):
        p.error("至少给一个 --image / --rtttl（或用 --status 查状态）")

    prefix = args.request_id_prefix
    if prefix is None:
        prefix = "skill-" + datetime.now().strftime("%Y%m%d-%H%M%S")

    # 先在本地把两类内容都准备好、校验好，一条不合规就整批不发——
    # 免得推送一半才发现图片不合规，AI 通行证上只显示半套内容
    jobs, rejected = [], []
    for path in args.image or []:
        try:
            data, filename, mime, notes = prepare_image(path, args.fit, args.pad_color, args.max_edge)
            jobs.append({"kind": "image", "label": filename, "notes": notes,
                         "data": data, "filename": filename, "mime": mime})
        except Rejected as exc:
            rejected.append(("image", path, str(exc)))
    for tune in args.rtttl or []:
        tune = str(tune or "").strip()
        # 与 service.normalize_sound_payload() 同一套判断与文案
        if not tune:
            rejected.append(("sound", "(空)", "声音内容需要提供 rtttl 曲谱。"))
        elif tune.count(":") < 2:
            rejected.append(("sound", tune, "rtttl 格式不正确，应形如 name:d=4,o=5,b=63:notes。"))
        else:
            jobs.append({"kind": "sound", "label": tune, "notes": [], "rtttl": tune})
    for kind, label, why in rejected:
        print("✕ %-6s %s\n    %s" % (kind, str(label)[:60], why))
    if rejected:
        print("\n有 %d 项不合规，未发送任何内容。" % len(rejected))
        return 1

    if not args.dry_run and not (args.sn and args.key):
        print("缺少凭证：--sn / --key，或环境变量 BADGE_SN / BADGE_KEY。", file=sys.stderr)
        return 2

    print("目标 %s%s  AI 通行证 %s  共 %d 条" % (base, PUSH_PATH, args.sn or "(未指定)", len(jobs)))

    sent = failed = 0
    unbound = False
    for index, job in enumerate(jobs, start=1):
        request_id = "%s-%d" % (prefix, index)
        for note in job["notes"]:
            print("  ! %s" % note)

        if job["kind"] == "image":
            body, ctype = encode_multipart({"kind": "image", "request_id": request_id},
                                           "image", job["filename"], job["data"], job["mime"])
            summary = "image  %s（%.1f KB）" % (job["filename"], len(job["data"]) / 1024)
        else:
            payload = {"kind": job["kind"], "request_id": request_id}
            payload["rtttl"] = job["rtttl"]
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            ctype = "application/json"
            summary = "%-6s %s" % (job["kind"], job["label"][:60])

        if args.dry_run:
            print("  [dry-run] POST %s  (%s, %d 字节, request_id=%s)"
                  % (summary, ctype.split(";")[0], len(body), request_id))
            sent += 1
            continue

        try:
            status, text = request(base + PUSH_PATH, headers, body, ctype, timeout=args.timeout)
        except ConnectionError as exc:
            print("  ✕ %s  %s" % (summary, exc))
            failed += 1
            continue

        line, data = explain(status, text)
        if status == 201:
            extra = ""
            if not data.get("deliverable", True):
                extra = "  ⚠ 这张 AI 通行证还没绑定观众"
                unbound = True
            print("  ✓ %s → item %s%s" % (summary, data.get("id"), extra))
            if data.get("image_url"):
                print("      %s" % data["image_url"])
            sent += 1
        else:
            print("  ✕ %s → %s" % (summary, line))
            failed += 1

    print("\n完成：成功 %d，失败 %d" % (sent, failed))
    if unbound:
        print("有内容入队了但暂时无法下发——这张 AI 通行证还没绑定观众，绑定后会自动下发。")
    if sent and not args.dry_run:
        print("内容不会实时显示在 AI 通行证上。用 --status <id> 查询是否已同步。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

## 硬约束（照抄 `backend/apps/mcp/service.py`）

| 项 | 约束 | 不满足会怎样 |
| --- | --- | --- |
| 图片比例 | **竖向 3:4**，`宽/高` 与 0.75 偏差 ≤1% | 后端拒。**最容易踩的坑**，用 `--fit cover` 可自动裁 |
| 图片体积 | ≤ 5MB | 后端拒 |
| 图片最长边 | >1024px 服务器**自动等比缩小** | 不拒 |
| RTTTL | 三段式 `name:d=4,o=5,b=63:notes`，**至少两个冒号** | 后端拒 |
| 限流 | 默认每张 AI 通行证每分钟 30 次 | 429。**按调用次数算，失败的也计数** |

> ⚠ AI 通行证屏幕是一块 320×240 的面板**旋转 90° 安装**，显示区域是竖向 3:4。
> 别照 320×240 出图——那是面板规格，不是显示区域。

> ⚠ 铃声**不是音频文件**。AI 通行证使用蜂鸣器，只支持 RTTTL 曲谱（老式诺基亚铃声格式）。
> 形如 `trae:d=4,o=5,b=125:16e6,16e6,32p,8e6`——`d` 默认时值、`o` 默认八度、`b` 速度。

## 常见问题

| 现象 | 原因 |
| --- | --- |
| 401 `MCP_CREDENTIAL_INVALID` | SN 或 KEY 不对。**SN 不存在和 KEY 错返回同一个错误**，是故意的，防止拿 SN 遍历试探 |
| 403 `MCP_CREDENTIAL_DISABLED` | AI 通行证的状态不是「可用」（停用/遗失），或后台已停用这个调用方 |
| 429 `MCP_RATE_LIMITED` | 超过限流。等待 60 秒，或让运营调高这张 AI 通行证的上限 |
| 推送成功但 `deliverable: false` | 这张 AI 通行证还没绑定观众。内容留在队列中，绑定后会下发 |
| 推送成功但 AI 通行证上一直没显示 | 观众的小程序未连接蓝牙或不在前台。`--status` 一直是 `pending` 通常就是这个原因 |
| 图片被拒 | 比例不是竖向 3:4。加 `--fit cover` 自动裁，或按提示的尺寸重裁 |
| `--status` 返回 `NOT_FOUND` | id 写错了，或**这条内容属于其他 AI 通行证**（跨通行证查询一律返回 404） |
| 重复推了一堆一样的内容 | 每次运行的 `request_id` 前缀按时间生成，两次运行就是两条。要幂等就显式传 `--request-id-prefix` |

## 相关

- 接口全貌：`trae-world-admin/docs/mydocs/feishu/doc_mcp.md`
- 校验逻辑源头：`trae-world-admin/backend/apps/mcp/service.py`
- 测试环境：`https://trae-dev.siliconpear.cn`，凭证使用 `YOUR_BADGE_SN` / `YOUR_BADGE_KEY` 占位符
