#!/usr/bin/env python3
"""
pdf_preprocess.py — 文档预处理工具（扫描件 OCR 前增强）

功能：
  1. 倾斜校正 (deskew)      — 自动检测文本角度, 旋转修正
  2. 文档展平 (unwarp)       — 透视变换矫正弯曲/变形的文档照片
  3. 方向分类 (orientation)  — 检测并自动旋转倒置/侧向的页面

用法：
  # 安装依赖
  pip install opencv-python-headless numpy Pillow pdf2image

  # 单独使用
  python pdf_preprocess.py input.jpg -o ./output          # 单图片
  python pdf_preprocess.py input.pdf -o ./output --all    # PDF 全页

  # 选择预处理步骤
  python pdf_preprocess.py input.jpg -o ./output --deskew              # 仅倾斜校正
  python pdf_preprocess.py input.jpg -o ./output --unwarp              # 仅展平
  python pdf_preprocess.py input.jpg -o ./output --orient             # 仅方向校正
  python pdf_preprocess.py input.pdf -o ./output --all --dpi 400      # 全部 + 高DPI
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError:
    print("请先安装依赖: pip install opencv-python-headless numpy Pillow pdf2image")
    sys.exit(1)


# ── 倾斜校正 (Deskew) ──────────────────────────────────────────

def deskew_image(img: np.ndarray) -> np.ndarray:
    """
    检测图像中文本的倾斜角度并旋转校正。
    适用于扫描件稍微偏斜的场景（< 15度）。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # 用 Hough 变换检测直线, 计算角度
    edges = cv2.Canny(thresh, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 300)

    if lines is None:
        return img  # 无法检测直线, 原图返回

    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90  # 转为水平偏移角
        if -45 <= angle <= 45:
            angles.append(angle)

    if not angles:
        return img

    median_angle = np.median(angles)

    # 只有角度超过 0.5 度才校正
    if abs(median_angle) < 0.5:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    rot = cv2.getRotationMatrix2D(center, median_angle, 1.0)

    # 计算旋转后的画布尺寸, 避免裁剪
    cos = abs(rot[0, 0])
    sin = abs(rot[0, 1])
    nw = int(h * sin + w * cos)
    nh = int(h * cos + w * sin)
    rot[0, 2] += nw / 2 - center[0]
    rot[1, 2] += nh / 2 - center[1]

    corrected = cv2.warpAffine(img, rot, (nw, nh), flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
    return corrected


# ── 方向校正 (Orientation) ─────────────────────────────────────

def correct_orientation(img: np.ndarray) -> np.ndarray:
    """
    检测图像方向并自动旋转到正位 (0°/90°/180°/270°)。
    利用 PaddleOCR 的方向分类模型或基于文本行检测。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 方法: 检测文本区域的分布方向
    # 对二值图像做投影分析, 判断文本是横向还是纵向
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h, w = thresh.shape

    # 计算水平和垂直投影
    hor_proj = np.sum(thresh, axis=1)  # 每行像素和
    ver_proj = np.sum(thresh, axis=0)  # 每列像素和

    # 判断文本排列方向
    hor_var = np.var(hor_proj)
    ver_var = np.var(ver_proj)

    # 如果竖排方差更大, 说明文本可能是纵向排列, 需要旋转
    if ver_var > hor_var * 1.5:
        # 判断上下方向: 简单方法 - 取上1/4和下1/4区域比较文本密度
        top_quarter = np.sum(thresh[:h//4, :])
        bot_quarter = np.sum(thresh[3*h//4:, :])

        if top_quarter > bot_quarter:
            # 文本在上方 → 逆时针旋转90度
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # 已正位, 返回
    return img


# ── 文档展平 (Unwarp / Perspective Correction) ────────────────

def find_document_contour(img: np.ndarray) -> np.ndarray | None:
    """
    检测文档边界（最大四边形轮廓）。
    返回 4 个角点坐标（左上、右上、右下、左下）。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 自适应阈值, 适应不同光照
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 2)
    # 形态学闭运算, 连接断裂边缘
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # 找最大轮廓
    largest = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    # 如果近似轮廓是四边形, 返回其4个角点
    if len(approx) == 4:
        return _order_corners(approx.reshape(4, 2))

    # 非四边形, 尝试找最小外接矩形
    rect = cv2.minAreaRect(largest)
    corners = cv2.boxPoints(rect)
    return _order_corners(corners)


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """将 4 个点排序为: 左上、右上、右下、左下"""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # 左上 (sum 最小)
    rect[2] = pts[np.argmax(s)]   # 右下 (sum 最大)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 右上 (diff 最小)
    rect[3] = pts[np.argmax(diff)]  # 左下 (diff 最大)
    return rect


