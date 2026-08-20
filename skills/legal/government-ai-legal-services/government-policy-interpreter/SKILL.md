# 政府政策智能解读技能

**技能名称：** government-policy-interpreter
**技能版本：** 1.0.0
**创建日期：** 2026-03-28
**开发者：** 阿拉丁
**指导：** 张海洋
**标准版本：** AI政府法律服务全球标准 v1.1

---

## 🎯 技能概述

AI自动解读政府政策，识别政策关键点，生成政策摘要，分析政策影响，提供实施指导。

---

## ✨ 核心功能

### 1. 政策智能解读

**功能描述：**
- 自动解读政府政策内容
- 识别政策关键点
- 生成政策摘要
- 分析政策影响
- 提供实施指导

**技术特点：**
- NLP自然语言处理
- 智能关键词提取
- 政策影响评估算法
- 实施指导生成

### 2. 政策关键点提取

**提取内容：**
- 政策目标
- 主要措施
- 保障措施
- 责任主体
- 适用范围

### 3. 政策摘要生成

**生成类型：**
- 完整版摘要（前5句）
- 简化版摘要（前3句 + 后2句）
- 一句话摘要

### 4. 政策影响评估

**评估维度：**
- 经济影响
- 社会影响
- 法律影响
- 环境影响
- 总体影响

### 5. 实施指导生成

**指导内容：**
- 实施步骤
- 实施时间线
- 实施要求
- 所需资源
- 实施风险
- 监控措施

### 6. 适用性检查

**检查内容：**
- 适用范围
- 适用条件
- 地域限制
- 主体限制

### 7. 合规性检查

**检查内容：**
- 与上位法一致性
- 政策冲突检查
- 敏感内容识别

---

## 🚀 使用方法

### JavaScript API

```javascript
const GovernmentPolicyInterpreter = require('./policy-interpreter');

const interpreter = new GovernmentPolicyInterpreter();

// 解读政策
const policyData = {
    name: '关于推进乡村振兴的政策',
    issuingAuthority: '国务院',
    publishDate: '2026-03-28',
    effectiveDate: '2026-04-01',
    expiryDate: null,
    content: '...'
};

const analysis = await interpreter.interpretPolicy(policyData, {
    level: 'county', // provincial, prefecture, county, township, village
    simplify: false,
    includeImpact: true,
    includeGuidance: true
});

// 生成报告
const report = interpreter.generateReport(analysis, 'markdown');

console.log(report);
```

### 输出示例

**JSON格式：**
```json
{
  "policy": {...},
  "keyPoints": [...],
  "summary": "...",
  "scope": [...],
  "validity": {...},
  "authority": {...},
  "relatedLaws": [...],
  "relatedPolicies": [...],
  "impact": {...},
  "guidance": {...},
  "applicability": {...},
  "compliance": {...}
}
```

**Markdown格式：**
```markdown
# 政策解读报告

**政策名称：** 关于推进乡村振兴的政策
**发布机关：** 国务院
**发布日期：** 2026-03-28
**生效日期：** 2026-04-01

## 📋 政策摘要
...

## 🎯 政策关键点
...

## 📊 政策影响评估
...
```

---

## 🏷 标签

- government
- policy
- interpretation
- AI
- legal
- analysis
- impact

---

## 📄 许可证

MIT License

---

## 📞 技术支持

**开发者：** 阿拉丁  
**指导：** 张海洋  
**团队：** 法律AI团队

---

## 📚 相关文档

- **政府标准：** AI政府法律服务全球标准 v1.1
- **技能包：** AI政府标准技能包

---

## 🔧 技术栈

- 运行环境：Node.js
- AI推理：OpenRouter
- NLP：自然语言处理
- 数据处理：JavaScript

---

**技能已完成，可立即使用！**