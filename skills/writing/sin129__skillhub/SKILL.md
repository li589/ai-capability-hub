---
name: Claw Skills Hub 官方智能安全审核引擎
description: 对第三方Skill进行8大安全维度扫描，输出风险评分、风险等级、检测报告与审核建议。扫描维度包括：1.恶意代码与后门，2.非法指令与高危调用，3.硬编码密钥与敏感信息，4.Prompt注入与恶意诱导，5.权限越权配置，6.第三方依赖安全，7.数据合规与不落地检查，8.源码篡改校验。使用场景：(1) 新Skill上线前安全审核，(2) 已上线Skill定期安全检查，(3) Skill安全风险评估，(4) 安全合规审计，(5) 恶意代码检测。
---

# Claw Skills Hub 官方智能安全审核引擎

## 概述

本技能是Claw Skills Hub的官方安全审核引擎，用于对第三方Skill进行全面的安全扫描和风险评估。引擎运行在沙箱只读环境中，确保审核过程自身安全，不产生任何高危行为。

## 安全扫描维度

### 1. 恶意代码与后门检测
- 检测可疑的系统调用（exec, system, subprocess等）
- 检测文件系统高危操作（删除、覆盖、权限修改）
- 检测网络连接和外部通信
- 检测隐藏的后门代码和恶意负载

### 2. 非法指令与高危调用
- 检测危险shell命令
- 检测敏感API调用
- 检测权限提升尝试
- 检测环境变量篡改

### 3. 硬编码密钥与敏感信息
- 检测API密钥、密码、令牌等硬编码凭证
- 检测数据库连接字符串
- 检测加密密钥
- 检测个人身份信息（PII）

### 4. Prompt注入与恶意诱导
- 检测恶意Prompt构造
- 检测权限绕过尝试
- 检测系统指令注入
- 检测上下文污染攻击

### 5. 权限越权配置
- 检测文件权限设置
- 检测网络访问权限
- 检测系统资源限制
- 检测沙箱逃逸尝试

### 6. 第三方依赖安全
- 检测已知漏洞依赖
- 检测未授权依赖包
- 检测依赖版本风险
- 检测供应链攻击

### 7. 数据合规与不落地检查
- 检测数据本地存储
- 检测数据跨境传输
- 检测隐私数据泄露
- 检测合规性违规

### 8. 源码篡改校验
- 检测代码签名验证
- 检测哈希值校验
- 检测完整性检查
- 检测版本一致性

## 使用方法

### 基本扫描
```bash
python3 scripts/security_audit.py --skill-path /path/to/skill
```

### 详细报告
```bash
python3 scripts/security_audit.py --skill-path /path/to/skill --verbose
```

### JSON输出
```bash
python3 scripts/security_audit.py --skill-path /path/to/skill --json
```

### 特定维度扫描
```bash
python3 scripts/security_audit.py --skill-path /path/to/skill --dimensions "1,2,3"
```

## 输出格式

### 标准报告格式
```
========================================
Claw Skills Hub 安全审核报告
========================================

📋 基本信息
• Skill名称: example-skill
• 扫描时间: 2026-04-13 15:48:00
• 文件数量: 15
• 总代码行数: 1250

🔍 扫描结果
• 恶意代码与后门: ✅ 通过 (0/10)
• 非法指令与高危调用: ⚠️ 警告 (2/10)
• 硬编码密钥与敏感信息: ❌ 高风险 (5/10)
• Prompt注入与恶意诱导: ✅ 通过 (0/10)
• 权限越权配置: ✅ 通过 (0/10)
• 第三方依赖安全: ⚠️ 警告 (1/10)
• 数据合规与不落地检查: ✅ 通过 (0/10)
• 源码篡改校验: ✅ 通过 (0/10)

📊 风险评分
• 总体风险评分: 65/100
• 风险等级: 中等
• 建议: 需要修复硬编码密钥和非法调用

💡 详细建议
1. 发现硬编码API密钥，建议使用环境变量
2. 发现危险shell命令，建议使用安全API替代
3. 发现过时依赖包，建议更新到安全版本
```

### JSON输出格式
```json
{
  "audit_report": {
    "metadata": {
      "skill_name": "example-skill",
      "scan_timestamp": "2026-04-13T15:48:00Z",
      "scan_duration_seconds": 2.5,
      "total_files_scanned": 15,
      "total_lines_scanned": 1250
    },
    "risk_assessment": {
      "overall_score": 65,
      "risk_level": "medium",
      "confidence_score": 0.92
    },
    "dimension_scores": [
      {
        "dimension_id": 1,
        "dimension_name": "恶意代码与后门",
        "score": 100,
        "status": "passed",
        "issues_found": 0,
        "issues": []
      }
    ],
    "detailed_findings": [],
    "recommendations": [],
    "compliance_status": {
      "claw_standards": true,
      "security_policy": true,
      "data_protection": false
    }
  }
}
```

## 技术实现

### 沙箱安全设计
1. **只读文件系统**: 所有扫描操作在只读模式下进行
2. **网络隔离**: 禁止外部网络连接（除必要的依赖检查）
3. **资源限制**: CPU、内存、执行时间限制
4. **权限最小化**: 仅需读取权限，无需写入或执行权限

### 检测算法
1. **静态代码分析**: 基于AST的代码模式匹配
2. **正则表达式匹配**: 敏感信息模式识别
3. **依赖分析**: 包依赖关系和安全漏洞检查
4. **启发式检测**: 基于行为模式的恶意代码识别

### 风险评估模型
1. **加权评分**: 不同维度权重不同
2. **风险等级**: 低(0-30)、中(31-70)、高(71-100)
3. **置信度**: 基于检测准确性的置信评分

## 集成指南

### Skills Hub集成
```python
from security_audit_engine import SecurityAuditEngine

# 初始化审核引擎
engine = SecurityAuditEngine()

# 执行安全扫描
report = engine.audit_skill("/path/to/skill")

# 获取风险评分
risk_score = report.get_risk_score()

# 检查是否通过审核
if report.is_passed():
    print("Skill通过安全审核")
else:
    print("Skill未通过安全审核")
```

### CI/CD集成
```yaml
# .github/workflows/security-audit.yml
name: Security Audit

on:
  pull_request:
    paths:
      - 'skills/**'

jobs:
  security-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Security Audit
        run: |
          python3 scripts/security_audit.py --skill-path ./skills/${{ github.event.pull_request.head.ref }} --json > audit-report.json
          
      - name: Upload Audit Report
        uses: actions/upload-artifact@v3
        with:
          name: security-audit-report
          path: audit-report.json
```

## 参考文件

- [安全检测规则](references/security_rules.md) - 详细的检测规则和模式
- [风险评估模型](references/risk_model.md) - 风险评估算法和权重配置
- [集成示例](references/integration_examples.md) - 各种集成场景示例
- [合规标准](references/compliance_standards.md) - Claw安全合规标准

## 注意事项

1. **沙箱环境**: 本引擎设计运行在沙箱环境中，确保审核过程安全
2. **误报处理**: 可能存在误报，需要人工复核
3. **性能考虑**: 大型Skill扫描可能需要较长时间
4. **隐私保护**: 扫描过程不收集或传输用户数据
5. **持续更新**: 安全规则需要定期更新以应对新威胁

## 支持与反馈

如发现安全漏洞或有改进建议，请通过Claw Skills Hub官方渠道反馈。