# AGENTS.md 提取规则详解

本文档定义每类要素的**提取方法**和**输出示例**，供 Agent 扫描时参照。

## 1. 技术栈提取

### 来源文件 → 提取规则

| 文件 | 提取方式 |
|------|----------|
| `pom.xml` → `<java.version>` | Java 版本 |
| `pom.xml` → `<spring-boot.version>` | Spring Boot 版本 |
| `pom.xml` → 核心 `<dependency>` | 框架/ORM/缓存版本 |
| `package.json` → `dependencies` | 前端框架/UI库/状态管理 |
| `package.json` → `devDependencies` | 构建工具/测试框架 |
| `docker-compose.yml` → `image:` | MySQL/Redis/MQ 版本 |

### 输出格式

```
**后端**: Java 21 | Spring Boot 3.5.11 | MyBatis-Plus 3.5.15 | MySQL 8.0.33 | Redis (Redisson 3.52.0)
**前端**: React 18.3.1 | TypeScript 5.3.3 | Ant Design 5.13.0 | Vite 6.4.1 | Zustand 5.0.0
**测试**: JUnit 5 5.11.4 + Mockito 5.14.2 | Vitest 1.1.0 + Playwright 1.58.2
```

**规则**：版本号必须从依赖文件提取精确值，禁止猜测或使用范围版本。

## 2. 编码规范提取

### 搜索策略

| 规范类型 | 搜索方法 | 提取内容 |
|----------|----------|----------|
| API 响应格式 | `Grep: "public R<"` | 统一返回包装类（如 `R<T>`） |
| 数据转换 | `Grep: "BeanUtils.copyProperties"` | Entity→DTO 转换约定 |
| ID 类型 | `Grep: "@TableId"` 抽样 | ID 字段统一类型（String/Long） |
| 日期处理 | `Grep: "LocalDateTime"` + `Grep: "JacksonConfig"` | 是否禁止手动 `.toString()` |
| 命名语言 | 抽样 3 个 Service/Controller | 注释语言（中文/英文） |

### 输出示例

```
- Controller 返回 R<T> 格式
- Entity转DTO必须用 BeanUtils.copyProperties，禁止手动setter
- 前后端所有ID字段统一使用String类型，避免前端Long转Number丢失精度
- VO直接返回 LocalDateTime/LocalDate，禁止手动 .toString()
```

## 3. 架构约定提取

### 搜索策略

| 约定类型 | 搜索方法 | 提取内容 |
|----------|----------|----------|
| 多租户 | `Grep: "TenantContext"` | 租户隔离策略、清理时机 |
| 领域事件 | `Grep: "DomainEvent"` / `Grep: "@EventListener"` | 模块解耦机制 |
| 软删除 | `Grep: "@TableLogic"` / `Grep: "deleted"` | 重要表删除策略 |
| 初始化器 | `Glob: "**/*Initializer.java"` | 平台级数据种子 |
| 跨模块引用 | `Grep: "import.*\\.api\\."` | 使用业务编码 vs FK ID |
| 框架限制 | `Grep: "spring-cloud"` (应为空) | 禁用的框架 |

### 输出示例

```
- 在 common.event 包下定义DomainEvent领域事件，通过 new XxxEvent().publish() 发布
- 业务表要有 tenant_id 字段，重要表加 deleted 字段，优先继承 BaseEntity
- 跨模块关联优先使用业务编码（如 logisticsNo），避免存储外键ID
- 新增菜单/权限时，必须同步更新 DataInitializer.java
- 禁止使用SpringCloud相关依赖，须使用SpringBoot代替
```

## 4. 构建与运维提取

### 搜索策略

| 类型 | 搜索方法 | 提取内容 |
|------|----------|----------|
| 本地启动 | Read `start.sh` / `Makefile` | 启动命令、端口、依赖服务 |
| 数据库迁移 | Read `migrate.sh` / `dbmate` 目录 | DDL 变更流程 |
| 模块构建 | Read `pom.xml` 的 `<modules>` | API 模块需单独 install |
| 日志路径 | Read `logback*.xml` 或脚本中的日志路径 | 后端/前端日志查看命令 |
| 环境管理 | Read `.env*` 文件 | dev/test/prod 环境区分 |
| CI/CD | Read `.gitlab-ci.yml` / `.github/workflows/` | 部署分支、流程 |
| 移动端 | Read `install_*.sh` | PDA/TMS 安装命令 |

### 输出示例

