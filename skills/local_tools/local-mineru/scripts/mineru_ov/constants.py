"""项目常量定义：支持的设备、精度、默认参数等。"""
from __future__ import annotations

from typing import Tuple


SUPPORTED_DEVICES: set[str] = {"CPU", "GPU", "NPU"}
SUPPORTED_PRECISIONS: set[str] = {"fp16", "int4"}
NPU_REQUIRED_PRECISION: str = "int4"

DEFAULT_LAYOUT_IMAGE_SIZE: Tuple[int, int] = (1036, 1036)
DEFAULT_MIN_IMAGE_EDGE: int = 8
DEFAULT_MAX_IMAGE_EDGE_RATIO: float = 4.0

# VLM 模型目录名称（位于 model_dir 下）
VLM_MODEL_BASENAME = "MinerU2.5-Pro-2605-1.2B"
VLM_MODEL_INT4_SUFFIX = "-int4"
DEFAULT_MAX_NEW_TOKENS: int = 2048
NPU_MAX_PROMPT_LEN: int = 4096
NPU_TIMEOUT_SECONDS: int = 600
DEFAULT_PDF_DPI: int = 150
DEFAULT_WEBUI_PORT: int = 7878

MINERU_OUTPUT_TOKENS: Tuple[str, ...] = (
    "<|box_start|>",
    "<|box_end|>",
    "<|ref_start|>",
    "<|ref_end|>",
    "<|rotate_up|>",
    "<|rotate_right|>",
    "<|rotate_down|>",
    "<|rotate_left|>",
    "<nl>",
    "<fcel>",
    "<ecel>",
    "<lcel>",
    "<ucel>",
    "<xcel>",
    "<ched>",
    "<|md_start|>",
    "<|md_end|>",
    "<|object_ref_start|>",
    "<|object_ref_end|>",
    "<|quad_start|>",
    "<|quad_end|>",
    "<|paratext|>",
    "<|txt_contd|>",
)

IMAGE_EXTS: set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXT: str = ".pdf"

SENTENCE_END_CHARS: set[str] = {"。", ".", "！", "!", "？", "?", "…", "」", "』", "）", ")"}
