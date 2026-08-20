# 安全扫描报告

## 扫描摘要

**扫描时间**: {{SCAN_TIME}}
**Skill 文件**: {{SKILL_FILE}}
**扫描范围**: {{SCAN_SCOPE}}

### 统计信息

| 指标 | 数值 |
|------|------|
| 扫描文件数 | {{FILES_SCANNED}} |
| 发现风险数 | {{RISKS_FOUND}} |
| 严重风险 (Critical) | {{CRITICAL_COUNT}} |
| 高风险 (High) | {{HIGH_COUNT}} |
| 中风险 (Medium) | {{MEDIUM_COUNT}} |
| 低风险 (Low) | {{LOW_COUNT}} |

### 风险分布

```
{{RISK_DISTRIBUTION_CHART}}
```

## 风险详情

### Critical 级别

{{#if CRITICAL_RISKS}}
{{#each CRITICAL_RISKS}}
**文件**: {{file}}  
**行号**: {{line}}  
**类型**: {{type}}  
**描述**: {{description}}  
**代码片段**: 
```
{{code_snippet}}
```
{{/each}}
{{else}}
无 Critical 级别风险
{{/if}}

### High 级别

{{#if HIGH_RISKS}}
{{#each HIGH_RISKS}}
**文件**: {{file}}  
**行号**: {{line}}  
**类型**: {{type}}  
**描述**: {{description}}  
**代码片段**: 
```
{{code_snippet}}
```
{{/each}}
{{else}}
无 High 级别风险
{{/if}}

### Medium 级别

{{#if MEDIUM_RISKS}}
{{#each MEDIUM_RISKS}}
**文件**: {{file}}  
**行号**: {{line}}  
**类型**: {{type}}  
**描述**: {{description}}  
**代码片段**: 
```
{{code_snippet}}
```
{{/each}}
{{else}}
无 Medium 级别风险
{{/if}}

## 修复建议

### 立即修复 (Critical)
{{#if CRITICAL_RECOMMENDATIONS}}
{{#each CRITICAL_RECOMMENDATIONS}}
- {{this}}
{{/each}}
{{else}}
无
{{/if}}

### 优先修复 (High)
{{#if HIGH_RECOMMENDATIONS}}
{{#each HIGH_RECOMMENDATIONS}}
- {{this}}
{{/each}}
{{else}}
无
{{/if}}

### 计划修复 (Medium)
{{#if MEDIUM_RECOMMENDATIONS}}
{{#each MEDIUM_RECOMMENDATIONS}}
- {{this}}
{{/each}}
{{else}}
无
{{/if}}

## 下一步操作

1. 审查扫描结果，确认风险项
2. 参考 [fix_strategies.md](references/fix_strategies.md) 了解修复方案
3. 使用 `fix_security_issues.py` 脚本应用修复
4. 使用 `smoke_test.py` 脚本验证修复效果

---

**注意**: 本报告由 Skill 安全扫描器自动生成，建议人工审查后再进行修复操作。
