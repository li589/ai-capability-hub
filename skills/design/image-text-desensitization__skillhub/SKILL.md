# SKILL.md - 智能自动脱敏工具

## 技能名称
智能自动脱敏工具 (Smart Desensitize Tool)

## 版本
3.0.0

## 描述
保护用户隐私的智能脱敏工具，支持文本、JSON、图片的自动敏感信息识别与脱敏。内置自检初始化功能，新建 agent 时自动启用脱敏规则。

## 功能列表

| 功能 | 说明 |
|------|------|
| 文本脱敏 | 手机号、身份证、银行卡、邮箱等 9 种类型 |
| JSON 脱敏 | 自动识别敏感字段并处理 |
| 图片脱敏 | OCR 识别敏感文字 + 区域模糊 |
| 智能策略 | 根据图片大小自动选择处理模式 |
| 自动初始化 | 新建 agent 时自动启用脱敏规则 |
| 自动清理 | 脱敏后自动删除原图 |

## 入口点

```python
from smart_desensitize_skill import SmartDesensitizer

# 创建脱敏器实例
desensitizer = SmartDesensitizer()

# 文本脱敏
result = desensitizer.desensitize_text(text)

# JSON 脱敏
result = desensitizer.desensitize_json(data)

# 图片脱敏（base64）
result = desensitizer.desensitize_image_base64(image_base64)
```

## 使用场景

1. **隐私保护**：用户发送包含敏感信息的文本/图片时自动脱敏
2. **数据清洗**：处理包含敏感信息的数据集
3. **日志脱敏**：对日志中的敏感信息进行脱敏存储
4. **截图处理**：对包含敏感信息的截图进行模糊处理

## 配置

工具首次导入时会自动创建配置：

- `./基础设定/DESENSITIZE_RULES.md` — 全局脱敏配置
- 更新 `./MEMORY.md` — 添加脱敏规则

## 依赖

### 核心功能（无需额外依赖）
- Python 3.6+
- re, json, base64, os（标准库）

### 增强功能（可选）
- easyocr — OCR 文字识别
- opencv-python-headless — 人脸检测

## 文件结构

```
脱敏工具/
├── SKILL.md                     # 本文件
├── smart_desensitize_skill.py   # 主程序
├── deep_desensitize_skill.py    # 标准版脱敏器
├── fast_deep_desensitize_skill.py # 高性能版
├── skill.json                   # 配置文件
├── SOP.md                       # 标准操作流程
├── INSTALL.md                   # 安装指南
└── README.md                    # 项目说明
```

## 快速开始

### 安装
将本目录复制到 `./工具/脱敏工具/`

### 初始化
```python
from smart_desensitize_skill import SmartDesensitizer
# 自动完成配置初始化
```

### 测试
```python
desensitizer = SmartDesensitizer()
print(desensitizer.desensitize_text("手机号：13812345678"))
# 输出: 手机号：138****5678
```

## 注意事项

1. 图片 OCR 脱敏需要安装 `easyocr`
2. 脱敏后的图片会自动删除原图
3. 用户明确要求不脱敏时会跳过处理
