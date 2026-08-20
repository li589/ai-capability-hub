---
name: loop_engineering
description: 通过交互式问答帮用户为代码项目快速创建一套可执行的 Loop Engineering 工作目录(GOAL/RULES/STATE/PROMPT 四件套 + 启动器)。当用户说"帮我创建 LOOP""做一个 Loop Engineering 任务""我想用 LOOP 修这个 bug""为这个项目搭一个循环工程""把 XX 任务做成 loop 自动跑"等表达时触发。仅适用于代码项目(支持 Python/Node/Java/Go/前端等任何能在命令行验证的语言)。
install_source: official
install_method: download
skill_id: official_IoT8W7v5
enabled_at: 1787232747854
version: 1.0.0
name_zh: 工程LOOP
---

# Loop Engineering Skill — 帮用户造一个能自己转的 LOOP

## 这个 skill 解决什么问题

Loop Engineering 是 2026 年 6 月被 Boris Cherny / Addy Osmani 推火的 AI 工程范式:
**人不再一轮一轮指挥 Agent,而是设计一个让 Agent 自我驱动的闭环系统。**

但这个概念非常抽象,普通用户即便读了文档也不知道**第一行字写在哪个文件、第一个命令怎么发**。

这个 skill 的作用是:**通过一段 5~10 分钟的交互问答,为用户的具体代码项目落地出一套真实可跑的 LOOP 工作目录**。
产物是用户可以"双击启动 → 复制粘贴给 Agent → LOOP 自己转起来"的真实文件。

---

## 触发条件(什么时候应该用这个 skill)

明确触发:

- 用户说"帮我创建 LOOP""搭一个 loop""做循环工程""设计一个 Loop Engineering 任务"
- 用户说"我想让 AI 自动修复 XX bug""我想让 AI 持续跟进 XX 任务"
- 
- 用户已经读过 Loop Engineering 文档,询问"我怎么开始?"

不要触发:

- 用户只是要修一个具体的 bug → 直接帮他修,不要把简单事情包装成 LOOP
- 用户的项目不是代码项目(纯写作、运营、设计) → 告诉用户"当前 skill 仅支持代码项目"
- 用户只是想了解 Loop Engineering 概念 → 解释概念即可,不要主动启动 skill

---

## 工作流程(Agent 必须严格按这 7 步执行)

### 步骤 1:确认用户意图

加载 skill 后,先用一句话向用户确认:

> 我会通过几个问题了解你的项目,然后为你生成一套完整的 LOOP 工作目录(包含目标定义、规则约束、持久记忆、启动咒语 4 个文件,以及一键启动脚本)。生成后你可以直接拿去跑。
> 
> 整个过程大约 5~10 分钟。准备好开始吗?

得到确认后再进入步骤 2。如果用户说"先解释一下 Loop Engineering 是什么",先简短解释(2~3 句话),再问是否开始。

### 步骤 2:交互式问答(7 个核心问题)

按 `references/INTERVIEW.md` 中给出的 7 个问题清单**逐个**问用户。

**关键纪律**:

- 每次只问 1~2 个相关问题,不要一次抛 7 个问题给用户
- 如果用户给的答案太模糊,**追问到能写进模板为止**(例如用户说"修复 bug",必须追问到"哪个 bug?报错信息是什么?")
- 用户答完一个问题,**立刻在内部草稿里记录**,不要等到最后才汇总
- 如果用户提供了项目路径,**立刻用 read/glob/grep 工具去看一下项目结构**,这样后续问题可以基于真实信息精准化(例如:"我看到你项目里有 package.json,所以测试命令应该是 npm test 还是 pnpm test?")

### 步骤 3:任务类型判定 + LOOP 模式选择

根据用户回答,从 `references/PATTERNS.md` 五种 LOOP 模式中选一种:

- 测试驱动 Loop(修 bug、回归测试、数据转换)
- 编译器驱动 Loop(类型迁移、依赖升级、重构)
- Review 驱动 Loop(PR 跟进、代码审查)
- 运行时调试 Loop(生产 bug、性能问题)
- 产品迭代 Loop(UI 调整、营销组件)

判定逻辑:

