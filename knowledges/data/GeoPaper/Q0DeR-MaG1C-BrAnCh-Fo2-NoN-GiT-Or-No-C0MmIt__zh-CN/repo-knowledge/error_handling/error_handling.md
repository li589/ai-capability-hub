---
kind: "repo_knowledge"
category: "error_handling"
title: "Python 脚本的错误处理实践：异常抛出、日志记录与容错策略"
scopes: ["**"]
updated_at: "2026-07-30T06:35:12Z"
---

# Python 脚本的错误处理实践：异常抛出、日志记录与容错策略

该仓库是一个基于 Python 的科研数据分析项目（Hyper-TCDF 滑坡预测模型），错误处理呈现以下特点：

**1. 异常类型使用**
- 主要使用 Python 内置异常：`ValueError`、`FileNotFoundError`、`NotADirectoryError`、`IndexError`、`RuntimeError`、`TimeoutException`（自定义）
- 参数验证通过 `argparse.ArgumentTypeError` 进行命令行参数校验
- 未定义统一的自定义错误类或错误码体系

**2. 异常抛出模式**
- **配置验证**：在 `config.py` 中使用 `_env_flag`、`_env_int` 等函数安全解析环境变量，失败时返回默认值而非抛出异常
- **数据完整性检查**：在数据加载和预处理阶段抛出明确的 `ValueError` 和 `FileNotFoundError`，如 "缺少必要配置参数"、"输入目录不存在"、"未找到有效文件"
- **边界条件处理**：在批量处理中抛出 `IndexError` 表示索引越界，如 "No events found for batch index"
- **运行时错误**：关键路径失败时使用 `RuntimeError`，如 "DEM export failed"、"No valid samples remain after skipping failed CSV files"

**3. 异常捕获与容错**
- **try-except 模式**：早期版本（V1.0-V3.0）广泛使用裸 `except:` 捕获所有异常并打印简单消息
- **渐进式改进**：新版本采用更具体的异常捕获，记录详细的错误信息到日志文件
- **失败隔离**：单个文件处理失败不影响整体流程，失败的样本被跳过并记录到专门的失败日志
- **降级策略**：当文件张量缓存不可用时自动回退到传统预加载模式

**4. 日志记录策略**
- **结构化失败日志**：将错误信息写入专门的 CSV/JSON 文件，包含错误类型、消息、影响范围等元数据
- **控制台输出**：使用带前缀的格式化消息，如 `[TCDF V8.0][Loader][Error]`、`[TCDF V8.0][Loader][Warning]`
- **进度跟踪**：使用 tqdm 显示处理进度，便于监控长时间运行的任务

**5. 关键文件中的错误处理**
- `data_loader.py`：实现健壮的数据加载，包含缓存失效处理和失败样本隔离
- `auto_run_tcdf_2000plus_pipeline.py`：批处理管道中的重试机制、网络探测、内存限制处理
- `config.py`：环境变量解析的安全封装，避免配置错误导致程序崩溃

**6. 开发规范建议**
- 避免使用裸 `except:`，应明确捕获具体异常类型
- 为关键操作添加适当的异常处理和日志记录
- 使用有意义的异常消息，包含上下文信息
- 对于可恢复的错误，实现降级或重试机制
- 保持错误信息的结构化，便于后续分析和调试
