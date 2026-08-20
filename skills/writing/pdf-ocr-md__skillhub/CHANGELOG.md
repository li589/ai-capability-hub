# Changelog

## [3.4.0] - 2026-07-30
### Changed
- **SKILL.md 分层精简** — 从 578 行缩减至 82 行（-83%），对标 OpenAI 上下文压缩策略
- 详细教程按主题拆分为 6 个独立 references 文件（按需加载）：LiteParse / PaddleOCR Python 3.13 / 预处理 / 结构化解析 / PP-OCRv6 / 完整备份
- 保留 SKILL.md 核心：快速选择命令 + 工作流 + 性能速查 + 注意事项
- 新增预处理关键词标注（deskew/orient/unwarp）

### Added
- **ppocrv6-guide.md 更新** — 新增官方 v3.7.0 50 语言统一模型、Apple Silicon CoreML 加速、浏览器端运行、Web 工作台、OpenVINO 加速数据

## [3.3.0] - 2026-06-26
### Added
- **GPU 加速** — DirectML 后端支持 Intel/AMD/NVIDIA GPU，默认 GPU 推理
  - `--device cpu|gpu` 参数，默认 gpu
  - Intel Arc B390 提速 6-9x（Tiny 10.5ms, Small 18.7ms, Medium 48.6ms）
  - 需 `onnxruntime-directml` 替代 `onnxruntime`

### Fixed
- **det 后处理修复** — 4D 输出 squeeze + ImageNet 归一化
- **rec 后处理修复** — char_dict 使用 list 索引（非 dict 查找）+ CTC 解码
- **Small/Medium 字符字典** — 自动从 inference.yml 解析 character_dict

### Changed
- SKILL.md F 节标题更新为"GPU 加速"
- 迁移说明更新，提及 DirectML 提速数据
- `pdf_ocr_v6.py` 新增字符字典诊断输出

---

## [3.2.0] - 2026-06-21
### Added
- **新增 F 节：PP-OCRv6 三档模型 OCR** — 基于 ONNX Runtime，无需 PaddlePaddle 框架
  - Tiny (1.5 MB)：极速，可浏览器端运行
  - Small (7.7 MB)：性能均衡
  - Medium (34.5 MB)：精度最高
  - CLI 工具: `scripts/pdf_ocr_v6.py` (支持 --tier 切换)
- 脚本: `scripts/pdf_ocr_v6.py` — PP-OCRv6 ONNX Runtime 推理 CLI
- 性能参照表新增 PP-OCRv6 三档数据
- 准确率表新增 OmniDocBench 评测数据

### Changed
- 快速选择流程更新：扫描件优先推荐 PP-OCRv6
- 工作流总览加入模型档位选择步骤
- 版本号 3.1.0 → 3.2.0
- description 更新提及 PP-OCRv6 三档模型

---

## [3.1.0] - 2026-06-14
### Changed
- **Description 重写为意图路由型** — 按 Anthropic Skill 方法论，从功能介绍型改为"当用户需要...时使用"格式
- **移除常识性内容（~2.4KB）** — 保留 Gotchas（Python 3.13 兼容性等），移除模型已知的代码示例、JSON 示例、安装命令
- **OpenDataLoader 节大幅精简** — 从 30 行压缩到 3 行，详情迁至 references
- 版本号 3.0.0 → 3.1.0

### Removed
- PaddleOCR 基础 Python 代码示例（模型已知 API）
- LiteParse 安装命令（pip install 是常识）
- D 节 Python import 示例
- E 节 JSON 结构示例

---

## [3.0.0] - 2026-06-13
### Added
- **新增 D 节：文档预处理** — OpenCV 驱动的扫描件增强管线
  - 倾斜校正 (deskew)：Hough 变换检测文本角度, 自动旋转
  - 方向校正 (orient)：文本投影分析, 自动旋转倒置/侧向页面
  - 文档展平 (unwarp)：透视变换校正弯曲/变形的文档照片
  - CLI 工具: `scripts/pdf_preprocess.py` (支持 PDF + 单图)
  - 预览模式: `--preview` 显示原图 vs 处理对比
- **新增 E 节：结构化文档解析** — docling 版面分析 + 结构化输出
  - 标题层级识别、段落/列表/表格结构化输出
  - 表格提取为 Markdown 表格 + JSON 网格
  - CLI 工具: `scripts/pdf_parse_structured.py`
  - 输出: 结构化 Markdown + 含 bbox 坐标的 JSON
- **scripts/ 目录** — 独立的 Python 工具脚本, 可 CLI 调用或作为模块导入
- 性能参照表新增预处理和结构化解析行
- 准确率表新增"预处理后"行 (~98%+)

### Changed
- 工作流更新: 扫描件建议走 `prep` → `pdf2md` / `structured_parse`
- 版本号 2.2.0 → 3.0.0
- description 更新提及预处理和结构化解析

---

## [2.2.0] - 2026-06-05
### Added
- Python 3.13 兼容性说明（imghdr、np.sctypes、OpenCV）
- Windows 平台注意事项（编码、文件路径、DLL 加载）
- 最佳实践章节（分阶段验证、独立虚拟环境、预检查依赖）

### Changed
- 更新 B 节（PaddleOCR）添加 Python 3.13 兼容性注意事项
- 更新 references/paddleocr.md 添加 Python 3.13 兼容性章节
- 版本号 2.1.0 → 2.2.0

---

## [2.1.0] - 2026-06-03
### Added
- LiteParse（Rust）快速通道，文本层 PDF 解析从 ~300ms 降至 ~0.9ms/页
- 新增 `lit parse input.pdf --no-ocr` CLI 命令
- PaddleOCR 中文扫描件保留为默认 OCR 引擎（~97%+）
- LiteParse 截图输出功能（`lit screenshot`）
- 快速选择流程：先试 LiteParse --no-ocr，空结果退到 pdf2md

### Changed
- 工作流由 OpenDataLoader 优先改为 LiteParse 优先
- 性能参照表扩充为 5 行（含 LiteParse / Tesseract / PaddleOCR 对比）
- description 更新提及 LiteParse 和 Office 格式支持

### Removed
- OpenDataLoader 不再作为默认建议（保留为备选，需 Java 11）

## [1.1.0] - 2026-05-14
### Changed
- 正式更名为 `pdf-ocr-md`（原 `pdf2md` 在 SkillHub/ClawHub 已被占用）
- SKILL.md 内 name、标题同步更新

## [1.0.0] - 2026-05-14
### Added
- 初始版本
- 文本层 PDF：OpenDataLoader 直读（~0.015s/页）
- 扫描件：docling 版面分析 + PaddleOCR PP-OCRv4（中文 ~97%+）
- CLI 封装（~/.local/bin/pdf2md）
- 模型自动下载（hf-mirror / modelscope，国内畅通）
