"""CLI for the local half of the SkillHub Pay workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

from .config import atomic_write_json, load_json
from .result import make_result, render_result
from .skillpay_client import (
    REQUEST_ID_PATTERN,
    apply_paid_plan,
    request_paid_plan,
    validate_plan,
)
from .skillpay_manifest import build_structure_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workbench-skillpay")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--source", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.add_argument("--confirm-structure-only", action="store_true")

    request = sub.add_parser("request-plan")
    request.add_argument("--manifest", type=Path, required=True)
    request.add_argument("--endpoint", required=True)
    request.add_argument("--state", type=Path, required=True)
    request.add_argument("--out-trade-no")
    request.add_argument("--payment-code")
    request.add_argument("--output", type=Path)
    request.add_argument("--confirm-structure-upload", action="store_true")

    apply = sub.add_parser("apply-plan")
    apply.add_argument("--workspace", type=Path, required=True)
    apply.add_argument("--source", type=Path, required=True)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--validated-host", required=True)
    return parser


def _request_plan(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    manifest = load_json(args.manifest)
    manifest_digest = manifest.get("manifest_digest")
    paid_retry = args.out_trade_no is not None or args.payment_code is not None
    if (args.out_trade_no is None) != (args.payment_code is None):
        return make_result(
            status="error",
            code="PAYMENT_RETRY_INCOMPLETE",
            message="Both out_trade_no and payment_code are required for the paid retry.",
        ), 2

    if args.output and args.output.is_file():
        plan = load_json(args.output)
        errors = validate_plan(plan)
        if not errors and plan.get("manifest_digest") == manifest_digest:
            return make_result(
                status="ok",
                code="SKILLPAY_PLAN_ALREADY_READY",
                message="A validated local plan already exists; no paid request was made.",
                artifacts=[str(args.output.resolve(strict=False))],
                data={
                    "plan_id": plan["plan_id"],
                    "manifest_digest": manifest_digest,
                    "requests_made": 0,
                },
            ), 0
        return make_result(
            status="error",
            code="SKILLPAY_EXISTING_PLAN_INVALID",
            message="The existing output plan is invalid or belongs to another structure manifest.",
        ), 2

    state: dict[str, object]
    if args.state.is_file():
        state = load_json(args.state)
        request_id = state.get("request_id")
        if (
            state.get("schema_version") != 1
            or not isinstance(request_id, str)
            or not REQUEST_ID_PATTERN.fullmatch(request_id)
        ):
            return make_result(
                status="error",
                code="SKILLPAY_REQUEST_STATE_INVALID",
                message="The local request state is invalid.",
            ), 2
        if state.get("manifest_digest") != manifest_digest:
            return make_result(
                status="error",
                code="SKILLPAY_REQUEST_STATE_MISMATCH",
                message="The request state belongs to another structure manifest.",
            ), 2
        prior_status = state.get("status")
        if prior_status in {
            "in_flight",
            "payment_retry_in_flight",
            "outcome_unknown",
            "review_required",
            "completed",
        }:
            return make_result(
                status="needs_user_input",
                code="SKILLPAY_PREVIOUS_REQUEST_OUTCOME_REVIEW_REQUIRED",
                message="A prior request may have created, charged, or fulfilled an order; reconcile it before any retry.",
                artifacts=[str(args.state.resolve(strict=False))],
                needs_user_input=[
                    {
                        "gate": "possible_duplicate_skillpay_order",
                        "requested_action": "review_same_request_order_and_payment_records_before_manual_retry",
                    }
                ],
                data={
                    "request_id": request_id,
                    "prior_status": prior_status,
                    "out_trade_no": state.get("out_trade_no"),
                    "requests_made": 0,
                    "automatic_retry_allowed": False,
                },
            ), 3
        if prior_status == "payment_required":
            if not paid_retry:
                return make_result(
                    status="needs_user_input",
                    code="SKILLPAY_PAYMENT_AUTHORIZATION_REQUIRED",
                    message="Use the saved payment response for this order; no new request was made.",
                    artifacts=[str(args.state.resolve(strict=False))],
                    data={
                        "request_id": request_id,
                        "out_trade_no": state.get("out_trade_no"),
                        "requests_made": 0,
                        "automatic_retry_allowed": False,
                    },
                ), 3
            if state.get("out_trade_no") != args.out_trade_no:
                return make_result(
                    status="error",
                    code="SKILLPAY_ORDER_STATE_MISMATCH",
                    message="The paid retry order does not match the saved request state.",
                ), 2
        elif paid_retry:
            return make_result(
                status="error",
                code="SKILLPAY_PAYMENT_STATE_REQUIRED",
                message="A saved PAYMENT_REQUIRED state is required before the paid retry.",
            ), 2
    else:
        if paid_retry:
            return make_result(
                status="error",
                code="SKILLPAY_PAYMENT_STATE_REQUIRED",
                message="The original request state is required before the paid retry.",
            ), 2
        state = {
            "schema_version": 1,
            "request_id": "skillpay_" + uuid.uuid4().hex,
            "manifest_digest": manifest_digest,
            "status": "prepared",
            "structure_upload_confirmed": False,
        }
        atomic_write_json(args.state, state)

    if not args.confirm_structure_upload:
        return make_result(
            status="needs_user_input",
            code="STRUCTURE_UPLOAD_CONFIRMATION_REQUIRED",
            message="Review the structure summary and confirm exactly one upload request.",
            artifacts=[str(args.state.resolve(strict=False))],
            needs_user_input=[
                {
                    "gate": "external_structure_upload",
                    "requested_action": "review_manifest_summary_and_confirm_one_upload",
                }
            ],
            data={
                "request_id": state["request_id"],
                "manifest_digest": manifest_digest,
                "requests_made": 0,
            },
        ), 3

    state = {
        **state,
        "status": "payment_retry_in_flight" if paid_retry else "in_flight",
        "structure_upload_confirmed": True,
    }
    atomic_write_json(args.state, state)
    payload, exit_code = request_paid_plan(
        endpoint=args.endpoint,
        manifest=manifest,
        out_trade_no=args.out_trade_no,
        payment_code=args.payment_code,
        request_id=str(state["request_id"]),
        upload_confirmed=True,
    )

    if payload.get("code") in {"PAYMENT_REQUIRED", "NOT_PAID"}:
        response_order = payload.get("data", {}).get("out_trade_no")
        state = {
            **state,
            "status": "payment_required",
            "out_trade_no": response_order or state.get("out_trade_no"),
            "last_code": payload.get("code"),
        }
        atomic_write_json(args.state, state)
        payload.setdefault("artifacts", []).append(str(args.state.resolve(strict=False)))
        payload["data"] = {
            **payload.get("data", {}),
            "automatic_retry_allowed": False,
            "request_state": str(args.state.resolve(strict=False)),
        }
        return payload, exit_code

    if exit_code == 0:
        if args.output is None:
            atomic_write_json(
                args.state,
                {**state, "status": "review_required", "last_code": "PLAN_OUTPUT_REQUIRED"},
            )
            return make_result(
                status="error",
                code="PLAN_OUTPUT_REQUIRED",
                message="A local output path is required to persist the delivered plan safely.",
            ), 2
        atomic_write_json(args.output, payload["data"]["plan"])
        state = {
            **state,
            "status": "completed",
            "out_trade_no": payload["data"].get("out_trade_no") or state.get("out_trade_no"),
            "fulfillment_id": payload["data"].get("fulfillment_id"),
            "plan_id": payload["data"]["plan"]["plan_id"],
        }
        atomic_write_json(args.state, state)
        payload["artifacts"].extend(
            [
                str(args.output.resolve(strict=False)),
                str(args.state.resolve(strict=False)),
            ]
        )
        return payload, exit_code

    next_status = (
        "outcome_unknown"
        if payload.get("code") == "PAYMENT_REQUEST_OUTCOME_UNKNOWN"
        else "review_required"
    )
    atomic_write_json(
        args.state,
        {
            **state,
            "status": next_status,
            "last_code": payload.get("code"),
        },
    )
    payload["data"] = {
        **payload.get("data", {}),
        "automatic_retry_allowed": False,
        "request_state": str(args.state.resolve(strict=False)),
    }
    return payload, exit_code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest":
        if not args.confirm_structure_only:
            payload, exit_code = make_result(
                status="needs_user_input",
                code="STRUCTURE_MANIFEST_CONFIRMATION_REQUIRED",
                message="Confirm structure-only local analysis before creating the upload candidate.",
                needs_user_input=[
                    {
                        "gate": "local_structure_analysis",
                        "requested_action": "confirm_structure_only_manifest_creation",
                    }
                ],
            ), 3
        else:
            manifest = build_structure_manifest(args.source)
            atomic_write_json(args.output, manifest)
            payload, exit_code = make_result(
                status="ok",
                code="STRUCTURE_MANIFEST_READY",
                message="A local aggregate-only manifest was created; it has not been uploaded.",
                artifacts=[str(args.output.resolve(strict=False))],
                next_actions=[{"action": "review_manifest_before_any_upload"}],
                data={
                    "manifest_digest": manifest["manifest_digest"],
                    "counts": manifest["counts"],
                    "privacy_mode": manifest["privacy_mode"],
                    "uploaded": False,
                },
            ), 0
    elif args.command == "request-plan":
        payload, exit_code = _request_plan(args)
    elif args.command == "apply-plan":
        payload, exit_code = apply_paid_plan(
            workspace=args.workspace,
            source=args.source,
            plan=load_json(args.plan),
            validated_host=args.validated_host,
        )
    else:  # pragma: no cover
        raise AssertionError(f"Unhandled command: {args.command}")

    sys.stdout.write(render_result(payload) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
