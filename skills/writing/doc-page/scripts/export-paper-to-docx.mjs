#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
const positional = args.filter((arg) => !arg.startsWith("--"));
const inputFile = positional[0];
const outputFile = positional[1];

const cleanHtmlArg = readOption("--clean-html");
const pandocArg = readOption("--pandoc");
const pythonArg = readOption("--python");
const referenceDocArg = readOption("--reference-doc");
const htmlOnly = args.includes("--html-only");
const noPythonFallback = args.includes("--no-python-fallback");
const keepCleanHtml = args.includes("--keep-clean-html") || htmlOnly;

if (!inputFile || (!outputFile && !htmlOnly)) {
  console.error([
    "Usage:",
    "  node export-paper-to-docx.mjs report.html report.docx [--reference-doc=template.docx] [--clean-html=out/report.clean.html]",
    "  node export-paper-to-docx.mjs report.html --html-only [--clean-html=out/report.clean.html]",
    "",
    "Exports the optional #cover-source.has-cover and semantic #source content of a paged Build Doc HTML file.",
    "The generated .page-frame preview DOM is intentionally ignored.",
  ].join("\n"));
  process.exit(2);
}

const inputPath = path.resolve(inputFile);
if (!fs.existsSync(inputPath)) {
  fail(`Input file not found: ${inputPath}`);
}

const inputHtml = fs.readFileSync(inputPath, "utf8");
const coverHtml = extractCover(inputHtml);
const sourceHtml = extractSource(inputHtml);
const title = extractTitle(inputHtml) || stripExt(path.basename(inputPath));
const cleanHtmlPath = cleanHtmlArg
  ? path.resolve(cleanHtmlArg)
  : path.resolve(path.dirname(inputPath), `${stripExt(path.basename(inputPath))}.clean.html`);

const cleanHtml = buildCleanHtml({ title, coverHtml, sourceHtml, inputPath });
fs.mkdirSync(path.dirname(cleanHtmlPath), { recursive: true });
fs.writeFileSync(cleanHtmlPath, cleanHtml);

if (htmlOnly) {
  console.log(`Wrote clean conversion HTML: ${cleanHtmlPath}`);
  process.exit(0);
}

const outputPath = path.resolve(outputFile);
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

const pandoc = pandocArg || findExecutable("pandoc");
if (!pandoc) {
  if (!noPythonFallback) {
    const python = pythonArg || findPython();
    if (python && exportWithPythonDocx({ python, cleanHtmlPath, outputPath })) {
      finishExport({ outputPath, cleanHtmlPath, keepCleanHtml });
      process.exit(0);
    }
  }
  console.error([
    "Pandoc was not found, and python-docx fallback was unavailable or failed.",
    `Clean conversion HTML was written to: ${cleanHtmlPath}`,
    "Install or expose pandoc, install python-docx+lxml, or import the clean HTML into a Docs tool manually.",
  ].join("\n"));
  process.exit(3);
}

const pandocArgs = [cleanHtmlPath, "-o", outputPath];
if (referenceDocArg) {
  pandocArgs.push("--reference-doc", path.resolve(referenceDocArg));
}

const result = spawnSync(pandoc, pandocArgs, { encoding: "utf8" });
if (result.error) {
  fail(`Failed to run pandoc: ${result.error.message}`);
}
if (result.status !== 0) {
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  process.exit(result.status || 1);
}

finishExport({ outputPath, cleanHtmlPath, keepCleanHtml });

