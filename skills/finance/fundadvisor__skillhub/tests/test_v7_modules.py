#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.0 新增模块测试（全部离线可跑）

覆盖：perf_metrics / asset_allocator / learning_engine / review_engine
无 pytest 时可 `python tests/test_v7_modules.py` 直接运行。
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "data_collection"))


# ─── perf_metrics ─────────────────────────────────────────
def test_perf_metrics_basic():
    """手工构造净值序列，验证年化/夏普/回撤的符号与数量级"""
    from analysis import perf_metrics as pm
    nav = [1, 1.01, 0.99, 1.02, 1.05]
    ann = pm.annualized_return(nav)
    assert ann is not None and ann > 0, f"上涨序列年化应为正，实际 {ann}"
    sp = pm.sharpe(nav)
    assert sp is not None and sp > 0, f"上涨序列夏普应为正，实际 {sp}"
    vol = pm.annualized_volatility(nav)
    assert vol is not None and vol > 0, f"波动率应为正，实际 {vol}"
    mdd = pm.max_drawdown(nav)
    assert mdd is not None and mdd["mdd"] <= 0, "回撤应为非正数"
    # [1,1.01] 峰值后跌到 0.99：回撤 (0.99-1.01)/1.01 ≈ -1.98%
    assert abs(mdd["mdd"] - (-1.9802)) < 0.01, f"mdd 应约 -1.98%，实际 {mdd['mdd']}"
    print(f"  ✅ test_perf_metrics_basic (ann={ann:.2f}%, sharpe={sp:.2f}, mdd={mdd['mdd']}%)")


def test_perf_metrics_mdd_known():
    """已知答案： [1,1.2,1.0,1.1] 最大回撤应为约 -16.67%"""
    from analysis import perf_metrics as pm
    mdd = pm.max_drawdown([1, 1.2, 1.0, 1.1])
    assert mdd is not None
    assert abs(mdd["mdd"] - (-16.6667)) < 0.01, f"mdd 应约 -16.67%，实际 {mdd['mdd']}"
    assert mdd["peak_idx"] == 1 and mdd["trough_idx"] == 2
    assert mdd["duration_days"] == 1
    print(f"  ✅ test_perf_metrics_mdd_known (mdd={mdd['mdd']}%)")


def test_perf_metrics_edge_and_benchmark():
    """短输入安全返回；带基准时 compute_all_metrics 给出 beta/IR"""
    from analysis import perf_metrics as pm
    assert pm.annualized_return([]) is None
    assert pm.annualized_return([1.0]) is None
    assert pm.max_drawdown([1.0]) is None
    assert pm.sharpe([]) is None
    p = [1, 1.02, 1.01, 1.04, 1.06, 1.05, 1.08]
    b = [1, 1.01, 1.00, 1.02, 1.03, 1.02, 1.04]
    m = pm.compute_all_metrics(p, b)
    assert m["total_return"] is not None and m["total_return"] > 0
    assert "beta" in m and m["beta"] is not None
    assert "information_ratio" in m
    assert "excess_return" in m
    roll = pm.rolling_metric(p, 3, "annualized")
    assert len(roll) == len(p) and roll[0] is None and roll[1] is None
    assert roll[-1] is not None
    print(f"  ✅ test_perf_metrics_edge_and_benchmark (beta={m['beta']}, "
          f"excess={m['excess_return']}%)")


# ─── asset_allocator ──────────────────────────────────────
def test_asset_allocator_questionnaire():
    """全 0 -> 保守型；全 4 -> 进取型"""
    from analysis import asset_allocator as aa
    p0 = aa.score_risk_questionnaire([0] * 10)
    assert p0["risk_level"] == "保守型", f"全0应为保守型，实际 {p0['risk_level']}"
    assert p0["mapped_score"] == 5
    p4 = aa.score_risk_questionnaire([4] * 10)
    assert p4["risk_level"] == "进取型", f"全4应为进取型，实际 {p4['risk_level']}"
    assert p4["mapped_score"] == 25
    bad = aa.score_risk_questionnaire([1, 2, 3])
    assert "error" in bad
    print(f"  ✅ test_asset_allocator_questionnaire (全0={p0['risk_level']}, 全4={p4['risk_level']})")


