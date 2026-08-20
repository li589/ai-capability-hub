# Input and Fact Contract

## Supported inputs

| Type | Required extraction | Provenance locator |
|---|---|---|
| PDF | text, tables, scanned-page content | filename + page |
| DOCX | headings, paragraphs, tables, relevant comments | filename + heading/table |
| PPTX | slide text, notes, chart values | filename + slide |
| XLSX/CSV | labels, values, formulas when relevant | filename + sheet + cell range |
| JPG/PNG | visible text, product, logo, colors, packaging | filename + image region |
| User message | explicit facts, corrections, constraints | message summary |

Use the matching installed PDF, document, presentation, spreadsheet, or image-inspection capability. Do not flatten structured files into lossy text when tables, slides, or cells matter.

## Required facts

Formal generation requires all four:

1. `产品/服务名称`
2. `所属行业`
3. `目标分销人群`
4. `分销目标`

`目标分销人群` means people who will directly promote or sell, not merely end consumers. `分销目标` needs a metric and time horizon when possible.

## Financial-priority facts

Ask for these before calculating incentives:

1. `产品售价或价格区间`
2. `成本或毛利率`
3. `激励预算`

If the user does not know them, research a range, label it as an estimate, and obtain confirmation. Auxiliary facts include region, platform, cycle, current channels, capacity, refund rate, tax assumptions, brand assets, internal restrictions, and historical conversion.

## Fact table

Use this exact shape:

| 字段 | 值或范围 | 证据类别 | 来源定位 | 可信度 | 状态 |
|---|---|---|---|---|---|
| 产品售价 | 299元 | 用户事实 | 报价表.xlsx / 价格表!B6 | 高 | 已确认 |
| 毛利率 | 50%–60% | 外部估算 | 来源链接 / 查询日期 | 中 | 待确认 |

Evidence classes are `用户事实`, `文件事实`, `外部事实`, `估算`, and `建议`. Status is `已确认`, `待确认`, or `冲突`.

## Conflict resolution

Show every conflicting value and its locator. Ask which value governs and where it applies. Do not infer that a chat message, newer file, or higher price automatically wins. Record the user's resolution in the fact table.

## Questioning contract

Ask the most consequential 1–3 questions per turn. Start with missing core facts, then unresolved conflicts, then finance facts. Do not repeat confirmed information. Offer ranges or examples only to make the question easier, not to bias the answer. After all blocking items are resolved, present a compact fact summary, ask for explicit confirmation, and stop the response there. Treat only a later user message such as “确认”“事实无误” or an explicit correction followed by confirmation as authorization to begin formal generation.