function readOption(name) {
  const prefix = `${name}=`;
  const found = args.find((arg) => arg.startsWith(prefix));
  return found ? found.slice(prefix.length) : "";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function stripExt(filename) {
  return filename.replace(/\.[^.]+$/, "");
}

function extractTitle(html) {
  const match = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return match ? decodeEntities(stripTags(match[1]).trim()) : "";
}

function extractSource(html) {
  const openTag = html.match(/<main\b[^>]*\bid=["']source["'][^>]*>/i);
  if (!openTag || openTag.index === undefined) {
    fail("No <main id=\"source\"> block found. Cannot create editable docs source.");
  }
  const start = openTag.index + openTag[0].length;
  const closeIndex = html.indexOf("</main>", start);
  if (closeIndex === -1) {
    fail("Found <main id=\"source\"> without a closing </main>.");
  }
  return cleanSourceHtml(html.slice(start, closeIndex));
}

function extractCover(html) {
  const openTag = html.match(/<section\b[^>]*\bid=["']cover-source["'][^>]*>/i);
  if (!openTag || openTag.index === undefined || !/\bhas-cover\b/.test(openTag[0])) {
    return "";
  }
  const start = openTag.index + openTag[0].length;
  const closeIndex = findClosingTag(html, openTag.index, "section");
  if (closeIndex === -1) {
    fail("Found <section id=\"cover-source\"> without a closing </section>.");
  }
  return cleanSourceHtml(html.slice(start, closeIndex));
}

function findClosingTag(html, openIndex, tagName) {
  const tagPattern = new RegExp(`<\\/?${tagName}\\b[^>]*>`, "gi");
  tagPattern.lastIndex = openIndex;
  let depth = 0;
  let match;
  while ((match = tagPattern.exec(html))) {
    if (match[0].startsWith("</")) {
      depth -= 1;
      if (depth === 0) return match.index;
    } else if (!match[0].endsWith("/>")) {
      depth += 1;
    }
  }
  return -1;
}

function cleanSourceHtml(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, "")
    .replace(/<style\b[\s\S]*?<\/style>/gi, "")
    .replace(/\saria-hidden=["'][^"']*["']/gi, "")
    .replace(/\sclass=["']([^"']*)["']/gi, (_match, classes) => {
      const kept = classes
        .split(/\s+/)
        .filter((name) => name && !["flow-block", "page-frame", "page", "page-content", "folio"].includes(name));
      return kept.length ? ` class="${kept.join(" ")}"` : "";
    })
    .replace(/\sstyle=["'][^"']*["']/gi, "")
    .trim();
}

function buildCleanHtml({ title, coverHtml, sourceHtml, inputPath }) {
  const baseHref = pathToFileUrl(path.dirname(inputPath)) + "/";
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(title)}</title>
  <base href="${baseHref}">
  <style>
    body {
      color: #222;
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", Georgia, serif;
      font-size: 11pt;
      line-height: 1.65;
    }
    h1, h2, h3 { color: #17227d; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d9d9d9; padding: 6px 8px; vertical-align: top; }
    th { background: #eeeeee; }
    .caption, .source-item { color: #555; font-size: 9pt; }
    .callout { border-left: 3px solid #777; padding-left: 12px; }
  </style>
</head>
<body>
${coverHtml}
${sourceHtml}
</body>
</html>
`;
}

function findExecutable(command) {
  const result = spawnSync("command", ["-v", command], {
    encoding: "utf8",
    shell: true,
  });
  if (result.status === 0) return result.stdout.trim().split(/\r?\n/)[0];
  return "";
}

function findPython() {
  return pythonArg || findExecutable("python3") || findExecutable("python");
}

function exportWithPythonDocx({ python, cleanHtmlPath, outputPath }) {
  const helper = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "export-paper-docx-fallback.py");
  const commandArgs = fs.existsSync(helper)
    ? [helper, cleanHtmlPath, outputPath]
    : ["-c", pythonDocxExporter(), cleanHtmlPath, outputPath];
  const result = spawnSync(python, commandArgs, {
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 10,
  });
  if (result.status === 0) {
    if (result.stdout) process.stdout.write(result.stdout);
    return true;
  }
  if (result.stderr) process.stderr.write(result.stderr);
  return false;
}

function finishExport({ outputPath, cleanHtmlPath, keepCleanHtml }) {
  if (!keepCleanHtml) {
    try {
      fs.unlinkSync(cleanHtmlPath);
    } catch {
      // Keep going: DOCX export succeeded, and the clean HTML is harmless.
    }
  }
  console.log(`Wrote DOCX: ${outputPath}`);
  if (keepCleanHtml) {
    console.log(`Kept clean conversion HTML: ${cleanHtmlPath}`);
  }
}

function stripTags(value) {
  return value.replace(/<[^>]*>/g, "");
}

function decodeEntities(value) {
  return value
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function pathToFileUrl(value) {
  const absolute = path.resolve(value);
  const prefix = process.platform === "win32" ? "file:///" : "file://";
  return prefix + absolute.split(path.sep).map(encodeURIComponent).join("/");
}

function pythonDocxExporter() {
  return String.raw`
from pathlib import Path
import sys

try:
    from lxml import html
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
except Exception as exc:
    print(f"python-docx fallback dependencies unavailable: {exc}", file=sys.stderr)
    sys.exit(4)

src = Path(sys.argv[1])
out = Path(sys.argv[2])
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.75)
sec.bottom_margin = Inches(0.7)
sec.left_margin = Inches(0.82)
sec.right_margin = Inches(0.82)

styles = doc.styles
styles["Normal"].font.name = "宋体"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
styles["Normal"].font.size = Pt(10.5)
for name, size in [("Title", 20), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)]:
    st = styles[name]
    st.font.name = "宋体"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor(0, 114, 178)

root = html.fromstring(src.read_text(encoding="utf-8"))
body = root.find("body")
source_counter = 0

def text_content(el):
    return " ".join(el.text_content().split())

def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)

def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(9)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP

def add_para(text, style=None, bold=False):
    if not text:
        return None
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.35
    r = p.add_run(text)
    r.font.name = "宋体"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    r.bold = bold
    return p

def add_table(table_el):
    rows = table_el.xpath("./thead/tr | ./tbody/tr | ./tr")
    if not rows:
        return
    col_count = max(len(row.xpath("./th|./td")) for row in rows)
    table = doc.add_table(rows=len(rows), cols=col_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        cells = row.xpath("./th|./td")
        is_header = bool(row.xpath("./th")) or (i == 0 and row.getparent() is not None and row.getparent().tag.lower() == "thead")
        for j in range(col_count):
            cell = table.cell(i, j)
            text = text_content(cells[j]) if j < len(cells) else ""
            if is_header:
                shade_cell(cell, "0072B2")
                set_cell_text(cell, text, bold=True, color="FFFFFF")
            else:
                if i % 2 == 0:
                    shade_cell(cell, "F3F8F6")
                set_cell_text(cell, text)
    doc.add_paragraph()

def handle_element(el):
    global source_counter
    tag = el.tag.lower() if isinstance(el.tag, str) else ""
    cls = el.get("class", "")
    if tag in ("section", "main", "div"):
        if "callout" in cls:
            add_para(text_content(el))
            return
        for child in el:
            handle_element(child)
        return
    if tag == "h1":
        add_para(text_content(el), style="Title", bold=True)
        return
    if tag == "h2":
        add_para(text_content(el), style="Heading 1", bold=True)
        return
    if tag == "h3":
        add_para(text_content(el), style="Heading 2", bold=True)
        return
    if tag == "p":
        text = text_content(el)
        if not text:
            return
        if "source-item" in cls:
            source_counter += 1
            p = add_para(f"{source_counter}. {text}")
            for run in p.runs:
                run.font.size = Pt(9)
            return
        if "caption" in cls:
            p = add_para(text)
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(85, 85, 85)
            return
        add_para(text)
        return
    if tag in ("ul", "ol"):
        style = "List Number" if tag == "ol" else "List Bullet"
        for li in el.xpath("./li"):
            add_para(text_content(li), style=style)
        return
    if tag == "table":
        add_table(el)
        return
    if tag == "hr":
        return
    text = text_content(el)
    if text:
        add_para(text, bold="subtitle" in cls)

if body is not None:
    for child in body:
        handle_element(child)

footer_p = sec.footer.paragraphs[0]
footer_p.add_run(root.xpath("string(//title)") or out.stem)
out.parent.mkdir(parents=True, exist_ok=True)
doc.save(out)
print(f"Wrote DOCX with python-docx fallback: {out}")
`;
}
