#!/usr/bin/env python3
"""
pdf_ocr_v6.py — PP-OCRv6 三档模型 OCR（ONNX Runtime）

使用 PP-OCRv6 模型家族进行本地 OCR，支持 Tiny / Small / Medium 三档选择。

用法：
  # Tiny 模型（极速，1.5MB）
  python scripts/pdf_ocr_v6.py input.jpg --tier tiny

  # Small 模型（均衡，7.7MB）
  python scripts/pdf_ocr_v6.py input.jpg --tier small -o output.txt

  # Medium 模型（高精度，34.5MB）
  python scripts/pdf_ocr_v6.py input.jpg --tier medium -o output.txt

  # PDF 批量处理
  python scripts/pdf_ocr_v6.py input.pdf --tier medium -o ./output_dir
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    import onnxruntime
except ImportError:
    print("请先安装依赖: pip install onnxruntime opencv-python-headless numpy Pillow pdf2image")
    sys.exit(1)


# ── 模型路径配置 ──────────────────────────────────────────────

MODELS_BASE = os.path.expanduser(r"~\.workbuddy\.venvs\ppocrv6_models")

MODEL_TIERS = {
    "tiny": {
        "dir": "ppocrv6_onnx",
        "size": "1.5 MB",
        "desc": "极速，可浏览器端运行",
    },
    "small": {
        "dir": "ppocrv6_small_onnx",
        "size": "7.7 MB",
        "desc": "性能均衡",
    },
    "medium": {
        "dir": "ppocrv6_medium_onnx",
        "size": "34.5 MB",
        "desc": "精度最高",
    },
}


# ── OCR 引擎 ──────────────────────────────────────────────────

class PaddleOCREngine:
    """PP-OCRv6 ONNX Runtime 推理引擎"""

    def __init__(self, tier: str = "tiny", device: str = "cpu"):
        if tier not in MODEL_TIERS:
            raise ValueError(f"不支持的模型档位: {tier}，可选: {list(MODEL_TIERS.keys())}")

        model_dir = os.path.join(MODELS_BASE, MODEL_TIERS[tier]["dir"])
        det_path = os.path.join(model_dir, "det", "inference.onnx")
        rec_path = os.path.join(model_dir, "rec", "inference.onnx")

        if not os.path.exists(det_path) or not os.path.exists(rec_path):
            raise FileNotFoundError(
                f"模型文件未找到: {model_dir}\n"
                f"请先下载模型: cd {MODELS_BASE} && 从 https://github.com/andyhuo520/ppocrv6-studio/releases 下载 {tier}.tar.gz"
            )

        # 选择推理后端
        if device == "gpu":
            try:
                import onnxruntime as _ort
                if "DmlExecutionProvider" not in _ort.get_available_providers():
                    print("⚠️ DirectML 不可用，回退到 CPU。请安装: pip install onnxruntime-directml")
                    device = "cpu"
            except ImportError:
                print("⚠️ onnxruntime 未安装，无法检查 DirectML")
                device = "cpu"

        if device == "gpu":
            providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
            print(f"  🔧 后端: DirectML (Intel Arc GPU)")
        else:
            providers = ["CPUExecutionProvider"]
            print(f"  🔧 后端: CPU")

        self.det_session = onnxruntime.InferenceSession(det_path, providers=providers)
        self.rec_session = onnxruntime.InferenceSession(rec_path, providers=providers)

        # 获取输入输出名称
        self.det_input = self.det_session.get_inputs()[0].name
        self.rec_input = self.rec_session.get_inputs()[0].name

        # 加载字符字典 (PP-OCRv6 的 char_dict.json 是 list, 不是 dict)
        # Tiny 有独立的 char_dict.json; Small/Medium 需从 inference.yml 解析
        char_dict_path = os.path.join(model_dir, "rec", "char_dict.json")
        yml_path = os.path.join(model_dir, "rec", "inference.yml")

        if os.path.exists(char_dict_path):
            with open(char_dict_path, "r", encoding="utf-8") as f:
                self.char_dict = json.load(f)
            if isinstance(self.char_dict, dict):
                self.char_dict = list(self.char_dict.values())
        elif os.path.exists(yml_path):
            # 从 inference.yml 解析 character_dict 列表
            self.char_dict = self._parse_char_dict_from_yml(yml_path)
        else:
            self.char_dict = None

        if self.char_dict:
            print(f"  📖 字符字典: {len(self.char_dict)} 个字符")

        self.tier = tier
        self.device = device

    # ── det 预处理参数（来自 inference.yml）──
    DET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    DET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    DET_THRESH = 0.2       # binarization threshold (from config)
    DET_BOX_THRESH = 0.4   # box threshold (from config)
    DET_MIN_AREA = 20
    DET_TARGET_SIZE = 640

    # ── rec 参数（来自 inference.yml）──
    REC_H, REC_W = 48, 320

    @staticmethod
    def _parse_char_dict_from_yml(yml_path: str) -> list:
        """从 inference.yml 的 PostProcess.character_dict 列表中提取字符"""
        import re
        with open(yml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 找到 character_dict: 行，然后收集后续的 "  - " 列表项
        chars = []
        in_dict = False
        for line in lines:
            if "character_dict:" in line:
                in_dict = True
                continue
            if in_dict:
                # 列表项格式: "  - 'x'" 或 "  - x"
                m = re.match(r'\s*-\s+(.*)', line)
                if m:
                    val = m.group(1).strip()
                    # 去除引号
                    if (val.startswith("'") and val.endswith("'")) or \
                       (val.startswith('"') and val.endswith('"')):
                        val = val[1:-1]
                    chars.append(val)
                elif line.strip() and not line.strip().startswith("#"):
                    # 遇到非列表项且非注释，说明 character_dict 段结束
                    if not line.startswith(" " * 4):  # 缩进减少，段结束
                        break
        return chars

    def detect(self, img: np.ndarray) -> list:
        """文本检测: 返回文本框列表 [[x1,y1,x2,y2,...], ...]"""
        h, w = img.shape[:2]
        # 保持长宽比 resize 到 640
        scale = self.DET_TARGET_SIZE / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (new_w, new_h))
        # pad 到 640x640
        canvas = np.zeros((self.DET_TARGET_SIZE, self.DET_TARGET_SIZE, 3), dtype=np.uint8)
        canvas[:new_h, :new_w] = resized

        # 归一化: (img/255 - mean) / std, 然后 HWC→CHW
        inp = canvas.astype(np.float32) / 255.0
        inp = (inp - self.DET_MEAN) / self.DET_STD
        inp = inp.transpose(2, 0, 1)  # HWC → CHW
        inp = np.expand_dims(inp, axis=0)

        out = self.det_session.run(None, {self.det_input: inp})[0]
        # 输出 shape: (1, 1, 640, 640) → squeeze 到 2D
        prob_map = out.squeeze()  # (640, 640)
        return self._db_postprocess(prob_map, (w, h), (new_h, new_w))

    def _db_postprocess(self, prob_map: np.ndarray, orig_size: tuple, resized_size: tuple,
                        threshold: float = None) -> list:
        """DB 后处理: prob_map → 文本框"""
        if threshold is None:
            threshold = self.DET_THRESH

        h_prob, w_prob = prob_map.shape
        bin_map = (prob_map > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(bin_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        ow, oh = orig_size
        new_h, new_w = resized_size
        boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.DET_MIN_AREA:
                continue
            # 计算最小外接矩形
            rect = cv2.minAreaRect(cnt)
            pts = cv2.boxPoints(rect)
            # 只取 prob_map 有效区域内的框（排除 padding 区产生的假框）
            if pts[:, 0].max() > new_w + 5 or pts[:, 1].max() > new_h + 5:
                continue
            # 缩放回原图尺寸
            pts[:, 0] = pts[:, 0] / new_w * ow
            pts[:, 1] = pts[:, 1] / new_h * oh
            boxes.append(pts.astype(np.int32).tolist())
        return boxes

    def recognize(self, img: np.ndarray, box: list) -> tuple[str, float]:
        """文本框识别: 返回 (文本, 置信度)"""
        pts = np.array(box, dtype=np.float32)
        x, y, bw, bh = cv2.boundingRect(pts)
        pad = max(3, int(bh * 0.1))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + bw + pad)
        y2 = min(img.shape[0], y + bh + pad)
        crop = img[y1:y2, x1:x2]

        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return "", 0.0

        # 保持宽高比 resize 到 (48, 320)
        h, w = crop.shape[:2]
        ratio = w / h
        target_w = min(int(self.REC_H * ratio), self.REC_W)
        target_w = max(target_w, 1)
        resized = cv2.resize(crop, (target_w, self.REC_H))
        # pad 宽度到 320
        canvas = np.zeros((self.REC_H, self.REC_W, 3), dtype=np.uint8)
        canvas[:, :target_w] = resized

        # 归一化到 [0, 1], HWC → CHW
        inp = canvas.astype(np.float32) / 255.0
        inp = inp.transpose(2, 0, 1)
        inp = np.expand_dims(inp, axis=0)

        outs = self.rec_session.run(None, {self.rec_input: inp})
        probs = outs[0][0]  # shape: (T, num_classes)
        pred_idx = probs.argmax(axis=-1)

        # CTC 解码: char_dict 是 list, index 0 = blank
        text = ""
        conf_sum = 0.0
        count = 0
        last_idx = 0  # 0 = blank

        for t in range(len(pred_idx)):
            idx = int(pred_idx[t])
            if idx != 0 and idx != last_idx:
                # char_dict[idx-1] 对应模型输出 idx (idx 0 = blank)
                if self.char_dict and idx - 1 < len(self.char_dict):
                    char = self.char_dict[idx - 1]
                    text += char
                    conf_sum += float(probs[t, idx])
                    count += 1
            last_idx = idx

        conf = conf_sum / max(count, 1)
        return text.strip(), conf

    def ocr_image(self, img: np.ndarray, min_conf: float = 0.5) -> list[dict]:
        """完整 OCR 流程: 检测 → 识别"""
        boxes = self.detect(img)
        results = []
        for box in boxes:
            text, conf = self.recognize(img, box)
            if text and conf >= min_conf:
                results.append({
                    "text": text,
                    "confidence": round(float(conf), 4),
                    "box": box,
                })
        return results


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PP-OCRv6 三档模型 OCR — ONNX Runtime 本地推理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模型档位:
  tiny   (1.5 MB)  极速，可浏览器端运行
  small  (7.7 MB)  性能均衡
  medium (34.5 MB) 精度最高

示例:
  %(prog)s input.jpg --tier medium
  %(prog)s input.jpg --tier tiny -o output.txt
  %(prog)s input.pdf --tier medium -o ./output
  %(prog)s input.jpg --tier small --device gpu
        """,
    )
    parser.add_argument("input", help="输入文件 (图片或 PDF)")
    parser.add_argument("--tier", "-t", choices=["tiny", "small", "medium"],
                        default="tiny", help="模型档位 (默认: tiny)")
    parser.add_argument("--device", "-d", choices=["cpu", "gpu"],
                        default="gpu", help="推理后端 (默认: gpu (DirectML)，cpu 用 CPU)")
    parser.add_argument("--output", "-o", help="输出文件或目录")
    parser.add_argument("--min-conf", type=float, default=0.5,
                        help="最低置信度阈值 (默认: 0.5)")

    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    # 加载引擎
    print(f"🔧 加载 PP-OCRv6 {args.tier} 模型...")
    try:
        engine = PaddleOCREngine(tier=args.tier, device=args.device)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print(f"✅ 模型已加载")

    # PDF 或图片
    ext = input_path.lower()
    if ext.endswith(".pdf"):
        try:
            from pdf2image import convert_from_path
        except ImportError:
            print("❌ PDF 处理需要 pdf2image: pip install pdf2image")
            sys.exit(1)
        print(f"📄 转换 PDF → 图片...")
        images = convert_from_path(input_path, dpi=300)
        imgs = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]
    else:
        img = cv2.imread(input_path)
        if img is None:
            print(f"❌ 无法读取图片: {input_path}")
            sys.exit(1)
        imgs = [img]

    # OCR
    all_results = []
    for i, img in enumerate(imgs):
        print(f"  OCR 第 {i+1}/{len(imgs)} 页...")
        results = engine.ocr_image(img, min_conf=args.min_conf)
        all_results.append({"page": i + 1, "results": results})
        print(f"    识别 {len(results)} 个文本块")

    # 输出
    basename = os.path.splitext(os.path.basename(input_path))[0]

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or len(imgs) > 1:
            os.makedirs(out_path, exist_ok=True)
            json_path = os.path.join(out_path, f"{basename}.json")
            text_path = os.path.join(out_path, f"{basename}.txt")
        else:
            json_path = out_path.replace(".txt", ".json") if out_path.endswith(".txt") else out_path + ".json"
            text_path = out_path
    else:
        json_path = f"{basename}_ocr.json"
        text_path = f"{basename}_ocr.txt"

    # 保存 JSON
    output_data = {
        "engine": f"PP-OCRv6 {args.tier}",
        "model_size": MODEL_TIERS[args.tier]["size"],
        "pages": all_results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ JSON: {json_path}")

    # 保存文本
    lines = []
    for page in all_results:
        lines.append(f"--- 第 {page['page']} 页 ---")
        for r in page["results"]:
            lines.append(r["text"])
        lines.append("")
    Path(text_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✅ 文本: {text_path}")

    # 汇总统计
    total_blocks = sum(len(p["results"]) for p in all_results)
    avg_conf = sum(r["confidence"] for p in all_results for r in p["results"]) / max(total_blocks, 1)
    print(f"\n📊 统计: {total_blocks} 个文本块, 平均置信度 {avg_conf:.2f}")


if __name__ == "__main__":
    main()
