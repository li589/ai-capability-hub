---
name: blueprint-report-generator
display_name: eMES 蓝图规划助手
display_name_en: eMES Blueprint Generator
description: Generate a customer-specific blueprint planning PPT (22-28 pages) from survey/implementation reports, covering scope, transparency, acceptance, main & sub processes, gaps, benefits, risks, next steps.
description_zh: 基于调研报告/实施报告/售前方案生成客户专属蓝图规划 PPT（22-28 页），覆盖范围界定、8大透明、验收条件、主流程、核心子流程、差异、效益、风险、下阶段工作九大重点。
description_en: Generate a customer-specific blueprint planning PPT (22-28 pages) from survey/implementation reports, covering scope, transparency, acceptance, main & sub processes, gaps, benefits, risks, next steps.
category: writing
version: 1.0.0
author: "Digihua"
trigger:
  - 蓝图
  - 蓝图规划
  - 蓝图报告
  - 蓝图设计
  - 蓝图汇报
  - 实施蓝图
  - eMES蓝图
  - 蓝图与设计
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
---
# 智能交付 · 蓝图报告生成器（智能交付助手-蓝图助手）

> 智能交付系列「蓝图与设计」阶段的核心交付物——基于前期调研报告与实施报告，生成签字后即锁实施范围与目标的蓝图规划 PPT。
> **设计基准**：动量守恒绿色能源 23 页交付件（2026.08）；方法论核心来源于客户A/客户B/宇牌三项目四件套 + 上海汽车空调/福士/万卡信/新泉模具四份参考��图。

## 1. 与现有 skill 的关系

```
smart-delivery-survey     → 智能交付助手-蓝图助手 → (进入实施)
  ┌─────────────┐             ┌─────────────┐
  │ ①问卷生成    │             │ 蓝图规划报告  │
  │ ②调研报告    │ ────────▶   │ (本skill)    │
  │ ③实施流程规划 │             └─────────────┘
  └─────────────┘
       输入                      输出
   调研报告.doc                  蓝图规划PPT
   会议纪要.docx                 22-28 页
   服务记录单
   实施报告.docx(可选)
   售前方案.pptx(可选)
```

> 本 skill 直接消费 `smart-delivery-survey` 阶段②/③的成果（调研报告 + 实施流程规划），并可独立调用——只要给一份客户调研报告即可启动。

## 2. 输入材料

| 必填 | 材料 | 用途 |
|:-:|:-|:-|
| ✓ | 客户调研报告（.doc/.docx） | 业务现状、各部门难点、生产模式 |
| ✓ | 实施报告/会议纪要/服务记录单（如有） | 实施团队草拟的蓝图草案 |
| ✓ | eMES 操作手册截图素材库 | 嵌入"操作流程截图"章节 |