```
- 修改完Java代码后须执行根目录 sh start.sh 重启本地服务（已包含mvn编译）
- DDL变更须生成dbmate迁移脚本到 sql/dbmate_scm/，格式：-- migrate:up + -- migrate:down
- 改动 fengqun-scm-api 后须执行 mvn install -pl fengqun-scm-api -DskipTests
- 查看后端日志：tail -100f logs/fengqun-scm-service.log
- 查看测试环境错误日志：dba 技能查 test 环境 sys_error_log 表
```

## 5. 禁止事项提取

从以下来源提取明确的禁止规则：

- **代码注释**中的 `// 禁止` `// 不要` `// 禁用`
- **lint 配置**中被禁用的规则
- **CI/CD** 中被排除的标签或依赖
- **已有 AGENTS.md** 中明确标记的 `禁止` 条目

### 输出示例

```
- 禁止使用SpringCloud相关依赖
- 禁止手动setter转换Entity到DTO
- 若非用户明确要求，禁止擅自使用 agent-browser 技能
- 禁用 DROP COLUMN IF EXISTS（MySQL不支持）
```

## 6. 增量更新策略

当已有 AGENTS.md 时，执行以下合并逻辑：

1. **保留**：用户手动添加的自定义规则（不在标准模板中的条目）
2. **更新**：版本号若与依赖文件不一致，以依赖文件为准
3. **补充**：新发现的代码模式/约定，追加到对应分类
4. **删除**：仅在代码中已不存在对应实现时，才删除某条规则
5. **不删**：用户明确标注保留的内容
# AGENTS.md 结构详解与编写指南

本文档深入解析 AGENTS.md 的每个章节，提供提取规则和编写建议。

## 文档定位

AGENTS.md 是给 AI Agent 阅读的**项目约定文档**，核心原则：

1. **只记录 Agent 容易出错的场景**——通用编程知识（如"变量要有意义的命名"）无需记录
2. **只记录工程定制规则**——项目特有的约定、工具、流程
3. **经验沉淀为精炼规则**——一行一条，避免长篇大论
4. **保持可执行性**——每条规则都应具体到可以直接遵守

## 三大章节详解

### 章节 1：编写规则

**作用**：告诉 Agent 这份文档的编写原则，避免 Agent 在修改文档时添加无用内容。

**核心要点**：
- 说明文档只记录 Agent 容易出错的场景和工程定制规则
- 强调经验需抽象精炼沉淀到最佳实践章节
- 明确通用知识无需记录

**示例**：
```markdown
## 编写规则

本说明文档仅记录AGENT容易出错的场景或当前工程定制规则，经验需抽象精炼沉淀到「最佳实践」章节（一行一条），通用知识无需沉淀（基模能力会提升）
```

### 章节 2：技术栈

**作用**：让 Agent 了解项目使用的技术和精确版本号，避免生成不兼容的代码。

**提取规则**：

| 信息来源 | 提取内容 |
|----------|----------|
| `pom.xml` → `<java.version>` / `<maven.compiler.source>` | Java 版本 |
| `pom.xml` → `<parent>` / `<dependency>` | Spring Boot、框架版本 |
| `package.json` → `dependencies` / `devDependencies` | 前端框架、工具版本 |
| `docker-compose.yml` → `image:` | MySQL、Redis、MQ 等中间件版本 |
| 测试框架依赖 | JUnit、Mockito、Vitest、Playwright 版本 |

**格式要求**：
- 按「后端 / 前端 / 测试 / 基础设施」分行
- 每项格式：`名称 版本号`
- 同类项用 `|` 分隔

**示例**：
```markdown
## 技术栈

**后端**: Java 21 | Spring Boot 3.5.11 | MyBatis-Plus 3.5.15 | MySQL 8.0.33 | Redis (Redisson 3.52.0)
**前端**: React 18.3.1 | TypeScript 5.3.3 | Ant Design 5.13.0 | Vite 6.4.1 | Zustand 5.0.0
**测试**: JUnit 5 5.11.4 + Mockito 5.14.2 | Vitest 1.1.0 + Playwright 1.58.2
```

**注意**：版本号必须从依赖文件中提取精确值，禁止猜测或使用范围版本。

### 章节 3：最佳实践

**作用**：这是 AGENTS.md 的核心章节，以一行一条的形式记录所有项目约定。

**内容分类与提取方法**：

#### 分类 A：沟通与语言

扫描点：项目代码注释语言、README 语言、commit message 语言。

典型规则：
- `使用中文交流和编写注释`

#### 分类 B：工具使用限制

