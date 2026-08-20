#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市场全景 CLI 入口 (v6.1 新增)

子命令：
  global            全球指数全景表（强弱排名 + 相关性提示）
  index <别名>      单指数深度分析 + T+1/T+3/T+5 预判（如 N225 / GOLD / 100.HSI）
  gold              黄金/白银/原油专题
  policy            政策解读 + 影响板块
  sectors <市场>    板块趋势（cn/hk/us，默认 cn）
  all               综合晨报（全球指数 + 政策 + 板块，markdown）

选项：
  --json            JSON 格式输出

示例：
  python scripts/market_overview.py global
  python scripts/market_overview.py index N225
  python scripts/market_overview.py gold --json
  python scripts/market_overview.py all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# 保证可 import scripts/ 下的 stock_researcher 包与 stock_predict
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stock_researcher.index_analysis.global_trends import (  # noqa: E402
    GLOBAL_INDEX_UNIVERSE, COMMODITY_ALIASES,
    fetch_index_data, analyze_index, global_market_outlook,
    index_forecast, sector_trend_report,
)
from stock_researcher.macro.policy_analyzer import (  # noqa: E402
    fetch_policy_news, analyze_policy_impact, policy_score,
    format_for_llm, format_policy_report,
)

DISCLAIMER = "仅供学习参考，不构成投资建议"


def _hr(ch="=", width=70):
    return ch * width


def _print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


# ── global：全球指数全景 ──────────────────────────────────
def cmd_global(args):
    outlook = global_market_outlook()
    if args.json:
        _print_json(outlook)
        return

    print(f"\n{_hr()}")
    print(f"  🌐 全球指数全景  |  {outlook['timestamp']}  |  {DISCLAIMER}")
    print(f"{_hr()}")
    print(f"  {'指数':<14}{'市场':>4} {'最新价':>12} {'涨跌幅':>8} "
          f"{'趋势':<8} {'评分':>7}")
    print(f"  {_hr('-', 66)}")
    market_names = {"cn": "A股", "hk": "港股", "us": "美股", "jp": "日本",
                    "kr": "韩国", "tw": "台湾", "au": "澳洲", "in": "印度",
                    "uk": "英国", "de": "德国", "fr": "法国",
                    "comex": "商品", "shfe": "商品", "nymex": "商品", "fx": "汇率"}
    for idx in outlook["indices"]:
        if idx.get("price") is None:
            print(f"  {idx['name']:<14}{market_names.get(idx['market'], idx['market']):>4} "
                  f"{'数据暂缺':>12} {'':>8} {'数据暂缺':<8} {'':>7}")
            continue
        chg = idx.get("change_pct")
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        score = idx.get("score")
        score_str = f"{score:+.0f}" if score is not None else "-"
        tag = "*" if idx.get("degraded") else ""
        print(f"  {idx['name']:<14}{market_names.get(idx['market'], idx['market']):>4} "
              f"{idx['price']:>12.2f} {chg_str:>8} {idx['trend'] + tag:<8} {score_str:>7}")
    print(f"  (带*为K线数据暂缺，仅基于当日涨跌粗略评估)")

    top = outlook["ranking"]["top"]
    bottom = outlook["ranking"]["bottom"]
    if top:
        top_text = "、".join("{}({:+.0f})".format(x["name"], x["score"]) for x in top[:3])
        print(f"\n  🚀 最强: {top_text}")
    if bottom:
        bottom_text = "、".join("{}({:+.0f})".format(x["name"], x["score"]) for x in bottom[:3])
        print(f"  🧊 最弱: {bottom_text}")

    print(f"\n  ── 相关性提示（近60日收益相关系数）──")
    for c in outlook["correlations"]:
        if c["corr"] is None:
            print(f"  · {c['label']}: {c['note']}")
        else:
            print(f"  · {c['label']}: {c['corr']:+.2f} ({c['note']})")
    print(_hr())


