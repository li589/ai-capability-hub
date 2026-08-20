# CHANGELOG — recruitment-expert-paid

## v4.1.0 (2026-07-25)

### Minor — Step-05 拆分 + SKILL.md 重构 + 检查点扩展

**背景**：step-05-interview-assessment.md 原 1005 行，包含 6 个独立辅助工具（评价表/十步法/BEI 题本/高管题库/沟通全景图/补充方法论）。单一文件难以按需加载，且 SKILL.md 缺少路由决策矩阵、依赖声明和错误处理策略。

#### 变更清单

##### P0 — step-05 辅助工具拆分为 6 个子文件
- `step-05-interview-assessment.md`：保留道/法/术/任务清单/关键输出核心内容（~80 行），替换为路由表指向辅助文件
- `step-05-aux/interview-evaluation-form.md`：按职级分层的标准化面试评价表
- `step-05-aux/interview-ten-steps.md`：结构化证据采集十步法
- `step-05-aux/bei-question-bank.md`：BEI 行为事件访谈题库（两套）
- `step-05-aux/executive-question-matrix.md`：高管面试能力矩阵题库
- `step-05-aux/candidate-communication.md`：4 阶段 × 23 场景沟通战术全景图
- `step-05-aux/supplementary-methods.md`：JD/简历 AI 解析 + 法律红线扫描 + 岗位适配
- 按需加载策略：日常面试仅 ~4KB，全链路操作全套 ~50KB

##### P0 — SKILL.md 路由表合并 + 添加目录/依赖区块
- 新增「目录」区块：完整内部锚点导航
- 合并「快速导航」+「适用场景」为「路由决策矩阵」：增加「输入信号 → 目标步骤 → 置信度」列
- 新增「依赖」区块：声明 weixinpay 插件 + screen.py 可选工具
- 添加「HTTP 请求错误处理」区块：try-catch 超时处理（30s）、4xx/5xx/timeout 分类响应
- 添加「SOUL.md 加载失败回退」策略：内置精简人设
- 修正「步骤文件最大不超过 600 行」为 「step-05 含 6 个辅助子文件，按需加载后主路由文件约 80 行」
- 更新步骤 5 文件引用路径，指向 `step-05-aux/` 下的新文件

##### P1 — 新增检查点 4 个（步骤 3/5/6/7）
- **检查点 2**（步骤 3）：渠道策略确认后 → 进入简历筛选
- **检查点 3**（步骤 5）：面试评估结论确认后 → 进入薪酬谈判
- **检查点 4**（步骤 6）：薪酬方案确认后 → 进入背景调查
- **检查点 5**（步骤 7）：背调结论确认后 → 进入 Offer
- 原检查点 1/2 重新编号为检查点 1/6

##### P2 — frontmatter 重构
- description 以 "Use when" 开头
- tags 精简到 8 个：recruitment, hiring, talent-acquisition, hr, payment, x402, interview, resume-screening
- version 更新为 "4.1.0"

##### P2 — step-04 僵尸引用修正
- `screen.py`/`screening_result.json`/`screening_report.html` 引用前添加可选工具说明

##### P2 — SOUL.md 步骤 5 路径更新
- 辅助工具引用从「步骤 5-6 文件内嵌」更新为 `step-05-aux/` 独立文件路径

### 兼容性

- 向后兼容：所有原有方法论内容完整保留，仅改变文件组织结构和路由方式
- SOUL.md 人设和交互脚本核心内容保持不变
- 支付流程（X402）未修改

### Major — 架构重组：God Skill 拆分 + 结构化标准化

**背景**：原始版本 WORKFLOW.md 达 2020 行/170KB，超出 skills-optimization-pro 定义的 God Skill 阈值（>500 行）4 倍。执行该优化将 2020 行的单体文件拆分为 9 个独立步骤文件 + 6 个辅助文件，并添加完整的 frontmatter、版本管理体系、检查点和降级策略。

### 变更清单

#### P0 — AP-1 拆分 WORKFLOW.md
- 原 2020 行 WORKFLOW.md 拆分为 15 个文件
- `references/steps/step-01~09-*.md`：每个步骤独立文件（平均 ~250 行，最大 600 行）
- `references/quick-cards.md`：9 张快速作战卡
- `references/scene-routing.md`：场景路由表 + 用户角色判定
- `references/flow-overview.md`：流程总览（含流程启动指南）
- `references/anti-patterns.md`：8 大反模式自检清单
- `references/appendix-data-metrics.md`：数据指标体系
- `references/appendix-compliance.md`：劳动法与合规实操速查

#### P0 — YAML frontmatter 结构化
- 添加完整的 YAML frontmatter：name、version、description、author、tags、metadata
- description 包含 "Use when" 规范的触发场景说明
- 17 个触发词从扁平列表升级为语义化 metadata.triggers

#### P1 — AP-5 添加检查点
- **检查点 1**：需求诊断完成后 → 展示结论 → 用户确认 → 方可进入步骤 2
- **检查点 2**：Offer 发放前 → 展示生效条件清单 + 承诺阶梯 → 用户确认 → 方可发送

