# Loop Engineering Skill

> 一句话:**让任何用户在 5~10 分钟内,为自己的代码项目造出一套真实可跑的 LOOP。**

## 这是什么

把 Boris Cherny / Addy Osmani 在 2026 年 6 月推火的 **Loop Engineering** 概念,
落地成一个 OpenCode skill。用户只需说一句"帮我创建 LOOP",
Agent 就会通过 7 个问题的交互式问答,生成一套完整的 LOOP 工作目录:

```
workspace/loops/<任务名>/
├── GOAL.md          ← 目标定义(意图 Intent)
├── RULES.md         ← 项目规范(技能 Skills)
├── STATE.md         ← 持久记忆(Memory)
├── PROMPT.md        ← 启动咒语(LOOP 本体)
└── start-loop.bat   ← 一键启动器(自动触发 Automations)
```

每个文件对应原文档的 LOOP 六大要素之一,文件名风格统一,内容由用户的真实项目信息填实。

## 用户怎么用

直接在 OpenCode 对话里说:
- "帮我创建一个 LOOP"
- "我想用 Loop Engineering 修这个 bug"
- "为我的项目搭一个循环工程任务"

skill 会被自动加载,然后引导用户完成 7 步问答,最后交付可立即启动的 LOOP。

## 文件结构

```
.opencode/skills/loop-engineering/
├── SKILL.md                          ← 主入口(Agent 第一个读)
├── README.md                         ← 本文件
├── references/
│   ├── INTERVIEW.md                  ← 7 个核心问题清单 + 追问指引
│   ├── PATTERNS.md                   ← 5 种 LOOP 模式选择决策树
│   └── PHILOSOPHY.md                 ← 核心理念速查(用户问"是什么"时用)
└── templates/
    ├── GOAL.template.md              ← 目标定义模板
    ├── RULES.template.md             ← 规范约束模板
    ├── STATE.template.md             ← 持久记忆模板
    ├── PROMPT.template.md            ← 启动咒语模板
    └── start-loop.template.bat       ← 启动脚本模板
```

## 适用范围

✅ 任何代码项目:Python / Node.js / Java / Go / Rust / 前端 等
✅ 任务类型:Bug 修复、重构、依赖升级、类型迁移、新功能开发
✅ 有/无自动化测试都支持(无测试时降级为人工验收双轨制)

⚠️ 暂不支持:
- 纯写作 / 运营 / 设计任务(后续可扩展)
- 需要 GitHub MCP 等连接器的高阶 LOOP(用户跑顺基础版后再加)

## 设计原则

1. **诚实**:不编造数据,所有变量要么用户给,要么 Agent 从项目里查到证据
2. **小步**:每个 LOOP 文件首版宁愿粗糙也要能跑,不追求"完美但永远在改"
3. **可见**:Agent 做的所有自动判断都列给用户看,让用户复核
4. **保命**:六大停止条件、三道闸、轮数预算,层层防止 LOOP 失控烧 token
5. **有刹车**:GUI 项目和无测试项目强制走"人工验收"分支,不让 Agent 自己说"完成"

## 与 OpenCode 内置 skills 的关系

- 本 skill **依赖** OpenCode 的 `task` 工具(用于子 Agent 自检 / Maker-Checker 模式)
- 本 skill **不依赖**任何 MCP 连接器(首版刻意保持简单)
- 生成的 LOOP **可以**调用其他 OpenCode skills(例如 `webapp-testing` 做 UI 视觉对比)

## 关键警告(用户必读)

来自 LOOP1.MD 第 358-362 行,用户在跑通 LOOP 后必须看一次:

> "两个人可以构建完全相同的 Loop,却得到截然相反的结果:
> 一个用它在深度理解的基础上更快推进,
> 另一个用它来回避理解工作本身。
> Loop 不知道区别。你知道。"

LOOP 不是用来让人少干活的,是把人从重复劳动里抽出来,
把时间花在**判断、验收、设计 GOAL** 这三件 AI 干不了的事上。

## 升级路线

跑通基础 LOOP 后,用户可以:
1. 把 RULES.md 升级成正式 SKILL.md(放到 `.opencode/skills/<项目名>/`)
2. 加 Windows 任务计划程序定时触发
3. 接 MCP 连接器(GitHub Issues / Slack)
4. 多 LOOP 并行 + Git Worktree 隔离

但首版**强烈建议**只用最小机制跑通一次完整闭环,获得正反馈后再升级。

## 维护

如果你想改进这个 skill:
- 修改触发条件 → 改 `SKILL.md` 顶部 frontmatter 的 description
- 增加新模板字段 → 同步改 4 个 `.template.md` 文件 + `SKILL.md` 步骤 4 的变量清单
- 加新的 LOOP 模式 → 改 `references/PATTERNS.md`
- 调整问答流程 → 改 `references/INTERVIEW.md`
