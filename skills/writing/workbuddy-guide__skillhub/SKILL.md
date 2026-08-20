---
name: workbuddy-guide
version: 2.3.0
description: WorkBuddy 全功能使用指南与故障排查手册（适配客户端 5.3.13）。用户问 WorkBuddy 怎么用/怎么配/连不上/报错，或问"我是HR/开发/运营怎么用"按角色推荐，或问人机双写/协同编辑/划词改文档，或问资料库/团队空间/三种载体/轻量发布，或问设计创意/Ardot/UI生成，或问多端同步/手机远程电脑/锁屏远程，或问灵感/一键做同款/套版复刻时触发。覆盖连接器、专家、自动化、新手引导、环境诊断、Teams协作、知识库、资料库、设计创意、多端同步、灵感、场景模式、记忆系统、模型选择、安全等全场景。边界不清时会先反问确认。内置错误速查表 + 官方错误码 + 59条FAQ + 6类角色路线图 + 一键诊断脚本，新手45分钟上手。
---

# WorkBuddy 使用指南

本技能是一个打包好的 WorkBuddy 参考手册，安装后开箱即用。

## 什么时候用这本手册？

> 遇到以下情况，直接在对话里问就行——本手册会自动匹配，不需要手动激活。

| 你遇到的情况 | 该查哪个部分 |
|-------------|-------------|
| "不知道怎么配 XXX" | 关键词速查表 → 对应功能文档 |
| "连不上 / 用不了 / 报错了" | 连接器排查 → `check_env.py` 诊断 |
| "第一次用，不知道从哪开始" | 新手 6 步路径 |
| "想让 AI 更懂我 / 更顺手" | Soul.md → 记忆系统 → 提示词 |
| "某个功能怎么用" | 关键词速查表 → 对应文档 |
| "试了都不行" | FAQ → `troubleshooting.md` → `check_env.py` |
| "怎么定时自动干活" | 自动化配置 |
| "安全吗 / 数据隐私" | 网络安全（术语表） |

**怎么叫出来**：在对话中直接提 WorkBuddy 相关的问题即可，比如"连接器连不上怎么办""怎么创建专家"——手册会自动加载。

## 触发规则（什么时候会触发 / 不会触发）

**会触发（13 种场景）：**
1. 提到 WorkBuddy 任何功能名（连接器/专家/自动化/Teams/场景模式/记忆/模型/安全中心/人机双写/资料库/设计创意/多端同步/灵感）
2. 描述 WorkBuddy 报错或异常（连不上/用不了/报错/不生效/没反应/错误码）
3. 问 WorkBuddy 配置方法（怎么配/怎么设/怎么连/怎么装）
4. 问 WorkBuddy 使用问题（怎么用/怎么操作/在哪设置）
5. 问自动化/定时任务相关问题（不触发/怎么设/RRULE 写法）
6. 问专家/专家团相关问题（创建/修改/不生效/注册）
7. 问 IMA 知识库/腾讯文档/腾讯会议集成问题
8. 问版本变更/新功能相关问题（某版本加了什么/某功能怎么没了）
9. 问人机双写/协同编辑/划词改文档相关问题（选中文字让 AI 改/边栏编辑文档）
10. 问资料库相关问题（我的文档/团队空间/三种载体/MD·CSV·HTML联动/本地HTML发在线链接/轻应用）
11. 问设计创意相关问题（Ardot/一句话生成UI/PPT/海报/设计稿转代码/画布精修）
12. 问多端同步相关问题（手机连电脑/移动端远程/锁屏远程/远程停止任务/多设备切换）
13. 问灵感相关问题（灵感库/一键做同款/制作我的版本/套版复刻/七大场景成品）

**不会触发（4 种场景）：**
1. 问其他产品的问题（Claude Code/Cursor/VS Code 等）
2. 纯代码/编程问题（写个函数/改个 bug/解释代码）
3. 要求修改本 skill 文件本身（请直接要求 AI 编辑文件，不通过本 skill）
4. 与 WorkBuddy 完全无关的通用问题（天气/翻译/写作等）

