"""公共工具函数：图像处理、文件操作等。

此模块集中管理项目中重复使用的工具函数，确保代码一致性。
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Union

import numpy as np
import openvino as ov
from PIL import Image
from loguru import logger


ImageInput = Union[Image.Image, str, Path, bytes]


def crop_image_from_bbox(
    page_img: Image.Image,
    bbox: list[float] | tuple[float, float, float, float],
    margin: int = 0,
) -> Image.Image | None:
    """根据归一化坐标裁剪图像区域。

    Parameters
    ----------
    page_img  : PIL Image 对象
    bbox      : 归一化坐标 [x1, y1, x2, y2]，值为 0.0-1.0
    margin    : 裁剪边距（像素）

    Returns
    -------
    PIL.Image | None: 裁剪后的图像，失败时返回 None
    """
    if len(bbox) != 4:
        logger.warning("无效的 bbox 格式: {}", bbox)
        return None

    try:
        w, h = page_img.size
        x1, y1, x2, y2 = bbox
        x1, x2 = int(x1 * w), int(x2 * w)
        y1, y2 = int(y1 * h), int(y2 * h)

        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)

        if x2 <= x1 or y2 <= y1:
            logger.warning("裁剪区域无效: x1={}, x2={}, y1={}, y2={}", x1, x2, y1, y2)
            return None

        return page_img.crop((x1, y1, x2, y2))
    except Exception as e:
        logger.warning("图像裁剪失败: {}", e)
        return None


def save_image(
    image: Image.Image,
    output_path: Path | str,
    format: str = "PNG",
    **kwargs,
) -> Path | None:
    """保存图像到文件。

    Parameters
    ----------
    image       : PIL Image 对象
    output_path : 输出文件路径
    format      : 图像格式（PNG, JPEG 等）
    **kwargs    : PIL save() 额外参数

    Returns
    -------
    Path | None: 成功返回保存路径，失败返回 None
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path), format=format, **kwargs)
        return path
    except Exception as e:
        logger.warning("保存图像失败 {}: {}", output_path, e)
        return None


def load_image(src: ImageInput) -> Image.Image:
    """从多种输入格式加载 PIL Image。

    Parameters
    ----------
    src : Image.Image, bytes, str, Path

    Returns
    -------
    Image.Image: PIL Image对象（不强制转换RGB，由调用方决定是否转换）
    """
    if isinstance(src, Image.Image):
        return src
    if isinstance(src, (bytes, bytearray)):
        return Image.open(io.BytesIO(src))
    return Image.open(str(src))


MIN_VLM_IMAGE_SIZE = 28  # Qwen2VL visual encoder 要求的最小尺寸


def pil_to_ov_tensor(image: Image.Image) -> ov.Tensor:
    """将 PIL Image 转换为 VLMPipeline 期望的 ov.Tensor (NHWC, uint8)。

    优化策略（v20）：
    - 先 convert("RGB") 确保内存连续，再用 np.asarray 零拷贝
    - 避免对非 RGB 图像使用 np.array 拷贝
    - 自动 padding 过小的图片以满足 Qwen2VL 视觉编码器最小尺寸要求

    Parameters
    ----------
    image : PIL Image 对象

    Returns
    -------
    ov.Tensor: 形状为 (1, H, W, 3) 的 NHWC 批次张量，dtype=uint8
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
    w, h = image.size
    if h < MIN_VLM_IMAGE_SIZE or w < MIN_VLM_IMAGE_SIZE:
        new_w = max(w, MIN_VLM_IMAGE_SIZE)
        new_h = max(h, MIN_VLM_IMAGE_SIZE)
        padded = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        padded.paste(image, (0, 0))
        image = padded
    arr = np.asarray(image, dtype=np.uint8)
    if arr.ndim == 3:
        arr = arr[None, ...]
    return ov.Tensor(arr)


def image_to_base64(image: Image.Image, format: str = "JPEG", quality: int = 88) -> str:
    """将 PIL Image 转换为 base64 编码字符串。

    Parameters
    ----------
    image   : PIL Image 对象
    format  : 图像格式（JPEG, PNG 等）
    quality : JPEG 质量（仅对 JPEG 有效）

    Returns
    -------
    str: base64 编码的图像数据（不含前缀）
    """
    buf = io.BytesIO()
    image.save(buf, format=format, quality=quality)
    import base64
    return base64.b64encode(buf.getvalue()).decode()


def image_to_thumbnail(
    image: Image.Image,
    max_size: tuple[int, int] = (1200, 1200),
) -> Image.Image:
    """生成图像缩略图。

    Parameters
    ----------
    image   : PIL Image 对象
    max_size: 最大尺寸 (width, height)

    Returns
    -------
    PIL.Image: 缩略图
    """
    img = image.copy()
    img.thumbnail(max_size, Image.LANCZOS)
    return img


def ensure_directory(path: Path | str, name: str = "目录") -> Path:
    """确保目录存在，不存在则创建。

    Parameters
    ----------
    path : 目录路径
    name : 目录名称（用于日志）

    Returns
    -------
    Path: 已创建的目录路径
    """
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        logger.debug("创建 {}: {}", name, p)
    return p
