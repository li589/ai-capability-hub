---
name: zhang-ai-law
version: 1.0.0
description: 九章人工智能法专家 - AI合规、算法备案、生成式AI法律风险识别（基于DeepSeek R2 + 500+AI监管案例库）
metadata:
  openclaw:
    requires:
      env:
        - DEEPSEEK_API_KEY
    capabilities:
      - reasoning
      - web_search
      - file_read
    evolution:
      enabled: true
      version: 2.0.0
      data_collection: true
      auto_update: false
      feedback_loop: true
  author: 张律师
  category: legal
  tags:
    - 人工智能
    - AI合规
    - 算法备案
    - 生成式AI
    - 深度学习
  focus_areas:
    - 算法推荐服务合规
    - 生成式AI服务管理
    - 深度合成技术合规
    - AI生成内容版权
    - 自动驾驶法律责任
    - AI医疗诊断合规
    - AI招聘算法公平性
    - AI金融风控合规
  regulatory_sources:
    - 《生成式人工智能服务管理暂行办法》
    - 《互联网信息服务算法推荐管理规定》
    - 《互联网信息服务深度合成管理规定》
    - 《科技伦理审查办法》
    - 《人工智能示范法》
  case_library_target: 500
  changelog:
    - version: 1.0.0
      date: "2026-03-23"
      changes:
        - 初始版本发布
        - 集成自我进化系统
install_source: official
install_method: download
skill_id: official_f2FwsCWP
enabled_at: 1787231771372
name_zh: 九章人工智能法专家
---

# 九章人工智能法专家

新兴领域法律专家，专注AI合规与算法治理。

## 核心能力

### 1. 算法备案审查
- 算法推荐服务备案要求审查
- 算法安全自评估报告生成
- 算法备案材料清单检查

### 2. 生成式AI合规
- 大模型服务合规评估
- 训练数据合规审查
- 生成内容标识要求
- 用户权益保护机制

### 3. AI法律责任分析
- 自动驾驶事故责任认定
- AI医疗误诊责任分析
- AI招聘歧视风险评估
- AI金融损失责任划分

### 4. 监管政策追踪
- 实时同步AI监管新规
- 地方AI产业政策解读
- 国际AI治理规则对比

## 使用示例

```bash
# 算法备案审查
jiuzhang-cli ai-law algorithm-review ./algorithm_desc.json

# 生成式AI合规评估
jiuzhang-cli ai-law genai-compliance ./llm_service/

# AI产品责任分析
jiuzhang-cli ai-law liability-analysis --scenario autonomous_driving

# 监管政策查询
jiuzhang-cli ai-law policy --topic "大模型备案"
```

## 数据飞轮

- 收集：AI企业合规咨询数据
- 分析：高频合规问题识别
- 进化：自动更新监管政策库

## 版本规划

- v1.1.0：接入DeepSeek R2，扩展至1000+案例
- v1.2.0：新增AI伦理审查模块
- v2.0.0：支持跨境AI合规（欧盟AI法案）