def test_asset_allocator_saa():
    """SAA：保守货基占比高、进取股基>55、各类和为100"""
    from analysis import asset_allocator as aa
    s0 = aa.saa_for_profile("保守型", horizon_years=3)
    assert s0["货基/短债"] >= 30, f"保守型货基应占比较高，实际 {s0['货基/短债']}"
    s4 = aa.saa_for_profile("进取型", horizon_years=3)
    assert s4["股基"] > 55, f"进取型股基应>55，实际 {s4['股基']}"
    for level in ("保守型", "稳健型", "平衡型", "成长型", "进取型"):
        s = aa.saa_for_profile(level, horizon_years=5)
        assert sum(v for k, v in s.items() if k != "note") == 100, \
            f"{level} SAA 和应为 100，实际 {sum(v for k, v in s.items() if k != 'note')}"
    cash = aa.saa_for_profile("平衡型", goal="现金")
    assert cash["货基/短债"] == 80 and cash["纯债"] == 20
    # 期限微调：>10 年股基应不低于基准
    long_s = aa.saa_for_profile("平衡型", horizon_years=15)
    assert long_s["股基"] >= aa.SAA_BASE["平衡型"]["股基"]
    print(f"  ✅ test_asset_allocator_saa (保守货基={s0['货基/短债']}%, 进取股基={s4['股基']}%)")


def test_asset_allocator_optimizer_and_suitability():
    """风险平价权重和为1且低波资产权重高；适当性校验拦截越级"""
    from analysis import asset_allocator as aa
    w = aa.optimize_equal_risk([0.20, 0.10, 0.05])
    assert abs(sum(w) - 1.0) < 1e-6, f"风险平价权重和应为1，实际 {sum(w)}"
    assert w[2] > w[1] > w[0], f"低波资产权重应更高，实际 {w}"
    corr = [[1, 0.3, 0.1], [0.3, 1, 0.2], [0.1, 0.2, 1]]
    w2 = aa.optimize_equal_risk([0.20, 0.10, 0.05], corr)
    assert abs(sum(w2) - 1.0) < 1e-6 and w2[2] > w2[0]
    mv = aa.optimize_mean_variance([0.08, 0.04, 0.02],
                                   [[0.04, 0.005, 0.001],
                                    [0.005, 0.01, 0.002],
                                    [0.001, 0.002, 0.002]])
    assert abs(sum(mv) - 1.0) < 1e-6 and all(0 <= x <= 0.4 + 1e-9 for x in mv)
    chk = aa.suitability_check("保守型", "R5")
    assert chk["match"] is False and chk["warning"], "保守客户买R5应不匹配并告警"
    chk2 = aa.suitability_check("进取型", "R3")
    assert chk2["match"] is True
    print(f"  ✅ test_asset_allocator_optimizer_and_suitability (rp={w})")


def test_asset_allocator_plan():
    """build_allocation_plan 返回必要键"""
    from analysis import asset_allocator as aa
    plan = aa.build_allocation_plan(100000, answers=[1] * 10, horizon_years=20, goal="养老")
    for key in ("risk_profile", "saa", "glide_path", "core_satellite",
                "fund_slots", "rebalancing_rule", "generated_at", "disclaimer"):
        assert key in plan, f"缺少键 {key}"
    assert plan["risk_profile"]["risk_level"] == "稳健型"  # raw=10 -> mapped=10
    assert plan["glide_path"] is not None and len(plan["glide_path"]) == 21
    # 下滑曲线应单调不增且终点低
    equities = [p["equity_pct"] for p in plan["glide_path"]]
    assert equities[-1] <= equities[0]
    total_pct = sum(v["pct"] for v in plan["saa"].values())
    assert total_pct == 100
    cs = plan["core_satellite"]
    assert abs(cs["core"]["amount"] + cs["satellite"]["amount"] - 100000) < 1
    print(f"  ✅ test_asset_allocator_plan (等级={plan['risk_profile']['risk_level']}, "
          f"核心={cs['core']['amount']})")


