# 场景 14 [英文发票识别]
**适用场景**: 商业发票识别接口利用夸克高精度的基础OCR识别能力，结合夸克自研的文档大模型基础，实现对各种不同格式和不同语种的商业发票结构化内容提取，支持常见的12个字段以及20多个扩展字段，准确率97%。商业发票识别接口适用于外贸场景处理各种海外商业发票，能够极大降低人工成本。

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
  --input-configs '{"function_option":"RecognizeCommercialInvoice"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeCommercialInvoice"}' \
  --output-configs '{"need_return_image":"false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "structure" \
  --input-configs '{"function_option":"RecognizeCommercialInvoice"}' \
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
        "CoverWord": {
          "Value": "INVOICE"
        },
        "VendorName": {
          "Value": "Vistra Corporate Services (HK) Limited"
        },
        "VendorAddress": {
          "Value": "19/F,LeeGardenOne,33HysanAve,CausewayBay,HongKong"
        },
        "VendorTaxID": {
          "Value": ""
        },
        "PurchaserName": {
          "Value": "Whale(Cayman) Co., Ltd"
        },
        "PurchaserAddress": {
          "Value": "P. O. Box 31119 Grand Pavilion"
        },
        "Number": {
          "Value": "300730"
        },
        "Date": {
          "Value": "2023-10-13"
        },
        "TaxRate": {
          "Value": ""
        },
        "NetAmount": {
          "Value": ""
        },
        "GrossAmount": {
          "Value": "3,725.00"
        },
        "TaxAmount": {
          "Value": ""
        },
        "Currency": {
          "Value": "USD"
        },
        "PurchaseOrderNumber": {
          "Value": [
            "PO12345678",
            "PO12345678"
          ]
        },
        "IsMultiInvoice": {
          "Value": false
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
| `CoverWord` | Dict | 发票标题 |
| `VendorName` | Dict | 销售方名称 |
| `VendorAddress` | Dict | 销售方地址 |
| `VendorTaxID` | Dict | 销售方税号 |
| `PurchaserName` | Dict | 购买方名称 |
| `PurchaserAddress` | Dict | 购买方地址 |
| `Number` | Dict | 发票号码 |
| `Date` | Dict | 发票日期 |
| `TaxRate` | Dict | 发票税率 |
| `NetAmount` | Dict | 发票不含税金额 |
| `GrossAmount` | Dict | 发票含税金额 |
| `TaxAmount` | Dict | 发票税额 |
| `Currency` | Dict | 发票币种 |
| `PurchaseOrderNumber` | Dict | 采购订单号 |
| `IsMultiInvoice` | Dict | 是否为多张发票 |
| `XXX/Value` | Enum[string, bool, List[string]] | 内容值，当输出为多个值时数据类型为List |
| `XXX/Position` | Enum[List[List[int,int]],List[List[List[int,int]]]] | 内容位置（当返回结果包含矫正图时返回），以4个顶点坐标表示 |
| `XXX/PageIndex` | Enum[int, List[int]] | 输入为多页时，表示内容所在的页面索引 |

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
  --input-configs '{"function_option":"RecognizeCommercialInvoice"}' \
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
        "CoverWord": {
          "Value": "INVOICE"
        },
        "VendorName": {
          "Value": "Vistra Corporate Services (HK) Limited"
        },
        "VendorAddress": {
          "Value": "19/F,LeeGardenOne,33HysanAve,CausewayBay,HongKong"
        },
        "VendorTaxID": {
          "Value": ""
        },
        "PurchaserName": {
          "Value": "Whale(Cayman) Co., Ltd"
        },
        "PurchaserAddress": {
          "Value": "P. O. Box 31119 Grand Pavilion"
        },
        "Number": {
          "Value": "300730"
        },
        "Date": {
          "Value": "2023-10-13"
        },
        "TaxRate": {
          "Value": ""
        },
        "NetAmount": {
          "Value": ""
        },
        "GrossAmount": {
          "Value": "3,725.00"
        },
        "TaxAmount": {
          "Value": ""
        },
        "Currency": {
          "Value": "USD"
        },
        "PurchaseOrderNumber": {
          "Value": [
            "PO12345678",
            "PO12345678"
          ]
        },
        "IsMultiInvoice": {
          "Value": false
        }
      }
    ]
  }
}
```

### 调用方展示
| 字段 | 值 |
|------|-----|
| CoverWord | INVOICE |
| VendorName | Vistra Corporate Services (HK) Limited |
| VendorAddress | 19/F,LeeGardenOne,33HysanAve,CausewayBay,HongKong |
| VendorTaxID |  |
| PurchaserName | Whale(Cayman) Co., Ltd |
| PurchaserAddress | P. O. Box 31119 Grand Pavilion |
| Number | 300730 |
| Date | 2023-10-13 |
| TaxRate |  |
| NetAmount |  |
| GrossAmount | 3,725.00 |
| TaxAmount |  |
| Currency | USD |
| PurchaseOrderNumber | ['PO12345678', 'PO12345678'] |
| IsMultiInvoice | False |

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
