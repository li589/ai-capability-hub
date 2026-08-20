#!/usr/bin/env python3
"""Check for text overflow in PPTX text boxes.

Usage:
    python scripts/check_text_overflow.py output.pptx

Temporarily sets all text boxes to normAutofit mode, re-saves via
LibreOffice to trigger layout calculation, then reports text boxes
where the font was scaled down (indicating the text doesn't fit).

Exits with code 1 if overflow is detected, 0 otherwise.
"""

import sys
import tempfile
import zipfile
from pathlib import Path

import lxml.etree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from office.soffice import run_soffice

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

FONT_SCALE_FULL = 100000  # 100% in OOXML units


def set_norm_autofit(slide_bytes):
    """Set all text shapes to normAutofit, return modified XML bytes."""
    root = ET.fromstring(slide_bytes)

    for sp in root.iter(f"{{{P_NS}}}sp"):
        txBody = sp.find(f"{{{P_NS}}}txBody")
        if txBody is None:
            continue

        # Skip shapes with no actual text
        if not any(
            t.text and t.text.strip() for t in txBody.iter(f"{{{A_NS}}}t")
        ):
            continue

        bodyPr = txBody.find(f"{{{A_NS}}}bodyPr")
        if bodyPr is None:
            continue

        # Remove existing autofit settings
        for child in list(bodyPr):
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local in ("spAutoFit", "normAutofit", "noAutofit"):
                bodyPr.remove(child)

        ET.SubElement(bodyPr, f"{{{A_NS}}}normAutofit")

    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")


def collect_overflow(slide_bytes):
    """Return list of (shape_name, font_scale_pct, text_preview) for overflowing shapes."""
    root = ET.fromstring(slide_bytes)
    issues = []

    for sp in root.iter(f"{{{P_NS}}}sp"):
        txBody = sp.find(f"{{{P_NS}}}txBody")
        if txBody is None:
            continue

        bodyPr = txBody.find(f"{{{A_NS}}}bodyPr")
        if bodyPr is None:
            continue

        norm = bodyPr.find(f"{{{A_NS}}}normAutofit")
        if norm is None:
            continue

        font_scale = norm.get("fontScale")
        if font_scale is None:
            continue

        scale_val = int(font_scale)
        if scale_val >= FONT_SCALE_FULL:
            continue

        # Get shape name
        name = "unnamed"
        nvSpPr = sp.find(f"{{{P_NS}}}nvSpPr")
        if nvSpPr is not None:
            cNvPr = nvSpPr.find(f"{{{P_NS}}}cNvPr")
            if cNvPr is not None:
                name = cNvPr.get("name", "unnamed")

        # Get text preview
        text_parts = []
        for t in txBody.iter(f"{{{A_NS}}}t"):
            if t.text:
                text_parts.append(t.text)
        full_text = "".join(text_parts)
        preview = full_text[:60] + "..." if len(full_text) > 60 else full_text

        issues.append((name, scale_val / 1000, preview))

    return issues


def main(pptx_path):
    pptx_path = Path(pptx_path).resolve()

    if not pptx_path.exists():
        print(f"Error: {pptx_path} not found", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        modified = tmpdir / "check.pptx"

        # Create modified copy with normAutofit on all text shapes
        with (
            zipfile.ZipFile(pptx_path, "r") as zin,
            zipfile.ZipFile(modified, "w", zipfile.ZIP_DEFLATED) as zout,
        ):
            for item in zin.namelist():
                data = zin.read(item)
                if item.startswith("ppt/slides/slide") and item.endswith(".xml"):
                    data = set_norm_autofit(data)
                zout.writestr(item, data)

        # Re-save via soffice to trigger layout engine
        result = run_soffice(
            [
                "--headless",
                "--convert-to",
                "pptx",
                "--outdir",
                str(tmpdir),
                str(modified),
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            print("Error: soffice failed", file=sys.stderr)
            stderr = result.stderr.decode(errors="replace")
            if stderr.strip():
                print(stderr, file=sys.stderr)
            sys.exit(2)

        # Read soffice output and check for overflow
        has_issues = False
        with zipfile.ZipFile(modified, "r") as z:
            slides = sorted(
                f
                for f in z.namelist()
                if f.startswith("ppt/slides/slide") and f.endswith(".xml")
            )
            for sf in slides:
                slide_label = sf.split("/")[-1].replace(".xml", "")
                issues = collect_overflow(z.read(sf))

                if issues:
                    has_issues = True
                    print(f"\n{slide_label}:")
                    for name, pct, preview in issues:
                        print(
                            f"  [TEXT OVERFLOW] '{name}' font scaled to {pct:.1f}%"
                            f' ("{preview}")'
                        )

        if has_issues:
            print()
            sys.exit(1)
        else:
            print("No text overflow detected.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <file.pptx>")
        sys.exit(1)
    main(sys.argv[1])
