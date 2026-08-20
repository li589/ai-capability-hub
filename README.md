# AI 能力整合包 · 发布版（能力优先 v2）

把 Trae / TraeCN / Qoder / QoderWork / QoderCN / WorkBuddy 共 6 款 AI 工具的能力（Skills、Plugins、Connectors、Experts、MCPs、Canvas、Knowledges、Design Libraries、Commands）**按能力类型归并**为一个可分发目录。`manifest.csv` 记录每个包的出处（来源工具 / 原路径 / 类别），同名跨工具能力加 `_<工具码>` 后缀并存、可追溯。

> 本目录已清除：真实密钥、用户机器路径（`C:\Users\likr` 等）、用户自建（`agent_created: true`）及个人项目能力。

## 规模

| 指标 | 数值 |
|---|---|
| 能力类型 | 9（skills / plugins / connectors / experts / mcps / canvas / design_libraries / knowledges / commands）|
| 包总数 | **3,510** |
| 文件总数 | **46,725** |
| 来源工具 | qoder-work 2012 · workbuddy 1371 · trae-cn 99 · trae 19 · qoder 6 · qoder-cn 3 |

各能力包数：skills 3149 · plugins 201 · connectors 120 · design_libraries 16 · experts 12 · mcps 5 · canvas 4 · knowledges 2 · commands 1

## 目录结构（能力优先）

```
AI能力整合包_发布版/
├── skills/           # 3149 包，按 ai_agent/dev/devops/data/design/writing/marketing/media/finance/knowledge/edu/office/legal/browser/travel/local_tools/other 归并
├── plugins/          # 201 包，含 devops/trae-remote-official 等
├── connectors/       # 120 包（原 connectors_marketplace）
├── design_libraries/ # 16 包
├── experts/          # 12 包（原 experts_embedded）
├── mcps/             # 5 包（**新增**：恢复自 trae 的 MCP 能力）
├── canvas/           # 4 包（含 kanban / recipes 模板）
├── knowledges/       # 2 包
├── commands/         # 1 包
├── manifest.csv      # 每个包的溯源：target_path, source_tool, package, capability, category, src_category, orig_rel
├── README.md
└── 检查报告.md
```

## 本次更新（相对 v1 能力优先版）

1. **细化 `other` 杂项桶**：原 346 个 other 包经扩展关键词分类器重分类，仅保留 23 个真·杂项。
   - skills/other：257 → 20（dev 69 / marketing 30 / devops 35 / office 21 / knowledge 20 / media 10 / local_tools 10 / finance 7 / design 6 / writing 9 / ai_agent 12 / edu 5 / legal 5 / browser 1 / travel 1）
   - connectors/other：62 → 0（finance 8 / knowledge 13 / office 12 / marketing 11 / data 3 / design 3 / local_tools 5 / devops 1 / dev 1 / media 2 / browser 1 / travel 2）
   - plugins/other：22 → 0（dev 15 / devops 2 / finance 2 / ai_agent 1 / local_tools 1 / office 1）
   - experts/canvas/commands/other：3 → 0（experts 人设、canvas 模板、command 文件均归位）
2. **恢复 trae 全量 MCP**：新建 `mcps/` 顶层能力，并入 trae 的 5 个 MCP 包（1532 文件）。
   - 注：trae 的 skills 此前已完整纳入；本次补齐缺失的 mcps。
3. **trae-cn devops 确认保留**：`plugins/devops/trae-remote-official`（4496 文件）本就在发布版中，已清理其中的厂商绝对路径（`/Users/bytedance/...` → `/home/bytedance`），并移除恢复过程中误生成的重复副本 `_tcn`。

## 安全与合规

- 真实密钥：**0**（已知密钥片段、API Key、Token 占位均复查无残留）
- 用户机器路径（`C:\Users\likr`、`/Users/likr`、`D:\...`）：**0**
- 用户自建技能（`agent_created: true` frontmatter / HTML 注释）：**0**（说明文档与模板示例中的该字样为误报，非真实标记）
- 垃圾文件（`__pycache__` / `*.pyc` / `.DS_Store` / `*.log` / `*.tmp`）：**0**
- 已排除用户**个人项目能力**（如 CGDA 综合地理数据分析系统等），仅纳入通用工具能力

## 使用说明

- `manifest.csv` 可用 Excel / 任意 CSV 工具打开，按 `capability`+`category` 筛选浏览。
- 包内 `source_tool` 字段标明来源工具；跨工具同名包以 `_tr`(trae) `_tcn`(trae-cn) `_qw`(qoder-work) `_wb`(workbuddy) `_qd`(qoder) `_qcn`(qoder-cn) 区分。
- 仍保留在 `*/other/` 的 23 个包为无法强制归类的通用/个人/模板类能力，属诚实保留。
