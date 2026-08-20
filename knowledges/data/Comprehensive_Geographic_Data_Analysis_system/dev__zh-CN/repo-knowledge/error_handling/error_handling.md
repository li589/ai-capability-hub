---
kind: "repo_knowledge"
category: "error_handling"
title: "错误处理体系：基于Python标准异常与FastAPI HTTPException的混合模式"
scopes: ["**"]
updated_at: "2026-07-29T19:23:58Z"
---

# 错误处理体系：基于Python标准异常与FastAPI HTTPException的混合模式

该仓库的错误处理采用**分散式、无统一异常框架**的模式，主要依赖Python内置异常和FastAPI的HTTPException进行错误传播，未定义专门的领域异常类型或全局错误处理器。

**系统与方法：**
- **算法层（Code/algorithms）**：广泛使用`ValueError`、`KeyError`、`TypeError`等内置异常进行参数校验和运行时错误提示，如`block_inversion.py`中大量使用`raise ValueError(...)`验证输入数组形状和数据类型
- **服务层（Code/backend/app/services）**：通过FastAPI的`HTTPException`将业务错误转换为HTTP响应码，在API路由层捕获并返回结构化错误信息
- **异步任务（Celery）**：使用`TimeoutError`等标准异常处理超时场景

**关键文件与位置：**
- `Code/algorithms/providers/Python/algorithms/block_inversion.py`：算法参数校验的核心错误抛出点
- `Code/algorithms/adapters/provider_adapter.py`：提供程序适配器的异常处理
- `Code/backend/app/api/`：FastAPI路由中的HTTPException使用
- `Code/backend/app/services/`：业务服务层的异常处理逻辑

**架构约定：**
- 无统一的异常基类或错误码枚举
- 算法层和业务层使用不同层次的异常策略（Python异常 vs HTTP异常）
- 缺乏全局异常中间件，错误处理分散在各模块内部
- 测试覆盖了大量异常场景（test_*.py文件中包含异常断言）

**开发者应遵循的规则：**
1. 算法函数使用`ValueError`进行参数验证，提供清晰的错误消息
2. API层使用`HTTPException(status_code, detail=...)`返回用户友好的错误
3. 避免使用裸`except Exception`捕获所有异常，应精确捕获特定异常类型
4. 对于可恢复的错误，考虑使用重试机制而非直接抛出异常
5. 保持异常消息的可读性和调试友好性