| 选填 | 材料 | 用途 |
|:-:|:-|:-|
| ○ | 售前方案 PPT | 沿用管理目标、阶段规划、预期效益口径 |
| ○ | 标准工具目录 `{{DOCS_PATH}} | 操作流程图六列（WHAT/HOW/WHEN/WHO/WHERE/Gain） |

> 操作手册素材库标准化路径：`C:\Users\Asus\WorkBuddy\<项目>\蓝图分析\操作手册素材库\raw\`
> （按模块 19 个目录组织，含 108 份手册 835 张界面截图，详见 `references/screenshot_library.md`）

## 3. 输出

**主交付件**：`<客户>eMES蓝图规划报告V1.pptx`（22-28 页，签字版交付）

| 文件类型 | 用途 |
|:-|:-|
| `V1.pptx` | 蓝图汇报主件（幻灯片） |
| `V1_操作流程界面补充页.pptx`（可选） | 操作截图单独补充件，用于跨客户端合并 |

**章节框架（22-28 页标准结构，动量守恒交付件为基准）**：

| # | 章节 | 页数 | role |
|:-:|:-|:-:|:-:|
| 1 | 封面 | 1 | hero |
| 2 | 报告大纲 | 1 | supporting |
| 3 | 1.1 项目背景·企业概况 | 1 | supporting |
| 4 | 1.2 项目进度·实施主计划 | 1 | transition |
| 5 | 2.1 项目范围界定 | 1 | supporting |
| 6 | 2.1 实施目标·8 大透明 | 1 | hero |
| 7 | 2.1 验收条件 | 1 | supporting |
| 8 | 2.2 主流程总览（9 节点） | 1 | hero |
| 9 | 2.2 跨系统集成规划 | 1 | supporting |
| 10 | 2.2 工单→派工→报工映射矩阵 | 1 | supporting |
| 11 | 2.2 一期数采设备清单 | 1 | transition |
| 12 | 2.3 工艺路线主流程 ① | 1 | supporting |
| 13 | 2.3 工艺路线主流程 ② | 1 | supporting |
| 14 | 2.3 工艺路线主流程 ③ + ④ | 1 | supporting |
| 15 | 2.4 核心子流程·派工/报工/质量/设备 | 1 | transition |
| 16 | 2.4 核心子流程·模具/上料/装箱/委外 | 1 | supporting |
| 17 | 2.5 报工点位规划 | 1 | supporting |
| 18 | 2.6 关键性差异说明（个案清单） | 1 | supporting |
| 19 | 2.7 效益概述 As Is → To Be | 1 | hero |
| 20 | 3.1 风险预警表 | 1 | supporting |
| 21 | 3.2 下阶段工作 | 1 | transition |
| 22 | 签字页 | 1 | transition |
| 23 | Thank You | 1 | hero |

## 4. 核心方法论（与 `references/blueprint_framework.md` 配套使用）

### 4.1 三大要点（不可遗漏）

- **进度对齐**：本期蓝图所有工作节点必须与 eMES 实施主计划同步，标 "I am here!"
- **范围界定**：物理区域 + 涉及产品系列 + 本次上线 eMES 模块（含暂缓项）
- **验收条件**：围绕 8 大透明列四类依据（报表/看板/无纸化覆盖/数采指标）

### 4.2 三者关联性

| 来源 | 回答的问题 | 在蓝图中的章节 |
|:-|:-|:-|
| 售前方案 | 为什么做？价值主张 | 1.1 背景 + 2.7 效益 |
| 调研报告 | 现状是什么？各部门怎么干活？ | 2.2/2.3/2.4 流程设计 |
| 蓝图报告 | 未来怎么做？怎么验收？ | 全文 |

**核心规律**：蓝图不产生新事实，只做"翻译"（现状→目标流程）和"补全"（售前没细化的内容）。

### 4.3 八大透明

派工透明 / 进度透明 / 设备透明 / 质量透明 / 人员透明 / 资料透明 / 不良透明 / 产能透明

每个本期目标透明 → 四类验收依据：①报表/看板 ②无纸化覆盖 ③数采指标 ④（如需）其他 KPI

### 4.4 个案/二开内容

调研"业务重点难点"中客户特殊诉求 → 固化为 2.6 关键差异说明（个案清单）+ 二开需求书

格式：`# / 差异/个案 / 设计处理 / 分类（个案|二开|待确认）`

### 4.6 报工点位规划（2.5 章节核心）

> 蓝图 2.5「报工点位规划」页：明确每车间/产线的**点位类型、数量、位置**，与硬件部署对应。数据直接引用流程规划技能产出的《报工点位规划》（方法论 3.4）。

**选型原则（与流程规划 `references/报工点位规划.md` 一致）**：

| 生产方式 | 点位模式 | 数量规则 |
|---|---|---|
| 固定生产设备为主 | 工位机 + 扫码枪 | 1 台覆盖 4-6 台设备（`max(1, ceil(设备数/5))`） |
| 车间界限明确 | 工位机 + 扫码枪 | 每车间 1 台起步，设备密集按 `ceil(设备数/5)` 叠加 |
| 流水线/组装车间 | 工位机 | 每产线 1-2 台 |
| 人员多且独立报工 | 移动端（手机/PDA） | 按操作工 1:1 |
| 质检人员 | 移动端（手机/PDA） | 按质检人数 1:1 |

