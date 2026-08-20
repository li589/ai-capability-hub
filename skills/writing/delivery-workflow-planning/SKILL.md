---
name: delivery-workflow-planning
display_name: 鼎华eMES 智能交付助手-流程规划
display_name_en: Survey & Workflow Planning
description: "Pre-delivery survey generator: turn survey templates, handover docs and research materials into customer-specific questionnaires, survey reports and implementation plans with risk alerts."
description_zh: 智能交付前置调研：由调研问卷模板、售前交接文档、调研素材生成客户专属调研问卷、调研报告与实施流程规划（含风险预警）。
description_en: "Pre-delivery survey generator: turn survey templates, handover docs and research materials into customer-specific questionnaires, survey reports and implementation plans with risk alerts."
category: research
version: 1.0.0
author: Digihua
trigger:
  - 调研
  - 调研问卷
  - 调研报告
  - 生产调研
  - 蓝图
  - 业务流程
  - 业务流程规划
  - 交接文档
  - 售前方案
  - 实施规划
  - 客户问卷
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
---
# 智能交付 · 生产调研生成器（智能交付助手-流程规划）

> eMES 智能交付系列的前置调研环节，衔接「售前 → 实施」。
> 输入：调研问卷模板 + 售前交接文档 + 调研素材 + 标准化流程文件 → 输出：客户专属调研问卷 / 调研报告 / 实施流程规划。

## 核心方法论（问卷"说明"页，必须遵循）

1. **实施调研 ≠ 售前调研**：侧重未来规划落地，以 eMES 系统为核心（系统有固化流程、最佳实践），不泛泛了解客户。
2. **以生产任务为中心**，围绕人、机、料、法、环、测。
3. **8 大透明**（按客户可选）：派工透明、产能透明、任务透明、进度透明、设备透明、质量透明、人员透明、不良透明。
4. 实施规划务必与现场场景结合（标签打印、流程卡打印、检验环节等）——客户"不得不用"。
5. 一个问题可问不同部门交叉验证；提问后总结并追问"还有没有其他问题"。

## 输入处理矩阵（已实测验证）

| 输入类型 | 常见格式 | 处理方式 | 脚本 |
|---|---|---|---|
| 调研问卷模板 | 腾讯在线表格 docs.qq.com/sheet | tencent-docs skill（sheet-mcp get_sheet_info + get_cell_data 批量读 CSV） | scripts/fetch_survey_sheets.py |
| 售前方案 | .pptx | 优先 editor_sdk open_file + slide_get_page_info；失败则 zipfile 直接解析 `<a:t>` | scripts/extract_pptx.py |
| 会议纪要 | .docx | python-docx 提取段落+表格 | scripts/extract_docx.py |
| 服务记录单 | .doc（老格式） | win32com 调 WPS/Word COM 提取 | scripts/extract_doc.py |
| 标准化流程文件 | 语雀密码文档 yuque.com | playwright 接管系统 Chrome → 输入密码 → 提取正文（API 直连被 CSRF 拦截，不可用） | scripts/yuque_read.py |
| 调研录音 | .mp3/.wav | faster-whisper 转写（机器需先装；首次下载模型 ~1GB） | 见下方"录音转写" |
| 参考蓝图 | .pptx | 同售前方案处理，作为输出结构模板 | scripts/extract_pptx.py |

## 阶段零：共识目标 + 项目计划制定（方法论任务 1.2 / 1.3）

> 交付启动期必做，衔接「售前交接 → 正式实施」。对应方法论 1.2 共识目标（初访）与 1.3 项目计划制定。

### 0.1 初访 PPT（1.2 共识目标）

- 模板见 `references/交付启动模板包.md`（8-10 页骨架 + 目标选择库）
- 关键动作：展示系统现有报表/看板清单，请客户圈选关注项（**不扩充表格，以现有报表为依据**）

### 0.2 共识目标确认（初访+调研后，蓝图体现）

- **8 大透明目标圈选**：根据调研掌握的客户痛点圈选本期透明化目标（一般 3-5 项），每项写清关注原因
- **验收 = 报表**：每个透明目标落到具体可见的报表/看板——"看到哪几张报表就算上线"，作为验收依据
  - 例：产能透明 → 生产日报表、车间产量看板；设备透明 → 稼动率报表、点检完成率