**边界模糊问题处理示例：**
| 用户原话 | Skill 判定 | 实际处理 |
|---------|-----------|---------|
| "我的 WorkBuddy 好卡" | 边界模糊（可能是网络/上下文/文件多） | 先反问：是连接慢、响应慢、还是文件太多？再给对应排查 |
| "帮我写个 Python 函数" | 不在范围（纯代码） | 礼貌拒绝："这是编程问题，直接让 AI 写代码即可，不用走本手册" |
| "腾讯文档怎么同步到 IMA" | 明确在范围（集成） | 直接给步骤：腾讯文档导出 → IMA 知识库上传 → 跨产品调用 |
| "WorkBuddy 怎么用" | 太宽泛 | 反问角色/场景："你是 HR/开发/运营？想做哪类事？"再指角色路线图 |

## 设计原则（本手册怎么取舍内容）

1. **只收录高概率真实困惑**：FAQ 每条都对应真实踩坑场景，一问一答 ≤150 字，不为凑数而写
2. **纯 bug 修复不收录**：客户端已修复的历史 bug 不写进手册（官方 Changelog 可查），只保留当前版本仍有效的应对方案
3. **三级检索不跳层**：速查卡 → 深度文档 → 官方文档，由浅入深，避免新手一上来就啃长文
4. **修复路径分级**：每个故障给「一级修复（最常见原因）→ 二级修复 → 验证方法」，不堆所有可能性
5. **版本适配只标不展开**：客户端新版本仅影响口径时在 FAQ 中标注版本号，不为每个小版本新增条目

## 🚀 新手学习路径（45分钟搞定）

> 第一次使用 WorkBuddy？按这个顺序来，约 45 分钟完成全部配置。

```
第1步：立规矩（5分钟）
  → 阅读 卡片7，按聊天式引导完成 Soul.md 配置
  → 输出：~/.workbuddy/SOUL.md 已生成

第2步：学下指令（10分钟）
  → 阅读 09-prompting-best-practices.md，掌握任务交代五要素
  → 验证：用一条结构化 Prompt 让 WorkBuddy 一次完成一个简单任务

第3步：连第一个工具（10分钟）
  → 阅读 卡片1，完成任意一个 MCP 连接器配置
  → 验证：工具调用成功一次

第4步：创建第一个专家（10分钟）
  → 阅读 卡片2，用三步法创建你的第一个自定义专家
  → 验证：专家出现在列表中，能正常对话

第5步：选对模式（5分钟）
  → 阅读 10-interaction-modes.md，理解 Ask/Plan/Craft 区别
  → 验证：日常用 Craft，不确定时切回 Ask 或 Plan

第6步：跑一次诊断（5分钟）
  → 运行 scripts/check_env.py，确认环境无异常
  → 输出：诊断报告显示 ✅
```

完成以上6步 → 你已经可以日常使用 WorkBuddy 了！
遇到问题 → 从上到下按 速查卡 → 深度文档 → 官方文档 检索

---

## 三层检索体系（🚀 升级版）

