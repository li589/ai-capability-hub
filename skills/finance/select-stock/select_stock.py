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
        self.service_url = os.environ.get("SELECT_STOCK_SERVICE_URL", "https://ai.zhangle.com")
        self.api_key = os.environ.get("HT_APIKEY") or _file_cfg.get("HT_APIKEY", "")
        self.base_url = os.environ.get("SELECT_STOCK_BASE_URL", "/edge/entry/gate")
        self.timeout = float(os.environ.get("SELECT_STOCK_TIMEOUT_SEC", "300"))


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
        "skillCode": "mx_select-stock",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, json=body or {}, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.Timeout:
        return _error(-3, "接口调用超时", "network", retriable=True, hint="选股接口耗时较长，请稍后再试。")
    except requests.exceptions.ConnectionError:
        return _error(
            -3, "无法连接到后端服务", "network", retriable=True,
            hint=f"请检查 SELECT_STOCK_SERVICE_URL（当前 {cfg.service_url}）是否正确，以及后端服务是否启动。",
        )
    except requests.exceptions.HTTPError as e:
        return _error(-2, f"后端返回异常状态码 {e.response.status_code}", "network", retriable=True)
    except json.JSONDecodeError:
        return _error(-2, "后端返回内容无法解析", "business", hint="请检查后端版本是否匹配。")
    except Exception as e:
        return _error(-3, f"未知网络错误：{e}", "network", retriable=True)

    if result.get("ok") is True:
        return result

    # 后端返回了业务错误
    err = result.get("error") or {}
    code = err.get("code", -2)
    msg = err.get("message", "未知错误")
    hint = err.get("hint", "")
    category = err.get("category", "business")
    retriable = err.get("retriable", False)
    return _error(code, msg, category, retriable=retriable, hint=hint)


# --- 工具函数 ---

def selectStock(query: str) -> dict:
    """条件选股：根据自然语言筛选条件查询符合条件的金融标的。

    Args:
        query: 筛选条件查询语句
    """
    return _post("/api/finAnalysis/selectStock", {"query": query})


# --- CLI ---

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="select_stock", description="金融标的条件选股工具调度入口")
    sub = p.add_subparsers(dest="tool", required=True, metavar="<tool>")

    s = sub.add_parser("selectStock", help="条件选股：根据自然语言筛选条件查询符合条件的金融标的")
    s.add_argument("--query", required=True, help="筛选条件查询语句")

    return p


def main() -> None:
    args = _build_parser().parse_args()

    if args.tool == "selectStock":
        result = selectStock(query=args.query)
    else:
        raise SystemExit(f"unknown tool: {args.tool}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
