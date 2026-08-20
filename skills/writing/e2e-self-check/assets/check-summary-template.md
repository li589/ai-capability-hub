# 检查汇总 (check.summary.md)

> 由 /e2e-self-check 自动生成 | 生成时间: {YYYY-MM-DD HH:mm}

## 元信息

| 项 | 值 |
|----|----|
| Spec 目录 | {specDir} |
| Work Item | [{workItemId}]({workItemUrl}) |
| Level | {standard \| simple} |
| Diff 范围 | {git range，如 main...HEAD} |
| 变更文件数 / 行数 | {N} 文件 / +{A} -{D} |
| 检查执行者 | 独立子代理（CodeReview / GeneralPurpose） |

## 总体判定

```
overall_result: {PASS | CONDITIONAL_PASS | FAIL}
```

| 视角 | BLOCKER | MAJOR | MINOR | 报告 |
|------|---------|-------|-------|------|
| 主链路 | {n} | {n} | {n} | [00-main-chain-report.md](./00-main-chain-report.md) |
| 产品视角 | {n} | {n} | {n} | [01-product-view.md](./01-product-view.md) |
| 研发视角 | {n} | {n} | {n} | [02-dev-view.md](./02-dev-view.md) |
| 安全SRE视角 | {n} | {n} | {n} | [03-security-sre-view.md](./03-security-sre-view.md) |
| **合计** | **{n}** | **{n}** | **{n}** | |

判定规则：无 BLOCKER 且无 MAJOR = PASS；无 BLOCKER 有 MAJOR = CONDITIONAL_PASS；有 BLOCKER = FAIL（禁止提测）。

## 阻塞项清单（BLOCKER）

<!-- 无阻塞项时写"无" -->

| # | 问题 | 证据（文件:行号） | 违反规则 | 来源报告 |
|---|------|------------------|----------|----------|
| 1 | {问题描述} | {path}:{line} | {RULE-x.x.x / BAN-x} | {00/01/02/03} |

## 重要项清单（MAJOR）

| # | 问题 | 证据（文件:行号) | 违反规则 | 来源报告 |
|---|------|------------------|----------|----------|
| 1 | {问题描述} | {path}:{line} | {规则编号或"-"} | {来源} |

## 修复建议顺序

1. {先修什么，为什么}
2. {其次}

## 结论

{一句话结论：能否进入下一阶段 / 需要修复后重检 / 禁止提测}
