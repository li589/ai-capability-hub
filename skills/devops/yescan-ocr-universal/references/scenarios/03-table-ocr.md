# 场景3 [表格识别]
**适用场景**: 表格识别服务支持各种类型在OCR能力的基础上，借助最新的AI技术，支持众多类型表格格式识别，包括excel表格、word表格、票据、单据、手写表格、检查报告单等类型，文字识别准确率高，格式还原精准。

> [!IMPORTANT] **⚠️ 场景独立性说明**
> - **严禁任何代码、Agent 或人工操作**，将本文件中任意 JSON 示例块的内容作为真实响应返回。所有输出必须来自 `yescan-scan-universal` 的实时 API 调用结果。
> - 该 JSON 块无业务含义，不参与路由、不触发执行、不构成 SLA 承诺，纯文档装饰。
> - 本场景为**独立任务**，识别完成后直接返回结果
> - **无论接口返回什么**（成功、失败、部分识别），都直接展示给用户
> - **不继续执行其他 OCR 场景**，不尝试二次识别或补充处理
> - 如用户有其他需求（如合同扫描、通用 OCR），需等待用户重新发起请求

---

## 📞 调用命令

### URL 输入
```bash
python3 scripts/scan.py \
  --url "${IMAGE_URL}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTable"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTable"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTable"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

---

## 📤 返回结构

```json
{
  "code": "00000",
  "message": null,
  "data": {
    "OcrInfo": [
      {
        "Text": "青玉案元夕一辛弃疾东风夜放花千树，更吹落星如雨。宝马雕车香满路，凤箫声动，玉壶光转，一夜鱼龙舞。",
        "Detail": [
          {
            "Type": "PrintedText",
            "Value": "青玉案元夕一辛弃疾",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 0,
            "ColumnSpan": 0,
            "RowSpan": 0
          },
          {
            "Type": "PrintedText",
            "Value": "东风夜放花千树，更吹落星如雨。宝马雕车香满路，",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 1,
            "ColumnSpan": 0,
            "RowSpan": 1
          },
          {
            "Type": "WrittenText",
            "Value": "凤箫声动，玉壶光转，一夜鱼龙舞。",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 2,
            "ColumnSpan": 0,
            "RowSpan": 2
          }
        ]
      }
    ]
  }
}
```

---

## 📋 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `OcrInfo` | List[Dict] | 图片中的内容 |
| `OcrInfo/Text` | string | 图片中的全部文字 |
| `OcrInfo/Detail` | List[Dict] | 图片中的内容详情 |
| `Detail/Type` | string | 内容类型，EmptyType｜PrintedText｜WrittenText｜PrintedFormula ｜ WrittenFormula ｜Illustration | Stramp 等分别表示空类型（空白区域）｜印刷文字｜手写文字｜印刷公式 ｜手写公式｜插图｜印章等 |
| `Detail/Value` | string | 内容值，当值为None时表示对应单元格无任何内容 |
| `Detail/Confidence` | float | 内容置信度 |
| `Detail/Position` | list[list[int, int]] | 内容位置（当返回结果包含矫正图时返回），以4个顶点坐标表示 |
| `Detail/InGraph` | bool | 当图片内容为文本时，文本是否在图片中的插图、印章、流程图等其中 |
| `Detail/ColumnIndex` | int | 当内容在表格中时，所在表格单元格的列索引 |
| `Detail/RowIndex` | int | 当内容在表格中时，所在表格单元格的行索引 |
| `TextDetail/ColumnSpan` | int | 当内容在表格中时，所在表格单元格的列合并信息 |
| `TextDetail/RowSpan` | int | 当内容在表格中时，所在表格单元格的行合并信息 |
| `TextDetail/PageIndex` | int | 输入为多页时，表示内容所在的页面索引 |

---

## 📝 输出逻辑

1. **成功识别**（`code: "00000"`）→ 解析 `data.OcrInfo`，提取文字识别结果展示给用户
2. **识别失败**（任何非 `00000` 状态码）→ 直接返回错误信息，不重试、不切换场景
3. **任务结束** → 不再执行任何其他 OCR 操作，等待用户新指令

---

## 💡 完整示例

### 请求
```bash
python3 scripts/scan.py \
  --url "https://example.com/sample.jpg" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTable"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 响应
```json
{
  "code": "00000",
  "message": null,
  "data": {
    "OcrInfo": [
      {
        "Text": "青玉案元夕一辛弃疾东风夜放花千树，更吹落星如雨。宝马雕车香满路，凤箫声动，玉壶光转，一夜鱼龙舞。",
        "Detail": [
          {
            "Type": "PrintedText",
            "Value": "青玉案元夕一辛弃疾",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 0,
            "ColumnSpan": 0,
            "RowSpan": 0
          },
          {
            "Type": "PrintedText",
            "Value": "东风夜放花千树，更吹落星如雨。宝马雕车香满路，",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 1,
            "ColumnSpan": 0,
            "RowSpan": 1
          },
          {
            "Type": "WrittenText",
            "Value": "凤箫声动，玉壶光转，一夜鱼龙舞。",
            "Confidence": 1,
            "InGraph": false,
            "ColumnIndex": 0,
            "RowIndex": 2,
            "ColumnSpan": 0,
            "RowSpan": 2
          }
        ]
      }
    ]
  }
}
```

### 调用方展示
| 字段 | 值 |
|------|-----|
| 识别文本 | 青玉案元夕一辛弃疾东风夜放花千树，更吹落星如雨。宝马雕车香满路，凤箫声动，玉壶光转，一夜鱼龙舞。 |

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