**页面内容**（slide 17）：
1. 点位规划表：车间/产线 | 生产方式 | 点位类型 | 数量 | 覆盖设备/人员
2. 布局示意：每车间标注工位机/移动端布点位置（配合车间布局图或文字描述）
3. 硬件采购清单（新购/利旧）与报工记录模式联动说明

**来源**：流程规划 `{客户}_报工点位规划.xlsx` → 蓝图页直接引用结论；若未提供，按调研报告中的车间/人数/设备布局现场推导并标注"待实施确认"。

### 4.5 配色与视觉（南京鼎华模板 · 客户A为基准）

> **模板基准**：客户A蓝图 V1（`{{PROJECT_DIR}}）——背景 `#F8F9FA` 浅灰白底 + 鼎华品牌蓝系，是后续所有蓝图 PPT 的视觉模板。

**配色（从客户A蓝图实测提取）**：

| 角色 | Hex | 用途 |
|:-|:-|:-|
| 背景 | `#F8F9FA` | 全篇页面底色（浅灰白） |
| 主蓝 | `#2DB8F1` | 标题竖条、卡片头、强调边框（鼎华标志亮蓝） |
| 深蓝 | `#007BD3` / `#034373` | 目录序号、章节块、表头深色底 |
| 浅蓝 | `#6EB0FF` | 流程节点、图表大面积（高频使用色） |
| 琥珀橙 | `#EE822F` | 个案/待确认/重点标注 |
| 高亮黄 | `#FFFF00` | 关键数据高亮 |
| 红色 | `#FF0000` | 风险/异常强调 |

**南京鼎华官方模板规范**（宇牌 XX机电实施蓝图母版提取，`{{PROJECT_DIR}} XX机电实施蓝图.pptx`）：
- 一级色彩：品牌色 `#00AFF0` + 同色系 `#000064` `#005AFF` `#00E1FF`（标题/正文/图表主色）
- 二级色彩（图表点缀）：`#FF5A6E` `#FFD200` `#14E69B` `#6446FF`
- 字体：思源黑体（标题 Medium / 正文 Regular）
- 字号规范：首页标题 42-44 / 演讲人 24 / 日期 21 / 目录 35 / 序列号 30 / 正文标题 20

**母版三区**：A 标题 0-120px / B 内容 120-660px / C 页脚 660-720px
**视觉语言**：全 SVG 流程/表格（蓝图无具象场景，无需生图）；页面底色浅灰白 `#F8F9FA`，白卡片浮起，蓝色系流程节点 + 琥珀色标注个案。

## 5. 三阶段生成流程

### 阶段一：素材准备

```bash
python scripts/extract_blueprint_materials.py \
  --project-dir <客户项目目录> \
  --report "<调研报告.doc>" \
  --implement "<实施报告.docx>" \
  --pre-sales "<售前方案.pptx>" \
  --out extracted/
```

自动产出：
- `extracted/调研报告.txt`、`extracted/实施报告.txt`、`extracted/售前方案.json`
- 章节素材映射（按 23 页结构预填每页素材清单）

### 阶段二：方法论应用

读 `references/blueprint_framework.md` 和 `references/screenshot_library.md`，按章节框架把提取的素材组织成 STORY.md（叙事逻辑 23 页）+ DESIGN.md（设计稿·配色字号）。

### 阶段三：PPT 生成（tencent-pptx）

按 `tencent-pptx` skill 标准流程：

```
slidep-start --project <客户项目> --filename "<客户>eMES蓝图规划报告V1.pptx" --dev
```

