
---

## 二、修正后的 `check_chapter_wordcount_tomato.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄章节字数检查脚本
检查字数是否在2200-2800字最佳区间
"""

import os
import re
import sys
from pathlib import Path

# 处理 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    # 更稳健的编码替换方式
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def count_chinese_words(text: str) -> int:
    """统计中文字符个数（不含Markdown格式符号）"""
    # 移除Markdown标题符号
    text = re.sub(r'#{1,6}\s*', '', text)
    # 移除加粗、斜体、删除线
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    # 移除行内代码
    text = re.sub(r'`(.*?)`', r'\1', text)
    # 移除链接，保留文本
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 统计中文字符（Unicode汉字区间）
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)


def extract_content_from_chapter(file_path: Path) -> str:
    """从章节文件中提取正文内容（跳过元数据部分）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    content_start = 0
    # 查找第一个以 # 开头且包含“章”字的行，视为标题行，从下一行开始计为正文
    for i, line in enumerate(lines):
        if line.startswith('#') and '章' in line:
            content_start = i + 1
            break
    
    # 如果没有找到标题行，则默认从第一行开始统计
    return '\n'.join(lines[content_start:])


def check_chapter(file_path: str, min_words: int = 2200, max_words: int = 2800) -> dict:
    """检查单个章节的字数"""
    path = Path(file_path)
    if not path.exists():
        return {
            'file': str(path),
            'exists': False,
            'word_count': 0,
            'status': 'error',
            'message': f'文件不存在: {file_path}'
        }
    
    main_content = extract_content_from_chapter(path)
    word_count = count_chinese_words(main_content)
    
    if word_count < min_words:
        status = 'short'
        message = f'字数: {word_count} (✗ 不足，需要至少 {min_words} 字)'
    elif word_count > max_words:
        status = 'long'
        message = f'字数: {word_count} (⚠️ 超标，建议精简至 {max_words} 字以内)'
    else:
        status = 'pass'
        message = f'字数: {word_count} (✓ 最佳区间 {min_words}-{max_words} 字)'
    
    return {
        'file': str(path),
        'exists': True,
        'word_count': word_count,
        'status': status,
        'message': message
    }


def check_all_chapters(directory: str, pattern: str = '第*.md', 
                       min_words: int = 2200, max_words: int = 2800) -> list:
    """检查目录下所有章节文件"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f'错误: 目录不存在 - {directory}')
        return []
    
    chapter_files = sorted(dir_path.glob(pattern))
    results = [check_chapter(str(f), min_words, max_words) for f in chapter_files]
    return results


def print_results(results: list, min_words: int = 2200, max_words: int = 2800):
    """打印检查报告"""
    if not results:
        print('没有找到章节文件')
        return
    
    total_words = 0
    passed = short = long = error = 0
    
    print('\n' + '=' * 60)
    print('番茄章节字数检查报告')
    print(f'最佳区间: {min_words}-{max_words} 字')
    print('=' * 60)
    
    for result in results:
        if not result['exists']:
            error += 1
            icon = '❌'
        elif result['status'] == 'pass':
            passed += 1
            icon = '✅'
            total_words += result['word_count']
        elif result['status'] == 'short':
            short += 1
            icon = '⚠️'
            total_words += result['word_count']
        elif result['status'] == 'long':
            long += 1
            icon = '📈'
            total_words += result['word_count']
        else:
            error += 1
            icon = '❌'
        
        print(f'\n{icon} {Path(result["file"]).name}')
        print(f'   {result["message"]}')
    
    print('\n' + '-' * 60)
    print(f'总计: {len(results)} 章 | {passed} 章达标 | {short} 章不足 | {long} 章超标 | 总字数: {total_words:,}')
    print('-' * 60)
    
    if short > 0:
        print(f'\n⚠️ 有 {short} 章内容不足 {min_words} 字，建议使用扩充技巧（参考 content-expansion.md）')
    if long > 0:
        print(f'\n📈 有 {long} 章内容超过 {max_words} 字，建议精简，番茄短篇过长会降低完读率。')


def main():
    min_words = 2200
    max_words = 2800
    
    if len(sys.argv) < 2:
        print('用法: python check_chapter_wordcount_tomato.py <章节文件路径> [最小字数] [最大字数]')
        print('      python check_chapter_wordcount_tomato.py --all <目录路径> [最小字数] [最大字数]')
        print(f'      默认字数区间: {min_words}-{max_words}')
        return
    
    if sys.argv[1] == '--all':
        if len(sys.argv) < 3:
            print('错误: 使用 --all 时需要指定目录路径')
            return
        directory = sys.argv[2]
        if len(sys.argv) >= 5:
            min_words = int(sys.argv[3])
            max_words = int(sys.argv[4])
        elif len(sys.argv) == 4:
            min_words = int(sys.argv[3])
        results = check_all_chapters(directory, min_words=min_words, max_words=max_words)
        print_results(results, min_words, max_words)
    else:
        file_path = sys.argv[1]
        if len(sys.argv) >= 4:
            min_words = int(sys.argv[2])
            max_words = int(sys.argv[3])
        elif len(sys.argv) == 3:
            min_words = int(sys.argv[2])
        result = check_chapter(file_path, min_words, max_words)
        print_results([result], min_words, max_words)


if __name__ == '__main__':
    main()