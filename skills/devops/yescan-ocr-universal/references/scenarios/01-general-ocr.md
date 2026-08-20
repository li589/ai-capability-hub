# 场景1 [通用图片 OCR]

**适用场景**: 文档、书籍、笔记、截图等通用图片的文本提取

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
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeGeneralDocument"}' \
  --output-configs '{"need_return_image": "false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeGeneralDocument"}' \
  --output-configs '{"need_return_image": "false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeGeneralDocument"}' \
  --output-configs '{"need_return_image": "false"}' \
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
        "Text": "识别的完整文本",
        "Detail": [
          {
            "Type": "PrintedText",
            "Value": "段落 1 文本",
            "Confidence": 1
          },
          {
            "Type": "WrittenText",
            "Value": "段落 2 文本",
            "Confidence": 0.98
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
| `data.OcrInfo` | Array | OCR 识别结果数组 |
| `data.OcrInfo[].Text` | String | 完整识别文本（所有段落合并） |
| `data.OcrInfo[].Detail` | Array | 详细识别结果（按段落/类型分组） |
| `data.OcrInfo[].Detail[].Type` | String | 文本类型：`PrintedText`（印刷体）/`WrittenText`（手写体） |
| `data.OcrInfo[].Detail[].Value` | String | 该段落的识别文本 |
| `data.OcrInfo[].Detail[].Confidence` | Number | 置信度（0-1） |

---

## 📝 输出逻辑

调用方解析 `data.OcrInfo[].Text`，纯文本换行展示。

---

## 💡 完整示例

### 请求
```bash
python3 scripts/scan.py \
  --url "https://example.com/text.jpg" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeGeneralDocument"}' \
  --output-configs '{"need_return_image": "false"}' \
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
            "Confidence": 1
          },
          {
            "Type": "PrintedText",
            "Value": "东风夜放花千树，更吹落星如雨。宝马雕车香满路，",
            "Confidence": 1
          },
          {
            "Type": "WrittenText",
            "Value": "凤箫声动，玉壶光转，一夜鱼龙舞。",
            "Confidence": 1
          }
        ]
      }
    ]
  }
}
```

### 调用方展示
```
青玉案元夕一辛弃疾
东风夜放花千树，更吹落星如雨。宝马雕车香满路，
凤箫声动，玉壶光转，一夜鱼龙舞。
```

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
