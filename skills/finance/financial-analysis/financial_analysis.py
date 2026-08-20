#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

import requests


# --- 配置 ---

def _load_config_file() -> dict:
    config_path = Path.home() / ".htsc-skills" / "config"
    if not config_path.exists():
        return {}
    result = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


class Config:
    def __init__(self) -> None:
        _file_cfg = _load_config_file()
        self.service_url = os.environ.get("FINANCIAL_ANALYSIS_SERVICE_URL", "https://ai.zhangle.com")
        self.api_key = os.environ.get("HT_APIKEY") or _file_cfg.get("HT_APIKEY", "")
        self.base_url = os.environ.get("FINANCIAL_ANALYSIS_BASE_URL", "/edge/entry/gate")
        self.timeout = float(os.environ.get("FINANCIAL_ANALYSIS_TIMEOUT", "600"))


_config: Optional[Config] = None


def _get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


# --- HTTP 客户端 ---

def _error(code: int, message: str, category: str, retriable: bool = False, hint: str = "") -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "category": category,
            "retriable": retriable,
            "hint": hint,
        },
    }


def _category_from_code(code: int) -> str:
    if code == -3:
        return "network"
    if code in (-2, -5):
        return "business"
    return "validation"


def _post(path: str, body: Optional[dict] = None, timeout: Optional[float] = None) -> dict:
    cfg = _get_config()
    url = cfg.service_url.rstrip("/") + cfg.base_url + path
    timeout_s = timeout if timeout is not None else cfg.timeout
    headers = {
        "apiKey": cfg.api_key,
        "skillCode": "mx_1779096185749",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, json=body or {}, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.Timeout:
        return _error(-3, "接口调用超时", "network", retriable=True, hint="后端响应较慢，请稍后再试。")
    except requests.exceptions.ConnectionError:
        return _error(
            -3, "无法连接到后端服务", "network", retriable=True,
            hint=f"请检查 FINANCIAL_ANALYSIS_SERVICE_URL（当前 {cfg.service_url}）是否正确，以及后端服务是否启动。",
        )
    except requests.exceptions.HTTPError as e:
        return _error(-2, f"后端返回异常状态码 {e.response.status_code}", "network", retriable=True)
    except json.JSONDecodeError:
        return _error(-2, "后端返回内容无法解析", "business", hint="请检查后端版本是否匹配。")
    except Exception as e:
        return _error(-3, f"未知网络错误：{e}", "network", retriable=True)

    if result.get("code") != 0:
        code = result.get("code", -2)
        msg = result.get("message", "未知错误")
        detail = result.get("detail", "")
        category = _category_from_code(code)
        return _error(code, msg, category, hint=detail)

    answer = result.get("data", {}).get("answer", "")
    return {"ok": True, "data": {"answer": answer}, "error": None}

def diagnosisStock(query: str) -> dict:
    """对个股、ETF、板块等进行分析诊断。

    Args:
        query: 用户问题
    """
    return _post("/api/finAnalysis/diagnosisStock", {"query": query}, timeout=360)


def marketInsight(query: str) -> dict:
    """市场洞察，覆盖个股分析、大盘分析、板块/行业分析、多标的对比、金融资讯等。

    Args:
        query: 用户问题
    """
    return _post("/api/finAnalysis/marketInsight", {"query": query}, timeout=360)


# --- CLI ---

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="financial_analysis", description="金融分析与资讯查询工具调度入口")
    sub = p.add_subparsers(dest="tool", required=True, metavar="<tool>")

    s = sub.add_parser("diagnosisStock", help="分析诊断")
    s.add_argument("--query", required=True, help="用户问题")

    s = sub.add_parser("marketInsight", help="市场洞察")
    s.add_argument("--query", required=True, help="用户问题")

    return p


def main() -> None:
    args = _build_parser().parse_args()

    if args.tool == "diagnosisStock":
        result = diagnosisStock(query=args.query)
    elif args.tool == "marketInsight":
        result = marketInsight(query=args.query)
    else:
        raise SystemExit(f"unknown tool: {args.tool}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