# ── index：单指数深度 + 预判 ──────────────────────────────
def cmd_index(args):
    alias = args.alias
    # quote+kline 一次抓取，分析与预判共用（减少请求防限流）
    data = fetch_index_data(
        GLOBAL_INDEX_UNIVERSE.get(alias.upper(), (alias,))[0], days=120)
    analysis = analyze_index(alias, data=data)
    forecast = index_forecast(alias, data=data)
    if args.json:
        _print_json({"analysis": analysis, "forecast": forecast})
        return

    t = analysis.get("technical", {})
    kl = analysis.get("key_levels", {})
    print(f"\n{_hr()}")
    print(f"  📈 {analysis['name']}({analysis['alias']}) 深度分析  |  {DISCLAIMER}")
    print(f"{_hr()}")
    price = analysis.get("price") or 0
    chg = analysis.get("change_pct")
    print(f"  现价: {price:.2f}  涨跌: {chg:+.2f}%" if chg is not None
          else f"  现价: {price:.2f}")
    print(f"  趋势: {analysis['trend']}  综合评分: {analysis['score']:+.1f}/±100"
          + ("  [K线数据暂缺,降级评估]" if analysis.get("degraded") else ""))

    if t:
        print(f"\n  ── 技术指标 ──")
        print(f"  MA5:{t.get('ma5')} MA10:{t.get('ma10')} "
              f"MA20:{t.get('ma20')} MA60:{t.get('ma60')}  [{t.get('ma_status')}]")
        macd = t.get("macd", {})
        print(f"  RSI:{t.get('rsi')} MACD:DIF={macd.get('dif')} "
              f"DEA={macd.get('dea')} HIST={macd.get('hist')}")
        kdj = t.get("kdj", {})
        boll = t.get("boll", {})
        print(f"  KDJ:K={kdj.get('k')} D={kdj.get('d')} J={kdj.get('j')}  "
              f"布林:上{boll.get('up')} 中{boll.get('mid')} 下{boll.get('lo')}")
        adx = t.get("adx", {})
        print(f"  ADX:{adx.get('adx', 0)} WR:{t.get('wr')} CCI:{t.get('cci')} "
              f"MFI:{t.get('mfi')} ATR:{t.get('atr')}")
        print(f"  近5日:{t.get('pct5')}%  近20日:{t.get('pct20')}%  "
              f"波动率(20日):{t.get('volatility20')}%")

    if kl:
        print(f"\n  ── 关键位 ──")
        print(f"  支撑:{kl.get('支撑')}  压力:{kl.get('压力')}  "
              f"MA20:{kl.get('MA20')}  布林上/下轨:{kl.get('布林上轨')}/{kl.get('布林下轨')}")

    if analysis.get("signals"):
        print(f"\n  ── 信号 ──")
        for s in analysis["signals"]:
            print(f"  · {s}")

    print(f"\n  ── T+1/T+3/T+5 蒙特卡洛预判 ──")
    print(f"  {'周期':<6} {'方向':<6} {'预测涨跌':>9} {'上涨概率':>8} {'80%置信区间':>18}")
    for h in ("1d", "3d", "5d"):
        f = forecast.get(h)
        if not f:
            continue
        ci = f"{f['p10']:+.2f}%~{f['p90']:+.2f}%"
        print(f"  T+{h[0]:<4} {f['direction']:<6} {f['predicted_pct']:>+8.2f}% "
              f"{f['prob_up']:>7.0f}% {ci:>18}")
    print(_hr())


