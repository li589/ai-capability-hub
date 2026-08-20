---
name: bid-analysis
description: 招标文件智能解析与投标辅助工具。上传招标文件（PDF/Word）后自动结构化解析，生成Word分析报告和交互式HTML投标辅助工作台网页。触发场景：用户上传招标文件要求"解析招标文件"、"生成投标工作台"、"投标SOP"、"标书辅助"、"招标文件分析"，或要求对招标文件进行全面投标流程管理时使用。
name_cn: 招标文件解析与投标辅助
description_cn: 上传招标文件，自动生成Word分析报告和交互式HTML投标工作台网页
---

# 招标文件解析与投标辅助

上传招标文件后，输出两份交付物：
1. **Word分析报告**（.docx）：结构化解析结果 + 投标SOP + 评分策略
2. **HTML投标工作台**（单文件网页）：10个交互页面，支持复选框追踪、主题切换、保存导出

## 工作流

### Step 1：提取文本

- PDF文件：用 `python -X utf8` + pdfplumber 提取全文，保存为 `.temp/bid_full_text.txt`
- Word文件：用 docx skill 提取文本
- 扫描件PDF：用 PaddleOCR 或在线OCR工具兜底
- 超过50页时优先提取关键章节：评标办法、采购需求、投标人须知、合同条款

### Step 2：结构化解析

从文本中提取以下数据，完整字段映射参见 [references/parsing-guide.md](references/parsing-guide.md)。

**必须提取的核心数据（11组）：**

| 变量名 | 内容 | 示例 |
|:---|:---|:---|
| `PROJECT` | 项目基本信息对象 | `{name, bidNo, purchaser, budget, deadline, ...}` |
| `EVAL_SCORES` | 评标评分项数组 | `[{category, item, score, detail, target}]` |
| `STRATEGIES` | 每项评分的策略建议 | `[{item, tips[]}]` |
| `TECH_REQS` | 技术功能要求 | `[{module, item, detail, importance}]` |
| `HARDWARE_REQS` | 硬件参数要求 | `[{name, qty, params}]` |
| `BIZ_REQS` | 商务条款 | `[{name, value}]` |
| `DARK_MARK_RULES` | 暗标格式规范 | `[{item, rule, consequence}]` |
| `RISKS` | 风险清单 | `[{type, desc, level, suggestion}]` |
| `QUALIFICATIONS` | 资质材料清单 | `[{name, necessity, deadline}]` |
| `PERSONNEL` | 人员配置要求 | `[{role, requirements, certs, score}]` |
| `SOP_PHASES` | 投标SOP阶段 | `[{name, period, color, tasks[]}]` |

**SOP生成规则：**
- 5个阶段：投标启动与研读(Day1-2) → 商务资信准备(Day3-7) → 技术方案编写(Day3-10) → 商务文件编制(Day8-12) → 审核校验与封装上传(Day13-14)
- 每阶段包含具体任务，每任务含 `{id, name, detail, responsible, deadline, necessity, priority}`
- deadline 根据开标日期倒推
- 评分策略根据评标办法生成针对性建议

### Step 3：生成Word分析报告

用 docx skill 生成 `.docx` 文件，保存到工作空间根目录，文件名：`【{采购人简称}】招标文件解析报告.docx`

报告结构（参考parsing-guide.md中的9张表）：
1. 项目概述（元数据+评分构成+关键时间节点）
2. 投标SOP（5阶段×N任务，含负责人和截止日）
3. 评分策略（每项评分的目标得分+具体策略）
4. 技术要求分析
5. 商务要求分析
6. 暗标格式规范检查表
7. 风险清单
8. 资质准备清单
9. 人员配置与证书要求

### Step 4：生成HTML投标工作台

1. 复制模板 `assets/workbench-template.html` 到工作空间
2. 搜索并替换模板中的11组JS常量数据
3. 修改 `<title>` 标签中的项目名称
4. **必须执行JS语法验证（见下方）**
5. 通过HTTP服务器打开验证

**模板文件位置：** `~/.config/teleai-super-agent/skills/bid-analysis/assets/workbench-template.html`

**数据替换方式：** 在模板中搜索 `/* === 项目数据 === */` 注释标记，将对应JS常量替换为Step 2解析的实际数据。变量名和数据结构必须保持一致。

**【强制】数据替换后JS语法验证：**

替换完成后，**必须**用Node.js检查JS语法，确认无错误后再打开浏览器。语法错误会导致整个脚本块不执行，页面显示为空白（侧边栏有但内容区无数据）。

验证命令（Python提取JS后交给Node检查）：
```python
import re, subprocess
with open(html_path,'r',encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
js = m.group(1)
with open('.temp/check_js.js','w',encoding='utf-8') as f:
    f.write(js)
result = subprocess.run(['node','--check','.temp/check_js.js'], capture_output=True, text=True)
if result.returncode != 0:
    print('SYNTAX ERROR:', result.stderr)  # 必须修复后才能继续
```

