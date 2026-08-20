---
install_source: official
install_method: download
skill_id: official_UVMwwqD0
enabled_at: 1787231849237
version: 1.0.0
name_zh: 夸克全能OCR文字识别专家
---
---
name: yescan-ocr-universal
description: 专业的OCR文字识别路由与处理专家。支持OCR 通用文字提取 | OCR 手写文档 | 提取表格内容 | 识别身份证 | 识别社保卡 | 识别港澳通行证 | 识别学位证 | 识别增值税发票 | 识别火车票 | 识别数学公式 | 识别习题题目 | 识别驾驶证 | 识别行驶证 | 识别英文发票 | 识别医疗报告单 | 识别营业执照 | 识别商品图片 | 把这张图转成文字 | 提取图中所有文字 | 读一下这张证件
version: 1.0.0

metadata:
  openclaw:
    requires:
      env:
        - SCAN_WEBSERVICE_KEY
    primaryEnv: SCAN_WEBSERVICE_KEY
    homepage: https://scan.quark.cn/business

security:
  dataFlow:
    - description: "用户图片发送至夸克官方 OCR 引擎进行实时识别"
    - destination: "https://scan.quark.cn/business"
    - retention: "我们只会在达成实时识别所需的期限内保留您的个人信息，不会永久存储，除非法律有强制的留存要求"
  privacy:
     - "敏感证件 (身份证/医疗报告等) 图片仅实时处理，不会永久存储"

permissions:
  filesystem:
    read:
      - ./scripts/
      - ./references/
      - 任意用户提供的本地文件路径
  network:
    - `https://scan-business.quark.cn/vision`
    - `https://scan.quark.cn/business`
  commands:
    - python3
---

# 🧭 使用前必读（30 秒）

> [!WARNING] **⚠️ 隐私与数据流向重要提示**
> - **第三方服务交互**：本技能会将您提供的**图片 URL 发送至夸克官方服务器 (`scan-business.quark.cn`)** 进行识别。
> - **数据可见性**：夸克服务将获取并处理该图片内容，不会永久保存

✅ **推荐方式：环境变量（免权限、即时生效、webchat 友好）**
在终端中运行（本次会话立即可用）：
```bash
export SCAN_WEBSERVICE_KEY="your_scan_webservice_key_here"
```

```bash
# 将凭证追加写入到 ~/.openclaw/env 文件
echo 'export SCAN_WEBSERVICE_KEY="your_scan_webservice_key_here"' >> ~/.openclaw/env
```

> [!TIP] **🔧 如何获取密钥？官方入口在此**
>
> 请访问 https://scan.quark.cn/business → 开发者后台 → 登录/注册账号 → 查看API Key。
>
> ⚠️ **注意**：若你点击链接后跳转到其他域名，说明该链接已失效 —— 请直接在浏览器地址栏手动输入 `https://scan.quark.cn/business`（这是当前唯一有效的官方入口）。

✅ **环境依赖**
```bash
pip3 install requests
```

## 强制执行规则

> [!IMPORTANT] **⚠️ 绝对执行原则（强制生效）**
> - **所有意图的调用命令必须且只能取自其对应 `references/scenarios/XX-xxx.md` 文件中的命令。**
> - `SKILL.md` 中的意图描述仅为语义说明，不参与参数匹配，不可用于构造调用命令。
> - **禁止伪造响应**：每个场景文件已添加「执行前必做」警告，不得使用示例 JSON 作为真实响应。
> - 违反此规则将导致 API 调用失败（如 `A0210` 未开通权限）。
> - **❗ 每次请求独立识别意图**：必须从用户本次指令中提取关键词进行意图匹配，**禁止惯性沿用上一次的场景**。

>
> 💡 **Agent 必读**：每个场景文件开头都有「执行前必做」检查清单，执行前请逐项确认。

---

## 🚀 通用调用规范

> 所有场景均遵循以下规范。

### 脚本位置

```
scripts/scan.py
```

### 输入方式（三选一）

| 方式 | 参数 | 适用场景 |
|------|------|---------|
| URL | `--url "https://..."` | 图片已在网上 |
| 本地文件 | `--path "/Users/..."` | 图片在本地（自动转 BASE64） |
| BASE64 | `--base64 "..."` | 图片已在内存/数据库 |

