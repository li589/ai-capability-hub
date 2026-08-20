"""Hybrid Backend：VLM + Pipeline 双引擎编排。

工作模式
--------
- VLM-Only 模式: 所有内容由 VLM 处理 (与原有 vlm_backend 行为一致)
- Hybrid 模式: VLM 处理版面布局 + 视觉内容 (image/table/equation/chart)，
                Pipeline 模型处理文本 OCR + 行内公式识别

参考 MinerU 源码:
  mineru/backend/hybrid/hybrid_analyze.py
  mineru/backend/hybrid/hybrid_magic_model.py
"""
from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 需要被 VLM 提取的区块类型 (visual content)
_VLM_EXTRACT_TYPES = {"image", "table", "equation", "chart", "code"}

# 各类型图表的 caption 字段名（参考 upstream MinerU content_list 规范）
IMAGE_CAPTION = "image_caption"
TABLE_CAPTION = "table_caption"
CHART_CAPTION = "chart_caption"

# Pipeline OCR 负责的区块类型 (text content)
_PIPELINE_OCR_TYPES = {"text", "title", "list", "header", "footer",
                       "paragraph_title", "doc_title", "aside_text",
                       "reference", "footnote", "page_number",
                       "page_footnote", "ref_text", "caption",
                       "content"}

# VLM 不做内容提取的区块类型（交给 pipeline OCR）
_NOT_EXTRACT_LIST = [
    "text", "title", "list", "header", "footer", "page_number",
    "ref_text", "page_footnote", "code", "caption", "footnote",
    "aside_text", "paragraph_title", "doc_title", "reference",
    "reference_content", "content", "number", "formula_number",
    "abstract", "algorithm", "vision_footnote",
]


def _mask_image_regions(
    image: np.ndarray, blocks: List[dict]
) -> np.ndarray:
    """将 IMAGE/TABLE/EQUATION/CHART 区域涂白。

    这些区域由 VLM 处理，Pipeline OCR 应跳过它们。

    Parameters
    ----------
    image : np.ndarray (H, W, 3)
    blocks : VLM layout blocks with "bbox" field

    Returns
    -------
    np.ndarray: masked image
    """
    masked = image.copy()
    h, w = image.shape[:2]
    for block in blocks:
        btype = block.get("type", "")
        if btype not in ("image", "table", "equation", "chart"):
            continue
        bbox = block.get("bbox")
        if bbox and len(bbox) == 4:
            x1 = max(0, int(bbox[0]))
            y1 = max(0, int(bbox[1]))
            x2 = min(w, int(bbox[2]))
            y2 = min(h, int(bbox[3]))
            if x2 > x1 and y2 > y1:
                masked[y1:y2, x1:x2] = 255
    return masked


def _normalize_bbox(bbox, img_w, img_h):
    xmin, ymin, xmax, ymax = [float(v) for v in bbox]
    xmin = max(0, min(img_w, int(xmin)))
    ymin = max(0, min(img_h, int(ymin)))
    xmax = max(0, min(img_w, int(xmax)))
    ymax = max(0, min(img_h, int(ymax)))
    if xmax <= xmin or ymax <= ymin:
        return None
    return [xmin, ymin, xmax, ymax]


def _build_formula_items(
    layout_boxes: List[dict], image: np.ndarray
) -> Tuple[List[dict], List[Tuple[dict, List[int]]]]:
    """从版面检测结果中提取行内/展示公式区域。

    Returns
    -------
    (formula_list, crop_targets)
      formula_list: 需要填充 latex 的公式项列表
      crop_targets: [(formula_item, [x1,y1,x2,y2]), ...]
    """
    h, w = image.shape[:2]
    formula_list = []
    crop_targets = []
    for item in layout_boxes:
        label = item.get("label", "")
        if label not in ("inline_formula", "display_formula"):
            continue
        formula_item = {"label": label, "latex": "", "bbox": item.get("bbox", [])}
        formula_list.append(formula_item)
        bbox = _normalize_bbox(formula_item["bbox"], w, h)
        if bbox is not None:
            crop_targets.append((formula_item, bbox))
    return formula_list, crop_targets


# ═══════════════════════════════════════════════════════════════════
# OVHybridClient
# ═══════════════════════════════════════════════════════════════════


