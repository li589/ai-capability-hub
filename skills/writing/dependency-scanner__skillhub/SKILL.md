---
name: dependency-scanner
display_name: 依赖安全扫描
description: 自动扫描项目依赖中的安全漏洞。支持 Node.js/npm、Python/pip、Java/Maven/Gradle、Go/modules 等多种语言，对接 CVE 数据库，检测已知漏洞并提供升级建议，生成安全评估报告。
version: 1.0.0
author: 叶建国
homepage: https://github.com/openclaw/dependency-scanner
tags:
  - 安全扫描
  - 依赖管理
  - CVE检测
  - 漏洞修复
  - DevSecOps
  - 代码安全
license: MIT
compatibility:
  - openclaw
  - skillhub
---

# 依赖安全扫描 (Dependency Scanner)

> 🔒 安全扫描 | 多语言支持 | CVE检测 | 自动修复建议

## 简介

依赖安全扫描是一个自动检测项目依赖安全漏洞的工具。支持 Node.js/npm、Python/pip、Java/Maven/Gradle、Go/modules 等多种语言生态，对接 CVE/NVD 数据库，识别已知漏洞并提供修复建议。

**适用场景**：当用户提到"扫描依赖漏洞"、"检查 package.json 安全"、"CVE 检测"、"依赖安全"、"漏洞修复"、"安全审计"时使用此 Skill。

---

## 支持的语言和包管理器

| 语言 | 包管理器 | 扫描文件 | 漏洞数据源 |
|------|----------|----------|------------|
| **Node.js** | npm/yarn/pnpm | package.json, package-lock.json, yarn.lock | NPM Audit, Snyk |
| **Python** | pip/poetry/pipenv | requirements.txt, Pipfile.lock, poetry.lock | SafetyDB, PyUp |
| **Java** | Maven/Gradle | pom.xml, build.gradle | OWASP Dependency-Check |
| **Go** | Go Modules | go.mod, go.sum | Go Vulnerability Database |
| **PHP** | Composer | composer.lock | FriendsOfPHP Security Advisories |
| **Ruby** | Bundler | Gemfile.lock | Ruby Advisory Database |
| **.NET** | NuGet | packages.config, *.csproj | GitHub Advisory Database |
| **Rust** | Cargo | Cargo.lock | RustSec Advisory Database |

---

## 核心功能

### 1. 漏洞检测

- 扫描依赖项中的已知 CVE 漏洞
- 按严重程度分类（Critical/High/Medium/Low）
- 提供漏洞详情和 CVSS 评分
- 关联漏洞修复版本

### 2. 许可证合规

- 检测依赖许可证类型
- 识别 GPL/AGPL 等传染性许可证
- 标记与项目不兼容的许可证

### 3. 过期依赖

- 检测过时依赖版本
- 提供最新版本信息
- 升级风险提醒（Breaking Changes）

### 4. 自动修复

- 生成安全升级建议
- 自动创建修复 PR（配合 CI/CD）
- 提供最小化升级方案

---

## 快速使用

### 扫描当前项目

```bash
# 自动检测项目类型并扫描
dependency-scanner scan

# 指定项目路径
dependency-scanner scan --path /path/to/project

# 指定语言
dependency-scanner scan --language nodejs

# 生成报告
dependency-scanner scan --output report.html
```

### 扫描特定文件

```bash
# Node.js
dependency-scanner scan --file package.json --lockfile package-lock.json

# Python
dependency-scanner scan --file requirements.txt

# Java Maven
dependency-scanner scan --file pom.xml

# Go
dependency-scanner scan --file go.mod
```

### CI/CD 集成

```bash
# 设置失败阈值，超过则退出非0
dependency-scanner scan --fail-on critical --fail-on high

# 输出 JSON 供后续处理
dependency-scanner scan --format json --output security-report.json

# 忽略特定 CVE
dependency-scanner scan --ignore CVE-2021-1234 --ignore CVE-2021-5678
```

---

## 扫描报告示例

### 安全评估报告

