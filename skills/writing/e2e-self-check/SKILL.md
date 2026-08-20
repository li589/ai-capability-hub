---
name: e2e-self-check
description: 研发自检 Agent——以独立视角（不共享编码会话上下文）对需求变更做多角色质检，产出 check_reports/（check.summary.md + 主链路报告 + 产品/研发/安全SRE 视角报告）。当用户要求"自检"、"跑检查报告"、"生成 check_reports"、需求编码完成进入检查阶段、或 /e2e-flow 进入阶段五时使用。
version: 2.0.0
install_source: official
install_method: download
skill_id: a9957ba4-ef22-480d-b7ae-a7f79d77a878
enabled_at: 1787231423386
name_zh: e2e-self-check 研发自检 Agent
---

# e2e-self-check：研发自检 Agent

把编码产出交给"第二双眼"检查。核心设计原则（来自端到端交付宪法第 III 条）：
**自检必须以独立视角执行**——检查者不知道编码 Agent 当时为什么这么写，只依据
diff、spec、plan、规则做判断，避免"厨师给自己的菜打分"的确认偏差。

## 触发方式

- `/e2e-self-check <specDir>` —— 对指定 spec 目录对应的变更做自检
- `/e2e-self-check <specDir> --range <git引用范围>` —— 显式指定 diff 范围（如 `main..HEAD`、`abc123..def456`）
- `/e2e-self-check <specDir> --scope <代码目录>` —— 显式指定被检代码所在仓库目录（多项目仓库时用）
- `/e2e-self-check <specDir> --deep` —— 强制开启深度影响面分析（默认 standard 级自动开启）

## 边界声明

- 只产出检查报告，不修改业务代码；发现问题列出证据，修复由用户或编码会话决定
- overall_result 为 FAIL 时必须在汇报中明确说明"禁止提测"（宪法第 III 条）
- 不执行 git commit / push
- 检查过程中可读取仓库内任何文件以理解上下文，但不得修改

## 执行流程

### 第 1 步：读取 spec 上下文

1. 读取 `{specDir}/spec.md`：提取 FR 功能需求、SC 成功标准、User Story 的验收场景、`Level` 分级
2. 读取 `{specDir}/plan.md`：提取模块划分、主流程设计、接口定义
3. 若 spec.md / plan.md 缺失 → 终止并提示先走 `/e2e-flow` 补齐前置产出物

### 第 2 步：确定检查范围（diff）

1. 用户指定了 `--range` 则用之；否则默认 `git diff main...HEAD`（当前分支相对 main 的全部变更）
2. 变更为空时检查是否有未提交改动（`git diff HEAD` + untracked），仍为空则终止提示"无变更可检"
3. 确定代码范围：优先用 `--scope`；否则从 diff 文件路径自动推断（本仓库为多项目结构，
   后端在 `backend-project/busyming-mcp-market/`，前端在 `fe-project/mcp-market-fe-project/`）
4. 记录待检文件清单与变更行数，若单次 diff 超过约 3000 行，按模块拆分为多轮检查（见第 5 步）

### 第 3 步：影响面分析（深度上下文）

**目标：不只看 diff 本身，还要找出"没改但受影响"的代码。**

本步骤通过直接读取本地代码仓库实现全量代码访问，无需远程 API：

1. **提取变更符号**：从 diff 中识别所有新增/修改/删除的公共方法签名、接口定义、常量
2. **追溯调用方（Callers）**：
   - 使用 Grep/Search 在整个项目中搜索变更方法的调用点
   - 重点关注：Facade 接口方法签名变更 → 所有调用该 Facade 的消费方
   - 重点关注：Service 接口新增/修改参数 → 所有实现类和调用类
3. **追溯被调用方（Callees）**：
   - 变更方法内部调用的其他方法，读取其完整实现确认语义兼容性
   - 特别是 Mapper 方法 → 对应 XML SQL 是否匹配新参数
4. **数据模型影响**：
   - Entity 字段变更 → 关联的 Request/Response/Convert 是否同步更新
   - 数据库 DDL 变更 → Mapper XML、Entity `@TableField` 是否一致
5. **跨模块影响**：
   - api 模块变更 → service/web/mq/job 中引用该 api 的代码
   - MQ Message 结构变更 → Producer 和 Consumer 是否同步

**产出**：`impact_files` 清单（变更文件 + 受影响文件），标注影响类型（caller/callee/model-sync/cross-module）

### 第 4 步：启动独立视角检查（关键）

**必须通过子代理执行检查，不得在当前编码会话中直接自查。**

