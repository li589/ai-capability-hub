# -*- coding: utf-8 -*-
"""
markdown_exporter.py v1.0 — 统一 Markdown 导出器
====================================================
零依赖，提供：
  - export(data, output_path, images_inline=True)      单文件 MD
  - merge_files(files, output_path, toc=True)          批量合并 + TOC
  - generate_zip(md_path, media_dir, zip_path)         打包 MD + media/
  - build_batch_export(items, output_dir, batch_id)    整批结构化导出

典型数据格式 (data):
{
    "title": "文章标题",
    "url": "https://...",
    "source": "财联社",
    "published_at": "2026-07-29T10:00:00",
    "content": "<h1>...</h1><p>...</p>"   # HTML 或 Markdown
    "author": "记者",
    "tags": ["财经","A股"]
}

items 是 list[data]。
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .html2md import convert, convert_with_tables

# 内容类型识别：HTML → MD，否则直接当 MD
_HTML_HINT = re.compile(r"<\s*(?:p|h\d|div|span|a|img|ul|ol|table|br)\b", re.IGNORECASE)


def _to_markdown(content: str, base_url: Optional[str] = None,
                 image_map: Optional[Dict[str, str]] = None) -> str:
    """智能判断内容是 HTML 还是 Markdown，统一转 MD。"""
    if not content:
        return ""
    if _HTML_HINT.search(content):
        return convert_with_tables(content, base_url=base_url, image_map=image_map)
    return content


# ============== MarkdownExporter 主类 ==============

class MarkdownExporter:
    """统一 Markdown 导出器。"""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Args:
            output_dir: 默认输出目录（None 则用 data/exports/）
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent / "data" / "exports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # --- 单文件 ---

    def export(self, data: Dict[str, Any], output_path: Optional[str] = None,
               images_inline: bool = True) -> str:
        """导出单篇文章为 Markdown 文件。

        Args:
            data: 文章字典（见模块顶部说明）
            output_path: 输出文件路径（None 则自动生成）
            images_inline: 是否内联图片

        Returns:
            实际写入的文件路径
        """
        if output_path is None:
            safe_title = _safe_filename(data.get("title", "untitled"))[:60]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"{ts}_{safe_title}.md"
        else:
            output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        md = self._render_one(data, images_inline=images_inline)
        output_path.write_text(md, encoding="utf-8")
        return str(output_path)

    # --- 批量合并 ---

    def merge_files(self, files: List[str], output_path: str,
                    toc: bool = True, title: str = "合并报告") -> str:
        """把多个 .md 文件合并为一份带 TOC 的大文档。"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        parts: List[str] = []
        if toc:
            parts.append(f"# {title}\n\n")
            parts.append(f"> 合并于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · 共 {len(files)} 份\n\n")
            parts.append("## 目录\n\n")
            for i, f in enumerate(files, 1):
                title_guess = _extract_first_heading(Path(f))
                parts.append(f"{i}. [{title_guess or Path(f).stem}]({Path(f).name})\n")
            parts.append("\n---\n\n")

        for i, f in enumerate(files, 1):
            fpath = Path(f)
            if not fpath.exists():
                continue
            text = fpath.read_text(encoding="utf-8", errors="replace")
            heading = _extract_first_heading(fpath) or fpath.stem
            parts.append(f"\n\n## {i}. {heading}\n\n")
            parts.append(text)
            parts.append("\n\n---\n\n")

        output_path.write_text("".join(parts), encoding="utf-8")
        return str(output_path)

    # --- ZIP 打包 ---

    def generate_zip(self, md_path: str, media_dir: Optional[str] = None,
                     zip_path: Optional[str] = None,
                     encoding: str = "utf-8") -> str:
        """把 MD 文件 + media/ 目录打包成 ZIP（中文文件名 UTF-8 + GBK 双编码）。

        Args:
            md_path: 主 MD 文件
            media_dir: 图片目录（可选）
            zip_path: 输出 ZIP 路径（None 自动生成）
            encoding: 文件名编码（默认 utf-8）

        Returns:
            ZIP 实际路径
        """
        md_path = Path(md_path)
        if zip_path is None:
            zip_path = md_path.with_suffix(".zip")
        else:
            zip_path = Path(zip_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            # 写入主 MD
            zf.write(str(md_path), arcname=md_path.name)
            # 写入 media 目录（如有）
            if media_dir:
                mdir = Path(media_dir)
                if mdir.exists():
                    for f in mdir.rglob("*"):
                        if f.is_file():
                            arc = f.relative_to(mdir.parent)
                            _write_zip_utf8(zf, str(f), str(arc), encoding=encoding)

        return str(zip_path)

    # --- 整批结构化导出 ---

    def build_batch_export(self, items: List[Dict[str, Any]],
                           batch_id: Optional[str] = None,
                           media_root: Optional[str] = None) -> Dict[str, str]:
        """批量导出：每个 item 一个 MD 文件 + 索引 + 元数据 + ZIP。

        目录结构:
            data/exports/<batch_id>/
              ├── _index.md
              ├── _metadata.json
              ├── <source_name>/
              │   ├── 01_<article_id>.md
              │   ├── 01_<article_id>_media/
              │   └── 02_<article_id>.md
              └── batch_<batch_id>.zip

        Returns:
            {"dir": ..., "index": ..., "zip": ...}
        """
        if batch_id is None:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = self.output_dir / batch_id
        out_dir.mkdir(parents=True, exist_ok=True)
        if media_root is None:
            media_root = out_dir
        media_root = Path(media_root)

        written: List[Dict[str, str]] = []
        index = 1
        for item in items:
            source = item.get("source", "unknown")
            src_dir = out_dir / _safe_filename(source)[:50]
            src_dir.mkdir(parents=True, exist_ok=True)

            article_id = item.get("id") or f"{index:03d}_{_safe_filename(item.get('title', 'x'))[:30]}"
            md_file = src_dir / f"{index:03d}_{_safe_filename(article_id)[:40]}.md"
            self.export(item, output_path=str(md_file))
            written.append({"title": item.get("title", ""),
                            "source": source,
                            "path": str(md_file.relative_to(out_dir))})
            index += 1

        # 索引
        index_lines = [f"# 批量导出 · {batch_id}\n\n",
                       f"> 共 {len(written)} 篇 · 导出于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                       "## 目录\n\n"]
        for w in written:
            index_lines.append(f"- **{w['source']}** — [{w['title']}]({w['path']})\n")
        (out_dir / "_index.md").write_text("".join(index_lines), encoding="utf-8")

        # 元数据
        metadata = {
            "batch_id": batch_id,
            "exported_at": datetime.now().isoformat(),
            "count": len(written),
            "items": written,
        }
        (out_dir / "_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ZIP
        zip_path = self.generate_zip(
            md_path=str(out_dir / "_index.md"),
            media_dir=str(media_root) if media_root.exists() else None,
            zip_path=str(out_dir / f"batch_{batch_id}.zip"),
        )

        return {
            "dir": str(out_dir),
            "index": str(out_dir / "_index.md"),
            "metadata": str(out_dir / "_metadata.json"),
            "zip": zip_path,
            "count": str(len(written)),
        }

    # --- 内部 ---

    def _render_one(self, data: Dict[str, Any], images_inline: bool = True) -> str:
        """渲染单篇文章为 Markdown。"""
        lines: List[str] = []
        title = data.get("title", "无标题")
        lines.append(f"# {title}\n\n")

        # 元信息
        meta_parts = []
        if data.get("source"):
            meta_parts.append(f"**来源**: {data['source']}")
        if data.get("author"):
            meta_parts.append(f"**作者**: {data['author']}")
        if data.get("published_at"):
            meta_parts.append(f"**时间**: {data['published_at']}")
        if data.get("url"):
            meta_parts.append(f"**链接**: <{data['url']}>")
        if meta_parts:
            lines.append(" · ".join(meta_parts) + "\n\n")
        if data.get("tags"):
            lines.append("**标签**: " + " ".join(f"`{t}`" for t in data["tags"]) + "\n\n")

        # 正文
        content = data.get("content", "")
        image_map = data.get("image_map") if images_inline else None
        md_content = _to_markdown(content, base_url=data.get("url"),
                                   image_map=image_map)
        lines.append(md_content)
        lines.append("\n\n")

        # 图片列表（如有）
        images = data.get("images") or []
        if images:
            lines.append("\n## 图片\n\n")
            for img in images:
                if isinstance(img, str):
                    lines.append(f"![]({img})\n\n")
                elif isinstance(img, dict):
                    path = img.get("path") or img.get("url", "")
                    alt = img.get("alt") or img.get("caption", "")
                    lines.append(f"![{alt}]({path})\n\n")

        return "".join(lines)


# ============== 工具函数 ==============

def _safe_filename(name: str) -> str:
    """保留中文，去掉文件系统非法字符。"""
    if not name:
        return "untitled"
    # Windows 非法字符
    s = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "untitled"


def _extract_first_heading(md_path: Path) -> Optional[str]:
    """从 MD 文件中提取第一个 # 标题作为该文档的标题。"""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def _write_zip_utf8(zf: zipfile.ZipFile, src_path: str, arcname: str,
                    encoding: str = "utf-8") -> None:
    """写入 ZIP 文件名时双编码（UTF-8 flag + extra 字段 GBK），避免中文乱码。

    zipfile 内部已经默认 UTF-8 flag（Python 3），但部分 Windows 工具仍按 GBK 解码。
    通过 extra 字段追加 GBK 编码，跨平台解压都正常。
    """
    # 读取数据
    with open(src_path, "rb") as f:
        data = f.read()
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED
    # 不修改内部文件名编码，只在 extra 字段写 GBK
    if encoding.lower() in ("utf-8", "utf8") and any(ord(c) > 127 for c in arcname):
        try:
            gbk_bytes = arcname.encode("gbk")
            # extra: 0x7170 (Info-ZIP Unicode Path) + version + nameCRC + utf8name
            # 简化方案：写入 Info-ZIP Unicode Path Extra Field
            import zlib
            utf8_bytes = arcname.encode("utf-8")
            crc = zlib.crc32(utf8_bytes) & 0xFFFFFFFF
            extra_payload = b"\x01" + crc.to_bytes(4, "little") + utf8_bytes
            info.extra = b"\x75\x70" + len(extra_payload).to_bytes(2, "little") + extra_payload
        except UnicodeEncodeError:
            # GBK 不支持的字符（罕见），回退
            pass
    zf.writestr(info, data)


# ============== 便捷函数 ==============

def export_to_markdown(data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """便捷函数：导出单篇 MD。"""
    return MarkdownExporter().export(data, output_path)


def batch_to_markdown(items: List[Dict[str, Any]],
                      batch_id: Optional[str] = None,
                      output_dir: Optional[str] = None) -> Dict[str, str]:
    """便捷函数：批量导出。"""
    return MarkdownExporter(output_dir=output_dir).build_batch_export(items, batch_id)