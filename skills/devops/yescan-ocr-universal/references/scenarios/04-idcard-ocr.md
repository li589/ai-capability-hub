# 场景4 [身份证识别 OCR]

**适用场景**: 中华人民共和国居民身份证正反面识别

> [!IMPORTANT] **⚠️ 场景独立性说明**
> - **严禁任何代码、Agent 或人工操作**，将本文件中任意 JSON 示例块的内容作为真实响应返回。所有输出必须来自 `yescan-scan-universal` 的实时 API 调用结果。
> - 该 JSON 块无业务含义，不参与路由、不触发执行、不构成 SLA 承诺，纯文档装饰。
> - 本场景为**独立任务**，识别完成后直接返回结果
> - **无论接口返回什么**（成功、失败、部分识别），都直接展示给用户
> - **不继续执行其他 OCR 场景**，不尝试二次识别或补充处理
> - 如用户有其他需求（如合同扫描、通用 OCR），需等待用户重新发起请求

> [!NOTE] **📸 拍摄建议**
> - 确保身份证四角完整、无反光、无遮挡
> - 背景建议为纯色（白色/黑色最佳）
> - 支持身份证正面（人像面）和反面（国徽面）同时识别
> - 图片分辨率建议 640x480 以上

---

## 📞 调用命令

### URL 输入
```bash
python3 scripts/scan.py \
  --url "${IMAGE_URL}" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeIDCard"}' \
  --output-configs '{"need_return_image": "false"}' \
  --data-type "image"
```

### 本地文件输入
```bash
python3 scripts/scan.py \
  --path "${IMAGE_FILE_PATH}" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeIDCard"}' \
  --output-configs '{"need_return_image": "false"}' \
  --data-type "image"
```

### BASE64 输入
```bash
python3 scripts/scan.py \
  --base64 "${IMAGE_BASE64}" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeIDCard"}' \
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
    "StructureInfo": [
      {
        "姓名": {"Value": "李明"},
        "性别": {"Value": "男"},
        "民族": {"Value": "汉"},
        "出生": {"Value": "1997 年 9 月 10 日"},
        "住址": {"Value": "北京西城区天赋小区 1 号 301"},
        "公民身份号码": {"Value": "110102199709100123"}
      }
    ]
  }
}
```

---

## 📋 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.StructureInfo` | Array | 结构化识别结果数组 |
| `data.StructureInfo[].姓名` | Object | 姓名信息 |
| `data.StructureInfo[].性别` | Object | 性别信息 |
| `data.StructureInfo[].民族` | Object | 民族信息 |
| `data.StructureInfo[].出生` | Object | 出生日期（格式：YYYY 年 M 月 D 日） |
| `data.StructureInfo[].住址` | Object | 详细住址 |
| `data.StructureInfo[].公民身份号码` | Object | 18 位身份证号码 |
| `[].Value` | String | 字段的具体值 |

### 字段详情

| 字段名 | 必填 | 示例值 | 说明 |
|--------|------|--------|------|
| 姓名 | 是 | 李明 | 居民身份证持有人姓名 |
| 性别 | 是 | 男 | 性别：男/女 |
| 民族 | 是 | 汉 | 民族信息，如：汉、回、维吾尔等 |
| 出生 | 是 | 1997 年 9 月 10 日 | 出生日期，格式固定为"YYYY 年 M 月 D 日" |
| 住址 | 是 | 北京西城区天赋小区 1 号 301 | 户籍所在地详细地址 |
| 公民身份号码 | 是 | 110102199709100123 | 18 位居民身份证号码 |

---

## 📝 输出逻辑

1. **成功识别**（`code: "00000"`）→ 解析 `data.StructureInfo`，按 Markdown 表格格式展示
2. **识别失败**（任何非 `00000` 状态码）→ 直接返回错误信息，不重试、不切换场景
3. **任务结束** → 不再执行任何其他 OCR 操作，等待用户新指令

### 常见错误场景

| 场景 | 表现 | 处理建议 |
|------|------|---------|
| 图片模糊 | 部分字段识别为空或错误 | 建议重新拍摄清晰图片 |
| 反光遮挡 | 关键字段（如身份证号）识别失败 | 调整光线角度后重拍 |
| 非身份证图片 | 返回空结果或错误码 | 确认图片为居民身份证 |
| 图片不完整 | 缺角、裁剪导致信息缺失 | 确保身份证四角完整 |

---

## 💡 完整示例

### 请求
```bash
python3 scripts/scan.py \
  --url "https://example.com/idcard.jpg" \
  --service-option "ocr" \
  --input-configs '{"function_option": "RecognizeIDCard"}' \
  --output-configs '{"need_return_image": "false"}' \
  --data-type "image"
```

### 响应
```json
{
  "code": "00000",
  "message": null,
  "data": {
    "StructureInfo": [{
      "姓名": {"Value": "李明"},
      "性别": {"Value": "男"},
      "民族": {"Value": "汉"},
      "出生": {"Value": "1997 年 9 月 10 日"},
      "住址": {"Value": "北京西城区天赋小区 1 号 301"},
      "公民身份号码": {"Value": "110102199709100123"}
    }]
  }
}
```

### 调用方展示
| 字段 | 值 |
|------|-----|
| 姓名 | 李明 |
| 性别 | 男 |
| 民族 | 汉 |
| 出生 | 1997 年 9 月 10 日 |
| 住址 | 北京西城区天赋小区 1 号 301 |
| 公民身份号码 | 110102199709100123 |

---

## 🔒 隐私与安全提示

> [!WARNING] **⚠️ 敏感信息处理**
> - 身份证信息属于**个人敏感信息**，请妥善保管识别结果
> - 识别完成后建议及时删除临时图片文件
> - 不要在公开场合展示完整的身份证号码
> - 本服务通过夸克官方 API 处理，不会永久保存图片数据

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [API 通用规范](../API.md)
- [夸克扫描王开放平台](https://scan-business.quark.cn)
