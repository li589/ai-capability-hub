# 场景 11 [题目识别]
**适用场景**: 题目切分采用先进的AI技术，针对全年龄段各学科试卷题目具备精准切分能力，通过全局智能理解实现灵活的细粒度切分，支持含手写、复杂排版、密集大版面等各类题目场景。

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
  --input-configs '{"function_option":"RecognizeQuestion"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeQuestion"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeQuestion"}' \
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
    "StructureInfo": [
      {
        "Detail": [
          {
            "InGraph": "false",
            "Type": "PrintedText",
            "Confidence": 1,
            "Value": "联系人:刘书生"
          },
          {
            "InGraph": "false",
            "Type": "PrintedText",
            "Confidence": 1,
            "Value": "手机:"
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
| `StructureInfo` | List[Dict] | 图片的结构信息 |
| `StructureInfo/Detail` | List[Dict] | 图片中的内容详情 |
| `Detail/InGraph` | bool | 当图片内容为文本时，文本是否在图片中的插图、印章、流程图等其中 |
| `Detail/Type` | string | 内容类型，PrintedText｜WrittenText｜PrintedFormula ｜ WrittenFormula ｜ Illustration ｜ Stamp 等分别表示印刷文字｜手写文字｜印刷公式｜手写公式 ｜插图｜印章等 |
| `Detail/Confidence` | float | 内容置信度 |
| `Detail/Value` | string | 内容值 |
| `Detail/InGraph` | bool | 当图片内容为文本时，文本是否在图片中的插图、印章、流程图等其中 |
| `Detail/Type` | string | 内容类型，PrintedText｜WrittenText｜PrintedFormula ｜ WrittenFormula ｜ Illustration ｜ Stamp 等分别表示印刷文字｜手写文字｜印刷公式｜手写公式 ｜插图｜印章等 |
| `Detail/Confidence` | float | 内容置信度 |
| `Detail/Value` | string | 内容值 |

---

## 📝 输出逻辑

1. **成功识别**（`code: "00000"`）→ 解析 `data.StructureInfo`，按 Markdown 表格格式展示
2. **识别失败**（任何非 `00000` 状态码）→ 直接返回错误信息，不重试、不切换场景
3. **任务结束** → 不再执行任何其他 OCR 操作，等待用户新指令

---

## 💡 完整示例

### 请求
```bash
python3 scripts/scan.py \
  --url "https://example.com/sample.jpg" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeQuestion"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 响应
```json
{
  "code": "00000",
  "message": null,
  "data": {
    "StructureInfo": [
      {
        "Detail": [
          {
            "InGraph": "false",
            "Type": "PrintedText",
            "Confidence": 1,
            "Value": "联系人:刘书生"
          },
          {
            "InGraph": "false",
            "Type": "PrintedText",
            "Confidence": 1,
            "Value": "手机:"
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
| Detail | [{'InGraph': 'false', 'Type': 'PrintedText', 'Confidence': 1, 'Value': '联系人:刘... |

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
