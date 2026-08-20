# business-blueprint-skill

> 售前需求、会议纪要、RFP 材料 → 可编辑的业务能力蓝图、泳道流程图、应用架构图。一份 canonical JSON IR，多个下游导出格式（SVG / draw.io / Excalidraw / Mermaid）。

适用于 [Claude Code](https://claude.ai/claude-code) 和 [OpenClaw](https://openclaw.ai) 的业务蓝图生成技能，将原始售前输入转化为结构化业务能力架构。

[English](README.md) | 简体中文

---

## 效果展示

零售行业蓝图，导出为 SVG 架构：

![retail-blueprint](demos/screenshots/retail-arch.svg)

该 SVG 由 `business-blueprint --export demos/retail.blueprint.json` 生成，源 JSON 在 `demos/retail.blueprint.json`，交互式查看器在 `demos/solution.viewer.html`。

---

## 设计理念：IR 优先管道

### 一、JSON 作为标准中间表示

所有工作流最终都收敛到 `solution.blueprint.json`——唯一的事实来源。所有其他产物（查看器、SVG、draw.io）都是从这个 JSON 确定性投影出来的。

```
原始文本 ──(--plan)──→ JSON ──(--generate)──→ 查看器 HTML
                          │
                          ├──(--export)──→ SVG / draw.io / Excalidraw / Mermaid
                          │
                          └──(--edit)────→ JSON（补丁日志）+ 查看器刷新
```

IR 文件的特点：
- **可版本管理**——标准 JSON，diff 有意义
- **AI 可读**——下游技能直接解析 `entities`、`relations`、`flowSteps`，不需要 HTML 解析
- **人类可编辑**——名称、标签等轻量字段可以直接修改，不会破坏结构

### 二、渐进式披露

技能文件（`SKILL.md`）是一个路由层——它告诉 Claude 在哪个命令下应该读哪个文件。重型资产（行业包、查看器 HTML 模板、导出引擎）只有在需要时才加载。

```
--plan        → 只需模型 + 生成规则；不加载 CSS 或导出引擎
--generate    → 一个 viewer.html 模板 + 一个行业包
--export      → 仅加载请求的导出引擎；其他格式保留在磁盘
--validate    → 仅加载 schema + 规则；不加载渲染代码
```

### 三、硅碳协作

**输入端：** 人类书写自然语言（需求、会议纪要、RFP），AI 解析为结构化实体（应用系统、业务能力、流程步骤、角色）和关系。

**输出端：** 查看器是纯静态 HTML——无需构建步骤、无 JS 框架、支持离线。每个节点都可以原地编辑，编辑操作记录为 JSON patch 日志（`solution.patch.jsonl`），确保完全可追溯。

---

## 安装

### Claude Code

```bash
git clone https://github.com/kaisersong/business-blueprint-skill ~/.claude/skills/business-blueprint-skill
```

然后：`cd business-blueprint-skill && pip install -e .`

### OpenClaw

```bash
git clone https://github.com/kaisersong/business-blueprint-skill ~/.openclaw/skills/business-blueprint-skill
cd business-blueprint-skill && pip install -e .
```

---

## 使用方式

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--plan "文本"` | 将原始文本解析为标准蓝图 JSON |
| `--generate <输出>` | 生成 JSON + 静态 HTML 查看器包 |
| `--edit <blueprint.json>` | 刷新现有蓝图的查看器（保留人工编辑） |
| `--export <blueprint.json>` | 导出 SVG、draw.io、Excalidraw、Mermaid 图表 |
| `--export-auto <blueprint.json>` | 使用内容路由 + 自由流式布局导出 SVG |
| `--validate <blueprint.json>` | 验证蓝图结构，输出错误/警告 |
| `--from <文件>` | 从指定文件读取源材料 |
| `--industry <包名>` | 指定行业模板包（默认：`common`） |

### 典型工作流

**从原始文本开始：**
```bash
# 第一步：解析为标准 JSON
business-blueprint --plan "ERP 支持 POS 系统..." --from meeting-notes.md --industry retail

# 第二步：生成查看器
business-blueprint --generate solution.blueprint.json

# 第三步：导出图表
business-blueprint --export solution.blueprint.json
```

**编辑现有蓝图：**
```bash
# 手动编辑 JSON 或让 AI 编辑
# 然后刷新查看器（通过 editor.fieldLocks 保留人工编辑的字段）
business-blueprint --edit solution.blueprint.json
```

**导出前验证：**
```bash
business-blueprint --validate solution.blueprint.json
# 修复错误后：
business-blueprint --export solution.blueprint.json
```

---

## 输出产物

| 文件 | 角色 |
|------|------|
| `solution.blueprint.json` | 标准 IR——唯一事实来源 |
| `solution.viewer.html` | 静态查看器 + 轻量编辑器 |
| `solution.exports/` | SVG、draw.io、Excalidraw、Mermaid 导出 |
| `solution.patch.jsonl` | 编辑追溯日志（JSON patches） |
| `solution.handoff.json` | AI 交接版本清单 |

### SVG 架构导出

SVG 导出渲染三层架构图：

- **应用系统**（顶部）——ERP、CRM、POS 等
- **业务能力**（中间）——门店运营、会员管理、订单管理
- **流程步骤**（底部）——带能力关联的泳道流程图
- **角色**（右侧列）——与对应系统对齐的人员角色

层高度通过两遍布局动态计算：第一遍放置所有节点，第二遍计算精确的内容高度，确保角色、多行流程、堆叠的能力永远不会溢出。

---

## 项目结构

```
business-blueprint-skill/
├── SKILL.md                      # 技能定义（路由层）
├── business_blueprint/           # Python 引擎（零外部依赖）
│   ├── cli.py                    # 命令行入口
│   ├── generate.py               # 从文本生成蓝图
│   ├── model.py                  # 数据模型与顶层结构
│   ├── validate.py               # 机器可读验证
│   ├── clarify.py                # 澄清请求构建器
│   ├── normalize.py              # 实体解析与同义词合并
│   ├── viewer.py                 # HTML 查看器写入器
│   ├── export_svg.py             # SVG 导出器（两遍布局、内容路由、自由流式布局）
│   ├── export_drawio.py          # draw.io 导出器
│   ├── export_excalidraw.py      # Excalidraw 导出器
│   ├── export_mermaid.py         # Mermaid 导出器
│   ├── templates/                # 行业包（通用、零售、金融、制造）
│   ├── assets/                   # viewer.html 模板
│   └── specs/                    # 蓝图 schema 定义
├── references/                   # Schema、编写规则、行业包
├── tests/                        # 测试套件
├── demos/                        # 演示蓝图与导出
└── examples/                     # 示例蓝图 JSON
```

---

## 架构规则

引擎强制执行以下结构规则：

| 规则 | 说明 |
|------|------|
| **每个能力必须关联到系统** | 不允许孤立的能力 |
| **每个流程步骤必须关联到能力** | 不允许悬空的流程 |
| **角色 → 系统** | 角色必须引用有效的系统 ID |
| **无循环关系** | 系统 → 能力 → 流程 必须是有向无环图 |

运行 `--validate` 检查所有规则。警告表示潜在问题（如某个系统没有任何能力），错误会阻止导出。

---

## 面向 AI 智能体

其他技能可以消费蓝图产物：

```
# report-creator：将蓝图摘要嵌入商业报告
/report --from blueprint-summary.md --theme corporate-blue

# slide-creator：从蓝图构建演示文稿
/slide-creator --from solution.handoff.json

# 从 relations 生成 PlantUML
# 解析 solution.blueprint.json 中的 relations → 生成 PlantUML 语法
```

**提取结构化数据：**
```python
import json

with open("solution.blueprint.json") as f:
    bp = json.load(f)

# 实体
for sys in bp["entities"].get("applicationSystems", []):
    print(f"系统: {sys['name']}")

for cap in bp["entities"].get("businessCapabilities", []):
    print(f"能力: {cap['name']} (支撑 {cap['systemId']})")

# 关系
for rel in bp["relations"]:
    print(f"{rel['from']} --{rel['type']}--> {rel['to']}")
```

---

## 依赖要求

| 要求 | 版本 | 说明 |
|------|------|------|
| **Python** | >= 3.12 | 零外部依赖 |

---

## 兼容性

| 平台 | 版本 | 安装路径 |
|------|------|----------|
| Claude Code | 任意 | `~/.claude/skills/business-blueprint-skill/` |
| OpenClaw | >= 0.9 | `~/.openclaw/skills/business-blueprint-skill/` |

---

## 版本日志

**v0.5.0** — 内容路由与自由流式布局引擎：`_content_router()` 根据蓝图内容自动选择视图（架构图、能力地图、泳道图、流程链）；`_layout_free_flow()` 按域分组、自动换行计算节点位置；`export_svg_auto()` 组合路由+布局；新增 CLI `--export-auto` 参数；HTML 查看器现在动态显示可用视图的标签页。

**v0.4.0** — HTML 查看器与布局修复：自包含 HTML 查看器，内嵌三个 SVG 视图（架构图、能力地图、泳道图），标签页导航，汇总卡片，暗色主题支持网格背景。

**v0.3.1** — CLI 修复：`--from` 参数长中文文本不再触发 `File name too long`，`--plan` 支持 stdin 管道输入。

**v0.2.0** — SVG 布局引擎：两遍动态层高、角色溢出修复、标题层间距、标题遮挡修复、图例截断修复。

**v0.1.0** — 初始发布：plan/generate/edit/export/validate 管道；HTML 查看器支持原地编辑；SVG/draw.io/Excalidraw/Mermaid 导出；行业模板包（通用、零售、金融、制造）。