```
═══════════════════════════════════════════════════
          依赖安全扫描报告
═══════════════════════════════════════════════════

扫描时间：2026-04-05 11:30:00
项目路径：/home/user/myproject
项目类型：Node.js (npm)
扫描文件：package.json, package-lock.json

【安全评分】🔴 45/100 (需立即处理)

【漏洞概览】
┌──────────┬───────┬─────────────────────────────┐
│ 严重程度 │ 数量  │ 说明                        │
├──────────┼───────┼─────────────────────────────┤
│ 🔴 Critical│   2   │ 需立即修复，可远程执行代码  │
│ 🟠 High   │   5   │ 需尽快修复，存在严重风险    │
│ 🟡 Medium │  12   │ 建议修复，存在一定风险      │
│ 🟢 Low    │   8   │ 风险较低，可延后处理        │
└──────────┴───────┴─────────────────────────────┘
总计：27个漏洞 | 直接影响依赖：15个

【关键漏洞详情】

🔴 CRITICAL

1. CVE-2021-44228 (Log4Shell)
   组件：log4j-core@2.14.0
   CVSS评分：10.0
   描述：Apache Log4j2 远程代码执行漏洞
   影响：攻击者可通过 JNDI 注入执行任意代码
   修复方案：升级至 2.17.0 或更高版本
   命令：npm install log4j-core@2.17.0

2. CVE-2023-28432
   组件：express@4.17.1
   CVSS评分：9.8
   描述：Express.js 原型污染漏洞
   影响：可导致拒绝服务或远程代码执行
   修复方案：升级至 4.18.2 或更高版本
   命令：npm install express@4.18.2

🟠 HIGH

3. CVE-2022-23812
   组件：node-fetch@2.6.1
   CVSS评分：7.5
   描述：信息泄露漏洞
   修复方案：升级至 2.6.7 或更高版本
   命令：npm install node-fetch@2.6.7

... (共5个 High 级别漏洞)

【过期依赖】

⚠️ 发现 23 个过期依赖

┌─────────────────┬────────────┬────────────┬──────────┐
│ 依赖名称        │ 当前版本   │ 最新版本   │ 落后版本 │
├─────────────────┼────────────┼────────────┼──────────┤
│ lodash          │ 4.17.15    │ 4.17.21    │ 6 个     │
│ axios           │ 0.21.1     │ 1.6.2      │ 15 个    │
│ react           │ 17.0.1     │ 18.2.0     │ 17 个    │
└─────────────────┴────────────┴────────────┴──────────┘

【许可证合规】

✅ 合规：MIT (45个), Apache-2.0 (12个), BSD-3-Clause (8个)
⚠️  注意：GPL-3.0 (2个) - 需确认是否符合项目许可策略
   - package-a@1.0.0
   - package-b@2.1.0

【自动修复建议】

执行以下命令可修复所有 Critical 和 High 级别漏洞：

npm audit fix --force

或手动升级：
npm install log4j-core@2.17.0 express@4.18.2 node-fetch@2.6.7

【配置建议】

1. 启用自动安全更新
   npm config set audit-level moderate

2. 添加 pre-commit 钩子检查
   npx husky add .husky/pre-commit "npm audit"

3. CI/CD 集成示例
   - name: Security Audit
     run: dependency-scanner scan --fail-on critical

═══════════════════════════════════════════════════
```

---

## 漏洞严重程度说明

| 等级 | CVSS评分 | 风险说明 | 处理建议 |
|------|----------|----------|----------|
| 🔴 Critical | 9.0-10.0 | 可远程执行代码，系统完全失控 | 立即修复，停止生产部署 |
| 🟠 High | 7.0-8.9 | 严重安全风险，可导致数据泄露 | 24小时内修复 |
| 🟡 Medium | 4.0-6.9 | 一定安全风险，需要特定条件触发 | 一周内修复 |
| 🟢 Low | 0.1-3.9 | 轻微风险，难以被利用 | 计划内修复 |

---

## 各语言使用指南

### Node.js / npm

```bash
# 基础扫描
dependency-scanner scan

# 使用 npm audit
dependency-scanner scan --method npm-audit

# 仅检查生产依赖
dependency-scanner scan --production

# 忽略开发依赖的漏洞
dependency-scanner scan --skip-dev
```

**常见问题：**

Q: npm audit fix 和 dependency-scanner 的区别？
A: npm audit 仅检查 npm  registry 的已知漏洞，dependency-scanner 还会对接更多漏洞数据库。

### Python / pip

```bash
# 扫描 requirements.txt
dependency-scanner scan --file requirements.txt

# 扫描 Poetry 项目
dependency-scanner scan --file pyproject.toml --lockfile poetry.lock

# 扫描 Pipenv 项目
dependency-scanner scan --file Pipfile --lockfile Pipfile.lock
```

**安全修复：**

```bash
# 自动修复（使用 pip-review）
pip-review --auto

# 或手动升级
pip install --upgrade package-name
```

### Java / Maven

```bash
# 扫描 Maven 项目
dependency-scanner scan --file pom.xml

# 生成 OWASP 报告
dependency-scanner scan --file pom.xml --format xml --output dependency-check-report.xml
```

**pom.xml 配置：**

```xml
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>8.4.0</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>
    </configuration>
</plugin>
```

### Go

```bash
# 扫描 Go 模块
dependency-scanner scan --file go.mod

# 使用官方漏洞检查
go list -json -m all | nancy sleuth
```

### PHP / Composer