### 通用参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--service-option` | 是 | 服务类型（structure/scan/ocr 等） |
| `--input-configs` | 是 | JSON 字符串（外层需引号包裹） |
| `--output-configs` | 是 | JSON 字符串（外层需引号包裹） |
| `--data-type` | 是 | 数据类型（image/pdf） |

### 返回格式（所有场景统一）

```json
{
  "code": "String",      // 状态码，"00000" 表示成功
  "message": "String",  // 错误描述或成功提示
  "data": "Object"      // API 原始返回数据，结构随场景变化
}
```

### 错误码说明

| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| `00000` | 成功 | 解析 `data` 字段 |
| `A0211` | 配额/余额不足 | **直接输出纯文本**：`请前往 https://scan.quark.cn/business，登录开发者后台，选择需要的套餐进行充值（请注意购买 Skill 专用套餐）` ⚠️ **不要包装成 JSON，不要总结** |
| `HTTP_ERROR` | HTTP 请求失败 | 检查网络/API 可用性 |
| `CONFIG_ERROR` | 配置错误（如缺少 API Key） | 检查环境变量 |
| `TIMEOUT` | 请求超时 | 重试或检查网络 |
| `NETWORK_ERROR` | 网络错误 | 检查网络连接 |
| `JSON_PARSE_ERROR` | 响应解析失败 | 联系技术支持 |
| `URL_VALIDATION_ERROR` | URL 格式验证失败 | 检查 URL 是否正确（需以 http:// 或 https:// 开头） |
| `BASE64_DECODE_ERROR` | BASE64 解码失败 | 检查 BASE64 字符串是否完整、合法 |
| `BASE64_FORMAT_ERROR` | BASE64 格式错误 | 检查 Data URL 格式是否正确 |
| `FILE_ERROR` | 本地文件验证失败 | 检查文件是否存在、格式是否支持、大小是否超限 |
| `FILE_READ_ERROR` | 文件读取失败 | 检查文件权限或磁盘空间 |
| `INVALID_INPUT` | 输入参数错误 | 确保只提供了一个输入参数（URL/路径/BASE64 三选一） |
| `INVALID_JSON` | JSON 配置格式错误 | 检查 `--input-configs` 或 `--output-configs` 是否为合法 JSON 字符串 |
---

## 🎯 意图路由（when to use）

> [!IMPORTANT] **⚠️ 全局流程控制**
> - **单一意图原则**：每次请求只执行一个意图类型，命中即执行
> - **接口返回即结束**：无论接口返回成功还是失败，都直接展示给用户
> - **不继续判断**：执行完一个意图后，**不再尝试其他意图**，不重试、不切换
> - **等待新指令**：任务完成后等待用户发起新的请求

> **AGENT 执行流程**：根据用户指令关键词匹配意图类型 → 点击链接获取完整执行策略（调用命令 + 返回结构 + 示例）→ 执行后直接返回结果

---

### 📋 意图类型与 API 场景映射

> 💡 **编号说明**：意图编号 (1-17) 为内部逻辑序号，场景编号 (1-17) 对应夸克 API 场景 ID，保持独立便于未来扩展。

