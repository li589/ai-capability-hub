#!/usr/bin/env python3
"""
多格式文件导入器 - 支持聊天记录、图片、Word、PDF、音频、视频等格式导入
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class MultiFormatImporter:
    """多格式文件导入器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def import_text(self, text: str) -> List[Dict[str, Any]]:
        """解析纯文本聊天记录"""
        messages = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            msg = self._parse_line(line)
            if msg:
                messages.append(msg)

        return messages

    def import_file(self, file_path: str) -> List[Dict[str, Any]]:
        """根据文件类型调用不同的解析器"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        parsers = {
            '.txt': self._import_txt,
            '.json': self._import_json,
            '.docx': self._import_docx,
            '.doc': self._import_doc,
            '.pdf': self._import_pdf,
            '.md': self._import_md,
        }

        if suffix in parsers:
            return parsers[suffix](file_path)
        elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return self._import_image(file_path)
        elif suffix in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
            return self._import_audio(file_path)
        elif suffix in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            return self._import_video(file_path)
        else:
            # 尝试作为文本解析
            return self._import_txt(file_path)

    def _import_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """导入文本文件"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return self.import_text(content)

    def _import_json(self, file_path: str) -> List[Dict[str, Any]]:
        """导入JSON格式聊天记录"""
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持多种JSON格式
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    messages.append({
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'sender': item.get('sender', item.get('name', 'unknown')),
                        'content': item.get('content', item.get('message', '')),
                        'msg_type': item.get('type', 'text')
                    })
        elif isinstance(data, dict):
            if 'messages' in data:
                for item in data['messages']:
                    messages.append({
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'sender': item.get('sender', item.get('name', 'unknown')),
                        'content': item.get('content', item.get('message', '')),
                        'msg_type': item.get('type', 'text')
                    })

        return messages

    def _import_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """导入Word DOCX文件"""
        try:
            from docx import Document
        except ImportError:
            print("错误: python-docx未安装，请使用 pip install python-docx")
            return []

        messages = []
        doc = Document(file_path)

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                msg = self._parse_line(text)
                if msg:
                    messages.append(msg)

        return messages

    def _import_doc(self, file_path: str) -> List[Dict[str, Any]]:
        """导入旧版Word DOC文件（降级尝试）"""
        # 尝试用 textract 解析 .doc 文件
        try:
            import textract
            content = textract.process(file_path).decode('utf-8')
            return self.import_text(content)
        except ImportError:
            print("错误: 无法解析 .doc 文件。请安装 textract: pip install textract")
            print("提示: 建议将 .doc 另存为 .docx 或 .txt 格式后导入")
            return []
        except Exception as e:
            print(f"DOC解析错误: {e}")
            return []

    def _import_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """导入PDF文件"""
        try:
            import pdfplumber
        except ImportError:
            print("错误: 需要安装 pdfplumber 来解析 PDF 文件")
            print("请使用: pip install pdfplumber")
            return []

        messages = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split('\n'):
                            line = line.strip()
                            if line:
                                msg = self._parse_line(line)
                                if msg:
                                    messages.append(msg)
        except Exception as e:
            print(f"PDF解析错误: {e}")

        return messages

    def _import_md(self, file_path: str) -> List[Dict[str, Any]]:
        """导入Markdown格式聊天记录"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return self.import_text(content)

    def _import_image(self, file_path: str) -> List[Dict[str, Any]]:
        """导入图片文件 - 返回图片消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[图片: {os.path.basename(file_path)}]',
            'msg_type': 'image',
            'file_path': file_path
        }]

    def _import_audio(self, file_path: str) -> List[Dict[str, Any]]:
        """导入音频文件 - 返回音频消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[语音: {os.path.basename(file_path)}]',
            'msg_type': 'audio',
            'file_path': file_path
        }]

    def _import_video(self, file_path: str) -> List[Dict[str, Any]]:
        """导入视频文件 - 返回视频消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[视频: {os.path.basename(file_path)}]',
            'msg_type': 'video',
            'file_path': file_path
        }]

    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行聊天记录"""
        # 格式1: [2024-01-01 12:30:00] 张三: 你好
        match = re.match(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*([^:：]+)[:：]\s*(.+)', line)
        if match:
            return {
                'timestamp': match.group(1).strip(),
                'sender': match.group(2).strip(),
                'content': match.group(3).strip()
            }

        # 格式2: 2024-01-01 12:30:00 | 张三 | 你好
        match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[|｜]\s*([^|：]+)\s*[|｜]\s*(.+)', line)
        if match:
            return {
                'timestamp': match.group(1).strip(),
                'sender': match.group(2).strip(),
                'content': match.group(3).strip()
            }

        # 格式3: 张三: 你好 (无时间)
        match = re.match(r'^([^:：]+)[:：]\s*(.+)', line)
        if match:
            return {
                'timestamp': datetime.now().isoformat(),
                'sender': match.group(1).strip(),
                'content': match.group(2).strip()
            }

        return None

    def parse_pasted_content(self, content: str) -> List[Dict[str, Any]]:
        """
        解析粘贴的多格式内容
        支持混合文本、图片描述、Word内容等
        """
        messages = []

        # 处理富文本粘贴的内容
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检测图片
            if '[图片]' in line or '[image]' in line.lower():
                messages.append({
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'image'
                })
            # 检测语音
            elif '[语音]' in line or '[voice]' in line.lower():
                messages.append({
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'audio'
                })
            # 检测视频
            elif '[视频]' in line or '[video]' in line.lower():
                messages.append({
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'video'
                })
            # 检测文件
            elif '[文件]' in line or '[file]' in line.lower():
                messages.append({
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'file'
                })
            # 普通文本
            elif line:
                msg = self._parse_line(line)
                if msg:
                    messages.append(msg)

            i += 1

        return messages