```bash
# 扫描 Composer 项目
dependency-scanner scan --file composer.lock

# 使用 local-php-security-checker
local-php-security-checker composer.lock
```

---

## CI/CD 集成

### GitHub Actions

```yaml
name: Security Audit
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Dependency Scanner
        run: dependency-scanner scan --fail-on critical --fail-on high
```

### GitLab CI

```yaml
security-scan:
  stage: test
  script:
    - dependency-scanner scan --format json --output gl-dependency-scanning-report.json
  artifacts:
    reports:
      dependency_scanning: gl-dependency-scanning-report.json
```

### Jenkins

```groovy
stage('Security Scan') {
    steps {
        sh 'dependency-scanner scan --fail-on critical'
    }
}
```

---

## 漏洞数据库来源

| 数据源 | 覆盖范围 | 更新频率 |
|--------|----------|----------|
| **CVE/NVD** | 通用漏洞数据库 | 每日 |
| **GitHub Advisory Database** | GitHub 生态 | 实时 |
| **Snyk Vulnerability DB** | 多语言覆盖 | 实时 |
| **OSV (Open Source Vulnerabilities)** | Google 维护 | 实时 |
| **National Vulnerability Database** | 美国国家标准 | 每日 |
| **语言专属数据库** | npm/rubysec/rustsec 等 | 实时 |

---

## 配置文件

```yaml
# dependency-scanner.yml
scan:
  # 扫描范围
  include-dev: true
  include-transitive: true
  
  # 失败阈值
  fail-on:
    - critical
    - high
  
  # 忽略的 CVE（需谨慎使用）
  ignore:
    - CVE-2021-1234  # 已知误报，不影响当前使用场景
    - CVE-2022-5678  # 已评估，风险可接受
  
  # 忽略路径
  ignore-paths:
    - "**/test/**"
    - "**/docs/**"

# 报告配置
report:
  format: html  # text/json/html/sarif
  output: security-report.html
  
# 通知配置
notifications:
  slack:
    webhook: https://hooks.slack.com/services/xxx
    channel: #security-alerts
  email:
    to: security@company.com
    on: critical  # 仅关键漏洞发送邮件
```

---

## 使用场景

### 场景一：日常安全审计

```
用户：帮我检查一下项目依赖的安全状况

执行步骤：
1. 自动检测项目类型和依赖文件
2. 扫描所有依赖的已知漏洞
3. 生成安全评分和详细报告
4. 提供修复建议和命令
```

### 场景二：发布前检查

```
用户：发布前帮我确保没有安全漏洞

执行步骤：
1. 扫描生产依赖（跳过 devDependencies）
2. 检查 Critical 和 High 级别漏洞
3. 如有漏洞则阻断发布流程
4. 生成发布安全报告
```

### 场景三：响应安全事件

```
用户：听说 log4j 有漏洞，快帮我检查一下

执行步骤：
1. 快速扫描特定 CVE（如 CVE-2021-44228）
2. 检查项目中是否存在受影响的依赖
3. 确认当前版本是否在受影响范围内
4. 提供紧急修复方案
```

---

## 命令参考

### 扫描命令

| 命令 | 说明 |
|------|------|
| `scan` | 扫描项目依赖 |
| `check` | 快速检查特定 CVE |
| `fix` | 自动修复可升级的漏洞 |
| `update-db` | 更新漏洞数据库 |

### 常用参数

| 参数 | 说明 |
|------|------|
| `--path` | 项目路径 |
| `--file` | 依赖文件路径 |
| `--lockfile` | 锁定文件路径 |
| `--language` | 指定语言 |
| `--fail-on` | 设置失败阈值 |
| `--ignore` | 忽略特定 CVE |
| `--format` | 输出格式 |
| `--output` | 输出文件 |
| `--production` | 仅扫描生产依赖 |

---

## 最佳实践

### 1. 定期扫描

- 每周运行一次完整扫描
- 每次依赖更新后自动扫描
- 发布前强制安全检查

### 2. 及时修复

- Critical 漏洞立即修复
- High 漏洞 24 小时内修复
- 设置自动 PR 修复低风险漏洞

### 3. 持续监控

- 订阅安全公告（GitHub Dependabot）
- 集成 Snyk 等商业服务（可选）
- 建立安全响应流程

---

## 注意事项

- ⚠️ 扫描结果仅供参考，需人工评估业务影响
- ⚠️ 升级依赖前请在测试环境验证
- ⚠️ 注意 Breaking Changes，避免升级导致功能异常
- ⚠️ 忽略 CVE 需有明确理由并记录

---

## 更新日志

### v1.0.0 (2026-04-05)
- 初始版本发布
- 支持 8 种语言和包管理器
- CVE/NVD 漏洞检测
- 许可证合规检查
- CI/CD 集成支持
- 自动生成修复建议