```
用户提问 WorkBuddy 相关问题
        │
        ▼
[第1层] 场景速查 → references/05-quick-cards.md
  7张"问题-解决方案-验证"卡片，3分钟内定位修复
        │
        │ 无匹配 ↓
        ▼
[第2层] 深度文档 → references/ 目录
  ├── troubleshooting.md    🆕 跨领域综合诊断决策树
  ├── 01-architecture.md    架构认知、核心概念
  ├── 02-connector-troubleshooting.md  连接器排查（含错误码对照表）
  ├── 03-expert-workflow.md           专家创建修改（含Prompt设计模式）
  ├── 04-automation-patterns.md       自动化配置（含RRULE模板库）
  ├── 06-scenario-examples.md         🆕 18个真实场景案例（通用+职场职能）
  ├── 20-scenario-integrations.md     🆕 集成与端到端案例（IMA+腾讯文档+深度闭环）
  ├── 07-advanced-practice.md         🆕 进阶工作习惯（工作空间/任务管理/探索复用/Claw远程）
  ├── 08-glossary.md                  📖 术语表（MCP/RRULE/Soul.md等核心概念速查）
  ├── 09-prompting-best-practices.md  🆕 提示词最佳实践（五要素/会话管理/质量自检）
  ├── 10-interaction-modes.md         🆕 交互模式与通道（Ask/Plan/Craft/助理/小程序/多端同步）
  ├── 11-memory-system.md             🆕 记忆系统详解（Cloud/Local/Workspace三层架构）
  ├── 12-faq.md                       📖 常见问答（Q&A结构，覆盖连接器/自动化/专家/记忆/模型边界问题）
  ├── 13-teams-collaboration.md        🆕 Teams团队协作（项目/看板/资产库/任务流转/消息中心）
  ├── 14-scene-modes.md                🆕 场景模式与工作界面（办公/开发/设计 + 布局）
  ├── 15-ima-official-knowledge.md     🆕 IMA官方知识库兜底检索（可选，需IMA已连接）
  ├── 16-ima-knowledge-base-guide.md   🆕 IMA知识库操作指南（连接/引用/存回/解绑）
  ├── 17-tencent-meeting-guide.md      🆕 腾讯会议Skill实践（安装/会议管理/纪要）
  ├── 19-role-routes.md                🆕 按角色快速上手（6类岗位路线图）
  ├── 21-ziliaoku-guide.md             🆕 资料库指南5.3.11（我的文档/团队空间/三种载体/轻量发布/人机修订）
  ├── 22-design-creative-guide.md      🆕 设计创意指南（Ardot/对话生成UI/PPT/海报/设计稿转代码）
  └── 23-inspiration-guide.md          🆕 灵感指南（七大场景成品库/一键做同款/自动就位，含三灵感划界）
        │
        │ 无匹配 / 涉及最新版本 ↓
        ▼
[第3层] 官方文档 → WebFetch
  ├── https://www.codebuddy.cn/docs/workbuddy/Overview
  ├── https://www.codebuddy.cn/docs/workbuddymini/quick-start/Overview
  └── https://www.codebuddy.cn/docs/workbuddy/Changelog
        │
        │ WebFetch 仍无明确答案 ↓
        ▼
[第3.5层] IMA 官方知识库（可选）
  ├── 前置条件：IMA 连接器处于 connected 状态
  ├── 调用方式：mcp__ima-mcp__search_knowledge
  │    knowledge_base_id = 7472132158135857
  │    query = 用户原始问题关键词
  └── 适用：本 skill 未覆盖的最新功能、版本特定问题
        │
        │ 未连接 IMA 时跳过，不阻断流程 ↓
        ▼
[第4层] 兜底建议
  → 指引用户查看桌面应用内帮助、社区或提交反馈
```

## 参考文件索引

