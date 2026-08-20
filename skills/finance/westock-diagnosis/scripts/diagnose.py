#!/usr/bin/env python3
"""
持仓概览诊断脚本 — 获取市场数据并计算组合指标。

Usage（运行时 --help 输出绝对路径）:
  python3 <本脚本绝对路径> --portfolio '[{"name":"贵州茅台","code":"sh600519","qty":100,"cost":1800}]'
  python3 <本脚本绝对路径> --portfolio-file /tmp/portfolio.json
  python3 <本脚本绝对路径> --portfolio '...' --cash 50000 --total-assets 500000

Output: JSON to stdout
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_PATH = Path(__file__).resolve()
# ── Configuration ────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SUBPROCESS_TIMEOUT = 30
# ─────────────────────────────────────────────────────────────────────────────


def log(msg: str):
    print(f"[diagnose] {msg}", file=sys.stderr)


# ── Markdown table parser ────────────────────────────────────────────────────

def parse_markdown_table(text: str) -> list[dict]:
    """Parse a markdown table into a list of dicts. Handles westock output."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    # Find header line (first line starting with |)
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|") and "---" not in line:
            header_idx = i
            break
    if header_idx is None:
        return []

    def split_row(line: str) -> list[str]:
        parts = line.split("|")
        # strip first and last empty parts from leading/trailing |
        if parts and parts[0].strip() == "":
            parts = parts[1:]
        if parts and parts[-1].strip() == "":
            parts = parts[:-1]
        return [p.strip() for p in parts]

    headers = split_row(lines[header_idx])
    rows = []
    for line in lines[header_idx + 1:]:
        if not line.startswith("|"):
            continue
        if "---" in line and all(c in "-| " for c in line):
            continue
        vals = split_row(line)
        if len(vals) == len(headers):
            rows.append(dict(zip(headers, vals)))
    return rows


