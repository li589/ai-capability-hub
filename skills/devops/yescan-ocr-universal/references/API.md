# API 通用规范 - 夸克扫描王综合服务

> 📖 **主文档**: [返回 SKILL.md](../SKILL.md)
> 
> 📁 **场景详情**: 每个场景的完整调用命令、返回结构、示例请查看 [scenarios/](scenarios/) 目录中的独立文件。

---

## 📋 调用规范

### 前置条件

```bash
# 1. 设置环境变量
export SCAN_WEBSERVICE_KEY="your_api_key_here"

# 2. 安装依赖
pip3 install requests
```

### 脚本位置

```
scripts/scan.py
```

### 通用参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--url` | 三选一 | 图片 URL（http/https） |
| `--path` | 三选一 | 本地文件路径（自动转 BASE64） |
| `--base64` | 三选一 | BASE64 字符串（支持 Data URL 格式） |
| `--service-option` | 必需 | 服务类型（structure/scan/ocr 等） |
| `--input-configs` | 必需 | JSON 字符串（外层需引号包裹） |
| `--output-configs` | 必需 | JSON 字符串（外层需引号包裹） |
| `--data-type` | 必需 | 数据类型（image/pdf） |

### 返回格式（所有场景统一）

```json
{
  "code": "String",      // 状态码，"00000" 表示成功
  "message": "String",  // 错误描述或成功提示（可能为 null）
  "data": "Object"      // API 原始返回数据，结构随场景变化
}
```

### 错误码说明

| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| `00000` | 成功 | 解析 `data` 字段 |
| `A0210` | 未开通此 API 权限 | 登录夸克控制台 → 进入应用 → 开通对应场景的 API 服务 |
| `A0211` | 配额/余额不足 | 请前往 [夸克扫描王开放平台](https://scan-business.quark.cn) 充值或升级套餐 |
| `A0300` | QPS 超限（请求过于频繁） | 等待 2-3 秒后重试，如频繁出现请升级套餐提升 QPS 限额 |
| `HTTP_ERROR` | HTTP 请求失败 | 检查网络/API 可用性 |
| `CONFIG_ERROR` | 配置错误（如缺少 API Key） | 检查环境变量 |
| `TIMEOUT` | 请求超时 | 重试或检查网络 |
| `NETWORK_ERROR` | 网络错误 | 检查网络连接 |
| `JSON_PARSE_ERROR` | 响应解析失败 | 联系技术支持 |

---

## 🎯 场景索引

| 编号 | 场景名称 | 适用场景 | 详情 |
|------|---------|---------|------|
| 01 | 通用图片 OCR | 文档、书籍、笔记、截图等通用文本提取 | [查看详情](scenarios/01-general-ocr.md) |
| 02 | 手写文档识别 | 学生作答、作文、会议记录、手写账单等中英文手写内容 | [查看详情](scenarios/02-handwritten-ocr.md) |
| 03 | 表格识别 | Excel/Word 表格、票据单据、手写表格、检查报告单 | [查看详情](scenarios/03-table-ocr.md) |
| 04 | 身份证识别 | 中华人民共和国居民身份证正反面 | [查看详情](scenarios/04-idcard-ocr.md) |
| 05 | 社保卡识别 | 中华人民共和国社保卡 | [查看详情](scenarios/05-social-security-card-ocr.md) |
| 06 | 港澳通行证识别 | 港澳通行证/港澳台通行证 | [查看详情](scenarios/06-travel-permit-ocr.md) |
| 07 | 学位证识别 | 学位证书（12 个字段提取） | [查看详情](scenarios/07-degree-certificate-ocr.md) |
| 08 | 增值税发票识别 | 增值税发票（30+ 字段提取） | [查看详情](scenarios/08-vat-invoice-ocr.md) |
| 09 | 火车票识别 | 火车票（10 个关键字段） | [查看详情](scenarios/09-train-ticket-ocr.md) |
| 10 | 公式识别 | 数学/化学公式转 LaTeX | [查看详情](scenarios/10-formula-ocr.md) |
| 11 | 题目识别 | 题目关键词提取 | [查看详情](scenarios/11-question-ocr.md) |
| 12 | 驾驶证识别 | 中华人民共和国驾驶证 | [查看详情](scenarios/12-driver-license-ocr.md) |
| 13 | 行驶证识别 | 中华人民共和国行驶证 | [查看详情](scenarios/13-vehicle-license-ocr.md) |
| 14 | 英文发票识别 | 英文商业发票 | [查看详情](scenarios/14-commercial-invoice-ocr.md) |
| 15 | 医疗报告单识别 | 医疗检验报告单 | [查看详情](scenarios/15-medical-report-ocr.md) |
| 16 | 营业执照识别 | 企业营业执照 | [查看详情](scenarios/16-business-license-ocr.md) |
| 17 | 商品图片识别 | 商品包装图片（支持条码提取） | [查看详情](scenarios/17-product-image-ocr.md) |
---