- **物理范围确认**：覆盖哪些厂区/车间/产线/工序，一期纳入哪些设备与物料
- 确认结果记录《实施进度确认表》首版，2.7 蓝图报告会正式签字

### 0.3 项目实施计划（1.3，强制用脚本生成）

```bash
# 倒排（推荐）：锚定上线日期，按方法论建议间隔反推
"$PY" scripts/gen_project_plan.py --client "客户名" --online-date 2026/08/01 \
  --adjust "1.4:2,3.5:3" --out-format both --out "{客户名}_项目实施计划"
# 正排：从项目启动日开始
"$PY" scripts/gen_project_plan.py --client "客户名" --launch-date 2026/06/01 --out "{客户名}_项目实施计划.html"
```

- 数据源：`references/实施计划任务表.json`（27 项任务，辅导天数/间隔周期/交付物，来自《实施方法论》）
- **倒排逻辑**：先按正排生成全表，再整体平移使 **4.2 系统正式切换锚定上线日**——间隔严格遵循方法论建议
- **时数调整** `--adjust "编码:天数,..."`：按调研实施范围（车间/产线数）与功能范围（模块覆盖）调整辅导天数
- **输出**：`--out-format html / xlsx / both`——Excel 甘特（里程碑一览 + 分阶段计划）供客户直接使用
- 生成后转 Word 交付（`generate_docx.py` 分块插入），HTML/Excel 为中间稿

### 0.4 启动会三件套（1.3）

- 启动会策划方案（议程/准备物/输出）、辅导通知单、服务记录单 —— 模板均在 `references/交付启动模板包.md`
- 启动会后输出：《会议签到表》+ 《实施进度确认表》首版（勾选目标与计划）

## 三阶段流程

### 阶段一：生成客户专属调研问卷

> **数据收集前移**：问卷生成时同步收集「实施物理范围 + 8 大透明目标倾向 + 关注报表」，作为阶段零共识目标确认与蓝图范围界定的输入。

1. 读取问卷模板（腾讯表格全部子表，常见为"说明/现场参观/高层访谈/计划部门/工艺工程/人员/设备/料/法/测"）。
2. 读取售前交接文档（方案 PPT 为主），提取：客户行业、产品、车间/产线、信息化现状、核心痛点、管理目标。
3. **筛选重点方向**：按客户痛点从模板中勾选/加权相关调研方向，剔除无关项；痛点集中在哪，问卷就深挖哪。
4. **前移收集（共识目标输入）**：问卷中固定加入三类问题——
   - **实施物理范围**：本次上线覆盖哪些厂区/车间/产线/工序？一期设备与物料范围？
   - **8 大透明目标倾向**：客户最希望看到哪些透明化（多选），原因是什么？
   - **关注报表**：客户日常最关心哪些数据/报表（用于映射到系统现有报表作为验收依据）
5. **点位规划采集（3.4 硬件规划输入）**：问卷「现场参观/生产部门」模块补充——
   - **车间/产线清单**：车间物理界限是否清晰？
   - **人员数量与分布**：每车间/产线操作工数？是否个人单独报工（计件）？
   - **设备布局与密度**：设备数量、机台间距、是否固定工位？哪些车间设备密集？
   - **质检人员**：质检员数量、是否跨工位流动检验？
   - **现有硬件**：客户已有平板/电脑/扫码枪？利旧可能？
   （采集项与选型原则见 `references/报工点位规划.md`）
6. 生成 `{客户名}_调研问卷.docx`：封面（客户名/日期/调研对象）+ 调研说明（8 大透明引导）+ 按模块分组的重点问题清单（问题/客户现状/系统支撑点三列）。
7. 输出用 scripts/generate_docx.py（HTML 分块插入）。

### 阶段二：生成调研报告

