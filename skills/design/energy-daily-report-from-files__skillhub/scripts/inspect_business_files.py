#!/usr/bin/env python3
"""Safely inspect supported business files and emit JSON plus Markdown reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from friendly_error import friendly_error

SUPPORTED = {".xlsx", ".xlsm", ".xls", ".ods", ".csv", ".tsv", ".docx", ".pdf", ".txt", ".md", ".zip"}
ZIP_MEMBER_SUPPORTED = SUPPORTED - {".zip"}
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_ZIP_MEMBERS = 500
MAX_ZIP_MEMBER_SIZE = 100 * 1024 * 1024
MAX_ZIP_TOTAL_SIZE = 500 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
MAX_TEXT_SAMPLE = 200_000
RETRY_MAX = 2
RETRY_DELAY = 0.5
DRIVE_RE = re.compile(r"^[A-Za-z]:")


def _retry_read(func, *args, **kwargs):
    """对暂时性文件 I/O 错误最多重试 RETRY_MAX 次."""
    last_exc = None
    for attempt in range(RETRY_MAX + 1):
        try:
            return func(*args, **kwargs)
        except OSError as exc:
            last_exc = exc
            if attempt < RETRY_MAX:
                time.sleep(RETRY_DELAY * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def sha256_file(path: Path) -> str:
    def calculate() -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    return _retry_read(calculate)


def problem(code: str, message: str, suggestion: str) -> dict:
    return {"code": code, "message": message, "suggestion": suggestion}


def safe_member_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return bool(normalized and not pure.is_absolute() and ".." not in pure.parts and not DRIVE_RE.match(normalized))


def inspect_zip(path: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    members: list[dict] = []
    total = 0
    valid_members = 0
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                errors.append(problem("ZIP_TOO_MANY_MEMBERS", f"ZIP 成员数 {len(infos)} 超过上限 {MAX_ZIP_MEMBERS}", "拆分压缩包后重试。"))
            for info in infos:
                if info.is_dir():
                    continue
                name = info.filename
                suffix = Path(name).suffix.casefold()
                item = {"name": name, "size": info.file_size, "compressed_size": info.compress_size, "extension": suffix}
                members.append(item)
                if not safe_member_name(name):
                    errors.append(problem("ZIP_UNSAFE_PATH", f"ZIP 包含不安全路径：{name}", "删除路径穿越、绝对路径或盘符成员后重新打包。"))
                    continue
                if info.file_size > MAX_ZIP_MEMBER_SIZE:
                    errors.append(problem("ZIP_MEMBER_TOO_LARGE", f"ZIP 成员过大：{name}", "拆分或压缩源文件。"))
                total += info.file_size
                if info.compress_size == 0 and info.file_size > 0:
                    errors.append(problem("ZIP_RATIO_UNSAFE", f"ZIP 成员压缩比异常：{name}", "检查是否为压缩炸弹或损坏文件。"))
                elif info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                    errors.append(problem("ZIP_RATIO_UNSAFE", f"ZIP 成员压缩比超过 {MAX_COMPRESSION_RATIO}:1：{name}", "重新生成正常压缩包。"))
                if suffix in ZIP_MEMBER_SUPPORTED and info.file_size > 0:
                    try:
                        payload = _retry_read(archive.read, info)
                        if suffix in {".xlsx", ".xlsm", ".docx"}:
                            with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                                required = "word/document.xml" if suffix == ".docx" else "xl/workbook.xml"
                                if required not in nested.namelist() or nested.testzip():
                                    raise ValueError("Office 内部结构无效")
                        elif suffix == ".ods":
                            with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                                if "content.xml" not in nested.namelist() or nested.testzip():
                                    raise ValueError("ODS 内部结构无效")
                        elif suffix == ".xls":
                            if not payload.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
                                raise ValueError("XLS 文件头无效")
                        elif suffix == ".pdf":
                            if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
                                raise ValueError("PDF 结构无效")
                        elif suffix in {".txt", ".md", ".csv", ".tsv"}:
                            decoded = None
                            for encoding in ["utf-8-sig", "gb18030"]:
                                try:
                                    decoded = payload.decode(encoding)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            if decoded is None or not decoded.strip():
                                raise ValueError("文本为空或编码不支持")
                        valid_members += 1
                    except (OSError, ValueError, zipfile.BadZipFile) as exc:
                        errors.append(problem("ZIP_MEMBER_CORRUPT", f"ZIP 内的文件 {name} 已损坏或格式不兼容，无法解析", "替换损坏成员后重新打包。"))
                elif suffix and suffix not in ZIP_MEMBER_SUPPORTED:
                    warnings.append(problem("ZIP_MEMBER_UNSUPPORTED", f"ZIP 成员格式不参与业务分析：{name}", "仅将支持的电子档用于建模。"))
            if total > MAX_ZIP_TOTAL_SIZE:
                errors.append(problem("ZIP_TOTAL_TOO_LARGE", f"ZIP 解压总量超过 {MAX_ZIP_TOTAL_SIZE // 1024 // 1024} MB", "拆分压缩包后重试。"))
            bad = archive.testzip()
            if bad:
                errors.append(problem("ZIP_CRC_FAILED", f"ZIP 成员 CRC 校验失败：{bad}", "重新获取或重新压缩文件。"))
    except (zipfile.BadZipFile, OSError) as exc:
        errors.append(problem("ZIP_CORRUPT", "压缩包文件已损坏或不是有效的 ZIP 格式，请从原始来源重新获取", "重新获取未损坏的 ZIP。"))
    return {"valid": not errors and valid_members > 0, "structure": {"member_count": len(members), "supported_member_count": valid_members, "total_uncompressed_size": total, "members": members[:100]}, "errors": errors, "warnings": warnings}


def inspect_office_zip(path: Path, kind: str) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    structure: dict = {}
    required = "xl/workbook.xml" if kind == "excel" else "word/document.xml"
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            bad = archive.testzip()
            if bad:
                errors.append(problem("OFFICE_CRC_FAILED", f"Office 文件内部成员损坏：{bad}", "重新导出电子档。"))
            if required not in names:
                errors.append(problem("OFFICE_STRUCTURE_INVALID", f"缺少关键结构：{required}", "确认扩展名与真实文件格式一致。"))
            if kind == "excel":
                macros = [name for name in names if name.casefold().endswith("vbaproject.bin")]
                externals = [name for name in names if name.startswith("xl/externalLinks/")]
                embeddings = [name for name in names if name.startswith("xl/embeddings/")]
                if macros:
                    warnings.append(problem("EXCEL_MACRO_PRESENT", "检测到宏；分析时不会执行宏", "生成系统时只读取安全数据与结构。"))
                if externals:
                    warnings.append(problem("EXCEL_EXTERNAL_LINKS", "检测到外部链接；不会访问外部源", "将外部来源标记为待确认。"))
                if embeddings:
                    warnings.append(problem("EXCEL_EMBEDDINGS", "检测到嵌入对象；不会执行或提取", "如业务需要请提供独立原始文件。"))
                sheets: list[str] = []
                if required in names:
                    root = ElementTree.fromstring(archive.read(required))
                    for node in root.iter():
                        if node.tag.endswith("sheet") and node.attrib.get("name"):
                            sheets.append(node.attrib["name"])
                structure.update({"sheet_count": len(sheets), "sheet_names": sheets, "has_macros": bool(macros), "external_links": len(externals), "embeddings": len(embeddings)})
                if not sheets:
                    errors.append(problem("EXCEL_NO_SHEETS", "工作簿没有可识别工作表", "重新导出包含数据的工作簿。"))
            else:
                embeddings = [name for name in names if name.startswith("word/embeddings/")]
                if embeddings:
                    warnings.append(problem("DOCX_EMBEDDINGS", "检测到嵌入对象；不会执行或提取", "如需分析请单独提供嵌入文件。"))
                text_length = 0
                if required in names:
                    root = ElementTree.fromstring(archive.read(required))
                    text_length = sum(len(node.text or "") for node in root.iter() if node.tag.endswith("}t"))
                structure.update({"text_length": text_length, "embeddings": len(embeddings)})
                if text_length == 0:
                    errors.append(problem("DOCX_EMPTY", "Word 文档没有可识别正文", "提供包含可读取文字或表格的文档。"))
    except (zipfile.BadZipFile, ElementTree.ParseError, OSError) as exc:
        errors.append(problem("OFFICE_CORRUPT", "Office 文件已损坏，请用 Excel/WPS 重新打开并另存为新文件后重试", "重新获取或重新导出文件。"))
    return {"valid": not errors, "structure": structure, "errors": errors, "warnings": warnings}


def inspect_legacy_excel(path: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    try:
        header = _retry_read(path.read_bytes)[:8]
        if header != bytes.fromhex("D0CF11E0A1B11AE1"):
            errors.append(problem("XLS_STRUCTURE_INVALID", "文件扩展名是 .xls，但内容不是可识别的旧版 Excel 工作簿", "用 Excel 或 WPS 打开并另存为 .xlsx。"))
        else:
            warnings.append(problem("XLS_CONVERSION_RECOMMENDED", "已安全识别旧版 XLS；不会执行宏或嵌入对象", "正式导入前优先另存为 .xlsx；无法转换时保留原文件并建立人工字段映射。"))
    except OSError as exc:
        errors.append(problem("XLS_READ_FAILED", friendly_error(exc), "关闭占用文件的程序后重试。"))
    return {"valid": not errors, "structure": {"format": "legacy-xls", "analysis_mode": "structure-only"}, "errors": errors, "warnings": warnings}


def inspect_ods(path: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    structure: dict = {"format": "ods"}
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if archive.testzip():
                errors.append(problem("ODS_CRC_FAILED", "ODS 内部文件校验失败", "用 WPS 或 LibreOffice 重新另存后重试。"))
            if "content.xml" not in names:
                errors.append(problem("ODS_STRUCTURE_INVALID", "ODS 缺少 content.xml", "确认扩展名与真实文件格式一致。"))
            mimetype = archive.read("mimetype").decode("ascii", errors="replace") if "mimetype" in names else ""
            structure["mimetype"] = mimetype
            if mimetype and mimetype != "application/vnd.oasis.opendocument.spreadsheet":
                errors.append(problem("ODS_MIMETYPE_INVALID", "文件不是标准开放表格 ODS", "用原软件重新导出为 ODS 或 XLSX。"))
        if not errors:
            warnings.append(problem("ODS_CONVERSION_RECOMMENDED", "已安全识别 ODS；独立程序默认不直接导入该格式", "优先另存为 XLSX 或 CSV；同时保留 ODS 原件用于追溯。"))
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(problem("ODS_READ_FAILED", friendly_error(exc), "重新获取或重新导出文件。"))
    return {"valid": not errors, "structure": structure, "errors": errors, "warnings": warnings}


def inspect_delimited(path: Path, delimiter: str) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    rows = 0
    columns = 0
    encoding = None
    for candidate in ["utf-8-sig", "gb18030"]:
        try:
            with path.open("r", encoding=candidate, newline="") as stream:
                reader = csv.reader(stream, delimiter=delimiter)
                for index, row in enumerate(reader):
                    if index == 0:
                        columns = len(row)
                    rows += 1
                    if rows >= 10000:
                        warnings.append(problem("DELIMITED_SAMPLE_LIMIT", "表格超过 10000 行，结构检查采用前 10000 行", "正式导入仍需逐行校验并输出错误报告。"))
                        break
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
        except (csv.Error, OSError) as exc:
            errors.append(problem("DELIMITED_READ_FAILED", "分隔文本格式不兼容或已损坏，请检查文件是否可用 Excel 正常打开后重新导出 CSV", "检查分隔符、引号和文件完整性。"))
            break
    if encoding is None and not errors:
        errors.append(problem("TEXT_ENCODING_UNSUPPORTED", "无法以 UTF-8 或 GB18030 读取文本", "转换为 UTF-8 后重试。"))
    if rows < 1 or columns < 1:
        errors.append(problem("DELIMITED_EMPTY", "文件没有可识别行列", "提供包含表头和数据的 CSV/TSV。"))
    return {"valid": not errors, "structure": {"rows_sampled": rows, "column_count": columns, "encoding": encoding}, "errors": errors, "warnings": warnings}


def inspect_text(path: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    text = None
    encoding = None
    for candidate in ["utf-8-sig", "gb18030"]:
        try:
            text = _retry_read(path.read_text, encoding=candidate)[:MAX_TEXT_SAMPLE]
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            errors.append(problem("TEXT_READ_FAILED", "文本文件编码问题或已损坏，请用记事本打开后另存为 UTF-8 编码", "确认文件权限和完整性。"))
            break
    if text is None and not errors:
        errors.append(problem("TEXT_ENCODING_UNSUPPORTED", "无法以 UTF-8 或 GB18030 读取文本", "转换为 UTF-8 后重试。"))
    if text is not None and not text.strip():
        errors.append(problem("TEXT_EMPTY", "文本文件为空", "提供包含业务内容的文件。"))
    return {"valid": not errors, "structure": {"encoding": encoding, "characters_sampled": len(text or ""), "line_count_sampled": len((text or "").splitlines())}, "errors": errors, "warnings": warnings}


def inspect_pdf(path: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    try:
        data = _retry_read(path.read_bytes)
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-4096:]:
            errors.append(problem("PDF_STRUCTURE_INVALID", "PDF 头或结束标记无效", "重新导出未损坏的 PDF。"))
        if b"/Encrypt" in data[: min(len(data), 2_000_000)]:
            errors.append(problem("PDF_ENCRYPTED", "PDF 可能已加密", "提供可读取的未加密副本。"))
        page_count = len(re.findall(rb"/Type\s*/Page\b", data))
        if page_count == 0 and not errors:
            warnings.append(problem("PDF_PAGE_COUNT_UNKNOWN", "无法通过结构快速确认页数", "后续使用受控 PDF 解析器提取文本和表格。"))
    except OSError as exc:
        errors.append(problem("PDF_READ_FAILED", "PDF 文件无法读取，可能已损坏或缺少访问权限，请确认文件完整", "确认文件权限和完整性。"))
        page_count = 0
    return {"valid": not errors, "structure": {"page_count_estimate": page_count}, "errors": errors, "warnings": warnings}


def inspect_file(path: Path) -> dict:
    item = {"path": str(path), "name": path.name, "extension": path.suffix.casefold(), "size": None, "sha256": None, "valid": False, "structure": {}, "errors": [], "warnings": []}
    if not path.is_file():
        item["errors"].append(problem("INPUT_NOT_FILE", "输入路径不是文件", "提供可读取的电子档文件。"))
        return item
    try:
        item["size"] = _retry_read(path.stat).st_size
        if item["size"] <= 0:
            item["errors"].append(problem("INPUT_EMPTY", "输入文件为空", "提供非空电子档。"))
            return item
        if item["size"] > MAX_FILE_SIZE and item["extension"] != ".zip":
            item["errors"].append(problem("INPUT_TOO_LARGE", "单文件超过 100 MB 安全上限", "拆分文件后重试。"))
            return item
        item["sha256"] = sha256_file(path)
    except OSError as exc:
        item["errors"].append(problem("INPUT_READ_FAILED", "文件无法访问，请检查文件是否被其他程序占用或缺少读取权限", "检查文件锁、权限和路径。"))
        return item
    suffix = item["extension"]
    if suffix not in SUPPORTED:
        item["errors"].append(problem("UNSUPPORTED_EXTENSION", f"不支持的格式：{suffix or '无扩展名'}", "转换为 xlsx、xlsm、xls、ods、csv、tsv、docx、pdf、txt、md 或 zip。"))
        return item
    if suffix == ".zip":
        result = inspect_zip(path)
    elif suffix in {".xlsx", ".xlsm"}:
        result = inspect_office_zip(path, "excel")
    elif suffix == ".xls":
        result = inspect_legacy_excel(path)
    elif suffix == ".ods":
        result = inspect_ods(path)
    elif suffix == ".docx":
        result = inspect_office_zip(path, "docx")
    elif suffix == ".csv":
        result = inspect_delimited(path, ",")
    elif suffix == ".tsv":
        result = inspect_delimited(path, "\t")
    elif suffix in {".txt", ".md"}:
        result = inspect_text(path)
    else:
        result = inspect_pdf(path)
    item.update(result)
    return item


def discover(inputs: list[str]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in inputs:
        path = Path(raw).resolve()
        candidates = [path]
        if path.is_dir():
            candidates = sorted(candidate for candidate in path.iterdir() if candidate.is_file())
        for candidate in candidates:
            if candidate not in seen:
                found.append(candidate)
                seen.add(candidate)
    return found


def analyze(inputs: list[str]) -> dict:
    files = [inspect_file(path) for path in discover(inputs)]
    valid_count = sum(1 for item in files if item["valid"])
    error_count = sum(1 for item in files if item["errors"])
    overall = hashlib.sha256()
    for item in sorted(files, key=lambda value: value["path"].casefold()):
        overall.update((item.get("sha256") or "missing").encode("ascii"))
        overall.update(item["path"].encode("utf-8"))
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "input_count": len(files),
        "valid_input_count": valid_count,
        "error_input_count": error_count,
        "input_fingerprint": overall.hexdigest(),
        "status": "ok" if valid_count and not error_count else "partial" if valid_count else "failed",
        "next_action": "继续生成系统" if valid_count else "停止生成并修复输入",
        "files": files,
    }


def render_markdown(result: dict) -> str:
    lines = ["# 电子档安全与结构分析报告", "", f"- 输入文件：{result['input_count']}", f"- 有效输入：{result['valid_input_count']}", f"- 错误输入：{result['error_input_count']}", f"- 状态：{result['status']}", f"- 下一步：{result['next_action']}", f"- 输入指纹：`{result['input_fingerprint']}`", ""]
    for item in result["files"]:
        lines.extend([f"## {item['name']}", "", f"- 格式：`{item['extension']}`", f"- 大小：{item['size']}", f"- 有效：{'是' if item['valid'] else '否'}", f"- SHA-256：`{item['sha256'] or '未计算'}`"])
        if item["structure"]:
            lines.append("- 结构：`" + json.dumps(item["structure"], ensure_ascii=False)[:1000] + "`")
        for issue in item["errors"]:
            lines.append(f"- 错误 [{issue['code']}]：{issue['message']}；解决：{issue['suggestion']}")
        for issue in item["warnings"]:
            lines.append(f"- 提示 [{issue['code']}]：{issue['message']}；建议：{issue['suggestion']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="安全检查并分析通用业务电子档")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args()
    result = analyze(args.inputs)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(result), encoding="utf-8")
    print(payload)
    return 0 if result["valid_input_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
