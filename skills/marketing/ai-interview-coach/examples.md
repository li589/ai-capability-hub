# AI Interview Coach - Examples

This document provides concrete examples of using the AI Interview Coach skill.

## Example 1: Resume-Based Interview (Frontend Developer)

**User Input:**
> "请帮我准备前端工程师的面试，这是我的简历：frontend-developer-resume.pdf"

**Process:**
1. Read PDF file `frontend-developer-resume.pdf`
2. Extract content:
   - 3 years React/Vue experience
   - Built e-commerce platform
   - Proficient in TypeScript, Webpack, CSS
   - Led team of 4 developers

**Sample Generated Questions:**

```markdown
### 第1题 (Technical - React)
请解释 React 的 Virtual DOM 工作原理，以及它与真实 DOM 的区别是什么？
在什么情况下 Virtual DOM 的优势最明显？

### 第5题 (Project Experience)
你在简历中提到主导开发了一个电商平台的前端架构。
请详细描述这个平台的架构设计，包括技术选型、性能优化方案，
以及你是如何解决高并发场景下的渲染性能问题的？

### 第8题 (Behavioral)
作为4人开发团队的负责人，你如何处理团队成员之间的技术分歧？
请举一个具体的例子说明。
```

---

## Example 2: Job Position-Based Interview (Product Manager)

**User Input:**
> "我想面试产品经理职位，请帮我生成一些练习题"

**Process:**
1. No resume file provided
2. Use job role "产品经理" as input
3. Generate generic PM interview questions

**Sample Generated Questions:**

```markdown
### 第2题 (Product Thinking)
假设你负责一个在线教育平台的产品，用户流失率在第三个月显著上升。
请描述你会如何分析这个问题，并提出至少3个可能的解决方案。

### 第6题 (Behavioral)
请描述一次你与研发团队在技术实现方案上产生分歧的经历。
你是如何处理的？最终结果如何？

### 第10题 (Scenario)
公司计划推出一个全新的社交功能，但市场调研显示竞品类似功能的用户接受度不高。
作为产品经理，你会如何决定是否推进这个项目？请列出你的分析框架。
```

---

## Example 3: Markdown Resume

**User Input:**
> "基于我的简历生成面试题：resume.md"

**Resume Content (resume.md):**
```markdown
# 王小明

## 工作经历
- 字节跳动 | 后端工程师 | 2021-至今
  - 负责抖音推荐系统的微服务架构设计
  - 优化Redis集群，QPS提升300%
  
## 技能
- Go, Python, Java
- Kubernetes, Docker
- Redis, MySQL, Kafka
```

**Sample Generated Questions:**

```markdown
### 第3题 (Technical - System Design)
你在抖音负责推荐系统的微服务架构。
请设计一个能够支撑每秒10万请求的推荐服务架构，
包括服务拆分策略、缓存策略和降级方案。

### 第4题 (Technical - Performance)
你提到优化Redis集群使QPS提升了300%。
请详细描述你遇到的性能瓶颈是什么，使用了哪些优化手段，
以及你是如何验证优化效果的？

### 第9题 (Technical - Database)
在高并发场景下，MySQL和Redis的数据一致性如何保证？
请列举至少3种方案并分析各自的优缺点。
```

---

## Example 4: Full Output Document Example

Below is a condensed example of the complete output format:

```markdown
# 面试练习题 - 后端工程师

> Generated on: 2026-04-14
> Source: resume.md (字节跳动后端工程师)

---

## 答题说明

1. 请在每道题下方的空白处写下你的答案
2. 完成后对照文档末尾的参考答案进行自我评估
3. 建议限时完成，模拟真实面试场景

---

## 面试题目

### 第1题
你在字节跳动负责抖音推荐系统的微服务架构设计。
请描述你是如何进行服务拆分的，以及你在设计时考虑了哪些核心因素？

---

（请在此作答）



---

### 第2题
请解释分布式系统中的CAP定理，并结合你的项目经验，
说明在推荐系统场景下你是如何权衡Consistency和Availability的？

---

（请在此作答）



---

[Questions 3-10 follow same format...]

---

## 参考答案

### 第1题答案

**考察点**: 微服务架构设计能力、系统思维、实际项目经验

**参考答案**:
一个优秀的回答应该包含以下要点：

1. **服务拆分原则**
   - 按业务领域拆分（Domain-Driven Design）
   - 单一职责原则
   - 关注服务间的依赖关系

2. **核心考虑因素**
   - 数据一致性要求
   - 服务间的通信成本
   - 团队组织结构
   - 部署和运维复杂度

3. **具体实践**
   - 用户服务、内容服务、推荐服务分离
   - 使用消息队列解耦
   - API网关统一入口

**答题建议**:
- 体现DDD思想
- 结合实际项目经验
- 说明权衡取舍的思考过程

### 第2题答案

**考察点**: 分布式系统理论理解、实际应用能力

**参考答案**:
CAP定理指出分布式系统无法同时满足一致性(Consistency)、
可用性(Availability)和分区容错性(Partition Tolerance)。

在推荐系统场景下的权衡：

1. **AP优先场景**
   - 用户个性化推荐：短暂的不一致可接受，但服务必须可用
   - 使用最终一致性方案

2. **CP优先场景**
   - 用户行为数据写入：需要强一致性
   - 使用分布式事务或补偿机制

3. **具体实践**
   - 读写分离架构
   - 缓存策略设计
   - 降级方案准备

**答题建议**:
- 先清晰解释CAP定理
- 结合具体业务场景分析
- 展示实际解决方案
```

---

## Usage Patterns

### Pattern 1: File Path Input

```
User: "帮我生成面试题，简历文件是 ./documents/my-resume.pdf"
Action: Read PDF file → Generate questions → Output markdown
```

### Pattern 2: Direct Role Input

```
User: "准备一下Java后端工程师的面试题"
Action: Use "Java后端工程师" as context → Generate questions → Output markdown
```

### Pattern 3: Follow-up Refinement

```
User: "这些题太难了，能不能简单一点？"
Action: Adjust question difficulty → Regenerate with easier questions
```

---

## Common Interview Topics by Role

### 前端工程师
- React/Vue生命周期和原理
- 浏览器渲染机制
- 性能优化策略
- 跨域解决方案
- 前端工程化

### 后端工程师
- 分布式系统设计
- 数据库优化
- 缓存策略
- 消息队列
- 微服务架构

### 产品经理
- 需求分析方法论
- 数据分析能力
- 用户研究
- 竞品分析
- 项目推进经验

### 算法工程师
- 机器学习理论基础
- 特征工程
- 模型评估
- 大规模数据处理
- A/B测试设计