| 场景 | 读取文件 | 新增亮点 |
|------|---------|---------|
| 🆕 综合诊断 | `references/troubleshooting.md` | 跨领域决策树、一键诊断命令、上报信息模板 |
| 架构认知 | `references/01-architecture.md` | 核心概念、七层定制化体系（Memories→Skills→Automations→Connectors→Experts→Expert Teams→Teams）、常见误区 |
| MCP/连接器故障 | `references/02-connector-troubleshooting.md` | 错误码对照表、日志分析、代理修复、逐步骤排查 |
| 专家创建/修改 | `references/03-expert-workflow.md` | Prompt设计模式(A/B/C)、Team SOP指南、格式错误修复 |
| 自动化配置 | `references/04-automation-patterns.md` | RRULE模板库、场景模板(6个)、故障排查、编写规范 |
| 快速查问题 | `references/05-quick-cards.md` | 7张卡片含新手引导，每张含验证步骤 + 错误码修复表 |
| 🆕 场景案例 | `references/06-scenario-examples.md` | 18个真实案例（通用+职场职能） |
| 🆕 集成/端到端案例 | `references/20-scenario-integrations.md` | IMA+腾讯文档+3条端到端深度闭环 |
| 🆕 进阶习惯 | `references/07-advanced-practice.md` | 工作空间分区/任务管理/探索复用/专家vsSkill/Claw远程 |
| 📖 术语表 | `references/08-glossary.md` | 核心概念速查（MCP/RRULE/SOP/Soul.md/模型/网络安全等） |
| 🆕 提示词实践 | `references/09-prompting-best-practices.md` | 任务交代五要素、会话管理、常见误区、质量自检清单 |
| 🆕 交互模式 | `references/10-interaction-modes.md` | Ask/Plan/Craft 三种模式、权限管理、三条交互通道、多端同步（手机远程电脑/锁屏远程） |
| 🆕 记忆系统 | `references/11-memory-system.md` | 三层记忆架构（Cloud/Local/Workspace）、画像管理、隐私控制 |
| 📖 常见问答 | `references/12-faq.md` | Q&A 结构，覆盖连接器/自动化/专家/记忆/模型/IMA/Teams 边界问题 |
| 🆕 Teams 协作 | `references/13-teams-collaboration.md` | 项目创建、看板、资产库、数据源、任务流转、消息中心 |
| 🆕 场景模式 | `references/14-scene-modes.md` | 办公/开发/设计三种场景、快捷方式联动、界面布局 |
| 🆕 IMA 官方知识库 | `references/15-ima-official-knowledge.md` | 官方教程/常见问题/功能说明，仅在 IMA 已连接时作为兜底检索 |
| 🆕 IMA 知识库操作 | `references/16-ima-knowledge-base-guide.md` | 连接授权、引用文件、产物存回、解除绑定 |
| 🆕 腾讯会议 Skill | `references/17-tencent-meeting-guide.md` | Skill安装（Token获取）、会议管理、成员管理、录制转写纪要 |
| 🆕 按角色上手 | `references/19-role-routes.md` | 6 类岗位差异化入口（通用/HR/开发/运营/财务/项目负责人） |
| 🆕 资料库 | `references/21-ziliaoku-guide.md` | 5.3.11 资料库（我的文档/团队空间/三种载体一套数据/轻量发布/人机修订，含 IMA 划界） |
| 🆕 设计创意 | `references/22-design-creative-guide.md` | Ardot 集成（对话生成UI/PPT/海报、跳转精修、设计稿一键生成应用代码） |
| 🆕 灵感 | `references/23-inspiration-guide.md` | 灵感模块（七大场景成品库、一键做同款、Prompt/Skill/专家自动就位，含三灵感划界） |
| 手工诊断 | `scripts/check_env.py` | 🆕 一键环境诊断脚本（自动检测代理/连接器/专家/日志；`--fix` 自动修复 JSON/代理/连接器状态，`--collect-logs` 导出脱敏快照。网络/账号/权限问题仍需按 troubleshooting 手动处理） |
| 关键词搜索 | `scripts/quick-search.sh` | 在知识库中 grep 关键词，快速定位相关文档（Windows 需 Git Bash） |

> **难度标记**：🔴 新手必读（卡片1/2/7）  🟡 进阶（卡片3/4）  🟢 高级（卡片5/6）

## 使用规范

1. **检索优先级**：快速卡 → 深度文档 → 官方文档（不要跳层）
2. **读取粒度**：先用 Grep 定位关键词，再读取对应段落，避免全文件加载
3. **诊断工具**：复杂环境问题先运行 `python scripts/check_env.py` 获取全局状态
4. **更新维护**：发现新踩坑经验时，追加到对应文件的"踩坑经验"区域
5. **只读操作**：本技能参考文件不修改用户项目文件，仅提供检索和回答
6. **聊天式分步引导**（来自新手指南）：引导用户配置时，每次只问1个问题，不给表格；等用户回答后再问下一个；确认时只问"OK 还是改？"
7. **Soul.md 六条规矩书**（基于四大支柱：核心性格 + 说话方式 + 工作原则 + 红线，可复用）：
   - 第一条：**核心性格** — 用 2-3 句话定义 AI 是谁（身份/职业/核心价值），作为所有回答的性格兜底
   - 第二条：**说话方式** — 明确该说什么、不该说什么。消除 AI 味：禁止"好的呢~""您说得太对了""感谢您的提问"等客套话，按用户偏好切换命令式/分析式/轻松感
   - 第三条：**工作原则** — 3-5 条铁律保证专业度：带着方案来、干完活顺手复盘、一次到位不反复确认、不确定就说"不确定"但先给最可能答案
   - 第四条：**嘴严** — 隐私/文件/聊天记录/未公开内容绝不泄露，敏感信息不记录不转述
   - 第五条：**红线禁区** — 法务合规底线 + 用户个人雷区（特定话题/语气/内容类型），绝不越界
   - 第六条：**持续进化** — AI 出主意、用户做决定；每次互动都是学习机会，随时用"你应该…""不要…"修正规则；开启全局记忆，长期积累偏好
   - **Soul.md 互动采集流程**（聊天式，每次只问 1 个问题）：
     1. 启动："准备好了吗，让我来修改你的性格档案"
     2. Q1 → 你希望我说话什么风格？（命令式/分析式/轻松/严肃…）
     3. Q2 → 有没有你特别讨厌的回答方式？（具体举例，如"不要客套话"）
     4. Q3 → 工作中有什么原则是你特别看重的？（"拿不准先问""不要省略步骤"…）
     5. Q4 → 有没有绝对不能碰的红线？（内容类型/语气/合规边界）
     6. 生成 Soul.md → 展示确认 → "OK 还是改？" → 写入 ~/.workbuddy/SOUL.md
     7. 后续维护：随时用"你要…""你应该…""不要…"句式微调规则，无需重新走完整流程
