# Paddleocr Py313 Compat

> 来源: pdf-ocr-md v3.3.0 SKILL.md | 从主文件拆分，保持原内容不变

### Python 3.13 兼容性注意事项

> ⚠️ **重要**：PaddleOCR 在 Python 3.13 环境下存在多个兼容性问题，需手动修复。

#### 问题1：imghdr 模块缺失

**现象：**
```
ModuleNotFoundError: No module named 'imghdr'
```

**原因：** Python 3.13 移除了 `imghdr` 模块（原用于检测图像类型）

**解决方案：** 创建兼容 shim 模块

```python
# 保存到 site-packages/imghdr.py
"""imghdr module shim for Python 3.13+ compatibility"""
def whatfile(f):
    return None

def what(buf, h=None):
    return None
```

#### 问题2：np.sctypes 移除

**现象：**
```
AttributeError: module 'numpy' has no attribute 'sctypes'
```

**原因：** NumPy 2.0 移除了 `np.sctypees` 属性（`imgaug` 包使用了该属性）

**解决方案：** 修改 `site-packages/imgaug/imgaug.py` 第44-46行

```python
# 原代码（不可用）：
# NP_FLOAT_TYPES = set(np.sctypes["float"])
# NP_INT_TYPES = set(np.sctypes["int"])
# NP_UINT_TYPES = set(np.sctypes["uint"])

# 修复后：
NP_FLOAT_TYPES = {np.float16, np.float32, np.float64}
NP_INT_TYPES = {np.int8, np.int16, np.int32, np.int64}
NP_UINT_TYPES = {np.uint8, np.uint16, np.uint32, np.uint64}
```

#### 问题3：OpenCV 与 NumPy 2.x 不兼容

**现象：**
```
ImportError: numpy.core.multiarray failed to import
```

**原因：** `opencv-python` 4.6 是针对 NumPy 1.x 编译的，与 NumPy 2.x ABI 不兼容

**解决方案：** 改用 `opencv-python-headless` 4.13.0.92+

```bash
~/.venvs/paddleocr/bin/pip uninstall opencv-python -y
~/.venvs/paddleocr/bin/pip install opencv-python-headless --no-cache-dir
```

#### 问题4：scikit-image DLL 加载失败（Windows）

**现象：**
```
ImportError: DLL load failed while importing _cython_blas
```

**原因：** Windows 安全策略阻止未签名的 C 扩展 DLL

**解决方案：**
- 方案A：使用预编译的 wheel（推荐）
- 方案B：临时关闭 Windows Defender 实时保护
- 方案C：使用 WSL2 或 Linux 环境

#### 推荐的 Python 3.13 安装命令

```bash
# 环境
python3 -m venv ~/.venvs/paddleocr
source ~/.venvs/paddleocr/bin/activate

# 安装（使用 PaddlePaddle 3.0.0，支持 NumPy 2.x）
pip install paddlepaddle==3.0.0
pip install "numpy>=2" paddleocr==2.7.3
pip uninstall opencv-python -y
pip install opencv-python-headless --no-cache-dir

# 创建 imghdr shim
cat > ~/.venvs/paddleocr/lib/python3.13/site-packages/imghdr.py << 'EOF'
def whatfile(f):
    return None
def what(buf, h=None):
    return None
EOF

# 修补 np.sctypes 问题
# 手动编辑 ~/.venvs/paddleocr/lib/python3.13/site-packages/imgaug/imgaug.py
```