---
name: erptax
description: "Fill ERP financial data (资产负债表, 利润表, 现金流量表) into official tax bureau Excel templates (.xls/.xlsx) while preserving all formatting, formulas, styles, colors, locked cells, and protection. Use when the user asks to fill financial statements, populate tax reporting templates, or transfer data from ERP exports to official forms. This skill covers: (1) Converting .xls to .xlsx via Excel COM, (2) Reading ERP files with xlrd, (3) XML-direct editing to preserve formulas and styles, (4) Repacking with xlsx_pack.py and calcChain cleanup."
install_source: official
install_method: download
skill_id: official_TTMKWbjy
enabled_at: 1787231900331
version: 1.0.0
name_zh: ERP 税务报表填充
---

# Excel 财务报表模板填充

## When to Use

Fill ERP financial data (资产负债表, 利润表, 现金流量表) into official tax bureau Excel templates (.xls/.xlsx) while **preserving all formatting, formulas, colors, locked cells, and cell protection**.

Triggered when user asks to:
- Fill in financial statements from ERP export
- Populate tax reporting templates
- Transfer data from ERP to official forms
- Fill Excel templates without breaking formulas or formatting

## Core Workflow

### Step 1 — Convert .xls to .xlsx first

If template is `.xls` (BIFF format), convert using Excel COM:
```powershell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false; $excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open("C:\path\to\template.xls")
$wb.SaveAs("C:\path\to\template.xlsx", 51)  # 51 = xlOpenXMLWorkbook
$wb.Close($false); $excel.Quit()
```
⚠️ Do NOT use xlutils for format-preserving operations on BIFF files.

### Step 2 — Unpack xlsx

```bash
python scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
```

### Step 3 — Read ERP data

Use `xlrd` to read ERP export files:
- 资产负债表: left cols 0-3 (资产), right cols 4-7 (负债)
- 利润表: col1=行次, col3=本期, col4=本年累计
- 现金流量表: col0=名称, col3=本期, col4=本年累计

See `references/erp-row-maps.md` for ERP row → template row mapping.

### Step 4 — Edit XML directly

**Key principle: Only modify `<v>` values, never touch `<f>` (formulas) or `s=` (styles).**

Pattern for numeric cells:
```xml
<!-- Before -->
<c r="D7" s="34">
  <v>0</v>
</c>

<!-- After (replace only <v>) -->
<c r="D7" s="34">
  <v>1638.81</v>
</c>
```

Pattern for formula cells (update cached value only):
```xml
<!-- Before -->
<c r="D21" s="40">
  <f>ROUND(D7+D8+D9+D10+D11+D12+D13+D14+D15+D20,2)</f>
  <v>0</v>
</c>

<!-- After (keep <f>, update <v>) -->
<c r="D21" s="40">
  <f>ROUND(D7+D8+D9+D10+D11+D12+D13+D14+D15+D20,2)</f>
  <v>5012140.22</v>
</c>
```

### Step 5 — Remove calcChain and repack

Delete `xl/calcChain.xml` (forces Excel to recalculate all formulas on open):
```bash
rm /tmp/xlsx_work/xl/calcChain.xml
python scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
```

## Key Rules

1. **Never use openpyxl** `load_workbook()` + `save()` on existing files — it corrupts VBA, pivot tables, sparklines, and theme colors
2. **Always delete calcChain.xml** after editing formulas or cached values
3. **Never change `s=` attribute** (style index) or `r=` attribute (cell reference)
4. **Only modify `<v>` tags** — everything else is untouched

## References

- **ERP row mapping**: `references/erp-row-maps.md`
- **XML edit patterns**: `references/xlsx-edit-guide.md`
- **xlsx unpack/pack scripts**: use from `minimax-xlsx` skill (copy to `scripts/`)

## Source Scripts

| Script | Purpose |
|--------|---------|
| `scripts/erp_fill.py` | Main orchestrator: reads ERP + edits XML + repacks |
| `scripts/xlsx_unpack.py` | Unzip and pretty-print xlsx XML |
| `scripts/xlsx_pack.py` | Repack edited XML into valid xlsx |