8. **按职业推荐技能包**（可复用为快速配置模板）：
   - 通用必装：Skill安全扫描、Agent Browser、AI绘图、PDF生成、Word生成、PPT生成
   - 自媒体/内容运营：小红书图文发布、微信公众号发布、AI写作助手
   - 企业培训：AI视频生成、Excel处理
   - 开发/技术：GitHub热门项目、ArXiv论文追踪

## ⚠️ 不适用场景（本 skill 不覆盖）

**先看一眼，少走弯路——这几种情况不适合查本手册：**

| 不适用 | 原因 | 替代方案 |
|--------|------|---------|
| 问 WorkBuddy 版本更新日志的最新内容 | 文档可能滞后于版本 | 直接用 WebFetch 查官方 Changelog |
| 需要修改 Skill 文件本身 | 只读操作原则 | 先退出本 skill，直接要求 AI 编辑文件 |
| 特定连接器的 API 入参/出参细节 | 连接器文档通常由对应 MCP 工具自行描述 | 直接问 AI 该连接器的用法，AI 会读取内置 schema |
| 代码调试 / 编程问题 | 本手册不覆盖编程 | 直接描述技术问题，AI 切入编程模式 |
| "帮我写一个 skill" | 创建类操作超出参考手册范围 | 要求 AI 直接用 `Skill` 工具创建，不通过本 skill |
| IMA 官方知识库未连接 | 第3.5层可选检索依赖 IMA 连接器 | 正常走 WebFetch 和后续流程，不阻断 |
| 不可复现的一次性故障 | 无通用排查模式 | 运行 `check_env.py` 获取诊断报告，提交给 AI 分析 |

> 💡 **记住：用它查用法，要动手干活时退出就行。**

## 官方文档智能检索

当参考文件无法解决用户问题，或涉及版本更新、新功能时，**必须用 WebFetch 主动检索官方文档**：

### 检索链接

| 场景 | 文档链接 | 用途 |
|------|----------|------|
| 综合文档 | `https://www.codebuddy.cn/docs/workbuddy/Overview` | 全局入口，覆盖所有功能模块 |
| 快速入门 | `https://www.codebuddy.cn/docs/workbuddymini/quick-start/Overview` | WorkBuddy Mini 新手引导 |
| 更新日志 | `https://www.codebuddy.cn/docs/workbuddy/Changelog` | 版本变更、新功能、Bug修复 |
| 连接器文档 | `https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector` | MCP/连接器配置、错误码、常见问题 |
| 专家系统文档 | `https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Expert-Center` | 专家创建/修改、plugin.json 字段、团队协作 |

### WebFetch 检索策略

