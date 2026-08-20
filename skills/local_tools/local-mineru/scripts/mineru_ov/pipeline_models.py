"""OpenVINO pipeline 模型封装：PP-DocLayoutV2, UniMerNet, PP-OCRv5.

这些模型在 hybrid backend 中用于：
  - PP-DocLayoutV2: 检测行内公式区域
  - UniMerNet (MFR): 行内公式识别
  - PP-OCRv5 (det + rec): 文本检测与识别
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import cv2
import numpy as np
import openvino as ov
from PIL import Image

logger = logging.getLogger(__name__)

# ── PP-DocLayoutV2 类别标签 ──────────────────────────────────────
PP_DOCLAYOUT_LABELS = [
    "abstract", "algorithm", "aside_text", "chart", "content",
    "display_formula", "doc_title", "figure_title", "footer",
    "footer_image", "footnote", "formula_number", "header",
    "header_image", "image", "inline_formula", "number",
    "paragraph_title", "reference", "reference_content", "seal",
    "table", "text", "vertical_text", "vision_footnote",
]

PP_DOCLAYOUT_CLASS_THRESHOLDS = [
    0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5,
    0.5, 0.5, 0.5, 0.4, 0.5, 0.4, 0.5, 0.5, 0.45, 0.5, 0.4, 0.4, 0.5,
]

PP_DOCLAYOUT_IMAGE_SIZE = (800, 800)
PP_DOCLAYOUT_RESCALE = 1.0 / 255.0


def _resize_with_aspect_ratio(
    img: np.ndarray, target_size: Tuple[int, int]
) -> np.ndarray:
    h, w = img.shape[:2]
    target_w, target_h = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    canvas = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
    canvas[:new_h, :new_w] = resized
    return canvas


def _letterbox_image(
    img: np.ndarray, target_size: Tuple[int, int]
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    h, w = img.shape[:2]
    target_w, target_h = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    canvas = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
    canvas[:new_h, :new_w] = resized
    return canvas, scale, (new_w, new_h)


# ═══════════════════════════════════════════════════════════════════
# PP-DocLayoutV2 — 版面检测（行内公式区域提取）
# ═══════════════════════════════════════════════════════════════════


class OVLayoutModel:
    """PP-DocLayoutV2 的 OpenVINO 封装。

    用于 hybrid backend 中检测行内公式 (inline_formula) 和展示公式
    (display_formula) 区域。

    Attributes
    ----------
    model_dir : Path
        OpenVINO IR 模型目录
    device : str
        推理设备
    conf : float
        检测置信度阈值
    """

    def __init__(
        self,
        model_dir: Union[str, Path],
        device: str = "CPU",
        conf: float = 0.45,
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        self.conf = conf
        self._imgsz = PP_DOCLAYOUT_IMAGE_SIZE

        core = ov.Core()
        xml_path = str(self.model_dir / "PP-DocLayoutV2.xml")
        self._model = core.compile_model(xml_path, device)
        self._input_name = self._model.input(0).get_any_name()
        logger.info("OVLayoutModel ready (device=%s)", device)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """将输入图像预处理为模型输入张量。

        Parameters
        ----------
        image : np.ndarray (H, W, 3), RGB 或 BGR

        Returns
        -------
        np.ndarray (1, 3, H, W), float32
        """
        if image.shape[2] == 3 and image.dtype == np.uint8:
            img = image.astype(np.float32)
        else:
            img = np.array(image, dtype=np.float32)
        img = _resize_with_aspect_ratio(img, self._imgsz)
        img = img / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, 0).astype(np.float32)
        return img

    def _get_order_seqs(self, order_logits: np.ndarray) -> np.ndarray:
        """从 order_logits 解析阅读顺序序列。"""
        order_scores = 1.0 / (1.0 + np.exp(-order_logits))
        batch_size, seq_len, _ = order_scores.shape
        order_votes = np.triu(order_scores, k=1).sum(axis=1) + (
            1.0 - np.transpose(order_scores, (0, 2, 1))
        ).triu(k=1).sum(axis=1)
        order_pointers = np.argsort(-order_votes, axis=1)
        order_seq = np.empty_like(order_pointers)
        ranks = np.arange(seq_len, dtype=np.int32)
        for b in range(batch_size):
            order_seq[b, order_pointers[b]] = ranks
        return order_seq

    def postprocess(
        self,
        logits: np.ndarray,
        pred_boxes: np.ndarray,
        order_logits: np.ndarray,
        orig_size: Tuple[int, int],
    ) -> List[dict]:
        """将模型输出解析为检测结果列表。

        Parameters
        ----------
        logits       : (1, N, C) 类别 logits
        pred_boxes   : (1, N, 4) 归一化检测框 (cx, cy, w, h)
        order_logits : (1, N, N) 阅读顺序 logits
        orig_size    : (orig_h, orig_w)

        Returns
        -------
        List[dict]: 每个检测项的 {label, score, bbox, index}
        """
        orig_h, orig_w = orig_size

        box_cx, box_cy, box_w, box_h = np.split(pred_boxes[0], 4, axis=-1)
        boxes = np.concatenate(
            [box_cx - 0.5 * box_w, box_cy - 0.5 * box_h,
             box_cx + 0.5 * box_w, box_cy + 0.5 * box_h],
            axis=-1,
        )

        scores = 1.0 / (1.0 + np.exp(-logits[0]))
        num_queries = scores.shape[0]
        scores_flat = scores.reshape(num_queries, -1)
        top_scores = np.max(scores_flat, axis=1)
        top_labels = np.argmax(scores_flat, axis=1)

        keep = top_scores >= self.conf
        if not np.any(keep):
            return []

        boxes = boxes[keep]
        top_scores = top_scores[keep]
        top_labels = top_labels[keep]

        order_seqs = self._get_order_seqs(order_logits)
        order_seq = order_seqs[0, keep]

        sorted_idx = np.argsort(order_seq)

        results = []
        for i in sorted_idx:
            score = float(top_scores[i])
            label_id = int(top_labels[i])
            if label_id >= len(PP_DOCLAYOUT_LABELS):
                continue
            label = PP_DOCLAYOUT_LABELS[label_id]

            x1, y1, x2, y2 = boxes[i]
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1

            x1 = int(x1 * orig_w / 1000.0)
            y1 = int(y1 * orig_h / 1000.0)
            x2 = int(x2 * orig_w / 1000.0)
            y2 = int(y2 * orig_h / 1000.0)

            x1 = max(0, min(orig_w, x1))
            y1 = max(0, min(orig_h, y1))
            x2 = max(0, min(orig_w, x2))
            y2 = max(0, min(orig_h, y2))

            if x2 <= x1 or y2 <= y1:
                continue

            results.append({
                "label": label,
                "score": round(score, 4),
                "bbox": [x1, y1, x2, y2],
                "cls_id": label_id,
            })

        return results

    def predict(self, image: np.ndarray) -> List[dict]:
        """对单张图像执行版面检测。

        Parameters
        ----------
        image : np.ndarray (H, W, 3), RGB

        Returns
        -------
        List[dict]: 检测结果列表
        """
        orig_h, orig_w = image.shape[:2]
        input_tensor = self.preprocess(image)
        outputs = self._model([input_tensor])
        logits = outputs[0]
        pred_boxes = outputs[1]
        order_logits = outputs[2]
        return self.postprocess(logits, pred_boxes, order_logits, (orig_h, orig_w))

    def batch_predict(
        self, images: List[np.ndarray], batch_size: int = 8
    ) -> List[List[dict]]:
        """对多张图像执行版面检测。"""
        results = []
        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            orig_sizes = [(img.shape[0], img.shape[1]) for img in batch]
            inputs = np.concatenate([self.preprocess(img) for img in batch], axis=0)
            outputs = self._model([inputs])
            logits = outputs[0]
            pred_boxes = outputs[1]
            order_logits = outputs[2]
            for j in range(len(batch)):
                res = self.postprocess(
                    logits[j : j + 1],
                    pred_boxes[j : j + 1],
                    order_logits[j : j + 1],
                    orig_sizes[j],
                )
                results.append(res)
        return results

    def get_inline_formula_boxes(
        self, image: np.ndarray
    ) -> List[dict]:
        """仅提取行内公式检测框 (label=inline_formula 或 display_formula)。"""
        layout_res = self.predict(image)
        formulas = []
        for item in layout_res:
            if item["label"] in ("inline_formula", "display_formula"):
                formulas.append(item)
        return formulas


# ═══════════════════════════════════════════════════════════════════
# UniMerNet — 行内公式识别
# ═══════════════════════════════════════════════════════════════════


class OVMFRModel:
    """UniMerNet 的 OpenVINO 封装，用于行内/展示公式识别。"""

    def __init__(
        self,
        model_dir: Union[str, Path],
        device: str = "CPU",
        max_tokens: int = 256,
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        self._max_tokens = max_tokens

        core = ov.Core()

        full_xml = str(self.model_dir / "unimernet_full.xml")
        self._full_model = core.compile_model(full_xml, device)

        encoder_xml = str(self.model_dir / "encoder.xml")
        self._encoder_model = core.compile_model(encoder_xml, device)

        self._input_names = self._full_model.inputs
        self._output_name = self._full_model.output(0).get_any_name()

        tokenizer_path = self.model_dir.parent / "unimernet_hf_small_2503"
        if not tokenizer_path.exists():
            tokenizer_path = self.model_dir

        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(tokenizer_path), trust_remote_code=True
        )
        self.decoder_start_id = self.tokenizer.convert_tokens_to_ids("<s>")
        self.pad_id = self.tokenizer.pad_token_id or 0
        self.eos_id = self.tokenizer.eos_token_id or 2

        self._imgsz = 224

        logger.info("OVMFRModel ready (device=%s)", device)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """将裁剪出的公式图像预处理为模型输入。"""
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        h, w = image.shape[:2]
        scale = self._imgsz / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        canvas = np.full((self._imgsz, self._imgsz, 3), 255, dtype=np.uint8)
        y_off = (self._imgsz - new_h) // 2
        x_off = (self._imgsz - new_w) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        tensor = canvas.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))
        tensor = np.expand_dims(tensor, 0).astype(np.float32)
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(3, 1, 1)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(3, 1, 1)
        tensor = (tensor - mean) / std
        return tensor

    def generate(self, image: np.ndarray) -> str:
        """对单张公式图像执行贪婪解码，返回 LaTeX 字符串。

        Parameters
        ----------
        image : np.ndarray 裁剪出的公式区域图像

        Returns
        -------
        str: LaTeX 表达式
        """
        tensor = self.preprocess(image)
        input_ids = np.array([[self.decoder_start_id]], dtype=np.int64)

        for _ in range(self._max_tokens):
            outputs = self._full_model([tensor, input_ids])
            logits = outputs[self._output_name]
            next_token = int(np.argmax(logits[0, -1, :]))
            if next_token == self.eos_id:
                break
            input_ids = np.concatenate(
                [input_ids, np.array([[next_token]], dtype=np.int64)], axis=1
            )

        token_ids = input_ids[0, 1:].tolist()
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)

    def batch_predict(
        self,
        images_mfd_res: List[List[dict]],
        images: List[np.ndarray],
        batch_size: int = 16,
        interline_enable: bool = True,
    ) -> List[List[dict]]:
        """批量预测公式（兼容 MinerU 接口）。

        Parameters
        ----------
        images_mfd_res : list[list[dict]], 每页的公式检测框列表
        images : list[np.ndarray], 每页的 RGB 图像
        batch_size : int
        interline_enable : bool, 是否同时预测行间公式

        Returns
        -------
        list[list[dict]]: 每页的公式结果列表，每项包含 latex
        """
        results = []
        for page_mfd, page_img in zip(images_mfd_res, images):
            page_results = list(page_mfd)
            for item in page_results:
                bbox = item.get("bbox")
                if bbox is None or len(bbox) != 4:
                    item["latex"] = ""
                    continue
                x1, y1, x2, y2 = [int(v) for v in bbox]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(page_img.shape[1], x2)
                y2 = min(page_img.shape[0], y2)
                if x2 <= x1 or y2 <= y1:
                    item["latex"] = ""
                    continue
                crop = page_img[y1:y2, x1:x2]
                try:
                    latex = self.generate(crop)
                    item["latex"] = latex
                except Exception as e:
                    logger.debug("MFR inference error: %s", e)
                    item["latex"] = ""
            results.append(page_results)
        return results


# ═══════════════════════════════════════════════════════════════════
# PP-OCRv5 — 文本检测与识别
# ═══════════════════════════════════════════════════════════════════


@dataclass
class OCRBox:
    text: str
    score: float
    bbox: List[float]


class OVDetector:
    """PP-OCRv5 文本检测器的 OpenVINO 封装。"""

    def __init__(self, model_dir: Union[str, Path], device: str = "CPU"):
        self.model_dir = Path(model_dir)
        self.device = device
        core = ov.Core()
        xml_path = str(self.model_dir / "det.xml")
        self._model = core.compile_model(xml_path, device)
        self._input_name = self._model.input(0).get_any_name()
        self._output_name = self._model.output(0).get_any_name()
        logger.info("OVDetector ready (device=%s)", device)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """预处理检测输入。"""
        h, w = image.shape[:2]
        target_h = max(32, math.ceil(h / 32) * 32)
        target_w = max(32, math.ceil(w / 32) * 32)
        resized = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        tensor = resized.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)
        tensor = (tensor - mean) / std
        tensor = np.transpose(tensor, (2, 0, 1))
        tensor = np.expand_dims(tensor, 0).astype(np.float32)
        return tensor, (target_h, target_w), (h, w)

    def predict(self, image: np.ndarray) -> np.ndarray:
        """检测文本区域，返回检测图。"""
        tensor, _, _ = self.preprocess(image)
        outputs = self._model([tensor])
        result = outputs[self._output_name]
        return result[0, 0]


class OVRecognizer:
    """PP-OCRv5 文本识别器的 OpenVINO 封装，使用 CTC 解码。"""

    def __init__(
        self,
        model_dir: Union[str, Path],
        device: str = "CPU",
        char_dict_path: Optional[Union[str, Path]] = None,
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        core = ov.Core()
        xml_path = str(self.model_dir / "rec.xml")
        self._model = core.compile_model(xml_path, device)
        self._input_name = self._model.input(0).get_any_name()
        self._output_name = self._model.output(0).get_any_name()

        if char_dict_path is None:
            char_dict_path = self._find_default_dict()
        self._character = self._load_char_dict(char_dict_path)
        logger.info(
            "OVRecognizer ready (device=%s, chars=%d)", device, len(self._character)
        )

    @staticmethod
    def _find_default_dict() -> str:
        try:
            from pathlib import Path as _P
            import os
            base = _P(__file__).resolve().parent
            while base.name != "mineru":
                base = base.parent
            candidate = (
                base
                / "model"
                / "utils"
                / "pytorchocr"
                / "utils"
                / "resources"
                / "dict"
                / "ppocrv4_doc_dict.txt"
            )
            if candidate.exists():
                return str(candidate)
        except Exception:
            pass
        return ""

    @staticmethod
    def _load_char_dict(path: Union[str, Path]) -> np.ndarray:
        chars = ["blank"]
        if path:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    c = line.strip("\n").strip("\r\n")
                    chars.append(c)
        else:
            import string as _s
            chars.extend(list(_s.digits + _s.ascii_lowercase))
        return np.array(chars)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        ratio = 48.0 / h
        target_w = max(int(w * ratio), 16)
        resized = cv2.resize(image, (target_w, 48), interpolation=cv2.INTER_LINEAR)
        tensor = resized.astype(np.float32) / 127.5 - 1.0
        tensor = np.transpose(tensor, (2, 0, 1))
        tensor = np.expand_dims(tensor, 0).astype(np.float32)
        return tensor

    def predict(self, image: np.ndarray) -> Tuple[str, float]:
        tensor = self.preprocess(image)
        outputs = self._model([tensor])
        logits = outputs[self._output_name][0]
        pred_ids = np.argmax(logits, axis=1)
        probs = np.max(logits, axis=1)
        text, conf = self._ctc_decode(pred_ids, probs)
        return text, conf

    def _ctc_decode(
        self, ids: np.ndarray, probs: np.ndarray
    ) -> Tuple[str, float]:
        blank = 0
        filtered_ids = []
        filtered_probs = []
        prev = -1
        for idx, prob in zip(ids, probs):
            if idx != blank and idx != prev:
                filtered_ids.append(idx)
                filtered_probs.append(prob)
            prev = idx
        if not filtered_ids:
            return "", 0.0
        text = "".join(self._character[filtered_ids].tolist())
        conf = float(np.mean(filtered_probs))
        return text, conf


class OVOCREngine:
    """PP-OCRv5 检测+识别 的 OpenVINO 封装。

    在 hybrid backend 中用于对非 VLM 处理的文本块进行 OCR。
    """

    def __init__(
        self,
        ov_models_dir: Union[str, Path],
        device: str = "CPU",
    ):
        self.ov_models_dir = Path(ov_models_dir)
        self.device = device
        self.detector = OVDetector(self.ov_models_dir / "det", device)
        self.recognizer = OVRecognizer(self.ov_models_dir / "rec", device)
        logger.info("OVOCREngine ready (device=%s)", device)

    def detect(self, image: np.ndarray) -> List[List[float]]:
        """文本检测，返回检测框列表。"""
        det_map = self.detector.predict(image)
        det_map = (det_map > 0.3).astype(np.uint8) * 255

        contours, _ = cv2.findContours(det_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h_img, w_img = image.shape[:2]
        boxes = []
        for cnt in contours:
            if cv2.contourArea(cnt) < 50:
                continue
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.array(box, dtype=np.float32)

            x_coords = box[:, 0]
            y_coords = box[:, 1]
            x1 = max(0, int(np.min(x_coords)))
            y1 = max(0, int(np.min(y_coords)))
            x2 = min(w_img, int(np.max(x_coords)))
            y2 = min(h_img, int(np.max(y_coords)))

            if x2 - x1 < 5 or y2 - y1 < 5:
                continue

            boxes.append([x1, y1, x2, y2])
        return boxes

    def recognize(self, image: np.ndarray, box: List[float]) -> OCRBox:
        """对单个检测框进行文字识别。"""
        x1, y1, x2, y2 = [int(v) for v in box]
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return OCRBox("", 0.0, box)
        text, score = self.recognizer.predict(crop)
        return OCRBox(text, score, box)

    def ocr_image(self, image: np.ndarray) -> List[OCRBox]:
        """对整张图像进行 OCR（全流程检测+识别）。"""
        boxes = self.detect(image)
        results = []
        for box in boxes:
            ocr_res = self.recognize(image, box)
            if ocr_res.text.strip():
                results.append(ocr_res)
        return results