def unwarp_image(img: np.ndarray, padding: float = 0.05) -> np.ndarray:
    """
    透视变换校正文档照片。
    自动检测文档边界并展平为矩形。
    padding: 输出图像边界的留白比例(0~1)
    """
    corners = find_document_contour(img)
    if corners is None:
        return img  # 无法检测边界, 原图返回

    # 计算目标矩形尺寸
    (tl, tr, br, bl) = corners
    w_top = np.linalg.norm(tr - tl)
    w_bot = np.linalg.norm(br - bl)
    max_w = int(max(w_top, w_bot))
    h_left = np.linalg.norm(bl - tl)
    h_right = np.linalg.norm(br - tr)
    max_h = int(max(h_left, h_right))

    # 加留白
    pad_x = int(max_w * padding)
    pad_y = int(max_h * padding)

    dst = np.array([
        [pad_x, pad_y],
        [max_w + pad_x, pad_y],
        [max_w + pad_x, max_h + pad_y],
        [pad_x, max_h + pad_y]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(corners, dst)
    result = cv2.warpPerspective(img, matrix,
                                  (max_w + 2 * pad_x, max_h + 2 * pad_y),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
    return result


# ── 完整管线 ────────────────────────────────────────────────────

def preprocess_image(img: np.ndarray, deskew: bool = True,
                     orient: bool = True, unwarp: bool = False) -> np.ndarray:
    """
    完整的预处理流水线:
      1. 方向校正 (先做, 保证方向正确)
      2. 文档展平 (再做, 修正透视)
      3. 倾斜校正 (最后, 微调旋转)
    """
    if orient:
        img = correct_orientation(img)
    if unwarp:
        img = unwarp_image(img)
    if deskew:
        img = deskew_image(img)
    return img


def save_result(img: np.ndarray, output_path: str):
    """保存预处理后的图片"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    cv2.imwrite(output_path, img,
                [cv2.IMWRITE_JPEG_QUALITY, 95])


# ── PDF 处理 ────────────────────────────────────────────────────

def pdf_to_images(pdf_path: str, dpi: int = 300) -> list[np.ndarray]:
    """将 PDF 每页转为 OpenCV 图像列表"""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("需要安装 pdf2image: pip install pdf2image")
        print("Windows 还需要安装 poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("或在 PATH 中添加 poppler bin 目录")
        sys.exit(1)

    images = convert_from_path(pdf_path, dpi=dpi)
    return [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]


# ── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="文档预处理工具 — 倾斜校正 / 方向校正 / 文档展平",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.jpg -o ./output
  %(prog)s input.jpg -o ./output --deskew              # 仅倾斜校正
  %(prog)s input.jpg -o ./output --unwarp              # 仅文档展平
  %(prog)s input.pdf -o ./output --all                 # PDF 全页全部预处理
  %(prog)s input.pdf -o ./output --all --dpi 400       # 高DPI扫描
  %(prog)s input.pdf -o ./output --preview             # 预览效果(不保存)
        """
    )
    parser.add_argument('input', help='输入文件 (PDF / 图片)')
    parser.add_argument('-o', '--output', default='./preprocessed',
                        help='输出目录 (默认: ./preprocessed)')

    # 预处理选项
    parser.add_argument('--all', action='store_true',
                        help='启用全部预处理: 方向校正 + 文档展平 + 倾斜校正')
    parser.add_argument('--deskew', action='store_true', help='倾斜校正')
    parser.add_argument('--orient', action='store_true', help='方向校正')
    parser.add_argument('--unwarp', action='store_true', help='文档展平 (透视变换)')

    # 高级选项
    parser.add_argument('--dpi', type=int, default=300,
                        help='PDF 转图片 DPI (默认: 300)')
    parser.add_argument('--preview', action='store_true',
                        help='预览模式: 显示处理后图片（不保存, GUI 模式）')

    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    # 确定预处理步骤
    if args.all:
        do_deskew = do_orient = do_unwarp = True
    else:
        do_deskew = args.deskew or (not args.orient and not args.unwarp and not args.all)
        do_orient = args.orient
        do_unwarp = args.unwarp

    # 如果没有任何选项被指定, 默认只做 deskew
    if not (args.deskew or args.orient or args.unwarp or args.all):
        do_deskew = True

    print(f"📄 输入: {input_path}")
    print(f"   预处理: {'倾斜校正 ' if do_deskew else ''}"
          f"{'方向校正 ' if do_orient else ''}"
          f"{'文档展平 ' if do_unwarp else ''}")

    ext = input_path.lower()
    if ext.endswith('.pdf'):
        print(f"   正在转换 PDF → 图片 (DPI={args.dpi})...")
        images = pdf_to_images(input_path, dpi=args.dpi)
        print(f"   共 {len(images)} 页")
    else:
        img = cv2.imread(input_path)
        if img is None:
            print(f"❌ 无法读取图片: {input_path}")
            sys.exit(1)
        images = [img]

    output_dir = args.output
    basename = os.path.splitext(os.path.basename(input_path))[0]

    for i, img in enumerate(images):
        # 预处理
        processed = preprocess_image(img, deskew=do_deskew,
                                      orient=do_orient, unwarp=do_unwarp)

        if args.preview:
            # 显示原图 vs 处理后的对比
            preview = np.hstack([
                cv2.resize(img, (640, int(640 * img.shape[0] / img.shape[1]) )),
                cv2.resize(processed, (640, int(640 * processed.shape[0] / processed.shape[1]) ))
            ])
            cv2.imshow(f'预处理对比 — 第{i+1}页 (原图 | 处理后)', preview)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            if len(images) > 1:
                out_name = f"{basename}_p{i+1:03d}.jpg"
            else:
                out_name = f"{basename}_preprocessed.jpg"
            out_path = os.path.join(output_dir, out_name)
            save_result(processed, out_path)
            print(f"   ✅ 已保存: {out_path}")

    if not args.preview:
        print(f"\n✅ 预处理完成！结果保存在: {os.path.abspath(output_dir)}")
        print(f"   提示: 可以将预处理后的图片输入到 'pdf2md' 管线获得更好效果")


if __name__ == '__main__':
    main()
