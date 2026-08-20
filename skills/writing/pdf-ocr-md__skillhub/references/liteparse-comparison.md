# LiteParse 实测数据与使用备忘

> 版本：`liteparse 2.0.4`（pip install），Rust 核心 + Python 绑定
> 安装：`~/.venvs/liteparse/`，CLI wrapper `~/.local/bin/lit`

## 实测性能

| 场景 | 耗时 | 准确率 | 命令 |
|------|------|--------|------|
| 文本层PDF（中文） | **0.9ms** | 100% | `lit parse --no-ocr` |
| 文本层PDF（英文） | **0.8ms** | 100% | `lit parse --no-ocr` |
| 中文扫描件（Tesseract） | **172ms** | ~80% | `lit parse --ocr-language chi_sim` |
| 中文扫描件（PaddleOCR） | **25.8s** | ~97% | `pdf2md`（退到 pdf-ocr-md B 节） |
| Screenshot（PDF→PNG） | ~15ms/页 | — | `lit screenshot --dpi 200` |

## GFW 下的 tessdata 处理

LiteParse 的 Tesseract 默认在 `~/.tesseract-rs/tessdata/` 找语言包。
从 GitHub 下载 `chi_sim.traineddata` 在 GFW 下会超时。解决方案：

```bash
# 方案：链接系统已安装的 tessdata
ln -sf /usr/share/tesseract-ocr/5/tessdata/chi_sim.traineddata ~/.tesseract-rs/tessdata/chi_sim.traineddata
ln -sf /usr/share/tesseract-ocr/5/tessdata/eng.traineddata ~/.tesseract-rs/tessdata/eng.traineddata
```

如果系统未安装，通过 apt 装：
```bash
apt install tesseract-ocr-chi-sim  # 国内源畅通
```

## 与 PaddleOCR 的选择策略

```
收到文件
→ lit parse --no-ocr        (0.9ms，有文本层直接出)
→ 空结果 = 扫描件
   ├─ 中文 → pdf2md          (25s，准确优先)
   └─ 英文 → lit parse       (170ms，够用)
```

## OpenDataLoader 弃用说明

LiteParse 作为文本层 PDF 提取方案已完全替代 OpenDataLoader：
- 速度快 300x（0.9ms vs 300ms 每 17 页）
- 无需 Java 11，无需单独 venv
- PDFium 引擎同等准确
- 保留 OpenDataLoader 章节作为备用，不主动推荐

## 已知限制

- `lit screenshot` 生成整页 PNG 适合喂给 LLM vision，但分辨率低于 `pdf2md` 的 `images/` 输出
- 不支持指定页码范围截图？实测 `--target-pages` 参数可用
- 本文实测环境：3.6GB RAM，`lit` 进程 ~50MB