- 优先使用 **CodeReview 子代理**（自带高信噪比缺陷识别）做研发视角检查
- 用 **GeneralPurpose/Search 子代理**做产品视角（FR/SC 覆盖比对）与安全SRE视角检查
- 喂给子代理的输入**允许**：
  - diff 内容/范围
  - spec.md、plan.md
  - `.qoder/rules/` 规则、code-standards 技能中的规范（后端）或 fe-code-standards（前端）
  - 宪法文件
  - **第 3 步产出的 `impact_files` 清单**（告知子代理哪些未变更文件需要一并审查）
  - **指令：子代理可以且应该读取 `impact_files` 中列出的完整文件**，用于验证兼容性
- **禁止**把本会话中编码时的思考过程、决策理由透传给子代理

### 第 5 步：分层检查策略（控制上下文量）

先主链路，后分治（宪法引用的"先确认主干逻辑，再分而治之"）：

1. **主链路检查**（强制）：端到端走一遍核心用户故事——请求入口 → 服务层 → 数据层 → 返回，
   比对 spec 的 P1 User Story 是否完整实现，主流程是否与 plan.md 一致。
   **必须读取主链路涉及的完整文件**（不只看 diff 行），验证调用链完整性
2. **模块分治**（standard 级）：主链路通过后，按 plan.md 的模块划分逐个检查细节；
   每轮子代理只检查一个模块的 diff + 该模块 `impact_files`，避免上下文过载
3. **simple 级简化**：只做主链路检查 + 单测执行结果，跳过多视角扩展报告

### 第 6 步：三视角检查维度

| 视角 | 检查内容 |
|------|----------|
| **产品视角** | spec 的 FR/SC 是否全部覆盖；User Story 的 Given-When-Then 验收场景是否都被实现；有无遗漏功能点 |
| **研发视角** | 架构是否符合 `.qoder/rules/backend-coding-convention.md`（分层/命名/依赖方向）；编码规范问题；逻辑矛盾；TODO 遗留；注释掉的死代码；单测覆盖；**调用链兼容性**（impact_files 中的 caller 是否因参数/返回值变更而需要同步修改） |
| **安全SRE视角** | 上下游接口变更影响（**结合 impact_files 验证所有消费方是否适配**）；新增接口参数校验；数据库变更向后兼容（含 RULE-8 建表规范）；日志规范与敏感信息脱敏（BAN-9/BAN-14）；可运维性（日志/回滚） |

**每个问题必须带证据**：文件路径 + 行号 + 违反的规则编号（如 `RULE-3.4.1`、`BAN-6`），
以及问题级别：`BLOCKER`（阻塞）/ `MAJOR`（重要）/ `MINOR`（建议）。

**影响面相关问题额外标注**：`[IMPACT]` 前缀，说明"A 文件变更导致 B 文件需要同步修改但未修改"。

### 第 7 步：产出报告

写入 `{specDir}/check_reports/`，模板见本技能 `assets/` 目录：

| 文件 | 必须性 | 模板 |
|------|--------|------|
| `check.summary.md` | 必须 | `assets/check-summary-template.md` |
| `00-main-chain-report.md` | 强制 | `assets/main-chain-template.md` |
| `01-product-view.md` | standard 级必须 | `assets/role-view-template.md` |
| `02-dev-view.md` | standard 级必须 | `assets/role-view-template.md` |
| `03-security-sre-view.md` | standard 级必须 | `assets/role-view-template.md` |
| `04-impact-analysis.md` | standard 级必须 | `assets/impact-analysis-template.md` |

`overall_result` 判定规则：

- **PASS**：无 BLOCKER 且无 MAJOR → 可进入下一阶段
- **CONDITIONAL_PASS**：无 BLOCKER 但有 MAJOR → 修复后可继续，无需重新全量自检
- **FAIL**：存在 BLOCKER → 必须修复后重新自检，禁止提测

### 第 8 步：结果汇报

向用户汇报：overall_result、各视角问题数（BLOCKER/MAJOR/MINOR）、影响面发现数、
Top 问题清单（带证据）、报告文件路径。FAIL 时明确说明阻塞项与建议的修复顺序。

---

## 云效 MCP 集成（可选增强）

当本地配置了云效 MCP（`yunxiao` server）时，可利用以下工具增强检查能力：

| MCP 工具 | 用途 |
|----------|------|
| `compare` | 获取两个分支/commit 之间的结构化 diff（含文件列表和变更统计） |
| `get_file_blobs` | 读取远程仓库中指定路径的文件内容（用于对比 main 分支的原始版本） |
| `list_commits` | 查看提交历史，辅助理解变更时间线 |

**使用场景**：
- 本地代码未拉取最新 main 时，通过 MCP 获取 main 分支文件作为对比基准
- 需要确认某文件在 main 上的原始内容以判断是否为新引入问题
- 跨仓库依赖检查（如其他服务的 api 模块是否有兼容性变更）

**注意**：本地文件系统已包含全量代码时，优先使用 Read/Grep 直接读取，MCP 仅作补充。
