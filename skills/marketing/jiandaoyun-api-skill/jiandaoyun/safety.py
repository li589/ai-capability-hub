"""Deterministic confirmation tokens and risk gates."""

import hashlib
import json

from .errors import JiandaoyunError


def confirmation_token(operation, params):
    canonical = json.dumps(
        {"operation": operation, "params": params},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"jdy-confirm-{digest}"


def require_confirmation(schema, params, supplied_token, acknowledge_destructive=False):
    expected = confirmation_token(schema["name"], params)
    if supplied_token != expected:
        raise JiandaoyunError(
            "confirmation_required",
            "确认令牌缺失或与当前操作参数不匹配。请先运行预览并使用返回的令牌。",
        )
    if schema["risk"] == "destructive" and not acknowledge_destructive:
        raise JiandaoyunError(
            "destructive_acknowledgement_required",
            "这是破坏性操作；还必须显式传入 --acknowledge-destructive。",
        )


def preview(schema, params):
    return {
        "status": "preview",
        "operation": schema["name"],
        "display_name": schema.get("display_name"),
        "risk": schema["risk"],
        "params": params,
        "confirmation_token": confirmation_token(schema["name"], params),
        "next_step": (
            "核对目标和参数后，使用相同输入并追加 --execute "
            "--confirm-token <confirmation_token>。"
        ),
    }