| 意图编号 | 意图类型 | 映射 API 场景 | 场景文件                                                                                  |
|---------|---------|-------------|---------------------------------------------------------------------------------------|
| 0 | **环境变量检查** | 场景 0 | [00-auth-check.md](references/scenarios/00-auth-check.md)                             |
| 1 | **手写文档识别** | 场景 2 | [02-handwritten-ocr.md](references/scenarios/02-handwritten-ocr.md)                   |
| 2 | **表格识别** | 场景 3 | [03-table-ocr.md](references/scenarios/03-table-ocr.md)                               |
| 3 | **身份证识别** | 场景 4 | [04-idcard-ocr.md](references/scenarios/04-idcard-ocr.md)                             |
| 4 | **社保卡识别** | 场景 5 | [05-social-security-card-ocr.md](references/scenarios/05-social-security-card-ocr.md) |
| 5 | **港澳通行证识别** | 场景 6 | [06-travel-permit-ocr.md](references/scenarios/06-travel-permit-ocr.md)               |
| 6 | **学位证识别** | 场景 7 | [07-degree-certificate-ocr.md](references/scenarios/07-degree-certificate-ocr.md)     |
| 7 | **增值税发票识别** | 场景 8 | [08-vat-invoice-ocr.md](references/scenarios/08-vat-invoice-ocr.md)                   |
| 8 | **火车票识别** | 场景 9 | [09-train-ticket-ocr.md](references/scenarios/09-train-ticket-ocr.md)                 |
| 9 | **公式识别** | 场景 10 | [10-formula-ocr.md](references/scenarios/10-formula-ocr.md)                           |
| 10 | **题目识别** | 场景 11 | [11-question-ocr.md](references/scenarios/11-question-ocr.md)                         |
| 11 | **驾驶证识别** | 场景 12 | [12-driver-license-ocr.md](references/scenarios/12-driver-license-ocr.md)             |
| 12 | **行驶证识别** | 场景 13 | [13-vehicle-license-ocr.md](references/scenarios/13-vehicle-license-ocr.md)           |
| 13 | **英文发票识别** | 场景 14 | [14-commercial-invoice-ocr.md](references/scenarios/14-commercial-invoice-ocr.md)     |
| 14 | **医疗报告单识别** | 场景 15 | [15-medical-report-ocr.md](references/scenarios/15-medical-report-ocr.md)             |
| 15 | **营业执照识别** | 场景 16 | [16-business-license-ocr.md](references/scenarios/16-business-license-ocr.md)         |
| 16 | **商品图片识别** | 场景 17 | [17-product-image-ocr.md](references/scenarios/17-product-image-ocr.md)               |
| 17 | **通用文字提取** | 场景 1 | [01-general-ocr.md](references/scenarios/01-general-ocr.md)                           |

---

### 🔍 意图匹配规则

**⚠️ 前置检查：环境变量**（自动执行，非意图）
- 在调用任何场景前，**自动检查** `SCAN_WEBSERVICE_KEY` 是否已配置
- 若未配置，直接提示用户获取密钥，**不执行任何 API 调用**
- 检查逻辑参考：[00-auth-check.md](references/scenarios/00-auth-check.md)

**意图 1 - 手写文档识别** （API 场景 2）
- 当用户存在识别各类中英文手写内容（如学生作答、作文、会议记录、手写账单等）、将潦草或非标准手写图片转化为高精度可编辑文本，或突破传统 OCR 限制处理复杂手写场景的意图
- [⚠️ 获取执行策略](references/scenarios/02-handwritten-ocr.md)

**意图 2 - 表格识别** （API 场景 3）
- 当用户存在识别图片中的各类表格（如 Excel/Word 表格、票据单据、手写表格、检查报告单等）、高精度提取文字内容并精准还原原始表格格式与结构的意图
- [⚠️ 获取执行策略](references/scenarios/03-table-ocr.md)

**意图 3 - 身份证识别** （API 场景 4）
- 当用户存在识别身份证图片、提取证件关键信息（包括但不限于姓名、身份证号、地址等字段）、将证件影像转化为结构化数据，或应用于身份核验、实名认证及信息准确性校验等场景的意图
- [⚠️ 获取执行策略](references/scenarios/04-idcard-ocr.md)

**意图 4 - 社保卡识别**（API 场景 5）
- 当用户存在识别社保卡图片、提取证件关键信息（包括但不限于姓名、社会保障号码、卡号、银联号码、性别、民族、发卡日期及有效期限等字段）、将证件影像转化为结构化数据，或应用于社保业务办理、身份核验及政务服务自动化等场景的意图
- [⚠️ 获取执行策略](references/scenarios/05-social-security-card-ocr.md)

**意图 5 - 港澳通行证识别** （API 场景 6）
- 当用户存在识别港澳通行证（或港澳台通行证）图片、提取证件关键信息（包括但不限于姓名、证件号码、签发机关、有效期限等 11 个字段）、将证件影像转化为结构化数据，或应用于身份核验、出入境管理及政务服务自动化等场景的意图
- [⚠️ 获取执行策略](references/scenarios/06-travel-permit-ocr.md)

