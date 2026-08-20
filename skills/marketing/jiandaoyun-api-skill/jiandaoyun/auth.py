"""Credential discovery and permission-restricted local storage."""

import getpass
import json
import os
from pathlib import Path

from .errors import JiandaoyunError


ENV_NAME = "JIANDAOYUN_API_KEY"
CREDENTIAL_FILE_ENV = "JIANDAOYUN_CREDENTIAL_FILE"


def credential_path():
    configured = os.environ.get(CREDENTIAL_FILE_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "jiandaoyun-agent" / "credentials.json"


def _check_mode(path):
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise JiandaoyunError(
            "unsafe_credentials",
            f"凭据文件权限不安全：{path} 当前为 {mode:03o}，要求 600。",
            retryable=False,
        )


def load_api_key():
    configured = os.environ.get(CREDENTIAL_FILE_ENV, "").strip()
    if configured:
        return _load_key_file(Path(configured).expanduser())

    value = os.environ.get(ENV_NAME, "").strip()
    if value:
        return value, "environment"

    path = credential_path()
    return _load_key_file(path)


def _load_key_file(path):
    if not path.exists():
        raise JiandaoyunError(
            "missing_credentials",
            f"未找到简道云 API Key。请设置 {ENV_NAME}，或运行 jdy configure。",
        )
    _check_mode(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JiandaoyunError(
            "invalid_credentials",
            f"无法读取凭据文件：{path}",
            details=str(exc),
        ) from exc
    value = str(payload.get("api_key", "")).strip()
    if not value:
        raise JiandaoyunError("invalid_credentials", "凭据文件中没有有效的 api_key。")
    return value, str(path)


def save_api_key(api_key):
    value = api_key.strip()
    if not value:
        raise JiandaoyunError("invalid_credentials", "API Key 不能为空。")
    path = credential_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps({"api_key": value}, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def configure_interactively(stdin=None):
    if os.environ.get(ENV_NAME, "").strip() and not os.environ.get(CREDENTIAL_FILE_ENV, "").strip():
        raise JiandaoyunError(
            "credential_source_conflict",
            f"当前进程已设置 {ENV_NAME}；重新配置文件不会覆盖该环境变量。"
            f"请先取消该环境变量，或设置 {CREDENTIAL_FILE_ENV} 指向要更新的凭据文件后重试。",
            retryable=False,
        )
    if stdin is not None:
        value = stdin.read().strip()
    else:
        value = getpass.getpass("请输入简道云 API Key（输入不会显示）: ").strip()
    return save_api_key(value)


def credential_status():
    configured = os.environ.get(CREDENTIAL_FILE_ENV, "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.exists():
            return {
                "configured": False,
                "source": str(path),
                "selected_by": CREDENTIAL_FILE_ENV,
                "safe": False,
            }
        mode = path.stat().st_mode & 0o777
        return {
            "configured": True,
            "source": str(path),
            "selected_by": CREDENTIAL_FILE_ENV,
            "safe": not bool(mode & 0o077),
            "mode": f"{mode:03o}",
        }
    if os.environ.get(ENV_NAME, "").strip():
        return {"configured": True, "source": "environment", "safe": True}
    path = credential_path()
    if not path.exists():
        return {"configured": False, "source": str(path), "safe": False}
    mode = path.stat().st_mode & 0o777
    return {
        "configured": True,
        "source": str(path),
        "safe": not bool(mode & 0o077),
        "mode": f"{mode:03o}",
    }
