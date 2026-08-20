# 场景零 [环境变量检查]

**适用场景**: 使用任何夸克扫描王 OCR 功能前的前置检查

---

## 🔍 检查步骤

### 1. 检查环境变量是否已设置

```bash
echo $SCAN_WEBSERVICE_KEY
```

### 2. 判断结果

| 结果 | 处理方式 |
|------|---------|
| 输出非空字符串 | ✅ 已配置，继续执行 任务 |
| 输出为空 | ❌ 未配置，提示用户获取密钥 |

---

## ❌ 未配置时的提示模板

当 `SCAN_WEBSERVICE_KEY` 未设置时，**不要执行任何 OCR 调用**，直接返回以下提示：

```markdown
⚠️ **环境变量 `SCAN_WEBSERVICE_KEY` 未配置**

夸克扫描王 OCR 服务需要 API Key 才能使用。

> [!TIP] **🔧 如何获取密钥？官方入口在此**
> 请访问 **[夸克扫描王开放平台](https://scan-business.quark.cn)** → 登录/注册账号 → 进入「控制台」→ 「创建新应用」→ 填写基本信息（应用名称建议填 `openclaw-ocr`）→ 提交后即可看到 `SCAN_WEBSERVICE_KEY`。
> 
> ⚠️ **注意**：若你点击链接后跳转到其他域名（如 `quark.feishu.cn` 或 `open.quark.com`），说明该链接已失效 —— 请直接在浏览器地址栏手动输入 `https://scan-business.quark.cn`（这是当前唯一有效的官方入口）。

获取密钥后，在终端执行：
```bash
export SCAN_WEBSERVICE_KEY="your_key_here"
```

然后重新运行 OCR 命令即可。
```

---

## ✅ 配置成功后的处理

环境变量已设置时，直接继续执行对应的 OCR 场景：

- 通用 OCR → [01-general-ocr.md](01-general-ocr.md)
- 身份证识别 → [02-idcard-ocr.md](02-idcard-ocr.md)
- 合同扫描 → [03-contract-scan.md](03-contract-scan.md)
...
---

## 💡 示例流程

### 用户请求
> 帮我提取这张图片的文字：https://example.com/doc.jpg

### Agent 执行流程

1. **先检查环境变量**
   ```bash
   echo $SCAN_WEBSERVICE_KEY
   ```

2. **如果为空** → 返回上述提示模板，**不执行后续步骤**

3. **如果已设置** → 继续调用通用 OCR：
   ```bash
   python3 scripts/scan.py \
     --url "https://example.com/doc.jpg" \
     --service-option "structure" \
     --input-configs '{"function_option": "RecognizeGeneralDocument"}' \
     --output-configs '{"need_return_image": "False"}' \
     --data-type "image"
   ```

---

## 🔗 相关资源

- [返回主文档](../../SKILL.md)
- [夸克扫描王开放平台](https://scan-business.quark.cn)
