#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Midu 智能校对工具

调用接口对文本进行校对，直接以 Markdown 展示校对结果，并提供下载链接（不落盘下载）。
用 requests 直连（TLS 证书默认校验），不禁用校验、不绕代理。
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests


API_URL = "https://api.midu.com/ability/skill/jdt/proof/read"
KEY_ENV = "MIDU_APP_SECRET"
GET_KEY_URL = "https://ai.mdata.net"


class MiduProofreadError(RuntimeError):
    pass


def load_api_key(explicit_key: Optional[str] = None) -> str:
    """读取鉴权 token。优先级：显式 --api-key 参数 > 环境变量 MIDU_APP_SECRET。"""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    v = os.environ.get(KEY_ENV, "").strip()
    if v:
        return v

    raise MiduProofreadError(
        f"未设置环境变量 {KEY_ENV}。请前往蜜度官网 {GET_KEY_URL} 注册并获取 Key，"
        f"然后配置环境变量：export {KEY_ENV}=<你的 Key>"
    )


@dataclass(frozen=True)
class ProofreadUrls:
    proof_json_url: str
    erratum_excel_url: str
    erratum_md_url: str
    transaction_id: str
    char_count: Optional[int]


@dataclass(frozen=True)
class ProofreadOutputs:
    urls: ProofreadUrls
    erratum_md: str


def call_proofread_api(
    proof_text: str,
    api_key: str,
    file_name: Optional[str] = None,
) -> ProofreadUrls:
    headers = {
        "Content-Type": "application/json",
        "X-Skill-Code": "JDT_PROOF",
        "Authorization": f"Bearer {api_key}",
    }
    params: Dict[str, Any] = {"proofText": proof_text}
    if file_name and file_name.strip():
        params["fileName"] = os.path.basename(file_name.strip())

    try:
        resp = requests.post(API_URL, json=params, headers=headers, timeout=60)
    except requests.RequestException as exc:
        raise MiduProofreadError(f"网络请求失败：{exc}") from exc

    if resp.status_code in (401, 403):
        raise MiduProofreadError(
            f"鉴权失败或 token 无效（HTTP {resp.status_code}）。请前往 {GET_KEY_URL} 重新获取 Key，"
            f"并配置到环境变量 {KEY_ENV}。"
        )
    if not resp.ok:
        raise MiduProofreadError(f"接口 HTTP 错误: {resp.status_code} {resp.text}".strip())

    try:
        data_all = resp.json()
    except ValueError as exc:
        raise MiduProofreadError(f"响应不是合法 JSON：{resp.text}") from exc

    code = data_all.get("code")
    msg = data_all.get("msg", "")
    txid = data_all.get("transactionId", "")
    char_count = data_all.get("charCount")
    if str(code).strip() != "0000":
        raise MiduProofreadError(
            f"接口调用失败: code={code}, msg={msg}" + (f", transactionId={txid}" if txid else "")
        )

    data = data_all.get("data") or {}
    proof_json_url = data.get("proofResultJsonUrl")
    excel_url = data.get("erratumExcelUrl")
    md_url = data.get("erratumMdUrl")
    if not (proof_json_url and excel_url and md_url):
        raise MiduProofreadError(f"响应缺少必要 URL 字段: {data_all}")

    return ProofreadUrls(
        proof_json_url=str(proof_json_url),
        erratum_excel_url=str(excel_url),
        erratum_md_url=str(md_url),
        transaction_id=str(txid),
        char_count=int(char_count) if isinstance(char_count, (int, float)) else None,
    )


def proofread_text(
    proof_text: str,
    api_key: Optional[str] = None,
    file_name: Optional[str] = None,
) -> ProofreadOutputs:
    if not proof_text.strip():
        raise MiduProofreadError("proofText 不能为空。")

    key = load_api_key(api_key)
    urls = call_proofread_api(proof_text=proof_text, api_key=key, file_name=file_name)

    try:
        resp = requests.get(urls.erratum_md_url, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MiduProofreadError(f"读取勘误 Markdown 失败：{exc}") from exc

    return ProofreadOutputs(urls=urls, erratum_md=resp.content.decode("utf-8", errors="replace"))


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Midu 智能校对：调用接口并展示 Markdown（不落盘下载）")
    p.add_argument("--text", required=True, help="待校对文本（直接传入）")
    p.add_argument(
        "--file-name",
        dest="file_name",
        default=None,
        help="来源文件名（仅 basename，可选）；当正文来自图片/PDF/Word 等文件抽取时建议传入",
    )
    p.add_argument("--api-key", dest="api_key", default=None, help="鉴权 token（覆盖环境变量/文件）")
    return p


def main(argv: Optional[Tuple[str, ...]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)

    try:
        outputs = proofread_text(args.text, api_key=args.api_key, file_name=args.file_name)

        print("✅ 校对完成")
        print(f"- transactionId: {outputs.urls.transaction_id}")
        if outputs.urls.char_count is not None:
            print(f"- charCount: {outputs.urls.char_count}")
        print("\n## 勘误 Markdown\n")
        print(outputs.erratum_md.rstrip())
        print("\n## 下载链接\n")
        print(f"- 校对结果 JSON: {outputs.urls.proof_json_url}")
        print(f"- 勘误表 Excel: {outputs.urls.erratum_excel_url}")
        print(f"- 勘误 Markdown: {outputs.urls.erratum_md_url}")
        return 0
    except MiduProofreadError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
