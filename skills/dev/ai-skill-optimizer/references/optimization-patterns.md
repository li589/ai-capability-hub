# AI Skill 优化代码模式参考（Optimization Patterns Reference）

> **版本**：v1.1.0
> **用途**：提供优化前后代码对比示例，帮助理解 Token 优化 / 性能优化 / 安全加固的具体实施方式
> **关联**：[SKILL.md - Step 3 优化实施](../SKILL.md#step-3--优化实施implementation)

---

## 1. Token 优化模式（Before/After 对比）

### 模式 A：渐进式披露重构

**Before（冗长）**：
```markdown
## 功能详解

### 模块 A

这里详细描述模块 A 的功能，包括：
1. 输入参数
2. 输出结果
3. 错误处理
4. 示例代码
5. 注意事项
...（500行详细内容）
```

**After（精简）**：
```markdown
## 功能模块

### 模块 A
[核心功能，5-10行]

详细文档：见 [references/module-a.md](references/module-a.md)
```

---

### 模式 B：代码外置

**Before（SKILL.md 中 50 行代码）**：
```markdown
```python
# 复杂的数据处理代码（50行）
def process_data(items):
    results = []
    for item in items:
        result = transform(item)
        results.append(result)
    return results
```
```

**After（外置到 scripts/）**：
```markdown
使用 `scripts/process_data.py` 处理数据：

```bash
python scripts/process_data.py --input <file> --output <output>
```

详细说明：见 [references/process-data.md](references/process-data.md)
```

---

## 2. 性能优化模式（Before/After 对比）

### 模式 A：懒加载

**Before（启动时加载全部）**：
```python
import heavy_module
import another_heavy
import yet_another

def simple_task():
    print("hello")
```

**After（按需加载）**：
```python
def simple_task():
    import heavy_module  # 仅在使用时加载
    heavy_module.do_something()
```

---

### 模式 B：缓存结果

**Before（每次调用重新计算）**：
```python
def get_data():
    return fetch_from_api()  # 每次都请求
```

**After（带缓存）**：
```python
_cache = {}
def get_data():
    if 'data' not in _cache:
        _cache['data'] = fetch_from_api()
    return _cache['data']
```

---

### 模式 C：批量操作

**Before（逐个处理）**：
```python
for item in items:
    write_file(item)
```

**After（批量处理）**：
```python
batch_write(items)  # 一次写入
```

---

## 3. 安全加固模式（Before/After 对比）

### 模式 A：移除硬编码密钥

**Before（危险）**：
```python
API_KEY = "sk-1234567890abcdef"
SECRET = "my-secret-token"
```

**After（安全）**：
```python
import os
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")
```

---

### 模式 B：输入验证强化

**Before（未验证）**：
```python
def read_file(path):
    return open(path).read()
```

**After（安全验证）**：
```python
import re
from pathlib import Path

def safe_path(user_input):
    """验证路径安全，防止路径遍历"""
    base = Path("workspace")
    requested = (base / user_input).resolve()
    if not str(requested).startswith(str(base)):
        raise ValueError("Path traversal detected")
    return requested

def safe_skill_name(name: str) -> str:
    """验证 Skill 名称格式，防止注入"""
    if not re.match(r"^[a-z][a-z0-9-]{2,64}$", name):
        raise ValueError(f"Invalid skill name: {name}")
    if ".." in name or "/" in name:
        raise ValueError("Path traversal detected in skill name")
    return name
```

---

### 模式 C：API 错误处理泛化

**Before（信息泄露）**：
```python
raise ValueError(f"Database connection failed: {db_host}:{db_port}")
```

**After（泛化安全）**：
```python
import logging
logger = logging.getLogger(__name__)

def handle_error(e: Exception, context: str):
    """泛化错误信息，防止内部路径泄露"""
    logger.error(f"{context} failed: {type(e).__name__}")
    raise RuntimeError(f"{context} failed. Contact administrator.")
```

---

## 4. 使用方式

优化时，将当前 SKILL.md 中的内容与上述模式对照：
- **Token 超限** → 使用模式 A（渐进式披露）或模式 B（代码外置）
- **P95 延迟超标** → 使用模式 C（懒加载/缓存/批量）
- **安全加固** → 使用模式 D（移除硬编码/输入验证/错误泛化）

将外置后的代码块替换为：
```markdown
[详见 references/optimization-patterns.md]
```