```
用户提问
    │
    ▼
参考文件有答案？── Yes ─→ 直接回复
    │ No
    ▼
用 WebFetch 检索官方文档:
  综合功能问题 → fetch_url = "https://www.codebuddy.cn/docs/workbuddy/Overview"
                prompt = "提取与'{关键词}'相关的内容"
  版本/更新问题 → fetch_url = "https://www.codebuddy.cn/docs/workbuddy/Changelog"
                prompt = "提取最新版本号和变更内容"
  Mini入门问题 → fetch_url = "https://www.codebuddy.cn/docs/workbuddymini/quick-start/Overview"
                prompt = "提取与'{关键词}'相关的入门指南"
    │
    ▼
官方文档有答案？── Yes ─→ 整理回复，注明来源为官方文档
    │ No
    ▼
指引用户查阅其他渠道（桌面应用内帮助、changelog、社区等）
```

## 问题类型决策树

先分大类，再查下表：

```
你的问题属于哪类？
    │
    ├── 🔧 某个功能不工作 / 报错
    │     → 连接器失败？查"连接器/MCP"
    │     → 自动化没触发？查"自动化"
    │     → 整体不确定？先跑 check_env.py
    │
    ├── ❓ 不知道怎么用 / 怎么配
    │     → 第一天上手？走"新手引导"路径
    │     → 要创建专家？查"专家"
    │     → 不知道怎么交任务？查"提示词"
    │     → 不知道怎么选模型？查"模型"
    │
    ├── 🤖 想让 AI 更懂我 / 更顺手
    │     → 改说话风格？查"立规矩/Soul.md"
    │     → 跨会话记住偏好？查"记忆"
    │     → 换工作模式？查"交互模式"
    │
    └── 🔒 安全 / 权限 / 合规
          → 数据安全？查"网络安全"
          → 权限控制？查"交互模式"
          → 企业安全？查"网络安全"
```

## 关键词速查

