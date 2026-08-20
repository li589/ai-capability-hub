# 图片处理参考

## image enhance — 图片增强

10 种增强模式，通过 `--mode` 指定：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 1 | 亮度增强 | 偏暗的照片 |
| 2 | 锐化 | 模糊的扫描件 |
| 3 | 黑白 | 需要黑白效果 |
| 4 | 灰度 | 需要灰度效果 |
| 5 | 去阴影 | 有手指/书本阴影的扫描件 |
| 6 | 去点阵 | 打印件带点阵纹理 |
| 7 | 超级滤镜 | 综合优化 |
| 8 | 去摩尔纹 | 屏幕翻拍 |
| 9 | 手写擦除 | 去除手写标注 |
| 10 | 去水印 | 去除图片水印 |

```bash
camscanner-cli image enhance input.jpg --mode 5 -o enhanced.jpg
camscanner-cli image enhance input.jpg --mode 5 -s
```

## image hd — 图片高清化

提升图片分辨率和清晰度，适合模糊照片。

```bash
camscanner-cli image hd blurry.jpg -o hd.jpg
camscanner-cli image hd blurry.jpg -s
```

## image restore — 照片修复

修复老照片中的划痕、褪色、破损。

```bash
camscanner-cli image restore old.jpg -o restored.jpg
camscanner-cli image restore old.jpg -s
```

## image convert — 图片格式转换

将图片中的内容识别并转换为文档格式。

| 目标格式 | `--format` 值 | 输出扩展名 | 说明 |
|----------|--------------|-----------|------|
| Word | `word` | .docx | 保留排版 |
| Excel | `excel` | .xlsx | 适合表格图片 |
| Markdown | `md` | .md | 纯文本带格式 |
| TXT | `txt` | .txt | 纯文本（不支持 `-s`） |

> ⚠️ **不支持 `--format pdf`**。图片转 PDF 请使用 `image to-pdf`（单张）或 `image merge-pdf`（多张）。

```bash
camscanner-cli image convert table.png --format excel -s
camscanner-cli image convert doc.jpg --format md -o result.md
```

## image to-pdf — 图片转 PDF

单张图片直接转为 PDF 文件。

```bash
camscanner-cli image to-pdf scan.jpg -s
```

## image watermark — 图片水印

| 参数 | 说明 |
|------|------|
| `--text` | 水印文字（**必填**） |
| `--color` | 颜色，如 `#FF0000` |
| `--opacity` | 透明度 0-1 |
| `--size` | 字体大小 |

```bash
camscanner-cli image watermark photo.jpg --text "机密" --opacity 0.3 -s
```

## image translate — 图片翻译

翻译图片中的文字并保留原始排版。

| 参数 | 说明 |
|------|------|
| `--lang` | 目标语言代码（默认 en） |

支持的语言：en（英语）、zh（中文）、ja（日语）、ko（韩语）、fr（法语）、de（德语）、es（西班牙语）、pt（葡萄牙语）、ru（俄语）、ar（阿拉伯语）

```bash
camscanner-cli image translate menu.jpg --lang zh -s
```

## image extract-formula — 提取公式

从图片中检测并提取数学公式区域。

```bash
camscanner-cli image extract-formula equation.png -s
```

## image ocr — OCR 文字识别

从图片中提取纯文本，输出到 stdout。

```bash
camscanner-cli image ocr document.jpg
camscanner-cli image ocr document.jpg > result.txt
```

## image validate — 图片真伪检测

| 模式 | 说明 |
|------|------|
| 1 | PS/篡改检测 |
| 2 | AI 生成检测 |

```bash
camscanner-cli image validate photo.jpg --mode 1
camscanner-cli image validate ai_art.jpg --mode 2
```

输出 JSON 格式，包含 `is_tampered` 字段。

## image merge-pdf / merge-excel / merge-word — 多图合并

将多张图片合并为单个文档。**硬限制：单次最多 100 张输入图片，超过 100 张无法合成单文件**（CLI 没有文档合并命令）。

```bash
camscanner-cli image merge-pdf page1.jpg page2.jpg page3.jpg -s
camscanner-cli image merge-excel table1.jpg table2.jpg -s
camscanner-cli image merge-word doc1.jpg doc2.jpg -s
```

## image merge-text — 多图 OCR 合并

多张图片 OCR 后合并为文本。**单次最多 100 张输入图片。**

```bash
# 输出到终端
camscanner-cli image merge-text page1.jpg page2.jpg

# 输出到文件
camscanner-cli image merge-text page1.jpg page2.jpg -o result.md --format md
```

