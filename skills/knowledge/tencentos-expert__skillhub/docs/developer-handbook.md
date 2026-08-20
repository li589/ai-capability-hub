# Skill 开发者手册

本手册面向研发同学，详细介绍如何从零开始开发、测试和发布一个 TencentOS Expert Skill。

---

## 目录

1. [概述：什么是 Skill](#1-概述什么是-skill)
2. [快速开始：5 分钟创建你的第一个 Skill](#2-快速开始5-分钟创建你的第一个-skill)
3. [详细开发指南](#3-详细开发指南)
4. [测试与验证](#4-测试与验证)
5. [提交与发布](#5-提交与发布)
6. [完整示例](#6-完整示例)

---

## 1. 概述：什么是 Skill

### 1.1 Skill 定义

Skill 是一个**结构化的 AI Prompt 包**，它告诉 AI 如何完成特定的运维任务。每个 Skill 包含：

- **SKILL.md**：核心文件，定义 AI 的执行逻辑
- **skill.yaml**：元信息，定义 Skill 的名称、依赖、触发词等
- **scripts/**：可选的辅助脚本
- **tests/**：测试用例

### 1.2 Skill 工作原理

```
用户请求 → 关键词匹配 → 加载对应 Skill 的 SKILL.md → AI 执行诊断 → 输出结果
```

### 1.3 目录结构

```
skills/<skill-name>/
├── skill.yaml      # [必需] Skill 元信息定义
├── SKILL.md       # [必需] 核心 Prompt 文件
├── OWNERS          # [必需] 代码负责人
├── scripts/        # [可选] 辅助脚本
│   ├── analyze.sh
│   └── collect.py
├── docs/           # [可选] 详细文档
│   └── README.md
└── tests/          # [推荐] 测试用例
    └── test.sh
```

---

## 2. 快速开始：5 分钟创建你的第一个 Skill

### 步骤 1：使用脚手架创建 Skill

```bash
cd /path/to/tencentos-expert-skills

# 创建新模块文档
touch references/my-skill.md

# 如果需要辅助脚本
touch scripts/my-skill-collect.sh
chmod +x scripts/my-skill-collect.sh
```

### 步骤 2：修改 OWNERS 文件

```bash
# 编辑 OWNERS，添加你的邮箱
vim skills/my-skill/OWNERS
```

```
# Skill 负责人
your-name@tencent.com
```

### 步骤 3：编辑 skill.yaml

```yaml
name: my-skill
display_name: 我的技能名称
version: 1.0.0
category: performance

description: |
  这个技能用于...

owners:
  - your-name@tencent.com

dependencies:
  required:
    - top
    - ps
  optional:
    - htop

triggers:
  - 关键词1
  - 关键词2
```

### 步骤 4：编写 SKILL.md

这是**最重要的文件**，定义 AI 如何执行任务：

```markdown
# 我的技能名称

你是 TencentOS 系统运维专家，现在需要帮助用户...

## 任务目标

[清楚说明这个技能要解决什么问题]

## 执行步骤

### 步骤 1：收集信息

首先，执行以下命令收集系统信息：

\`\`\`bash
# 命令1
some_command
\`\`\`

分析上述输出，关注以下指标：
- 指标 1：正常范围是 xxx
- 指标 2：如果超过 xxx 说明 yyy

### 步骤 2：深入诊断

[继续写诊断逻辑...]

## 结果输出格式

请按以下格式输出诊断结果：

| 检查项 | 状态 | 详情 |
|-------|------|-----|
| xxx   | ✅/⚠️/❌ | ... |

## 常见问题处理

- **问题 1**：xxx
  - 解决方案：yyy

- **问题 2**：xxx
  - 解决方案：yyy
```

### 步骤 5：验证 Skill

```bash
# 验证文档格式（检查 references/ 文件引用是否存在）
grep -oP 'references/\S+\.md' references/my-skill.md | while read f; do [ -f "$f" ] || echo "BROKEN: $f"; done
```

---

## 3. 详细开发指南

### 3.1 SKILL.md 编写规范

#### 3.1.1 基本结构

```markdown
# 技能名称

[角色设定 + 任务背景]

## 任务目标

[明确说明要解决的问题]

## 前置检查

[检查必要条件，如工具是否安装、权限是否足够]

## 执行步骤

### 步骤 1：xxx
[详细步骤]

### 步骤 2：xxx
[详细步骤]

## 结果输出

[定义输出格式]

## 异常处理

[常见错误及处理方法]
```

#### 3.1.2 编写原则

| 原则 | 说明 | 示例 |
|-----|------|------|
| **角色明确** | 开头声明 AI 的角色 | "你是 TencentOS 内核专家..." |
| **目标清晰** | 明确任务目标 | "帮助用户定位 CPU 占用过高的原因" |
| **步骤具体** | 每个步骤可执行 | 提供完整的命令 |
| **命令安全** | 避免危险操作 | 只读诊断，修改需确认 |
| **输出规范** | 统一输出格式 | 使用表格、状态图标 |
| **错误处理** | 考虑异常情况 | 工具不存在、权限不足 |

#### 3.1.3 命令编写规范

```markdown
## 好的写法 ✅

\`\`\`bash
# 查看 CPU 使用率（取前 10 个进程）
ps aux --sort=-%cpu | head -11
\`\`\`

分析输出：
- 第一列 `USER`：进程所属用户
- 第三列 `%CPU`：CPU 使用率，超过 80% 需要关注
- ...

## 不好的写法 ❌

\`\`\`bash
ps aux
\`\`\`
（没有说明命令作用，没有分析指导）
```

#### 3.1.4 安全注意事项

```markdown
## 只读操作：直接执行 ✅
\`\`\`bash
cat /proc/meminfo
\`\`\`

## 修改操作：需要用户确认 ⚠️
如果需要清理日志，请先确认：
- 确认文件内容已备份或不再需要
- 执行清理：
\`\`\`bash
# 请确认后再执行
truncate -s 0 /var/log/xxx.log
\`\`\`

## 危险操作：明确警告 🚫
> ⚠️ **警告**：以下操作会重启服务，可能影响业务
\`\`\`bash
systemctl restart xxx
\`\`\`
```

#### 3.1.5 TencentOS 版本规范

本项目专为 TencentOS 设计，编写 Skill 时必须遵循以下版本规范：

| TencentOS 版本 | 包管理器 | 说明 |
|---------------|---------|------|
| **TencentOS 2** | `yum` | 对标 CentOS 7 |
| **TencentOS 3** | `dnf` | 对标 CentOS 8 |
| **TencentOS 4** | `dnf` | 独立版本，不对标任何系统 |

**重要原则**：

1. **禁止**在文档中提及 CentOS、RHEL、Red Hat 等字样
2. 涉及包管理器命令时，必须注明 TencentOS 版本

**正确示例**：

```markdown
\`\`\`bash
# 安装 smartmontools
# TencentOS 2
yum install -y smartmontools
# TencentOS 3/4
dnf install -y smartmontools
\`\`\`

\`\`\`bash
# 清理软件包缓存
# TencentOS 2（yum 管理）
yum clean all

# TencentOS 3/4（dnf 管理）
dnf clean all
\`\`\`
```

**错误示例**：

```markdown
\`\`\`bash
# CentOS/RHEL 7     ❌ 不允许
yum install -y xxx

# CentOS/RHEL 8+    ❌ 不允许
dnf install -y xxx
\`\`\`
```

### 3.2 skill.yaml 字段详解

```yaml
# ========== 必填字段 ==========

name: disk-space                    # 唯一标识符
                                    # 规则：小写字母、数字、连字符
                                    # 示例：disk-space, cpu-flamegraph

display_name: 磁盘空间排查           # 用户可见的名称

version: 1.0.0                      # 语义化版本
                                    # 格式：主版本.次版本.修订号
                                    # 主版本：不兼容的变更
                                    # 次版本：向后兼容的功能新增
                                    # 修订号：向后兼容的问题修复

category: basic-ops                 # 分类
                                    # 可选值：security / basic-ops / performance

description: |                      # 详细描述
  分析磁盘空间使用情况，
  定位占用空间大的文件和目录。

owners:                             # 负责人邮箱列表
  - zhangsan@tencent.com
  - lisi@tencent.com

# ========== 可选字段 ==========

dependencies:                       # 依赖的系统工具
  required:                         # 必需（缺少则无法运行）
    - df
    - du
  optional:                         # 可选（有则增强功能）
    - ncdu

supported_os:                       # 支持的 OS 版本
  - TencentOS Server 3.1
  - TencentOS Server 2.4
  - CentOS 7
  - CentOS 8

related_skills:                     # 关联的 Skill
  - system-log                      # 可以推荐用户一起使用
  - oom-killer

triggers:                           # 触发关键词
  - 磁盘空间                         # 用于智能匹配用户请求
  - 磁盘满
  - 空间不足
  - disk full
  - no space left

tags:                               # 标签（用于分类筛选）
  - 磁盘
  - 存储
  - 空间
```

### 3.3 辅助脚本开发

当诊断逻辑复杂时，可以将部分功能封装为脚本。

#### 3.3.1 Shell 脚本模板

```bash
#!/bin/bash
#
# 脚本名称：analyze_disk.sh
# 功能：分析磁盘空间占用
# 用法：./analyze_disk.sh [目录路径]
#
# 作者：your-name@tencent.com
# 版本：1.0.0
#

set -euo pipefail

# 引入公共函数库（优雅降级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/common.sh" ]; then
    source "${SCRIPT_DIR}/common.sh"
else
    info()    { echo "[INFO] $*"; }
    warning() { echo "[WARN] $*" >&2; }
    error()   { echo "[ERROR] $*" >&2; }
fi
[ -f "${SCRIPT_DIR}/output.sh" ] && source "${SCRIPT_DIR}/output.sh"

# 默认参数
TARGET_DIR="${1:-/}"
TOP_N="${2:-20}"

# 主函数
main() {
    print_header "磁盘空间分析报告"
    
    # 检查权限
    if [[ "${TARGET_DIR}" == "/" ]] && [[ $EUID -ne 0 ]]; then
        print_warning "分析根目录建议使用 root 权限"
    fi
    
    # 执行分析
    print_section "目录大小 TOP ${TOP_N}"
    du -sh "${TARGET_DIR}"/* 2>/dev/null | sort -hr | head -"${TOP_N}"
    
    print_section "大文件列表 (>100MB)"
    find "${TARGET_DIR}" -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -20
    
    print_footer
}

# 执行
main "$@"
```

#### 3.3.2 Python 脚本模板

```python
#!/usr/bin/env python3
"""
脚本名称：analyze_disk.py
功能：分析磁盘空间占用（高级版）
用法：python3 analyze_disk.py [目录路径] [--top N] [--format json|table]

作者：your-name@tencent.com
版本：1.0.0
"""

import argparse
import os
import sys
import json
from pathlib import Path


def get_dir_size(path: str) -> int:
    """计算目录大小"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(entry.path)
    except PermissionError:
        pass
    return total


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def analyze(target_dir: str, top_n: int = 20) -> list:
    """分析目录"""
    results = []
    
    for entry in os.scandir(target_dir):
        try:
            if entry.is_dir(follow_symlinks=False):
                size = get_dir_size(entry.path)
            else:
                size = entry.stat().st_size
            results.append({
                'name': entry.name,
                'path': entry.path,
                'size': size,
                'size_human': format_size(size),
                'is_dir': entry.is_dir()
            })
        except PermissionError:
            continue
    
    # 按大小排序
    results.sort(key=lambda x: x['size'], reverse=True)
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description='磁盘空间分析工具')
    parser.add_argument('path', nargs='?', default='/', help='目标目录')
    parser.add_argument('--top', type=int, default=20, help='显示前 N 个')
    parser.add_argument('--format', choices=['json', 'table'], default='table')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.path):
        print(f"错误：{args.path} 不是有效目录", file=sys.stderr)
        sys.exit(1)
    
    results = analyze(args.path, args.top)
    
    if args.format == 'json':
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'名称':<30} {'大小':>15} {'类型':>10}")
        print("-" * 60)
        for item in results:
            type_str = '目录' if item['is_dir'] else '文件'
            print(f"{item['name']:<30} {item['size_human']:>15} {type_str:>10}")


if __name__ == '__main__':
    main()
```

---

## 4. 测试与验证

### 4.1 测试类型

| 测试类型 | 说明 | 必要性 |
|---------|------|-------|
| **格式验证** | 检查 skill.yaml 和 SKILL.md 格式 | 必需 |
| **脚本测试** | 测试辅助脚本能否正常运行 | 推荐 |
| **Prompt 测试** | 在真实环境中测试 Prompt 效果 | 推荐 |
| **集成测试** | 端到端测试完整流程 | 可选 |

### 4.2 格式验证

```bash
# 验证 references/ 中文件引用的完整性
for f in references/*.md; do
    grep -oP '`references/\S+\.md`' "$f" | tr -d '`' | while read ref; do
        [ -f "$ref" ] || echo "BROKEN in $f: $ref"
    done
done

# 验证 SKILL.md 文档路径映射表
grep 'references/' SKILL.md | grep -oP 'references/\S+\.md' | sort -u | while read ref; do
    [ -f "$ref" ] || echo "MISSING: $ref"
done
```

### 4.3 编写测试用例

在 `tests/` 目录下创建测试脚本：

```bash
#!/bin/bash
#
# tests/test.sh - Skill 测试脚本
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "${SCRIPT_DIR}")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo "=========================================="
echo "测试 Skill: $(basename "${SKILL_DIR}")"
echo "=========================================="

# 测试 1：skill.yaml 存在且有效
echo -n "检查 skill.yaml... "
if [[ -f "${SKILL_DIR}/skill.yaml" ]]; then
    # 检查必填字段
    if grep -q "^name:" "${SKILL_DIR}/skill.yaml" && \
       grep -q "^display_name:" "${SKILL_DIR}/skill.yaml" && \
       grep -q "^version:" "${SKILL_DIR}/skill.yaml"; then
        pass "skill.yaml 有效"
    else
        fail "skill.yaml 缺少必填字段"
    fi
else
    fail "skill.yaml 不存在"
fi

# 测试 2：SKILL.md 存在且非空
echo -n "检查 SKILL.md... "
if [[ -f "${SKILL_DIR}/SKILL.md" ]] && [[ -s "${SKILL_DIR}/SKILL.md" ]]; then
    pass "SKILL.md 有效"
else
    fail "SKILL.md 不存在或为空"
fi

# 测试 3：OWNERS 存在
echo -n "检查 OWNERS... "
if [[ -f "${SKILL_DIR}/OWNERS" ]]; then
    pass "OWNERS 存在"
else
    fail "OWNERS 不存在"
fi

# 测试 4：检查依赖工具（仅检查 required）
echo -n "检查依赖工具... "
REQUIRED_TOOLS=$(grep -A 100 "^dependencies:" "${SKILL_DIR}/skill.yaml" | \
                 grep -A 100 "required:" | \
                 grep "^\s*-" | \
                 sed 's/^\s*-\s*//' | \
                 head -10)

MISSING_TOOLS=""
for tool in $REQUIRED_TOOLS; do
    if ! command -v "$tool" &>/dev/null; then
        MISSING_TOOLS="${MISSING_TOOLS} ${tool}"
    fi
done

if [[ -z "$MISSING_TOOLS" ]]; then
    pass "所有依赖工具已安装"
else
    echo -e "${RED}缺少工具:${MISSING_TOOLS}${NC}"
fi

# 测试 5：如果有辅助脚本，检查语法
if [[ -d "${SKILL_DIR}/scripts" ]]; then
    echo -n "检查脚本语法... "
    SCRIPT_ERROR=0
    for script in "${SKILL_DIR}"/scripts/*.sh; do
        if [[ -f "$script" ]]; then
            if ! bash -n "$script" 2>/dev/null; then
                echo -e "${RED}语法错误: $(basename "$script")${NC}"
                SCRIPT_ERROR=1
            fi
        fi
    done
    if [[ $SCRIPT_ERROR -eq 0 ]]; then
        pass "脚本语法正确"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}所有测试通过！${NC}"
echo "=========================================="
```

### 4.4 Prompt 效果测试

#### 方法 1：使用 CodeBuddy 测试

1. 将 Skill 加载到 CodeBuddy
2. 输入触发词，观察 AI 是否正确执行
3. 检查输出是否符合预期格式

---

## 5. 提交与发布

### 5.1 提交前检查清单

在提交 PR 前，请确保：

- [ ] `skill.yaml` 所有必填字段已填写
- [ ] `SKILL.md` 内容完整，步骤清晰
- [ ] `OWNERS` 已更新为你的邮箱
- [ ] 文档引用完整性验证通过（无 BROKEN 引用）
- [ ] 测试用例通过
- [ ] 版本号符合语义化版本规范

### 5.2 提交流程

```bash
# 1. 创建功能分支
git checkout -b feature/add-my-skill

# 2. 添加文件
git add skills/my-skill/

# 3. 提交（使用规范的 commit message）
git commit -m "feat(skills): 添加 my-skill 技能

- 实现 xxx 功能
- 添加辅助脚本
- 添加测试用例"

# 4. 推送到远程
git push origin feature/add-my-skill

# 5. 创建 Pull Request
```

### 5.3 Commit Message 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- `feat`: 新增 Skill 或功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `refactor`: 重构（不影响功能）
- `test`: 测试相关
- `chore`: 其他杂项

示例：
```
feat(skills/performance): 添加 CPU 火焰图技能

- 支持使用 perf 采集 CPU 性能数据
- 自动生成火焰图 SVG
- 添加常见热点分析指导

Closes #123
```

### 5.4 版本更新规则

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 修复 Bug | 修订号 +1 | 1.0.0 → 1.0.1 |
| 新增功能（向后兼容） | 次版本 +1 | 1.0.1 → 1.1.0 |
| 重大变更（不兼容） | 主版本 +1 | 1.1.0 → 2.0.0 |

---

## 6. 完整示例

以下是一个完整的 `disk-space` Skill 示例：

### 6.1 skill.yaml

```yaml
name: disk-space
display_name: 磁盘空间排查
version: 1.0.0
category: basic-ops

description: |
  分析磁盘空间使用情况，快速定位占用空间大的文件和目录，
  提供清理建议，帮助解决磁盘空间不足问题。

owners:
  - zhangsan@tencent.com

dependencies:
  required:
    - df
    - du
    - find
  optional:
    - ncdu
    - lsof

supported_os:
  - TencentOS Server 3.1
  - TencentOS Server 2.4
  - CentOS 7
  - CentOS 8

related_skills:
  - system-log
  - oom-killer

triggers:
  - 磁盘空间
  - 磁盘满
  - 空间不足
  - disk full
  - no space left
  - 磁盘告警

tags:
  - 磁盘
  - 存储
  - 空间
  - 清理
```

### 6.2 SKILL.md

```markdown
# 磁盘空间排查

你是 TencentOS 系统运维专家，帮助用户排查和解决磁盘空间问题。

## 任务目标

当用户报告磁盘空间不足、磁盘满、或收到磁盘告警时，帮助用户：
1. 了解当前磁盘使用情况
2. 定位占用空间最大的目录和文件
3. 提供安全的清理建议

## 执行步骤

### 步骤 1：查看整体磁盘使用情况

首先，让我们查看所有挂载分区的使用情况：

\`\`\`bash
df -h
\`\`\`

**分析要点：**
- `Use%` 列显示使用率，**超过 85% 需要关注，超过 95% 紧急处理**
- 重点关注 `/`、`/home`、`/var` 等关键分区
- 检查是否有分区 100% 满

### 步骤 2：检查 inode 使用情况

有时磁盘空间还有，但 inode 耗尽也会导致无法创建文件：

\`\`\`bash
df -i
\`\`\`

**分析要点：**
- 如果 `IUse%` 接近 100%，说明小文件过多
- 常见原因：大量小文件、邮件队列堆积

### 步骤 3：定位占用空间大的目录

从根目录开始，逐层定位空间占用：

\`\`\`bash
# 查看根目录下各目录大小（排除特殊文件系统）
du -sh /* 2>/dev/null | sort -hr | head -15
\`\`\`

根据输出，继续深入分析占用最大的目录：

\`\`\`bash
# 替换 <目录> 为上一步发现的大目录
du -sh /var/* 2>/dev/null | sort -hr | head -10
du -sh /home/* 2>/dev/null | sort -hr | head -10
\`\`\`

### 步骤 4：查找大文件

查找超过 100MB 的大文件：

\`\`\`bash
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -20
\`\`\`

**常见大文件位置：**
- `/var/log/` - 日志文件
- `/tmp/` - 临时文件
- `/var/lib/docker/` - Docker 镜像和容器
- `/home/*/` - 用户目录

### 步骤 5：检查已删除但未释放的文件

有时文件已删除，但进程仍持有句柄，空间未释放：

\`\`\`bash
lsof 2>/dev/null | grep deleted | head -20
\`\`\`

如果发现大量已删除文件，可能需要重启相关进程释放空间。

## 结果输出

请按以下格式输出诊断结果：

### 📊 磁盘使用概览

| 分区 | 大小 | 已用 | 可用 | 使用率 | 状态 |
|------|------|------|------|--------|------|
| /    | xxx  | xxx  | xxx  | xx%    | ✅/⚠️/❌ |

### 🔍 空间占用 TOP 10

| 排名 | 目录/文件 | 大小 | 说明 |
|------|-----------|------|------|
| 1    | xxx       | xxx  | xxx  |

### 💡 清理建议

根据分析结果，提供具体的清理建议。

## 常见清理操作

> ⚠️ **注意**：以下清理操作请在确认后再执行

### 1. 清理系统日志

\`\`\`bash
# 查看日志大小
du -sh /var/log/*

# 清理超过 7 天的日志（谨慎执行）
find /var/log -type f -name "*.log" -mtime +7 -delete

# 或使用 logrotate 强制轮转
logrotate -f /etc/logrotate.conf
\`\`\`

### 2. 清理软件包缓存

\`\`\`bash
# CentOS/TencentOS
yum clean all
rm -rf /var/cache/yum/*
\`\`\`

### 3. 清理旧内核

\`\`\`bash
# 查看已安装的内核
rpm -qa | grep kernel

# 清理旧内核（保留当前使用的）
package-cleanup --oldkernels --count=2
\`\`\`

### 4. 清理 Docker（如适用）

\`\`\`bash
# 查看 Docker 空间占用
docker system df

# 清理未使用的资源
docker system prune -a
\`\`\`

### 5. 清理临时文件

\`\`\`bash
# 清理 /tmp（通常安全）
find /tmp -type f -atime +7 -delete

# 清理 /var/tmp
find /var/tmp -type f -atime +7 -delete
\`\`\`

## 异常处理

### Q: df 和 du 显示的大小不一致？

A: 可能原因：
1. 已删除文件被进程占用 → 检查 `lsof | grep deleted`
2. 挂载点遮挡 → 检查 `/proc/mounts`

### Q: 找不到大文件但空间仍满？

A: 检查以下情况：
1. 检查 inode：`df -i`
2. 检查保留块：`tune2fs -l /dev/xxx | grep Reserved`
3. 检查隐藏的挂载点

### Q: 清理后空间没有释放？

A: 如果删除的文件被进程占用：
\`\`\`bash
# 找到占用进程
lsof | grep deleted
# 重启对应服务或进程
\`\`\`
```

### 6.3 OWNERS

```
# disk-space Skill 负责人
zhangsan@tencent.com
```

---

## 附录

### A. 常用命令速查

| 场景 | 命令 |
|------|------|
| 查看磁盘使用 | `df -h` |
| 查看 inode | `df -i` |
| 目录大小 | `du -sh /path/*` |
| 查找大文件 | `find / -type f -size +100M` |
| 已删除文件 | `lsof \| grep deleted` |

### B. 相关文档链接

- [TencentOS 官方文档](https://cloud.tencent.com/document/product/1397)
- [Linux 磁盘管理](https://www.kernel.org/doc/html/latest/filesystems/)

### C. 获取帮助

- 负责人：见 OWNERS 文件
