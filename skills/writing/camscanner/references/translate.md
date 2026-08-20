# 多语言翻译工作流

> **前置阅读**：`references/image-processing.md`（translate 参数和语言代码）

## 场景

用户有包含文字的图片（如菜单、路标、文档截图），需要翻译为目标语言并保持原始排版。

## 决策流程

### 1. 确认目标语言

从用户需求推断 `--lang` 参数值。语言代码见 `references/image-processing.md`。

### 2. 单语言 vs 多语言

- **单语言**：一次 `image translate --lang xx -s` 即可
- **多语言版本**：对同一图片依次执行不同 `--lang`，配合 `--save-title` 区分

### 3. 多语言衔接逻辑

```
同一输入文件 → 分别执行 N 次 translate（每次不同 --lang + --save-title）
```

## 注意事项

- 处理时间较长（10-60 秒），超时按重试策略处理
- 图片中的文字需足够清晰才能准确识别和翻译
