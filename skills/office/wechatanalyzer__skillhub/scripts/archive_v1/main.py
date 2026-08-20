#!/usr/bin/env python3
"""
微信聊天分析助手 - 主入口
支持CLI和Web服务两种模式
支持 LLM API 增强分析
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path


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
        '█': '#', '░': '.',
    }
    for emoji, alt in replacements.items():
        text = text.replace(emoji, alt)
    return text.encode(encoding, errors='replace').decode(encoding, errors='replace')


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.text_analyzer import TextAnalyzer
from scripts.report_generator import ReportGenerator
from scripts.data_manager import DataManager
from scripts.scheduler import SchedulerManager
from scripts.calendar_manager import CalendarManager
from scripts.file_importer import MultiFormatImporter


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_llm_configured(config):
    """检查 LLM 是否已配置（兼容显式 enabled 或隐式非空 api_key）"""
    llm = config.get('llm', {})
    enabled = llm.get('enabled')
    if enabled is None:
        return bool(llm.get('api_key', '').strip())
    return bool(enabled) and bool(llm.get('api_key', '').strip())


def cmd_analyze(args):
    """分析聊天记录"""
    config = load_config()
    dm = DataManager(config)
    analyzer = TextAnalyzer(config)
    cm = CalendarManager(config)

    messages = None

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
            return
        messages = dm.parse_text_input(text)
        
    elif args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
        messages = dm.parse_text_input(text)
        
    elif args.file:
        importer = MultiFormatImporter(config)
        messages = importer.import_file(args.file)
        if not messages:
            print(f"错误：无法解析文件 {args.file}")
            return
        print(f"已导入 {len(messages)} 条消息")

    if not messages:
        print("错误：未能解析出有效消息，请检查格式")
        return

    msg_count = len(messages)
    if msg_count > 500:
        print(f"提示：共 {msg_count} 条消息，数量较多，分析可能需要较长时间。建议单次分析不超过 500 条以获得最佳效果。")
    print(f"\n已解析 {msg_count} 条消息，开始分析...")

    # 优先用LLM分析（如果已配置）
    use_llm = is_llm_configured(config)

    if use_llm:
        print("[AI增强模式] 检测到LLM API配置，尝试AI增强分析...")
        try:
            from scripts.llm_analyzer import enhance_results, LLMAnalyzer

            rule_results = analyzer.analyze(messages)
            results = enhance_results(rule_results, messages, config)
            results['ai_enhanced'] = True
            print("[OK] LLM增强分析完成")

        except Exception as e:
            err_msg = str(e)
            if '401' in err_msg or '403' in err_msg or 'apikey' in err_msg.lower():
                print(f"[警告] LLM API Key 无效或未授权，已切换到本地规则分析。请检查 .env 中的 LLM_API_KEY。")
            elif 'timeout' in err_msg.lower() or 'timed out' in err_msg.lower():
                print(f"[警告] LLM API 连接超时，已切换到本地规则分析。请检查网络或 LLM_BASE_URL 是否正确。")
            elif 'connection' in err_msg.lower() or 'refused' in err_msg.lower() or 'resolve' in err_msg.lower():
                print(f"[警告] 无法连接 LLM API（{e}），已切换到本地规则分析。请检查网络和 LLM_BASE_URL。")
            elif 'model' in err_msg.lower():
                print(f"[警告] LLM 模型不可用（{e}），已切换到本地规则分析。请检查 config.json 中的 model 字段。")
            else:
                print(f"[警告] LLM 分析失败（{e}），已自动切换到本地规则分析，核心功能不受影响。")
            results = analyzer.analyze(messages)
            results['ai_enhanced'] = False
    else:
        print("[规则分析模式] LLM未配置，使用本地规则分析")
        results = analyzer.analyze(messages)
        results['ai_enhanced'] = False

    chat_id = dm.save_analysis(results)
    events = cm.extract_events_from_messages(messages, chat_id)

    # 显示结果
    display_results(results, events, messages, config)
    
    return chat_id


def display_results(results, events, messages, config):
    """展示分析结果"""
    stats = results.get('stats', {})
    mbti = results.get('mbti', {})
    big_five = results.get('big_five', {})
    sentiment = results.get('sentiment', {})
    prediction = results.get('prediction', {})
    risks = results.get('risks', {})
    summary = results.get('summary', '')
    ai_mode = results.get('analysis_mode', 'rule_only')

    print(f"\n{'='*55}")
    print(_safe_emoji(f"   微信聊天分析报告"))
    print(f"{'='*55}")

    # 分析模式
    mode_labels = {
        'llm_primary': '[AI] LLM AI 增强分析',
        'rule_only': '[规则] 本地规则分析',
        'rule_fallback': '[规则] 规则分析（LLM降级）',
    }
    print(f"\n分析模式: {mode_labels.get(ai_mode, ai_mode)}")

    # 统计
    print(f"\n{'[统计]'} 聊天统计")
    print(f"  总消息数: {stats.get('total_messages', 0)}")
    print(f"  对方消息: {stats.get('other_messages', 0)}")
    print(f"  你的消息: {stats.get('self_messages', 0)}")
    if stats.get('conversation_duration_days'):
        print(f"  聊天跨度: {stats.get('conversation_duration_days')} 天")

    # MBTI
    if mbti and mbti.get('type') and mbti.get('type') != '未知':
        print(f"\n{'[MBTI]'} MBTI 人格推断")
        print(f"  {mbti.get('type')} - {mbti.get('name', '未知')}")
        print(f"  置信度: {mbti.get('confidence', 0):.0f}%")
        if mbti.get('preference'):
            prefs = mbti['preference']
            print(f"  特征: {prefs.get('E_I', '')}{prefs.get('S_N', '')}{prefs.get('T_F', '')}{prefs.get('J_P', '')}")

    # 大五人格
    if big_five and big_five.get('openness', 0) > 0:
        print(f"\n{'[大五]'} 大五人格分析")
        labels = big_five.get('labels', {
            'openness': '开放性', 'conscientiousness': '尽责性',
            'extraversion': '外向性', 'agreeableness': '宜人性', 'neuroticism': '神经质'
        })
        for dim, key in enumerate(['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']):
            val = big_five.get(key, 50)
            bar = '#' * int(val / 10) + '.' * (10 - int(val / 10))
            print(f"  {labels[key]}: [{bar}] {val:.0f}%")

    # 情感
    if sentiment:
        trend_map = {'up': '[上升]', 'down': '[下降]', 'stable': '[稳定]'}
        trend = trend_map.get(sentiment.get('trend', 'stable'), sentiment.get('trend', ''))
        print(f"\n{'[情感]'} 情感分析")
        print(f"  整体趋势: {trend}")
        if sentiment.get('positive_ratio') is not None:
            print(f"  正面: {sentiment.get('positive_ratio', 0):.1f}% / 负面: {sentiment.get('negative_ratio', 0):.1f}%")

    # 风险预警
    print(f"\n{'='*55}")
    if risks and not risks.get('no_risk_detected'):
        risk_names = {
            'work_shirt': '职场甩锅',
            'pig_butcher': '杀猪盘',
            'hr_bad': 'HR不当人',
            'teammate_trouble': '猪队友'
        }
        for risk_type, data in risks.items():
            if risk_type == 'no_risk_detected':
                continue
            level = data.get('risk_level', 'low')
            level_label = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}.get(level, '[-]')
            print(f"\n  {level_label} {risk_names.get(risk_type, risk_type)} (风险: {level})")
            print(f"     {data.get('description', '')}")
            kws = data.get('matched_keywords', [])
            if kws:
                print('     命中: ' + ' / '.join(kws[:5]))
            strategies = data.get('response_strategies', {})
            if strategies.get('defensive'):
                print(f"     [应对]: {strategies['defensive'][0]}")
    else:
        print(_safe_emoji(f"\n  [OK] 未检测到明显风险话术"))

    # 对话预测
    if prediction and prediction.get('next_message'):
        print(f"\n{'[预测]'} 对话预测")
        print(f"  对方可能说:「{prediction.get('next_message', '')}」")
        alts = prediction.get('alternatives', [])
        if alts:
            print('  其他可能: ' + ' / '.join(alts[:2]))

    # 场景
    scenario = results.get('scenario_analysis', {})
    if scenario and scenario.get('primary'):
        scene_map = {'romantic': '[恋爱]', 'work': '[工作]', 'social': '[社交]', 'important': '[重要]'}
        print(f"\n{'[场景]'} 场景判断: {scene_map.get(scenario['primary'], scenario['primary'])}")

    # AI摘要（如果有）
    if summary:
        print(f"\n{'[摘要]'} AI分析摘要")
        print(f"  {summary}")

    # 日历事件
    if events:
        print(f"\n{'[日程]'} 发现 {len(events)} 个日程事项")
        for ev in events[:3]:
            date = ev.get('event_date', '')[:10]
            print(f"  - {ev.get('title', '')} ({date})")

    print(f"\n{'='*55}")
    print(f"详细报告已保存，使用 report 命令可生成完整报告")


def cmd_report(args):
    """生成报告"""
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
    """管理定时任务"""
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
    """启动Web服务"""
    config = load_config()
    port = args.port or 5000

    use_llm = is_llm_configured(config)
    if use_llm:
        print(f"[AI模式] LLM API 已配置，Web分析将使用AI增强")

    from scripts.web_server import create_app
    app = create_app(config)
    print(f"启动Web服务: http://localhost:{port}")
    print("按 Ctrl+C 停止")
    debug_mode = config.get('server', {}).get('debug', False)
    app.run(host='0.0.0.0', port=port, debug=debug_mode)


def cmd_calendar(args):
    """查看日历事件"""
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


def main():
    parser = argparse.ArgumentParser(
        description="微信聊天分析助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/main.py analyze --paste          # 粘贴聊天记录分析
  python scripts/main.py analyze --input 1.txt   # 从文件分析
  python scripts/main.py report --type html      # 生成HTML报告
  python scripts/main.py serve --port 5000        # 启动Web服务

首次使用请先运行:
  python scripts/main_setup.py                   # 一键配置
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析聊天记录')
    analyze_parser.add_argument('--paste', action='store_true', help='粘贴聊天记录（推荐）')
    analyze_parser.add_argument('--input', type=str, help='从文本文件导入聊天记录')
    analyze_parser.add_argument('--file', type=str, help='从多格式文件导入（支持txt/docx/pdf/json等）')
    analyze_parser.set_defaults(func=cmd_analyze)

    # report 命令
    report_parser = subparsers.add_parser('report', help='生成分析报告')
    report_parser.add_argument('--report-type', type=str, default='html',
                              choices=['html', 'pptx', 'word', 'all'],
                              help='报告类型（默认html）')
    report_parser.add_argument('--period', type=str, default='weekly',
                              choices=['daily', 'weekly', 'monthly', 'quarterly', 'semi-annually', 'annually'],
                              help='报告周期')
    report_parser.add_argument('--chat-id', type=str, help='指定聊天记录ID')
    report_parser.set_defaults(func=cmd_report)

    # schedule 命令
    schedule_parser = subparsers.add_parser('schedule', help='管理定时任务')
    schedule_parser.add_argument('--list', action='store_true', help='列出所有定时任务')
    schedule_parser.add_argument('--add', action='store_true', help='添加定时任务')
    schedule_parser.add_argument('--remove', type=str, metavar='NAME', help='删除定时任务')
    schedule_parser.add_argument('--enable', type=str, metavar='NAME', help='启用定时任务')
    schedule_parser.add_argument('--disable', type=str, metavar='NAME', help='禁用定时任务')
    schedule_parser.add_argument('--name', type=str, help='任务名称')
    schedule_parser.add_argument('--period', type=str,
                                 choices=['daily', 'weekly', 'monthly', 'quarterly', 'semi-annually', 'annually'],
                                 help='任务周期')
    schedule_parser.add_argument('--chat-id', type=str, help='聊天记录ID')
    schedule_parser.add_argument('--report-type', type=str, default='html', help='报告类型')
    schedule_parser.set_defaults(func=cmd_schedule)

    # serve 命令
    serve_parser = subparsers.add_parser('serve', help='启动Web服务')
    serve_parser.add_argument('--port', type=int, help='端口号（默认5000）')
    serve_parser.set_defaults(func=cmd_serve)

    # calendar 命令
    calendar_parser = subparsers.add_parser('calendar', help='查看日历事件')
    calendar_parser.add_argument('--list', action='store_true', help='列出所有事件')
    calendar_parser.add_argument('--upcoming', action='store_true', help='即将到来的事件')
    calendar_parser.add_argument('--days', type=int, default=7, help='天数范围（默认7）')
    calendar_parser.add_argument('--type', type=str, help='事件类型过滤')
    calendar_parser.add_argument('--importance', type=str, choices=['high', 'medium', 'low'], help='重要性过滤')
    calendar_parser.set_defaults(func=cmd_calendar)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\n快速开始:")
        print("  python scripts/main_setup.py    # 一键配置（首次使用必运行）")
        print("  python scripts/main.py analyze --paste   # 粘贴聊天记录分析")
        return

    args.func(args)


if __name__ == '__main__':
    main()
