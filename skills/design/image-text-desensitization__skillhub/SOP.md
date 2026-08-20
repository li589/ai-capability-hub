# 智能自动脱敏工具 - 标准操作流程 (SOP)

## 一、工具概述

智能自动脱敏工具用于保护用户隐私，自动识别并脱敏敏感信息。

**支持脱敏的敏感信息类型：**
- 手机号：`138****5678`
- 身份证号：`110101********1234`
- 银行卡号：`6222****1234`
- 邮箱：`te****@example.com`
- 姓名、地址、QQ、微信、车牌号等

**支持的处理对象：**
- 纯文本
- JSON 数据
- 图片（含 OCR 文字识别 + 区域模糊）

---

## 二、在龙虾系统中集成

### 2.1 自动初始化（推荐）

**工具已内置自检功能**，首次导入时会自动：
1. 检查并创建全局配置 `./基础设定/DESENSITIZE_RULES.md`
2. 检查并更新 `./MEMORY.md` 添加脱敏规则

无需手动配置！

### 2.2 配置文件说明

在 `./MEMORY.md` 中添加以下规则：

```markdown
### 自动脱敏模式
**开启时间：** {日期}

**规则：** 主人发送的所有内容（文本、JSON、图片），在处理前先进行敏感信息脱敏：
- 手机号：138****5678
- 身份证：110101********1234
- 银行卡：6222****1234
- 邮箱：te****@example.com
- 姓名、地址、QQ、微信、车牌号等

**使用工具：** `./工具/脱敏工具/smart_desensitize_skill.py`

**自动删除原图：** 脱敏处理完成后，自动删除原始图片，只保留脱敏版本

**例外：** 
- 主人明确要求不脱敏的内容
- 已知的安全/测试数据
```

### 2.2 处理流程

**文本/JSON 处理：**
```python
from smart_desensitize_skill import SmartDesensitizer

# 文本脱敏
result = SmartDesensitizer.desensitize_text(text)

# JSON 脱敏
result = SmartDesensitizer.desensitize_json(data)
```

**图片处理：**
```python
from smart_desensitize_skill import SmartDesensitizer

# 读取图片 base64
with open(image_path, 'rb') as f:
    import base64
    base64_image = base64.b64encode(f.read()).decode()

# 脱敏处理
result_base64 = SmartDesensitizer.desensitize_image(base64_image)

# 保存脱敏图片
with open(output_path, 'wb') as f:
    f.write(base64.b64decode(result_base64))

# 删除原图
import os
os.remove(original_path)
```

---

## 三、处理策略

### 3.1 图片大小自动选择

| 图片大小 | 处理模式 | 说明 |
|---------|---------|------|
| < 1MP | 标准模式 | 完整深度学习处理 |
| 1MP - 4MP | 高性能模式 | 平衡速度与质量 |
| > 4MP | 高性能模式 | 优先处理速度 |

### 3.2 敏感信息识别规则

| 类型 | 正则表达式 | 脱敏规则 |
|------|-----------|---------|
| 手机号 | `1[3-9]\d{9}` | 前3后4，中间*号 |
| 身份证 | `[1-9]\d{5}(19\|20)\d{2}...` | 前6后4，中间*号 |
| 银行卡 | `\d{16,19}` | 前4后4，中间*号 |
| 邮箱 | `[a-zA-Z0-9._%+-]+@...` | 前2字符 + *号 |

---

## 四、注意事项

1. **OCR 依赖**：图片文字识别需要安装 `easyocr` 或 `paddleocr`
2. **人脸检测**：需要安装 `opencv-python-headless`
3. **原图删除**：处理完必须删除原图，避免敏感信息残留
4. **性能考虑**：大图片会自动降级到高性能模式

---

## 五、常见问题

**Q: 为什么图片脱敏后文字还可见？**
A: 需要安装 OCR 依赖：`pip install easyocr`

**Q: 如何临时关闭脱敏？**
A: 告诉龙虾"这条消息不要脱敏"

**Q: 支持哪些图片格式？**
A: JPEG、PNG、GIF（通过 base64 编码传入）