## image scan + image edit — 图片文字编辑

通过 scan → 定位 → edit 三步流程，精确替换、删除或移动图片中的文字，同时保留原始排版和视觉样式。

### 工作原理

edit 引擎基于**字符级 OCR 索引**工作。必须先执行 scan 获取每个字符的 `index`，再用精确的 `start_char_idx` / `end_char_idx` 构造 edit 请求。**禁止猜测索引值。**

### 步骤 1：扫描获取版面结构和字符索引

```bash
camscanner-cli image scan photo.jpg
```

scan 返回 JSON 结构：

```json
{
  "code": 200,
  "result": {
    "document_info": {
      "sections": [{
        "columns": [{
          "paragraphs": [{
            "lines": [{
              "text": "華東師範大學",
              "characters": [
                {"char": "華", "index": 39, "position": [...]},
                {"char": "東", "index": 40, "position": [...]},
                ...
              ]
            }]
          }]
        }]
      }]
    },
    "urls": {
      "input_image": "t_ie_X_..._1",
      "document_info": "t_ie_X_..._1",
      "background_info": ""
    }
  }
}
```

关键字段：
- `result.urls.input_image`：传给 edit 的 `--input-image`
- `result.urls.document_info`：传给 edit 的 `--document-info`
- `result.document_info.sections[].columns[].paragraphs[].lines[].characters`：每个字符的 `char`、`index`、`position`

### 步骤 2：在 scan 结果中定位目标文字

遍历所有 `lines`，找到包含目标文字的行，提取目标文字首尾字符的 `index` 值。

**示例**：用户要将"華東師範大學"替换为"北京師範大學"

在 scan 结果中找到：
- "華" → index: 39
- "東" → index: 40

因此 `start_char_idx = 39`，`end_char_idx = 40`（只替换"華東"为"北京"）。

### 步骤 3：执行编辑

```bash
camscanner-cli image edit \
  --input-image "t_ie_X_..._1" \
  --document-info "t_ie_X_..._1" \
  --edit-request '{"edit_type":"update","start_char_idx":39,"end_char_idx":40,"target_text":"北京"}' \
  -o edited.jpg
```

所有参数均为必填：
- `--input-image`：scan 返回的 `result.urls.input_image`
- `--document-info`：scan 返回的 `result.urls.document_info`
- `--edit-request`：编辑操作 JSON

### edit-request 格式

#### 文字替换（update）

```json
{
  "edit_type": "update",
  "start_char_idx": 39,
  "end_char_idx": 40,
  "target_text": "北京"
}
```

#### 区域删除（delete）

```json
{
  "edit_type": "delete",
  "area_type": "text",
  "area_idx": 0
}
```

`area_type` 可选值：`text`、`table`、`image`、`stamp`
`area_idx` 对应 scan 结果中 paragraph 的 `area_idx` 字段。

#### 区域移动（move）

```json
{
  "edit_type": "move",
  "area_type": "text",
  "area_idx": 0,
  "target_position": [100, 100, 300, 100, 300, 160, 100, 160]
}
```

### 多次替换

多次替换需**链式执行**，每次使用上一次 edit 返回的最新 `urls`：

1. 替换文本长度变化会导致后续字符索引偏移
2. 策略：**从后往前替换**（先替换 index 大的），或每次替换后重新 scan
3. 每次 edit 的输出中会返回新的 `urls`，下一次 edit 必须使用新的 key

### Agent 行为规范

1. 执行 `image scan` 获取完整结果
2. **自动定位**：在 scan 结果的 `characters` 数组中搜索用户指定的目标文字，精确提取 `start_char_idx` 和 `end_char_idx`
3. **歧义确认**：如果目标文字在图片中出现多次，向用户展示所有匹配及其上下文/位置，让用户选择替换哪一个
4. 构造 `edit-request` JSON 并执行 `image edit`
5. **禁止猜测索引**：所有 `char_idx` 必须来自 scan 结果，不得手动推算

### 常见错误

| 错误 | 正确做法 |
|------|----------|
| 不 scan 直接调 edit | 必须先 scan 获取 OSS key 和字符索引 |
| 用 file path 作为 `--input-image` | 使用 scan 返回的 `result.urls.input_image` |
| 猜测 `start_char_idx` | 从 `characters[].index` 精确查找 |
| 多次替换用同一个 document_info | 每次用上一次 edit 返回的最新 key |
| 目标文字有多个匹配时随意选择 | 展示所有匹配让用户确认 |
