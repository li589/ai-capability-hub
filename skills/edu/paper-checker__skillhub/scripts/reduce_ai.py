"""
AI Rate Reducer - 论文降AI率工具
降低论文被识别为AI生成的概率
"""
import argparse
import os
import random
import re
import sys


# AI特征词（需要替换的AI常用词）
AI_PATTERNS = {
    "首先": ["开头", "第一", "开始时"],
    "其次": ["接着", "第二", "随后"],
    "最后": ["结尾", "最终", "结束时"],
    "总之": ["总的来说", "综合来看", "总结来说"],
    "显而易见": ["很明显", "不用说", "一目了然"],
    "综上所述": ["总的来看", "从以上"],
    "一般来说": ["通常而言", "通常情况"],
    "事实上": ["实际上", "实则"],
    "需要注意的是": ["特别要", "值得关注"],
    "研究表明": ["有研究指出", "有数据显示"],
    "可以看出": ["能够发现", "可见"],
    "结果表明": ["结果显示", "数据表明"],
    "此外": ["另外", "还有"],
    "同时": ["并且", "并且"],
    "因此": ["所以", "这导致"],
}


# 过渡词（增加human特征）
TRANSITIONS = [
    "这时候",
    "这里需要说明的是",
    "有意思的是",
    "让我想想",
    "从这个角度",
    "实际上",
    "不过",
    "但是",
    "幸运的是",
    "不幸的是",
    "一般来说",
]


def split_into_sentences(text):
    """按句子拆分"""
    pattern = r'([。！？\n]+)'
    parts = re.split(pattern, text)
    
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentences.append(parts[i])
        if i + 1 < len(parts):
            sentences.append(parts[i + 1])
    
    return sentences


def detect_ai_patterns(sentence):
    """检测AI特征"""
    detected = []
    for pattern in AI_PATTERNS.keys():
        if pattern in sentence:
            detected.append(pattern)
    return detected


def replace_ai_patterns(sentence):
    """替换AI特征词"""
    result = sentence
    for pattern, replacements in AI_PATTERNS.items():
        if pattern in sentence:
            # 随机选择一个替换词
            replacement = random.choice(replacements)
            result = result.replace(pattern, replacement, 1)
    return result


def add_human_elements(sentence):
    """添加人性化元素"""
    # 添加过渡词
    if random.random() < 0.2 and len(sentence) > 20:
        transition = random.choice(TRANSITIONS)
        sentence = transition + "，" + sentence
    
    return sentence


def add_personal_analysis(sentence):
    """添加个人分析建议（用于高AI率段落）"""
    suggestions = [
        "（这里可以加入个人案例）",
        "（建议补充具体实例）",
        "（可加入亲身经历）",
        "（需要进一步验证）",
    ]
    
    # 在句末添加建议
    if random.random() < 0.3 and len(sentence) > 30:
        suggestion = random.choice(suggestions)
        sentence = sentence.rstrip() + " " + suggestion
    
    return sentence


def break_monotone(sentence):
    """打破单调句式"""
    # 检测是否有连续短句
    if len(sentence) < 50:
        return sentence
    
    # 拆分并重组长句
    clauses = re.split(r'[，,]', sentence)
    if len(clauses) > 2:
        random.shuffle(clauses)
        sentence = '，'.join(clauses[:len(clauses)])
    
    return sentence


def process_sentence(sentence, intensity='normal'):
    """
    处理单个句子
    
    Args:
        sentence: 原始句子
        intensity: 处理强度 (light, normal, strong)
    """
    # 先检测AI特征
    ai_patterns = detect_ai_patterns(sentence)
    
    # 基础处理：替换AI模式词
    result = replace_ai_patterns(sentence)
    
    # 根据强度添加处理
    if intensity in ['normal', 'strong']:
        result = add_human_elements(result)
    
    if intensity == 'strong':
        result = break_monotone(result)
        result = add_personal_analysis(result)
    
    return result


def suggest_improvements(paragraphs):
    """生成改进建议"""
    suggestions = []
    
    # 检测连续AI模式
    ai_pattern_count = 0
    for para in paragraphs:
        if isinstance(para, str):
            for pattern in AI_PATTERNS.keys():
                ai_pattern_count += para.count(pattern)
    
    if ai_pattern_count > 5:
        suggestions.append("1. 段落中AI模式词使用较多，建议替换为更个人化的表达")
    
    if len(paragraphs) > 3:
        suggestions.append("2. 建议在段落间添加过渡句，使逻辑更连贯")
    
    suggestions.append("3. 建议在关键论点处加入个人案例或分析")
    suggestions.append("4. 可以尝试用第一人称表达观点")
    suggestions.append("5. 检查每个段落是否太长，适当拆分")
    
    return suggestions


def process_file(input_path, output_path, intensity='normal'):
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
    
    print(f"正在使用 {intensity} 强度降AI率...")
    
    # 按段落处理
    paragraphs = text.split('\n\n')
    processed = []
    high_ai_paragraphs = []
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            processed.append(para)
            continue
        
        # 处理段落
        sentences = split_into_sentences(para)
        new_para = []
        
        for sent in sentences:
            if sent.strip() and sent not in '。！？\n':
                new_para.append(process_sentence(sent, intensity))
            else:
                new_para.append(sent)
        
        processed_para = ''.join(new_para)
        
        # 标记高AI率段落
        ai_count = len(detect_ai_patterns(para))
        if ai_count >= 3:
            high_ai_paragraphs.append(f"第{i+1}段: 检测到{ai_count}个AI模式")
        
        processed.append(processed_para)
    
    result = '\n\n'.join(processed)
    
    # 生成建议
    suggestions = suggest_improvements(paragraphs)
    
    suggestions_text = """
# 降AI率建议

## 检测到的高AI率段落
"""
    if high_ai_paragraphs:
        suggestions_text += '\n'.join(high_ai_paragraphs)
    else:
        suggestions_text += "未检测到明显高AI率段落"
    
    suggestions_text += "\n\n## 改进建议\n" + '\n'.join(suggestions)
    
    # 保存结果
    if output_path:
        save_path = output_path
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        save_path = os.path.join(os.path.dirname(input_path), f"{base_name}_deai{ext}")
    
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
    
    # 保存建议
    suggest_path = os.path.join(os.path.dirname(input_path), f"{base_name}_deai_suggestions.md")
    with open(suggest_path, 'w', encoding='utf-8') as f:
        f.write(suggestions_text)
    
    print(f"降AI率完成:")
    print(f"  - 处理后文件: {save_path}")
    print(f"  - 改进建议: {suggest_path}")
    
    return save_path, suggest_path


def main():
    parser = argparse.ArgumentParser(description='论文降AI率工具')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--output', help='输出文件路径（可选）')
    parser.add_argument('--intensity', choices=['light', 'normal', 'strong'],
                    default='normal', help='处理强度')
    
    args = parser.parse_args()
    
    # 检查文件
    if not os.path.exists(args.file):
        print(f"错误: 文件不存在 {args.file}")
        sys.exit(1)
    
    # 处理
    process_file(args.file, args.output, args.intensity)


if __name__ == '__main__':
    main()