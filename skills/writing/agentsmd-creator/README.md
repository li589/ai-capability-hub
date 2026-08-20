# AGENTS.MD 生成器

一句话为你的项目生成 `AGENTS.md`——AI Agent 的项目约定文档。

## 使用

```bash
# 为当前项目生成（已有则覆盖）
/agentsmd-creator

# 增量更新（保留自定义规则 + 补充新发现）
/agentsmd-creator --update

# 为指定目录生成
/agentsmd-creator /path/to/project

# 基于现有文档优化
/agentsmd-creator 根据 AGENTS.md 优化
```

## 工作原理

1. **读取** — 如已有 AGENTS.md，先提取自定义规则
2. **扫描** — 读取 pom.xml / package.json / start.sh 等 + 深度搜索代码模式
3. **提取** — 识别技术栈版本、编码规范、架构约定、构建命令
4. **组装** — 按模板结构化输出，质量自检
5. **写入** — 生成 AGENTS.md 到项目根目录

## 输出结构

```
## 编写规则          ← 文档定位（固定文案）
## 技术栈            ← 精确版本号（后端/前端/测试）
## 最佳实践          ← 一行一条可执行规则（≤100条）
```

## 支持的技术栈

Java (Spring Boot/Gradle) · Node.js/前端 (React/Vue/Next.js) · Python · Go · Rust 及多语言混合项目。
# AGENTS.MD 生成器

一句话为你的项目生成 `AGENTS.md`——AI Agent 的项目约定文档。

## 它是什么

AGENTS.md 是给 AI Agent 阅读的项目规则手册，记录技术栈（精确版本）和最佳实践（一行一条可直接遵守的编码规范、架构约定、构建流程），让 AI Agent 立刻理解你的项目并遵循团队规范。

## 快速使用

```bash
# 为当前项目生成
/agentsmd-creator

# 为指定目录生成
/agentsmd-creator /path/to/project
```

生成后文件写入项目根目录的 `AGENTS.md`（已存在则覆盖）。

## 输出示例

```markdown
## 技术栈
**后端**: Java 21 | Spring Boot 3.5.11 | MyBatis-Plus 3.5.15 | MySQL 8.0.33
**前端**: React 18.3.1 | TypeScript 5.3.3 | Ant Design 5.13.0 | Vite 6.4.1

## 最佳实践
- 使用中文交流和编写注释
- Controller 返回 R<T> 格式
- 所有 ID 字段统一使用 String 类型
- 修改完 Java 代码后须执行 sh start.sh 重启服务
- 禁止使用 SpringCloud 相关依赖
```

## 工作原理

1. **扫描** — 读取 `pom.xml`、`package.json`、`docker-compose.yml` 等配置
2. **提取** — 识别技术栈版本、编码规范、架构模式、构建命令
3. **组装** — 按标准模板结构化输出
4. **写入** — 生成 `AGENTS.md` 到项目根目录

## 支持的技术栈

Java (Spring Boot/Gradle) · Node.js/前端 (React/Vue/Next.js) · Python · Go · Rust 及多语言混合项目。

## FAQ

- **已有 AGENTS.md？** 直接覆盖，建议先备份。
- **内容不满意？** 手动编辑 `AGENTS.md` 即可，它只是普通 Markdown。