- 用户的"成功条件"能用一条命令的退出码判断 → 优先 测试驱动 / 编译器驱动
- 没有自动测试,但有可观察的运行时行为 → 运行时调试
- 是 GUI/UI/视觉类任务 → 产品迭代,且必须设计"人工验收"环节
- 不能确定 → 默认用测试驱动并告诉用户为什么选它

把选择结果告诉用户,简短解释为什么选这个模式,问用户认不认同。

### 步骤 4:生成工作目录

- 默认生成位置:`workspace/loops/<任务短名>/`(如果用户指定了别的路径就用用户的)
- 创建该目录,从 `templates/` 复制以下 5 个文件并替换变量:
  - `GOAL.md`(由 `templates/GOAL.template.md` 生成)
  - `RULES.md`(由 `templates/RULES.template.md` 生成)
  - `STATE.md`(由 `templates/STATE.template.md` 生成)
  - `PROMPT.md`(由 `templates/PROMPT.template.md` 生成)
  - `start-loop.bat`(由 `templates/start-loop.template.bat` 生成)

变量替换清单(模板中所有 `{{VAR}}` 占位符必须全部替换,共 20 个):

**基础信息(7 个,从用户问答+项目探查得到)**

- `{{TASK_NAME}}` 任务短名(英文小写,只用于目录命名,例如 `fix-auth-tests`)
- `{{TASK_TITLE}}` 任务的中文标题(出现在文件标题和启动器界面)
- `{{PROJECT_PATH}}` 项目绝对路径
- `{{PROJECT_LANG}}` 技术栈(如 "Python 3.11 + PyQt6")
- `{{PROBLEM_DESC}}` 用户描述的真实问题(完整段落)
- `{{LOOP_DIR}}` LOOP 工作目录绝对路径
- `{{LOOP_PATTERN}}` 选定的 LOOP 模式(从 references/PATTERNS.md 五种之一)

**命令清单(3 个)**

- `{{INSTALL_CMD}}` 依赖安装命令(如 `pip install -r requirements.txt`)
- `{{VERIFY_CMD}}` 核心验收命令(如 `pytest` / `npm test`),决定 LOOP 成功信号
- `{{EXTRA_COMMANDS}}` 辅助命令(类型检查、lint 等),没有则填注释 `# (本项目无额外命令)`

**预算控制(2 个)**

- `{{ROUNDS_BUDGET}}` 轮数预算(默认 15,简单任务给 5~10,复杂任务给 20)
- `{{FILES_PER_ROUND}}` 单轮文件改动上限(默认 5)

**验收方式开关(2 个)**

- `{{HAS_AUTO_TEST}}` 是否有自动化测试,值为 `yes` 或 `no`
- `{{HUMAN_REVIEW_NEEDED}}` 是否需要人工验收,值为 `yes` 或 `no`(GUI/UI 项目必须 yes,无自动测试也必须 yes)

**条件展开块(6 个,Agent 根据上下文展开成完整段落,而不是替换成短词)**

- `{{EXTRA_HARD_CRITERIA}}` 额外的自动验收条目,markdown 列表形式,每行 `- [ ] xxx`
- `{{HUMAN_REVIEW_CHECKLIST}}` 人工验收清单,如果 HUMAN_REVIEW_NEEDED=no 则填 `(本任务无需人工验收)`,否则展开为 markdown 列表
- `{{FORBIDDEN_PATHS_LIST}}` GOAL.md 第四节用的禁区清单(简短列表)
- `{{FORBIDDEN_DETAILS}}` RULES.md 第四节用的禁区详细说明(每条带 🚫 emoji 和理由)
- `{{CORE_CONVENTIONS}}` 项目核心约定(从用户回答+代码观察总结)
- `{{CRITICAL_NOTES}}` 项目踩过的坑(从用户回答+代码观察总结)
- `{{EXTRA_GRAY_AREA}}` 项目特有的灰色地带,没有则填 `(本项目无额外灰色地带)`

**生成时的纪律**:

- 替换前 grep 一次确认所有 `{{VAR}}` 都在上面清单里
- 替换后再 grep 一次确认输出文件里**没有任何**残留的 `{{` 字符串
- 任何无法确定的字段,宁可填 `[请确认: 你的XXX]` 让用户补,也不要凭空编