#### P1 — AP-3 降级策略
- WORKFLOW 分块加载降级：目标文件不可达 → 回退到 quick-cards.md 精简响应
- weixinpay 插件缺失降级：三步引导文案（安装插件 → 重新发起 → 公开概览）

#### P2 — AP-6 消除矛盾 + 步骤统一
- 将原 11 项核心任务清单统一为 10 步骤（反模式自检 + 终局飞轮合并到各步骤自检中）
- 章节标题、路由表、快速作战卡全部对齐为 10 步骤体系
- SKILL.md 快速导航表 + 适用场景表 统一编号

#### P2 — 版本管理体系
- 添加 CHANGELOG.md，起始版本号 v4.0.0（对应架构重组升级）
- SKILL.md 中标注 version: "4.0.0"

### 文件统计

| 文件 | 大小 |
|------|------|
| SKILL.md (入口) | ~6.2 KB |
| SOUL.md | ~14.7 KB（保持不变）|
| 9 个步骤文件 (references/steps/) | ~200 KB 合计 |
| 6 个辅助文件 (references/) | ~23 KB 合计 |
| CHANGELOG.md | 本文件 |

### 兼容性

- 向后兼容：所有原有方法论内容完整保留，仅改变文件组织结构
- SOUL.md 路径引用已更新
- 支付流程（X402）未修改

---

## v4.1.1 (2026-07-25)

### Patch — 检查点嵌入式补全 + 加载顺序约束

**背景**：SKILL.md 中心化定义了 6 个检查点闸门，但步骤 3/6/7 文件内未嵌入闸门副本。Agent 按路由矩阵直接加载步骤文件时可能跳过闸门（尤其高置信度场景：步骤 3 85%、步骤 6 90%、步骤 7 85%）。

#### 变更
- `step-03-channel-strategy.md`：末尾嵌入检查点闸门（渠道策略 → 简历筛选）
- `step-06-salary-negotiation.md`：末尾嵌入检查点闸门（薪酬方案 → 背景调查）
- `step-07-background-check.md`：末尾嵌入检查点闸门（背调结论 → 录用通知）
- `SKILL.md`：检查点区块添加"加载顺序约束"规则

#### 影响
- 检查点覆盖率：嵌入式 6/6 ✅（原 3/6 → 6/6）
- 双保险：SKILL.md 路由矩阵 + 步骤文件嵌入式闸门，任一路径均触发

---

## v4.1.2 (2026-07-25)

### Patch — 补全输出模板 + 路由扩展

**背景**：v4.1.1 10 步链路压测发现 3 个 P1 改善点：（1）步骤 2 无结构化输出模板 → 画像产出不一致 （2）步骤 4 缺候选人对比矩阵 → 多候选决策展示不规范 （3）candidate-communication.md 未入路由矩阵 → 候选人沟通类问题精准路由失效。

#### 变更
- `step-02-talent-portrait.md`：末尾新增"关键输出"模板（11 字段，8 必填）
- `step-04-resume-screening.md`：末尾新增候选人对比矩阵（5 维度加权评分 + 🔴🟡🟢 裁决规则）
- `SKILL.md`：路由决策矩阵新增"候选人沟通战术"行（→ `candidate-communication.md`，置信度 85%）
- `SKILL.md`：快速导航表新增"候选人犹豫/沟通跟进"条目

#### 影响
- 步骤 2 输出标准化：8 必填字段保证画像完整一致
- 步骤 4 多候选对比：加权评分 + 证据锚点，决策可追溯
- 路由覆盖率：步骤 1-9 + 反模式 + 合规 + 候选沟通 → 12 条路由全精准匹配

---

## v4.1.3 (2026-07-25)

### Patch — 降级韧性加固

**背景**：v4.1.2 异常路径专项测试（5 场景）发现 2 个 P2 改善点：（1）anti-patterns / appendix-compliance / scene-routing 三个非步骤文件缺少快速卡备份 （2）step-05 辅助子文件加载失败时未通知用户降级详情。

#### 变更
- `quick-cards.md`：新增卡 10（反模式自检）、卡 11（合规速查）、卡 12（场景路由）——覆盖全部 12 个 references 文件
- `SKILL.md`：降级策略新增"step-05 辅助子文件加载失败"条目，强制通知用户哪些模块缺失、用何替代

#### 影响
- 快速卡覆盖率：9/12 → 12/12（全文件有降级备份）
- 子文件加载失败从静默降级升级为显式通知
- 降级韧性：正常路径（v4.1.2 压测 10/10）+ 异常路径（v4.1.3 压测 5/5）→ 全路径覆盖

---

## v4.1.4 (2026-07-25)

### Patch — 编码修复

**背景**：`appendix-compliance.md` 在 WORKFLOW.md 拆分（extract.ps1）阶段引入三重编码污染（GBK→Latin-1→UTF-8 错误链），原始文件已不可恢复。文件内容全部为乱码，7 项合规内容不可读。

#### 变更
- `appendix-compliance.md`：完全重建，基于中国劳动法规重写为干净 UTF-8（3017 字符，7 章节），覆盖：①试用期合规 ②竞业限制合规 ③五险一金缴纳 ④Offer 撤回法律风险 ⑤离职补偿计算 ⑥招聘歧视红线 ⑦Offer 核心条款清单
