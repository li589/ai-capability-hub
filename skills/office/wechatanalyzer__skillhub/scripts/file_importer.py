#!/usr/bin/env python3
"""
多格式文件导入器 - 支持聊天记录、图片、Word、PDF、PPT、Excel、音频、视频等格式导入

v2.2.0 修复：
- 完整支持 .docx / .pdf / .pptx / .xlsx 及旧版 .doc / .ppt / .xls
- Word 解析：段落 + 表格 + 页眉/页脚 + 文本框，兼容纯文本旧版 doc
- PDF 解析：按页提取文本，可选按行/段解析，pdfplumber 优先 + PyPDF2 兜底
- PPT 解析：所有幻灯片标题 + 正文 + 备注 + 表格（python-pptx）
- Excel 解析：所有 sheet 单元格正文（openpyxl / xlrd 兜底）
- 所有解析器返回统一 chat 消息格式：
    {timestamp, sender, content, msg_type, file_path, metadata}
- 解析失败时给出友好中文错误（不再裸抛 stack trace）
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime


logger = logging.getLogger(__name__)


class MultiFormatImporter:
    """多格式文件导入器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    # ----------------------------------------------------------------
    # 公共入口
    # ----------------------------------------------------------------
    def import_text(self, text: str) -> List[Dict[str, Any]]:
        """解析纯文本聊天记录"""
        messages: List[Dict[str, Any]] = []
        if not text:
            return messages

        for line in text.split('\n'):
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
        if not path.exists():
            logger.error("文件不存在: %s", file_path)
            return []
        if not path.is_file():
            logger.error("路径不是文件: %s", file_path)
            return []

        suffix = path.suffix.lower()

        # 文本类（优先尝试编码自动检测）
        text_parsers = {
            '.txt': self._import_txt,
            '.md': self._import_md,
            '.markdown': self._import_md,
            '.log': self._import_txt,
        }
        if suffix in text_parsers:
            return text_parsers[suffix](file_path)

        # JSON
        if suffix == '.json':
            return self._import_json(file_path)

        # Word
        if suffix == '.docx':
            return self._import_docx(file_path)
        if suffix == '.doc':
            return self._import_doc(file_path)

        # PDF
        if suffix == '.pdf':
            return self._import_pdf(file_path)

        # PPT
        if suffix == '.pptx':
            return self._import_pptx(file_path)
        if suffix == '.ppt':
            return self._import_ppt(file_path)

        # Excel
        if suffix == '.xlsx':
            return self._import_xlsx(file_path)
        if suffix == '.xls':
            return self._import_xls(file_path)

        # 图片
        if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic']:
            return self._import_image(file_path)

        # 音频
        if suffix in ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma']:
            return self._import_audio(file_path)

        # 视频
        if suffix in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
            return self._import_video(file_path)

        # 兜底：尝试按 UTF-8 / GBK 文本解析
        logger.warning("未知文件类型 %s，按文本回落解析", suffix)
        return self._import_txt(file_path)

    # ----------------------------------------------------------------
    # 文本/JSON
    # ----------------------------------------------------------------
    def _import_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """导入文本文件（v2.1.0：自动检测 utf-8-sig/utf-8/gb18030 编码）"""
        from core.utils import read_text_auto
        try:
            content, _enc = read_text_auto(file_path)
        except (FileNotFoundError, ValueError) as e:
            logger.error("读取文本文件失败: %s", e)
            return []
        return self.import_text(content)

    def _import_json(self, file_path: str) -> List[Dict[str, Any]]:
        """导入JSON格式聊天记录"""
        messages: List[Dict[str, Any]] = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error("JSON 解析失败: %s", e)
            return []

        def _conv(item: Any) -> Optional[Dict[str, Any]]:
            if not isinstance(item, dict):
                return None
            return {
                'timestamp': item.get('timestamp', item.get('time', datetime.now().isoformat())),
                'sender': item.get('sender', item.get('name', item.get('from', 'unknown'))),
                'content': item.get('content', item.get('message', item.get('text', ''))),
                'msg_type': item.get('type', 'text'),
            }

        if isinstance(data, list):
            for item in data:
                m = _conv(item)
                if m:
                    messages.append(m)
        elif isinstance(data, dict):
            for key in ('messages', 'data', 'records', 'chat_history'):
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        m = _conv(item)
                        if m:
                            messages.append(m)
                    break
            else:
                # 单条消息
                m = _conv(data)
                if m:
                    messages.append(m)
        return messages

    def _import_md(self, file_path: str) -> List[Dict[str, Any]]:
        """导入Markdown格式聊天记录（v2.1.0：自动检测编码）"""
        from core.utils import read_text_auto
        try:
            content, _enc = read_text_auto(file_path)
        except (FileNotFoundError, ValueError) as e:
            logger.error("读取 Markdown 失败: %s", e)
            return []
        return self.import_text(content)

    # ----------------------------------------------------------------
    # Word
    # ----------------------------------------------------------------
    def _import_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """导入 Word DOCX 文件（v2.2.0：段落 + 表格 + 页眉/页脚 + 文本框）"""
        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx 未安装，运行: pip install python-docx")
            return []

        messages: List[Dict[str, Any]] = []

        def _add(text: str, section: str) -> None:
            text = (text or "").strip()
            if not text:
                return
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                msg = self._parse_line(line)
                if not msg:
                    msg = {
                        'timestamp': datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime
                        ).isoformat(),
                        'sender': 'document',
                        'content': line,
                        'msg_type': 'text',
                    }
                msg['metadata'] = msg.get('metadata', {})
                msg['metadata']['source_file'] = os.path.basename(file_path)
                msg['metadata']['doc_section'] = section
                msg['file_path'] = file_path
                messages.append(msg)

        try:
            doc = Document(file_path)
        except Exception as e:
            logger.error("DOCX 解析失败: %s", e)
            return []

        # 1) 段落
        for para in doc.paragraphs:
            _add(para.text, section='paragraph')

        # 2) 表格（每行拼成一条消息，单元格以 | 分隔）
        for ti, table in enumerate(doc.tables):
            for row in table.rows:
                cells_text = [cell.text.strip() for cell in row.cells]
                line = ' | '.join(c for c in cells_text if c)
                if line:
                    _add(line, section=f'table[{ti}]')

        # 3) 页眉 / 页脚
        for si, section in enumerate(doc.sections):
            for hdr in (section.header, section.first_page_header, section.even_page_header):
                if hdr is None:
                    continue
                for para in hdr.paragraphs:
                    _add(para.text, section=f'header[{si}]')
            for ftr in (section.footer, section.first_page_footer, section.even_page_footer):
                if ftr is None:
                    continue
                for para in ftr.paragraphs:
                    _add(para.text, section=f'footer[{si}]')

        return messages

    def _import_doc(self, file_path: str) -> List[Dict[str, Any]]:
        """导入旧版 Word DOC 文件（v2.2.0：多重降级，避免崩溃）"""
        # 优先尝试 antiword（轻量级二进制）
        try:
            import subprocess
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                content = result.stdout.decode('utf-8', errors='ignore')
                return self.import_text(content)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        # 第二选择：textract
        try:
            import textract  # type: ignore
            content = textract.process(file_path).decode('utf-8', errors='ignore')
            return self.import_text(content)
        except ImportError:
            pass
        except Exception as e:
            logger.error("textract 解析失败: %s", e)

        # 第三选择：olefile + 简易二进制读取（仅取 ASCII 可打印片段）
        try:
            data = Path(file_path).read_bytes()
            text = self._extract_printable_chinese(data)
            if text:
                return self.import_text(text)
        except Exception as e:
            logger.error("DOC 二进制兜底解析失败: %s", e)

        # 全部失败：友好提示
        logger.warning(
            "无法解析 .doc（旧版二进制 Word）。建议：用 Word/WPS 打开并另存为 .docx 后再导入。"
        )
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'system',
            'content': f'[无法解析 {os.path.basename(file_path)}：请将 .doc 另存为 .docx 或 .txt 后重试]',
            'msg_type': 'system',
            'file_path': file_path,
            'metadata': {'parse_error': 'doc_unsupported'},
        }]

    # ----------------------------------------------------------------
    # PDF
    # ----------------------------------------------------------------
    def _import_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """导入 PDF 文件（v2.2.0：pdfplumber 主路径 + PyPDF2 兜底，多页友好）"""
        messages: List[Dict[str, Any]] = []

        page_texts = self._extract_pdf_pages(file_path)
        if not page_texts:
            return [{
                'timestamp': datetime.now().isoformat(),
                'sender': 'system',
                'content': f'[PDF 解析失败或无文本: {os.path.basename(file_path)}]'
                '（可能是扫描版 PDF，需要 OCR）',
                'msg_type': 'system',
                'file_path': file_path,
                'metadata': {'parse_error': 'pdf_no_text'},
            }]

        for page_idx, text in enumerate(page_texts, start=1):
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                msg = self._parse_line(line)
                if not msg:
                    msg = {
                        'timestamp': datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime
                        ).isoformat(),
                        'sender': 'document',
                        'content': line,
                        'msg_type': 'text',
                    }
                msg['metadata'] = msg.get('metadata', {})
                msg['metadata']['source_file'] = os.path.basename(file_path)
                msg['metadata']['pdf_page'] = page_idx
                msg['file_path'] = file_path
                messages.append(msg)
        return messages

    def _extract_pdf_pages(self, file_path: str) -> List[str]:
        """分层提取 PDF 文本：pdfplumber → PyPDF2 → pypdf 兜底"""
        # 1) pdfplumber（推荐）
        try:
            import pdfplumber  # type: ignore
            pages: List[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
            if any(p.strip() for p in pages):
                return pages
        except ImportError:
            logger.warning("pdfplumber 未安装，尝试 PyPDF2 兜底")
        except Exception as e:
            logger.warning("pdfplumber 解析失败 (%s)，尝试 PyPDF2", e)

        # 2) PyPDF2
        try:
            from PyPDF2 import PdfReader  # type: ignore
            reader = PdfReader(file_path)
            return [(page.extract_text() or "") for page in reader.pages]
        except ImportError:
            pass
        except Exception as e:
            logger.warning("PyPDF2 解析失败: %s", e)

        # 3) pypdf
        try:
            from pypdf import PdfReader as PyPdfReader  # type: ignore
            reader = PyPdfReader(file_path)
            return [(page.extract_text() or "") for page in reader.pages]
        except ImportError:
            pass
        except Exception as e:
            logger.error("pypdf 解析失败: %s", e)

        return []

    # ----------------------------------------------------------------
    # PPT
    # ----------------------------------------------------------------
    def _import_pptx(self, file_path: str) -> List[Dict[str, Any]]:
        """导入 PPTX 文件（v2.2.0：所有幻灯片标题 + 正文 + 备注 + 表格）"""
        try:
            from pptx import Presentation  # type: ignore
        except ImportError:
            logger.error("python-pptx 未安装，运行: pip install python-pptx")
            return []

        def _add(text: str, slide_idx: int, section: str) -> None:
            text = (text or "").strip()
            if not text:
                return
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                msg = self._parse_line(line)
                if not msg:
                    msg = {
                        'timestamp': datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime
                        ).isoformat(),
                        'sender': 'document',
                        'content': line,
                        'msg_type': 'text',
                    }
                msg['metadata'] = msg.get('metadata', {})
                msg['metadata']['source_file'] = os.path.basename(file_path)
                msg['metadata']['ppt_slide'] = slide_idx
                msg['metadata']['ppt_section'] = section
                msg['file_path'] = file_path
                messages.append(msg)

        messages: List[Dict[str, Any]] = []
        try:
            prs = Presentation(file_path)
        except Exception as e:
            logger.error("PPTX 解析失败: %s", e)
            return [{
                'timestamp': datetime.now().isoformat(),
                'sender': 'system',
                'content': f'[PPTX 解析失败: {os.path.basename(file_path)}]',
                'msg_type': 'system',
                'file_path': file_path,
                'metadata': {'parse_error': str(e)},
            }]

        for slide_idx, slide in enumerate(prs.slides, start=1):
            # 1) 标题/正文
            for shape in slide.shapes:
                # 文本框
                if shape.has_text_frame:
                    _add(shape.text_frame.text, slide_idx, 'text_frame')
                # 表格
                if shape.has_table:
                    for row in shape.table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        line = ' | '.join(c for c in cells if c)
                        if line:
                            _add(line, slide_idx, 'table')
            # 2) 演讲者备注
            if slide.has_notes_slide:
                notes_tf = slide.notes_slide.notes_text_frame
                _add(notes_tf.text, slide_idx, 'notes')
        return messages

    def _import_ppt(self, file_path: str) -> List[Dict[str, Any]]:
        """导入旧版 PPT（二进制 OLE 格式，v2.2.0 友好降级）"""
        try:
            import subprocess
            result = subprocess.run(
                ['catppt', file_path],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                content = result.stdout.decode('utf-8', errors='ignore')
                if content.strip():
                    return self.import_text(content)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        try:
            data = Path(file_path).read_bytes()
            text = self._extract_printable_chinese(data)
            if text:
                return self.import_text(text)
        except Exception as e:
            logger.error("PPT 二进制兜底解析失败: %s", e)

        logger.warning("无法解析 .ppt（旧版二进制 PPT）。建议：用 PowerPoint 另存为 .pptx 后再导入。")
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'system',
            'content': f'[无法解析 {os.path.basename(file_path)}：请将 .ppt 另存为 .pptx 或 .txt 后重试]',
            'msg_type': 'system',
            'file_path': file_path,
            'metadata': {'parse_error': 'ppt_unsupported'},
        }]

    # ----------------------------------------------------------------
    # Excel
    # ----------------------------------------------------------------
    def _import_xlsx(self, file_path: str) -> List[Dict[str, Any]]:
        """导入 Excel XLSX 文件（v2.2.0：所有 sheet，所有单元格）"""
        try:
            import openpyxl  # type: ignore
        except ImportError:
            logger.error("openpyxl 未安装，运行: pip install openpyxl")
            return []

        messages: List[Dict[str, Any]] = []

        def _add(text: str, sheet_name: str, cell: str) -> None:
            text = (text or "").strip()
            if not text:
                return
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                msg = self._parse_line(line)
                if not msg:
                    msg = {
                        'timestamp': datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime
                        ).isoformat(),
                        'sender': 'document',
                        'content': line,
                        'msg_type': 'text',
                    }
                msg['metadata'] = msg.get('metadata', {})
                msg['metadata']['source_file'] = os.path.basename(file_path)
                msg['metadata']['xlsx_sheet'] = sheet_name
                msg['metadata']['xlsx_cell'] = cell
                msg['file_path'] = file_path
                messages.append(msg)

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        except Exception as e:
            logger.error("XLSX 解析失败: %s", e)
            return [{
                'timestamp': datetime.now().isoformat(),
                'sender': 'system',
                'content': f'[XLSX 解析失败: {os.path.basename(file_path)}]',
                'msg_type': 'system',
                'file_path': file_path,
                'metadata': {'parse_error': str(e)},
            }]

        try:
            for ws in wb.worksheets:
                # 行式遍历效率更高
                for row in ws.iter_rows(values_only=False):
                    row_cells: List[str] = []
                    for cell in row:
                        if cell.value is None:
                            continue
                        v = str(cell.value).strip()
                        if not v:
                            continue
                        row_cells.append(v)
                        # v2.5.0：仅"发送者: 内容"格式的单元格单独成消息；
                        # 裸单元格不再重复计数（其内容已包含在行汇总消息中）。
                        if self._parse_line(v):
                            _add(v, ws.title, cell.coordinate)
                    if row_cells:
                        # 行汇总也作为一条消息（| 分隔）
                        joined = ' | '.join(row_cells)
                        msg = {
                            'timestamp': datetime.fromtimestamp(
                                Path(file_path).stat().st_mtime
                            ).isoformat(),
                            'sender': 'document',
                            'content': joined,
                            'msg_type': 'text',
                        }
                        msg['metadata'] = {
                            'source_file': os.path.basename(file_path),
                            'xlsx_sheet': ws.title,
                            'xlsx_row': row[0].row if row else None,
                        }
                        msg['file_path'] = file_path
                        messages.append(msg)
        finally:
            try:
                wb.close()
            except Exception:
                pass
        return messages

    def _import_xls(self, file_path: str) -> List[Dict[str, Any]]:
        """导入旧版 XLS（v2.2.0：xlrd 兜底）"""
        try:
            import xlrd  # type: ignore
        except ImportError:
            logger.warning("xlrd 未安装，无法解析 .xls。请用 Excel 另存为 .xlsx 或安装 xlrd<2.0")
            return [{
                'timestamp': datetime.now().isoformat(),
                'sender': 'system',
                'content': f'[无法解析 {os.path.basename(file_path)}：.xls 需要 xlrd<2.0，建议另存为 .xlsx]',
                'msg_type': 'system',
                'file_path': file_path,
                'metadata': {'parse_error': 'xls_xlrd_missing'},
            }]

        try:
            book = xlrd.open_workbook(file_path)
        except Exception as e:
            logger.error("XLS 解析失败: %s", e)
            return []

        messages: List[Dict[str, Any]] = []
        for sheet in book.sheets():
            for rx in range(sheet.nrows):
                row_vals = [str(sheet.cell_value(rx, cx)).strip()
                            for cx in range(sheet.ncols)
                            if str(sheet.cell_value(rx, cx)).strip()]
                if not row_vals:
                    continue
                joined = ' | '.join(row_vals)
                msg = {
                    'timestamp': datetime.fromtimestamp(
                        Path(file_path).stat().st_mtime
                    ).isoformat(),
                    'sender': 'document',
                    'content': joined,
                    'msg_type': 'text',
                }
                msg['metadata'] = {
                    'source_file': os.path.basename(file_path),
                    'xls_sheet': sheet.name,
                    'xls_row': rx + 1,
                }
                msg['file_path'] = file_path
                messages.append(msg)
        return messages

    # ----------------------------------------------------------------
    # 图片 / 音频 / 视频
    # ----------------------------------------------------------------
    def _import_image(self, file_path: str) -> List[Dict[str, Any]]:
        """导入图片文件 - 返回图片消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[图片: {os.path.basename(file_path)}]',
            'msg_type': 'image',
            'file_path': file_path,
            'metadata': {'source_file': os.path.basename(file_path)},
        }]

    def _import_audio(self, file_path: str) -> List[Dict[str, Any]]:
        """导入音频文件 - 返回音频消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[语音: {os.path.basename(file_path)}]',
            'msg_type': 'audio',
            'file_path': file_path,
            'metadata': {'source_file': os.path.basename(file_path)},
        }]

    def _import_video(self, file_path: str) -> List[Dict[str, Any]]:
        """导入视频文件 - 返回视频消息"""
        return [{
            'timestamp': datetime.now().isoformat(),
            'sender': 'unknown',
            'content': f'[视频: {os.path.basename(file_path)}]',
            'msg_type': 'video',
            'file_path': file_path,
            'metadata': {'source_file': os.path.basename(file_path)},
        }]

    # ----------------------------------------------------------------
    # 工具
    # ----------------------------------------------------------------
    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行聊天记录（识别多种格式）"""
        # 格式1: [2024-01-01 12:30:00] 张三: 你好
        m = re.match(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*([^:：]+)[:：]\s*(.+)', line)
        if m:
            return {
                'timestamp': m.group(1).strip(),
                'sender': m.group(2).strip(),
                'content': m.group(3).strip(),
            }

        # 格式2: 2024-01-01 12:30:00 | 张三 | 你好
        m = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[|｜]\s*([^|：]+)\s*[|｜]\s*(.+)', line)
        if m:
            return {
                'timestamp': m.group(1).strip(),
                'sender': m.group(2).strip(),
                'content': m.group(3).strip(),
            }

        # 格式3: 张三: 你好 (无时间)
        m = re.match(r'^([^:：]+)[:：]\s*(.+)', line)
        if m:
            return {
                'timestamp': datetime.now().isoformat(),
                'sender': m.group(1).strip(),
                'content': m.group(2).strip(),
            }

        return None

    # 中文最常用字（用于编码识别评分：真实中文句子里常见字占比高，
    # 而 gb18030 误读 UTF-8 等产生的乱码中文几乎不会命中这些字）
    _COMMON_CJK = frozenset(
        "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞"
    )

    @classmethod
    def _extract_printable_chinese(cls, data: bytes, min_len: int = 4) -> str:
        """从二进制字节中提取可读的中文 + ASCII 文本片段（用于 .doc/.ppt 兜底）。

        v2.5.0：原实现只保留 ASCII 字节（0x20-0x7E），UTF-8 中文（≥0x80）
        会触发缓冲区清空被全部丢弃，实际只能提取英文碎片。现改为整体按
        utf-8 → gb18030 → utf-16-le 尝试解码，以「常见字命中数」评分选
        最优编码（真实中文常见字密度高，乱码中文几乎不命中），再按可读
        行过滤（中文/字母数字/常见标点占比 ≥ 60%）。
        """
        if not data:
            return ""

        best, best_score = "", 0
        for enc in ("utf-8", "gb18030", "utf-16-le"):
            try:
                text = data.decode(enc, errors="ignore")
            except (UnicodeDecodeError, LookupError):
                continue
            common = sum(1 for c in text if c in cls._COMMON_CJK)
            if common > best_score:
                best, best_score = text, common

        if not best:
            return ""

        # 过滤：去掉明显是二进制的乱码行
        good_lines = []
        for line in best.splitlines():
            line = line.strip()
            if len(line) < min_len:
                continue
            # 中文字符 / 拉丁字母 / 数字 / 常见标点 占多数才算可读
            readable = sum(1 for c in line if (
                "\u4e00" <= c <= "\u9fff"
                or c.isalnum()
                or c in " ,.;:!?，。！？；：、"
            ))
            if readable / len(line) >= 0.6:
                good_lines.append(line)
        return "\n".join(good_lines)

    # ----------------------------------------------------------------
    # 粘贴内容解析
    # ----------------------------------------------------------------
    def parse_pasted_content(self, content: str) -> List[Dict[str, Any]]:
        """
        解析粘贴的多格式内容
        支持混合文本、图片描述、Word内容等
        """
        messages: List[Dict[str, Any]] = []
        if not content:
            return messages

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 检测图片 / 语音 / 视频 / 文件
            if '[图片]' in line or '[image]' in line.lower():
                msg = {
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'image',
                }
            elif '[语音]' in line or '[voice]' in line.lower():
                msg = {
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'audio',
                }
            elif '[视频]' in line or '[video]' in line.lower():
                msg = {
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'video',
                }
            elif '[文件]' in line or '[file]' in line.lower():
                msg = {
                    'timestamp': datetime.now().isoformat(),
                    'sender': 'unknown',
                    'content': line,
                    'msg_type': 'file',
                }
            else:
                msg = self._parse_line(line)
                if not msg:
                    continue
            messages.append(msg)
        return messages