1. 输入：调研录音（转写）或文字稿/会议纪要/服务记录单。
2. 按问卷模块结构化归纳：现状 → 差异 → 痛点 → 实施关注点。
3. 交叉验证：同一问题不同部门回答不一致时，标注"待二次确认"。
4. 生成 `{客户名}_调研报告.docx`：调研概览、各部门现状、核心痛点、系统差异、实施关注点清单。

### 阶段三：流程规划 + 风险预警

1. 读取标准化流程文件（语雀《最佳实践流程图》21 份 xlsx 清单或本地产品培训目录 10 套标准化文档）。
2. **调用规划参考知识库** `references/knowledge_base.md`：识别新客户是否属于已知客户画像（行业/车间结构/生产模式/设备/集成），套用其中"流程设计模式库"和"风险预警清单"；客户明细档案在 `references/cases/{客户}.md`。
3. 将调研结果映射到 eMES 标准流程模块：派工/报工/首自巡检/设备保养/稼动/工单拆并/返工/工艺变更/上料/委外/包装等。
4. 按客户车间差异化设计主流程（每个车间一版：工序节点 + 步骤清单 + 特殊说明）。
5. 参考蓝图 PPT 结构规划输出：概述 → 主流程总览 → 各车间主流程 → 核心子流程（派工/报工/质量/设备）→ 报工点位 → 关键差异 → 效益 → 下阶段工作。
6. **风险预警**：检索历史实施项目（工作区竞品分析/产品培训/平台手册等 + 历史项目档案目录）+ 知识库风险要点，找共同风险点（如"模具一期暂缓""质量只录基础检验不替代 QMS""设备无 PLC 不做数采"），输出预警表。
7. **报工点位与硬件规划（3.4，强制）**：按调研的车间/人数/设备布局输出点位规划——
   - 选型原则与采集项见 `references/报工点位规划.md`
   - 生成点位规划表：
     ```bash
     "$PY" scripts/gen_point_plan.py --client "<客户名>" \
       --plan "PVC车间:fixed:8:6:1,组装线1:line:0:10:0,质检科:qc:0:0:3" \
       --out "<输出目录>/{客户名}_报工点位规划.xlsx"
     ```
     `--plan` 格式：`车间名:模式:设备数:操作工人数:质检人数`；模式 fixed（固定设备）/ zone（车间界限）/ line（流水线）/ mobile（人员独立报工）/ qc（质检）
   - 输出：Sheet1 报工点位规划（车间/生产方式/点位类型/数量/覆盖设备人员）+ Sheet2 硬件采购清单（新购/利旧）
   - 选型核心：固定设备→工位机+扫码枪（1 台覆盖 4-6 台设备）；车间界限→按车间设工位机；流水线→工位机按产线；人员多且独立报工→移动端；质检→移动端
   - 点位规划章节写入 `{客户名}_实施流程规划.docx`，并与报工记录模式（设备/派工/人员）联动
8. 生成 `{客户名}_实施流程规划.docx`。

### 阶段三附加：业务流程 × 产品参数映射（强制）

规划完成后，必须将业务流程与 eMES 产品标准流程、参数规划结合，输出参数配置建议：

1. 读取 `references/eMES参数规划_16项.json`（7 大作业模块 16 项参数，作业编号 PCB_OP_0001 ~ PCP_MO_0002）。
2. 将客户流程环节逐节点映射到产品功能支持 + 对应参数（通用主流程 8+1 节点映射见 knowledge_base 案例）。
3. 按客户流程差异化配置参数，输出 `{客户名}_参数配置建议表`。
4. 遵循实施要点：
   - **报工记录模式决定流程骨架**：先确认客户主报工模式（设备/派工/人员），再映射其他参数
   - **序列号类参数联动**：是否收集序列号=是时，须联动确认序号收集方式、是否卡控报工顺序、是否可扫系统外序列号、是否校验用料清单
   - **设备/模具参数按客户投入分级**：无 PLC 设可加工；有数采/锁机设不可加工；模具不管设超寿命可加工=是
   - **委外统一走 ERP**：MES 侧工艺是否可委外均设不可委外
   - **参数以客户为单位配置**：同参数不同客户取值不同，按客户维度分别设定