| 自然语言提问 | 技术关键词 | 对应文档 |
|-------------|-----------|---------|
| "不知道哪坏了"、"整体出问题" | 综合诊断、不确定原因 | `references/troubleshooting.md` |
| "WorkBuddy是什么"、"有哪些功能" | 架构、核心概念、组件 | `references/01-architecture.md` |
| "连不上"、"工具用不了"、"调用失败" | MCP失败、连接器、disconnected、401、404、错误码 | `references/02-connector-troubleshooting.md` |
| "帮我建个专家"、"自定义AI"、"修改专家配置" | 专家、expert-manager、创建专家、Prompt设计 | `references/03-expert-workflow.md` |
| "定时任务没执行"、"怎么设提醒" | 自动化、schedule、RRULE、定时、不触发 | `references/04-automation-patterns.md` |
| "回答不准"、"格式不对"、"太啰嗦" | 回答质量、提示词优化、格式错误 | `references/05-quick-cards.md`（卡片4） |
| "查股价"、"基金数据"、"财报" | 股票、行情、westock、neodata | `references/05-quick-cards.md`（卡片5） |
| "多个AI一起工作"、"搭专家团" | 专家团、多智能体、Team、SOP | `references/05-quick-cards.md`（卡片6） |
| "环境检查"、"跑诊断" | 环境诊断、全局检查、check_env | `scripts/check_env.py` |
| 🔢 "错误码 1001/3002/6003"、"报错 11115"、"14003" | 错误码、数字报错、模型侧/网络/频率限制/输入过长 | `references/troubleshooting.md`（五、官方错误码速查） |
| ✍️ "人机双写"、"划词改文档"、"选中文字让AI改"、"边栏编辑"、"协同编辑" | 人机双写、协同创作、AI编辑、选区精调、腾讯文档编辑 | `references/12-faq.md`（人机双写 Q&A） |
| "老是答非所问"、"踩坑"、"常见误区" | 反模式、踩坑、答非所问、人设漂移 | `references/05-quick-cards.md`（卡片8） · `references/12-faq.md` 末尾踩坑 Q&A |
| "搜索知识库"、"找文档" | 搜索知识库、grep、关键词 | `scripts/quick-search.sh` |
| "第一次用"、"怎么上手"、"立规矩" | 新手、上手、立规矩、Soul.md | `references/05-quick-cards.md`（卡片7） |
| 🆕 "类似问题怎么处理"、"有案例吗"、"产品经理/运营/HR怎么用" | 场景案例、真实例子、用户原话、职场职能 | `references/06-scenario-examples.md` |
| 🔌 "知识库"、"IMA"、"资料归档"、"历史方案" | IMA知识库集成、知识沉淀、跨产品调用、回传 | `references/20-scenario-integrations.md`（案例19-20） |
| 🔗 "端到端流程"、"全自动流水线"、"多工具串联"、"闭环" | 端到端案例、跨工具闭环、全自动、流水线 | `references/20-scenario-integrations.md`（深度案例A/B/C） |
| 🆕 "怎么高效用"、"工作习惯"、"进阶技巧" | 工作空间、任务管理、探索复用、Claw远程 | `references/07-advanced-practice.md` |
| 📖 "MCP是什么"、"RRULE格式"、"SOP"、"术语" | 术语表、概念定义、Glossary | `references/08-glossary.md` |
| 📄 "腾讯文档"、"在线文档"、"产物分享"、"二维码分享" | 腾讯文档集成、资料库、上传云端、微信分享 | `references/20-scenario-integrations.md`（案例21-22） |
| 🆕 "怎么写提示词"、"AI总听不懂"、"交代任务"、"Prompt技巧" | 提示词、Prompt、任务交代、五要素 | `references/09-prompting-best-practices.md` |
| 🆕 "Ask和Craft什么区别"、"怎么切换模式"、"权限控制"、"小程序"、"助理" | 工作模式、交互、Ask/Plan/Craft、权限、通道 | `references/10-interaction-modes.md` |
| 🆕 "手机连电脑"、"多端同步"、"移动端远程"、"锁屏远程"、"远程停止任务"、"多设备切换" | 多端同步、远程遥控、锁屏远程、远程急停、双端协同 | `references/10-interaction-modes.md`（多端同步） |
| 🆕 "怎么让AI记住"、"记忆系统"、"跨会话记忆"、"Cloud Memory" | 记忆、Memories、画像、跨会话 | `references/11-memory-system.md` |
| 🆕 "用哪个模型"、"模型对比"、"模型倍率"、"Auto还是GLM" | 模型选择、Credit、倍率、模型对比 | `references/08-glossary.md`（模型章节） |
| 🆕 "安全吗"、"数据隐私"、"沙箱"、"VPC"、"企业安全" | 网络安全、数据保护、沙箱、合规 | `references/08-glossary.md`（网络安全章节） |
| 📖 "试过了还不行"、"文档没写"、"怎么都没解决" | 常见问答、FAQ、边界问题 | `references/12-faq.md` |
| 🆕 "团队协作"、"建项目"、"邀请成员"、"看板"、"任务流转"、"资产库" | Teams、项目、团队、协作、移交 | `references/13-teams-collaboration.md` |
| 🆕 "办公模式"、"开发模式"、"设计模式"、"场景切换"、"界面布局" | 场景模式、快捷方式、办公、开发、设计 | `references/14-scene-modes.md` |
| 🆕 "怎么连IMA知识库"、"ima引用文件"、"产物存回知识库" | IMA知识库、连接授权、引用、存回、解绑 | `references/16-ima-knowledge-base-guide.md` |
| 🆕 "腾讯会议"、"开会"、"会议纪要"、"会议录制"、"转写" | 腾讯会议Skill、Token、预约、转写、智能纪要 | `references/17-tencent-meeting-guide.md` |
| 🆕 "我是HR/开发/运营怎么用"、"按岗位推荐"、"新手选哪条路" | 角色路线、岗位上手、差异化入口 | `references/19-role-routes.md` |
| 📚 "资料库"、"团队空间"、"我的文档"、"三种载体"、"MD CSV HTML联动"、"本地HTML发链接"、"轻应用" | 资料库、团队空间、三种载体、轻量发布、人机修订 | `references/21-ziliaoku-guide.md` |
| 🎨 "设计创意"、"Ardot"、"一句话生成UI"、"PPT设计"、"海报"、"设计稿转代码"、"画布精修" | 设计创意、Ardot、对话生成、精修、生成应用代码 | `references/22-design-creative-guide.md` |
| 💡 "灵感"、"一键做同款"、"制作我的版本"、"做同款"、"套版复刻"、"七大场景" | 灵感、成品库、一键做同款、自动就位 | `references/23-inspiration-guide.md` |
