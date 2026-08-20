"""
Paper Reducer - 论文降重工具
支持paraphrasing改写、同义词替换、句式调整
"""
import argparse
import os
import re
import random
import sys


# 同义词词典（简化版，实际可用更丰富的词典）
SYNONYMS = {
    "研究": ["探讨", "分析", "考察", "剖析"],
    "方法": ["途径", "手段", "方式", "措施"],
    "结果": ["成果", "结论", "发现", "Outcome"],
    "问题": ["议题", "难题", "挑战", "情况"],
    "影响": ["作用", "效应", "后果", "冲击"],
    "原因": ["成因", "因素", "根源", "动因"],
    "重要": ["关键", "主要", "核心", "显著"],
    "发展": ["成长", "演进", "进步", "变迁"],
    "使用": ["运用", "应用", "采用", "采纳"],
    "提供": ["给予", "供应", "带来", "带来"],
    "通过": ["经由", "借助", "依靠", "凭借"],
    "基于": ["依据", "根据", "按照", "遵照"],
    "目前": ["当前", "现今", "现在", "当下"],
    "本文": ["本篇", "本论文", "本研究"],
    "认为": ["觉得", "看法", "观点", "主张"],
    "表明": ["显示", "说明", "体现", "揭示"],
    "证明": ["证实", "表明", "验证", "说明"],
    "分析": ["剖析", "解析", "研究", "探讨"],
    "总结": ["归纳", "概括", "汇总", "综述"],
    "提出": ["给出", "指出", "阐述", "论述"],
    "相关": ["关联", "联系", "涉及", "有关"],
    "不同": ["差异", "区别", "各有", "不一致"],
    "包括": ["包含", "涵盖", "含有", "涉及"],
    "应该": ["需要", "应当", "必须", "理应"],
    "可能": ["或许", "也许", "大概", "或许"],
    "因为": ["由于", "基于", "鉴于", "依据"],
    "所以": ["因此", "故而", "因而", "于是"],
    "但是": ["然而", "但是", "不过", "可是"],
    "如果": ["假设", "倘若", "要是", "假如"],
    "虽然": ["尽管", "虽然", "固然", "虽然"],
}


def get_paraphrase(text, method='paraphrase'):
    """
    降重处理主函数
    
    Args:
        text: 原始文本
        method: 降重方法
            - paraphrase: 改写换表达
            - synonym: 同义词替换
            - restructure: 句式调整
    """
    if method == 'synonym':
        return synonym_replace(text)
    elif method == 'restructure':
        return restructure(text)
    elif method == 'paraphrase':
        return paraphrase(text)
    else:
        return text


def synonym_replace(text):
    """同义词替换"""
    words = text.split()
    replaced = []
    
    for word in words:
        # 查找匹配的同义词
        key = word
        if key in SYNONYMS and random.random() < 0.3:
            new_word = random.choice(SYNONYMS[key])
            replaced.append(new_word)
        else:
            replaced.append(word)
    
    return ' '.join(replaced)


def restructure(text):
    """句式调整"""
    sentences = re.split(r'([。！？])', text)
    result = []
    
    for i, s in enumerate(sentences):
        if not s.strip() or s in '。！？':
            result.append(s)
            continue
        
        # 拆分句子成分
        # 简单实现：把被字句改成把字句，把字句改成被字句
        modified = s
        
        # 检查是否有"被"字
        if '被' in s:
            # 尝试把"被"字句转换成主动句
            parts = s.split('被')
            if len(parts) == 2:
                modified = parts[1] + "由" + parts[0].strip() + "完成"
        
        # 检查是否有"把"字
        elif '把' in s:
            parts = s.split('把')
            if len(parts) == 2:
                modified = parts[1] + "进行" + parts[0].strip()
        
        result.append(modified)
    
    return ''.join(result)


def paraphrase(text):
    """paraphrasing改写"""
    # 先同义词替换，再句式调整
    result = synonym_replace(text)
    return restructure(result)


def split_into_sentences(text):
    """按句子拆分文本"""
    # 保留分隔符
    pattern = r'([。！？\n]+)'
    parts = re.split(pattern, text)
    
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentences.append(parts[i])
        if i + 1 < len(parts):
            sentences.append(parts[i + 1])
    
    return sentences


def process_file(input_path, output_path, method='paraphrase'):
    """处理文件"""
    # 读取文件
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == '.txt':
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(input_path)
            text = '\n'.join([p.text for p in doc.paragraphs])
        except ImportError:
            print("错误: 需要安装 python-docx 库")
            sys.exit(1)
    else:
        print(f"错误: 不支持的文件格式 {ext}")
        sys.exit(1)
    
    # 处理文本
    print(f"正在使用 {method} 方法降重...")
    
    sentences = split_into_sentences(text)
    processed = []
    
    for i, sentence in enumerate(sentences):
        if sentence.strip() and sentence not in '。！？\n':
            # 对非空句子进行降重
            processed.append(get_paraphrase(sentence, method))
        else:
            processed.append(sentence)
    
    result = ''.join(processed)
    
    # 保存结果
    if output_path:
        save_path = output_path
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        save_path = os.path.join(os.path.dirname(input_path), f"{base_name}_reduced{ext}")
    
    # 如果是docx，需要用python-docx保存
    if ext == '.docx':
        try:
            from docx import Document
            doc = Document()
            for para in result.split('\n'):
                doc.add_paragraph(para)
            doc.save(save_path)
        except ImportError:
            print("错误: 需要安装 python-docx 库")
            sys.exit(1)
    else:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(result)
    
    print(f"降重完成，结果已保存到: {save_path}")
    return save_path


def main():
    parser = argparse.ArgumentParser(description='论文降重工具')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--output', help='输出文件路径（可选）')
    parser.add_argument('--method', choices=['paraphrase', 'synonym', 'restructure'], 
                    default='paraphrase', help='降重方法')
    
    args = parser.parse_args()
    
    # 检查文件
    if not os.path.exists(args.file):
        print(f"错误: 文件不存在 {args.file}")
        sys.exit(1)
    
    # 处理
    process_file(args.file, args.output, args.method)


if __name__ == '__main__':
    main()