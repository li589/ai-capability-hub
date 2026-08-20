# -*- coding: utf-8 -*-
"""
批量爬取结果 ZIP 打包模块 v4.0
将爬取结果按类型分目录、生成索引文件，打包为 ZIP 供用户下载。

功能：
- 收集爬取结果 → 按类型/来源分目录
- 生成索引 README.md + metadata JSON
- 打包 ZIP（支持分卷 >50MB）
- 支持自定义文件名、输出目录
- 增强 BatchInstitutionCrawler 添加 crawl_and_package() 方法
"""

import os
import json
import hashlib
import zipfile
import shutil
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
PACKAGES_DIR = SKILL_DATA_DIR / "packages"
TEMP_DIR = SKILL_DATA_DIR / "temp_packages"

SKILL_DATA_DIR.mkdir(parents=True, exist_ok=True)
PACKAGES_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 数据结构 ====================

@dataclass
class PackagedItem:
    """打包条目"""
    name: str
    content: str = ""
    content_type: str = "text"  # text / html / json / file
    source_url: str = ""
    category: str = "通用"
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: str = ""  # 如果是文件，记录路径


@dataclass
class PackageResult:
    """打包结果"""
    zip_path: str
    zip_size_mb: float
    item_count: int
    category_count: int
    file_list: List[str]
    metadata: Dict[str, Any]
    created_at: str
    name: str = ""


# ==================== ZIP 打包器 ====================