# ── gold：黄金白银原油专题 ────────────────────────────────
def cmd_gold(args):
    results = {}
    for alias in COMMODITY_ALIASES:
        # 每个品种只抓一次数据，分析与预判共用
        secid = GLOBAL_INDEX_UNIVERSE[alias][0]
        data = fetch_index_data(secid, days=120)
        results[alias] = {
            "analysis": analyze_index(alias, data=data),
            "forecast": index_forecast(alias, data=data),
        }
    if args.json:
        _print_json(results)
        return

    print(f"\n{_hr()}")
    print(f"  🥇 黄金/白银/原油专题  |  {time.strftime('%Y-%m-%d %H:%M')}  |  {DISCLAIMER}")
    print(f"{_hr()}")
    for alias in COMMODITY_ALIASES:
        a = results[alias]["analysis"]
        f = results[alias]["forecast"]
        if a.get("price") is None and a.get("degraded"):
            print(f"  {a['name']}: 数据暂缺")
            continue
        chg = a.get("change_pct")
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        f5 = f.get("5d", {})
        print(f"\n  ■ {a['name']}  {a.get('price', 0):.2f}  {chg_str}  "
              f"趋势:{a['trend']}({a['score']:+.0f})")
        if a.get("signals"):
            print(f"    信号: {'；'.join(a['signals'][:2])}")
        if f5:
            print(f"    T+5预判: {f5.get('direction')} "
                  f"{f5.get('predicted_pct', 0):+.2f}% (涨的概率{f5.get('prob_up', 50):.0f}%)")
    print(_hr())


# ── policy：政策解读 ──────────────────────────────────────
def cmd_policy(args):
    if args.json:
        news = fetch_policy_news(days=7)
        _print_json({
            "score_cn": policy_score("cn"),
            "events": analyze_policy_impact(news),
            "llm_markdown": format_for_llm(news),
        })
        return
    print(format_policy_report(market="cn", days=7))
    print(f"\n  ── LLM 深度解读素材（markdown）──")
    print(format_for_llm(fetch_policy_news(days=7)))


# ── sectors：板块趋势 ─────────────────────────────────────
def cmd_sectors(args):
    report = sector_trend_report(market=args.market)
    if args.json:
        _print_json(report)
        return

    mlabel = {"cn": "A股", "hk": "港股", "us": "美股"}.get(args.market, args.market)
    print(f"\n{_hr()}")
    print(f"  🏭 {mlabel}板块趋势  |  {report['timestamp']}  |  {DISCLAIMER}")
    print(f"{_hr()}")
    print(f"  {'板块':<10} {'平均涨跌':>8} {'上/下':>7} {'主力净流入':>12} "
          f"{'信号':<8} {'政策'}")
    print(f"  {_hr('-', 66)}")
    for s in report["sectors"]:
        if s.get("avg_change_pct") is None:
            print(f"  {s['name']:<10} {'数据暂缺':>8}")
            continue
        arrow = "▲" if s["avg_change_pct"] > 0 else \
                ("▼" if s["avg_change_pct"] < 0 else "-")
        flow = s.get("total_net_flow", 0)
        boost = "🟢" + s["policy_boost"][:6] if s.get("policy_boost") else ""
        print(f"  {s['name']:<10} {arrow}{abs(s['avg_change_pct']):>6.1f}% "
              f"{s.get('up_count', 0)}/{s.get('down_count', 0):<3} "
              f"{flow:>10.0f}万 {s.get('signal', ''):<8} {boost}")
    if report.get("rotation_note"):
        print(f"\n  🔄 {report['rotation_note']}")
    ps = report.get("policy_score", {})
    print(f"  📜 政策面: {ps.get('score', 0):+.1f} [{ps.get('label', '')}]")
    if report.get("policy_benefited_sectors"):
        items = "、".join(f"{k}({v})" for k, v in
                          list(report["policy_benefited_sectors"].items())[:5])
        print(f"  🎯 政策受益板块: {items}")
    print(_hr())


