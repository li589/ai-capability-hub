"""PDF 和图像加载工具。

提供统一的 PDF（pypdfium2）和图像文件加载接口。
"""
from __future__ import annotations

from pathlib import Path
from typing import Generator, Tuple

from PIL import Image
from loguru import logger

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
_PDF_EXT = {".pdf"}


def _render_pdf(
    pdf_path: str | Path, 
    dpi: int = 150, 
) -> Generator[Image.Image, None, None]:
    """使用 pypdfium2 将 PDF 逐页渲染为 PIL Image（惰性生成器）。
    
    逐页渲染而非一次性渲染所有页面，配合 pipeline 的预取机制可实现
    渲染与 VLM 推理并行，显著降低首页延迟和内存峰值。
    
    Parameters
    ----------
    pdf_path : PDF文件路径
    dpi      : 渲染分辨率（150是推荐平衡值）
    
    Yields
    ------
    Image.Image: 每页的 PIL Image（RGB 模式）
    """
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ImportError("pypdfium2 未安装，请运行: pip install pypdfium2")

    pdf_path = str(pdf_path)
    doc = pdfium.PdfDocument(pdf_path)
    scale = dpi / 72.0
    
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            bitmap = page.render(scale=scale, rotation=0)
            pil_image = bitmap.to_pil()
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            yield pil_image
    finally:
        doc.close()


def load_images_from_path(
    input_path: str | Path,
    dpi: int = 150,
) -> Generator[Tuple[str, int, Image.Image], None, None]:
    """
    从输入路径加载图像，逐个 yield (来源文件路径, 页码/帧号, PIL Image)。

    参数
    ----
    input_path : 文件路径（PDF/图像）或目录路径
    dpi        : PDF 渲染分辨率

    Yields
    ------
    (source_path, page_index, pil_image)
    """
    path = Path(input_path)

    if path.is_dir():
        files = sorted(path.iterdir())
        for fp in files:
            if fp.suffix.lower() in _IMAGE_EXTS or fp.suffix.lower() in _PDF_EXT:
                yield from load_images_from_path(fp, dpi)
    elif path.suffix.lower() in _PDF_EXT:
        logger.info("渲染 PDF: {} (DPI={})", path.name, dpi)
        for idx, page_img in enumerate(_render_pdf(path, dpi)):
            yield str(path), idx, page_img
    elif path.suffix.lower() in _IMAGE_EXTS:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        yield str(path), 0, img
    else:
        logger.warning("不支持的文件类型，已跳过: {}", path)
