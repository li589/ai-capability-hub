"""Local SkillPay client and paid-plan application boundary."""

from __future__ import annotations

from http.client import HTTPResponse
import json
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import INTERNAL_DIR, atomic_write_json, normalized
from .orchestrator import run_auto
from .result import make_result
from .skillpay_manifest import build_structure_manifest, validate_structure_manifest


MAX_RESPONSE_BYTES = 1024 * 1024
MAX_PAYMENT_CODE_LENGTH = 4096
REQUEST_ID_PATTERN = re.compile(r"^skillpay_[a-f0-9]{32}$")


def _safe_header_value(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} is missing or too long")
    if "\r" in value or "\n" in value:
        raise ValueError(f"{field} cannot contain line breaks")
    return value


def _safe_out_trade_no(value: object) -> str:
    value = _safe_header_value(value, field="out_trade_no", maximum=32)
    if not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in value):
        raise ValueError("out_trade_no contains unsupported characters")
    return value


def _read_json_response(response: HTTPResponse) -> dict[str, Any]:
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("SkillPay response exceeded 1 MiB")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("SkillPay response must be a JSON object")
    return payload


def validate_plan(plan: object) -> list[str]:
    if not isinstance(plan, dict):
        return ["plan must be a JSON object"]
    required = {
        "schema_version",
        "rules_version",
        "manifest_digest",
        "privacy_mode",
        "generation_engine",
        "model_calls",
        "dashboard_profile",
        "dashboard_sections",
        "execution",
        "billing_unit",
        "plan_id",
        "plan_digest",
    }
    errors: list[str] = []
    if set(plan) != required:
        errors.append("plan fields do not match the supported contract")
    if plan.get("schema_version") != 1:
        errors.append("unsupported plan schema version")
    if plan.get("privacy_mode") != "structure-only":
        errors.append("plan privacy mode must be structure-only")
    if plan.get("generation_engine") != "deterministic-rules" or plan.get("model_calls") != 0:
        errors.append("the initial paid plan must use the zero-model deterministic engine")
    if plan.get("billing_unit") != "one-workspace-plan":
        errors.append("unsupported billing unit")
    if not isinstance(plan.get("dashboard_sections"), list) or not all(
        isinstance(value, str) for value in plan.get("dashboard_sections", [])
    ):
        errors.append("dashboard sections must be a string list")
    execution = plan.get("execution")
    if not isinstance(execution, dict):
        errors.append("plan execution settings are missing")
    else:
        if execution.get("mode") not in {"markdown", "obsidian"}:
            errors.append("plan execution mode is invalid")
        if execution.get("privacy_mode") != "metadata-only":
            errors.append("local execution must remain metadata-only")
        if execution.get("update_mode") != "manual":
            errors.append("initial paid plan only supports manual updates")
        if execution.get("max_vault_depth") != 3:
            errors.append("initial paid plan max vault depth is invalid")
    for key in ("manifest_digest", "plan_digest"):
        value = plan.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            errors.append(f"{key} must be a lowercase SHA-256 hex digest")
    if not isinstance(plan.get("plan_id"), str) or not plan.get("plan_id", "").startswith("plan_"):
        errors.append("plan_id is invalid")
    return errors


def _validated_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("SkillPay endpoint cannot contain credentials or a fragment")
    if parsed.scheme == "https" and parsed.netloc:
        return endpoint
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return endpoint
    raise ValueError("SkillPay endpoint must use HTTPS; HTTP is allowed only for loopback development")


