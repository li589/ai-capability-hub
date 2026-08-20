# MiroFish 群体智能引擎（可选模块）

本目录集成了 MiroFish OASIS 模拟引擎，用于增强对话预测功能。

## 集成状态

⚠️ **注意**：MiroFish 作为一个独立项目被引入，其核心服务依赖外部项目结构（`backend/app/models/task.py`等），目前处于 **可选模块** 状态。

核心分析功能（MBTI/大五/情感/风险检测）完全独立工作，无需此模块。

## 功能说明

- `conversation_predictor.py` 优先调用 MiroFish OASIS 模拟引擎
- 若 MiroFish 不可用或未配置，自动降级到规则预测
- 配置 LLM API Key 后可启用增强对话预测

## 安装（可选）

```bash
pip install -r scripts/mirofish/requirements.txt
```

## 依赖

- `openai>=1.12.0` - LLM 支持
- `zep-cloud>=0.14.0` - 群体记忆增强（可选）
- `PyMuPDF>=1.23.0` - PDF 解析
- `charset-normalizer>=3.3.0` - 字符编码检测

## 配置

在项目根目录 `.env` 文件中配置：

```bash
DEEPSEEK_API_KEY=your-key
ZEP_API_KEY=your-zep-key  # 可选
FLASK_DEBUG=true
```
