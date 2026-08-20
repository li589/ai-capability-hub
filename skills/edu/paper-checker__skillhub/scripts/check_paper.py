"""
Paper Checker - 论文查重与AI率检测（本地版）
不需要API key，直接能用
"""
import argparse
import json
import os
import re
import sys
import math
from collections import Counter
from datetime import datetime


def get_file_text(file_path):
    """提取文件文本内容"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([p.text for p in doc.paragraphs])
        except ImportError:
            print("警告: python-docx未安装，将跳过docx文件处理")
            print("安装命令: pip install python-docx")
            sys.exit(1)
    elif ext == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return '\n'.join([page.extract_text() for page in reader.pages])
        except ImportError:
            print("警告: PyPDF2未安装，将跳过pdf文件处理")
            print("安装命令: pip install PyPDF2")
            sys.exit(1)
    else:
        print(f"错误: 不支持的文件格式 {ext}")
        sys.exit(1)


def preprocess_text(text):
    """文本预处理"""
    # 移除标点符号和空格
    text = re.sub(r'[^\w]', ' ', text)
    # 转小写
    text = text.lower()
    # 分词（简单按空格分）
    words = text.split()
    # 移除单字和停用词
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
              'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
              'would', 'could', 'should', 'may', 'might', 'must',
              '的', '了', '是', '在', '我', '有', '和', '就', '不', '人'}
    words = [w for w in words if len(w) > 1 and w not in stopwords]
    return words


def jaccard_similarity(words1, words2):
    """Jaccard相似度（集合法）"""
    set1 = set(words1)
    set2 = set(words2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    if union == 0:
        return 0
    return intersection / union


def cosine_similarity(words1, words2):
    """余弦相似度（TF-IDF思想）"""
    # 构建词频向量
    all_words = list(set(words1 + words2))
    vec1 = [words1.count(w) for w in all_words]
    vec2 = [words2.count(w) for w in all_words]
    
    # 计算余弦相似度
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)


def ngram_similarity(text, n=3):
    """N-gram相似度"""
    ngrams1 = [text[i:i+n] for i in range(len(text) - n + 1)]
    ngrams2 = [text[i:i+n] for i in range(len(text) - n + 1)]
    
    set1 = set(ngrams1)
    set2 = set(ngrams2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0
    return intersection / union


def check_similarity_local(text):
    """
    本地查重算法
    检测文本中是否有明显重复的模式
    """
    words = preprocess_text(text)
    word_count = len(words)
    unique_words = len(set(words))
    
    # 计算词汇多样性
    diversity = unique_words / word_count if word_count > 0 else 0
    
    # 简单判断：如果词汇多样性太低，可能���复制粘贴
    # 真实论文通常词汇多样性在0.4-0.8之间
    if diversity < 0.3:
        similarity = 85  # 推定高重复
    elif diversity < 0.4:
        similarity = 60
    elif diversity < 0.5:
        similarity = 40
    else:
        similarity = 15  # 正常范围
    
    # 检测重复段落（简单方法：检查连续相同词）
    sentences = re.split(r'[。！？\n]', text)
    repeated_sentences = []
    for i, sent in enumerate(sentences):
        if len(sent) > 50:  # 长句子才检测
            sent_words = preprocess_text(sent)
            for j, other_sent in enumerate(sentences):
                if i != j and len(other_sent) > 50:
                    other_words = preprocess_text(other_sent)
                    sim = jaccard_similarity(sent_words, other_words)
                    if sim > 0.5:  # 50%以上相同
                        repeated_sentences.append({
                            'sentence': sent[:30] + '...',
                            'similar_to': j + 1,
                            'similarity': round(sim * 100, 1)
                        })
    
    # 去重
    seen = set()
    unique_repeated = []
    for r in repeated_sentences:
        key = (r['sentence'], r['similar_to'])
        if key not in seen:
            seen.add(key)
            unique_repeated.append(r)
    
    return {
        'word_count': word_count,
        'unique_words': unique_words,
        'diversity': round(diversity * 100, 1),
        'similarity_percentage': similarity,
        'suspicious_sentences': unique_repeated[:10]  # 最多显示10个
    }


def detect_ai_patterns(text):
    """检测AI生成特征"""
    # AI写作特征检测
    
    # 1. 过渡词统计（AI常用）
    transition_words = ['首先', '其次', '最后', '总之', '综上所述', '由此可见',
                   '显而易见', '研究表明', '一般来说', '事实上',
                   '首先', '其次', '第三', '一方面', '另一方面']
    transition_count = sum(text.count(w) for w in transition_words)
    
    # 2. 句子长度分析（AI倾向用长句）
    sentences = re.split(r'[。！？]', text)
    sentence_lengths = [len(s) for s in sentences if s.strip()]
    avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    
    # 3. 词汇多样性（AI vocab倾向于过于规范化）
    words = preprocess_text(text)
    unique_ratio = len(set(words)) / len(words) if words else 0
    
    # 4. 被动语态使用（AI倾向多用）
    passive_patterns = ['被', '受到', '得以', '获得']
    passive_count = sum(text.count(p) for p in passive_patterns)
    
    # 5. 机械短语检测
    mechanical_phrases = ['值得注意的是', '需要说明的是', '不言而喻', '毋庸置疑',
                      '由此可见一斑', '也就不难理解']
    mechanical_count = sum(text.count(p) for p in mechanical_phrases)
    
    # 计算综合AI率
    ai_score = 0
    
    # 过渡词过多
    if transition_count > 3:
        ai_score += min(transition_count * 5, 20)
    
    # 句子过长
    if avg_sentence_length > 30:
        ai_score += min((avg_sentence_length - 30) * 1, 15)
    
    # 词汇过于规范（多样性太高或太低都不好）
    if unique_ratio > 0.7 or unique_ratio < 0.3:
        ai_score += 15
    
    # 被动语态过多
    if passive_count > 2:
        ai_score += min(passive_count * 5, 10)
    
    # 机械短语
    if mechanical_count > 2:
        ai_score += min(mechanical_count * 8, 15)
    
    # 限制范围
    ai_percentage = min(max(ai_score, 0), 100)
    
    # 生成详细报告
    predictions = []
    
    if transition_count > 2:
        predictions.append({
            'type': '过渡词过多',
            'count': transition_count,
            'severity': 'high' if transition_count > 5 else 'medium'
        })
    
    if avg_sentence_length > 25:
        predictions.append({
            'type': '句子过长',
            'length': round(avg_sentence_length, 1),
            'severity': 'high' if avg_sentence_length > 35 else 'medium'
        })
    
    if unique_ratio < 0.35 or unique_ratio > 0.65:
        predictions.append({
            'type': '词汇多样性异常',
            'ratio': round(unique_ratio * 100, 1),
            'severity': 'medium'
        })
    
    if mechanical_count > 1:
        predictions.append({
            'type': '机械短语',
            'count': mechanical_count,
            'severity': 'medium'
        })
    
    return {
        'word_count': len(words),
        'ai_percentage': ai_percentage,
        'predictions': predictions,
        'details': {
            'transition_words': transition_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'vocabulary_diversity': round(unique_ratio * 100, 1),
            'passive_usage': passive_count,
            'mechanical_phrases': mechanical_count
        }
    }


def generate_report(file_path, similarity_result, ai_result):
    """生成检测报告"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, f"{base_name}_report_{timestamp}.json")
    md_path = os.path.join(output_dir, f"{base_name}_report_{timestamp}.md")
    
    # JSON报告
    report = {
        "file": file_path,
        "check_time": timestamp,
        "similarity": similarity_result,
        "ai_detection": ai_result
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Markdown报告
    sim = similarity_result or {}
    ai = ai_result or {}
    
    md_content = f"""# 论文检测报告

## 基本信息
- 文件：{os.path.basename(file_path)}
- 检测时间：{timestamp}

## 查重结果
- 总重复率：{sim.get('similarity_percentage', 0)}%
- 字数：{sim.get('word_count', 0)}
- 词汇多样性：{sim.get('diversity', 0)}%

### 可疑重复段落
"""
    
    suspicious = sim.get('suspicious_sentences', [])
    if suspicious:
        for s in suspicious:
            md_content += f"- **{s['sentence']}** → 与第{s['similar_to']}段相似度{s['similarity']}%\n"
    else:
        md_content += "- 未检测到明显重复段落\n"
    
    md_content += f"""
## AI率检测结果
- AI率：{ai.get('ai_percentage', 0)}%
- 字数：{ai.get('word_count', 0)}

### 检测详情
"""
    
    details = ai.get('predictions', [])
    if details:
        for d in details:
            md_content += f"- {d['type']}: {d.get('count', d.get('length', d.get('ratio', '')))} ({d['severity']})\n"
    else:
        md_content += "- 未检测到明显AI特征\n"
    
    md_content += "\n## 建议\n"
    
    sim_rate = sim.get('similarity_percentage', 0)
    ai_rate = ai.get('ai_percentage', 0)
    
    if sim_rate > 40:
        md_content += "- ⚠️ 重复率较高，建议人工复查\n"
    elif sim_rate > 20:
        md_content += "- 重复率中等，注意检查可疑段落\n"
    else:
        md_content += "- ✅ 重复率正常\n"
    
    if ai_rate > 50:
        md_content += "- ⚠️ AI率较高，建议进行降AI率处理\n"
    elif ai_rate > 30:
        md_content += "- ⚠️ 检测到一些AI特征，建议检查\n"
    else:
        md_content += "- ✅ 未��测��明显AI特征\n"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"报告已生成:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description='论文查重与AI率检测（本地版）')
    parser.add_argument('--file', required=True, help='论文文件路径')
    parser.add_argument('--check', choices=['similarity', 'ai', 'both'], default='both',
                    help='检测类型: similarity=查重, ai=AI率检测, both=两者')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"错误: 文件不存在 {args.file}")
        sys.exit(1)
    
    print(f"正在读取文件: {args.file}")
    text = get_file_text(args.file)
    print(f"已提取 {len(text)} 字符")
    
    similarity_result = None
    ai_result = None
    
    if args.check in ['similarity', 'both']:
        print("正在查重...")
        similarity_result = check_similarity_local(text)
        print(f"重复率: {similarity_result['similarity_percentage']}%")
        print(f"词汇多样性: {similarity_result['diversity']}%")
    
    if args.check in ['ai', 'both']:
        print("正在检测AI率...")
        ai_result = detect_ai_patterns(text)
        print(f"AI率: {ai_result['ai_percentage']}%")
    
    if similarity_result or ai_result:
        generate_report(args.file, similarity_result, ai_result)
    
    print("检测完成!")


if __name__ == '__main__':
    main()