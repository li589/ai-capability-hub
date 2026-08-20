#!/usr/bin/env python3
"""
DesignKit 电商套图 — webapi 基址默认正式环境，鉴权与 run_command.sh 一致。

环境变量：
- DESIGNKIT_OPENCLAW_AK：请求头 X-Openclaw-AK（必填）
- DESIGNKIT_OPENCLAW_AK_URL：获取/核对 AK 的页面基址，公共渠道会自动写入查询参数
- DESIGNKIT_WEBAPI_BASE：仅域名基址（不含版本前缀）；默认 https://openclaw-designkit-api.meitu.com，具体 path 跟随各接口定义
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
import ssl
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from security_logging import (
    format_curl_command,
    format_json_log,
    format_multipart_curl,
    request_log_enabled as shared_request_log_enabled,
    sanitize_json_payload,
)
from local_image_guard import describe_local_image, normalize_local_image_path
from request_context import account_portal_url, channel_value, with_channel

# 可通过 DESIGNKIT_WEBAPI_BASE 覆盖；仅域名，不自动拼版本前缀，具体 path 在各接口调用处定义
_webapi_base_raw = os.environ.get(
    "DESIGNKIT_WEBAPI_BASE",
    "https://openclaw-designkit-api.meitu.com",
).rstrip("/")
WEBAPI_BASE = re.sub(r"/v1/?$", "", _webapi_base_raw)

def _build_ssl_context() -> Optional[ssl.SSLContext]:
    cafile = os.environ.get("SSL_CERT_FILE", "").strip()
    if cafile:
        try:
            return ssl.create_default_context(cafile=cafile)
        except Exception:  # pylint: disable=broad-except
            pass

    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # pylint: disable=broad-except
        return None


_SSL_CONTEXT = _build_ssl_context()


def _remote_image_delivery() -> Dict[str, str]:
    """返回 WorkBuddy 商品图片的统一对话渲染协议。"""
    return {
        "mode": "remote_url",
        "render": "inline",
        "render_format": "markdown_image",
        "render_template": "![{label}]({url})",
        "source_field": "items[].res_img",
        "download_policy": "on_user_request",
        "instruction": "在最终回复中按 items 顺序逐个输出 ![标签](res_img)；每个图片节点单独一行，不要放进 Markdown 表格或代码块，也不要用 present_files 处理远程 URL。",
    }


def _urlopen(req: urllib.request.Request, timeout: int | float):
    full_url = str(getattr(req, "full_url", "")).lower()
    if _SSL_CONTEXT is not None and full_url.startswith("https://"):
        return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)
    return urllib.request.urlopen(req, timeout=timeout)


def _request_log_enabled() -> bool:
    return shared_request_log_enabled()


def _request_log(message: str) -> None:
    if _request_log_enabled():
        print(f"[REQUEST] {message}", file=sys.stderr)


def _request_log_as_curl(
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes] = None,
) -> None:
    if not _request_log_enabled():
        return
    print(
        "[REQUEST] "
        + format_curl_command(
            method,
            url,
            headers,
            data,
            max_time=120,
        ),
        file=sys.stderr,
    )


def _request_log_as_curl_multipart(
    upload_url: str,
    fname: str,
    file_path: str,
    mime: str,
) -> None:
    if not _request_log_enabled():
        return
    print(
        "[REQUEST] "
        + format_multipart_curl(
            upload_url,
            file_path=file_path,
            mime=mime,
            form_fields={
                "token": "<redacted>",
                "key": "<redacted>",
                "fname": fname,
            },
            headers={
                "Origin": "https://www.designkit.cn",
                "Referer": "https://www.designkit.cn/editor/",
            },
            max_time=120,
        ),
        file=sys.stderr,
    )


def _request_log_response_json(
    label: str,
    text: str,
    http_code: Optional[int] = None,
) -> None:
    if not _request_log_enabled():
        return
    try:
        max_len = int(os.environ.get("OPENCLAW_REQUEST_LOG_BODY_MAX", "20000"))
    except ValueError:
        max_len = 20000
    print(
        format_json_log(label, text, max_len=max_len, http_code=http_code),
        file=sys.stderr,
    )

# 爆款风格 prompt：仅替换 [输入] 三节；市场审美段默认美国，可用 market_zh 覆盖标题
STYLE_PROMPT_HEAD = (
    "\n你是电商视觉美术指导，精通品类视觉定调与风格一致性控制。\n\n[输入]\n"
    "- 产品: {product_info}\n- 平台: {platform}\n- 目标市场: {market}\n\n[市场审美参考]\n\n"
    "        [目标市场：{market_zh}]\n"
    "        - **视觉审美偏好**：高对比度、鲜艳有冲击力、商业感强、直接明快\n"
    "        - **环境风格参考**：现代美式、工业风、开放式空间、充足自然光\n"
    "        - **色彩调性**：明亮饱和、温暖色调、\"商业流行风\"\n"
    "    \n\n[平台风格]\n"
    "- **中国电商**（淘宝/京东/抖音/拼多多）：视觉冲击力强，可用彩色底/渐变底，强调吸睛转化\n"
    "- **海外电商**（amazon/temu/tiktok/Shopee/Aliexpress/Alibaba/OZON/shopify）：克制高级，强调真实感品质感\n\n[任务]\n"
    "为该产品生成 **4 套视觉差异明显** 的商业摄影风格方案，每套可复用于7张图集。\n\n[品类风格参考]\n"
    "根据产品品类灵活调整，不要机械套用：\n"
    "- 科技产品 → 均匀柔光，干净留白，中性色调\n"
    "- 游戏设备 → 侧光透射，暗色背景，冷峻力量感\n"
    "- 家居产品 → 自然暖光，柔和通透，生活气息\n"
    "- 运动装备 → 自然光，明快清晰，阳光活力\n"
    "- 服饰配件 → 柔和侧光，质感细腻，优雅克制\n"
    "- 美妆护肤 → 均匀柔光，干净透亮，精致感\n\n[核心规则]\n"
    "1. **仅限真实摄影风格**：严禁油画/水彩/动漫/素描等插画风格\n"
    "2. **globalStyleNote 格式**：\n"
    "   - 仅含光影+氛围关键词，15-25词\n"
    "   - ✅ 允许：\"自然暖光，45度柔和漫射光，柔和通透，生活气息\"\n"
    "   - ❌ 禁止：任何场景、物体、背景、道具描述\n"
    "3. **产品颜色真实**：禁止极端色温（<2700K或>6500K）和浓重滤镜\n"
    "4. **colorPalette 首位**：必须是产品固有色（如绿色沙发→绿色）\n"
    "5. **字体红线**：严禁细字体/书法体/手写体，禁止输出具体字体名\n"
    "6. **全局风格可复用性**：每套风格必须能作为基调应用到7张商品图中，仅需调整场景细节即可保持视觉语言统一\n"
    "7. **转化导向**：风格必须提升产品感知价值，建立买家信任\n\n[输出格式]\n"
    "直接输出纯JSON数组，中文输出。每个对象包含以下字段：\n\n"
    "| 字段 | 描述 | 示例 |\n"
    "|------|------|------|\n"
    "| name | 风格名称（2-4词，通俗易懂） | \"温馨居家\" \"简约专业\" |\n"
    "| reasoning | 选择理由（≤15词，口语化） | \"让沙发看起来更舒适温馨\" |\n"
    "| globalStyleNote | 光影+氛围关键词（15-25词） | \"自然暖光，45度柔和漫射光，柔和通透\" |\n"
    "| fontStyleDescription | 字体视觉特征描述 | \"粗壮无衬线体，中等字重，现代商业感\" |\n"
    "| colorPalette | 3个hex色值（产品色+背景色+强调色） | \"#2ECC71, #F8F9FA, #FF6B6B\" |\n"
    "| colorDescription | 颜色用途说明 | \"森林绿（产品原色），云雾白（背景），珊瑚红（强调）\" |\n"
    "| iconStyle | 图标风格描述 | \"粗线性极简风格\" |\n\n[输出前自检]\n"
    "- [ ] globalStyleNote 包含光影+氛围词，不包含场景/物体/背景描述，15-25词\n"
    "- [ ] 光影设置不会导致产品颜色失真\n"
    "- [ ] fontStyleDescription 是描述性语言，不包含具体字体名称\n"
    "- [ ] colorPalette 第一个颜色是产品固有色\n"
    "- [ ] 4 个风格方案视觉上有明显差异\n"
    "- [ ] name 和 reasoning 简洁易懂\n"
)

MARKET_ZH = {
    "US": "美国",
    "CN": "中国",
    "UK": "英国",
    "JP": "日本",
    "DE": "德国",
    "FR": "法国",
    "AU": "澳大利亚",
}

PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT_SUBDIR = "designkit-ecommerce-product-kit"
PRICE_SUBFUNC = "gemini_ai_product"
PRODUCT_KIT_IMAGE_COUNT = 7


def _json_error(
    ok: bool,
    error_type: str,
    message: str,
    user_hint: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    out: Dict[str, Any] = {
        "ok": ok,
        "error_type": error_type,
        "message": message,
        "user_hint": user_hint,
    }
    if extra:
        out.update(extra)
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(1 if not ok else 0)


def _require_ak() -> str:
    ak = os.environ.get("DESIGNKIT_OPENCLAW_AK", "").strip()
    if not ak:
        _json_error(
            False,
            "CREDENTIALS_MISSING",
            "缺少 DESIGNKIT_OPENCLAW_AK",
            f"请前往 {account_portal_url()} 完成注册或付费，并在运行环境的安全凭据配置中设置 API Key",
        )
    return ak


def _query_params() -> Dict[str, str]:
    """构造商品套图服务的公共查询参数，包含统一渠道标记。"""
    return {
        "client_id": os.environ.get("DESIGNKIT_OPENCLAW_CLIENT_ID", "2288866677"),
        "client_language": os.environ.get("DESIGNKIT_CLIENT_LANGUAGE", "zh-Hans"),
        "channel": channel_value(),
        "country_code": os.environ.get("DESIGNKIT_COUNTRY_CODE", "CN"),
        "ts_random_id": str(uuid.uuid4()),
        "client_source": "pc",
        "client_timezone": os.environ.get("DESIGNKIT_CLIENT_TIMEZONE", "Asia/Shanghai"),
        "operate_source": "web",
    }


def _headers_json(require_ak: bool = True) -> Dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.designkit.cn",
        "Referer": "https://www.designkit.cn/product-kit/?from=home",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    ak = os.environ.get("DESIGNKIT_OPENCLAW_AK", "").strip()
    if require_ak:
        ak = _require_ak()
    if ak:
        headers["X-Openclaw-AK"] = ak
    return headers


def _headers_get(require_ak: bool = True) -> Dict[str, str]:
    h = _headers_json(require_ak=require_ak)
    del h["Content-Type"]
    return h


def _url(path: str, extra: Optional[Dict[str, str]] = None) -> str:
    """生成 OpenClaw 商品套图 URL，并阻止附加参数覆盖渠道标记。"""
    from urllib.parse import urlencode

    q = _query_params()
    if extra:
        q = {**q, **extra}
    return with_channel(f"{WEBAPI_BASE}{path}?{urlencode(q)}")


def _http_request(
    method: str,
    url: str,
    body: Optional[bytes] = None,
    json_mode: bool = True,
    extra_headers: Optional[Dict[str, str]] = None,
    require_ak: bool = True,
) -> Tuple[int, Any]:
    url = with_channel(url)
    headers = _headers_json(require_ak=require_ak) if json_mode and body else _headers_get(require_ak=require_ak)
    if extra_headers:
        headers.update(extra_headers)
    if body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    _request_log_as_curl(method, url, headers, body)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with _urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode() or 200
            _request_log_response_json("response_body", raw, code)
            try:
                return code, json.loads(raw)
            except json.JSONDecodeError:
                return code, {"_raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        _request_log_response_json("response_body", raw, e.code)
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw, "_http_message": str(e)}
    except urllib.error.URLError as e:
        return 503, {"_raw": str(e), "_error_type": "url_error"}


def _downloads_dir() -> pathlib.Path:
    return pathlib.Path.home() / "Downloads"


def _default_visual_dir() -> pathlib.Path:
    openclaw_home = os.environ.get("OPENCLAW_HOME", "").strip()
    if openclaw_home:
        return pathlib.Path(openclaw_home).expanduser() / "workspace" / "visual"
    return pathlib.Path.home() / ".openclaw" / "workspace" / "visual"


def _looks_like_skill_internal(path: pathlib.Path) -> bool:
    try:
        path.relative_to(PROJECT_ROOT)
        return True
    except ValueError:
        return False


def resolve_output_dir(inp: Dict[str, Any]) -> pathlib.Path:
    explicit = str(inp.get("output_dir", "") or os.environ.get("DESIGNKIT_OUTPUT_DIR", "")).strip()
    if explicit:
        output_dir = pathlib.Path(explicit).expanduser().resolve()
    else:
        cwd = pathlib.Path.cwd().resolve()
        if (cwd / "openclaw.yaml").is_file():
            output_dir = cwd / "output"
        else:
            visual_dir = _default_visual_dir()
            if visual_dir.is_dir():
                output_dir = visual_dir / "output" / DEFAULT_OUTPUT_SUBDIR
            else:
                output_dir = _downloads_dir()

    if _looks_like_skill_internal(output_dir):
        _json_error(
            False,
            "PARAM_ERROR",
            f"输出目录不能位于 skill 目录内部: {output_dir}",
            "请改用项目 output 目录、共享 visual output 目录，或传入其他 output_dir",
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _safe_filename_part(value: str, fallback: str, max_bytes: int = 96) -> str:
    """生成适合本地文件名的片段，并按 UTF-8 字节数截断以兼容文件系统限制。"""
    text = re.sub(r"\s+", "_", (value or "").strip())
    text = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    text = text or fallback
    if len(text.encode("utf-8")) > max_bytes:
        text = text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore").rstrip("._-")
    return text or fallback


def _guess_extension(url: str, default_ext: str = ".jpg") -> str:
    path = urllib.parse.urlparse(url).path
    ext = pathlib.Path(path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    return default_ext


def _local_image_paths_from_items(
    items: List[Dict[str, Any]],
    output_dir: pathlib.Path,
    product_name: str,
    *,
    reuse_existing: bool = False,
) -> List[str]:
    """将图片写入指定目录；预览缓存可复用已有文件，用户保存则始终重新获取最新结果。"""
    saved_paths: List[str] = []
    product_part = _safe_filename_part(product_name, "product")

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        image_url = str(item.get("res_img", "")).strip()
        if not image_url.startswith("http"):
            continue
        label = _safe_filename_part(str(item.get("label", "")).strip(), f"image_{index}", max_bytes=48)
        ext = _guess_extension(image_url)
        filename = f"{product_part}_{index:02d}_{label}{ext}"
        target = output_dir / filename
        if reuse_existing and target.is_file() and target.stat().st_size > 0:
            saved_paths.append(str(target))
            continue

        req = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": _headers_get().get("User-Agent", "Mozilla/5.0"),
                "Accept": "image/*,*/*;q=0.8",
            },
            method="GET",
        )
        try:
            with _urlopen(req, timeout=120) as resp:
                data = resp.read()
            target.write_bytes(data)
        except Exception as exc:
            # 图片已在服务端生成，本地落盘失败只记录脱敏诊断并保留在线结果。
            print(
                json.dumps(
                    {
                        "event": "product_artifact_download_failed",
                        "item_index": index,
                        "error_type": type(exc).__name__,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            saved_paths.append("")
            continue

        saved_paths.append(str(target))

    return saved_paths


def _report_product_batch_download(task_ids: List[str]) -> str:
    """批量调用商品套图 download 接口上报下载；异常时返回空值供调用方回退 res_img。"""
    normalized_task_ids = list(
        dict.fromkeys(str(task_id).strip() for task_id in task_ids if str(task_id).strip())
    )
    if not normalized_task_ids:
        return ""
    body = json.dumps({"task_ids": ",".join(normalized_task_ids)}, ensure_ascii=False).encode("utf-8")
    try:
        code, resp = _http_request("POST", _url("/v1/hackathon/download"), body)
    except Exception as exc:  # pylint: disable=broad-except
        # 下载上报不能阻断图片交付，仅记录异常类型，不记录任务参数或凭据信息。
        print(
            json.dumps(
                {
                    "event": "product_kit_download_report_failed",
                    "error_type": type(exc).__name__,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return ""

    api_code = _api_code(resp)
    if code != 200 or api_code not in (0, None):
        error_type, _ = _map_api_error(api_code, _api_message(resp))
        print(
            json.dumps(
                {
                    "event": "product_kit_download_report_failed",
                    "error_type": error_type,
                    "http_code": code,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return ""

    data = resp.get("data") if isinstance(resp, dict) else {}
    if isinstance(data, dict):
        download_url = str(data.get("download_url") or "").strip()
        if download_url.startswith("http"):
            return download_url
    return ""


def _report_product_downloads(items: List[Dict[str, Any]]) -> List[str]:
    """在用户明确下载时一次上报整套成功图片；失败任务 ID 由调用方用于重试提示。"""
    task_ids: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result_url = str(item.get("res_img") or "").strip()
        task_id = str(item.get("task_id") or item.get("id") or "").strip()
        if not result_url.startswith("http") or not task_id:
            continue
        task_ids.append(task_id)
    if not task_ids:
        return []
    reported_url = _report_product_batch_download(task_ids)
    return [] if reported_url.startswith("http") else task_ids


def upload_local_image(file_path: str) -> str:
    normalized_path = normalize_local_image_path(file_path)
    if not os.path.isfile(normalized_path):
        _json_error(False, "PARAM_ERROR", f"文件不存在: {normalized_path}", "请检查图片路径")

    try:
        _, mime = describe_local_image(normalized_path)
    except ValueError as exc:
        _json_error(False, "PARAM_ERROR", str(exc), "请提供 JPG/JPEG/PNG/WEBP/GIF 图片文件")
    fname = os.path.basename(normalized_path)

    getsign_url = _url("/maat/getsign", {"type": "openclaw"})
    getsign_code, getsign_resp = _http_request("GET", getsign_url, json_mode=False)
    if getsign_code < 200 or getsign_code >= 300 or not isinstance(getsign_resp, dict):
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")
    if getsign_resp.get("code") != 0:
        _request_log(
            f"maat getsign rejected: {json.dumps(sanitize_json_payload(getsign_resp), ensure_ascii=False)}"
        )
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")

    policy_url_full = str((getsign_resp.get("data") or {}).get("upload_url") or "").strip()
    if not policy_url_full:
        _request_log(
            f"maat getsign missing upload_url: {json.dumps(sanitize_json_payload(getsign_resp), ensure_ascii=False)}"
        )
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")
    policy_url_full = with_channel(policy_url_full)

    _request_log_as_curl(
        "GET",
        policy_url_full,
        {
            "Origin": "https://www.designkit.cn",
            "Referer": "https://www.designkit.cn/editor/",
        },
        None,
    )
    policy_req = urllib.request.Request(policy_url_full)
    policy_req.add_header("Origin", "https://www.designkit.cn")
    policy_req.add_header("Referer", "https://www.designkit.cn/editor/")
    try:
        with _urlopen(policy_req, timeout=30) as resp:
            code = resp.getcode() or 200
            raw_policy = resp.read().decode()
            _request_log_response_json("policy_response_body", raw_policy, code)
            if code < 200 or code >= 300:
                _json_error(False, "UPLOAD_ERROR", "获取上传策略失败", "请检查网络连接后重试")
            arr = json.loads(raw_policy)
    except Exception as e:
        _json_error(False, "UPLOAD_ERROR", str(e), "获取上传策略失败，请检查网络")

    provider = arr[0]["order"][0]
    p = arr[0][provider]
    token, key, up_url, up_data = p["token"], p["key"], p["url"], p["data"]

    boundary = uuid.uuid4().hex.encode()
    with open(normalized_path, "rb") as f:
        file_bytes = f.read()

    def part(name: str, value: str) -> bytes:
        return (
            b"--"
            + boundary
            + b'\r\nContent-Disposition: form-data; name="'
            + name.encode()
            + b'"\r\n\r\n'
            + value.encode()
            + b"\r\n"
        )

    post_body = (
        part("token", token)
        + part("key", key)
        + part("fname", fname)
        + b"--"
        + boundary
        + b'\r\nContent-Disposition: form-data; name="file"; filename="'
        + fname.encode()
        + b'"\r\nContent-Type: '
        + mime.encode()
        + b"\r\n\r\n"
        + file_bytes
        + b"\r\n--"
        + boundary
        + b"--\r\n"
    )

    upload_target = f"{up_url}/"
    _request_log_as_curl_multipart(upload_target, fname, normalized_path, mime)
    up_req = urllib.request.Request(upload_target, data=post_body, method="POST")
    up_req.add_header("Content-Type", f"multipart/form-data; boundary={boundary.decode()}")
    up_req.add_header("Origin", "https://www.designkit.cn")
    up_req.add_header("Referer", "https://www.designkit.cn/editor/")
    try:
        with _urlopen(up_req, timeout=120) as resp:
            ucode = resp.getcode() or 200
            raw_up = resp.read().decode()
            _request_log_response_json("upload_response_body", raw_up, ucode)
            up_json = json.loads(raw_up)
    except Exception as e:
        _json_error(False, "UPLOAD_ERROR", str(e), "上传失败，请换图或稍后重试")

    cdn = up_json.get("data") or up_data
    if not cdn:
        _request_log("upload response: no CDN URL in body")
        _json_error(False, "UPLOAD_ERROR", "无 CDN URL", "上传响应异常")
    return str(cdn)


def resolve_image_url(image: str) -> str:
    image = (image or "").strip()
    if not image:
        _json_error(False, "PARAM_ERROR", "缺少 image", "请提供商品图 URL 或本地路径")
    if re.match(r"^https?://", image, re.I):
        return image
    return upload_local_image(image)


def extract_task_id(resp: Any) -> Optional[str]:
    if not isinstance(resp, dict):
        return None
    for path in (
        ("data", "task_id"),
        ("data", "id"),
        ("task_id",),
        ("id",),
    ):
        cur: Any = resp
        for k in path:
            if isinstance(cur, dict):
                cur = cur.get(k)
            else:
                cur = None
                break
        if isinstance(cur, str) and cur:
            return cur
    return None


def k2_done(resp: Any) -> Tuple[bool, Optional[str]]:
    """返回 (是否已结束, 文本/结果串用于解析风格)."""
    if not isinstance(resp, dict):
        return False, None
    data = resp.get("data")
    if not isinstance(data, dict):
        return False, None
    st = data.get("status")
    st_str = str(st).lower() if st is not None else ""
    if st in (0, 1, "0", "1") or st_str in ("pending", "running", "processing", "queue", "queued"):
        return False, None
    # 在 data 的直属字段中查找文本结果
    for key in ("result", "content", "text", "output", "message", "answer"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return True, v
    # 在嵌套的 result 对象中查找文本字段（如 data.result.message）
    result_obj = data.get("result")
    if isinstance(result_obj, dict):
        for key in ("message", "content", "text", "output", "answer"):
            v = result_obj.get(key)
            if isinstance(v, str) and v.strip():
                return True, v
    # result 为 None 表示尚无结果产出，即使 status >= 2 也继续等待
    if result_obj is None:
        return False, None
    # result 非空但无可识别的文本字段，序列化整个 data 返回
    is_terminal = (isinstance(st, int) and st >= 2) or st_str in (
        "2", "3", "success", "complete", "done", "finished",
    )
    if is_terminal:
        return True, json.dumps(data, ensure_ascii=False)
    return False, None


def extract_batch_media(resp: Any) -> List[str]:
    urls: List[str] = []
    if not isinstance(resp, dict):
        return urls
    data = resp.get("data") or resp

    def collect(obj: Any) -> None:
        if isinstance(obj, str) and obj.startswith("http"):
            urls.append(obj)
        elif isinstance(obj, dict):
            for k in ("url", "media_url", "image_url", "src"):
                v = obj.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
            for v in obj.values():
                collect(v)
        elif isinstance(obj, list):
            for v in obj:
                collect(v)

    collect(data)
    return list(dict.fromkeys(urls))


def _api_code(resp: Any) -> Optional[int]:
    if not isinstance(resp, dict):
        return None
    value = resp.get("code")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def _api_message(resp: Any) -> str:
    if isinstance(resp, dict):
        return str(resp.get("message", "")).strip()
    return ""


def _map_api_error(code: Optional[int], message: str) -> Tuple[str, str]:
    mapping = {
        401: ("AUTH_ERROR", "账号凭据无效，请在运行环境的安全凭据配置中重新设置 API Key"),
        11001: ("PARAM_ERROR", "请求参数有误，请检查商品图和生成设置后重试"),
        11002: ("API_ERROR", "服务暂时不可用，请稍后重试"),
        10024: ("PARAM_ERROR", "商品图参数错误，请更换商品图后重试"),
        10025: ("CONTENT_RISK", "图片或文案未通过内容安全审核，请更换素材后重试"),
        10041: ("CONTENT_RISK", "商品图不合规，请更换图片后重试"),
        300101: ("MEMBER_REQUIRED", "当前账号缺少所需权益，请先完成开通后再试"),
        300106: ("PARAM_ERROR", "请求参数有误，请检查输入后重试"),
        16800001: ("BALANCE_INSUFFICIENT", "余额不足，请先充值后再提交商品套图任务"),
        1600001: ("BALANCE_INSUFFICIENT", "余额不足，请先充值后再提交商品套图任务"),
        60000001: ("RATE_LIMITED", "操作过于频繁，请稍后再试"),
    }
    if code in mapping:
        return mapping[code]
    return "API_ERROR", (message or "请求失败，请稍后重试")


def _ensure_ok_envelope(code: int, resp: Any, action_hint: str) -> None:
    if code != 200:
        if isinstance(resp, dict) and resp.get("_error_type") == "url_error":
            _json_error(
                False,
                "TEMPORARY_UNAVAILABLE",
                "网络连接失败",
                "网络连接失败或服务暂时不可用，请检查网络后稍后重试",
                {"http_code": code, "result": resp},
            )
        api_code = _api_code(resp)
        error_type, hint = _map_api_error(api_code, _api_message(resp))
        _json_error(
            False,
            error_type,
            _api_message(resp) or f"HTTP {code}",
            hint or action_hint,
            {"http_code": code, "api_code": api_code, "result": resp},
        )

    api_code = _api_code(resp)
    if api_code not in (0, None):
        error_type, hint = _map_api_error(api_code, _api_message(resp))
        _json_error(
            False,
            error_type,
            _api_message(resp) or action_hint,
            hint or action_hint,
            {"api_code": api_code, "result": resp},
        )


def _preview_hint(result: Dict[str, Any]) -> str:
    payment = int(result.get("payment_amount") or result.get("price") or 0)
    success = bool(result.get("success"))
    guide_policy = result.get("guide_policy")
    if success and payment <= 0:
        return "本次 7 张商品套图预计可使用限免或现有权益完成，不消耗美豆。"
    if success:
        return f"本次预计消耗 {payment} 美豆生成 7 张商品套图；当前只是价格预览，尚未提交或扣费。"
    if guide_policy == 3:
        return "需要先配置有效 API Key，才能校验账号权益和余额。"
    if guide_policy in {1, 4, 9, 10}:
        return "当前账号权益不足，请先通过专属页面开通所需权益。"
    if guide_policy in {2, 7}:
        return f"本次预计需要 {payment} 美豆，请先确认余额充足。"
    return str(result.get("message") or "价格预览未通过，请检查账号权益后重试。")


def cmd_preview(inp: Dict[str, Any]) -> None:
    market = str(inp.get("market", "US")).strip() or "US"
    is_pro = bool(inp.get("is_pro", True))
    has_ak = bool(os.environ.get("DESIGNKIT_OPENCLAW_AK", "").strip())
    preview_scope = "account" if has_ak else "anonymous"

    body_obj = {
        "client_id": os.environ.get("DESIGNKIT_OPENCLAW_CLIENT_ID", "2288866677"),
        "client_language": os.environ.get("DESIGNKIT_CLIENT_LANGUAGE", "zh-Hans"),
        "client_timezone": os.environ.get("DESIGNKIT_CLIENT_TIMEZONE", "Asia/Shanghai"),
        "country_code": market.upper() if re.fullmatch(r"[A-Za-z]{2}", market) else "US",
        "ignore_login": "false" if has_ak else "true",
        "num": str(PRODUCT_KIT_IMAGE_COUNT),
        "preview_mode": "1",
        "subfunc": PRICE_SUBFUNC,
        "task_param": json.dumps({"is_pro": is_pro}, ensure_ascii=False),
    }

    def request_price(require_ak: bool) -> Tuple[int, Any]:
        return _http_request(
            "POST",
            _url("/v1/purchase/price_calculate"),
            urllib.parse.urlencode(body_obj).encode("utf-8"),
            json_mode=False,
            extra_headers={"Content-Type": "application/x-www-form-urlencoded"},
            require_ak=require_ak,
        )

    code, resp = request_price(has_ak)
    if has_ak and _api_code(resp) == 401:
        body_obj["ignore_login"] = "true"
        preview_scope = "anonymous"
        code, resp = request_price(False)

    _ensure_ok_envelope(code, resp, "暂时无法获取商品套图价格，请稍后重试")

    data = resp.get("data") if isinstance(resp, dict) else {}
    result = data if isinstance(data, dict) else {}
    user_hint = _preview_hint(result)
    if preview_scope == "anonymous":
        user_hint = "当前为未登录价格估算，不代表账号余额已校验。" + user_hint

    print(
        json.dumps(
            {
                "ok": True,
                "command": "ecommerce_preview",
                "preview_scope": preview_scope,
                "count": PRODUCT_KIT_IMAGE_COUNT,
                "price": result.get("price"),
                "payment_amount": result.get("payment_amount"),
                "unit_price": result.get("unit_price"),
                "discount_unit_price": result.get("discount_unit_price"),
                "available_amount": result.get("available_amount"),
                "guide_policy": result.get("guide_policy"),
                "success": result.get("success"),
                "user_hint": user_hint,
                "next": "价格确认后再执行 render_submit。",
            },
            ensure_ascii=False,
        )
    )


def cmd_style_create(inp: Dict[str, Any]) -> None:
    image = resolve_image_url(str(inp.get("image", "")))
    product_info = str(inp.get("product_info", inp.get("selling_points", ""))).strip() or "商品"
    platform = str(inp.get("platform", "amazon")).strip()
    market = str(inp.get("market", "US")).strip()
    market_zh = str(inp.get("market_zh", "") or MARKET_ZH.get(market.upper(), "美国"))
    api_engine = str(inp.get("api_engine", "doubao-seed-2.0-lite"))

    prompt = STYLE_PROMPT_HEAD.format(
        product_info=product_info,
        platform=platform,
        market=market,
        market_zh=market_zh,
    )
    body = json.dumps(
        {"api_engine": api_engine, "prompt": prompt, "images": image},
        ensure_ascii=False,
    ).encode()

    url = _url("/v1/mtlab/ai_text")
    code, resp = _http_request("POST", url, body)
    _ensure_ok_envelope(code, resp, "创建风格任务失败，请稍后重试")

    task_id = extract_task_id(resp)
    out = {
        "ok": True,
        "command": "ecommerce_style_create",
        "task_id": task_id,
        "result": resp,
        "user_hint": "若 task_id 为空，请从 result 内自行查找任务 id 后轮询 k2_query",
    }
    print(json.dumps(out, ensure_ascii=False))


def cmd_style_poll(inp: Dict[str, Any]) -> None:
    task_id = str(inp.get("task_id", "")).strip()
    if not task_id:
        _json_error(False, "PARAM_ERROR", "缺少 task_id", "请先执行 style_create 或从创建响应取 task_id")

    max_wait = float(inp.get("max_wait_sec", 180))
    interval = float(inp.get("interval_sec", 2))
    deadline = time.time() + max_wait

    while time.time() < deadline:
        url = _url("/v1/mtlab/k2_query", {"task_id": task_id})
        code, resp = _http_request("GET", url)
        _ensure_ok_envelope(code, resp, "查询风格任务失败，请稍后重试")

        done, text = k2_done(resp)
        if done and text:
            styles: Any = None
            try:
                # 模型可能输出 ```json ... ```
                m = re.search(r"\[[\s\S]*\]", text)
                if m:
                    styles = json.loads(m.group(0))
            except json.JSONDecodeError:
                styles = None
            out = {
                "ok": True,
                "command": "ecommerce_style_poll",
                "done": True,
                "styles": styles,
                "styles_raw": text,
                "result": resp,
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        time.sleep(interval)

    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "TEMPORARY_UNAVAILABLE",
                "message": "轮询超时",
                "user_hint": f"在 {max_wait}s 内未完成，可增大 max_wait_sec 后重试",
                "task_id": task_id,
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


def cmd_render_submit(inp: Dict[str, Any]) -> None:
    transfer_id = str(inp.get("transfer_id", "") or str(uuid.uuid4()).upper())
    image_urls = inp.get("image_urls")
    if not image_urls:
        one = inp.get("image")
        if one:
            image_urls = [resolve_image_url(str(one))]
    if not isinstance(image_urls, list) or not image_urls:
        _json_error(False, "PARAM_ERROR", "缺少 image_urls", "请传 image_urls 数组或单个 image")

    resolved = [resolve_image_url(str(u)) if not re.match(r"^https?://", str(u), re.I) else str(u) for u in image_urls]

    brand_style = inp.get("brand_style")
    if brand_style is not None and not isinstance(brand_style, dict):
        _json_error(False, "PARAM_ERROR", "brand_style 须为对象或留空", "请传入风格 JSON 或省略此字段由服务端自动选择")

    style_name = str(inp.get("style_name", (brand_style or {}).get("name", "")))
    product_info = str(inp.get("product_info", "")).strip() or "商品"
    raw_aspect_ratio = inp.get("aspect_ratio")
    if raw_aspect_ratio in (None, ""):
        raw_aspect_ratio = inp.get("ratio", "1:1")
    aspect_ratio = str(raw_aspect_ratio or "1:1").strip() or "1:1"
    language = str(inp.get("language", "English"))
    platform = str(inp.get("platform", "amazon"))
    market = str(inp.get("market", "US"))
    is_pro = bool(inp.get("is_pro", True))

    burial = inp.get("burial_point")
    if burial is None:
        burial = {
            "first_func": "product_kit",
            "page_name": "commerce",
            "target_platform": platform,
            "target_market": market,
            "language": language,
            "proportion": aspect_ratio,
            "fileName": "openclaw",
            "productInfo": product_info,
            "core_point_type": "customize",
            "is_pro": is_pro,
        }
    burial_str = burial if isinstance(burial, str) else json.dumps(burial, ensure_ascii=False)

    body_obj = {
        "image_urls": resolved,
        "style_name": style_name,
        "product_info": product_info,
        "aspect_ratio": aspect_ratio,
        "language": language,
        "platform": platform,
        "market": market,
        "is_pro": is_pro,
        "burial_point": burial_str,
    }
    if brand_style is not None:
        body_obj["brand_style"] = brand_style
    body = json.dumps(body_obj, ensure_ascii=False).encode()
    url = _url("/v1/hackathon/ai_product/task_submit", {"transfer_id": transfer_id})
    code, resp = _http_request("POST", url, body)
    _ensure_ok_envelope(code, resp, "提交商品套图任务失败，请稍后重试")

    batch_id = None
    if isinstance(resp, dict):
        batch_id = (
            resp.get("data", {}).get("batch_id")
            if isinstance(resp.get("data"), dict)
            else None
        ) or resp.get("batch_id")

    if not batch_id:
        _json_error(False, "API_ERROR", "提交成功但未返回任务引用", "暂时无法创建商品套图任务，请稍后重试")

    out = {
        "ok": True,
        "command": "ecommerce_render_submit",
        "transfer_id": transfer_id,
        "batch_id": batch_id,
        "result": resp,
        "user_hint": "任务已提交，可继续轮询生成结果",
    }
    print(json.dumps(out, ensure_ascii=False))


def cmd_render_regen(inp: Dict[str, Any]) -> None:
    transfer_id = str(inp.get("transfer_id", "")).strip()
    if not transfer_id:
        _json_error(False, "PARAM_ERROR", "缺少 transfer_id", "请传入需要重生成的 transfer_id")

    task_id = str(inp.get("task_id", "")).strip()
    if not task_id:
        _json_error(False, "PARAM_ERROR", "缺少 task_id", "请传入需要重生成的 task_id")

    form_body = urllib.parse.urlencode({"task_id": task_id}).encode("utf-8")
    url = _url("/v1/hackathon/regen", {"transfer_id": transfer_id})
    code, resp = _http_request(
        "POST",
        url,
        form_body,
        json_mode=False,
        extra_headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    _ensure_ok_envelope(code, resp, "提交单张重生成任务失败，请稍后重试")

    batch_id = None
    if isinstance(resp, dict):
        batch_id = (
            resp.get("data", {}).get("batch_id")
            if isinstance(resp.get("data"), dict)
            else None
        ) or resp.get("batch_id")

    if not batch_id:
        _json_error(False, "API_ERROR", "提交成功但未返回任务引用", "暂时无法创建重生成任务，请稍后重试")

    out = {
        "ok": True,
        "command": "ecommerce_render_regen",
        "transfer_id": transfer_id,
        "task_id": task_id,
        "batch_id": batch_id,
        "result": resp,
        "user_hint": "重生成任务已提交，可继续轮询生成结果",
    }
    print(json.dumps(out, ensure_ascii=False))


def _check_render_items(resp: Any) -> Tuple[int, int, List[str], List[Dict[str, Any]]]:
    """解析渲染结果中子 item 的完成状态。
    返回 (total, done_count, res_img_urls, items_list)。
    """
    items_list: List[Dict[str, Any]] = []
    res_urls: List[str] = []
    if not isinstance(resp, dict):
        return 0, 0, res_urls, items_list
    data = resp.get("data", {})
    if not isinstance(data, dict):
        return 0, 0, res_urls, items_list
    items_map = data.get("items", {})
    if not isinstance(items_map, dict):
        return 0, 0, res_urls, items_list
    for batch_val in items_map.values():
        if not isinstance(batch_val, dict):
            continue
        sub_items = batch_val.get("items", [])
        if not isinstance(sub_items, list):
            continue
        for item in sub_items:
            if not isinstance(item, dict):
                continue
            items_list.append(item)
            res_img = (item.get("res_img") or "").strip()
            if res_img.startswith("http"):
                res_urls.append(res_img)
    return len(items_list), len(res_urls), res_urls, items_list


def _is_failed_render_item(item: Dict[str, Any]) -> bool:
    status = item.get("status")
    if isinstance(status, str) and status.strip().lstrip("-").isdigit():
        status = int(status)
    if status in {-1, 4, 5}:
        return True
    return any(str(item.get(key) or "").strip() for key in ("err_message", "error_message", "error_msg"))


def cmd_render_poll(inp: Dict[str, Any]) -> None:
    batch_id = str(inp.get("batch_id", "")).strip()
    if not batch_id:
        _json_error(False, "PARAM_ERROR", "缺少 batch_id", "请先执行 render_submit")

    max_wait = float(inp.get("max_wait_sec", 600))
    interval = float(inp.get("interval_sec", 3))
    deadline = time.time() + max_wait
    last_done = -1
    last_total = 0
    last_done_count = 0

    while time.time() < deadline:
        url = _url("/v1/hackathon/query", {"batch_id": batch_id})
        code, resp = _http_request("GET", url)
        _ensure_ok_envelope(code, resp, "查询商品套图结果失败，请稍后重试")

        total, done_count, res_urls, items_list = _check_render_items(resp)
        failed_items = [item for item in items_list if _is_failed_render_item(item)]
        terminal_count = done_count + len(failed_items)
        last_total, last_done_count = total, done_count

        # 输出渲染进度
        if total > 0 and done_count != last_done:
            last_done = done_count
            done_labels = [
                it.get("label", "")
                for it in items_list
                if isinstance(it, dict) and (it.get("res_img") or "").startswith("http")
            ]
            hint = "（" + "、".join(done_labels[-3:]) + "）" if done_labels else ""
            print(f"[PROGRESS] {done_count}/{total}{hint}", file=sys.stderr)

        if total > 0 and terminal_count >= total:
            # 结果就绪时完成服务端下载上报并继续交付逐张 URL；该步骤不写本地文件。
            download_report_failed_ids = _report_product_downloads(items_list)
            out = {
                "ok": True,
                "command": "ecommerce_render_poll",
                "done": True,
                "media_urls": res_urls,
                "local_paths": [],
                "download_performed": False,
                "download_reported": not download_report_failed_ids,
                "download_report_failed_count": len(download_report_failed_ids),
                "delivery_mode": "remote_url",
                "delivery": _remote_image_delivery(),
                "items": items_list,
                "failed_items": failed_items,
                "summary": {"total": total, "success": done_count, "failed": len(failed_items)},
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        time.sleep(interval)

    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "TEMPORARY_UNAVAILABLE",
                "message": "生图轮询超时",
                "user_hint": f"在 {max_wait}s 内未拿到全部图片，可增大 max_wait_sec",
                "batch_id": batch_id,
                "progress": f"{last_done_count}/{last_total}",
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


def cmd_render_download(inp: Dict[str, Any]) -> None:
    """用户明确要求保存后，将已经上报的成功图片写入下载目录。"""
    batch_id = str(inp.get("batch_id", "")).strip()
    if not batch_id:
        _json_error(False, "PARAM_ERROR", "缺少 batch_id", "请先等待商品套图生成完成")

    code, resp = _http_request("GET", _url("/v1/hackathon/query", {"batch_id": batch_id}))
    _ensure_ok_envelope(code, resp, "查询商品套图结果失败，请稍后重试")
    total, done_count, res_urls, items_list = _check_render_items(resp)
    failed_items = [item for item in items_list if _is_failed_render_item(item)]
    if total <= 0 or done_count + len(failed_items) < total:
        _json_error(False, "NOT_READY", "商品套图尚未全部完成", "请稍后继续确认生成状态")

    output_dir = resolve_output_dir(inp)
    product_name = str(inp.get("product_name", "")).strip() or str(inp.get("product_info", "")).strip() or "product"
    local_paths = _local_image_paths_from_items(items_list, output_dir, product_name)
    downloadable_items = [
        item
        for item in items_list
        if isinstance(item, dict) and str(item.get("res_img") or "").startswith("http")
    ]
    local_save_failed_ids = [
        str(item.get("task_id") or item.get("id") or f"item-{index}")
        for index, (item, path) in enumerate(zip(downloadable_items, local_paths), start=1)
        if not path
    ]
    print(
        json.dumps(
            {
                "ok": True,
                "command": "ecommerce_render_download",
                "done": True,
                "media_urls": res_urls,
                "output_dir": str(output_dir),
                "local_paths": local_paths,
                "download_performed": True,
                "download_failed_count": len(local_save_failed_ids),
                "local_save_failed_count": len(local_save_failed_ids),
                "download_report_failed_count": 0,
                "delivery": _remote_image_delivery(),
                "items": items_list,
                "failed_items": failed_items,
                "summary": {"total": total, "success": done_count, "failed": len(failed_items)},
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    p = argparse.ArgumentParser(description="DesignKit 电商套图 webapi 执行器")
    p.add_argument(
        "command",
        choices=(
            "preview",
            "style_create",
            "style_poll",
            "render_submit",
            "render_regen",
            "render_poll",
            "render_download",
        ),
    )
    p.add_argument("--input-json", required=True, help="JSON 参数字符串")
    args = p.parse_args()
    try:
        inp = json.loads(args.input_json)
    except json.JSONDecodeError as e:
        _json_error(False, "PARAM_ERROR", str(e), "--input-json 必须是合法 JSON")

    if not isinstance(inp, dict):
        _json_error(False, "PARAM_ERROR", "根节点须为 JSON 对象", "")

    if args.command == "preview":
        cmd_preview(inp)
    elif args.command == "style_create":
        cmd_style_create(inp)
    elif args.command == "style_poll":
        cmd_style_poll(inp)
    elif args.command == "render_submit":
        cmd_render_submit(inp)
    elif args.command == "render_regen":
        cmd_render_regen(inp)
    elif args.command == "render_poll":
        cmd_render_poll(inp)
    else:
        cmd_render_download(inp)


if __name__ == "__main__":
    main()
