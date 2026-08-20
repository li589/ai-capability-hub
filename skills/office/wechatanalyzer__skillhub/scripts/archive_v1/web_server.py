#!/usr/bin/env python3
"""
Web服务器 - 提供网页界面访问
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from pathlib import Path
import json
import os
import uuid
from datetime import datetime


def create_app(config):
    """创建Flask应用"""
    app = Flask(__name__, template_folder='../templates', static_folder='../data')
    CORS(app)

    data_manager = None
    text_analyzer = None
    report_generator = None
    calendar_manager = None

    def get_data_manager():
        nonlocal data_manager
        if data_manager is None:
            from scripts.data_manager import DataManager
            data_manager = DataManager(config)
        return data_manager

    def get_text_analyzer():
        nonlocal text_analyzer
        if text_analyzer is None:
            from scripts.text_analyzer import TextAnalyzer
            text_analyzer = TextAnalyzer(config)
        return text_analyzer

    def get_report_generator():
        nonlocal report_generator
        if report_generator is None:
            from scripts.report_generator import ReportGenerator
            report_generator = ReportGenerator(config)
        return report_generator

    def get_calendar_manager():
        nonlocal calendar_manager
        if calendar_manager is None:
            from scripts.calendar_manager import CalendarManager
            calendar_manager = CalendarManager(config)
        return calendar_manager

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/api/analyze', methods=['POST'])
    def analyze():
        """分析聊天记录"""
        data = request.json
        text = data.get('text', '')

        dm = get_data_manager()
        analyzer = get_text_analyzer()

        messages = dm.parse_text_input(text)
        results = analyzer.analyze(messages)

        # 提取日历事件
        cm = get_calendar_manager()
        events = cm.extract_events_from_messages(messages, results.get('chat_id', 'temp'))

        chat_id = dm.save_analysis(results)

        return jsonify({
            'success': True,
            'chat_id': chat_id,
            'results': results,
            'events': events
        })

    @app.route('/api/chat/list', methods=['GET'])
    def chat_list():
        """获取聊天列表"""
        dm = get_data_manager()
        chats = dm.get_chat_list()
        return jsonify({'success': True, 'chats': chats})

    @app.route('/api/chat/<chat_id>', methods=['GET'])
    def get_chat(chat_id):
        """获取指定聊天"""
        dm = get_data_manager()
        messages = dm.get_messages(chat_id)
        return jsonify({'success': True, 'messages': messages})

    @app.route('/api/report/<chat_id>', methods=['GET'])
    def get_report(chat_id):
        """获取分析报告"""
        report_type = request.args.get('type', 'html')
        dm = get_data_manager()
        generator = get_report_generator()

        results = dm.get_analysis(chat_id)
        if not results:
            return jsonify({'success': False, 'error': 'Not found'})

        output_path = generator.generate(results, report_type=report_type)
        return jsonify({'success': True, 'path': output_path})

    @app.route('/api/events', methods=['GET'])
    def get_events():
        """获取日历事件"""
        cm = get_calendar_manager()
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        event_type = request.args.get('type')
        importance = request.args.get('importance')

        events = cm.get_events(start_date, end_date, event_type, importance)
        return jsonify({'success': True, 'events': events})

    @app.route('/api/events/upcoming', methods=['GET'])
    def upcoming_events():
        """获取即将到来的事件"""
        cm = get_calendar_manager()
        days = int(request.args.get('days', 7))
        events = cm.get_upcoming_events(days)
        return jsonify({'success': True, 'events': events})

    @app.route('/api/events', methods=['POST'])
    def create_event():
        """创建事件"""
        cm = get_calendar_manager()
        data = request.json

        event = {
            'id': str(uuid.uuid4()),
            'chat_id': data.get('chat_id', ''),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'event_date': data.get('event_date', datetime.now().isoformat()),
            'event_time': data.get('event_time'),
            'event_type': data.get('event_type', 'reminder'),
            'importance': data.get('importance', 'medium'),
            'created_at': datetime.now().isoformat(),
            'source_message': ''
        }

        return jsonify({'success': True, 'event': event})

    @app.route('/api/upload/screenshot', methods=['POST'])
    def upload_screenshot():
        """上传截图（需要安装 easyocr）"""
        data = request.json
        image_data = data.get('image_data')

        if not image_data:
            return jsonify({'success': False, 'error': 'No image data'})

        try:
            import base64
            from pathlib import Path

            # Save image to temp file
            tmp_dir = Path(config.get('data_dir', 'data')) / 'uploads'
            tmp_dir.mkdir(parents=True, exist_ok=True)
            img_path = tmp_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            if ',' in image_data:
                image_data = image_data.split(',')[1]
            img_bytes = base64.b64decode(image_data)
            img_path.write_bytes(img_bytes)

            # Try OCR
            try:
                import easyocr
                reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                result = reader.readtext(str(img_path))
                text = '\n'.join([item[1] for item in result])
            except ImportError:
                text = f'[截图已保存: {img_path.name}]'

            messages = get_data_manager().parse_text_input(text)

            if messages:
                analyzer = get_text_analyzer()
                results = analyzer.analyze(messages)

                cm = get_calendar_manager()
                events = cm.extract_events_from_messages(messages, 'screenshot')

                chat_id = get_data_manager().save_analysis(results)

                return jsonify({
                    'success': True,
                    'chat_id': chat_id,
                    'messages': messages,
                    'results': results,
                    'events': events
                })
            else:
                return jsonify({'success': False, 'error': 'No messages extracted from screenshot'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return app


if __name__ == '__main__':
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    app = create_app(config)
    debug_mode = config.get('server', {}).get('debug', False)
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