class OVHybridClient:
    """Hybrid backend 主类。

    封装 OVMinerUClient + Pipeline 模型，提供两种模式:
      - VLM-Only: 纯 VLM 推理 (等效于 OVMinerUClient)
      - Hybrid: VLM + Pipeline 双引擎

    Parameters
    ----------
    vlm_client : OVMinerUClient
        已初始化的 VLM 客户端实例
    layout_model : OVLayoutModel, optional
        PP-DocLayoutV2 模型
    mfr_model : OVMFRModel, optional
        UniMerNet 公式识别模型
    ocr_engine : OVOCREngine, optional
        PP-OCRv5 检测+识别引擎
    enable_hybrid : bool
        True = hybrid 模式, False = VLM-only 模式
    """

    def __init__(
        self,
        vlm_client,
        layout_model=None,
        mfr_model=None,
        ocr_engine=None,
        enable_hybrid: bool = True,
    ):
        self._vlm = vlm_client
        self._layout = layout_model
        self._mfr = mfr_model
        self._ocr = ocr_engine
        self._enable_hybrid = enable_hybrid
        # _mineru_client 已移除——原来通过 getattr(vlm_client, "_client", None)
        # 获取，但 OVMinerUClient 没有该属性，始终为 None，导致 hybrid 模式失效。
        # 现在直接使用 self._vlm 调用 two_step_extract。

        logger.info(
            "OVHybridClient initialized (hybrid=%s, layout=%s, mfr=%s, ocr=%s)",
            enable_hybrid,
            "yes" if layout_model else "no",
            "yes" if mfr_model else "no",
            "yes" if ocr_engine else "no",
        )

    # ── VLM-Only 模式 ──────────────────────────────────────────

    def process_image_vlm_only(
        self, image, **kwargs
    ) -> Tuple[str, List[dict]]:
        """纯 VLM 模式处理单页图像。"""
        from mineru_vl_utils.post_process import json2md
        blocks = list(self._vlm.two_step_extract(image, **kwargs))
        return json2md(blocks), blocks

    def process_images_batch_vlm_only(
        self, images: List, **kwargs
    ) -> List[Tuple[str, List[dict]]]:
        """纯 VLM 模式批量处理。"""
        return [self.process_image_vlm_only(img, **kwargs) for img in images]

    def two_step_extract(
        self,
        image,
        not_extract_list=None,
        image_analysis=None,
        pause_check=None,
    ):
        """兼容 MinerUPipeline.process_image 的统一接口。

        返回 blocks 列表，与 OVMinerUClient.two_step_extract 行为一致。
        """
        if not self._enable_hybrid:
            return self._vlm.two_step_extract(
                image,
                not_extract_list=not_extract_list,
                image_analysis=image_analysis,
                pause_check=pause_check,
            )
        _, blocks = self._process_hybrid(
            image,
            image_analysis=image_analysis if image_analysis is not None else False,
        )
        return blocks

    # ── Hybrid 模式 ─────────────────────────────────────────────

    def _run_vlm_layout(self, image) -> Tuple[object, List[dict]]:
        """执行 VLM 版面分析，只获取区块位置（不提取内容）。

        直接调用 self._vlm.two_step_extract，传入 _NOT_EXTRACT_LIST
        使 VLM 跳过文本内容提取，只返回版面结构。
        """
        try:
            result = self._vlm.two_step_extract(
                image,
                not_extract_list=_NOT_EXTRACT_LIST,
            )
            return image, list(result)
        except Exception as e:
            logger.warning("VLM layout analysis failed: %s; falling back to VLM-only", e)
            return image, []

    def _run_vlm_visual_extraction(
        self, images: List
    ) -> List[List[dict]]:
        """对视觉内容 (image/table/equation/chart) 执行 VLM 提取。

        逐张调用 self._vlm.two_step_extract，不传 not_extract_list
        使 VLM 提取全部区块内容。
        """
        results = []
        for img in images:
            try:
                result = self._vlm.two_step_extract(img, not_extract_list=None)
                results.append(list(result))
            except Exception as e:
                logger.warning("VLM extraction failed for one image: %s", e)
                results.append([])
        return results

    def _run_pipeline_ocr(
        self, image: np.ndarray, layout_blocks: List[dict]
    ) -> Tuple[List[dict], List[dict]]:
        """执行 Pipeline OCR + MFR。

        步骤:
          1. 从 VLM layout blocks 中分离视觉块和文本块
          2. Mask 视觉块区域
          3. PP-DocLayoutV2 检测公式区域
          4. UniMerNet 识别公式
          5. PP-OCRv5 检测+识别文本

        Returns
        -------
        (ocr_blocks, formula_blocks)
          ocr_blocks: [{"type": "text", "bbox": [...], "content": str}, ...]
          formula_blocks: [{"label": str, "bbox": [...], "latex": str}, ...]
        """
        h, w = image.shape[:2]
        ocr_blocks: List[dict] = []
        formula_blocks: List[dict] = []

        # ── 1) Mask 视觉块区域 ─────────────────────────────────
        masked_image = _mask_image_regions(image, layout_blocks)

        # ── 2) PP-DocLayoutV2 检测公式区域 ─────────────────────
        mfd_res: List[dict] = []
        if self._layout is not None:
            try:
                mfd_res = self._layout.get_inline_formula_boxes(masked_image)
            except Exception as e:
                logger.debug("Layout detection error: %s", e)

        # ── 3) UniMerNet 识别公式 ──────────────────────────────
        if self._mfr is not None and mfd_res:
            try:
                formula_results = self._mfr.batch_predict(
                    [mfd_res], [masked_image], batch_size=8
                )
                if formula_results:
                    formula_blocks = [
                        f for f in formula_results[0] if f.get("latex")
                    ]
            except Exception as e:
                logger.debug("MFR inference error: %s", e)

        # ── 4) PP-OCRv5 检测 + 识别文本 ────────────────────────
        if self._ocr is not None:
            try:
                ocr_results = self._ocr.ocr_image(masked_image)
                for ocr_item in ocr_results:
                    if ocr_item.text.strip():
                        ocr_blocks.append({
                            "type": "text",
                            "bbox": ocr_item.bbox,
                            "content": ocr_item.text,
                            "angle": None,
                        })
            except Exception as e:
                logger.debug("OCR inference error: %s", e)

        return ocr_blocks, formula_blocks

    def _merge_blocks(
        self,
        layout_blocks: List[dict],
        vlm_blocks: List[dict],
        ocr_blocks: List[dict],
        formula_blocks: List[dict],
    ) -> List[dict]:
        """将 VLM layout + VLM visual extraction + Pipeline OCR + MFR 统一合并。

        合并策略:
          - VLM visual blocks (image/table/equation/chart): 直接用 VLM 提取结果
          - Pipeline OCR blocks: 使用 OCR 识别的文本块
          - Inline formula blocks: 如果在文本块 bbox 内，内联到文本块 content
          - 保持 VLM 定义的阅读顺序

        Parameters
        ----------
        layout_blocks : VLM layout 阶段返回的区块 (含 type/bbox)
        vlm_blocks    : VLM visual extraction 阶段返回的区块 (含 content)
        ocr_blocks    : Pipeline OCR 识别的文本块
        formula_blocks: Pipeline MFR 识别的公式块

        Returns
        -------
        list[dict]: 统一区块列表 {type, bbox, content, ...}
        """
        final_blocks: List[dict] = []

        # 用 VLM 的 layout blocks 建立区块索引 (按类型)
        vlm_visual_map: Dict[int, dict] = {}
        for i, lb in enumerate(layout_blocks):
            btype = lb.get("type", "")
            if btype in _VLM_EXTRACT_TYPES:
                vlm_visual_map[i] = dict(lb)

        # 如果 VLM 有 visual extraction 结果，填入 content
        vlm_content_map: Dict[str, List[dict]] = {}
        for vb in vlm_blocks:
            vbtype = vb.get("type", "")
            vlm_content_map.setdefault(vbtype, []).append(vb)

        used_ocr_indices = set()

        for idx, lb in enumerate(layout_blocks):
            btype = lb.get("type", "")
            bbox = lb.get("bbox", [])

            if btype in _VLM_EXTRACT_TYPES:
                content_blocks = vlm_content_map.get(btype, [])
                if content_blocks:
                    final_blocks.append({
                        "type": btype,
                        "bbox": bbox,
                        "content": content_blocks[0].get("content", ""),
                        "angle": content_blocks[0].get("angle"),
                    })
                else:
                    final_blocks.append({
                        "type": btype,
                        "bbox": bbox,
                        "content": "",
                        "angle": None,
                    })

            elif btype == "caption":
                caption_text = ""
                for ob in ocr_blocks:
                    if self._is_bbox_inside(ob.get("bbox", []), bbox):
                        caption_text += ob.get("content", "")
                caption_candidates = [cb for cb in reversed(final_blocks) if cb["type"] in _VLM_EXTRACT_TYPES]
                if caption_candidates:
                    parent = caption_candidates[0]
                    ptype = parent["type"]
                    if ptype == "image":
                        parent[IMAGE_CAPTION] = caption_text
                    elif ptype == "table":
                        parent[TABLE_CAPTION] = caption_text
                    elif ptype == "chart":
                        parent[CHART_CAPTION] = caption_text
                elif caption_text.strip():
                    final_blocks.append({
                        "type": "text",
                        "bbox": bbox,
                        "content": caption_text,
                        "angle": None,
                    })

            elif btype in _PIPELINE_OCR_TYPES:
                final_blocks.append({
                    "type": btype,
                    "bbox": bbox,
                    "content": "",
                    "angle": None,
                })

        # 如果没有 layout blocks (VLM layout failed)，用 OCR 结果直接填充
        if not final_blocks:
            for ob in ocr_blocks:
                final_blocks.append(ob)

        # 合并 inline formula 到 text block content
        for fb in formula_blocks:
            fb_bbox = fb.get("bbox", [])
            latex = fb.get("latex", "")
            if not latex:
                continue
            for i, block in enumerate(final_blocks):
                block_bbox = block.get("bbox", [])
                if self._is_bbox_inside(fb_bbox, block_bbox):
                    existing = block.get("content", "") or ""
                    block["content"] = existing + f" ${latex}$ " if existing else f"${latex}$"
                    break

        return final_blocks

    @staticmethod
    def _is_bbox_inside(inner: List[float], outer: List[float]) -> bool:
        if len(inner) < 4 or len(outer) < 4:
            return False
        ix1, iy1, ix2, iy2 = inner
        ox1, oy1, ox2, oy2 = outer
        return ox1 <= ix1 and oy1 <= iy1 and ox2 >= ix2 and oy2 >= iy2

    # ── 统一接口 ────────────────────────────────────────────────

    def process_image(
        self,
        image: np.ndarray,
        image_analysis: bool = False,
        **kwargs,
    ) -> Tuple[str, List[dict]]:
        """处理单张图像 (根据构造函数 enable_hybrid 决定模式)。

        Parameters
        ----------
        image : np.ndarray (H, W, 3), RGB
        image_analysis : bool
            是否启用图表/图片内容分析 (传递给 VLM)

        Returns
        -------
        (markdown_str, blocks_list)
        """
        if not self._enable_hybrid:
            return self.process_image_vlm_only(
                image, image_analysis=image_analysis, **kwargs
            )

        return self._process_hybrid(image, image_analysis=image_analysis)

    def _process_hybrid(
        self,
        image,
        image_analysis: bool = False,
    ) -> Tuple[str, List[dict]]:
        """Hybrid 模式处理单页。

        流程:
          1. VLM layout analysis → layout_blocks (所有块的位置)
          2. VLM visual extraction → vlm_blocks (image/table/equation 的 content)
          3. Pipeline OCR + MFR → ocr_blocks + formula_blocks
          4. Merge final blocks
          5. post_process → markdown
        """
        from .post_process import blocks_to_markdown
        from PIL import Image as PILImage

        # 统一转换为两种格式：VLM 需要 PIL，Pipeline OCR 需要 numpy
        if isinstance(image, np.ndarray):
            pil_image = PILImage.fromarray(image)
            np_image = image
        elif isinstance(image, PILImage.Image):
            pil_image = image
            np_image = np.array(image)
        else:
            pil_image = PILImage.open(str(image))
            np_image = np.array(pil_image)

        final_blocks: List[dict] = []

        try:
            # Step 1: VLM Layout（传 PIL）
            _, layout_blocks = self._run_vlm_layout(pil_image)

            if not layout_blocks:
                logger.info("No layout blocks from VLM; falling back to VLM-only")
                return self.process_image_vlm_only(
                    pil_image, image_analysis=image_analysis
                )

            # Step 2: VLM Visual Extraction（传 PIL）
            vlm_blocks = self._run_vlm_visual_extraction([pil_image])
            vlm_blocks_page = vlm_blocks[0] if vlm_blocks else []

            # Step 3: Pipeline OCR + MFR（传 numpy）
            ocr_blocks, formula_blocks = self._run_pipeline_ocr(
                np_image, layout_blocks
            )

            # Step 4: Merge
            final_blocks = self._merge_blocks(
                layout_blocks, vlm_blocks_page, ocr_blocks, formula_blocks
            )

            # Step 5: Post-process
            orig_md = blocks_to_markdown(final_blocks)

        except Exception as e:
            logger.error("Hybrid processing failed: %s; falling back to VLM-only", e)
            return self.process_image_vlm_only(
                pil_image, image_analysis=image_analysis
            )

        return orig_md, final_blocks

    def process_images_batch(
        self,
        images: List[np.ndarray],
        image_analysis: bool = False,
        **kwargs,
    ) -> List[Tuple[str, List[dict]]]:
        """批量处理多张图像。"""
        results = []
        for img in images:
            md, blocks = self.process_image(
                img, image_analysis=image_analysis, **kwargs
            )
            results.append((md, blocks))
        return results

    def unload(self):
        """释放资源。"""
        if hasattr(self._vlm, "unload"):
            self._vlm.unload()
        self._layout = None
        self._mfr = None
        self._ocr = None
        logger.info("OVHybridClient resources released")