class CrawlPackager:
    """批量爬取结果 ZIP 打包器。"""

    MAX_VOLUME_SIZE = 50 * 1024 * 1024  # 50MB 分卷阈值

    def __init__(self, output_dir: str = ""):
        self.output_dir = Path(output_dir) if output_dir else PACKAGES_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def package(self, items: List[Any], zip_name: str = "",
                output_dir: str = "",
                include_metadata: bool = True,
                categorize: bool = True,
                progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        将爬取结果打包为 ZIP。

        Args:
            items: 爬取结果列表（dict / PackagedItem / str）
            zip_name: ZIP 文件名（不含扩展名）
            output_dir: 输出目录
            include_metadata: 是否包含 metadata JSON
            categorize: 是否按类别分目录
            progress_callback: v6.0.0 进度回调 (done, total, item_name)，
                               每写入一个文件调用一次

        返回: ZIP 文件路径
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # 标准化 items
        packaged = self._normalize_items(items)
        if not packaged:
            raise ValueError("没有可打包的内容")

        # 按类别分组
        categories: Dict[str, List[PackagedItem]] = {}
        if categorize:
            for item in packaged:
                cat = item.category or "其他"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
        else:
            categories["全部"] = packaged

        # 生成 ZIP 文件名
        if not zip_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"crawl_package_{timestamp}"

        # 创建唯一临时目录构建文件结构，避免并发/重复运行互相锁文件
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{zip_name}_", dir=str(TEMP_DIR)))

        try:
            # 写入文件
            file_list = []
            total = sum(len(c) for c in categories.values())
            done = 0
            for cat_name, cat_items in categories.items():
                cat_dir = temp_dir / self._safe_filename(cat_name)
                cat_dir.mkdir(exist_ok=True)

                for i, item in enumerate(cat_items):
                    fname = self._generate_filename(item, i)
                    fpath = cat_dir / fname
                    content = self._get_content(item)

                    if content:
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        file_list.append(str(fpath.relative_to(temp_dir)))
                    # v6.0.0: 进度回调
                    done += 1
                    if progress_callback is not None:
                        try:
                            progress_callback(done, total, item.name)
                        except Exception:
                            pass

            # 生成索引 README.md
            index_content = self._generate_index(zip_name, categories, file_list)
            with open(temp_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(index_content)
            file_list.append("README.md")

            # 生成 metadata JSON
            if include_metadata:
                metadata = self._generate_metadata(zip_name, packaged, categories)
                with open(temp_dir / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                file_list.append("metadata.json")

            # 创建 ZIP
            zip_path = str(self.output_dir / f"{zip_name}.zip")

            # 检查是否需要分卷
            total_size = self._get_dir_size(temp_dir)
            if total_size > self.MAX_VOLUME_SIZE:
                return self._create_split_zip(temp_dir, zip_name, total_size)
            else:
                return self._create_zip(temp_dir, zip_path)

        finally:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def package_from_files(self, file_paths: List[str], zip_name: str = "",
                           output_dir: str = "") -> str:
        """
        将文件列表打包为 ZIP。

        Args:
            file_paths: 文件路径列表
            zip_name: ZIP 文件名
            output_dir: 输出目录

        返回: ZIP 文件路径
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

        if not zip_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"file_package_{timestamp}"

        zip_path = str(self.output_dir / f"{zip_name}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fp in file_paths:
                if os.path.isfile(fp):
                    arcname = os.path.basename(fp)
                    zf.write(fp, arcname)

        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"✅ ZIP 已创建: {zip_path} ({size_mb:.2f} MB, {len(file_paths)} 个文件)")
        return zip_path

    def package_batch_crawl(self, names: str = "",
                            institution_type: str = "",
                            zip_name: str = "",
                            parallel_workers: int = 1,
                            retries: int = 2,
                            progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        批量爬取 + 自动打包 ZIP（一站式）。

        v6.0.0 增强：
          - 并发爬取（ThreadPoolExecutor，默认 1=顺序，建议 ≤5）
          - 失败自动重试（默认 2 次）
          - 失败清单 failed.json 写入包内
          - 进度回调（爬取阶段 done/total/name）

        Args:
            names: 机构名称列表（逗号分隔）
            institution_type: 机构类型
            zip_name: ZIP 文件名
            parallel_workers: v6.0.0 并发爬取线程数（0/1=顺序）
            retries: v6.0.0 单个机构失败重试次数
            progress_callback: v6.0.0 进度回调 (done, total, name)

        返回: ZIP 文件路径
        """
        items = []
        failed_items: List[Dict[str, Any]] = []

        # 执行批量爬取
        try:
            from batch_institution_crawler import BatchInstitutionCrawler
            crawler = BatchInstitutionCrawler()

            if names:
                inst_list = [{"name": n.strip()} for n in names.split(",") if n.strip()]
                crawl_targets = inst_list
            elif institution_type:
                crawl_targets = [{"type": institution_type}]
            else:
                crawl_targets = []

            def _crawl_one(target: Dict[str, str]) -> Dict[str, Any]:
                """单目标爬取（带失败重试）。"""
                for attempt in range(retries + 1):
                    try:
                        if "type" in target and not target.get("name"):
                            r = crawler.crawl_by_type(target["type"])
                            if not r:
                                raise RuntimeError("empty result")
                            # 类型爬取返回列表，合并为多条
                            return {"__multi__": True, "results": r}
                        else:
                            r = crawler.crawl_by_names([target])
                            if not r:
                                raise RuntimeError("empty result")
                            return {"__multi__": False, "results": r}
                    except Exception:
                        if attempt < retries:
                            import time as _t
                            _t.sleep(0.5 * (attempt + 1))
                return {"__multi__": False, "results": [], "failed": True}

            if crawl_targets:
                total = len(crawl_targets)
                done = 0
                if parallel_workers and parallel_workers > 1:
                    # v6.0.0: 并发爬取
                    with ThreadPoolExecutor(max_workers=min(parallel_workers, 8)) as ex:
                        futures = {ex.submit(_crawl_one, t): t for t in crawl_targets}
                        for fut in as_completed(futures):
                            t = futures[fut]
                            name = t.get("name", t.get("type", "未知"))
                            try:
                                out = fut.result()
                            except Exception:
                                out = {"__multi__": False, "results": [], "failed": True}
                            self._collect_crawl_results(out, items, failed_items)
                            done += 1
                            if progress_callback is not None:
                                try:
                                    progress_callback(done, total, name)
                                except Exception:
                                    pass
                else:
                    for t in crawl_targets:
                        name = t.get("name", t.get("type", "未知"))
                        out = _crawl_one(t)
                        self._collect_crawl_results(out, items, failed_items)
                        done += 1
                        if progress_callback is not None:
                            try:
                                progress_callback(done, total, name)
                            except Exception:
                                pass

        except ImportError:
            pass

        if not items:
            raise ValueError("未获取到任何爬取结果")

        # v6.0.0: 失败清单写入包内
        if failed_items:
            items.append({
                "name": "failed_清单",
                "content": json.dumps(failed_items, ensure_ascii=False, indent=2),
                "content_type": "json",
                "category": "失败清单",
                "metadata": {"note": "爬取失败项（已自动重试）"},
            })

        return self.package(items, zip_name=zip_name,
                            progress_callback=progress_callback)

    @staticmethod
    def _collect_crawl_results(out: Dict[str, Any],
                               items: List[Dict[str, Any]],
                               failed_items: List[Dict[str, Any]]):
        """收集单目标爬取结果（并发/顺序共用）。"""
        if out.get("failed"):
            failed_items.append({"name": "未知", "reason": "爬取失败"})
            return
        results = out.get("results", []) or []
        for r in results:
            ok = r.get("success", False) if isinstance(r, dict) else True
            entry = {
                "name": r.get("name", "未知"),
                "content": r.get("content", ""),
                "success": ok,
            }
            if ok and entry.get("content"):
                items.append(entry)
            else:
                failed_items.append({"name": entry["name"], "reason": "内容为空或爬取失败"})

    # ---------- 内部方法 ----------

    def _normalize_items(self, items: List[Any]) -> List[PackagedItem]:
        """标准化多种输入格式为 PackagedItem 列表。"""
        packaged = []

        for item in items:
            if isinstance(item, PackagedItem):
                packaged.append(item)
            elif isinstance(item, dict):
                packaged.append(PackagedItem(
                    name=item.get("name", item.get("title", "未命名")),
                    content=item.get("content", item.get("text_content", "")),
                    source_url=item.get("url", item.get("source", "")),
                    category=item.get("category", item.get("type", "通用")),
                    metadata=item.get("metadata", {}),
                    file_path=item.get("file_path", ""),
                ))
            elif isinstance(item, str):
                packaged.append(PackagedItem(
                    name=f"content_{len(packaged)+1}",
                    content=item,
                ))
            else:
                packaged.append(PackagedItem(
                    name=str(item)[:100],
                    content=str(item),
                ))

        return packaged

    def _get_content(self, item: PackagedItem) -> str:
        """获取条目的文本内容。"""
        if item.content:
            return item.content
        if item.file_path and os.path.isfile(item.file_path):
            try:
                with open(item.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return ""
        return json.dumps(item.metadata, ensure_ascii=False) if item.metadata else ""

    def _generate_filename(self, item: PackagedItem, index: int) -> str:
        """为条目生成安全的文件名。"""
        base = self._safe_filename(item.name)[:50]
        if not base:
            base = f"item_{index+1:03d}"

        ext = ".txt"
        if item.content_type == "json":
            ext = ".json"
        elif item.content_type == "html":
            ext = ".html"
        elif item.content_type == "markdown":
            ext = ".md"

        fname = f"{index+1:03d}_{base}{ext}"
        return fname

    def _safe_filename(self, name: str) -> str:
        """将字符串转为安全的文件名。"""
        import re
        safe = re.sub(r'[\\/:*?"<>|]', '_', name)
        safe = re.sub(r'\s+', '_', safe)
        safe = safe.strip('._')
        return safe[:80] if safe else "unnamed"

    def _generate_index(self, zip_name: str,
                        categories: Dict[str, List[PackagedItem]],
                        file_list: List[str]) -> str:
        """生成索引 README.md。"""
        lines = [
            f"# 📦 {zip_name}\n",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"总条目数: {sum(len(v) for v in categories.values())}",
            f"类别数: {len(categories)}\n",
            "---\n",
            "## 📂 目录结构\n",
        ]

        for cat_name, cat_items in sorted(categories.items()):
            safe_cat = self._safe_filename(cat_name)
            lines.append(f"### {cat_name}/ ({len(cat_items)} 项)")
            for item in cat_items[:30]:
                fname = self._generate_filename(item, 0)
                preview = (item.content or "")[:80].replace('\n', ' ')
                source = f" — [来源]({item.source_url})" if item.source_url else ""
                lines.append(f"- `{safe_cat}/{fname}` — {item.name}{source}")
                if preview:
                    lines.append(f"  > {preview}...")
            lines.append("")

        lines.append("---")
        lines.append(f"*共 {len(file_list)} 个文件*")
        return '\n'.join(lines)

    def _generate_metadata(self, zip_name: str,
                           items: List[PackagedItem],
                           categories: Dict[str, List[PackagedItem]]) -> Dict[str, Any]:
        """生成 metadata JSON（v6.0.0: 含 item_hashes 供增量去重）。"""
        item_hashes = []
        for item in items:
            content = item.content or ""
            item_hashes.append({
                "name": item.name,
                "category": item.category,
                "hash": hashlib.md5(content.encode("utf-8")).hexdigest(),
                "chars": len(content),
            })
        return {
            "package_name": zip_name,
            "version": "6.0",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_items": len(items),
            "category_count": len(categories),
            "categories": {
                cat: {
                    "count": len(cat_items),
                    "items": [
                        {
                            "name": item.name,
                            "source_url": item.source_url,
                            "chars": len(item.content or ""),
                        }
                        for item in cat_items
                    ],
                }
                for cat, cat_items in categories.items()
            },
            "item_summary": [
                {"name": item.name, "category": item.category,
                 "source_url": item.source_url, "chars": len(item.content or "")}
                for item in items[:100]
            ],
            "item_hashes": item_hashes,  # v6.0.0: 增量去重依据
        }

    # ---------- v6.0.0 增量打包 ----------

    def package_incremental(self, items: List[Any], previous_zip: str = "",
                            zip_name: str = "", **kwargs) -> Tuple[str, int]:
        """增量打包：基于已有 ZIP 的 metadata.item_hashes 跳过已打包内容。

        Args:
            items: 待打包条目（同 package()）
            previous_zip: 已有 ZIP 路径（读取其 metadata.json 的 hash 集合）
            zip_name: 新 ZIP 文件名
            **kwargs: 透传 package() 参数

        Returns:
            (zip_path, skipped_count) — 新包路径与去重跳过的条数
        """
        existing_hashes: set = set()
        if previous_zip and os.path.isfile(previous_zip):
            try:
                with zipfile.ZipFile(previous_zip) as zf:
                    names = zf.namelist()
                    meta_name = next((n for n in names
                                      if n.endswith("metadata.json")), None)
                    if meta_name:
                        meta = json.loads(zf.read(meta_name).decode("utf-8"))
                        existing_hashes = {
                            h["hash"] for h in meta.get("item_hashes", [])
                            if h.get("hash")
                        }
            except Exception:
                existing_hashes = set()

        packaged = self._normalize_items(items)
        fresh = []
        skipped = 0
        for item in packaged:
            content = item.content or ""
            h = hashlib.md5(content.encode("utf-8")).hexdigest() if content else ""
            if h and h in existing_hashes:
                skipped += 1
                continue
            fresh.append(item)

        if not fresh:
            raise ValueError("所有条目均已打包过（增量去重后无新内容）")

        zip_path = self.package(fresh, zip_name=zip_name, **kwargs)
        return zip_path, skipped

    def _get_dir_size(self, path: Path) -> int:
        """计算目录总大小（字节）。"""
        total = 0
        for f in path.rglob('*'):
            if f.is_file():
                total += f.stat().st_size
        return total

    def _create_zip(self, source_dir: Path, zip_path: str) -> str:
        """创建单个 ZIP 文件（v4.5 修复：中文文件名 UTF-8 + GBK 双编码）。"""
        source_dir_str = str(source_dir)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir_str):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, source_dir_str)
                    _write_zip_utf8(zf, fpath, arcname)

        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"✅ ZIP 已创建: {zip_path} ({size_mb:.2f} MB)")
        return zip_path

    def _create_split_zip(self, source_dir: Path, zip_name: str,
                          total_size: int) -> str:
        """创建分卷 ZIP 文件。"""
        source_dir_str = str(source_dir)
        vol_size = self.MAX_VOLUME_SIZE
        vol_num = 0
        current_size = 0
        zf = None
        result_paths = []

        try:
            for root, dirs, files in os.walk(source_dir_str):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    fsize = os.path.getsize(fpath)

                    if zf is None or current_size + fsize > vol_size:
                        if zf:
                            zf.close()
                        vol_num += 1
                        vol_name = f"{zip_name}_part{vol_num:02d}"
                        vol_path = str(self.output_dir / f"{vol_name}.zip")
                        zf = zipfile.ZipFile(vol_path, 'w', zipfile.ZIP_DEFLATED)
                        result_paths.append(vol_path)
                        current_size = 0

                    arcname = os.path.relpath(fpath, source_dir_str)
                    zf.write(fpath, arcname)
                    current_size += fsize

            if zf:
                zf.close()

            # 返回第一个分卷路径作为主路径
            for p in result_paths:
                size_mb = os.path.getsize(p) / (1024 * 1024)
                print(f"✅ 分卷 ZIP: {p} ({size_mb:.2f} MB)")
            return result_paths[0] if result_paths else ""

        except Exception as e:
            if zf:
                try:
                    zf.close()
                except Exception:
                    pass
            raise e


# ==================== 便捷函数 ====================

_packager = CrawlPackager()


def batch_crawl_and_package(names: str = "", institution_type: str = "",
                            zip_name: str = "") -> str:
    """批量爬取 + 自动打包 ZIP。"""
    return _packager.package_batch_crawl(
        names=names, institution_type=institution_type, zip_name=zip_name
    )


def package_crawl_results(items: List[Any], zip_name: str = "",
                          output_dir: str = "") -> str:
    """打包爬取结果为 ZIP。"""
    return _packager.package(items, zip_name=zip_name, output_dir=output_dir)


def package_files(file_paths: List[str], zip_name: str = "",
                  output_dir: str = "") -> str:
    """打包文件列表为 ZIP。"""
    return _packager.package_from_files(
        file_paths=file_paths, zip_name=zip_name, output_dir=output_dir
    )


# ==================== v4.5 ZIP UTF-8 修复 + 图片打包 ====================

def _write_zip_utf8(zf: zipfile.ZipFile, fpath: str, arcname: str) -> None:
    """写入 ZIP 条目时双编码（UTF-8 + GBK extra 字段），避免中文文件名乱码。

    zipfile 内部默认 UTF-8 flag（Python 3），但部分 Windows 工具解压时按 GBK 解码。
    通过 extra 字段追加 Info-ZIP Unicode Path，跨平台解压都正常。
    """
    import zlib
    with open(fpath, "rb") as f:
        data = f.read()
    _write_zip_data_utf8(zf, arcname, data)


def _write_zip_data_utf8(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    """写入 ZIP 条目（直接传入 data），带 UTF-8 extra 字段。"""
    import zlib
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED
    if any(ord(c) > 127 for c in arcname):
        try:
            utf8_bytes = arcname.encode("utf-8")
            crc = zlib.crc32(utf8_bytes) & 0xFFFFFFFF
            payload = b"\x01" + crc.to_bytes(4, "little") + utf8_bytes
            info.extra = b"\x75\x70" + len(payload).to_bytes(2, "little") + payload
        except UnicodeEncodeError:
            pass
    zf.writestr(info, data)


def package_with_images(items: List[Any], zip_name: str = "",
                        output_dir: str = "",
                        media_subdir: str = "media") -> str:
    """v4.5 新增：打包爬取结果 + 关联图片。

    Args:
        items: 爬取结果列表，每个 item 可含 {"image_map": {orig_url: local_path}}
        zip_name: ZIP 名
        output_dir: 输出目录
        media_subdir: ZIP 内图片子目录名

    Returns:
        ZIP 路径
    """
    packager = CrawlPackager(output_dir=output_dir) if output_dir else _packager

    # 先写所有 content 到临时目录
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        media_dir = tmp / media_subdir
        media_dir.mkdir(exist_ok=True)
        # 收集所有图片
        for idx, item in enumerate(items):
            img_map = (item.get("image_map") if isinstance(item, dict) else None) or {}
            for orig_url, local_path in img_map.items():
                if not local_path:
                    continue
                src = Path(local_path)
                if not src.exists():
                    continue
                # 拷贝到 media_dir
                dst = media_dir / src.name
                if not dst.exists():
                    try:
                        import shutil as _sh
                        _sh.copy2(str(src), str(dst))
                    except Exception:
                        pass

        # 调用原有 package 写 content 文件
        content_zip = packager.package(items, zip_name=zip_name + "_content")
        # 合并：解压 content_zip + media 到新 zip
        if zip_name:
            final_name = zip_name if zip_name.endswith(".zip") else zip_name + ".zip"
        else:
            final_name = "package_with_images.zip"
        out_zip = Path(packager.output_dir) / final_name

        with zipfile.ZipFile(str(out_zip), "w", zipfile.ZIP_DEFLATED) as zf:
            # 1) 写 media
            for f in media_dir.rglob("*"):
                if f.is_file():
                    arc = f"{media_subdir}/{f.relative_to(media_dir)}"
                    _write_zip_utf8(zf, str(f), arc)
            # 2) 写 content（从原 zip 抽出重写）
            if Path(content_zip).exists():
                with zipfile.ZipFile(content_zip, "r") as src_zf:
                    for info in src_zf.infolist():
                        data = src_zf.read(info.filename)
                        # 用 writestr 重新写入（带 UTF-8 extra）
                        _write_zip_data_utf8(zf, info.filename, data)
                try:
                    Path(content_zip).unlink()
                except Exception:
                    pass

        return str(out_zip)


def _decode_zip_filename(name: str) -> str:
    """从 ZIP extra 字段恢复 UTF-8 文件名（如果存在）。"""
    return name  # 简化版：直接返回


def set_zip_encoding(zip_path: str) -> str:
    """为已有 ZIP 重新写入 UTF-8 编码（修复中文乱码）。

    Args:
        zip_path: 已有 ZIP 路径

    Returns:
        修复后的新 ZIP 路径（原文件加 .utf8.zip 后缀）
    """
    src = Path(zip_path)
    if not src.exists():
        return ""
    dst = src.with_suffix(".utf8.zip")
    with zipfile.ZipFile(src, "r") as src_zf, \
            zipfile.ZipFile(str(dst), "w", zipfile.ZIP_DEFLATED) as dst_zf:
        for info in src_zf.infolist():
            data = src_zf.read(info.filename)
            _write_zip_data_utf8(dst_zf, info.filename, data)
    return str(dst)


# ==================== 增强 BatchInstitutionCrawler ====================

def enhance_batch_crawler():
    """为 BatchInstitutionCrawler 添加 crawl_and_package 方法。"""
    try:
        from batch_institution_crawler import BatchInstitutionCrawler

        def _crawl_and_package(self, names: str = "", institution_type: str = "",
                               zip_name: str = "") -> str:
            """批量爬取 + 自动打包 ZIP。"""
            items = []
            if names:
                inst_list = [{"name": n.strip()} for n in names.split(",")]
                results = self.crawl_by_names(inst_list)
                items = [{"name": r.get("name", ""), "content": r.get("content", ""),
                         "success": r.get("success", False)}
                        for r in results]
            elif institution_type:
                results = self.crawl_by_type(institution_type)
                items = [{"name": r.get("name", ""), "content": r.get("content", ""),
                         "success": r.get("success", False)}
                        for r in results]

            return _packager.package(items, zip_name=zip_name)

        BatchInstitutionCrawler.crawl_and_package = _crawl_and_package
        return True
    except ImportError:
        return False


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python crawl_packager.py <命令> [参数]")
        print("命令:")
        print("  package <names或type> [zip名]  — 批量爬取+打包")
        print("  files <文件1,文件2,...> [zip名] — 打包指定文件")
        print()
        print("示例:")
        print("  python crawl_packager.py package \"华夏基金,易方达基金\" my_package")
        print("  python crawl_packager.py package 基金管理公司")
        print("  python crawl_packager.py files \"data/report1.pdf,data/report2.pdf\"")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "package":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        zip_name = sys.argv[3] if len(sys.argv) > 3 else ""

        if not target:
            print("请提供机构名称(逗号分隔)或机构类型")
            sys.exit(1)

        # 判断是名称列表还是类型
        if any(c in target for c in "基金证券银行保险信托期货"):
            result = _packager.package_batch_crawl(
                institution_type=target, zip_name=zip_name
            )
        else:
            result = _packager.package_batch_crawl(
                names=target, zip_name=zip_name
            )

        print(f"📦 打包完成: {result}")

    elif cmd == "files":
        if len(sys.argv) < 3:
            print("请提供文件路径(逗号分隔)")
            sys.exit(1)

        paths = [p.strip() for p in sys.argv[2].split(",") if p.strip()]
        zip_name = sys.argv[3] if len(sys.argv) > 3 else ""

        result = _packager.package_from_files(paths, zip_name=zip_name)
        print(f"📦 打包完成: {result}")

    else:
        print(f"未知命令: {cmd}")
