# generate-tech-proposal

生成标准化的技术设计方案文档的 Claude Code Skill，包含数据库设计、架构设计、接口设计、业务流程等完整章节规范。

## 功能特性

- ✅ **数据库设计规范** - 表清单、ER 图（简化/详细两种格式）、建表 SQL、表关系说明
- ✅ **接口设计规范** - Controller/Service/Mapper 三层架构设计
- ✅ **业务流程设计** - 后端使用时序图（sequenceDiagram），前端使用 flowchart，流程说明、异常处理
- ✅ **文档结构模板** - 统一的章节结构和格式规范
- ✅ **完整示例** - 基于真实项目的设计示例
- ✅ **详细 ER 图** - 包含完整表结构、字段类型、约束和注释的 ER 图

## 安装

### 方式 1: 通过 npx skills 安装（推荐）

```bash
# 全局安装（所有 AI 编程工具可用）
npx skills add https://github.com/kevinqpeng/generate-tech-proposal --skill generate-tech-proposal --global --yes

# 项目级安装（仅当前项目可用）
npx skills add https://github.com/kevinqpeng/generate-tech-proposal --skill generate-tech-proposal --yes
```

### 方式 2: 手动安装

```bash
# 克隆仓库
git clone https://github.com/kevinqpeng/generate-tech-proposal.git

# 复制到 Claude Code skills 目录
cp -r generate-tech-proposal ~/.claude/skills/

# 或复制到全局 agents skills 目录
cp -r generate-tech-proposal ~/.agents/skills/
```

## 使用方法

安装后，在 Claude Code 中使用以下触发词即可激活此 skill：

- "生成技术方案"
- "创建技术设计文档"
- "数据库设计"
- "接口设计"
- "技术设计"

### 示例

```
用户: 帮我生成一个用户管理模块的技术方案

Claude: [自动加载 generate-tech-proposal skill]
我将为您生成用户管理模块的技术设计方案，包含以下章节：
1. 数据库设计
2. 架构设计
3. 数据模型
4. 组件接口设计
5. 核心业务流程
6. 功能权限配置
...
```

## 文档结构

```
generate-tech-proposal/
├── SKILL.md                    # 主要使用指南
└── references/
    ├── template-overview.md    # 文档结构模板
    ├── database-design.md      # 数据库设计规范
    ├── api-design.md           # 接口设计规范
    ├── business-flow.md        # 业务流程设计规范
    └── er-diagram-examples.md  # ER 图示例集（简化/详细格式）
```

## 生成的技术方案包含

### 1. 数据库设计
- 表清单（序号、表名、说明）
- ER 图（Mermaid erDiagram）
  - 简化格式：快速展示表关系
  - 详细格式：包含完整字段结构、类型、约束
- 表关系说明（1:1, 1:N, N:M）
- 建表 SQL（完整可执行）

### 2. 架构设计
- 系统架构图
- 技术栈说明
- 模块划分

### 3. 数据模型
- 表关系图
- 数据权限规则
- 多租户隔离
- 软删除机制

### 4. 组件接口设计
- Controller 接口（HTTP 层）
- Service 接口（业务逻辑层）
- Mapper 接口（数据访问层）

### 5. 核心业务流程
- 后端流程图（Mermaid 时序图 sequenceDiagram）
- 前端流程图（Mermaid flowchart）
- 流程说明
- 异常处理

### 6. 功能权限配置
- 数据权限规则
- 操作权限

## 技术栈

- **图表工具**: Mermaid（ER 图、后端时序图 sequenceDiagram、前端 flowchart）
- **文档格式**: Markdown
- **代码示例**: Java/Spring Boot

## 适用场景

- ✅ 创建新功能的技术方案
- ✅ 规范化现有技术文档
- ✅ 生成符合团队标准的设计文档
- ✅ 技术评审前的文档准备
- ✅ 新人培训的文档模板

## 示例输出

查看 [references/](references/) 目录中的完整示例，包含：
- 线索管理系统的数据库设计
- 完整的接口设计示例
- 多个业务流程示例
- ER 图示例集（简化/详细格式对比）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT

## 作者

[@kevinqpeng](https://github.com/kevinqpeng)

---

**注意**: 此 skill 生成的技术方案遵循特定团队的开发规范，使用前请根据您的团队标准进行调整。