**意图 6 - 学位证识别** （API 场景 7）
- 当用户存在识别学位证书图片、提取证书关键信息（包括但不限于证书名称、学校、姓名、性别、出生日期、学习日期、学制、学历、学位、专业、证书编号及发证日期等 12 个字段）、将证书影像转化为结构化数据，或应用于企业人才信息录入和学历核验等场景的意图
- [⚠️ 获取执行策略](references/scenarios/07-degree-certificate-ocr.md)

**意图 7 - 增值税发票识别** （API 场景 8）
- 当用户存在识别增值税发票图片、提取单据关键信息（包括但不限于销售方、购买方、货物详情、金额等 30 多个字段）、将发票影像转化为结构化数据，或应用于财务报销自动化、税务管理及企业风控等场景的意图
- [⚠️ 获取执行策略](references/scenarios/08-vat-invoice-ocr.md)

**意图 8 - 火车票识别** （API 场景 9）
- 当用户存在识别火车票图片、提取票号/出发站/到达站/车次/开车时间/票价/座位号/座位类型/旅客身份号码/旅客姓名等 10 个关键字段信息、将车票照片转化为结构化文本数据，或应用于企业出行报销场景的意图
- [⚠️ 获取执行策略](references/scenarios/09-train-ticket-ocr.md)

**意图 9 - 公式识别** （API 场景 10）
- 当用户存在识别数学/化学公式图片、高精度解析分数、矩阵、分段函数及化学方程式等复杂结构、将图像公式转化为可编辑的 LaTeX 代码或结构化数据，或应用于智能试卷自动批改、学术论文数字化归档、在线教育题目解析及科研文献深度分析等场景的意图
- [⚠️ 获取执行策略](references/scenarios/10-formula-ocr.md)

**意图 10 - 题目识别** （API 场景 11）
- 当用户存在精准提取题目关键词、利用智能算法锁定内容核心、优化信息检索路径，或应用于自动化内容创作、智能问答系统构建、教育题库索引优化及垂直领域知识图谱搭建等场景的意图
- [⚠️ 获取执行策略](references/scenarios/11-question-ocr.md)

**意图 11 - 驾驶证识别** （API 场景 12）
- 当用户存在识别驾驶证图片、提取证件关键信息（如证号、姓名、住址、有效期等）、将非结构化图像转化为结构化数据，或应用于身份核验、交通管理等场景的意图
- [⚠️ 获取执行策略](references/scenarios/12-driver-license-ocr.md)

**意图 12 - 行驶证识别** （API 场景 13）
- 当用户存在识别行驶证图片、提取证件关键信息（包括但不限于证号、姓名、住址、有效期、准驾车型等）、将行驶证影像转化为结构化数据，或应用于身份核验、交通管理及汽车租赁等场景的意图
- [⚠️ 获取执行策略](references/scenarios/13-vehicle-license-ocr.md)

**意图 13 - 英文发票识别** （API 场景 14）
- 当用户存在识别英文商业发票图片、提取单据关键信息（包括但不限于发票号、日期、买卖双方信息、商品明细、金额及税额等）、将非结构化英文单据转化为结构化数据，或应用于跨境贸易单证处理、海外费用报销及国际化财务自动化审核等场景的意图
- [⚠️ 获取执行策略](references/scenarios/14-commercial-invoice-ocr.md)

**意图 14 - 医疗报告单识别**（API 场景 15）
- 当用户存在识别医疗报告单图片、提取报告关键信息（包括但不限于检验项目、结果、参考值等）、将医疗报告影像转化为结构化数据，或应用于电子病历归档、健康数据分析及远程医疗辅助诊断等场景的意图
- [⚠️ 获取执行策略](references/scenarios/15-medical-report-ocr.md)

**意图 15 - 营业执照识别**（API 场景 16）
- 当用户存在识别营业执照图片、提取证件关键信息（包括但不限于统一社会信用代码、名称、类型、法定代表人、经营范围等）、将执照影像转化为结构化数据，或应用于企业身份核验、工商注册自动化、供应链准入审核及金融风控等场景的意图
- [⚠️ 获取执行策略](references/scenarios/16-business-license-ocr.md)

**意图 16 - 商品图片识别**（API 场景 17）
- 用户需要识别图片中的具体商品对象，包括商品名称、品牌、品类等信息，用于商品检索或分类
- [⚠️ 获取执行策略](references/scenarios/17-product-image-ocr.md)

