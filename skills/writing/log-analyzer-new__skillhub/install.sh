#!/bin/bash
# 日志分析器 Skill 安装脚本
# Log Analyzer

set -e

SKILL_NAME="log-analyzer"
SKILL_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  日志分析器 Skill"
echo "  Log Analyzer"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  智能日志分析工具"
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
name: log-analyzer
display_name: 日志分析器
description: 智能日志分析工具。支持 nginx、Apache、应用日志等多种格式，自动提取错误模式、性能指标、访问趋势。
version: 1.0.0
author: 叶建国
homepage: https://github.com/openclaw/log-analyzer
tags:
  - 日志分析
  - 运维工具
  - nginx
  - 性能监控
license: MIT
compatibility:
  - openclaw
  - skillhub
---

# 日志分析器

> 📊 智能分析 | 多格式支持 | 错误定位 | 性能优化

## 简介

智能日志分析工具，支持 nginx、Apache、应用日志等多种格式。

## 支持格式

- Nginx 访问日志/错误日志
- Apache 访问日志/错误日志
- 应用日志（JSON/Plain Text）
- 系统日志（Syslog）

## 核心功能

- 错误分析：错误类型统计、趋势、堆栈提取
- 性能分析：响应时间、慢请求、吞吐量
- 访问分析：PV/UV、热门URL、状态码分布
- 安全分析：异常请求、攻击检测

## 使用方式

```bash
# 分析 nginx 日志
log-analyzer analyze --file /var/log/nginx/access.log --type nginx

# 查找特定错误
log-analyzer search --file error.log --pattern "timeout"
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
echo "    - 分析日志"
echo "    - 查看错误日志"
echo "    - nginx日志分析"
echo "    - 性能瓶颈"
echo "    - 排查问题"
echo "    - 日志监控"
echo ""
echo "📖 完整文档请阅读："
echo "    $SKILL_DIR/SKILL.md"
echo ""
echo "═══════════════════════════════════════════════════"