# 外观设计 · 交底/设计说明成文（Step 7）

**本文件仅用于外观设计。** 发明 / 实用新型分见对应目录。

命名时间戳、脱敏、禁止仓库脚注等公共纪律可参照 `../invention/disclosure_builder.md` §7.3 / 文末清洁要求。  
成文前须 AppearanceSchema（`prompts/shared/fill_appearance_schema.md`）及同目录 **`figure_plan.yaml`**（`references/schemas/figure_plan.schema.yaml`）。

外观文件实务格式因代理所而异；本技能交付 **Markdown + 同名 Word**。视图说明须同时嵌入**干净实拍**与**线稿**（两套文档一致，用 `tools/shared/md_to_docx.py`；勿只出 md、勿漏实拍或漏线稿）。

## 7.1 建议结构

```
1. 注意事项（代理人可读、公开充分）
2. 一、产品名称与用途
3. 二、设计要点（形状 / 图案 / 色彩或其结合；对齐 schema.design_points）
4. 三、视图说明（立体/六视；对齐 schema.views + **仅嵌 figure_plan 入文图**）
5. 四、与在先外观的主要差异（查新后写；禁止无依据贬低）
6. 五、其它（可选：使用状态参考图说明；勿写内部结构）
```

## 7.2 文头

```markdown
# 外观设计说明（交底底稿）

**产品名称**：[待填写]

**技术联系人**：
- 姓名：[待填写]
- 电话：[待填写]
- 邮箱：[待填写]

**专利类型**：外观设计
```

## 7.3 写作硬性要求

- 只写**看得见的造型/图案/色彩**，不写内部电路、卡扣受力、工艺步骤。  
- 视图齐全或在 AppearanceSchema `uncertain` 标明缺视图；正文「见图 N」**只引用** `figure_plan` 中 `use_in_disclosure: true` 的条目（按 `fig`），勿临场扫全目录。  
- **多视联读**：立体/正交/局部之间用 `relates_to`（`same_state` / `alternate_view` / `detail_of`）；正文说明须与之一致，跨图造型特征勿互相矛盾。  
- **入文同时嵌干净实拍与合格线稿**（`photo_clean` + `kind: lineart`）。实拍不得标成线稿；CAD 禁止入文。缺正式六视写入 AppearanceSchema `uncertain`。  
- **线稿（必做）**：成文前已按 `shared/image_gen.md` + `shared/design_lineart_assist.md` 选用或生成；不问用户。  
- **交付**：`.md` 与同名 `.docx` 均须含上述实拍与线稿。  
- 查新：`tools/crawl/cnipa_epub_search.py --type design`；每条在先外观须可核验来源。  
- `not_design_signals` 非空时须反问是否改实用新型/发明。  
- **禁止**交付正文末尾追加技能仓库 / `examples/` /「虚构教学」脚注。

## 7.4 命名与交付

- 主文件名：`{产品名规范化}_{YYYYMMDDHHmmss}.md`（规则同发明 §7.3：去占位、非法字符、≤80 字、凡交付必时间戳）。  
- 配图：按 `figure_plan.path` 拷到交付同级 `assets/` 或写相对路径；勿覆盖旧交付。实拍与线稿都拷。  
- **必须**：`tools/shared/md_to_docx.py` 生成同名 `.docx`（与 md 同一套入文图）。

## 7.5 自检（内部）

执行 `../disclosure_self_check.md` **通用项 + §8.5 外观设计**，并确认：

- [ ] 文头为外观设计  
- [ ] 设计要点可追溯 AppearanceSchema  
- [ ] 视图仅来自 `figure_plan` 且「见图 N」与 `fig` 对齐；干净实拍与线稿均已入文  
- [ ] 入文多视/局部的 `relates_to` 已写且正文联读一致（可无场景参考图）  
- [ ] 线稿经 image_gen + design_lineart_gate；CAD 未入文；实拍未标成 lineart  
- [ ] 已交付同名 `.md` 与 `.docx`，两套都嵌实拍与线稿  
- [ ] 未把功能构造写成外观要点  
- [ ] 查新 `--type design`  
- [ ] 交付回复：若适用，已按 **`prompts/evolution/soft_nudge.md`** 决定是否加政策感知一句（低频）
- [ ] 交付回复末尾：若 cad_scan 为 `ask_enable_step_parse`，交底已落盘后再反问是否开启 STEP 解析；未得「是」未装依赖

表例见同目录 **`template_reference.md`**。