**意图 17 - 通用文字提取**（兜底意图）（API 场景 1）
- 当用户指令中不包含上述任何具体场景，仅表达提取纯文字意图时
- [⚠️ 获取执行策略](references/scenarios/01-general-ocr.md)

---

### ⚠️ 匹配顺序说明

1. **前置检查**：调用任何场景前，自动检查 `SCAN_WEBSERVICE_KEY` 环境变量
2. **顺序匹配**：按逻辑序号升序匹配（1 → 2 → ... → 17），命中即止
3. **兜底机制**：逻辑序号 17（通用文字提取）为最后兜底，仅当上述具体意图均未命中时使用

---


## ⛔ 不适用场景（When Not to Use）

> 本技能**不支持**以下场景，请勿尝试：

| 不支持的场景 | 原因 | 建议替代方案 |
|------------|------|------------|
| **视频处理** | 仅支持单张静态图片 | 先提取视频帧，再逐帧处理 |
| **批量处理** | 每次调用仅限单张图片 | 如需批量，请循环调用或联系管理员 |
| **实时摄像头流** | 非实时流处理架构 | 使用专用视频处理服务 |
| **超大图片（>5MB）** | API 限制 | 先压缩或裁剪后再处理 |
| **非图片格式** | 仅支持 jpg/jpeg/png/gif/bmp/webp/tiff/wbmp | 先转换为支持的图片格式 |

---

## 💡 示例参考

> 每个意图场景的完整调用示例已在对应场景文件中提供，请直接查阅：
> - 各场景调用命令 + 响应结构 + 完整示例：`references/scenarios/XX-xxx.md`
> - 通用参数规范：见上文「🚀 通用调用规范」章节

---

## ⚠️ 重要注意事项

1. **JSON 格式**: `--input-configs` 和 `--output-configs` 必须是 **JSON 字符串**
   - ✅ 正确：`--input-configs '{"function_option": "..."}'`
   - ❌ 错误：`--input-configs {"function_option": "..."}`

2. **安全与配额**: 严禁泄露 API Key，注意 `A0211` 配额限制

3. **图片大小**: 本地文件最大 5MB，支持 jpg/jpeg/png/gif/bmp/webp/tiff/wbmp/webp 格式

---

## 🔗 相关资源

- [夸克扫描王开放平台](https://scan.quark.cn/business)
- [API 通用规范](references/API.md)（可选参考）
- [场景文件目录](references/scenarios/)

---

## 📁 文件结构
- `SKILL.md` —  本文档（意图分析 + 通用规范）
- `scripts/scan.py` —  主执行脚本 (Python 3.9+)
- `references/scenarios/00-auth-check.md` - 场景零 [环境变量检查]
- `references/scenarios/01-general-ocr.md` - 场景1 [通用图片 OCR]
- `references/scenarios/02-handwritten-ocr.md` - 场景2 [手写文档识别]
- `references/scenarios/03-table-ocr.md` - 场景3 [表格识别]
- `references/scenarios/04-idcard-ocr.md` - 场景4 [身份证识别]
- `references/scenarios/05-social-security-card-ocr.md` - 场景5 [社保卡识别]
- `references/scenarios/06-travel-permit-ocr.md` - 场景6 [港澳通行证识别]
- `references/scenarios/07-degree-certificate-ocr.md` - 场景7 [学位证识别]
- `references/scenarios/08-vat-invoice-ocr.md` - 场景8 [增值税发票识别]
- `references/scenarios/09-train-ticket-ocr.md` - 场景9 [火车票识别]
- `references/scenarios/10-formula-ocr.md` - 场景10 [公式识别]
- `references/scenarios/11-question-ocr.md` - 场景11 [题目识别]
- `references/scenarios/12-driver-license-ocr.md` - 场景12 [驾驶证识别]
- `references/scenarios/13-vehicle-license-ocr.md` - 场景13 [行驶证识别]
- `references/scenarios/14-commercial-invoice-ocr.md` - 场景14 [英文发票识别]
- `references/scenarios/15-medical-report-ocr.md` - 场景15 [医疗报告单识别]
- `references/scenarios/16-business-license-ocr.md` - 场景16 [营业执照识别]
- `references/scenarios/17-product-image-ocr.md` - 场景17 [商品图片识别]