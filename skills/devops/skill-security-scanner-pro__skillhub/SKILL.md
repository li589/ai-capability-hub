---
name: skill-security-scanner
description: 安全扫描和修复 Skill 文件中的高风险内容；当用户需要扫描 Skill、检查安全漏洞、修复安全问题或验证修复效果时使用
---

# Skill 安全扫描器

## 任务目标
- 本 Skill 用于：检测和修复 Skill 文件及其引用文档中的安全风险内容
- 能力包含：安全风险扫描、自动修复建议、冒烟测试验证
- 触发条件：用户上传 Skill 文件需要安全检查、发现潜在安全问题、需要修复验证时

## 前置准备
- 无需额外依赖（使用 Python 标准库）
- 确保有足够权限读写目标 Skill 文件

## 操作步骤

### 步骤 1：扫描安全风险
1. 接收用户上传的 `.skill` 文件
2. 调用 `scripts/scan_skill.py` 执行扫描
   - 参数：
     - `--skill-file`: .skill 文件路径
     - `--output-dir`: 输出目录（可选，默认为临时目录）
3. 分析扫描结果，识别高风险项
4. 参考 [references/security_patterns.md](references/security_patterns.md) 理解风险类型

### 步骤 2：评估与建议修复
1. 根据扫描结果，智能体评估风险严重性
2. 参考 [references/fix_strategies.md](references/fix_strategies.md) 制定修复方案
3. 生成修复建议报告

### 步骤 3：应用修复
1. 调用 `scripts/fix_security_issues.py` 执行修复
   - 参数：
     - `--scan-result`: 扫描结果 JSON 文件路径
     - `--skill-dir`: Skill 目录路径
     - `--auto-fix`: 是否自动修复（true/false）
2. 审查修复日志，确认修复效果

### 步骤 4：冒烟测试
1. 调用 `scripts/smoke_test.py` 执行测试
   - 参数：
     - `--skill-dir`: Skill 目录路径
2. 验证修复后的 Skill 是否可用
3. 生成测试报告

### 步骤 5：重新打包
1. 确认所有修复完成且测试通过
2. 使用 `package_skill` 工具重新打包 Skill
3. 返回修复后的 .skill 文件

## 资源索引
- 必要脚本：
  - [scripts/scan_skill.py](scripts/scan_skill.py)（扫描 Skill 文件中的安全风险）
  - [scripts/fix_security_issues.py](scripts/fix_security_issues.py)（应用安全修复）
  - [scripts/smoke_test.py](scripts/smoke_test.py)（执行冒烟测试验证）
- 领域参考：
  - [references/security_patterns.md](references/security_patterns.md)（安全风险模式定义与识别规则）
  - [references/fix_strategies.md](references/fix_strategies.md)（常见风险的修复策略与最佳实践）
- 输出资产：
  - [assets/templates/risk_report_template.md](assets/templates/risk_report_template.md)（风险报告模板）

## 注意事项
- 脚本执行前会自动创建备份，修复失败可回滚
- 某些高风险项需要人工确认，不自动修复
- 扫描结果包含文件路径、行号、风险类型和修复建议
- 智能体负责风险判断和策略制定，脚本负责精确执行

## 使用示例

### 示例 1：完整扫描与修复流程
```bash
# 1. 扫描 Skill
python /workspace/projects/skill-security-scanner/scripts/scan_skill.py \
  --skill-file ./user-skill.skill \
  --output-dir ./scan-output

# 2. 查看扫描结果
cat ./scan-output/scan-result.json

# 3. 应用修复
python /workspace/projects/skill-security-scanner/scripts/fix_security_issues.py \
  --scan-result ./scan-output/scan-result.json \
  --skill-dir ./scan-output/skill-name \
  --auto-fix false

# 4. 执行冒烟测试
python /workspace/projects/skill-security-scanner/scripts/smoke_test.py \
  --skill-dir ./scan-output/skill-name
```

### 示例 2：仅扫描不修复
```bash
python /workspace/projects/skill-security-scanner/scripts/scan_skill.py \
  --skill-file ./target.skill
```

### 示例 3：自动修复并测试
```bash
python /workspace/projects/skill-security-scanner/scripts/scan_skill.py \
  --skill-file ./target.skill

python /workspace/projects/skill-security-scanner/scripts/fix_security_issues.py \
  --scan-result ./scan-output/scan-result.json \
  --skill-dir ./scan-output/skill-name \
  --auto-fix true

python /workspace/projects/skill-security-scanner/scripts/smoke_test.py \
  --skill-dir ./scan-output/skill-name
```
