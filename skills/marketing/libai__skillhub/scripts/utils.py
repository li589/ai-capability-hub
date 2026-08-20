#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions for text processing - Optimized version."""

import re
from pathlib import Path
from typing import List, Union

# ---------- 句子分割 ----------
_SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[。！？!?…\.])\s*(?=[^。！？!?…\.]|$)')
_SPACE_PATTERN = re.compile(r' +')
_NEWLINE_PATTERN = re.compile(r'\n{3,}')
_SPACE_BEFORE_COMMA = re.compile(r'\s+([,，])')


def split_sentences(text: str) -> List[str]:
    """将文本分割为句子列表，保持标点。"""
    sentences = _SENTENCE_SPLIT_PATTERN.split(text)
    return [s.strip() for s in sentences if s.strip()]


# ---------- 文本清洗 ----------
def clean_text(text: str) -> str:
    """基础清洗：去除多余空格、合并换行、修复标点等。
    
    新增：统一全角/半角省略号（U+2026 …… 统一为 ASCII ...），确保后续替换规则对两种形式都生效。
    """
    text = text.strip()
    # 统一省略号：全角 → 半角
    text = text.replace('\u2026', '...')  # horizontal ellipsis
    text = text.replace('\uff0e' * 3, '...')  # full-width period x3
    text = _SPACE_PATTERN.sub(' ', text)
    text = _NEWLINE_PATTERN.sub('\n\n', text)
    text = _SPACE_BEFORE_COMMA.sub(r'\1', text)
    text = re.sub(r'([。！？])([^"\'\s])', r'\1 \2', text)
    return text


# ---------- 文件读写 ----------
def read_file(path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """读取文件内容。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding=encoding)


def write_file(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
    """写入内容到文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


# ---------- 文本统计 ----------
_WORD_PATTERN = re.compile(
    r'[\u4e00-\u9fa5]+'            # 中文连续字
    r'|[a-zA-Z]+(?:[\'-][a-zA-Z]+)*'  # 英文词（含缩写 don't / 连字符 state-of-the-art）
    r'|\d+(?:\.\d+)?'               # 数字（含小数）
)


def word_count(text: str) -> int:
    """统计中英文混合文本的词语数量。"""
    return len(_WORD_PATTERN.findall(text))


# ---------- 句子特征提取 ----------
_CURLY_QUOTES = ('\u201c', '\u201d', '\u2018', '\u2019')


def count_em_dashes(text: str) -> int:
    """统计破折号数量。"""
    return text.count('——') + text.count('—')


def count_curly_quotes(text: str) -> int:
    """统计弯引号数量。"""
    return sum(text.count(q) for q in _CURLY_QUOTES)


def count_exclamation(text: str) -> int:
    """统计感叹号数量。"""
    return text.count('！') + text.count('!')


def count_question(text: str) -> int:
    """统计问号数量。"""
    return text.count('？') + text.count('?')


# ---------- spaCy 集成（可选）----------
try:
    import spacy
    HAS_SPACY = True
    try:
        _nlp = spacy.load('zh_core_web_sm')
    except OSError:
        _nlp = None
except ImportError:
    HAS_SPACY = False
    _nlp = None


def get_sentences(text: str) -> List[str]:
    """智能句子分割：优先 spaCy，否则使用正则。"""
    if HAS_SPACY and _nlp is not None:
        doc = _nlp(text)
        sents = [sent.text.strip() for sent in doc.sents]
        if sents:
            return sents
    return split_sentences(text)
