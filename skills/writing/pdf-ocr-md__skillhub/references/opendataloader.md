# OpenDataLoader PDF Integration — Reference

> Text-layer PDF parsing: JSON with bounding boxes, Markdown, HTML, Text, Tagged PDF.
> Supports table detection, reading order (XY-Cut++), sanitization.

## Environment

Requires Java 11+ and the `opendataloader-pdf` PyPI package (~21.5MB, includes 23MB Java CLI JAR).

```bash
java -version 2>&1 | head -1  # must be 11+
python3 -c "import opendataloader_pdf; print('✅')" 2>&1 || echo "⚠️ not installed"
```

### Installation

```bash
# 1. Java (if missing)
sudo apt-get install -y -qq default-jre

# 2. Python SDK (use Tsinghua mirror for speed — official PyPI often times out)
python3 -m venv ~/.venvs/opendataloader
~/.venvs/opendataloader/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opendataloader-pdf

# 3. Optional: add to PATH
ln -sf ~/.venvs/opendataloader/bin/opendataloader-pdf ~/.local/bin/
```

**Key Finding**: Official PyPI (files.pythonhosted.org) downloads frequently time out; Tsinghua mirror delivers at 60+ MB/s.

## CLI Usage

```bash
# Basic: JSON + Markdown
opendataloader-pdf input.pdf -f json,markdown -o ./output_dir

# All formats
opendataloader-pdf input.pdf -f json,markdown,html,text,tagged-pdf -o ./output_dir

# Stdout (single format only)
opendataloader-pdf input.pdf -f markdown --to-stdout 2>/dev/null

# Page range
opendataloader-pdf input.pdf -f json -o ./output --pages "1,3,5-7"

# Sanitize (redact emails, phones, bank card numbers)
opendataloader-pdf input.pdf -f json -o ./output --sanitize

# Table detection mode
opendataloader-pdf input.pdf -f json -o ./output --table-method cluster

# Keep original line breaks
opendataloader-pdf input.pdf -f markdown -o ./output --keep-line-breaks
```

## Python SDK

```python
from opendataloader_pdf import convert
convert(
    "/path/to/contract.pdf",
    output_dir="/path/to/output",
    format="json,markdown,html",
    reading_order="xycut",      # XY-Cut++ reading order (default)
    table_method="default",     # or "cluster"
    pages="1,3,5-7",
    sanitize=False,
    keep_line_breaks=False
)
```

## Output Formats

| Format | Content | Use Case |
|--------|---------|----------|
| `json` | type/hierarchy/content/bounding box/font/size/color per element | Programmatic processing, positional traceability |
| `markdown` | Structured text with headings, lists, tables | LLM input, quick reading |
| `html` | Layout-preserving page | Web preview |
| `text` | Plain text | Search, simple analysis |
| `tagged-pdf` | Tagged PDF | Accessibility (PDF/UA) |

## Performance

- **Local deterministic mode**: ~0.015s/page (pure Java, no API calls)
- **AI hybrid mode**: Complex pages (OCR) need extra Hybrid service
- **No network required**: Local mode fully offline
- **23MB JAR**: Large initial download

## Limitations

- Source PDF must have extractable text layer (scanned docs need PaddleOCR path — see main pdf-ocr-md skill)
- Scanned OCR recommended path: PaddleOCR (Chinese) or OpenDataLoader hybrid mode