- 模板：参考**客户A蓝图 V1**（南京鼎华模板，`{{PROJECT_DIR}}）的视觉风格；pages/*.jsx 以动量守恒交付件为基线，按客户数据替换
- 配色/字体：按 §4.5 南京鼎华模板规范（背景 #F8F9FA + 主蓝 #2DB8F1 + 深蓝 #007BD3 + 浅蓝 #6EB0FF + 琥珀 #EE822F，思源黑体）
- 校验：`for f in pages/*.jsx; do slidep-validate "$f"; done`
- 编译：后台 dev 模式自动编译，关闭时手动 close_file

> ⚠️ **文件锁经验**：slidep 实时编译常撞 editor_sdk 文件锁（"Export file is occupied"）。见第 7 节故障处理。

### 阶段四：交付与签字

- 主 pptx 提交给客户蓝图汇报会
- 各部门主管在签字页签字确认
- 沉淀案例到 `references/cases/<客户>.md`（输入材料 + 章节映射 + 素材调用 + 签字节点）

### 阶段二附加：最佳实践流程培训配套（方法论 2.2 ☆）

> 蓝图汇报之外的另一项客户培训交付物，与蓝图同期产出（素材同源）。

1. 读取 `references/best_practice_training.md`（六列流程库 + DEMO 数据模板 + 问题管制表）
2. 生成培训材料：
   ```bash
   python scripts/gen_training_materials.py \
     --client "<客户名>" \
     --tool-dir "E:/eMES 3.0/标准工具" \
     --library-index "<项目>/蓝图分析/操作手册素材库/索引.json" \
     --out "<项目>/最佳实践流程培训/"
   ```
3. 产出：
   - `<客户>_最佳实践流程图.html`：7 条核心流程（派工/报工/首自巡检/设备点检/模具/上料/委外）六列表格 + 关键界面截图
   - 截图选取规则与蓝图一致（优先前端 PADA_/手机 APPA_ 手册前 3 张）
4. 同步准备：
   - **DEMO 数据收集模板**：按 工厂→车间→工艺→设备→物料→工单→工艺路线→订单→领料→仓库 顺序（与 Excel 导入技能模板复用）
   - **问题管制表（初版）**：培训结束创建，2.2 创建 → 3.5/3.6/4.2 持续更新，状态流转 打开→处理中→已关闭

### 阶段二附加：模拟剧本生成（方法论 3.5/3.6 模拟验证与客户应用培训）

> 依据最佳实践流程（客户实际工序/设备）生成客户版《模拟剧本》，供 3.5 各部门流程模拟验证与 3.6 客户应用培训使用。

```bash
python scripts/gen_simulation_script.py --client "<客户名>" \
  --processes "PVC工序:高速混料造粒一体机,拉丝工序,制链工序,攻拉测试工序,包塑工序,配件组装" \
  --out "<项目>/3.5-1 模拟剧本V1.xlsx"
```

- **模板**：`templates/模拟剧本模板V1.xlsx`（用户提供基准，4 个 Sheet）
  - Sheet1 基础数据搭建：用户/组织/工厂/车间/仓库/设备/物料/工艺/检验/SOP 搭建标准动作（原样保留）
  - Sheet2 生产报工模拟流程：按 `--processes` 动态生成（每工序 8 步：报工台选择→选设备→点检→上下料→开始加工→过程检验→送检→结束加工）
  - Sheet3 质检流程：首检/自巡检/末检/不良审核（保留）
  - Sheet4 设备流程：设备维修/保养（保留）
- **工序清单来源**：流程规划输出的实施流程规划/调研报告中的工艺路线；设备名从客户设备清单取
- **组装/装配/包装类工序自动用 PDA 手机端模板**（4 步精简操作）
- 生成后交客户模拟验证使用，问题记入问题管制表

## 6. 操作流程截图引用规范

按 `references/screenshot_library.md`：

1. 定位模块（派工 → 任务聪明派，报工 → 工厂数字化 + 手机端……）
2. 在 `raw/<模块>/<手册名>/NN.png` 选**前端/手机端手册**前 3 张图（入口/主界面）
3. 命名 `ui_<子流程>_<终端>.png`，复制到新项目 `resources/images/`
4. JSX 引用：

```jsx
<Image src='resources/images/ui_派工_平板.png'
       style={{ width: '100%', height: 210, objectFit: 'contain',
                borderRadius: 6, border: '1px solid #E5E7EB' }} />
```

每个核心子流程（派工/报工/质量/设备/模具/上料/装箱/委外）配 1 张关键界面截图，集中在「操作流程截图示例」补充页（封面 + N 张界面）。

## 7. 故障处理（实测经验）

| 故障 | 原因 | 解法 |
|:-|:-|:-|
| `validate` 报溢出 | B 区内容过高 | 压缩 height 500-520 / 减 padding / 减 gap |
| slidep `save FAIL: Export file is occupied` | editor_sdk 持久持有文件锁 | `edsdk.py call close_file file_id=<id> force=true` 释放锁；再杀旧 worker pid 重启 slidep-start |
| slidep worker 不再自动重试 | withReopenRetry 触发后未恢复 | `taskkill /F /PID <worker_pid>` 后再启动 slidep-start |
| 新页 slide_24 编译不保存 | 同上文件锁 | 用 `scripts/build_blueprint_pptx.py`（python-pptx 离线构造）兜底交付独立补充页 pptx |
| `slidep-start` 被 SIGPIPE 杀掉 | 命令接 `\| head -5` | 用 `run_in_background` 直接执行，不截断输出 |
| FAIcon 'factory' 不存在 | 元数据未含 | 改用 `'industry'` |
| `slidep-export-images` 报 437005 | 云端临时不可用 | 不影响文件本身，pptx 已成功编译到磁盘 |

## 8. 目录结构

```
智能交付助手-蓝图助手/
├── SKILL.md                       # 本文件
├── templates/
│   └── 模拟剧本模板V1.xlsx         # 模拟剧本基准模板（4 Sheet：基础数据/生产报工/质检/设备）
├── references/
│   ├── blueprint_framework.md     # 章节框架 + 撰写要点（核心方法论）
│   ├── design_template.md         # 南京鼎华模板视觉基准（客户A V1 实测配色/版式）
│   ├── screenshot_library.md      # 操作手册截图引用规范
│   ├── best_practice_training.md  # 最佳实践流程培训配套（六列流程库/DEMO模板/问题管制表）
│   ├── case_template.md           # 单客户档案模板
│   └── cases/
│       └── 动量守恒.md            # 首个已沉淀案例（输入材料/章节映射/素材调用）
└── scripts/
    ├── extract_blueprint_materials.py  # 从调研/实施/售前 PPT 中提取素材
    ├── gen_training_materials.py       # 最佳实践流程培训材料生成（2.2☆）
    ├── gen_simulation_script.py        # 模拟剧本生成（3.5/3.6，按客户工序）
    └── build_blueprint_pptx.py         # python-pptx 离线构造补充页（绕开文件锁）
```

## 9. 已沉淀案例

| 客户 | 报告 | 页数 | 特征 |
|:-|:-|:-:|:-|
| **客户A（视觉基准）** | `客户A蓝图V1.pptx`（南京鼎华模板） | 43 | **视觉模板基准**：背景 #F8F9FA + 主蓝 #2DB8F1 + 深蓝 #007BD3 + 浅蓝 #6EB0FF + 琥珀 #EE822F |
| 动量守恒绿色能源 | `动量守恒eMES蓝图规划报告V1.pptx` | 23 | 4 条工艺路线（1 自产+1 自产+1 委外+1 自产）、11 台设备数采、12 项个案 |

详见 `references/cases/动量守恒.md`。

## 10. 验收 checklist（交付前自查）

- [ ] 进度对齐：所有工作节点与 eMES 实施主计划一致、标 "I am here"
- [ ] 范围界定：物理区域 + 产品系列 + 上线 eMES 模块明确
- [ ] 实施目标：8 大透明按客户选择并写清含义
- [ ] 验收条件：每个透明目标都有报表/看板/无纸化/数采四类依据
- [ ] 十大场景：集成/数采/派工/报工/检验/设备/包装/委外/模具/eSOP 覆盖
- [ ] 操作流程：每工序都有角色/时机/工具/步骤/异常/输出，引用操作手册截图
- [ ] 效益对比：图文展示 As Is→To Be，与 8 大透明挂钩
- [ ] 硬件部署：报工点位明确数量与位置（类型/数量/覆盖设备人员，引用流程规划点位结论）
- [ ] 二开：个案有背景+初版需求书，标注优先级
- [ ] 签字页：客户各部门主管签字确认