扫描点：项目脚本（`*.sh`）、自定义工具引用、CI/CD 配置中的工具。

典型规则：
- `若非用户明确要求，禁止擅自使用 dbmate、agent-browser 技能`
- `使用 dba 技能直接操作 dev 开发数据库`

#### 分类 C：测试规范

扫描点：测试目录结构、测试框架配置、测试基类。

典型规则：
- `复杂Service/核心算法/状态机先写测试（TDD）`

#### 分类 D：数据库规范

扫描点：`BaseEntity.java`、建表 SQL、ORM 配置。

提取方法：
1. 查看 `BaseEntity` 包含哪些字段（如 `tenant_id`、`created_at`、`updated_at`）
2. 查看是否有软删除注解（如 `@TableLogic`）
3. 查看字段命名约定

典型规则：
- `业务表要有 tenant_id 字段，重要表需要加 deleted 字段，BaseEntity如果适用则优先继承`
- `前后端所有ID字段统一使用String类型，避免前端Long转Number丢失精度`

#### 分类 E：API 规范

扫描点：Controller 层返回类型、统一响应类、异常处理类。

提取方法：
1. 搜索 Controller 方法的返回类型（如 `R<T>`、`ResponseEntity`、`Result`）
2. 查看全局异常处理器（如 `@ControllerAdvice`）
3. 查看序列化配置（如 `JacksonConfig`）

典型规则：
- `Controller 返回 R<T> 格式`
- `VO直接返回 LocalDateTime/LocalDate，禁止手动 .toString()`
- `Entity转DTO必须用 BeanUtils.copyProperties，禁止手动setter`

#### 分类 F：上下文与安全

扫描点：`TenantContext`、`SecurityContext`、拦截器、过滤器。

典型规则：
- `异常处理后恢复租户上下文（TenantContext.clear()）`
- `定时任务跨租户查询用 TenantContext.skip()，普通业务保持自动隔离`

#### 分类 G：构建与部署

扫描点：`start.sh`、`Makefile`、`package.json` scripts、CI/CD 配置。

典型规则：
- `修改完Java代码后须执行根目录 sh start.sh 重启本地服务`
- `若安装PDA端执行 sh install_pda.sh`

#### 分类 H：架构约束

扫描点：项目模块结构、事件机制、初始化类、跨模块引用方式。

典型规则：
- `在 common.event 包下定义DomainEvent领域事件，用于解耦不同模块间的调用`
- `跨模块关联优先使用业务编码，避免存储外键ID`
- `禁止使用SpringCloud相关依赖，须使用SpringBoot代替`

#### 分类 I：运维与调试

扫描点：日志配置、日志路径、错误日志表、调试脚本。

典型规则：
- `本地查看后端日志可访问 tail -100f logs/fengqun-scm-service.log`
- `查看测试环境log.error错误日志：dba 技能查test环境 sys_error_log 表`

## 最佳实践条目编写标准

### 句式模板

| 句式 | 适用场景 | 示例 |
|------|----------|------|
| `动词 + 对象` | 操作指令 | `使用中文交流和编写注释` |
| `禁止 + 行为` | 明确禁止 | `禁止使用SpringCloud相关依赖` |
| `若非...禁止...` | 条件禁止 | `若非用户明确要求，禁止擅自使用 dbmate` |
| `条件 + 须/必须 + 操作` | 条件触发 | `修改完Java代码后须执行 sh start.sh` |
| `主语 + 约定内容` | 静态约定 | `Controller 返回 R<T> 格式` |
| `使用 + 工具 + 做 + 事情` | 工具引用 | `使用 dba 技能直接操作 dev 数据库` |

### 质量标准

- ✅ 每条规则只占一行
- ✅ 具体到可以直接遵守（有类名、方法名、命令）
- ✅ 不含"建议""尽量""考虑"等模糊词
- ✅ 不含通用编程知识
- ❌ 不超过 100 条（超出时按重要性裁剪）

## 常见错误

| 错误 | 正确做法 |
|------|----------|
| 写入通用规范（如"代码要有注释"） | 只记录项目特有约定 |
| 版本号使用范围（如"Spring Boot 3.x"） | 从依赖文件提取精确版本 |
| 最佳实践写成段落 | 一行一条祈使句 |
| 包含密码、密钥等敏感信息 | 使用占位符或引用环境变量 |
| 最佳实践超过 100 条 | 按重要性裁剪，保留核心规则 |
| 捏造项目中不存在的工具或规范 | 只从实际代码中提取 |
