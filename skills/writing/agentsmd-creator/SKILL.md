---
name: agentsmd-creator
description: 分析项目代码库，提取技术栈、编码规范、架构约定等要素，生成结构化的 AGENTS.md 项目约定文档。当用户要求生成 AGENTS.md、创建项目约定文档、更新 AGENTS.md、或初始化 AI Agent 项目指引时触发。
title: AGENTS.MD生成器
category: 开发
install_source: official
install_method: download
skill_id: b9415a2e-b2fc-4d6a-b531-8a00412fbcf9
enabled_at: 1787232676463
version: 1.0.0
name_zh: AGENTS.MD生成器
---

# AGENTS.MD生成器

分析项目代码库的技术栈、编码规范、架构约定、构建流程等要素，自动生成或增量更新结构化的 AGENTS.md 项目约定文档。

## 核心原则

1. **只记录 Agent 容易出错的场景**——通用编程知识无需记录（基模能力会提升）
2. **只记录工程定制规则**——项目特有的约定、工具、流程
3. **经验沉淀为精炼规则**——一行一条祈使句，可直接遵守
4. **保持可执行性**——每条规则具体到类名、方法名、命令

## 工作流

### 步骤 1：读取已有文档（如有）

若项目根目录已存在 `AGENTS.md`，**必须先读取全文**，提取其中的自定义规则（用户手动添加的、不在模板中的内容），后续生成时保留这些内容。

### 步骤 2：项目扫描

**并行读取**以下文件（不存在则跳过）：

**基础配置文件**：
- `pom.xml` / `build.gradle` / `package.json` / `go.mod` / `Cargo.toml` — 技术栈与版本
- `.gitignore` — 项目类型线索
- `docker-compose.yml` / `Dockerfile` — 基础设施与中间件
- `start.sh` / `Makefile` / `build.sh` — 构建启动命令
- `.env*` / `application*.yml` / `application*.properties` — 环境配置
- `.gitlab-ci.yml` / `.github/workflows/` — CI/CD 流程
- `README.md` — 项目简介

**深度代码扫描**（使用 Grep/SearchCodebase 搜索以下模式）：

| 搜索目标 | 搜索方法 | 提取内容 |
|----------|----------|----------|
| Controller 返回类型 | `Grep: "public R<"` 或 `Grep: "ResponseEntity"` | API 统一响应格式 |
| 基类实体 | `Glob: "**/BaseEntity.java"` → Read | tenant_id、deleted、审计字段约定 |
| 数据转换 | `Grep: "BeanUtils.copyProperties"` 或 `Grep: "MapStruct"` | Entity→DTO 转换方式 |
| 领域事件 | `Grep: "DomainEvent"` 或 `Grep: "@EventListener"` | 模块解耦机制 |
| 多租户 | `Grep: "TenantContext"` 或 `Grep: "tenant_id"` | 租户隔离策略 |
| 全局异常 | `Grep: "@ControllerAdvice"` 或 `Grep: "GlobalExceptionHandler"` | 异常处理规范 |
| 配置类 | `Glob: "**/*Config.java"` → 抽样 Read | Jackson/Redis/Security 等配置 |
| 初始化器 | `Glob: "**/*Initializer.java"` → Read | 平台级数据种子约定 |
| ID 类型 | `Grep: "@TableId"` → 抽样查看 | ID 字段类型约定(String/Long) |
| 跨模块引用 | `Grep: "import.*\\.api\\."` | 模块间通信方式（编码 vs FK） |

### 步骤 3：要素提取与组装

从扫描结果中提取要素，按模板 [assets/agentsmd-template.md](assets/agentsmd-template.md) 组装。详细提取规则见 [references/agentsmd-structure-guide.md](references/agentsmd-structure-guide.md)。

**三大章节**：

1. **编写规则** — 固定文案，说明文档定位
2. **技术栈** — 按「后端 / 前端 / 测试」分类，精确版本号，`|` 分隔
3. **最佳实践** — 核心章节，每条一行祈使句

**最佳实践条目按优先级排列**：

1. 沟通与语言（影响所有输出）
2. 工具使用限制（防止误操作）
3. 数据库操作（查询/迁移命令）
4. 数据库设计规范（表字段约定）
5. API 规范（响应格式、转换方式）
6. 编码约定（类型、日期、命名）
7. 上下文与安全（租户、权限）
8. 架构约束（事件、模块通信）
9. 前端规范（组件复用、状态管理）
10. 构建与部署（启动命令、环境管理）
11. 运维与调试（日志查看、错误排查）
12. 禁止事项（明确红线）

**条目句式模板**：

| 类型 | 句式 | 示例 |
|------|------|------|
| 操作指令 | 动词开头 | `使用中文交流和编写注释` |
| 禁止规则 | `禁止` / `若非...禁止` | `禁止使用SpringCloud相关依赖` |
| 条件规则 | 条件 + 须/必须 + 操作 | `修改完Java代码后须执行 sh start.sh` |
| 引用规则 | 使用 + 工具/类名 | `使用 dba 技能查询 dev 数据库` |
| 约定规则 | 主语 + 约定 | `Controller 返回 R<T> 格式` |
| 路径规则 | 命令/路径 + 说明 | `查看后端日志：tail -100f logs/xxx.log` |

**质量自检**（生成前逐条检查）：

- [ ] 每条规则是否只占一行？
- [ ] 是否有类名/方法名/命令等具体信息？（非"建议""尽量"等模糊词）
- [ ] 是否只包含项目特有约定？（非通用编程知识）
- [ ] 版本号是否从依赖文件提取的精确值？（非范围版本）
- [ ] 是否不含敏感信息？（密码、密钥、内部 IP）
- [ ] 最佳实践总条目是否 ≤ 100 条？（超出时按重要性裁剪）

### 步骤 4：文件生成

将内容写入项目根目录 `AGENTS.md`。

- **新建**：直接写入
- **更新**（已有 AGENTS.md）：合并已有文档中的自定义规则 + 新扫描结果，覆盖写入
- **用户明确要求保留某内容**：确保该内容不被覆盖

## 参数

| 参数 | 说明 |
|------|------|
| 无参数 | 扫描当前项目并生成/覆盖 AGENTS.md |
| `/path/to/project` | 为指定目录生成 |
| `--update` | 增量更新：保留已有自定义规则，补充新发现的规则 |
| `根据 AGENTS.md 优化` | 读取现有文档，基于实际代码验证并补充缺失规则 |

## 错误处理

| 场景 | 处理 |
|------|------|
| 项目根目录无法识别 | 提示用户指定项目路径 |
| 依赖文件不存在 | 告知未识别到技术栈，请手动补充 |
| 多语言项目 | 按模块分别提取技术栈，统一输出 |

## 禁止事项

- ❌ 不生成空泛通用规范（如"代码要有注释"）
- ❌ 不在最佳实践中重复技术栈章节的版本信息
- ❌ 不捏造项目中不存在的规范或工具
- ❌ 不包含敏感信息（密码、密钥、内部 IP）
- ❌ 不使用"建议""尽量""考虑"等模糊词

## 参考资料

- 提取规则详解 → [references/agentsmd-structure-guide.md](references/agentsmd-structure-guide.md)
- 输出模板 → [assets/agentsmd-template.md](assets/agentsmd-template.md)
