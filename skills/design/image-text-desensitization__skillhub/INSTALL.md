# 一键安装指南

## 快速安装

### 方法一：直接复制（推荐）

将整个 `脱敏工具` 目录复制到龙虾的 `./工具/` 目录下：

```
./工具/脱敏工具/
├── smart_desensitize_skill.py   # 主程序（含自动初始化）
├── deep_desensitize_skill.py    # 标准版脱敏器
├── fast_deep_desensitize_skill.py # 高性能版
├── skill.json                   # Skill 配置
├── SOP.md                       # 标准操作流程
├── INSTALL.md                   # 本文件
└── README.md                    # 使用说明
```

**自动初始化**：首次导入工具时，会自动创建：
- `./基础设定/DESENSITIZE_RULES.md` — 全局脱敏配置
- 更新 `./MEMORY.md` — 添加脱敏规则

新建 agent 时，只要工具目录存在，就会自动启用脱敏！

### 方法二：从 GitHub 克隆

```bash
cd ./工具/
git clone https://github.com/{your-username}/smart-desensitize-tool.git 脱敏工具
```

## 依赖安装

### 核心功能（无需额外依赖）
- 文本脱敏
- JSON 脱敏
- 图片基础模糊

### 增强功能（可选依赖）

```bash
# 图片 OCR 文字识别
pip install easyocr

# 或使用 PaddleOCR（中文效果更好）
pip install paddleocr

# 人脸检测
pip install opencv-python-headless
```

## 配置启用

### 1. 编辑记忆文件

在 `./MEMORY.md` 中添加脱敏规则（见 SOP.md）

### 2. 测试运行

```python
from smart_desensitize_skill import SmartDesensitizer

# 测试文本脱敏
text = "我的手机号是13812345678"
result = SmartDesensitizer.desensitize_text(text)
print(result)  # 我的手机号是138****5678
```

## 验证安装

运行测试脚本：

```bash
cd ./工具/脱敏工具/
python test_full.py
```

如果看到所有测试通过，说明安装成功！
