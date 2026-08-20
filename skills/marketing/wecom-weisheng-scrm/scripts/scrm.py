#!/usr/bin/env python3
"""scrm.py - SCRM Skill CLI 主入口。

基于 wshoto-open 开放平台 Claw 模块，动态发现并调用可用业务接口。
所有业务接口通过通用代理 /claw/proxy/forward 调用，不在 Skill 中硬编码。

@author jzc
@date 2026-04-02 17:11
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from pathlib import Path

_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from utils import ApiError, ConfigError, SCRMError, ValidationError, CallApiError, ERROR_DOC_READ_REQUIRED, ERROR_DOC_VALIDATION_REQUIRED, ERROR_PATH_PARAM_MISSING, ERROR_AUTH_ERROR, ERROR_NETWORK_ERROR, ERROR_SERVER_ERROR, ERROR_BUSINESS_ERROR, force_utf8_output, output_error, output_success
from environment import run_check_env
from api_client import SCRMClient
from get_access_token import TokenManager
from identity_manager import IdentityManager
from claw_client import ClawClient
from file_utils import upload_image
from raw_fetcher import fetch_raw_text
from robot_app_key import get_or_create_app_key
import doc_inspector
import doc_read_tracker
import param_validator

force_utf8_output()


# ---------------------------------------------------------------------------
# 命令处理函数
# ---------------------------------------------------------------------------

def cmd_check_env(args, client=None):
    """检查运行环境。"""
    return run_check_env()


def persist_app_key(app_key: str) -> dict:
    """将 SCRM_APP_KEY 持久化写入用户环境（跨平台），并在当前进程立即生效。

    - Windows：调用 setx 写入用户级注册表环境变量
    - Unix/macOS：写入 shell profile（.zshrc / .bashrc / .profile）

    Args:
        app_key: 待持久化的 APP KEY（调用方需保证已 strip 且非空）

    Returns:
        描述写入结果的字典（platform / action / note 等）。
    """
    import platform

    system = platform.system()

    if system == "Windows":
        import subprocess
        subprocess.run(
            ["setx", "SCRM_APP_KEY", app_key],
            capture_output=True, text=True,
        )
        os.environ["SCRM_APP_KEY"] = app_key
        return {
            "platform": "Windows",
            "action": "setx",
            "note": "已通过 setx 写入用户环境变量，重新打开终端后生效",
        }

    # Unix/macOS：写入 shell profile
    home = os.path.expanduser("~")
    shell = os.environ.get("SHELL", "")
    candidates = []
    if "zsh" in shell:
        candidates = [os.path.join(home, ".zshrc"), os.path.join(home, ".zprofile")]
    elif "bash" in shell:
        candidates = [os.path.join(home, ".bashrc"), os.path.join(home, ".bash_profile")]
    candidates.append(os.path.join(home, ".profile"))

    target = next((f for f in candidates if os.path.exists(f)), candidates[0])

    export_line = f"export SCRM_APP_KEY='{app_key}'"
    export_pattern = re.compile(r"^export\s+SCRM_APP_KEY=.*$", re.MULTILINE)

    existing = ""
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            existing = f.read()

    if export_pattern.search(existing):
        new_content = export_pattern.sub(export_line, existing)
        action_taken = "updated"
    else:
        new_content = existing.rstrip("\n") + f"\n\n# SCRM Skill 凭证\n{export_line}\n"
        action_taken = "appended"

    with open(target, "w", encoding="utf-8") as f:
        f.write(new_content)

    os.environ["SCRM_APP_KEY"] = app_key

    return {
        "platform": system,
        "profile": target,
        "action": action_taken,
        "note": f"已写入 {target}，重新打开终端后生效",
    }


def cmd_set_app_key(args, client=None):
    """将 SCRM_APP_KEY 持久化写入用户环境（跨平台）。"""
    app_key = args.app_key_value.strip()
    if not app_key:
        raise ValueError("APP_KEY 不能为空")

    return persist_app_key(app_key)


def _get_bot_id_from_openclaw() -> str | None:
    """从 openclaw 配置中读取当前机器人 ID（channels.wecom.botId）。

    优先执行：openclaw config get channels.wecom.botId
    失败时回退：直接解析 ~/.openclaw/openclaw.json
    """
    import subprocess
    try:
        result = subprocess.run(
            ["openclaw", "config", "get", "channels.wecom.botId"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
            if value:
                return value
    except (OSError, subprocess.TimeoutExpired):
        pass

    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("channels", {}).get("wecom", {}).get("botId") or None
    except (OSError, json.JSONDecodeError):
        pass

    return None


def cmd_get_bot_id(args, client=None):
    """从 openclaw 配置文件读取当前机器人 ID（channels.wecom.botId）。"""
    bot_id = _get_bot_id_from_openclaw()
    if not bot_id:
        raise ConfigError(
            "无法从 openclaw 配置中读取 botId，"
            "请确认 openclaw CLI 已安装且 channels.wecom.botId 已配置"
        )
    return {"bot_id": bot_id, "source": "openclaw config channels.wecom.botId"}


def cmd_debug_context(args, client=None):
    """调试专用：仅输出 bot_id 和 operator_userid，不调用任何 SCRM 接口。"""
    userid = (args.operator_userid or "").strip()
    if not userid:
        raise ValidationError("--operator-userid 不能为空（请传入 OpenClaw 消息上下文的 sender_id）")

    bot_id = (args.bot_id or "").strip()
    bot_id_source = "parameter"
    if not bot_id:
        bot_id = _get_bot_id_from_openclaw() or ""
        bot_id_source = "openclaw_config"
    if not bot_id:
        raise ConfigError(
            "无法确定 bot_id：请通过 --bot-id 参数提供，"
            "或确认 ~/.openclaw/openclaw.json 中 channels.wecom.botId 已配置"
        )

    return {
        "debug": True,
        "operator_userid": userid,
        "bot_id": bot_id,
        "bot_id_source": bot_id_source,
        "note": "调试模式：仅验证 ID 获取，未调用任何 SCRM 接口",
    }


def cmd_setup_context(args, client=None):
    """企微机器人场景一键初始化：使用 sender_id + bot_id 直接获取并持久化 SCRM_APP_KEY。

    operator_userid 来源：OpenClaw 框架注入的 sender_id（直接作为参数传入）。
    bot_id 来源：--bot-id 参数（必填）。
    """
    userid = (args.operator_userid or "").strip()
    if not userid:
        raise ValidationError("--operator-userid 不能为空（请传入 OpenClaw 消息上下文的 sender_id）")

    bot_id = (args.bot_id or "").strip()
    if not bot_id:
        raise ValidationError("--bot-id 不能为空（来自 openclaw.json channels.wecom.botId）")

    app_key = get_or_create_app_key(open_user_id=userid, source_botid=bot_id)

    persist_result = persist_app_key(app_key)
    return {
        "sender_id": userid,
        "bot_id": bot_id,
        "scrm_app_key": app_key,
        "persist": persist_result,
        "export_hint": f"export SCRM_APP_KEY='{app_key}'",
        "note": (
            "SCRM_APP_KEY 已获取并持久化。"
            "请执行 export_hint 中的命令使其在当前会话生效。"
        ),
    }


def cmd_check_identity(args, client):
    """获取用户身份信息（超管/分管/员工）。"""
    user_id = client.user_id
    identity_mgr = IdentityManager(client, user_id)
    result = identity_mgr.get_identity()
    return result


def cmd_list_apis(args, client):
    """从接口仓库匹配调用规则。"""
    claw = ClawClient(client)
    result = claw.get_api_list(keyword=args.keyword)
    return result


def _raise_call_api_error_from_api_error(exc: ApiError, doc_url: str, write_operation: bool) -> None:
    """将 ApiError 映射为 call-api 标准错误类型。"""
    # Step 1: 识别 access_token 失效类业务码，避免误判为普通业务错误
    if exc.code in {10001, 10010, 10011}:
        raise CallApiError(
            "access_token 已失效或不可用，请检查当前环境配置并重新获取 token 后再试",
            error_type=ERROR_AUTH_ERROR,
            doc_url=doc_url,
            write_operation=write_operation,
            extra_details={"code": exc.code, "status": exc.status, "response_body": exc.response_body},
        ) from exc

    # Step 2: 处理开放平台或聚合接口未返回 HTTP 状态的异常
    if exc.status is None:
        if exc.code is None:
            raise CallApiError(
                "网络连接失败，请稍后重试",
                error_type=ERROR_NETWORK_ERROR,
                doc_url=doc_url,
                write_operation=write_operation,
            ) from exc
        if exc.code == 3:
            raise CallApiError(
                str(exc),
                error_type=ERROR_SERVER_ERROR,
                doc_url=doc_url,
                write_operation=write_operation,
            ) from exc
        raise CallApiError(
            str(exc),
            error_type=ERROR_BUSINESS_ERROR,
            doc_url=doc_url,
            write_operation=write_operation,
        ) from exc

    # Step 3: 处理带 HTTP 状态码的服务端或业务异常
    if exc.status >= 500:
        raise CallApiError(
            "服务端错误 (HTTP {})，请稍后重试".format(exc.status),
            error_type=ERROR_SERVER_ERROR,
            doc_url=doc_url,
            write_operation=write_operation,
        ) from exc

    raise CallApiError(
        "接口返回业务错误 (HTTP {})".format(exc.status),
        error_type=ERROR_BUSINESS_ERROR,
        doc_url=doc_url,
        write_operation=write_operation,
        extra_details={"code": exc.code, "status": exc.status, "response_body": exc.response_body},
    ) from exc


def _merge_warnings(cached_warnings: list[dict] | None, runtime_warnings: list[dict] | None) -> list[dict]:
    """合并缓存告警和运行时告警，并按内容去重。"""
    # Step 1: 归一化输入，统一转为列表
    normalized_cached = cached_warnings or []
    normalized_runtime = runtime_warnings or []

    # Step 2: 顺序合并并按 JSON 内容去重，优先保留缓存中的原始告警
    merged: list[dict] = []
    seen: set[str] = set()
    for warning in normalized_cached + normalized_runtime:
        warning_key = json.dumps(warning, ensure_ascii=False, sort_keys=True)
        if warning_key in seen:
            continue
        seen.add(warning_key)
        merged.append(warning)
    return merged


def _has_cached_field_input_spec_warning(cached_warnings: list[dict] | None) -> bool:
    """判断缓存中是否已有 FIELD_INPUT_SPEC 相关告警。"""
    # Step 1: 缓存为空时直接返回 False
    if not cached_warnings:
        return False

    # Step 2: 识别提取阶段已经落盘的真实告警，避免运行时再退化为 missing
    for warning in cached_warnings:
        if not isinstance(warning, dict):
            continue
        warning_type = warning.get("type", "")
        if warning_type in {"field_input_spec_missing", "field_input_spec_parse_error", "field_input_spec_invalid"}:
            return True
    return False


def _get_param_section(field_input_spec: dict | None, section_name: str) -> dict[str, dict]:
    """读取 FIELD_INPUT_SPEC 中的指定参数分区。"""
    if not isinstance(field_input_spec, dict):
        return {}
    section = field_input_spec.get(section_name, {})
    return section if isinstance(section, dict) else {}


def _extract_uri_path_param_names(uri: str) -> list[str]:
    """从 URI 模板中提取路径参数名。"""
    return [name for name in re.findall(r"\{([^}]+)\}", uri) if name]


def _split_call_params(raw_params: dict, field_input_spec: dict | None, uri: str) -> dict[str, dict]:
    """按照 FIELD_INPUT_SPEC 将输入参数拆分为 path/query/body 三段。"""
    # Step 1: 获取三个参数分区的定义集合
    path_param_map = _get_param_section(field_input_spec, "path_params")
    query_param_map = _get_param_section(field_input_spec, "query_params")
    field_map = _get_param_section(field_input_spec, "fields")

    # Step 2: 文档缺少可用 spec 时，按 URI 模板回收同名路径参数，保持路径参数接口可调用
    if not path_param_map and not query_param_map and not field_map:
        uri_path_param_names = set(_extract_uri_path_param_names(uri))
        path_params = {key: value for key, value in raw_params.items() if key in uri_path_param_names}
        fields = {key: value for key, value in raw_params.items() if key not in uri_path_param_names}
        return {"path_params": path_params, "query_params": {}, "fields": fields}

    # Step 3: 逐个参数分配到 path/query/body，未命中的保持在 fields 兼容旧文档
    path_params: dict[str, object] = {}
    query_params: dict[str, object] = {}
    fields: dict[str, object] = {}

    for key, value in raw_params.items():
        if key in path_param_map:
            path_params[key] = value
            continue
        if key in query_param_map:
            query_params[key] = value
            continue
        fields[key] = value

    return {"path_params": path_params, "query_params": query_params, "fields": fields}


def _replace_path_params(uri: str, path_params: dict[str, object], doc_url: str, write_operation: bool) -> str:
    """将路径参数替换到 URI 模板中。"""
    # Step 1: 替换已提供的路径参数
    resolved_uri = uri
    for key, value in path_params.items():
        resolved_uri = resolved_uri.replace("{" + key + "}", str(value))

    # Step 2: 检查是否仍有未替换的占位符
    unresolved_names = re.findall(r"\{([^}]+)\}", resolved_uri)
    if unresolved_names:
        raise CallApiError(
            "当前接口缺少路径参数，无法完成 URI 拼接，请重新阅读接口文档后再调用",
            error_type=ERROR_PATH_PARAM_MISSING,
            doc_url=doc_url,
            write_operation=write_operation,
            extra_details={"missing_path_params": unresolved_names},
        )

    return resolved_uri


def _append_query_params(uri: str, query_params: dict[str, object]) -> str:
    """将 query 参数拼接到 URI 上。"""
    # Step 1: 无 query 参数时直接返回原始 URI
    if not query_params:
        return uri

    # Step 2: 展开数组参数，并用标准 query string 形式拼接
    query_items: list[tuple[str, object]] = []
    for key, value in query_params.items():
        if isinstance(value, list):
            for item in value:
                query_items.append((key, item))
            continue
        query_items.append((key, value))

    query_string = urlencode(query_items, doseq=True)
    separator = "&" if "?" in uri else "?"
    return uri + separator + query_string


def _extract_missing_path_params(validation_result: dict | None) -> list[str]:
    """从强校验结果中提取缺失的路径参数名。"""
    if not isinstance(validation_result, dict):
        return []

    path_result = validation_result.get("path_params")
    if not isinstance(path_result, dict):
        return []

    missing_fields = path_result.get("missing_fields")
    if not isinstance(missing_fields, list):
        return []

    return [field for field in missing_fields if isinstance(field, str) and field]


def cmd_call_api(args, client):
    """通过通用代理调用业务接口（文档驱动强门禁）。"""
    doc_url = args.doc_url

    # Step 1: 解析输入参数
    raw_params = json.loads(args.biz_params) if args.biz_params else {}
    if not isinstance(raw_params, dict):
        raise ValidationError("biz_params 必须是 JSON 对象，例如 {'currentIndex':1,'pageSize':10}")

    # Step 2: 检查文档已读缓存
    cache_status = doc_read_tracker.check_valid(doc_url)
    if cache_status == "not_found":
        raise CallApiError(
            "当前接口调用前必须先阅读接口文档，请重新执行 fetch-raw-doc --url {} 后再调用".format(doc_url),
            error_type=ERROR_DOC_READ_REQUIRED, doc_url=doc_url,
        )
    if cache_status == "expired":
        raise CallApiError(
            "文档已读缓存已过期，请重新执行 fetch-raw-doc --url {} 后再调用".format(doc_url),
            error_type=ERROR_DOC_READ_REQUIRED, doc_url=doc_url,
        )

    # Step 3: 根据 doc_url 查找接口元数据
    claw = ClawClient(client)
    try:
        api_record = claw.find_api_by_doc_url(doc_url)
    except ApiError as exc:
        _raise_call_api_error_from_api_error(exc, doc_url, False)
    except ValueError as exc:
        raise CallApiError(str(exc), error_type=ERROR_DOC_VALIDATION_REQUIRED, doc_url=doc_url) from exc

    service_name = api_record["category"]
    uri = api_record["api_path"]
    method = (api_record.get("method") or "POST").upper()

    # Step 4: 检测写操作
    write_operation = claw._is_write_operation(uri)
    args._write_operation = write_operation

    # Step 5: 获取缓存的 field_input_spec 并进行参数校验
    cache_record = doc_read_tracker.load(doc_url)
    field_input_spec = cache_record.get("field_input_spec") if cache_record else None
    cached_warnings = cache_record.get("warnings", []) if cache_record else []

    call_params = _split_call_params(raw_params, field_input_spec, uri)

    if field_input_spec is None and _has_cached_field_input_spec_warning(cached_warnings):
        validation_result, runtime_warnings = None, []
    else:
        validation_result, runtime_warnings = param_validator.validate_call_params(call_params, field_input_spec, doc_url)
    warnings = _merge_warnings(cached_warnings, runtime_warnings)

    # Step 6: 强校验失败
    if validation_result is not None:
        missing_path_params = _extract_missing_path_params(validation_result)
        if missing_path_params:
            raise CallApiError(
                "当前接口缺少路径参数，无法完成 URI 拼接，请重新阅读接口文档后再调用",
                error_type=ERROR_PATH_PARAM_MISSING,
                doc_url=doc_url,
                write_operation=write_operation,
                extra_details={"missing_path_params": missing_path_params},
            )

        raise CallApiError(
            "当前请求参数未通过文档校验，请先重新阅读接口文档后再调用",
            error_type=ERROR_DOC_VALIDATION_REQUIRED,
            doc_url=doc_url,
            write_operation=write_operation,
            extra_details=validation_result,
        )

    # Step 7: 组装真实请求参数
    resolved_uri = _replace_path_params(uri, call_params["path_params"], doc_url, write_operation)
    resolved_uri = _append_query_params(resolved_uri, call_params["query_params"])

    # Step 8: 真实接口调用
    try:
        result = claw.forward(service_name=service_name, uri=resolved_uri, method=method, biz_params=call_params["fields"])
    except ApiError as exc:
        _raise_call_api_error_from_api_error(exc, doc_url, write_operation)

    # Step 9: 附加 warnings 到成功响应
    if warnings:
        result["warnings"] = warnings

    return result


def cmd_upload_image(args, client):
    """上传本地图片，返回公网 URL 和 file_id。"""
    path = Path(args.path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValidationError(f"文件不存在：{path}")
    return upload_image(path, client=client)


def cmd_fetch_raw_doc(args, client=None):
    """读取受控远程文档原文，提取 FIELD_INPUT_SPEC 并写入已读缓存。"""
    # Step: 获取远程文档原文
    result = fetch_raw_text(args.url, timeout=args.timeout, max_bytes=args.max_bytes)

    # Step: 从原文中提取 FIELD_INPUT_SPEC
    spec_result = doc_inspector.extract_field_input_spec(result.get("content", ""))
    field_input_spec = spec_result["field_input_spec"]
    warnings = spec_result["warnings"]

    # Step: 将已读状态写入缓存
    cache_record = doc_read_tracker.save(args.url, field_input_spec, warnings)

    # Step: 在返回结果中追加缓存相关信息
    result["field_input_spec"] = field_input_spec
    result["warnings"] = warnings
    result["read_at"] = cache_record["read_at"]
    result["expire_at"] = cache_record["expire_at"]

    return result


def cmd_inspect_api_doc(args, client=None):
    """检查文档缓存状态并返回缓存记录。"""
    doc_url = args.url

    # Step: 检查缓存状态
    status = doc_read_tracker.check_valid(doc_url)

    if status == "not_found":
        raise SCRMError("文档尚未缓存，请先执行 fetch-raw-doc 读取该文档", error_code="doc_not_cached")
    if status == "expired":
        raise SCRMError("文档缓存已过期，请重新执行 fetch-raw-doc 读取该文档", error_code="doc_cache_expired")

    # Step: 缓存有效，返回完整记录
    return doc_read_tracker.load(doc_url)


# ---------------------------------------------------------------------------
# 子命令注册
# ---------------------------------------------------------------------------

def _add_base_subparsers(subparsers) -> None:
    """基础子命令。"""
    p = subparsers.add_parser("check-env", help="检查运行环境")
    p.set_defaults(handler=cmd_check_env, success_message="环境检查通过")

    p = subparsers.add_parser("set-app-key", help="将 SCRM_APP_KEY 持久化写入 shell profile")
    p.add_argument("app_key_value", help="APP_KEY 的值（personal_access_token）")
    p.set_defaults(handler=cmd_set_app_key, success_message="APP_KEY 已持久化")

    p = subparsers.add_parser("fetch-raw-doc", help="读取远程文档原文")
    p.add_argument("--url", required=True, help="目标文档 URL")
    p.add_argument("--timeout", type=int, default=30, help="请求超时时间，默认 30 秒")
    p.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024, help="最大读取字节数，默认 52428800")
    p.set_defaults(handler=cmd_fetch_raw_doc, success_message="远程文档读取成功")

    p = subparsers.add_parser("inspect-api-doc", help="检查文档缓存状态并返回缓存记录")
    p.add_argument("--url", required=True, help="目标文档 URL")
    p.set_defaults(handler=cmd_inspect_api_doc, success_message="文档缓存读取成功")

    # 企微机器人场景：自动初始化 SCRM_APP_KEY（原 wecom-weisheng-robot 能力）
    p = subparsers.add_parser(
        "get-bot-id",
        help="从 openclaw 配置自动读取机器人 ID（channels.wecom.botId）",
    )
    p.set_defaults(handler=cmd_get_bot_id, success_message="bot_id 读取成功")

    p = subparsers.add_parser(
        "debug-context",
        help="【调试专用】仅输出 bot_id 和 sender_id，不调用任何 SCRM 接口",
    )
    _add_argument_aliases(
        p, "--bot-id", default="",
        help="机器人 ID（可选，未提供时自动从 openclaw.json 读取）",
    )
    _add_argument_aliases(
        p, "--operator-userid", required=True,
        help="操作者 userid（来自 OpenClaw 消息上下文的 sender_id）",
    )
    p.set_defaults(handler=cmd_debug_context, success_message="调试信息读取成功")

    p = subparsers.add_parser(
        "setup-context",
        help="企微机器人场景一键初始化：用 sender_id + bot_id 获取并持久化 SCRM_APP_KEY",
    )
    _add_argument_aliases(
        p, "--bot-id", required=True,
        help="企业智能机器人 ID（来自 openclaw.json channels.wecom.botId）",
    )
    _add_argument_aliases(
        p, "--operator-userid", required=True,
        help="操作者 userid（来自 OpenClaw 消息上下文的 sender_id）",
    )
    p.set_defaults(handler=cmd_setup_context, success_message="SCRM 上下文初始化成功")


def _add_claw_subparsers(subparsers) -> None:
    """Claw 动态接口相关子命令。"""
    p = subparsers.add_parser("check-identity", help="获取用户身份（超管/分管/员工）")
    p.set_defaults(handler=cmd_check_identity, success_message="用户身份获取成功")

    p = subparsers.add_parser("list-apis", help="通过关键词从接口仓库匹配调用规则")
    _add_argument_aliases(p, "--keyword", required=True,
                   help="逗号分隔的多个关键词，模糊匹配 api_name")
    p.set_defaults(handler=cmd_list_apis, success_message="接口匹配成功")

    p = subparsers.add_parser("call-api", help="通过通用代理调用业务接口（文档驱动强门禁）")
    _add_argument_aliases(p, "--doc-url", required=True,
                   help="接口文档 URL，必须先通过 fetch-raw-doc 读取过该文档")
    _add_argument_aliases(p, "--biz-params", default=None,
                   help="业务参数 JSON 字符串，如 '{\"currentIndex\":1,\"pageSize\":10}'")
    p.set_defaults(handler=cmd_call_api, success_message="接口调用成功")

    p = subparsers.add_parser("upload-image", help="上传本地图片，返回公网 URL 和 file_id")
    p.add_argument("--path", required=True, help="本地图片文件路径")
    p.set_defaults(handler=cmd_upload_image, success_message="图片上传成功")


def _add_argument_aliases(parser, name, **kwargs):
    """注册一个带连字符的参数，同时支持下划线格式的别名。

    例如 _add_argument_aliases(p, "--service-name", ...) 会同时注册
    --service-name 和 --service_name 作为同一个参数的两个 flag，
    两种写法都能正常使用，required 校验也都能正确生效。
    """
    prefix = "--" if name.startswith("--") else ""
    base = name.lstrip("-")
    alias_base = base.replace("-", "_")
    if alias_base != base:
        parser.add_argument(name, prefix + alias_base, **kwargs)
    else:
        parser.add_argument(name, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="scrm",
        description="SCRM Skill CLI - 基于 Claw 模块动态发现并调用业务接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--app-key", help="覆盖环境变量 SCRM_APP_KEY")
    parser.add_argument("--base-url", default="", help="覆盖环境变量 SCRM_BASE_URL")

    subparsers = parser.add_subparsers(dest="action", metavar="ACTION")
    subparsers.required = True

    _add_base_subparsers(subparsers)
    _add_claw_subparsers(subparsers)

    return parser


def main() -> None:
    """程序入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.app_key:
        os.environ["SCRM_APP_KEY"] = args.app_key
    if args.base_url:
        os.environ["SCRM_BASE_URL"] = args.base_url

    action = args.action
    try:
        # 不需要 client 的命令
        if action in ("check-env", "set-app-key", "fetch-raw-doc", "inspect-api-doc",
                      "setup-context", "get-bot-id", "debug-context"):
            result = args.handler(args)
            output_success(action, result, getattr(args, "success_message", "执行成功"))
            return

        # 需要 client 的命令：先做环境检查（可能从持久化配置恢复 SCRM_APP_KEY 到 os.environ），
        # 再读取 app_key / base_url，避免在恢复前捕获到 None。
        run_check_env()

        app_key = os.getenv("SCRM_APP_KEY")
        base_url = os.getenv("SCRM_BASE_URL", "https://open.wshoto.com")

        token_manager = TokenManager(app_key, base_url=base_url)
        access_token = token_manager.get_token()
        user_id = token_manager.get_user_id()
        client = SCRMClient(access_token, base_url=base_url, user_id=user_id, token_manager=token_manager)

        result = args.handler(args, client)
        output_success(action, result, getattr(args, "success_message", "执行成功"))
    except ValidationError as exc:
        output_error(action, "validation_error", str(exc),
                     details={**exc.details, "write_operation": getattr(args, "_write_operation", False)})
    except CallApiError as exc:
        output_error(action, exc.error_type, str(exc), details=exc.details)
    except ConfigError as exc:
        output_error(action, "config_error", str(exc), details=exc.details)
    except SCRMError as exc:
        output_error(action, exc.error_code or "scrm_error", str(exc),
                     details={**exc.details, "write_operation": getattr(args, "_write_operation", False)})
    except json.JSONDecodeError as exc:
        output_error(action, "json_error", f"JSON 解析失败：{exc}")
    except Exception as exc:
        output_error(action, "unexpected_error", f"执行失败：{exc}",
                     details={"write_operation": getattr(args, "_write_operation", False)})


if __name__ == "__main__":
    main()
