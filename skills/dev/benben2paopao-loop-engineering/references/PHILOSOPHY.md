# PHILOSOPHY.md — Loop Engineering 核心理念速查

> 当用户问"什么是 Loop Engineering"或"为什么这么设计"时,Agent 用这份卡做简短回答。
> 不要讲长篇,理念部分最多 2~3 句话回答用户的具体疑问。

---

## 一句话定义

**Loop Engineering = 你不再亲自一轮一轮指挥 Agent,而是设计一个让 Agent 自我驱动的闭环系统。**

人的位置:从执行者 → 调度者。

---

## 三层技术栈

| 层次 | 优化什么 | 工作单位 |
|---|---|---|
| Prompt Engineering | 怎么措辞一条指令 | 一次手动对话 |
| Context Engineering | 给 AI 什么背景信息 | 围绕一次回答的环境 |
| **Loop Engineering** | **决定提示什么、何时提示、结果是否可接受的自运行系统** | **跨越多轮的自动工作流** |

Loop Engineering 不是替代前两者,是**叠加在它们之上**。

---

## Loop 的五阶段(Agent 内循环)

```
意图(Intent) → 上下文(Context) → 行动(Action) → 观察(Observation) → 调整(Adjustment) → 回到意图
```

LOOP 的力量不在任何单独阶段,在**闭环**。

---

## 六大要素 → 本 skill 如何实现

| 文档要素 | 在生成的 LOOP 里对应什么 |
|---|---|
| 意图(Intent) | GOAL.md |
| 技能(Skills) | RULES.md |
| 持久记忆(Memory) | STATE.md |
| 自动触发(Automations) | start-loop.bat(初级)/ Windows 任务计划(进阶) |
| 子 Agent(Sub-Agents) | PROMPT.md 步骤 4 调用 task 工具 |
| 连接器(MCP) | 首版不集成,后续可加 |
| 并行隔离(Worktrees) | 首版不需要,单 Agent 串行 |

---

## 三大风险(Agent 必须帮用户警惕)

来自 LOOP1.MD 第 342-372 行:

1. **验证仍然是用户的责任**——LOOP 说"通过了"不等于"真对了"
2. **理解债积累**——LOOP 写代码越快,用户理解的比例越低
3. **认知投降**——接受 LOOP 任何输出,是最舒适也最危险的选择

> "两个人可以构建完全相同的 Loop,却得到截然相反的结果:
> 一个用它在深度理解的基础上更快推进,
> 另一个用它来回避理解工作本身。
> Loop 不知道区别。你知道。"

这段话 Agent 在交付时**必须**贴给用户,不要省略。

---

## 关键警告

- LOOP 不是 cron + AI,真正的 LOOP 必须有**完整闭环**(自启动 + 拿信息 + 干活 + 自检 + 记录 + 停止)
- LOOP 烧 token 比单次对话快**很多倍**,首版必须设轮数预算
- 写代码的 Agent 不能给自己当 reviewer——必须有独立子 Agent 当 checker
- 模型每次会忘,**仓库不会忘**——记忆必须落到文件里