**常见替换陷阱（踩坑记录）：**
- 模板原有占位数据的 `];` 或 `}` 在替换时未完全删除，导致多余的闭合符号残留
- 数组/对象内部字符串包含 `[` 或 `]`（如正则表达式、文档示例），会影响括号统计但Node `--check` 能准确定位真正的语法错误
- 替换时必须完整替换旧常量声明（从 `const XXX =` 到对应的闭合 `];` 或 `};`），不能只替换值部分而保留旧的闭合符号

### Step 5：验证交付

- **前置条件：Step 4的JS语法验证必须通过**（`node --check` 返回码为0）
- 启动HTTP服务器：`Start-Process python -ArgumentList "-m","http.server","8899","--directory","工作空间路径"`
- 用浏览器打开HTML文件，逐页检查10个页面渲染
- 验证交互功能：阶段折叠、策略展开、复选框、SOP保存、主题切换
- 若页面空白（侧边栏有但内容区无数据），优先用Node.js语法检查排查JS错误

## HTML网页功能清单

| 页面 | 功能 | 交互 |
|:---|:---|:---|
| 项目概览 | 4卡横铺（限价/截止/质保/评标）+ 项目信息 + 评分构成 + 进度总览 | 无 |
| 投标SOP | 5阶段折叠 + 44项复选框 + 到期提醒 + 保存按钮 | 复选框持久化、阶段折叠、保存含时间戳文件名 |
| 评标分析 | 可交互环状图 + 评分策略 + 得分汇总表 | Hover高亮、点击切换右侧分值构成、策略展开折叠 |
| 技术要求 | 技术参数表 + 搜索筛选 + 硬件要求 | 搜索过滤 |
| 商务要求 | 商务条款信息卡 | 无 |
| 暗标规范 | 13条格式规则检查表 | 复选框持久化 |
| 风险分析 | 风险卡片 + 筛选器 | 状态切换（待处理/处理中/已解决） |
| 资质准备 | 资质清单表格 + 筛选器 | 复选框持久化 |
| 人员配置 | 人员资质卡片 | 无 |
| 商务报价 | 4策略卡片 + 报价计算器 + 基准价模拟器 | 计算交互 |

## 交互设计规范

- **事件绑定**：用 `onclick="全局函数()"` 而非 `addEventListener`（避免Playwright兼容问题）
- **数据持久化**：localStorage，key = `bidding_portal_state`
- **SOP保存**：离开SOP页面时若有修改弹窗提醒；保存文件名格式 `大模型智能融合平台建设项目_投标辅助工作台_20260430_143025.html`
- **主题切换**：`[data-theme="dark"]` + CSS变量
- **分页**：数据列表必须配分页组件
- **金额**：万元，取整，千分位分隔

## 踩坑记录

| 问题 | 原因 | 防范措施 |
|:---|:---|:---|
| 页面空白，侧边栏有但内容区无数据 | 数据替换时残留多余的 `];` 或 `}`，导致JS语法错误，整个`<script>`块不执行 | Step 4替换后**必须**运行 `node --check` 验证语法；替换旧常量时完整删除旧声明（含闭合符号） |
| 残留代码覆盖导致回退 | 函数替换时未完整删除旧版本，残留代码导致语法错误 | 函数替换使用唯一上下文（前后各多取几行）确保精确匹配 |
| `querySelector`返回null | DOM元素ID与实际不匹配 | 渲染函数中ID必须与HTML模板一致，全局搜索确认 |
| setTimeout延迟注入不可靠 | `renderAll()`在数据注入前执行，渲染为空状态 | 数据在变量声明处直接赋值，不使用setTimeout |
| 概览页评分构成三卡片分值之和≠100分 | 模板`renderOverview()`函数中硬编码了上一个项目的分值（如商务25、暗标65），JS常量声明区域替换不会覆盖这些渲染函数内的写死数字 | Step 4替换数据后，**必须全局搜索模板中所有硬编码的旧项目分值**（如`25`分、`65`分、`暗标`、`明标`等关键词），改为从`EVAL_SCORES`按`category`动态汇总计算；侧边栏项目名（`sidebar-subtitle`）、概览页副标题（`page-desc`）等处的旧项目名/编号也需一并替换 |
| 项目概览/评标分析页面点击无反应（侧边栏可见但内容区空白） | `renderOverview()`和`renderEval()`函数依赖`CAT_KEYS`/`CAT_SCORES`两个全局变量（用于动态汇总各category分值），但这两个变量在模板中从未定义，导致`ReferenceError`使渲染函数崩溃，`content.innerHTML`未赋值 | **已在模板中修复**：在`EVAL_SCORES`声明结束后、`STRATEGIES`声明之前插入`CAT_KEYS`/`CAT_SCORES`动态计算代码（遍历`EVAL_SCORES`按`category`分组求和）。同时将`renderEval()`中硬编码的描述文字和`renderBreakdown()`中硬编码的分值改为从`CAT_KEYS`/`CAT_SCORES`动态读取。**后续生成工作台时无需额外处理此问题** |

## 资源文件

- `assets/workbench-template.html`：完整HTML模板（含所有10个页面、CSS主题、JS交互逻辑），约2800行
- `references/parsing-guide.md`：招标文件解析字段映射指南（11组数据结构定义 + 解析要点 + 9张标准产出表）
