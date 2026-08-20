# Schema 合同说明

| 文件 | 用途 | 交底 | 解读 |
|------|------|------|------|
| `structure.schema.yaml` | 形状/构造 | `disclosure/utility_model/` | 实用新型 / 装置附图 → `structure_schema.json` → 笔记「结构说明」+ Canvas |
| `appearance.schema.yaml` | 外观造型 | `disclosure/design/` | 外观设计 → `appearance_schema.json` → 笔记「外观要点」+ Canvas |
| `figure_plan.schema.yaml` | 附图选用、排序与图际关联（`relates_to`） | 实用/外观成文只嵌 `use_in_disclosure: true` | 可选；解读不强依赖 |
| `formula_plan.schema.yaml` | 发明公式选题 + 可算提纲 | 含公式时先写 `formula_plan.yaml`；范式见 `references/formulas/` | 一般不用 |
| `design_lineart_brief.schema.yaml` | 外观线稿描述（成文前必做） | 不问用户；已有合格线稿或大模型生成；CAD 不得当线稿 | 一般不用 |
| `structure_lineart_brief.schema.yaml` | 实用结构线稿描述（成文前必做） | 不问用户；轮廓与序号分层；禁止自创件号；CAD 不入文 | 一般不用 |
| `evolution_backlog.schema.yaml` | 技能进化清单（模式 C） | 旁路产出 `outputs/evolution/EVOL-*.md`；人审前不改 prompts | 不用 |
| `oa_case.schema.yaml` | 审查答复案例（模式 D） | 旁路：脱敏入库 Obs / 系统文档目录 `…/oa/cases` + sqlite-vec；答复先检索 | 可同库 `oa/cases/` |

填写指令：`prompts/shared/fill_structure_schema.md`、`fill_appearance_schema.md`（填表末步写出 **`figure_plan.yaml`**，含跨图核对与 `relates_to`）；线稿公共合同 **`prompts/shared/image_gen.md`**；外观见 **`prompts/shared/design_lineart_assist.md`**；实用新型见 **`prompts/shared/structure_lineart_assist.md`**。  
**禁止**在 disclosure 与 reader 各维护一份字段定义。  
多轮改材料或主题时须同步重评 `figure_plan`（含 `relates_to`；见该合同「多轮同步」）。StructureSchema 可选 `relations[].seen_in` 标注连接可见于哪些 `fig`。
