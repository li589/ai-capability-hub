---
name: paper-checker
description: 论文查重与AI率检测工具，支持中文英文论文查重、AI率检测、降重和降AI率处理。用于：(1)上传论文文件进行查重和AI率检测 (2)生成详细的重复率和AI率报告 (3)对高重复率内容进行降重改写 (4)对高AI率内容进行降AI率处理。不需要API key，直接能用。
---

# Paper Checker - 论文查重与AI率检测

## 功能概述

- **查重** - 本地文本相似度算法，检测重复率
- **AI率检测** - 基于规则判断，检测AI生成特征
- **报告生成** - 输出详细的重复率、AI率报告
- **降重** - paraphrasing改写、同义词替换、句式调整
- **降AI率** - 替换AI特征词、添加个人化元素

## 使用方法

### 安装依赖（可选）

```bash
pip install python-docx PyPDF2
```

- `python-docx`: 处理Word文件
- `PyPDF2`: 处理PDF文件
- 不安装也能处理txt文件

### 查重流程

#### 1. 上传论文

支持格式：`.docx`, `.pdf`, `.txt`

将论文文件放入skill目录，或直接提供文件路径。

#### 2. 检测

```bash
python scripts/check_paper.py --file <论文文件路径> --check both
```

参数说明：
- `--check similarity` - 仅查重
- `--check ai` - 仅AI率检测
- `--check both` - 查重+AI率（默认）

#### 3. 查看报告

检测完成后，报告保存在 `output/` 目录：
- `output/_report_<时间戳>.json` - 详细JSON报告
- `output/_report_<时间戳>.md` - 可读Markdown报告

## 降重流程

### 仅查重

```bash
python scripts/reduce_similarity.py --file <论文文件路径>
```

降重方法：
- `paraphrasing` - 改写换表达（默认）
- `synonym` - 同义词替换
- `restructure` - 句式调整

### 降AI率

```bash
python scripts/reduce_ai.py --file <论文文件路径>
```

处理强度：
- `light` - 轻度
- `normal` - 常规（默认）
- `strong` - 强力

## 算法说明

### 查重算法

1. **Jaccard相似度** - 词汇集合交集
2. **余弦相似度** - 词频向量
3. **N-gram相似度** - 字符n-gram匹配

判断逻辑：
- 词汇多样性 < 30% → 推定高重复
- 连续相同句子 > 50% → 标记为可疑

### AI率检测算法

检测以下AI特征：

1. **过渡词统计** - 首先/其次/最后等AI常用词
2. **句子长度** - AI倾向用长句
3. **词汇多样性** - 过于规范或过于单调
4. **被动语态** - 被/受到等多
5. **机械短语** - 值得注意的是等套话

## 输出示例

### 查重报告

```markdown
# 论文检测报告

## 基本信息
- 文件：example.docx
- 检测时间：2024-01-01 12:00

## 查重结果
- 总重复率：15%
- 字数：5000
- 词汇多样性：65%

### 可疑重复段落
- 与第3段相似度85%
- 与第5段相似度72%
```

### AI率报告

```markdown
## AI率检测结果
- AI率：45%
- 字数：5000

### 检测详情
- 过渡词过多: 5 (high)
- 句子过长: 35 (medium)
- 词汇多样性异常: 75% (medium)
```

## 注意事项

1. 首次使用无需配置任何key
2. 支持Word/PDF/Txt格式
3. 建议降重后人工检查语义
4. 算法基于统计规律，仅供参考