# ─── learning_engine ──────────────────────────────────────
def _make_engine(tmpdir):
    """在临时目录构造 LearningEngine（不污染真实数据目录）"""
    os.environ["FUND_ADVISOR_LEARNING_DIR"] = tmpdir
    from learning import LearningEngine
    return LearningEngine()


def test_learning_engine_full_cycle():
    """log_advice -> record_outcome -> compute_stats -> calibrate -> report 全链路"""
    with tempfile.TemporaryDirectory() as td:
        le = _make_engine(td)
        try:
            # playbook 首次运行应从默认模板拷贝出 5 条规则
            pb = le._read_json(le.playbook_path, {})
            assert len(pb.get("rules", [])) == 5, "默认规则库应有 5 条规则"
            # 记录 6 条止盈建议 + 1 条止损建议
            ids = [le.log_advice("c1", "rebalance", "110022", "减持止盈",
                                 ["收益超30%"], confidence=0.7) for _ in range(6)]
            stop_id = le.log_advice("c1", "risk_alert", "510300", "评估止损",
                                    ["亏损超20%"], confidence=0.8)
            assert ids[0] != ids[1], "advice_id 应唯一"
            # 回填：5 条 miss（基金涨得比基准好，止盈错了）+ 1 条 hit
            for aid in ids[:5]:
                oc = le.record_outcome(aid, 30, 8.0, 2.0)   # 减持后基金仍跑赢 -> miss
                assert oc["hit"] is False
            oc = le.record_outcome(ids[5], 30, -5.0, 2.0)   # 减持后基金跌 -> hit
            assert oc["hit"] is True
            assert oc["action_benefit"] == 7.0              # 2 - (-5)
            dup = le.record_outcome(ids[5], 30, -5.0, 2.0)
            assert "error" in dup, "重复回填应被拒绝"
            # 止损建议：基金继续跌 -> hit=True（反向验证方向）
            oc2 = le.record_outcome(stop_id, 30, -8.0, 1.0)
            assert oc2["hit"] is True
            stats = le.compute_stats()
            tp = stats["by_action"]["减持止盈"]
            assert tp["samples"] == 6 and tp["hits"] == 1
            assert abs(tp["win_rate"] - 16.7) < 0.2
            # 止盈命中率 16.7% < 40% 且样本>=5 -> profit_take_threshold +5 (30->35)
            cal_res = le.calibrate()
            assert cal_res["calibration"]["profit_take_threshold"] == 35.0, \
                f"止盈阈值应校准为35，实际 {cal_res['calibration']['profit_take_threshold']}"
            assert cal_res["adjustments"], "应有调整记录"
            # playbook_update：止盈规则胜率 16.7% < 35% 且样本>=5 -> 停用
            pu = le.playbook_update()
            rules = {r["rule_id"]: r for r in le._read_json(le.playbook_path, {})["rules"]}
            assert rules["R001"]["enabled"] is False, "止盈规则应被自动停用"
            assert pu["disabled"] >= 1
            # 报告
            rep = le.get_learning_report()
            assert rep["样本量"] == 7 and rep["已评估"] == 7
            assert rep["playbook"]["规则总数"] == 5
            assert len(rep["最近建议"]) == 7
            # apply_calibration 覆盖
            merged = le.apply_calibration({"profit_take_threshold": 30, "其他": 1})
            assert merged["profit_take_threshold"] == 35.0 and merged["其他"] == 1
            # 手工加规则
            new_rule = le.add_rule("测试新规则", {"text": "t", "action": "持有"}, "持有")
            assert new_rule["rule_id"] == "R006"
        finally:
            os.environ.pop("FUND_ADVISOR_LEARNING_DIR", None)
    print("  ✅ test_learning_engine_full_cycle (6止盈1hit->阈值30->35, R001停用)")