def request_paid_plan(
    *,
    endpoint: str,
    manifest: dict[str, Any],
    out_trade_no: str | None,
    payment_code: str | None,
    request_id: str | None = None,
    upload_confirmed: bool,
    timeout_seconds: float = 15.0,
) -> tuple[dict[str, Any], int]:
    """Perform one official Agent Pay request; never retries or weakens TLS.

    The first request has no merchant order number. The merchant service returns
    HTTP 402 with ``X-Out-Trade-No`` and ``WeixinPay-Required``. After payment,
    callers retry once with those values in headers while keeping the JSON body
    byte-for-byte identical.
    """

    if not upload_confirmed:
        return make_result(
            status="needs_user_input",
            code="STRUCTURE_UPLOAD_CONFIRMATION_REQUIRED",
            message="User confirmation is required before sending the aggregate structural manifest.",
            needs_user_input=[
                {
                    "gate": "external_structure_upload",
                    "requested_action": "review_manifest_summary_and_confirm_one_upload",
                }
            ],
        ), 3
    manifest_errors = validate_structure_manifest(manifest)
    if manifest_errors:
        return make_result(
            status="error",
            code="MANIFEST_INVALID",
            message="; ".join(manifest_errors),
        ), 2
    try:
        endpoint = _validated_endpoint(endpoint)
    except ValueError as exc:
        return make_result(status="error", code="ENDPOINT_INVALID", message=str(exc)), 2
    if request_id is not None and not REQUEST_ID_PATTERN.fullmatch(request_id):
        return make_result(
            status="error",
            code="SKILLPAY_REQUEST_ID_INVALID",
            message="The SkillPay request id is invalid.",
        ), 2
    body = json.dumps(
        {"schema_version": 1, "manifest": manifest},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    try:
        if request_id is not None:
            headers["Idempotency-Key"] = request_id
            headers["X-SkillPay-Request-Id"] = request_id
        if out_trade_no is not None:
            headers["X-Out-Trade-No"] = _safe_out_trade_no(out_trade_no)
        if payment_code is not None:
            headers["WeixinPay-Required"] = _safe_header_value(
                payment_code,
                field="payment_code",
                maximum=MAX_PAYMENT_CODE_LENGTH,
            )
    except ValueError as exc:
        return make_result(status="error", code="PAYMENT_RETRY_INVALID", message=str(exc)), 2
    request = Request(
        endpoint,
        data=body,
        method="POST",
        headers=headers,
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - endpoint is validated above
            payload = _read_json_response(response)
    except HTTPError as exc:
        if exc.code == 402:
            try:
                payment = _read_json_response(exc)
                remote_code = payment.get("code")
                if remote_code == "NOT_PAID":
                    response_order = _safe_out_trade_no(
                        exc.headers.get("X-Out-Trade-No")
                        or payment.get("out_trade_no")
                        or out_trade_no
                    )
                    return make_result(
                        status="needs_user_input",
                        code="NOT_PAID",
                        message=str(payment.get("message") or "Payment is not confirmed yet."),
                        needs_user_input=[
                            {
                                "gate": "agent_pay_confirmation",
                                "requested_action": "verify_same_order_payment_status_before_one_manual_retry",
                            }
                        ],
                        data={
                            "request_id": request_id,
                            "out_trade_no": response_order,
                            "trade_state": payment.get("trade_state"),
                            "automatic_retry_allowed": False,
                        },
                    ), 3
                response_order = _safe_out_trade_no(
                    exc.headers.get("X-Out-Trade-No") or payment.get("out_trade_no")
                )
                response_payment_code = _safe_header_value(
                    exc.headers.get("WeixinPay-Required")
                    or (payment.get("WeixinPay") or {}).get("WeixinPay-Required"),
                    field="payment_code",
                    maximum=MAX_PAYMENT_CODE_LENGTH,
                )
                response_request_id = (
                    exc.headers.get("X-SkillPay-Request-Id") or payment.get("request_id")
                )
                if (
                    request_id is not None
                    and response_request_id is not None
                    and response_request_id != request_id
                ):
                    raise ValueError("HTTP 402 response request id mismatch")
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError):
                return make_result(
                    status="error",
                    code="PAYMENT_RESPONSE_INVALID",
                    message="HTTP 402 response did not contain valid Agent Pay headers.",
                ), 1
            return make_result(
                status="needs_user_input",
                code="PAYMENT_REQUIRED",
                message="The paid service requested Agent Pay authorization.",
                needs_user_input=[
                    {
                        "gate": "agent_pay",
                        "requested_action": "present_platform_payment_authorization_then_retry_same_order_once",
                    }
                ],
                data={
                    "request_id": request_id,
                    "out_trade_no": response_order,
                    "payment_code": response_payment_code,
                    "payment": payment,
                },
            ), 3
        return make_result(
            status="error",
            code="SERVICE_HTTP_ERROR",
            message=f"SkillPay service returned HTTP {exc.code}.",
            data={"request_id": request_id, "out_trade_no": out_trade_no},
        ), 1
    except (OSError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return make_result(
            status="error",
            code="PAYMENT_REQUEST_OUTCOME_UNKNOWN",
            message=str(exc),
            data={
                "request_id": request_id,
                "out_trade_no": out_trade_no,
                "automatic_retry_allowed": False,
                "payment_outcome_must_be_checked_before_retry": True,
            },
        ), 1

    plan = payload.get("plan")
    plan_errors = validate_plan(plan)
    if payload.get("code") != "PLAN_READY" or plan_errors:
        return make_result(
            status="error",
            code="SERVICE_RESPONSE_INVALID",
            message="; ".join(plan_errors) or "service did not return PLAN_READY",
            data={"request_id": request_id, "out_trade_no": out_trade_no},
        ), 1
    return make_result(
        status="ok",
        code="PLAN_READY",
        message="The paid workspace plan was delivered and validated.",
        data={
            "request_id": request_id,
            "out_trade_no": out_trade_no or payload.get("out_trade_no"),
            "fulfillment_id": payload.get("fulfillment_id"),
            "plan": plan,
        },
    ), 0


def apply_paid_plan(
    *,
    workspace: Path,
    source: Path,
    plan: dict[str, Any],
    validated_host: str,
) -> tuple[dict[str, Any], int]:
    """Bind a delivered plan to the current source structure and build locally."""

    plan_errors = validate_plan(plan)
    if plan_errors:
        return make_result(status="error", code="PLAN_INVALID", message="; ".join(plan_errors)), 2
    current_manifest = build_structure_manifest(source)
    if current_manifest["manifest_digest"] != plan["manifest_digest"]:
        return make_result(
            status="error",
            code="PLAN_SOURCE_MISMATCH",
            message="The local source structure changed after this paid plan was generated.",
            next_actions=[
                {
                    "action": "create_new_structure_manifest_before_requesting_another_plan",
                    "additional_charge_required": "depends_on_platform_refund_or_retry_policy",
                }
            ],
            data={"plan_id": plan["plan_id"]},
        ), 2

    execution = plan["execution"]
    payload, exit_code = run_auto(
        workspace=workspace,
        sources=[source],
        requested_config=None,
        mode=str(execution["mode"]),
        privacy_mode="metadata-only",
        preferred_port=8765,
        max_vault_depth=int(execution["max_vault_depth"]),
        resume=False,
        validated_host=validated_host,
    )
    if exit_code != 0:
        return payload, exit_code

    workspace = normalized(workspace)
    receipt_path = workspace / INTERNAL_DIR / "skillpay-plan.json"
    atomic_write_json(receipt_path, plan)
    return make_result(
        status="ok",
        code="SKILLPAY_APPLIED",
        message="The paid plan was bound to the local source and the HTML workbench was generated.",
        artifacts=[*payload.get("artifacts", []), str(receipt_path)],
        next_actions=payload.get("next_actions", []),
        data={
            "plan_id": plan["plan_id"],
            "manifest_digest": plan["manifest_digest"],
            "dashboard_profile": plan["dashboard_profile"],
            "local_run_code": payload["code"],
            "privacy_mode": "metadata-only",
            "source_files_changed": False,
            "model_calls": 0,
        },
    ), 0
