"""MinerU-OV Pipeline：统一入口，整合 PDF 解析、VLM 推理与后处理。"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from pathlib import Path
from typing import Callable, Optional

import functools

from loguru import logger
from .config import OVConfig
from .utils import crop_image_from_bbox, ensure_directory, save_image
from .vlm_backend import create_ov_vlm_client


def _create_backend(cfg: OVConfig):
    """根据配置创建推理后端 (VLM 或 Hybrid)。"""
    if cfg.backend_type == "hybrid":
        from .hybrid_backend import OVHybridClient
        from .pipeline_models import OVLayoutModel, OVMFRModel, OVOCREngine

        vlm_client = create_ov_vlm_client(cfg)

        ov_dir = cfg.model_dir
        layout_model = OVLayoutModel(
            str(ov_dir / "PP-DocLayoutV2"), device=cfg.device.split(":")[0]
        )
        mfr_model = OVMFRModel(
            str(ov_dir / "unimernet_hf_small_2503"), device=cfg.device.split(":")[0]
        )
        ocr_engine = OVOCREngine(
            str(ov_dir / "PP-OCRv5"), device=cfg.device.split(":")[0]
        )

        backend = OVHybridClient(
            vlm_client=vlm_client,
            layout_model=layout_model,
            mfr_model=mfr_model,
            ocr_engine=ocr_engine,
            enable_hybrid=True,
        )
        logger.info("Created hybrid backend (VLM + pipeline models)")
        return backend
    else:
        return create_ov_vlm_client(cfg)


class MinerUPipeline:
    """MinerU + OpenVINO 文档解析 Pipeline。"""

    def __init__(self, cfg: OVConfig):
        self.cfg = cfg
        self.client = _create_backend(cfg)

    def process_image(
        self,
        image,
        not_extract_list: Optional[list] = None,
        image_analysis: Optional[bool] = None,
        pause_check: Optional[Callable[[], bool]] = None,
    ):
        """对单张图像进行版面分析与内容提取。"""
        if pause_check is not None and pause_check():
            return []
        blocks = self.client.two_step_extract(
            image,
            not_extract_list=not_extract_list,
            image_analysis=image_analysis if image_analysis is not None else self.cfg.image_analysis,
            pause_check=pause_check,
        )
        if pause_check is not None and pause_check():
            return []
        return list(blocks)

    def process_pdf(
        self,
        input_path: str | Path,
        output_dir: str | Path = "output",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        not_extract_list: Optional[list] = None,
        image_analysis: Optional[bool] = None,
        save_images: bool = True,
        original_filename: Optional[str] = None,
        pause_check: Optional[Callable[[], bool]] = None,
    ) -> tuple[str, int]:
        """完整文档解析流程。

        Parameters
        ----------
        input_path        : 输入 PDF / 图像 / 目录
        output_dir        : 输出目录（自动创建）
        progress_callback : 进度回调 (current, total, message)
        not_extract_list  : 要跳过提取的区块类型列表
        image_analysis    : 是否对图片/图表区块进行分析识别
        save_images       : 是否保存图片区块到 images 子目录
        original_filename : 原始文件名（用于日志显示）

        Returns
        -------
        (markdown_content, page_count)
        """
        from .pdf_utils import load_images_from_path

        logger.info("─" * 60)
        output_dir = ensure_directory(output_dir, "输出目录")

        t_start = time.time()

        pages_iter = load_images_from_path(input_path, self.cfg.pdf_dpi)

        try:
            first = next(pages_iter)
        except StopIteration:
            logger.warning("未找到任何可处理的图像/PDF 页面")
            return "", 0

        display_filename = original_filename if original_filename else first[0]
        logger.info("推理设备: {}, 批处理模式: {}", self.cfg.device, self.cfg.use_batch_backend)
        logger.info("开始解析: {} -> {}", display_filename, output_dir)

        total = _count_pages_if_possible(input_path)
        source_name = Path(input_path).stem
        images_dir = ensure_directory(output_dir / "images", "图片目录") if save_images else None

        # ── Batch 后端路径：两阶段批处理 ──
        if self.cfg.use_batch_backend and hasattr(self.client, "batch_process_pages"):
            all_page_data = list(chain([first], pages_iter))
            total = len(all_page_data)
            page_images = [img for _, _, img in all_page_data]

            if progress_callback:
                progress_callback(0, total, "渲染页面完成，开始批处理解析...")
            logger.info("Batch processing {} pages — Phase 1/2: layout + Phase 2/2: extraction", total)

            all_blocks = self.client.batch_process_pages(
                page_images,
                progress_callback=progress_callback,
                not_extract_list=not_extract_list,
                image_analysis=image_analysis,
            )

            page_results = []
            md_parts = []
            for page_idx, ((src, p_idx, page_img), blocks) in enumerate(zip(all_page_data, all_blocks)):
                if pause_check is not None and pause_check():
                    logger.info("收到暂停信号，停止后续页处理")
                    break
                if save_images:
                    page_md = self._page_blocks_to_markdown(
                        blocks, page_img, images_dir, source_name, p_idx
                    )
                else:
                    page_md = self._page_blocks_to_markdown(
                        blocks, None, None, source_name, p_idx
                    )
                if page_md.strip():
                    md_parts.append(page_md)
                page_results.append((src, p_idx, blocks))
                del page_img

            actual_total = len(page_results)
            markdown = "\n\n---\n\n".join(md_parts)

            md_path = output_dir / f"{source_name}.md"
            md_path.write_text(markdown, encoding="utf-8")

            elapsed = time.time() - t_start
            logger.info("解析完成！耗时 {:.1f}s", elapsed)
            if progress_callback:
                progress_callback(actual_total, actual_total, f"完成！耗时 {elapsed:.1f}s")
            return markdown, actual_total

        # ── 逐页串行/并行路径（OVMinerUClient） ──
        page_results = []
        md_parts = []
        pages_gen = chain([first], pages_iter)

        if progress_callback:
            progress_callback(0, total or 1, "页面渲染完成，开始逐页解析...")
        logger.info("Serial processing — processing pages individually")

        if self.cfg.parallel_pages > 1 and total and total > 1:
            page_data_list = list(pages_gen)
            total = len(page_data_list)
            logger.info("启用并行页处理: {} 个线程", self.cfg.parallel_pages)

            infer_lock = threading.Lock()

            def _parallel_pages(pages_chunk, base_idx):
                chunk_results = []
                for chunk_idx, (src, p_idx, page_img) in enumerate(pages_chunk):
                    if pause_check is not None and pause_check():
                        logger.info("收到暂停信号，停止并行处理")
                        break
                    i = base_idx + chunk_idx + 1
                    page_num_hint = f"/{total}"
                    msg = f"处理第 {i}{page_num_hint} 页"
                    logger.info(msg)

                    t_page = time.time()
                    try:
                        with infer_lock:
                            blocks = self.process_image(
                                page_img,
                                not_extract_list=not_extract_list,
                                image_analysis=image_analysis,
                                pause_check=pause_check,
                            )
                    except Exception as e:
                        logger.error("第 {} 页处理失败: {}", p_idx, e)
                        blocks = []

                    elapsed_page = time.time() - t_page
                    logger.info(
                        "第 {}/{} 页完成，耗时 {:.1f}s，{} 区块",
                        i, total, elapsed_page, len(blocks),
                    )

                    if save_images:
                        page_md = self._page_blocks_to_markdown(
                            blocks, page_img, images_dir, source_name, p_idx
                        )
                    else:
                        page_md = self._page_blocks_to_markdown(
                            blocks, None, None, source_name, p_idx
                        )
                    chunk_results.append((src, p_idx, blocks, page_md, i))
                    del page_img

                return chunk_results

            workers = min(self.cfg.parallel_pages, total)
            chunk_size = max(1, total // workers)

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                for w in range(workers):
                    start = w * chunk_size
                    end = start + chunk_size if w < workers - 1 else total
                    chunk = page_data_list[start:end]
                    futures.append(executor.submit(_parallel_pages, chunk, start))

                # 按提交顺序收集结果（不用 as_completed，避免乱序）
                all_chunk_results = []
                for future in futures:
                    all_chunk_results.extend(future.result())

            # 按页码排序，保证多线程下输出顺序正确
            all_chunk_results.sort(key=lambda x: x[4])

            for src, p_idx, blocks, page_md, page_i in all_chunk_results:
                if page_md.strip():
                    md_parts.append(page_md)
                page_results.append((src, p_idx, blocks))
        else:
            for page_idx, (source, p_idx, page_img) in enumerate(pages_gen):
                if pause_check is not None and pause_check():
                    logger.info("收到暂停信号，停止后续页处理")
                    break
                i = page_idx + 1
                page_num_hint = f"/{total}" if total else ""
                msg = f"处理第 {i}{page_num_hint} 页"
                logger.info(msg)
                if progress_callback:
                    progress_callback(i, total if total is not None else i, msg)

                t_page = time.time()
                try:
                    blocks = self.process_image(
                        page_img,
                        not_extract_list=not_extract_list,
                        image_analysis=image_analysis,
                        pause_check=pause_check,
                    )
                except Exception as e:
                    logger.error("第 {} 页处理失败: {}", p_idx, e)
                    blocks = []

                elapsed_page = time.time() - t_page
                logger.info(
                    "第 {}/{} 页完成，耗时 {:.1f}s，检测到 {} 个区块",
                    i, total or "?", elapsed_page, len(blocks),
                )

                if save_images:
                    page_md = self._page_blocks_to_markdown(
                        blocks, page_img, images_dir, source_name, p_idx
                    )
                else:
                    page_md = self._page_blocks_to_markdown(
                        blocks, None, None, source_name, p_idx
                    )
                if page_md.strip():
                    md_parts.append(page_md)

                page_results.append((source, p_idx, blocks))
                del page_img

        actual_total = len(page_results)

        if progress_callback:
            progress_callback(actual_total, actual_total, "后处理中...")

        markdown = "\n\n---\n\n".join(md_parts)

        md_path = output_dir / f"{source_name}.md"
        md_path.write_text(markdown, encoding="utf-8")

        elapsed = time.time() - t_start
        logger.info("解析完成！耗时 {:.1f}s", elapsed)

        if progress_callback:
            progress_callback(actual_total, actual_total, f"完成！耗时 {elapsed:.1f}s")

        return markdown, actual_total

    def unload(self):
        """释放 VLMPipeline 资源。"""
        if self.client:
            self.client.unload()
            self.client = None

    def _page_blocks_to_markdown(
        self,
        blocks: list,
        page_img,
        images_dir: Optional[Path],
        source_name: str,
        page_idx: int,
    ) -> str:
        """将单页的 ContentBlocks 转换为 Markdown，包含图片保存。"""
        lines = []
        img_counter = 0
        chart_counter = 0

        for block in blocks:
            btype = block.get("type", "")
            content = block.get("content", "")
            if content is None:
                content = ""
            bbox = block.get("bbox", [])

            if btype == "text" and content.strip():
                lines.append(content.strip())
                lines.append("")
            elif btype == "title":
                title_text = content.strip().replace("\n", " ")
                if title_text:
                    lines.append(f"## {title_text}")
                    lines.append("")
            elif btype == "table":
                table_caption = block.get("table_caption", "") or ""
                if table_caption:
                    lines.append(table_caption.strip())
                    lines.append("")
                lines.append(content)
                lines.append("")
            elif btype == "equation":
                lines.append(f"$$\n{content}\n$$")
                lines.append("")
            elif btype == "image" and len(bbox) == 4 and images_dir and page_img:
                img_filename = f"{source_name}_p{page_idx+1}_img{img_counter}.png"
                cropped = crop_image_from_bbox(page_img, bbox)
                if cropped:
                    save_image(cropped, images_dir / img_filename)
                image_caption = block.get("image_caption", "") or ""
                if image_caption:
                    lines.append(f"![{image_caption}](images/{img_filename})")
                else:
                    lines.append(f"![](images/{img_filename})")
                lines.append("")
                img_counter += 1
            elif btype == "chart" and len(bbox) == 4 and images_dir and page_img:
                chart_filename = f"{source_name}_p{page_idx+1}_chart{chart_counter}.png"
                cropped = crop_image_from_bbox(page_img, bbox)
                if cropped:
                    save_image(cropped, images_dir / chart_filename)
                chart_caption = block.get("chart_caption", "") or ""
                if chart_caption:
                    lines.append(f"![{chart_caption}](images/{chart_filename})")
                else:
                    lines.append(f"![](images/{chart_filename})")
                lines.append("")
                chart_counter += 1
            elif btype == "caption":
                caption_text = block.get("content", "") or ""
                if caption_text.strip():
                    lines.append(caption_text.strip())
                    lines.append("")
            elif btype == "code":
                lines.append(f"```\n{content}\n```")
            elif content.strip():
                lines.append(content.strip())

        return "\n".join(lines).strip()

    def load(self):
        """预加载模型（当前实现在 __init__ 中已完成）。"""
        pass

    def run(
        self,
        input_path: str | Path,
        output_dir: str | Path = "output",
        progress_callback=None,
        not_extract_list: Optional[list] = None,
        image_analysis: Optional[bool] = None,
        save_images: bool = True,
        original_filename: Optional[str] = None,
        pause_file: str = "",
    ) -> tuple[str, int]:
        """运行完整解析流程。"""
        pause_check: Optional[Callable[[], bool]] = None
        if pause_file:
            pause_file_path = Path(pause_file)
            pause_check = functools.partial(Path.exists, pause_file_path)
        return self.process_pdf(
            input_path=input_path,
            output_dir=output_dir,
            progress_callback=progress_callback,
            not_extract_list=not_extract_list,
            image_analysis=image_analysis,
            save_images=save_images,
            original_filename=original_filename,
            pause_check=pause_check,
        )


def _count_pages_if_possible(input_path: str | Path) -> int | None:
    """快速估算页面总数（不渲染全部页面）。"""
    path = Path(input_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(path))
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return None
    if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}:
        return 1
    return None