### 步骤 5:写一份"差异说明"给用户

生成完毕后,**不要直接说"好了"**。要做三件事:

1. 用一段话告诉用户每个文件是什么(对应 LOOP 六大要素的哪一个)
2. 列出"我自动给你做的判断",哪些可能需要用户复核(例如"我把 migrations/ 加进了禁区,因为我猜你不想让 AI 改数据库迁移,如果不对告诉我")
3. 给出"立即可执行的下一步指令"(具体到双击哪个文件 / 复制哪段话 / 粘贴到哪)

### 步骤 6:首轮预演(可选但强烈推荐)

询问用户:"要不要我现在就**模拟跑一轮 LOOP** 看看效果?(我会按 PROMPT.md 的流程做诊断+设计,不会真改代码,你看完再决定要不要正式启动。)"

如果用户同意,执行一次"只读模式"的首轮:

- 读 GOAL/RULES/STATE
- 探查项目结构,产出对该项目的诊断分析
- 在 STATE.md 的"设计决策记录"区写下首轮发现
- 把状态从 `[INIT]` 改为 `[RUNNING]`
- 提出第一个改造方案的草案,等用户拍板

### 步骤 7:交付清单

最后给用户一份简短的"操作指引":

- 在哪个目录:`{{LOOP_DIR}}`
- 怎么启动:双击 `start-loop.bat`,或直接对 OpenCode 说"按 {{LOOP_DIR}}\PROMPT.md 跑一轮 LOOP"
- 每天看哪个文件:`STATE.md`(顶部的状态标记 + 运行日志)
- 什么时候人工介入:状态变成 `[STUCK]/[BLOCKED]/[NEEDS_HUMAN_REVIEW]` 时

---

## 资源文件

加载本 skill 后,Agent 还应当在需要时读取:

- **`references/INTERVIEW.md`** —— 7 个核心问题的完整清单和每个问题的"如何追问"指引
- **`references/PATTERNS.md`** —— 五种 LOOP 模式的详细对比 + 选择决策树
- **`references/PHILOSOPHY.md`** —— Loop Engineering 核心理念(给需要解释概念时用)
- **`templates/`** —— 5 个文件模板(`GOAL/RULES/STATE/PROMPT.template.md` + `start-loop.template.bat`)

---

## 设计纪律(Agent 必须遵守)

1. ❌ **不要凭空生成假数据填模板**—— 任何变量,要么用户给了答案,要么 Agent 从项目里查到了证据,要么明确标注 `[请确认]` 让用户检查。绝不编造。
2. ❌ **不要省略问答直接生成**—— 即便用户提供了一句话需求,也至少要问 3~4 个澄清问题。LOOP 的质量 80% 取决于 GOAL 和 RULES 写得多具体。
3. ❌ **不要生成"完美但没人改的"模板**—— 最好的模板是"用户能一眼看懂、能自己接着改"的,不是看起来高大上的。
4. ❌ **不要把 skill 当文档讲**—— 用户来用 skill 是要造东西,不是听课。能少说就少说,能问问题就别讲概念。
5. ✅ **大胆假设、小心确认**—— 自动从项目代码里推断信息(测试命令、依赖、禁区),但每个推断都要在交付清单里告诉用户"我猜的,你看对不对"。
6. ✅ **跑通比完美重要**—— 首版 LOOP 文件即便有几处需要用户调整也没关系,目标是让用户**今天**就能跑起来,而不是给一份永远在改的草稿。

---

## 验证 skill 是否成功的标准

用户跑完这个 skill 后,应当满足:

1. `workspace/loops/<任务名>/` 目录下有 5 个文件,所有 `{{VAR}}` 占位符都已替换
2. 用户立即可以双击 `start-loop.bat` 或粘贴 PROMPT.md 启动第一轮
3. 用户看完输出后能用一句话说清楚"我的 LOOP 是干什么的、我下一步要做什么"
4. 用户**不需要再回来问**"那 GOAL.md 是干嘛的"——交付清单里都写清楚了