def safe_float(val, default=None):
    """Convert string to float, return default on failure."""
    if val is None:
        return default
    try:
        s = str(val).strip().replace(",", "").replace("%", "")
        if s in ("", "-", "--", "N/A", "null"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


# ── westock caller ──────────────────────────────────────────────────────

def resolve_westock_bin() -> str | None:
    """Locate the `westock` Go CLI binary.
      1. PATH 查找（shutil.which）—— 安装脚本会把 ~/.local/bin 写入 shell profile
      2. ~/.local/bin/westock   setup.sh 默认安装目录（兜底，防 PATH 未生效）
    找不到返回 None。
    """
    on_path = shutil.which("westock")
    if on_path:
        return on_path
    default = os.path.expanduser("~/.local/bin/westock")
    if os.path.isfile(default) and os.access(default, os.X_OK):
        return default
    return None


# 模块加载时解析一次（环境 PATH 不会在运行时变化）
WESTOCK_BIN = resolve_westock_bin()


def run_westock(args: list[str]) -> str:
    """Call westock CLI and return stdout."""
    if not WESTOCK_BIN:
        log("westock binary not found")
        return ""
    cmd = [WESTOCK_BIN] + args
    log(f"calling: westock {' '.join(args)}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT
        )
        if result.returncode != 0:
            log(f"westock error (exit {result.returncode}): {result.stderr[:200]}")
            return ""
        return result.stdout
    except subprocess.TimeoutExpired:
        log(f"westock timeout: {' '.join(args)}")
        return ""
    except Exception as e:
        log(f"westock exception: {e}")
        return ""


def search_stock(name: str) -> str | None:
    """Search for a stock code by name. Returns code like 'sh600519' or None."""
    output = run_westock(["search", name])
    rows = parse_markdown_table(output)
    if rows:
        return rows[0].get("code")
    return None


def fetch_quotes(codes: list[str]) -> dict[str, dict]:
    """Fetch quote data for multiple codes. Returns {code: {field: value}}."""
    if not codes:
        return {}
    output = run_westock(["quote", ",".join(codes)])
    rows = parse_markdown_table(output)
    result = {}
    for row in rows:
        code = row.get("code", "")
        if code:
            result[code] = row
    return result


def fetch_profiles(codes: list[str]) -> dict[str, dict]:
    """Fetch profile data for multiple codes. Returns {code: {field: value}}."""
    if not codes:
        return {}
    output = run_westock(["profile", ",".join(codes)])
    rows = parse_markdown_table(output)
    result = {}
    for row in rows:
        code = row.get("code", "")
        if code:
            result[code] = row
    return result


# ── Calculation engine ───────────────────────────────────────────────────────

INDUSTRY_KEYWORDS = [
    (["汽车", "新能源汽车", "整车"], "汽车"),
    (["电池", "充电", "储能", "锂"], "新能源"),
    (["半导体", "芯片", "集成电路"], "半导体"),
    (["互联网", "软件", "云计算", "人工智能", "AI"], "互联网"),
    (["银行"], "银行"),
    (["保险", "寿险"], "保险"),
    (["证券", "期货", "基金"], "券商"),
    (["地产", "房地产", "物业"], "房地产"),
    (["医药", "生物", "医疗", "疫苗", "制药"], "医药"),
    (["白酒", "酿酒", "啤酒"], "白酒"),
    (["食品", "饮料", "乳"], "食品饮料"),
    (["光伏", "太阳能", "风电", "风力"], "新能源"),
    (["消费电子", "手机", "家电"], "消费电子"),
    (["钢铁", "有色", "铝", "铜"], "有色金属"),
    (["石油", "天然气", "化工", "煤炭"], "能源化工"),
    (["航空", "航天", "军工", "国防"], "军工"),
    (["游戏", "传媒", "影视", "直播"], "传媒"),
    (["通信", "5G", "运营商"], "通信"),
    (["物流", "快递", "运输", "航运"], "物流"),
    (["农业", "养殖", "种业", "化肥"], "农业"),
]


def _infer_industry(business_desc: str, stock_name: str) -> str:
    """Try to infer industry from business description or stock name."""
    text = (business_desc + " " + stock_name).lower()
    for keywords, industry in INDUSTRY_KEYWORDS:
        for kw in keywords:
            if kw.lower() in text:
                return industry
    return "未知"


def diagnose_portfolio(positions: list[dict], cash: float | None, total_assets_input: float | None) -> dict:
    """Main diagnosis logic. Returns structured JSON result."""

    # 1. Resolve missing codes
    for pos in positions:
        if not pos.get("code"):
            name = pos.get("name", "")
            if name:
                code = search_stock(name)
                if code:
                    pos["code"] = code
                    log(f"resolved '{name}' -> {code}")
                else:
                    log(f"could not resolve code for '{name}'")

    # Filter positions with valid codes
    valid_positions = [p for p in positions if p.get("code")]
    if not valid_positions:
        return {"error": "没有有效的持仓数据（股票代码无法识别）"}

    codes = [p["code"] for p in valid_positions]

    # 2. Fetch market data
    quotes = fetch_quotes(codes)
    profiles = fetch_profiles(codes)

    # 3. Enrich positions
    enriched = []
    for pos in valid_positions:
        code = pos["code"]
        q = quotes.get(code, {})
        prof = profiles.get(code, {})

        current_price = safe_float(q.get("price"))
        prev_close = safe_float(q.get("prev_close"))
        qty = safe_float(pos.get("qty"), 0)
        cost = safe_float(pos.get("cost"))
        input_market_value = safe_float(pos.get("market_value"))
        input_pnl = safe_float(pos.get("pnl"))

        # ── Reverse-engineering missing fields ──
        # If qty missing but have market_value and current_price → qty = market_value / current_price
        if (not qty or qty == 0) and input_market_value and current_price and current_price > 0:
            qty = round(input_market_value / current_price)
            log(f"  inferred qty={qty} from market_value={input_market_value}/price={current_price}")

        # If cost missing but have market_value, pnl, qty → cost = (market_value - pnl) / qty
        if not cost and input_market_value and input_pnl is not None and qty and qty > 0:
            cost = round((input_market_value - input_pnl) / qty, 4)
            log(f"  inferred cost={cost} from market_value={input_market_value}, pnl={input_pnl}, qty={qty}")

        # If cost missing but have pnl, current_price, qty → cost = current_price - pnl/qty
        if not cost and input_pnl is not None and current_price and qty and qty > 0:
            cost = round(current_price - input_pnl / qty, 4)
            log(f"  inferred cost={cost} from price={current_price}, pnl={input_pnl}, qty={qty}")

        # Compute market value
        if input_market_value:
            market_value = input_market_value
        elif current_price and qty:
            market_value = round(current_price * qty, 2)
        else:
            market_value = None

        # ── P&L calculations ──
        daily_pnl = None
        daily_pnl_pct = None
        total_pnl = None
        total_pnl_pct = None

        if current_price and prev_close and qty:
            daily_pnl = round((current_price - prev_close) * qty, 2)
            if prev_close > 0:
                daily_pnl_pct = round((current_price - prev_close) / prev_close * 100, 2)

        # Use input_pnl directly if available and we couldn't compute
        if input_pnl is not None and cost and qty and cost > 0:
            total_pnl = round((current_price - cost) * qty, 2) if current_price else input_pnl
            total_pnl_pct = round((current_price - cost) / cost * 100, 2) if current_price and cost > 0 else None
        elif current_price and cost and qty and cost > 0:
            total_pnl = round((current_price - cost) * qty, 2)
            total_pnl_pct = round((current_price - cost) / cost * 100, 2)

        # Industry from profile
        industry = prof.get("industry", "")
        sector = prof.get("sector", "")
        # Fallback: if both are missing, try to infer from business description
        if (not industry or industry == "-") and (not sector or sector == "-"):
            biz = prof.get("business", "")
            industry = _infer_industry(biz, pos.get("name", ""))
            sector = industry
        elif not industry or industry == "-":
            industry = sector if sector and sector != "-" else "未知"
        if not sector or sector == "-":
            sector = industry

        enriched.append({
            "name": pos.get("name", q.get("name", code)),
            "code": code,
            "qty": qty,
            "cost": cost,
            "current_price": current_price,
            "prev_close": prev_close,
            "market_value": round(market_value, 2) if market_value else None,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "pe": safe_float(q.get("pe_ratio")),
            "pb": safe_float(q.get("pb_ratio")),
            "market_cap": safe_float(q.get("total_market_cap")),
            "change_pct": safe_float(q.get("change_percent")),
            "industry": industry,
            "sector": sector,
        })

    # 4. Portfolio-level calculations
    total_market_value = sum(p["market_value"] for p in enriched if p["market_value"])

    if total_market_value <= 0:
        return {"error": "无法计算持仓市值（行情数据获取失败）"}

    # Weights
    for p in enriched:
        if p["market_value"] and total_market_value > 0:
            p["weight_pct"] = round(p["market_value"] / total_market_value * 100, 2)
        else:
            p["weight_pct"] = 0

    # Sort by weight descending
    enriched.sort(key=lambda x: x["weight_pct"], reverse=True)

    # Account overview
    total_cost = sum(
        (p["cost"] or 0) * (p["qty"] or 0)
        for p in enriched
        if p["cost"] and p["qty"]
    )
    has_cost = total_cost > 0

    agg_daily_pnl = sum(p["daily_pnl"] for p in enriched if p["daily_pnl"] is not None)
    agg_total_pnl = sum(p["total_pnl"] for p in enriched if p["total_pnl"] is not None) if has_cost else None

    cash_val = cash if cash is not None else None
    if total_assets_input is not None:
        total_assets = total_assets_input
    elif cash_val is not None:
        total_assets = total_market_value + cash_val
    else:
        total_assets = total_market_value

    cash_ratio = round(cash_val / total_assets * 100, 2) if cash_val is not None and total_assets > 0 else None

    account = {
        "total_market_value": round(total_market_value, 2),
        "total_cost": round(total_cost, 2) if has_cost else None,
        "cash": cash_val,
        "total_assets": round(total_assets, 2),
        "cash_ratio": cash_ratio,
        "position_count": len(enriched),
        "daily_pnl": round(agg_daily_pnl, 2),
        "daily_pnl_pct": round(agg_daily_pnl / total_market_value * 100, 2) if total_market_value > 0 else None,
        "total_pnl": round(agg_total_pnl, 2) if agg_total_pnl is not None else None,
        "total_pnl_pct": round(agg_total_pnl / total_cost * 100, 2) if has_cost and total_cost > 0 else None,
    }

    # Sector distribution
    sector_map: dict[str, float] = {}
    for p in enriched:
        s = p["sector"] or p["industry"] or "未知"
        sector_map[s] = sector_map.get(s, 0) + p["weight_pct"]
    sector_dist = sorted(
        [{"sector": k, "weight_pct": round(v, 2)} for k, v in sector_map.items()],
        key=lambda x: x["weight_pct"], reverse=True
    )

    # Concentration
    weights = [p["weight_pct"] for p in enriched]
    concentration = {
        "top1_name": enriched[0]["name"] if enriched else "",
        "top1_pct": round(weights[0], 2) if len(weights) >= 1 else 0,
        "top3_pct": round(sum(weights[:3]), 2) if len(weights) >= 3 else round(sum(weights), 2),
        "top5_pct": round(sum(weights[:5]), 2) if len(weights) >= 5 else round(sum(weights), 2),
    }

    # 5. Diagnostics (signal lights)
    diagnostics = {}

    # Cash status
    if cash_ratio is not None:
        if cash_ratio < 5:
            diagnostics["cash_status"] = "red"
            diagnostics["cash_issue"] = f"现金仅占{cash_ratio}%，几乎满仓"
        elif cash_ratio <= 20:
            diagnostics["cash_status"] = "green"
            diagnostics["cash_issue"] = f"现金占{cash_ratio}%，仓位适中"
        elif cash_ratio <= 50:
            diagnostics["cash_status"] = "yellow"
            diagnostics["cash_issue"] = f"现金占{cash_ratio}%，偏保守"
        else:
            diagnostics["cash_status"] = "yellow"
            diagnostics["cash_issue"] = f"现金占{cash_ratio}%，大部分是现金"
    else:
        diagnostics["cash_status"] = "unknown"
        diagnostics["cash_issue"] = "现金数据未提供"

    # Sector concentration
    if sector_dist:
        top1_sector = sector_dist[0]
        top2_weight = sum(s["weight_pct"] for s in sector_dist[:2]) if len(sector_dist) >= 2 else top1_sector["weight_pct"]
        if top1_sector["weight_pct"] > 40:
            diagnostics["sector_status"] = "red"
            diagnostics["sector_issue"] = f"{top1_sector['sector']}占{top1_sector['weight_pct']}%，单行业超40%"
        elif top2_weight > 70:
            diagnostics["sector_status"] = "red"
            diagnostics["sector_issue"] = f"前2行业合计{round(top2_weight, 1)}%，过于集中"
        elif len(sector_dist) >= 5 and top1_sector["weight_pct"] <= 30:
            diagnostics["sector_status"] = "green"
            diagnostics["sector_issue"] = f"{len(sector_dist)}个行业，分布不错"
        else:
            diagnostics["sector_status"] = "yellow"
            diagnostics["sector_issue"] = f"{top1_sector['sector']}占{top1_sector['weight_pct']}%，有一定集中"

    # Position concentration
    if concentration["top1_pct"] > 30:
        diagnostics["concentration_status"] = "red"
        diagnostics["concentration_issue"] = f"{concentration['top1_name']}占{concentration['top1_pct']}%，单只过重"
    elif concentration["top5_pct"] > 80:
        diagnostics["concentration_status"] = "red"
        diagnostics["concentration_issue"] = f"前5大占{concentration['top5_pct']}%，分散度低"
    elif concentration["top5_pct"] > 50:
        diagnostics["concentration_status"] = "yellow"
        diagnostics["concentration_issue"] = f"前5大占{concentration['top5_pct']}%，有一定集中"
    else:
        diagnostics["concentration_status"] = "green"
        diagnostics["concentration_issue"] = f"前5大占{concentration['top5_pct']}%，持仓分散"

    # P&L status
    if has_cost and account["total_pnl_pct"] is not None:
        pnl_pct = account["total_pnl_pct"]
        if pnl_pct > 30:
            diagnostics["pnl_status"] = "green"
            diagnostics["pnl_summary"] = f"整体盈利{pnl_pct}%，注意保护利润"
        elif pnl_pct > 10:
            diagnostics["pnl_status"] = "green"
            diagnostics["pnl_summary"] = f"整体盈利{pnl_pct}%，状态不错"
        elif pnl_pct > 0:
            diagnostics["pnl_status"] = "green"
            diagnostics["pnl_summary"] = f"整体微利{pnl_pct}%"
        elif pnl_pct > -10:
            diagnostics["pnl_status"] = "yellow"
            diagnostics["pnl_summary"] = f"整体小幅亏损{pnl_pct}%"
        elif pnl_pct > -20:
            diagnostics["pnl_status"] = "yellow"
            diagnostics["pnl_summary"] = f"整体亏损{pnl_pct}%，需要关注"
        else:
            diagnostics["pnl_status"] = "red"
            diagnostics["pnl_summary"] = f"整体亏损{pnl_pct}%，建议审视组合"
    else:
        diagnostics["pnl_status"] = "unknown"
        diagnostics["pnl_summary"] = "成本价未提供，无法计算盈亏"

    # Position count
    n = len(enriched)
    if n <= 2:
        diagnostics["count_status"] = "yellow"
        diagnostics["count_issue"] = f"仅{n}只，过于集中"
    elif n <= 8:
        diagnostics["count_status"] = "green"
        diagnostics["count_issue"] = f"{n}只，数量适中"
    elif n <= 15:
        diagnostics["count_status"] = "green"
        diagnostics["count_issue"] = f"{n}只，偏多但可管理"
    else:
        diagnostics["count_status"] = "yellow"
        diagnostics["count_issue"] = f"{n}只，可能过度分散"

    return {
        "account": account,
        "positions": enriched,
        "sector_distribution": sector_dist,
        "concentration": concentration,
        "diagnostics": diagnostics,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog=f"python3 {SCRIPT_PATH}",
        description="持仓概览诊断 — 获取数据并计算组合指标",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--portfolio", help="持仓 JSON 字符串")
    group.add_argument("--portfolio-file", help="持仓 JSON 文件路径")
    parser.add_argument("--cash", type=float, default=None, help="可用现金金额")
    parser.add_argument("--total-assets", type=float, default=None, help="账户总资产")
    args = parser.parse_args()

    # Parse portfolio input
    if args.portfolio:
        try:
            positions = json.loads(args.portfolio)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
            sys.exit(1)
    else:
        try:
            with open(args.portfolio_file, "r", encoding="utf-8") as f:
                positions = json.load(f)
        except Exception as e:
            print(json.dumps({"error": f"文件读取失败: {e}"}, ensure_ascii=False))
            sys.exit(1)

    if not isinstance(positions, list) or len(positions) == 0:
        print(json.dumps({"error": "持仓数据为空"}, ensure_ascii=False))
        sys.exit(1)

    # Run diagnosis
    result = diagnose_portfolio(positions, args.cash, args.total_assets)

    # Output JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
