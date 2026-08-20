#!/bin/bash
# 依赖安全扫描 Skill 安装脚本
# Dependency Scanner

set -e

SKILL_NAME="dependency-scanner"
SKILL_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  依赖安全扫描 Skill"
echo "  Dependency Scanner"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  自动检测项目依赖安全漏洞"
echo ""
echo "═══════════════════════════════════════════════════"
echo ""

# 检查目录是否存在
if [ -d "$SKILL_DIR" ]; then
  echo "📁 Skill 目录已存在，正在更新..."
else
  echo "📁 创建 Skill 目录..."
  mkdir -p "$SKILL_DIR"
fi

# 复制文件
echo "📄 安装 SKILL.md..."
cat > "$SKILL_DIR/SKILL.md" << 'SKILL_EOF'
---
name: dependency-scanner
display_name: 依赖安全扫描
description: 自动扫描项目依赖中的安全漏洞。支持 Node.js、Python、Java、Go 等多语言，对接 CVE 数据库，检测已知漏洞并提供升级建议。
version: 1.0.0
author: 叶建国
homepage: https://github.com/openclaw/dependency-scanner
tags:
  - 安全扫描
  - 依赖管理
  - CVE检测
  - DevSecOps
license: MIT
compatibility:
  - openclaw
  - skillhub
---

# 依赖安全扫描

> 🔒 安全扫描 | 多语言支持 | CVE检测 | 自动修复建议

## 简介

自动检测项目依赖安全漏洞。

## 支持语言

- Node.js (npm/yarn/pnpm)
- Python (pip/poetry/pipenv)
- Java (Maven/Gradle)
- Go (Modules)
- PHP (Composer)
- Ruby (Bundler)
- .NET (NuGet)
- Rust (Cargo)

## 核心功能

- 漏洞检测：CVE 识别、CVSS 评分
- 许可证合规：检测传染性许可证
- 过期依赖：版本检查
- 自动修复：生成升级建议

## 使用方式

```bash
# 扫描当前项目
dependency-scanner scan

# 指定路径
dependency-scanner scan --path /path/to/project

# 生成报告
dependency-scanner scan --output report.html
```

SKILL_EOF

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ 安装完成！"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📚 使用说明："
echo ""
echo "  当用户提到以下关键词时自动触发："
echo "    - 扫描依赖漏洞"
echo "    - 检查 package.json 安全"
echo "    - CVE 检测"
echo "    - 依赖安全"
echo "    - 漏洞修复"
echo "    - 安全审计"
echo ""
echo "📖 完整文档请阅读："
echo "    $SKILL_DIR/SKILL.md"
echo ""
echo "═══════════════════════════════════════════════════"