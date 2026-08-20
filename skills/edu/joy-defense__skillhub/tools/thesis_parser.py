#!/usr/bin/env python3
"""
thesis_parser.py
A lightweight CLI to parse thesis text from PDF/TXT/Markdown and emit a structured JSON.

- Supports input via --input <file> or --text <text>.
- File types: .txt, .md, .pdf
- Extracts: title, abstract, sections (intro, methods, results, discussion, conclusion),
  figures, tables, references, word_count, raw_text
- PDF extraction: tries pdfplumber first, falls back to PyPDF2
- Outputs JSON to stdout
"""

import argparse
import json
import os
import re
from pathlib import Path


def extract_text_pdf(pdf_path: str) -> str:
    # Try pdfplumber first
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(pdf_path) as pdf:
            text = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(text)
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(pdf_path)
        text = []
        for page in reader.pages:
            t = page.extract_text() or ""
            text.append(t)
        return "\n".join(text)
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_text(text: str) -> dict:
    # Normalize lines
    lines = text.splitlines()
    sections = {
        "introduction": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
    }
    abstract_text = []
    in_abstract = False
    current_section = None  # one of the keys of sections
    references_text = []
    in_references = False
    figs = []
    tables = []

    def identify_section(header: str):
        h = header.strip().lower()
        if h in ("introduction", "intro", "background"):  # intro variants
            return "introduction"
        if any(k in h for k in ("methods", "materials and methods")):
            return "methods"
        if any(k in h for k in ("results", "findings")):
            return "results"
        if any(k in h for k in ("discussion",)):
            return "discussion"
        if any(k in h for k in ("conclusion", "conclusions")):
            return "conclusion"
        return None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            # skip empty lines, but keep whitespace in sections
            if current_section:
                sections[current_section] += line + "\n"
            continue
        # Detect headings (markdown style or simple headings)
        header = line.strip()
        # Remove markdown heading markers
        header = re.sub(r"^#+\s*", "", header)
        # Remove leading numbering like 1. Introduction or 1) Introduction
        header_clean = re.sub(r"^\d+[\.)]\s*", "", header).strip()
        key = identify_section(header_clean)
        if header_clean.lower() in ("abstract",):
            in_abstract = True
            current_section = None
            continue
        if header_clean.lower() in ("references", "bibliography"):
            in_references = True
            current_section = None
            continue
        if key:
            current_section = key
            in_abstract = False
            in_references = False
            continue
        # Capture figures/tables captions in the text
        m_fig = re.match(r"(?i)(Figure|Fig\.?|Figura)\s*(\d+)\s*[:.\-]?\s*(.*)", line)
        if m_fig:
            n = int(m_fig.group(2))
            cap = (m_fig.group(3) or "").strip()
            figs.append({"number": n, "caption": cap})
        m_tab = re.match(r"(?i)(Table|Tab\.?|Tabla)\s*(\d+)\s*[:.\-]?\s*(.*)", line)
        if m_tab:
            n = int(m_tab.group(2))
            cap = (m_tab.group(3) or "").strip()
            tables.append({"number": n, "caption": cap})

        if in_abstract:
            abstract_text.append(line + "\n")
            continue
        if in_references:
            references_text.append(line)
            continue
        if current_section:
            sections[current_section] += line + "\n"

    result = {
        "title": "",
        "abstract": "".join(abstract_text).strip(),
        "sections": sections,
        "figures": figs,
        "tables": tables,
        "references": "\n".join(references_text).strip(),
        "word_count": len(text.split()),
        "raw_text": text,
    }

    # Try to guess a title: first non-empty line that isn't a header or abstract
    probable_title = ""
    for line in lines:
        s = line.strip()
        if not s:
            continue
        lower = s.lower()
        if lower in ("abstract", "references", "bibliography"):
            continue
        if len(s) > 5:
            probable_title = s
            break
    result["title"] = probable_title
    return result


def parse_input_text(text: str) -> dict:
    return parse_text(text)


def main():
    parser = argparse.ArgumentParser(description="Extract structured data from a thesis document.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Path to input file (.txt, .md, .pdf)")
    group.add_argument("--text", help="Raw text to parse")
    args = parser.parse_args()

    text = ""
    if args.input:
        path = Path(args.input)
        if not path.exists():
            raise SystemExit(f"Input file not found: {args.input}")
        ext = path.suffix.lower()
        if ext == ".pdf":
            text = extract_text_pdf(str(path))
        elif ext in {".txt", ".md"}:
            text = read_text_file(str(path))
        else:
            raise SystemExit("Unsupported input file type. Use .txt, .md, or .pdf.")
    else:
        text = args.text

    result = parse_input_text(text)
    # Ensure ascii-safe representation for title
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
