<div align="center">

# AI Interview Coach

> *「你好考官，帮我准备面试」*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Cursor](https://img.shields.io/badge/Cursor-Skill-blue)](https://cursor.com)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

<br>

**你的专属 AI 面试考官，帮你高效准备面试。**

基于简历或职位描述，**每次生成10道**针对性面试题，附带参考答案。

<br>

[效果示例](#效果示例) · [安装](#安装) · [使用方法](#使用方法) · [面试题设计](#面试题设计)

</div>

---

## 效果示例

### 基于简历生成

```
用户      ❯ 你好考官，这是我的简历：resume.pdf

考官      ❯ 好的，我已阅读你的简历。你申请的是前端工程师职位，
            有3年 React 经验。我为你准备了10道面试题：
            
            第1题：请解释 React 的 Virtual DOM 工作原理...
            
            参考答案见文档末尾。
```

### 基于职位生成

```
用户      ❯ 我想面试 AI 算法工程师

考官      ❯ 明白。针对 AI 算法工程师职位，我为你生成10道面试题：
            
            第1题：请解释 Transformer 的注意力机制...
            第2题：如何处理类别不平衡的数据集？
            ...
```

### 自然对话方式

```
用户      ❯ 你好考官，我是3年经验的 Java 后端，帮我准备面试

考官      ❯ 好的。针对你的 Java 后端背景，我准备了10道题：
            
            第1题：请解释 Spring Boot 的自动配置原理...
            第2题：你如何设计一个高并发的订单系统？
            ...
```

---

## 安装

### 一键安装（推荐）

适用于 Cursor、Claude Code、Codex 等支持 skills 的 AI 工具：

```bash
npx skills add HogoZhang/ai-interview-coach
```

### 手动安装

1. 克隆或下载本项目
2. 将整个文件夹复制到你的 skills 目录：
   ```
   # Cursor
   ~/.cursor/skills/ai-interview-coach/
   
   # Claude Code
   ~/.claude/skills/ai-interview-coach/
   ```
3. 重启 AI 工具或刷新缓存

---

## 使用方法

像和面试官对话一样自然：

| 场景 | 你可以这样说 |
|------|-------------|
| **提供简历** | "你好考官，这是我的简历：path/to/resume.pdf" |
| **描述背景** | "你好考官，我是3年经验的前端工程师，帮我准备面试" |
| **指定职位** | "我想面试 AI 算法工程师，生成10道面试题" |
| **直接提问** | "准备一下 Java 后端面试题" |

---

## 面试题设计

每次生成 **10道题**，涵盖以下维度：

| 维度 | 题数 | 说明 |
|------|------|------|
| **技术知识** | 2-3题 | 考察核心技术栈深度 |
| **项目经验** | 2-3题 | 基于简历项目或职位要求 |
| **问题解决** | 2题 | 场景分析和方案设计 |
| **行为面试** | 2-3题 | 团队合作、沟通能力等 |

### 输出格式

```markdown
# 面试练习题 - Java后端工程师

> Generated on: 2026-04-14
> Source: resume.pdf

---

## 答题说明

1. 请在每道题下方的空白处写下你的答案
2. 完成后对照文档末尾的参考答案进行自我评估
3. 建议限时完成，模拟真实面试场景

---

## 面试题目

### 第1题
请解释 Spring Boot 的自动配置原理，以及它是如何简化 Spring 应用开发的？

---

（请在此作答）



---

### 第2题
...

## 参考答案

### 第1题答案

**考察点**: Spring 框架理解、自动配置机制

**参考答案**:
...

**答题建议**:
- 从 @SpringBootApplication 注解说起
- 解释 @EnableAutoConfiguration 的作用
- 说明条件化配置的原理
```

---

## 功能特性

- 📄 **简历分析** - 自动读取 PDF、Word、Markdown 格式的简历文件
- 🎯 **职位定制** - 根据指定职位生成针对性面试题
- 📝 **智能出题** - 基于简历内容或职位要求生成 **10道** 高质量面试题
- ✅ **参考答案** - 每道题附带详细参考答案和答题建议
- ✍️ **练习友好** - 每道题后预留 3 行空白供你手写答案

---

## 支持的简历格式

| 格式 | 扩展名 | 支持状态 |
|------|--------|----------|
| PDF | .pdf | ✅ 支持 |
| Word | .docx | ✅ 支持 |
| Markdown | .md, .markdown | ✅ 支持 |
| 纯文本 | .txt | ✅ 支持 |

---

## 适用场景

- 💻 准备技术岗位面试（前端、后端、算法等）
- 📊 准备产品/运营/管理类面试
- 🔍 自我能力评估和查漏补缺
- 🎭 模拟面试练习

---

## 项目结构

```
ai-interview-coach/
├── SKILL.md          # 核心技能定义
├── examples.md       # 使用示例
├── README.md         # 项目说明
└── LICENSE           # MIT License
```

---

## 贡献

欢迎提交 Issue 和 PR！

- 发现了问题？提交 [Issue](https://github.com/HogoZhang/ai-interview-coach/issues)
- 想改进功能？提交 [Pull Request](https://github.com/HogoZhang/ai-interview-coach/pulls)

---

## 许可证

MIT Copyright (c) 2026 HogoZhang — 随便用，随便改。

<div align="center">

**祝你面试顺利！** 🎉

</div>
