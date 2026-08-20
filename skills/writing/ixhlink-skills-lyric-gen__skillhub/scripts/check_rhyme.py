#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌词押韵检查脚本

按中文十三辙归类每段句末字，标记跨韵与落音不统一，
并按曲风预设的韵脚密度给出建议。

依赖：pypinyin（用于取拼音）。未安装时给出安装提示：
    .venv/bin/pip install pypinyin

用法:
  python scripts/check_rhyme.py lyrics/歌名.md
  python scripts/check_rhyme.py lyrics/歌名.md --genre rap
  python scripts/check_rhyme.py lyrics/歌名.md --genre pop
"""

import io
import re
import sys
from pathlib import Path

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from pypinyin import lazy_pinyin, Style
except ImportError:
    print('缺少依赖 pypinyin，请先安装：')
    print('  .venv/bin/pip install pypinyin')
    sys.exit(1)


# 十三辙：韵母 -> 辙名
# final 为去声调后的韵母字符串
ZHE_MAP = [
    ('发花', ('a', 'ia', 'ua')),
    ('梭波', ('o', 'e', 'uo')),
    ('乜斜', ('ie', 'üe', 'ue')),
    ('一七', ('i', 'ü', 'v')),
    ('姑苏', ('u',)),
    ('怀来', ('ai', 'uai')),
    ('灰堆', ('ei', 'uei', 'ui')),
    ('遥条', ('ao', 'iao')),
    ('由求', ('ou', 'iou', 'iu')),
    ('言前', ('an', 'ian', 'uan', 'üan', 'van')),
    ('人辰', ('en', 'in', 'un', 'ün', 'vn')),
    ('江阳', ('ang', 'iang', 'uang')),
    ('中东', ('ong', 'iong')),
]

# 曲风预设：建议最低押韵密度（押韵句 / 总句）
GENRE_PRESETS = {
    'pop': (0.5, '流行'),
    'ballad': (0.35, '民谣'),
    'rap': (0.85, '说唱'),
    'guofeng': (0.7, '古风'),
    'rock': (0.4, '摇滚'),
    'electronic': (0.5, '电子'),
    'rnb': (0.6, 'R&B/布鲁斯'),
    'generic': (0.5, '通用'),
}

SECTION_RE = re.compile(r'^\s*\[([^\]]+)\]')
SENTENCE_END_RE = re.compile(r'[，。；！？、,\.\!\?\n]')


def classify_zhe(pinyin_final: str) -> str:
    """根据韵母归类十三辙，未命中返回「-」。

    按「最长韵母优先」匹配，避免短韵母（o/e/i/u）误吞长韵母
    （如 iao 不应因 endswith('o') 被归入梭波辙，而属遥条辙）。
    """
    f = pinyin_final.lower().replace('v', 'ü')
    # 展平 (韵母, 辙名)，按韵母长度降序：先匹配精确或最长后缀
    pairs = []
    for zhe, finals in ZHE_MAP:
        for fin in finals:
            pairs.append((fin.replace('v', 'ü'), zhe))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    for fin, zhe in pairs:
        if f == fin or f.endswith(fin):
            return zhe
    return '-'

def last_han_char(sentence: str) -> str:
    """取句末最后一个汉字"""
    for ch in reversed(sentence):
        if '\u4e00' <= ch <= '\u9fff':
            return ch
    return ''


def parse_sections(text: str):
    """按 [段名] 拆分段落，返回 [(段名, [句子])]"""
    sections = []
    cur_name = None
    cur_lines = []
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            if cur_name is not None:
                sections.append((cur_name, cur_lines))
            cur_name = m.group(1).strip()
            cur_lines = []
        else:
            stripped = line.strip()
            if stripped:
                cur_lines.append(stripped)
    if cur_name is not None:
        sections.append((cur_name, cur_lines))
    return sections


def split_sentences(line: str):
    """一行可能含多句，按标点拆分"""
    parts = SENTENCE_END_RE.split(line)
    return [p.strip() for p in parts if p.strip()]


def analyze(text: str, genre_key: str):
    sections = parse_sections(text)
    min_density, genre_label = GENRE_PRESETS.get(genre_key, GENRE_PRESETS['generic'])

    print('\n' + '=' * 60)
    print(f'{genre_label}歌词押韵检查报告（建议密度 ≥ {min_density:.0%}）')
    print('=' * 60)

    total_sents = 0
    rhymed_sents = 0

    for name, lines in sections:
        sentences = []
        for ln in lines:
            sentences.extend(split_sentences(ln))
        if not sentences:
            continue

        print(f'\n[{name}]')
        zhes = []
        for s in sentences:
            ch = last_han_char(s)
            if not ch:
                print(f'  · {s}  （无汉字句末，跳过）')
                continue
            py = lazy_pinyin(ch, style=Style.FINALS, errors='ignore')
            final = py[0] if py else ''
            zhe = classify_zhe(final) if final else '-'
            zhes.append(zhe)
            total_sents += 1
            print(f'  · {s}  末字「{ch}」 -> {zhe}辙')

        # 段内韵辙统计
        if zhes:
            from collections import Counter
            cnt = Counter(zhes)
            main = cnt.most_common(1)[0]
            density = sum(1 for z in zhes if z == main[0]) / len(zhes)
            rhymed = sum(1 for z in zhes if z != '-')
            rhymed_sents += rhymed
            cross = [z for z in set(zhes) if z != '-' and z != main[0]]
            flag = '✅' if density >= 0.5 else '⚠️'
            print(f'  {flag} 主韵：{main[0]}辙（{main[1]}/{len(zhes)}）'
                  + (f' | 跨韵：{",".join(cross)}' if cross else ''))

    print('\n' + '-' * 60)
    if total_sents:
        overall = rhymed_sents / total_sents
        print(f'总计 {total_sents} 句，押韵句 {rhymed_sents}，整体密度 {overall:.0%}')
        if overall < min_density:
            print(f'⚠️ 低于 {genre_label} 建议密度 {min_density:.0%}，建议加强句末押韵（查 references/rhyme-system.md）')
        else:
            print(f'✅ 达到 {genre_label} 建议密度')
    else:
        print('未检测到有效歌词句。请确认文件含 [段名] 标记的歌词正文。')
    print('-' * 60)


def parse_args(argv):
    genre = 'generic'
    target = None
    args = argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--genre':
            i += 1
            if i < len(args):
                genre = args[i].lower()
                i += 1
        elif a.startswith('--'):
            i += 1
        else:
            target = a
            i += 1
    return target, genre


def print_usage():
    print('用法:')
    print('  python scripts/check_rhyme.py <歌词文件> [--genre <曲风键>]')
    print('')
    print('曲风键 (--genre):')
    for k, (_, label) in GENRE_PRESETS.items():
        print(f'  {k:12s} {label}')
    print('')
    print('示例:')
    print('  python scripts/check_rhyme.py lyrics/歌名.md --genre pop')
    print('  python scripts/check_rhyme.py lyrics/歌名.md --genre rap')


def main():
    target, genre = parse_args(sys.argv)
    if not target:
        print_usage()
        return
    path = Path(target)
    if not path.exists():
        print(f'错误: 文件不存在 - {target}')
        return
    text = path.read_text(encoding='utf-8')
    analyze(text, genre)


if __name__ == '__main__':
    main()
