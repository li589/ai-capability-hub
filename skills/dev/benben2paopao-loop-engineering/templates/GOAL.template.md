# GOAL.md — {{TASK_TITLE}}

> 这是 LOOP 的「意图(Intent)」要素。回答:**成功长什么样?**

---

## 一、我要解决的真实问题

{{PROBLEM_DESC}}

---

## 二、项目基本信息(LOOP 每轮都要读这块)

- **项目根目录**:`{{PROJECT_PATH}}`
- **技术栈**:{{PROJECT_LANG}}
- **依赖安装命令**:`{{INSTALL_CMD}}`
- **核心验收命令**:`{{VERIFY_CMD}}`
- **是否有自动化测试**:{{HAS_AUTO_TEST}}
- **是否需要人工验收**:{{HUMAN_REVIEW_NEEDED}}
- **本次选用 LOOP 模式**:{{LOOP_PATTERN}}

---

## 三、可验证的成功条件

### A. 自动可验证的硬指标(LOOP 每轮自动检查)

- [ ] 在项目根目录运行 `{{VERIFY_CMD}}` 退出码为 0
- [ ] 输出中没有 `FAIL` / `Error` / `失败` / `error` 字样
{{EXTRA_HARD_CRITERIA}}

### B. 人工验收(只在 HUMAN_REVIEW_NEEDED=yes 时存在)

{{HUMAN_REVIEW_CHECKLIST}}

> ⚠️ 如果 A 类全部通过 + 不需要人工验收 → 状态写 `[DONE]`,LOOP 退出
> ⚠️ 如果 A 类全部通过 + 需要人工验收 → 状态写 `[NEEDS_HUMAN_REVIEW]`,等用户手工确认后才能写 `[DONE]`

---

## 四、范围边界

LOOP **只允许**做这些事:
- 读取 `{{PROJECT_PATH}}` 下的源代码、配置、文档
- 修改源代码(具体允许目录见下一节)
- 运行验收命令、语法检查、lint
- 创建辅助文件(测试用例、工具脚本)在指定目录

LOOP **绝对不能**做这些事(详见 RULES.md 第四节):
{{FORBIDDEN_PATHS_LIST}}

---

## 五、停止条件(满足任意一条 LOOP 必须停)

1. ✅ 第三节 A 类硬指标全部满足
   → HUMAN_REVIEW_NEEDED=no:写 `[DONE]`
   → HUMAN_REVIEW_NEEDED=yes:写 `[NEEDS_HUMAN_REVIEW]`
2. 🛑 同一个错误连续 3 轮没有进展 → 写 `[STUCK]` 等人工介入
3. 🛑 触碰到 RULES.md 中的禁区 → 写 `[BLOCKED]` 等人工授权
4. 🛑 单轮修改的文件超过 {{FILES_PER_ROUND}} 个 → 写 `[TOO_BIG]` 强制分解
5. 🛑 累计运行超过 {{ROUNDS_BUDGET}} 轮 → 写 `[BUDGET_OUT]` 等评估
6. 🛑 任何一次修改后语法/编译失败,且当轮无法修复 → 写 `[SYNTAX_BROKEN]`,回滚

> 这六个停止条件是硬约束,防止原文里说的"空转、过拟合、上下文漂移、不安全的自主"。