def test_learning_hit_direction():
    """命中规则方向：'减持'后基金跌 -> hit=True；'增持'后基金涨 -> hit=True"""
    with tempfile.TemporaryDirectory() as td:
        le = _make_engine(td)
        try:
            a1 = le.log_advice("c2", "rebalance", "111", "减持", ["r"], 0.6)
            a2 = le.log_advice("c2", "fund_pick", "222", "增持", ["r"], 0.6)
            a3 = le.log_advice("c2", "fund_pick", "333", "增持", ["r"], 0.6)
            assert le.record_outcome(a1, 30, -3.0, 0.0)["hit"] is True    # 减持后跌 ✓
            assert le.record_outcome(a2, 30, 5.0, 1.0)["hit"] is True     # 增持后涨 ✓
            assert le.record_outcome(a3, 30, -2.0, 1.0)["hit"] is False   # 增持后跌 ✗
        finally:
            os.environ.pop("FUND_ADVISOR_LEARNING_DIR", None)
    print("  ✅ test_learning_hit_direction (减持后跌=hit, 增持后涨=hit)")


def test_learning_auto_evaluate_offline():
    """auto_evaluate_pending 离线不崩：无 nav_at_log 的建议跳过并计数"""
    with tempfile.TemporaryDirectory() as td:
        le = _make_engine(td)
        try:
            # 手工塞一条 40 天前的建议（无 nav_at_log）
            from datetime import datetime, timedelta
            old_ts = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d %H:%M:%S")
            le._append_jsonl(le.advice_log_path, {
                "advice_id": "20990101-001", "ts": old_ts, "client_id": "c3",
                "kind": "other", "target": "110022", "action": "持有",
                "confidence": 0.6, "reasons": [], "context": {},
                "params_used": {}, "nav_at_log": None})
            r = le.auto_evaluate_pending()
            assert r["evaluated"] == 0
            assert r["skipped_no_nav"] >= 1 or r["skipped_network"] >= 1
        finally:
            os.environ.pop("FUND_ADVISOR_LEARNING_DIR", None)
    print("  ✅ test_learning_auto_evaluate_offline (离线优雅跳过)")


# ─── review_engine ────────────────────────────────────────
def test_review_engine_import_and_format():
    """review_engine 可导入；format_review 渲染假数据不报错"""
    from analysis.review_engine import ReviewEngine, format_review
    fake = {
        "type": "weekly", "client_id": "demo",
        "dashboard": [
            {"维度": "总收益", "值": 2.5, "单位": "%", "灯号": "🟢"},
            {"维度": "年化收益", "值": 6.0, "单位": "%", "灯号": "🟢"},
            {"维度": "最大回撤", "值": -5.0, "单位": "%", "灯号": "🟢"},
            {"维度": "夏普比率", "值": 1.1, "单位": "", "灯号": "🟢"},
            {"维度": "配置漂移", "值": 3.0, "单位": "%", "灯号": "🟢"},
            {"维度": "偏离提示", "值": 0, "单位": "项", "灯号": "🟢"},
        ],
        "health": "🟢 组合健康", "highlights": ["演示要点"],
        "degraded": True, "degraded_note": "演示降级",
        "reviewed_at": "2026-01-01 09:00:00", "next_review": "2026-01-08",
    }
    text = format_review(fake)
    assert "周度检视" in text and "🟢" in text and "2026-01-08" in text
    fake_m = dict(fake, type="monthly", perf_table={"本月": {"return": 1.2, "mdd": -2.0}},
                  attribution={"配置贡献": -0.5, "选基贡献": 1.0, "时机贡献": 0.7},
                  alerts=[], suggestions=["按季度检视即可"])
    text_m = format_review(fake_m)
    assert "月度检视" in text_m and "归因" in text_m
    err = format_review({"error": "测试错误"})
    assert "❌" in err
    print("  ✅ test_review_engine_import_and_format")


if __name__ == "__main__":
    test_perf_metrics_basic()
    test_perf_metrics_mdd_known()
    test_perf_metrics_edge_and_benchmark()
    test_asset_allocator_questionnaire()
    test_asset_allocator_saa()
    test_asset_allocator_optimizer_and_suitability()
    test_asset_allocator_plan()
    test_learning_engine_full_cycle()
    test_learning_hit_direction()
    test_learning_auto_evaluate_offline()
    test_review_engine_import_and_format()
    print("\n  🎉 All v7.0 tests passed!")