> ⚠️ **知识库定位**：`references/knowledge_base.md`（主库）+ `references/cases/`（客户档案）是顾问 AI 给客户做规划时调用的**内部参考知识**（行业画像/流程设计/风险预警），不是给客户看的材料。
> **累积机制（强制）**：每完成一个客户项目，必须：① 新建 `references/cases/{客户}.md` 档案（套用 shengpasi.md 模板）；② 更新主库"客户档案索引"表；③ 将新发现的画像维度/风险点/设计模式追加到主库第二、三、四章；④ 输出 `{客户名}_参数配置建议表`（依据 eMES参数规划）。客户越多，后续规划越准。

## 录音转写（faster-whisper）

```bash
# 首次安装（机器当前未装）
python -m pip install faster-whisper
# 转写（首次运行自动下载模型 ~1GB）
python -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, _ = model.transcribe('录音.mp3', language='zh')
print('\n'.join(s.text for s in segments))
"
```
> ⚠️ 若 CTranslate2 与 python 3.13 不兼容，改用 openai-whisper 或云端转写 API。

## 生成 Word 文档的规范

- 输出一律 .docx，用 scripts/generate_docx.py（create_doc → doc_insert_html_content 分块插入 → save_file）。
- HTML 支持：`<h1>~<h6>`（映射 Heading1~6）、`<p>`、`<b>/<i>/<u>`、`<ul>/<ol><li>`、`<table><tr><td>`、`<br>/<hr>`。
- 章节顺序插入，idx 用响应返回的 position+1 推进，不要手算。
- 大型文档（>10 章）分多次插入，每次 1 章，便于定位失败点。

## 环境与依赖（本机已验证）

- Python venv：`{{HOME}}/.workbuddy/binaries/python/envs/default/Scripts/python.exe`
- 必备包：python-docx、requests、playwright（含系统 Chrome 接管，无需下载内核）、win32com（提取 .doc）
- 依赖 skill：tencent-docs（腾讯表格）、tencent-local-office-edit（editor_sdk 读写本地 Office）
- ⚠️ pip 并发安装会破坏 venv（site-packages 丢包）。**任何 pip 操作串行执行**，损坏后用 `get-pip.py --ignore-installed` 修复。
- ⚠️ editor_sdk 对部分文件 open 后 is_open=false（如蓝图 pptx），fallback 用 zipfile 解析。

## 目录结构

```
智能交付助手-流程规划/
├── SKILL.md                    # 本文件
├── scripts/
│   ├── gen_project_plan.py     # 项目实施计划生成（正排/倒排甘特，方法论任务表）
│   ├── gen_point_plan.py       # 报工点位与硬件规划（3.4，车间/人数/设备布局→点位+采购清单）
│   ├── fetch_survey_sheets.py  # 腾讯在线表格（问卷模板）批量读取
│   ├── extract_pptx.py         # PPTX 文本提取（zipfile 零依赖）
│   ├── extract_docx.py         # DOCX 段落+表格提取
│   ├── extract_doc.py          # DOC 老格式提取（WPS/Word COM）
│   ├── yuque_read.py           # 语雀密码文档读取（playwright+系统Chrome）
│   └── generate_docx.py        # Word 文档生成（HTML 分块插入）
└── references/
    ├── knowledge_base.md       # 主知识库：客户索引 + 画像矩阵 + 风险清单 + 设计模式（累积核心）
    ├── 实施计划任务表.json      # 方法论 27 项任务标准参数（辅导天数/间隔/交付物，计划生成数据源）
    ├── 交付启动模板包.md        # 初访PPT骨架 + 目标选择库 + 启动会/辅导通知单/服务记录单模板
    ├── 报工点位规划.md          # 3.4 现场硬件选型原则 + 调研采集项 + 点位规划输出规范
    ├── eMES参数规划_16项.json   # 产品参数规划（7大模块16项，作业编号PCB_OP_0001~PCP_MO_0002）
    └── cases/
        ├── shengpasi.md       # 客户档案：客户A（已沉淀）
        ├── nanchang_lianda.md # 客户档案：客户B（已沉淀）
        └── yupai.md           # 客户档案：客户C（已沉淀）
```
