# PaddleOCR Chinese Document OCR — Reference

> Scanned Chinese document OCR with PP-OCRv4. ~98% simplified Chinese accuracy.
> Supports traditional Chinese, vertical text, and handwriting.

## Environment

- **Venv**: `~/.venvs/paddleocr/`
- **Python**: `~/.venvs/paddleocr/bin/python`
- **Dependencies**: paddlepaddle==2.6.2 + paddleocr==2.7.3 + numpy==1.26.4 (numpy<2 avoids opencv ABI conflict)

### Installation

```bash
python3 -m venv ~/.venvs/paddleocr
~/.venvs/paddleocr/bin/pip install paddlepaddle==2.6.2
~/.venvs/paddleocr/bin/pip install "numpy<2" paddleocr==2.7.3
```

## Python 3.13 Compatibility (Important!)

> ⚠️ **PaddleOCR has multiple compatibility issues with Python 3.13**. You MUST fix them manually.

### Issue 1: imghdr Module Removed

**Symptom:**
```
ModuleNotFoundError: No module named 'imghdr'
```

**Cause:** Python 3.13 removed the `imghdr` module (originally used for image type detection).

**Solution:** Create a shim module:

```python
# Save to site-packages/imghdr.py
"""imghdr module shim for Python 3.13+ compatibility"""
def whatfile(f):
    return None

def what(buf, h=None):
    return None
```

### Issue 2: np.sctypes Removed

**Symptom:**
```
AttributeError: module 'numpy' has no attribute 'sctypes'
```

**Cause:** NumPy 2.0 removed `np.sctypes` attribute (used by `imgaug` package).

**Solution:** Edit `site-packages/imgaug/imgaug.py` lines 44-46:

```python
# Original code (BROKEN):
# NP_FLOAT_TYPES = set(np.sctypes["float"])
# NP_INT_TYPES = set(np.sctypes["int"])
# NP_UINT_TYPES = set(np.sctypes["uint"])

# Fixed code:
NP_FLOAT_TYPES = {np.float16, np.float32, np.float64}
NP_INT_TYPES = {np.int8, np.int16, np.int32, np.int64}
NP_UINT_TYPES = {np.uint8, np.uint16, np.uint32, np.uint64}
```

### Issue 3: OpenCV Incompatible with NumPy 2.x

**Symptom:**
```
ImportError: numpy.core.multiarray failed to import
```

**Cause:** `opencv-python` 4.6 was compiled against NumPy 1.x, incompatible with NumPy 2.x ABI.

**Solution:** Use `opencv-python-headless` 4.13.0.92+:

```bash
~/.venvs/paddleocr/bin/pip uninstall opencv-python -y
~/.venvs/paddleocr/bin/pip install opencv-python-headless --no-cache-dir
```

### Issue 4: scikit-image DLL Load Failed (Windows)

**Symptom:**
```
ImportError: DLL load failed while importing _cython_blas
```

**Cause:** Windows security policy blocks unsigned C extension DLLs.

**Solutions:**
- Option A: Use pre-compiled wheel (Recommended)
- Option B: Temporarily disable Windows Defender Real-time Protection
- Option C: Use WSL2 or Linux environment

### Recommended Python 3.13 Installation

```bash
# Environment
python3 -m venv ~/.venvs/paddleocr
source ~/.venvs/paddleocr/bin/activate

# Install (use PaddlePaddle 3.0.0 which supports NumPy 2.x)
pip install paddlepaddle==3.0.0
pip install "numpy>=2" paddleocr==2.7.3
pip uninstall opencv-python -y
pip install opencv-python-headless --no-cache-dir

# Create imghdr shim
cat > ~/.venvs/paddleocr/lib/python3.13/site-packages/imghdr.py << 'EOF'
def whatfile(f):
    return None
def what(buf, h=None):
    return None
EOF

# Patch np.sctypes issue
# Manually edit ~/.venvs/paddleocr/lib/python3.13/site-packages/imgaug/imgaug.py
```

---

## CLI: OCR a Single Image

```bash
~/.venvs/paddleocr/bin/python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch')  # auto-downloads models on first run
result = ocr.ocr('image.png')
for line_info in result[0]:
    text = line_info[1][0]
    conf = line_info[1][1]
    print(f'{conf:.2f} {text}')
"
```

## Workflow: Scanned PDF → Structured Markdown

### Step 1: Split pages

Preferred (if OpenDataLoader installed):
```bash
opendataloader-pdf input_scan.pdf -f text -o ./pages
```

Alternative (pdf2image):
```bash
pip install pdf2image
python -c "
from pdf2image import convert_from_path
images = convert_from_path('input.pdf', dpi=300)
for i, img in enumerate(images):
    img.save(f'page_{i+1:03d}.png')
"
```

### Step 2: OCR each page

```python
from paddleocr import PaddleOCR
import os

ocr = PaddleOCR(lang='ch', use_angle_cls=True, use_gpu=False)
output_pages = {}

png_files = sorted([f for f in os.listdir('./pages') if f.endswith('.png')],
                   key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

for png in png_files:
    result = ocr.ocr(f'./pages/{png}')
    page_num = ''.join(filter(str.isdigit, png))
    lines = []
    for line_info in result[0]:
        text = line_info[1][0]
        conf = line_info[1][1]
        if conf > 0.6:
            lines.append(text)
    output_pages[page_num] = lines
```

### Step 3: Assemble Markdown

```markdown
# OCR Result — filename
> Engine: PaddleOCR PP-OCRv4 (Simplified Chinese)
> Pages: 17 | Date: YYYY-MM-DD

---

## Page 1

Body text...

---

## Page 2

Body text...
```

## Accuracy

| Engine | Simplified Chinese | Traditional Chinese | Seals/Signatures | Vertical Text |
|--------|-------------------|-------------------|------------------|---------------|
| Tesseract chi_sim | ~80% | ~60% | ❌ garbled | ❌ not supported |
| **PaddleOCR PP-OCRv4** | **~98%** | **~95%** | **✅ mostly correct** | **✅ supported** |
| **PaddleOCR + 预处理** | **~98%+** | **~96%** | **✅** | **✅** |

> 预处理（倾斜校正/文档展平）对手机拍照、弯曲文档提升 1~5%。
> 详见 SKILL.md D 节 `scripts/pdf_preprocess.py`。

## Troubleshooting

### Poor character accuracy?
- Increase DPI: minimum 300, recommended 400-600
- Lower confidence threshold: `if conf > 0.3` to retain more candidates
- Verify critical pages (signatures, amounts) with `vision_analyze`

### Poor table recognition?
PaddleOCR's table recognition (`lang='ch'` + `use_angle_cls=True`) is moderate. For dense tables, combine with the main `pdf-ocr-md` docling+PaddleOCR pipeline.

### GPU acceleration
```bash
~/.venvs/paddleocr/bin/pip install paddlepaddle-gpu==2.6.2
```
Set `use_gpu=True` when creating PaddleOCR.
