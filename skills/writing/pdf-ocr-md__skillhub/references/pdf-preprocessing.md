# Pdf Preprocessing

> 来源: pdf-ocr-md v3.3.0 SKILL.md | 从主文件拆分，保持原内容不变

## D：文档预处理 — 扫描件 OCR 增强

适用于质量不佳的扫描件（手机拍照、弯曲书页、倾斜/倒置的文档）。
预处理后 PaddleOCR 的中文准确率可从 ~97% 提升到 ~98%+。

### 安装

```bash
pip install opencv-python-headless numpy Pillow pdf2image
```

### CLI 命令

```bash
# 全部预处理（推荐）
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all

# 仅倾斜校正
python scripts/pdf_preprocess.py input.jpg -o ./output --deskew

# 仅方向校正
python scripts/pdf_preprocess.py input.jpg -o ./output --orient

# 仅文档展平（弯曲/透视照片）
python scripts/pdf_preprocess.py input.jpg -o ./output --unwarp

# PDF 全页 + 高DPI
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all --dpi 400

# 预览模式（显示对比图，不保存）
python scripts/pdf_preprocess.py input.jpg --preview --all
```

### 预处理项说明

| 预处理 | CLI 参数 | 适用场景 | 效果 |
|--------|---------|---------|------|
| **倾斜校正** (deskew) | `--deskew` | 扫描件轻微歪斜 (<15°) | 自动检测角度并旋转正位 |
| **方向校正** (orient) | `--orient` | 页面旋转/倒置 | 检测文本方向并自动旋转到正位 |
| **文档展平** (unwarp) | `--unwarp` | 手机拍的弯曲/透视变形的文档 | 自动检测边界, 透视变换展平 |

### 工作流集成

```bash
# 完整管线: 预处理 → pdf2md
python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
pdf2md ./preprocessed/input_p001.jpg -o ./output_dir

# 对于平整扫描件, 预处理效果不大, 可跳过
pdf2md input.pdf -o ./output_dir
```

### 预处理效果预测

| 文档类型 | 建议 | 预期提升 |
|---------|------|---------|
| 平整扫描件 (A4 扫描仪) | 跳过预处理 | OCR 已很好, 无明显提升 |
| 轻微歪斜 (< 15°) | `--deskew` | 准确率 +1~2% |
| 照片 (手机拍文档) | `--deskew --unwarp` | 准确率 +3~5% |
| 页面倒置/旋转 | `--orient` | 从乱码到正常识别 |
| 弯曲书页 | `--unwarp` | 准确率 +2~4% |

### 脚本参考

预处理脚本位于 `scripts/pdf_preprocess.py`，支持作为 Python 模块导入使用：

```python
from scripts.pdf_preprocess import preprocess_image, deskew_image, unwarp_image
import cv2

img = cv2.imread('scan.jpg')
processed = preprocess_image(img, deskew=True, orient=True, unwarp=True)
cv2.imwrite('corrected.jpg', processed)

---