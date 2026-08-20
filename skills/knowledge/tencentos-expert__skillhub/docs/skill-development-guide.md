# Skill 开发指南

本文档详细介绍如何开发 TencentOS Expert Skill。

## 快速开始

### 1. 创建新 Skill

```bash
# 在 references/ 下创建新模块文档
touch references/my-new-skill.md

# 在 scripts/ 下创建辅助脚本（如需要）
touch scripts/my-new-skill-collect.sh
```

### 2. 目录结构

```
skills/<skill-name>/
├── skill.yaml      # Skill 元信息
├── SKILL.md        # 核心 Prompt
├── scripts/        # 辅助脚本
├── docs/           # 文档
├── tests/          # 测试
└── OWNERS          # 负责人
```

## skill.yaml 详解

### 必填字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| name | string | 唯一标识，小写字母和连字符 |
| display_name | string | 显示名称 |
| version | string | 语义化版本 (x.y.z) |
| category | string | 分类标签（如 security, basic-ops, performance） |
| description | string | 详细描述 |
| owners | list | 负责人邮箱列表 |

### 可选字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| dependencies.required | list | 必需的系统工具 |
| dependencies.optional | list | 可选的系统工具 |
| supported_os | list | 支持的操作系统版本 |
| triggers | list | 触发关键词 |
| tags | list | 标签 |

## SKILL.md 编写指南

### 结构模板

```markdown
# 技能名称

## 概述
说明技能的用途和适用场景。

## 前置条件
- 需要的工具
- 需要的权限

## 使用步骤

### 步骤 1：信息收集
收集必要的系统信息。

### 步骤 2：诊断分析
执行诊断命令并分析结果。

### 步骤 3：结果输出
输出诊断结果和建议。

## 常见问题
Q: ...
A: ...
```

### 编写原则

1. **目标明确**：清楚说明要解决什么问题
2. **步骤清晰**：分步骤指导，便于执行
3. **命令具体**：提供可直接执行的命令
4. **结果可读**：输出格式统一、易于理解
5. **安全优先**：涉及修改操作要有确认

## 辅助脚本开发

### Shell 脚本规范

```bash
#!/bin/bash
# 脚本说明
# 用法: ./script.sh [options]

set -e  # 遇错即停

# 引入公共函数（优雅降级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "${SCRIPT_DIR}/common.sh" ]; then
    source "${SCRIPT_DIR}/common.sh"
else
    info()    { echo "[INFO] $*"; }
    warning() { echo "[WARN] $*" >&2; }
    error()   { echo "[ERROR] $*" >&2; }
fi

# 主逻辑
main() {
    check_root
    # ...
}

main "$@"
```

### Python 脚本规范

```python
#!/usr/bin/env python3
"""
脚本说明
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='...')
    args = parser.parse_args()
    # ...

if __name__ == '__main__':
    main()
```

## 测试指南

### 测试用例编写

```bash
#!/bin/bash
# tests/test.sh

source "$(dirname "$0")/../scripts/common.sh" 2>/dev/null || true

test_basic() {
    # 测试基本功能
    echo "Testing basic functionality..."
}

test_error_handling() {
    # 测试错误处理
    echo "Testing error handling..."
}

# 运行测试
test_basic
test_error_handling

echo "All tests passed!"
```

## 发布流程

1. 完成开发和测试
2. 更新版本号
3. 提交 Pull Request
4. 代码审查
5. 合并到主分支

## 最佳实践

1. **复用共享组件**：使用 `scripts/common.sh` 和 `scripts/output.sh` 中的公共函数
2. **保持独立性**：每个 Skill 应该独立可用
3. **文档完整**：确保文档和代码同步
4. **版本管理**：遵循语义化版本
5. **持续改进**：根据反馈优化 SKILL.md
