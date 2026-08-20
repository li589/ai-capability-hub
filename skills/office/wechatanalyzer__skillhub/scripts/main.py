#!/usr/bin/env python3
"""
微信聊天分析助手 - 主入口

完整保留 v1.2.0 CLI 命令（analyze/report/schedule/serve/calendar），
v2.0.0 命令（analyze-v2/predict-v2/graph-stats），
v2.3.0 新增时间感知对话预测与回复时机提示；v2.1.0 新增 demo/doctor/report-v2 + 交互式向导。
v2.5.0 接入友好错误提示（friendly_errors）、predict-v2 --seed 可复现预测、版本号统一。

v2.1.0 新增特性：
- 修复 graph-stats 崩溃（补齐 mirofish/ 本地图谱包）
- 输入文件编码自动检测（utf-8-sig → utf-8 → gb18030）
- 大五人格归一化校准（避免小样本饱和 100%）
- MBTI 稳定性低时给出中文提示
- 分析进度实时反馈
- analyze-v2 支持 --export JSON / --html 单文件报告
- report-v2 从最近一次分析结果生成离线 HTML 报告
- demo 一键体验 / doctor 环境自检
- 无参数启动进入交互式向导
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# 禁用 .pyc 生成（避免上传/打包时混入二进制缓存）
sys.dont_write_bytecode = True


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# v2.5.0：版本号单一来源
from core.version import __version__


def _safe_emoji(text: str) -> str:
    """Replace emoji with plain-text for GBK terminal compatibility."""
    encoding = sys.stdout.encoding or 'utf-8'
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    replacements = {
        '📋': '[规则]', '📊': '[统计]', '🧠': '[MBTI]', '🔬': '[大五]',
        '💬': '[情感]', '⚠️': '[预警]', '🔴': '[高]', '🟡': '[中]',
        '🟢': '[低]', '⚪': '[-]', '💡': '[应对]', '🔮': '[预测]',
        '🎯': '[场景]', '💕': '[恋爱]', '💼': '[工作]', '👥': '[社交]',
        '📌': '[重要]', '📝': '[摘要]', '📅': '[日程]', '✅': '[OK]',
        '📈': '[上升]', '📉': '[下降]', '➡️': '->', '🌟': '*',
        '█': '#', '░': '.', '🤖': '[AI]', '🧪': '[测试]', '📚': '[RAG]',
        '🐟': '[MiroFish]', '🧬': '[图谱]',
    }
    for emoji, alt in replacements.items():
        text = text.replace(emoji, alt)
    return text.encode(encoding, errors='replace').decode(encoding, errors='replace')


# ============== v1.2.0 兼容层 ==============

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_llm_configured(config):
    """检查 LLM 是否已配置"""
    llm = config.get('llm', {})
    enabled = llm.get('enabled')
    if enabled is None:
        return bool(llm.get('api_key', '').strip())
    return bool(enabled) and bool(llm.get('api_key', '').strip())


# ============== v1.2.0 命令（保留向后兼容）==============

def cmd_analyze(args):
    """v1.2.0 analyze 命令 - 调用旧 TextAnalyzer"""
    print(_safe_emoji("📋 使用 v1.2.0 分析模式（向后兼容）"))
    print(_safe_emoji("💡 提示：尝试 `analyze-v2` 体验 v2.0.0 新特性（jieba/否定识别/RAG/多智能体）\n"))

    from scripts.text_analyzer import TextAnalyzer
    from scripts.data_manager import DataManager
    from scripts.calendar_manager import CalendarManager
    from scripts.file_importer import MultiFormatImporter

    config = load_config()
    dm = DataManager(config)
    analyzer = TextAnalyzer(config)
    cm = CalendarManager(config)

    messages = _load_messages(args, config, dm)
    if not messages:
        return None

    msg_count = len(messages)
    if msg_count > 500:
        print(f"提示：共 {msg_count} 条消息，数量较多，分析可能需要较长时间。")
    print(f"\n已解析 {msg_count} 条消息，开始分析...")

    use_llm = is_llm_configured(config)

    if use_llm:
        print("[AI增强模式] 检测到LLM API配置，尝试AI增强分析...")
        try:
            from scripts.llm_analyzer import enhance_results
            rule_results = analyzer.analyze(messages)
            results = enhance_results(rule_results, messages, config)
            results['ai_enhanced'] = True
            print("[OK] LLM增强分析完成")
        except Exception as e:
            print(f"[警告] LLM 分析失败（{e}），已切换到本地规则分析")
            results = analyzer.analyze(messages)
            results['ai_enhanced'] = False
    else:
        print("[规则分析模式] LLM未配置，使用本地规则分析")
        results = analyzer.analyze(messages)
        results['ai_enhanced'] = False

    chat_id = dm.save_analysis(results)
    events = cm.extract_events_from_messages(messages, chat_id)
    _display_v1_results(results, events, messages, config)
    return chat_id


def _load_messages(args, config, dm) -> list:
    """从不同来源加载消息（粘贴/文件/导入）"""
    if args.paste:
        print("\n请粘贴聊天记录内容，完成后输入 END（单独一行）后回车：")
        print('(支持从微信直接复制粘贴，只需包含"发送者: 内容"格式)\n')
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == "END":
                break
            lines.append(line)
        text = "\n".join(lines)
        if not text.strip():
            print("错误：未输入任何内容")
            return None
        return dm.parse_text_input(text)

    elif args.input:
        # v2.1.0：自动检测文件编码（utf-8-sig → utf-8 → gb18030）
        from core.utils import read_text_auto
        try:
            text, used_enc = read_text_auto(args.input)
        except (FileNotFoundError, ValueError) as e:
            print(f"错误：{e}")
            return None
        if used_enc not in ("utf-8", "utf-8-sig"):
            print(f"提示：检测到文件编码为 {used_enc}，已自动转换")
        return dm.parse_text_input(text)

    elif args.file:
        from scripts.file_importer import MultiFormatImporter
        importer = MultiFormatImporter(config)
        messages = importer.import_file(args.file)
        if not messages:
            print(f"错误：无法解析文件 {args.file}")
            return None
        print(f"已导入 {len(messages)} 条消息")
        return messages

    print("错误：未指定输入（使用 --paste/--input/--file）")
    return None


def _display_v1_results(results, events, messages, config):
    """v1.2.0 结果展示"""
    stats = results.get('stats', {})
    mbti = results.get('mbti', {})
    big_five = results.get('big_five', {})
    sentiment = results.get('sentiment', {})
    prediction = results.get('prediction', {})
    risks = results.get('risks', {})

    print(f"\n{'='*55}")
    print(_safe_emoji("   微信聊天分析报告"))
    print(f"{'='*55}")

    print(f"\n[统计] 聊天统计")
    print(f"  总消息数: {stats.get('total_messages', 0)}")
    print(f"  对方消息: {stats.get('other_messages', 0)}")
    print(f"  你的消息: {stats.get('self_messages', 0)}")

    if mbti and mbti.get('type') and mbti.get('type') != '未知':
        print(f"\n[MBTI] {mbti.get('type')} - {mbti.get('name', '未知')} (置信度 {mbti.get('confidence', 0):.0f}%)")

    if big_five and big_five.get('openness', 0) > 0:
        print(f"\n[大五] 大五人格分析")
        labels = big_five.get('labels', {
            'openness': '开放性', 'conscientiousness': '尽责性',
            'extraversion': '外向性', 'agreeableness': '宜人性', 'neuroticism': '神经质'
        })
        for key in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            val = big_five.get(key, 50)
            bar = '#' * int(val / 10) + '.' * (10 - int(val / 10))
            print(f"  {labels[key]}: [{bar}] {val:.0f}%")

    if sentiment:
        trend_map = {'up': '[上升]', 'down': '[下降]', 'stable': '[稳定]'}
        print(f"\n[情感] 趋势: {trend_map.get(sentiment.get('trend', 'stable'), '')}")

    if risks and not risks.get('no_risk_detected'):
        print(f"\n[风险预警]")
        for risk_type, data in risks.items():
            if risk_type == 'no_risk_detected':
                continue
            level = data.get('risk_level', 'low')
            print(f"  [{level.upper()}] {risk_type}: {data.get('description', '')}")

    if prediction and prediction.get('next_message'):
        print(f"\n[预测] 对方可能说:「{prediction.get('next_message', '')}」")

    if events:
        print(f"\n[日程] 发现 {len(events)} 个事件")
        for ev in events[:3]:
            print(f"  - {ev.get('title', '')} ({ev.get('event_date', '')[:10]})")

    print(f"\n{'='*55}")


def cmd_report(args):
    """v1.2.0 报告生成命令"""
    from scripts.report_generator import ReportGenerator
    from scripts.data_manager import DataManager

    config = load_config()
    dm = DataManager(config)

    chat_id = args.chat_id
    if not chat_id:
        results = dm.get_latest_analysis()
        if results:
            chat_id = results.get('chat_id')
        else:
            print("错误：没有找到可用的分析结果，请先运行 analyze 命令")
            return

    results = dm.get_analysis(chat_id)
    if not results:
        print(f"错误：找不到指定的分析结果 {chat_id}")
        return

    generator = ReportGenerator(config)
    output_path = generator.generate(
        results=results,
        report_type=args.report_type,
        period=args.period
    )
    print(f"报告已生成: {output_path}")
    return output_path


def cmd_schedule(args):
    """v1.2.0 定时任务管理"""
    from scripts.scheduler import SchedulerManager

    config = load_config()
    scheduler = SchedulerManager(config)

    if args.list:
        jobs = scheduler.list_jobs()
        if not jobs:
            print("暂无定时任务")
        else:
            print("=== 定时任务列表 ===")
            for job in jobs:
                print(f"  {job['id']}: {job['name']} ({job['period']})")
    elif args.add:
        scheduler.add_job(
            name=args.name,
            period=args.period,
            chat_id=args.chat_id,
            report_type=args.report_type
        )
        print(f"已添加定时任务: {args.name}")
    elif args.remove:
        scheduler.remove_job(args.name)
        print(f"已删除定时任务: {args.name}")
    elif args.enable:
        scheduler.enable_job(args.name)
        print(f"已启用定时任务: {args.name}")
    elif args.disable:
        scheduler.disable_job(args.name)
        print(f"已禁用定时任务: {args.name}")


def cmd_serve(args):
    """v1.2.0 Web 服务启动"""
    config = load_config()
    # v2.5.0：优先用 config.json 的 server.default_port（此前硬编码 5000 忽略配置）
    port = args.port or config.get('server', {}).get('default_port', 5000)

    use_llm = is_llm_configured(config)
    if use_llm:
        print(_safe_emoji("🤖 [AI模式] LLM API 已配置"))

    from scripts.web_server import create_app
    app = create_app(config)
    print(f"启动Web服务: http://localhost:{port}")
    print("按 Ctrl+C 停止")
    debug_mode = config.get('server', {}).get('debug', False)
    app.run(host='0.0.0.0', port=port, debug=debug_mode)


def cmd_calendar(args):
    """v1.2.0 日历事件"""
    from scripts.calendar_manager import CalendarManager

    config = load_config()
    cm = CalendarManager(config)

    if args.upcoming:
        events = cm.get_upcoming_events(args.days)
        print(f"=== 即将到来的 {len(events)} 个事件 ===")
        for event in events:
            imp = event.get('importance', 'medium').upper()
            print(f"  [{imp}] {event['title']} - {event['event_date'][:10]}")
    elif args.list:
        events = cm.get_events(event_type=args.type, importance=args.importance)
        print(f"=== 所有 {len(events)} 个事件 ===")
        for event in events:
            imp = event.get('importance', 'medium').upper()
            print(f"  [{imp}] {event['title']} - {event['event_date'][:10]} ({event.get('event_type', '')})")
    else:
        print("请使用 --list 或 --upcoming")


# ============== v2.0.0 新命令 ==============

def _make_progress_callback():
    """v2.1.0 分析进度回调：[i/N] name ... 完成 (0.12s)"""
    def callback(event, name, index, total, elapsed):
        if event == "start":
            print(f"  [{index}/{total}] {name} ... ", end="", flush=True)
        elif event == "done":
            print(_safe_emoji(f"完成 ({elapsed:.2f}s) ✅"))
        elif event == "skip":
            print(_safe_emoji("跳过（样本不足或校验未通过）"))
        elif event == "error":
            print(_safe_emoji(f"失败 ({elapsed:.2f}s) ⚠️"))
    return callback


def _v2_message_meta(messages) -> dict:
    """消息统计元数据（用于导出/HTML 报告）"""
    from core.message import SenderRole
    self_count = sum(1 for m in messages if m.is_self())
    other_count = sum(1 for m in messages if m.is_other())
    timestamps = [m.timestamp for m in messages if m.timestamp]
    meta = {
        "total_messages": len(messages),
        "self_messages": self_count,
        "other_messages": other_count,
    }
    if len(timestamps) >= 2:
        meta["time_span"] = {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
        }
    return meta


def cmd_analyze_v2(args):
    """v2 分析命令 - 使用模块化分析器"""
    print(_safe_emoji(f"🤖 [v{__version__}] 模块化分析引擎"))
    print(_safe_emoji("    jieba分词 + 否定识别 + 程度副词 + 反讽检测 + 风险预警\n"))

    from core.message import messages_from_legacy
    from analyzers import create_default_registry
    from scripts.data_manager import DataManager
    from scripts.calendar_manager import CalendarManager

    config = load_config()
    dm = DataManager(config)
    cm = CalendarManager(config)

    raw_messages = _load_messages(args, config, dm)
    if not raw_messages:
        return None

    # 转换为 v2 Message 对象
    messages = messages_from_legacy(raw_messages)

    msg_count = len(messages)
    if msg_count > 500:
        print(f"提示：共 {msg_count} 条消息，建议单次分析不超过 500 条。")
    print(f"\n已解析 {msg_count} 条消息，运行 v2 分析器...")

    # 创建分析器注册中心
    registry = create_default_registry(config)
    print(f"已注册 {len(registry.list())} 个分析器: {', '.join(registry.list())}")

    # 运行所有分析器（v2.1.0：带进度反馈）
    results = registry.run_all(messages, progress_callback=_make_progress_callback())

    # 显示结果
    _display_v2_results(results, messages, cm, raw_messages, dm, config)

    # 可选：导出 JSON
    if getattr(args, "export", None):
        export_path = args.export
        try:
            payload = {
                "version": __version__,
                "generated_at": datetime.now().isoformat(),
                "meta": _v2_message_meta(messages),
                "results": {k: v.to_dict() for k, v in results.items()},
            }
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(_safe_emoji(f"\n✅ 分析结果已导出: {export_path}"))
        except OSError as e:
            print(f"\n错误：导出失败（{e}）")

    # 可选：生成单文件 HTML 报告
    if getattr(args, "html", None):
        try:
            from scripts.v2_report_generator import V2ReportGenerator
            generator = V2ReportGenerator(config)
            out = generator.generate(
                results={k: v.to_dict() for k, v in results.items()},
                meta=_v2_message_meta(messages),
                output_path=args.html,
            )
            print(_safe_emoji(f"✅ HTML 报告已生成: {out}"))
        except Exception as e:
            print(f"错误：HTML 报告生成失败（{e}）")

    # 可选：构建 MiroFish 图谱
    if config.get("mirofish", {}).get("enabled", False):
        try:
            from mirofish.core.zep_local import ZepLocalGraph
            graph = ZepLocalGraph()
            count = graph.build_from_messages(messages)
            stats = graph.get_stats()
            print(_safe_emoji(f"\n🧬 [MiroFish] 已构建本地图谱：{count} 条记忆 / {stats['entities']} 实体 / {stats['relations']} 关系"))
        except Exception as e:
            print(f"[MiroFish] 图谱构建失败: {e}")

    return results


def _display_v2_results(results: dict, messages, cm, raw_messages, dm, config):
    """v2 结果展示（统一格式）"""
    print(f"\n{'='*60}")
    print(_safe_emoji(f"   微信聊天分析报告 v{__version__}"))
    print(f"{'='*60}")

    # MBTI
    if "mbti" in results:
        mbti = results["mbti"].details
        # v2.5.0：分析器失败时 run_all 返回 {"error": ...} 错误桩，
        # 之前直接 mbti['type'] 会 KeyError 崩溃，这里降级展示。
        if "type" in mbti and "name" in mbti:
            print(_safe_emoji(f"\n🧠 [MBTI] {mbti['type']} - {mbti['name']}"))
            print(f"  置信度: {results['mbti'].confidence:.1f}%")
            print(f"  特征: {mbti.get('dim_description', '')}")
            if "stability" in mbti:
                stability_pct = mbti['stability'] * 100
                print(f"  稳定性: {stability_pct:.0f}%")
                # v2.1.0：稳定性低时给出可解释提示
                if stability_pct < 50:
                    print("  提示: 样本较少或特征不明显，结果仅供参考")
        elif "error" in mbti:
            print(_safe_emoji("\n🧠 [MBTI] 分析失败，已跳过"))
            print(f"   原因: {mbti['error']}")

    # 大五
    if "bigfive" in results:
        bf = results["bigfive"].details
        print(_safe_emoji("\n🔬 [大五] OCEAN 人格分析"))
        for item in bf.get("radar_data", []):
            val = item["value"]
            bar = '#' * int(val / 10) + '.' * (10 - int(val / 10))
            print(f"  {item['label']}: [{bar}] {val:.0f}%")

    # 情感
    if "sentiment" in results:
        sent = results["sentiment"].details
        trend_map = {"up": "[上升]", "down": "[下降]", "stable": "[稳定]"}
        print(_safe_emoji(f"\n💬 [情感] 趋势: {trend_map.get(sent.get('trend', 'stable'), '')}"))
        print(f"  正面: {sent.get('positive', 0):.1f}% / 负面: {sent.get('negative', 0):.1f}% / 中性: {sent.get('neutral', 0):.1f}%")
        if sent.get("irony_count", 0) > 0:
            print(f"  [v2.0.0] 检测到 {sent['irony_count']} 条反讽")
        ew = sent.get("emotional_words", {})
        if ew.get("positive"):
            print(f"  正面词: {', '.join(ew['positive'][:5])}")
        if ew.get("negative"):
            print(f"  负面词: {', '.join(ew['negative'][:5])}")

    # 风险
    if "risk" in results:
        risk = results["risk"].details
        print(_safe_emoji("\n⚠️ [风险]"))
        if risk.get("overall_level") == "low" and not risk.get("risks"):
            print(_safe_emoji("  ✅ 未检测到明显风险"))
        else:
            for risk_type, data in risk.get("risks", {}).items():
                level = data.get("level", "low")
                fp = "（可能误报）" if data.get("false_positive_likely") else ""
                print(f"  [{level.upper()}] {risk_type} {fp}")
                print(f"    {data.get('description', '')}")
                print(f"    命中 {data.get('keyword_count', 0)} 次: {', '.join(data.get('matched_keywords', [])[:5])}")
                if data.get("response_strategies", {}).get("diplomatic"):
                    print(f"    [建议]: {data['response_strategies']['diplomatic'][0]}")

    # 场景
    if "scenario" in results:
        scen = results["scenario"].details
        scene_map = {"romantic": "[恋爱]", "work": "[工作]", "social": "[社交]", "important": "[重要]"}
        print(_safe_emoji(f"\n🎯 [场景] 主场景: {scene_map.get(scen.get('primary', 'social'), '')}"))
        for item in scen.get("sorted", [])[:3]:
            print(f"    {item['scenario']}: {item['weight']}")

    # 对话模式
    if "pattern" in results:
        pat = results["pattern"].details
        print(_safe_emoji("\n📊 [模式] 对话模式分析"))
        if pat.get("initiation"):
            init = pat["initiation"]
            print(f"  主动发起: 我 {init.get('self_pct', 0):.0f}% / TA {init.get('other_pct', 0):.0f}%")
        if pat.get("reply_speed"):
            rs = pat["reply_speed"]
            print(f"  平均回复: {rs.get('avg_seconds', 0):.0f} 秒")
            print(f"  快速回复 (<1分钟): {rs.get('fast_replies', 0)}")
            print(f"  慢速回复 (>1小时): {rs.get('slow_replies', 0)}")
        if pat.get("duration_days") is not None:
            print(f"  聊天跨度: {pat['duration_days']} 天")

    # 日历事件
    try:
        chat_id = dm.save_analysis({"v2_results": {k: v.to_dict() for k, v in results.items()}})
        events = cm.extract_events_from_messages(raw_messages, chat_id)
        if events:
            print(_safe_emoji(f"\n📅 [日程] 发现 {len(events)} 个事件"))
            for ev in events[:3]:
                print(f"  - {ev.get('title', '')} ({ev.get('event_date', '')[:10]})")
    except Exception:
        pass

    # v2.1.0：一句话总结（规则生成，放在分隔线内）
    try:
        from scripts.v2_report_generator import generate_v2_summary
        summary = generate_v2_summary({k: v.to_dict() for k, v in results.items()})
        if summary:
            print(f"\n{'='*60}")
            print(_safe_emoji(f"📝 一句话总结: {summary}"))
    except Exception:
        pass

    print(f"\n{'='*60}")


def cmd_predict_v2(args):
    """v2 三层融合预测"""
    print(_safe_emoji(f"🔮 [v{__version__}] 多层集成预测器"))
    print(_safe_emoji("    Rule + RAG + MiroFish 三层融合\n"))

    from core.message import messages_from_legacy
    from core.predictor_base import PredictionContext
    from analyzers import create_default_registry
    from predictors import create_default_ensemble
    from scripts.data_manager import DataManager

    config = load_config()
    dm = DataManager(config)

    raw_messages = _load_messages(args, config, dm)
    if not raw_messages:
        return

    messages = messages_from_legacy(raw_messages)

    # 1. 先分析得到 MBTI / BigFive / Sentiment / Scenario
    print("[1/3] 运行分析器...")
    registry = create_default_registry(config)
    analysis_results = registry.run_all(messages, progress_callback=_make_progress_callback())

    mbti_type = analysis_results["mbti"].details.get("type") if "mbti" in analysis_results else None
    big_five = analysis_results["bigfive"].details if "bigfive" in analysis_results else None
    sentiment = analysis_results["sentiment"].details if "sentiment" in analysis_results else None
    scenario = analysis_results["scenario"].details.get("primary", "social") if "scenario" in analysis_results else "social"

    print(f"  MBTI: {mbti_type or '未知'}")
    print(f"  场景: {scenario}")

    # 2. 构建预测上下文
    print("\n[2/3] 构建预测上下文...")
    context = PredictionContext(
        messages=messages,
        mbti=mbti_type,
        big_five=big_five,
        sentiment=sentiment,
        scenario=scenario,
        recent_window=3,
    )

    # 3. 运行集成预测
    print("\n[3/3] 运行三层集成预测...")

    # v2.5.0：--seed 可复现预测（MiroFish 随机选择确定性化）
    seed = getattr(args, "seed", None)
    if seed is not None:
        config.setdefault("mirofish", {})["seed"] = seed
        print(f"  [随机种子] {seed}（预测结果可复现）")

    ensemble = create_default_ensemble(config)
    print(f"  已加载预测器: {', '.join(ensemble.list_predictors())}")

    result = ensemble.predict(context)

    print(f"\n{'='*60}")
    print(_safe_emoji("   对话预测结果"))
    print(f"{'='*60}")
    print(f"\n[最佳预测] 置信度 {result.top_prediction.confidence*100:.1f}%")
    print(f"  策略: {result.top_prediction.strategy}")
    print(f"  内容: 「{result.top_prediction.text}」")
    if result.top_prediction.rationale:
        print(f"  依据: {result.top_prediction.rationale}")

    if result.alternatives:
        print(f"\n[备选预测] (共 {len(result.alternatives)} 条)")
        for i, alt in enumerate(result.alternatives, 1):
            print(f"  {i}. [{alt.confidence*100:.0f}%] ({alt.strategy}) 「{alt.text}」")

    if result.metadata.get("predictors_used"):
        print(f"\n[使用预测器] {', '.join(result.metadata['predictors_used'])}")
    if result.metadata.get("total_candidates"):
        print(f"[候选总数] {result.metadata['total_candidates']}")

    timing = result.context.get("timing") or result.metadata.get("timing")
    if timing:
        urgency_label = {
            "immediate": "立即回复",
            "soon": "尽快回复",
            "today": "今天内回复",
            "stale": "隔太久，先主动找回联系",
            "unknown": "时间未知",
        }.get(timing.get("urgency", ""), timing.get("urgency", "未知"))
        age = timing.get("last_message_age_minutes")
        age_text = f"，距最后消息约 {age:.0f} 分钟" if age is not None else ""
        print(f"[回复时机] {urgency_label}{age_text}")


def cmd_graph_stats(args):
    """v2 MiroFish 图谱统计"""
    print(_safe_emoji("🧬 [v2.1.0] MiroFish 本地图谱统计\n"))

    from mirofish.core.zep_local import ZepLocalGraph
    graph = ZepLocalGraph()
    stats = graph.get_stats()

    print(f"实体数: {stats['entities']}")
    print(f"关系数: {stats['relations']}")
    print(f"记忆数: {stats['memories']}")

    if stats['entities'] > 0:
        graph_data = graph.get_graph()
        print(f"\n[实体 Top 10]")
        # 按出现频率排
        from collections import Counter
        ent_counter = Counter(e['name'] for e in graph_data['entities'])
        for name, count in ent_counter.most_common(10):
            print(f"  {name}: {count}")

        if graph_data['relations']:
            print(f"\n[关系 Top 10]")
            rel_counter = Counter()
            for r in graph_data['relations']:
                rel_counter[r['type']] += 1
            for rel_type, count in rel_counter.most_common(10):
                print(f"  {rel_type}: {count}")


# ============== v2.1.0 新命令 ==============

def cmd_report_v2(args):
    """v2.1.0 报告命令 - 从最近一次 analyze-v2 结果生成离线 HTML 报告"""
    print(_safe_emoji("📊 [v2.1.0] 生成单文件 HTML 报告\n"))

    from scripts.data_manager import DataManager
    from scripts.v2_report_generator import V2ReportGenerator

    config = load_config()
    dm = DataManager(config)

    latest = dm.get_latest_analysis()
    if not latest or "v2_results" not in latest:
        print("未找到 v2 分析结果。")
        print(_safe_emoji("💡 请先运行: python scripts/main.py analyze-v2 --input <文件> "
                          "（或 --paste），再执行 report-v2"))
        return None

    generator = V2ReportGenerator(config)
    output_path = generator.generate(
        results=latest["v2_results"],
        meta={"total_messages": None, "chat_id": latest.get("chat_id")},
        output_path=getattr(args, "output", None),
    )
    print(_safe_emoji(f"✅ HTML 报告已生成: {output_path}"))
    return output_path


def cmd_demo(args):
    """v2.1.0 一键演示 - 分析内置示例数据并生成 HTML 报告"""
    print(_safe_emoji("🌟 [v2.1.0] 一键演示：使用内置示例聊天记录\n"))

    sample_path = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_chat.txt"
    if not sample_path.exists():
        print(f"错误：示例文件不存在: {sample_path}")
        return None

    # 复用 analyze-v2 全流程（终端展示 + 进度反馈）
    demo_args = argparse.Namespace(
        paste=False, input=str(sample_path), file=None,
        export=None, html=None,
    )
    results = cmd_analyze_v2(demo_args)
    if not results:
        return None

    # 生成 HTML 报告到 data/reports/
    from scripts.v2_report_generator import V2ReportGenerator
    from core.message import messages_from_legacy
    from core.utils import read_text_auto
    from scripts.data_manager import DataManager

    config = load_config()
    dm = DataManager(config)
    text, _enc = read_text_auto(sample_path)
    messages = messages_from_legacy(dm.parse_text_input(text))

    generator = V2ReportGenerator(config)
    output_path = generator.generate(
        results={k: v.to_dict() for k, v in results.items()},
        meta=_v2_message_meta(messages),
    )
    print(_safe_emoji(f"\n✅ 演示完成！HTML 报告已生成: {output_path}"))
    print(_safe_emoji("💡 用浏览器打开该文件即可查看完整可视化报告（离线可用）"))
    return output_path


def cmd_doctor(args):
    """v2.1.0 环境自检"""
    import platform

    print(_safe_emoji("🧪 [v2.1.0] 环境自检\n"))

    ok_mark = _safe_emoji("✅")
    warn_mark = _safe_emoji("⚠️")
    problems = []   # (问题描述, 修复建议)

    def check(label, ok, note="", fix=""):
        mark = ok_mark if ok else warn_mark
        suffix = f" - {note}" if note else ""
        print(f"  {mark} {label}{suffix}")
        if not ok and fix:
            problems.append((label, fix))

    # 1. Python 版本
    py_ver = platform.python_version()
    py_ok = sys.version_info >= (3, 8)
    check(f"Python 版本: {py_ver}", py_ok,
          "" if py_ok else "需要 >= 3.8",
          "请升级 Python 到 3.8 及以上版本")

    # 2. 必需依赖
    try:
        import jieba  # noqa: F401
        check("jieba（必需，精准分词）", True)
    except ImportError:
        check("jieba（必需，精准分词）", False, "未安装",
              "pip install jieba")

    # 3. v1 功能依赖（可选）
    for mod, pkg in [("flask", "flask"), ("docx", "python-docx"), ("pptx", "python-pptx")]:
        try:
            __import__(mod)
            check(f"{pkg}（v1 功能）", True)
        except ImportError:
            check(f"{pkg}（v1 功能）", False, "未安装，v1 报告/Web 功能不可用",
                  f"pip install {pkg}")

    # 4. RAG 可选依赖
    for mod, pkg in [("sentence_transformers", "sentence-transformers"),
                     ("chromadb", "chromadb")]:
        try:
            __import__(mod)
            check(f"{pkg}（RAG 可选）", True)
        except ImportError:
            check(f"{pkg}（RAG 可选）", False, "未安装，RAG 预测自动降级",
                  f"pip install -r requirements-rag.txt")

    # 5. config.json 可解析
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    try:
        config = load_config()
        check("config.json 可解析", True, f"version={config.get('version', '?')}")
    except Exception as e:
        config = {}
        check("config.json 可解析", False, str(e),
              "检查 config.json 是否为合法 JSON")

    # 6. data/ 目录可写
    data_dir = Path(__file__).resolve().parent.parent / config.get("data_dir", "data")
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".doctor_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        check(f"data/ 目录可写（{data_dir}）", True)
    except OSError as e:
        check(f"data/ 目录可写（{data_dir}）", False, str(e),
              "检查目录权限或以有权限的用户运行")

    # 7. stdout 编码
    out_enc = sys.stdout.encoding or "unknown"
    enc_ok = out_enc.lower() not in ("unknown", "ascii")
    check(f"终端输出编码: {out_enc}", enc_ok,
          "" if enc_ok else "可能出现乱码",
          "Windows 可执行 chcp 65001 切换为 UTF-8 代码页")

    # 汇总
    print(f"\n{'='*50}")
    if not problems:
        print(_safe_emoji("✅ 环境自检全部通过，可以正常使用"))
    else:
        print(_safe_emoji(f"⚠️ 发现 {len(problems)} 个待处理项，修复建议："))
        for i, (label, fix) in enumerate(problems, 1):
            print(f"  {i}. [{label}] {fix}")
    print(f"{'='*50}")
    return len(problems)


def _run_interactive_wizard():
    """v2.1.0 交互式向导（无参数启动时进入）"""
    print(_safe_emoji("🌟 欢迎使用微信聊天分析助手 v2.1.0"))
    print("完全本地运行，零数据外传。")
    print(_safe_emoji("💡 提示: 使用 -h 查看全部命令，或运行 demo 一键体验示例数据\n"))

    print("请粘贴聊天记录（每行一条，格式「发送者: 内容」），")
    print("完成后输入 END（单独一行）并回车：\n")

    lines = []
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消，再见！")
            return
        if line.strip() == "END":
            break
        lines.append(line)

    text = "\n".join(lines)
    if not text.strip():
        print("未输入任何内容，已退出。")
        print(_safe_emoji("💡 想快速体验？运行: python scripts/main.py demo"))
        return

    # 直接复用 analyze-v2 的分析与展示逻辑
    from core.message import messages_from_legacy
    from analyzers import create_default_registry
    from scripts.data_manager import DataManager
    from scripts.calendar_manager import CalendarManager

    config = load_config()
    dm = DataManager(config)
    cm = CalendarManager(config)

    raw_messages = dm.parse_text_input(text)
    if not raw_messages:
        print("未能从输入中解析出消息，请检查格式（应为「发送者: 内容」）。")
        return

    messages = messages_from_legacy(raw_messages)
    print(f"\n已解析 {len(messages)} 条消息，开始分析...")
    registry = create_default_registry(config)
    results = registry.run_all(messages, progress_callback=_make_progress_callback())
    _display_v2_results(results, messages, cm, raw_messages, dm, config)

    # 询问是否生成 HTML 报告
    try:
        answer = input(_safe_emoji("\n是否生成 HTML 可视化报告？(y/N) ")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消报告生成，再见！")
        return
    if answer in ("y", "yes"):
        from scripts.v2_report_generator import V2ReportGenerator
        generator = V2ReportGenerator(config)
        output_path = generator.generate(
            results={k: v.to_dict() for k, v in results.items()},
            meta=_v2_message_meta(messages),
        )
        print(_safe_emoji(f"✅ HTML 报告已生成: {output_path}"))
        print(_safe_emoji("💡 用浏览器打开该文件即可查看（离线可用）"))
    else:
        print("好的，已跳过报告生成。")


def cmd_version(args):
    """显示版本信息"""
    print(f"微信聊天分析助手 v{__version__}")
    print(f"\nv{__version__} 新特性:")
    print(_safe_emoji("  🛡 健壮性升级：非法转义修复 / Python 3.15 日期解析兼容 / 裸 except 收紧"))
    print(_safe_emoji("  🧪 全覆盖编译烟囱测试（全部 .py 编译+警告升错误 / 裸 except 防回归 / 版本一致性）"))
    print(_safe_emoji("  🧹 clean.py --check 上传前残留检查（退出码 1=有二进制残留）"))
    print(_safe_emoji("  ✅ Python 3.11 / 3.14 双版本零警告，329 测试全过"))
    print("\nv2.3.0 新特性:")
    print(_safe_emoji("  🔮 时间感知对话预测（消息新鲜度/时间段/周末/连续对话节奏）"))
    print(_safe_emoji("  ⏱ predict-v2 输出回复时机提示（立即/尽快/今天内/隔太久找回联系）"))
    print("\nv2.1.0 新特性:")
    print(_safe_emoji("  🧬 补齐 mirofish/ 本地图谱包（修复 graph-stats 崩溃）"))
    print(_safe_emoji("  📄 输入文件编码自动检测（utf-8-sig / utf-8 / gb18030）"))
    print(_safe_emoji("  📊 大五人格归一化校准（小样本不再轻易饱和 100%）"))
    print(_safe_emoji("  🧠 MBTI 稳定性低时给出中文提示"))
    print(_safe_emoji("  📈 分析进度实时反馈（[i/6] xxx ... 完成）"))
    print(_safe_emoji("  💾 analyze-v2 支持 --export JSON 导出"))
    print(_safe_emoji("  🌐 analyze-v2 --html / report-v2 单文件离线 HTML 报告"))
    print(_safe_emoji("  🌟 demo 一键体验 / doctor 环境自检"))
    print(_safe_emoji("  🧭 无参数启动进入交互式向导"))
    print(_safe_emoji("  📝 终端报告末尾自动生成一句话总结"))
    print(_safe_emoji("  🔮 predict-v2 备选预测按规范化文本去重"))
    print("\nv2.0.0 特性:")
    print(_safe_emoji("  🧠 jieba 精准分词（替代正则分词）"))
    print(_safe_emoji("  💬 否定识别（修复'我不开心'误判）"))
    print(_safe_emoji("  🎭 反讽检测（虽然...但是...）"))
    print(_safe_emoji("  📊 MBTI 新置信度算法（维度差距+样本量）"))
    print(_safe_emoji("  📚 本地 RAG 引擎（sentence-transformers + ChromaDB）"))
    print(_safe_emoji("  🐟 MiroFish 多智能体（8 Agent × N 轮博弈）"))
    print(_safe_emoji("  🔮 三层集成预测（Rule + RAG + MiroFish）"))
    print("\n保留 v1.2.0 兼容命令: analyze, report, schedule, serve, calendar")


def main():
    parser = argparse.ArgumentParser(
        description=f"微信聊天分析助手 v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  python scripts/main.py                        # 交互式向导（v2.1.0）
  python scripts/main.py demo                   # 一键体验示例数据（v2.1.0）
  python scripts/main.py doctor                 # 环境自检（v2.1.0）
  python scripts/main.py analyze-v2 --paste     # 粘贴分析（带进度反馈）
  python scripts/main.py analyze-v2 --input 1.txt --export result.json
  python scripts/main.py analyze-v2 --input 1.txt --html report.html
  python scripts/main.py report-v2              # 用最近结果生成 HTML 报告
  python scripts/main.py predict-v2 --input 1.txt [--seed 42]  # 三层融合预测
  python scripts/main.py graph-stats            # 查看 MiroFish 图谱
  python scripts/main.py analyze --paste        # v1.2.0 兼容（保留）
  python scripts/main.py version                # 版本信息

首次使用请先运行:
  python scripts/main_setup.py                   # 一键配置
        """
    )
    # v2.5.0：出错时默认显示友好中文提示，--debug 可看完整堆栈。
    # --debug 在子命令前后均可使用（parse_args 前从 argv 中取出）。
    parser.add_argument('--debug', action='store_true',
                        help='出错时显示完整堆栈（默认显示友好提示）')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # ========= v1.2.0 命令（向后兼容）=========
    analyze_parser = subparsers.add_parser('analyze', help='[v1.2.0] 分析聊天记录')
    analyze_parser.add_argument('--paste', action='store_true')
    analyze_parser.add_argument('--input', type=str)
    analyze_parser.add_argument('--file', type=str)
    analyze_parser.set_defaults(func=cmd_analyze)

    report_parser = subparsers.add_parser('report', help='[v1.2.0] 生成报告')
    report_parser.add_argument('--report-type', type=str, default='html',
                              choices=['html', 'pptx', 'word', 'all'])
    report_parser.add_argument('--period', type=str, default='weekly')
    report_parser.add_argument('--chat-id', type=str)
    report_parser.set_defaults(func=cmd_report)

    schedule_parser = subparsers.add_parser('schedule', help='[v1.2.0] 定时任务')
    schedule_parser.add_argument('--list', action='store_true')
    schedule_parser.add_argument('--add', action='store_true')
    schedule_parser.add_argument('--remove', type=str, metavar='NAME')
    schedule_parser.add_argument('--enable', type=str, metavar='NAME')
    schedule_parser.add_argument('--disable', type=str, metavar='NAME')
    schedule_parser.add_argument('--name', type=str)
    schedule_parser.add_argument('--period', type=str)
    schedule_parser.add_argument('--chat-id', type=str)
    schedule_parser.add_argument('--report-type', type=str, default='html')
    schedule_parser.set_defaults(func=cmd_schedule)

    serve_parser = subparsers.add_parser('serve', help='[v1.2.0] 启动Web服务')
    serve_parser.add_argument('--port', type=int)
    serve_parser.set_defaults(func=cmd_serve)

    calendar_parser = subparsers.add_parser('calendar', help='[v1.2.0] 日历事件')
    calendar_parser.add_argument('--list', action='store_true')
    calendar_parser.add_argument('--upcoming', action='store_true')
    calendar_parser.add_argument('--days', type=int, default=7)
    calendar_parser.add_argument('--type', type=str)
    calendar_parser.add_argument('--importance', type=str, choices=['high', 'medium', 'low'])
    calendar_parser.set_defaults(func=cmd_calendar)

    # ========= v2 命令 =========
    analyze_v2_parser = subparsers.add_parser('analyze-v2', help='[v2] 模块化分析（jieba/否定识别/反讽）')
    analyze_v2_parser.add_argument('--paste', action='store_true')
    analyze_v2_parser.add_argument('--input', type=str)
    analyze_v2_parser.add_argument('--file', type=str)
    analyze_v2_parser.add_argument('--export', type=str, metavar='PATH.json',
                                  help='[v2.1.0] 导出全部分析结果为 JSON')
    analyze_v2_parser.add_argument('--html', type=str, metavar='PATH.html',
                                  help='[v2.1.0] 生成单文件离线 HTML 报告')
    analyze_v2_parser.set_defaults(func=cmd_analyze_v2)

    predict_v2_parser = subparsers.add_parser('predict-v2', help='[v2] 三层融合预测（Rule + RAG + MiroFish）')
    predict_v2_parser.add_argument('--paste', action='store_true')
    predict_v2_parser.add_argument('--input', type=str)
    predict_v2_parser.add_argument('--file', type=str)
    predict_v2_parser.add_argument('--seed', type=int, default=None,
                                   help='[v2.5.0] 随机种子，使 MiroFish 模拟结果可复现')
    predict_v2_parser.set_defaults(func=cmd_predict_v2)

    graph_parser = subparsers.add_parser('graph-stats', help='[v2] MiroFish 图谱统计')
    graph_parser.set_defaults(func=cmd_graph_stats)

    # ========= v2.1.0 新命令 =========
    report_v2_parser = subparsers.add_parser('report-v2', help='[v2.1.0] 用最近一次 analyze-v2 结果生成 HTML 报告')
    report_v2_parser.add_argument('--output', type=str, metavar='PATH.html',
                                 help='输出路径（默认 data/reports/v2_report_<时间戳>.html）')
    report_v2_parser.set_defaults(func=cmd_report_v2)

    demo_parser = subparsers.add_parser('demo', help='[v2.1.0] 一键体验：分析内置示例并生成 HTML 报告')
    demo_parser.set_defaults(func=cmd_demo)

    doctor_parser = subparsers.add_parser('doctor', help='[v2.1.0] 环境自检')
    doctor_parser.set_defaults(func=cmd_doctor)

    version_parser = subparsers.add_parser('version', help='[v2] 版本信息')
    version_parser.set_defaults(func=cmd_version)

    # v2.1.0：无参数启动进入交互式向导（-h/--help 行为不变）
    if len(sys.argv) == 1:
        _run_interactive_wizard()
        return

    # v2.5.0：--debug 位置无关（子命令前后均可），parse_args 前取出
    debug_flag = False
    if "--debug" in sys.argv:
        sys.argv.remove("--debug")
        debug_flag = True

    args = parser.parse_args()
    args.debug = getattr(args, "debug", False) or debug_flag

    if args.command is None:
        parser.print_help()
        return

    # v2.5.0：全链路友好错误提示（此前 friendly_errors 从未被接入）
    try:
        args.func(args)
    except KeyboardInterrupt:
        print(_safe_emoji("\n⏹ 已取消（Ctrl+C），再见！"))
        sys.exit(130)
    except Exception as e:
        if getattr(args, "debug", False):
            raise
        try:
            from friendly_errors import friendly_error
            print(_safe_emoji("\n" + friendly_error(e)), file=sys.stderr)
        except Exception:
            # 友好提示自身出错时回退到原始堆栈，避免掩盖真实错误
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
