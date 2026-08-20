# 场景 9 [火车票识别]
**适用场景**: 火车票识别接口利用夸克高精度的基础OCR识别能力，结合夸克自研的文档大模型基础，实现对各种火车票内容信息的提取，支持"票号", "出发站", "到达站", "车次", "开车时间", "票价", "座位号", "座位类型", "旅客身份号码", "旅客姓名"等10个字段信息的提取，适用于企业出行报销等场景。

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
  --input-configs '{"function_option":"RecognizeTrainTicket"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTrainTicket"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTrainTicket"}' \
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
    "Result": [
      {
        "票号": {
          "Value": "************"
        },
        "出发站": {
          "Value": "************"
        },
        "到达站": {
          "Value": "************"
        },
        "车次": {
          "Value": "************"
        },
        "开车时间": {
          "Value": "************"
        },
        "票价": {
          "Value": "************"
        },
        "座位号": {
          "Value": "************"
        },
        "座位类型": {
          "Value": "************"
        },
        "旅客身份号码": {
          "Value": "************"
        },
        "旅客姓名": {
          "Value": "************"
        }
      }
    ]
  }
}
```

---

## 📋 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `票号` | Dict | 票号 |
| `出发站` | Dict | 出发站 |
| `到达站` | Dict | 到达站 |
| `车次` | Dict | 车次 |
| `开车时间` | Dict | 开车时间 |
| `票价` | Dict | 票价 |
| `座位号` | Dict | 座位号 |
| `座位类型` | Dict | 座位类型 |
| `旅客身份号码` | Dict | 旅客身份号码 |
| `旅客姓名` | Dict | 旅客姓名 |
| `XXX/Value` | string | 内容值 |
| `XXX/Position` | List[List[int, int]] | 内容位置（当返回结果包含矫正图时返回），以4个顶点坐标表示 |
| `XXX/PageIndex` | int | 输入为多页时，表示内容所在的页面索引 |

---

## 📝 输出逻辑

1. **成功识别**（`code: "00000"`）→ 解析 `data.Result`，按 Markdown 表格格式展示各字段
2. **识别失败**（任何非 `00000` 状态码）→ 直接返回错误信息，不重试、不切换场景
3. **任务结束** → 不再执行任何其他 OCR 操作，等待用户新指令

---

## 💡 完整示例

### 请求
```bash
python3 scripts/scan.py \
  --url "https://example.com/sample.jpg" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeTrainTicket"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 响应
```json
{
  "code": "00000",
  "message": null,
  "data": {
    "Result": [
      {
        "票号": {
          "Value": "************"
        },
        "出发站": {
          "Value": "************"
        },
        "到达站": {
          "Value": "************"
        },
        "车次": {
          "Value": "************"
        },
        "开车时间": {
          "Value": "************"
        },
        "票价": {
          "Value": "************"
        },
        "座位号": {
          "Value": "************"
        },
        "座位类型": {
          "Value": "************"
        },
        "旅客身份号码": {
          "Value": "************"
        },
        "旅客姓名": {
          "Value": "************"
        }
      }
    ]
  }
}
```

### 调用方展示
| 字段 | 值 |
|------|-----|
| 票号 | ************ |
| 出发站 | ************ |
| 到达站 | ************ |
| 车次 | ************ |
| 开车时间 | ************ |
| 票价 | ************ |
| 座位号 | ************ |
| 座位类型 | ************ |
| 旅客身份号码 | ************ |
| 旅客姓名 | ************ |

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