# ── all：综合晨报 ─────────────────────────────────────────
def cmd_all(args):
    outlook = global_market_outlook()
    news = fetch_policy_news(days=7)
    events = analyze_policy_impact(news)
    pscore = policy_score("cn")
    sectors = sector_trend_report(market="cn")

    if args.json:
        _print_json({"outlook": outlook, "policy_events": events,
                     "policy_score": pscore, "sectors": sectors})
        return

    lines = []
    lines.append(f"# 📰 全球市场综合晨报  {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\n> {DISCLAIMER}\n")

    lines.append("## 一、全球指数全景")
    lines.append("| 指数 | 最新价 | 涨跌幅 | 趋势 | 评分 |")
    lines.append("|---|---|---|---|---|")
    for idx in outlook["indices"]:
        if idx.get("price") is None:
            lines.append(f"| {idx['name']} | 数据暂缺 | - | 数据暂缺 | - |")
            continue
        chg = idx.get("change_pct")
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        score = idx.get("score")
        lines.append(f"| {idx['name']} | {idx['price']:.2f} | {chg_str} | "
                     f"{idx['trend']} | {score:+.0f} |" if score is not None
                     else f"| {idx['name']} | {idx['price']:.2f} | {chg_str} | "
                          f"{idx['trend']} | - |")
    top = outlook["ranking"]["top"][:3]
    bottom = outlook["ranking"]["bottom"][:3]
    if top:
        top_text = "、".join("{}({:+.0f})".format(x["name"], x["score"]) for x in top)
        bottom_text = "、".join("{}({:+.0f})".format(x["name"], x["score"]) for x in bottom)
        lines.append(f"\n最强: {top_text}；最弱: {bottom_text}")

    lines.append("\n### 相关性提示（近60日）")
    for c in outlook["correlations"]:
        if c["corr"] is None:
            lines.append(f"- {c['label']}: {c['note']}")
        else:
            lines.append(f"- {c['label']}: {c['corr']:+.2f}（{c['note']}）")

    lines.append("\n## 二、政策面解读")
    lines.append(f"政策面净影响(A股): **{pscore['score']:+.1f}** [{pscore['label']}]，"
                 f"近7天捕获政策事件 {pscore['event_count']} 件"
                 f"（利多{pscore['pos_count']}/利空{pscore['neg_count']}）\n")
    for ev in events[:8]:
        icon = "🟢" if ev["direction"] == "利多" else \
               ("🔴" if ev["direction"] == "利空" else "🟡")
        lines.append(f"- {icon} **[{ev['category']}|重要度{ev['importance']}]** "
                     f"{ev['title']}")
        lines.append(f"  - {ev['interpretation']}")
    if not events:
        lines.append("- 近期未捕获到政策相关新闻（数据源不可用或限流）")

    lines.append("\n## 三、A股板块趋势")
    if sectors.get("rotation_note"):
        lines.append(sectors["rotation_note"] + "\n")
    lines.append("| 板块 | 平均涨跌 | 信号 | 政策受益 |")
    lines.append("|---|---|---|---|")
    for s in sectors["sectors"]:
        if s.get("avg_change_pct") is None:
            continue
        boost = s.get("policy_boost", "")
        lines.append(f"| {s['name']} | {s['avg_change_pct']:+.1f}% | "
                     f"{s.get('signal', '')} | {boost} |")
    if sectors.get("policy_benefited_sectors"):
        items = "、".join(sectors["policy_benefited_sectors"].keys())
        lines.append(f"\n政策受益板块叠加: {items}")

    print("\n".join(lines))


# ── CLI ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="market_overview",
        description="市场全景分析：全球指数/商品趋势 + 政策解读 + 板块轮动"
        f"（{DISCLAIMER}）")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("global", help="全球指数全景表")

    p_index = sub.add_parser("index", help="单指数深度分析 + T+1/3/5 预判")
    p_index.add_argument("alias", help="指数别名(如 N225/GOLD/HSI)或东财 secid")

    sub.add_parser("gold", help="黄金/白银/原油专题")
    sub.add_parser("policy", help="政策解读 + 影响板块")

    p_sec = sub.add_parser("sectors", help="板块趋势")
    p_sec.add_argument("market", nargs="?", default="cn",
                       choices=["cn", "hk", "us"], help="市场(默认 cn)")

    sub.add_parser("all", help="综合晨报(markdown)")

    args = parser.parse_args()
    handlers = {
        "global": cmd_global, "index": cmd_index, "gold": cmd_gold,
        "policy": cmd_policy, "sectors": cmd_sectors, "all": cmd_all,
    }
    handler = handlers.get(args.cmd)
    if not handler:
        parser.print_help()
        sys.exit(0)
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\n已取消。")
    except Exception as e:
        # 兜底：任何意外不抛 traceback，打印简讯
        print(f"\n  ⚠️ 执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
