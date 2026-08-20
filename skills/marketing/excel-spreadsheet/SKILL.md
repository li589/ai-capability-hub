---
name: excel-spreadsheet
description: Generate Excel .xlsx files with openpyxl using a dedicated Python venv. Handles styling, formulas (SUMIF, COUNTIF, VLOOKUP, IF), charts, and data validation.
version: 1.0.0
author: Hermes Agent
license: MIT
tags:
  - excel
  - openpyxl
  - spreadsheet
  - business
install_source: official
install_method: download
skill_id: official_GReXVbP4
enabled_at: 1787230811699
name_zh: Excel 电子表格
---

# Excel Spreadsheet Generation

Generate `.xlsx` files with full formula support using Python's `openpyxl` library.

## Key Finding

**execute_code sandbox does NOT have openpyxl installed.** You must use a dedicated Python venv at `/home/ubuntu/excel-venv`.

## Quick Start

```bash
# Check if venv exists, create if not
python3 -m venv /home/ubuntu/excel-venv 2>/dev/null || true
/home/ubuntu/excel-venv/bin/pip install openpyxl -q

# Generate Excel using heredoc
/home/ubuntu/excel-venv/bin/python << 'PYEOF'
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
# ... your code ...
wb.save("/path/to/output.xlsx")
print("Done")
PYEOF
```

## Common Formula Patterns

| Purpose | Formula |
|---------|---------|
| Total Nilai | `=G2*H2` |
| Profit/Unit | `=G2-F2` |
| Margin % | `=(G2-F2)/F2` then format as `0.0"%"` |
| Status LOW/OK | `=IF(H2<I2,"LOW","OK")` |
| SUMIF by category | `=SUMIF('Daftar Barang'!D:D,"Makanan",'Daftar Barang'!J:J)` |
| COUNTIF status | `=COUNTIF(M2:M21,"LOW")` |
| VLOOKUP | `=VLOOKUP(C2,'Daftar Barang'!B:H,7,FALSE)` |
| Running balance | `=IF(E2="Masuk",G2+F2,G2-F2)` |
| AVERAGE | `=AVERAGE(G2:G21)` |
| SUMPRODUCT | `=SUMPRODUCT('Daftar Barang'!F2:F21,'Daftar Barang'!H2:H21)` |

## Styling Helpers

```python
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF")
warning_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
danger_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                     top=Side(style='thin'), bottom=Side(style='thin'))
center = Alignment(horizontal='center', vertical='center')

def style_header(ws, row, cols):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin_border

# Auto-width columns
def auto_width(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if len(str(cell.value)) > max_len:
                    max_len = len(str(cell.value))
            except: pass
        ws.column_dimensions[col_letter].width = min(max_len + 3, 45)
```

## Data Validation (Dropdown)

```python
from openpyxl.worksheet.datavalidation import DataValidation
dv = DataValidation(type="list", formula1='"Makanan,Sembako,Protein,Minuman"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"D2:D{last_row}")
```

## Sheet Structure Recommendations

| Sheet | Purpose |
|-------|---------|
| `Daftar Barang` | Master item list with formulas (Total Nilai, Profit, Margin, Status) |
| `Stok Movement` | In/out transactions with running balance formulas |
| `History Harga` | Price change tracking with diff/% formulas |
| `Dashboard` | Summary with SUMIF/COUNTIF/AVERAGE referencing other sheets |
| `Tambah Barang` | Form input for new items |
| `Panduan` | Help/documentation |

## Number Formats

```python
# Currency
ws.cell(row=r, column=c).number_format = '#,##0'

# Percentage
ws.cell(row=r, column=c).number_format = '0.0"%"'

# Freeze panes (keep header visible)
ws.freeze_panes = "A2"
```

## Gotchas

- execute_code sandbox lacks openpyxl, use `/home/ubuntu/excel-venv`
- Formula strings must be passed as strings: `value=f"=G{row}*H{row}"`
- For VLOOKUP to work across sheets, sheet name with spaces must be quoted: `'Daftar Barang'!B:H`
- Color fills use hex without `#` prefix
