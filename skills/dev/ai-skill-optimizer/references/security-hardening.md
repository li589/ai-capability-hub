# Skill 安全加固检查清单

> **版本**：v1.0.0
> **依据**：CISO-001 安全标准 + OWASP Top 10

---

## 目录

1. [加固优先级矩阵](#1-加固优先级矩阵)
2. [逐项加固指南](#2-逐项加固指南)
3. [加固验证清单](#3-加固验证清单)

---

## 1. 加固优先级矩阵

| 优先级 | 加固类别 | 威胁类型 | 影响 | CVSS 改善 |
|--------|---------|---------|------|-----------|
| **P0** | 移除硬编码密钥 | I（信息泄露）| 高 | 7.5→0 |
| **P0** | 收紧文件权限 | E（权限提升）| 高 | 7.5→0 |
| **P0** | 减少依赖 | T（供应链攻击）| 高 | 7.5→5.0 |
| **P1** | 强化输入验证 | T/I（注入）| 高 | 6.5→3.5 |
| **P1** | 泛化错误信息 | I（信息泄露）| 中 | 5.0→2.5 |
| **P2** | 添加超时保护 | D（DoS）| 中 | 5.0→2.5 |
| **P2** | 日志脱敏 | I（信息泄露）| 中 | 5.0→2.5 |
| **P3** | 安全头注释 | I（信息泄露）| 低 | 3.0→1.0 |

---

## 2. 逐项加固指南

### P0-A：移除硬编码密钥

**危险模式**：
```python
# ❌ 危险
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
DB_URL = "postgresql://user:pass@host/db"
```

**加固方案**：
```python
# ✅ 安全
import os

def get_api_key():
    key = os.environ.get("API_KEY")
    if not key:
        raise EnvironmentError("API_KEY environment variable is required")
    return key
```

### P0-B：收紧文件权限

**危险模式**：
```python
# ❌ 危险：任意路径写入
def save_file(path, content):
    with open(path, "w") as f:  # path 完全可控
        f.write(content)
```

**加固方案**：
```python
# ✅ 安全：路径验证 + workspace 限制
from pathlib import Path
import os

ALLOWED_DIR = Path("~/.qclaw/workspace").expanduser().resolve()

def safe_save_file(relative_path, content):
    target = (ALLOWED_DIR / relative_path).resolve()
    if not str(target).startswith(str(ALLOWED_DIR)):
        raise ValueError("Path outside workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
```

### P0-C：减少依赖

**原则**：
- 只引入必要的依赖
- 优先使用标准库
- 依赖必须声明版本

**检查命令**：
```bash
# Node.js
npm list --depth=0

# Python
pip freeze
```

### P1-A：强化输入验证

**危险模式**：
```python
# ❌ 危险：未验证输入
def query(sql, user_input):
    return db.execute(f"SELECT * FROM users WHERE {user_input}")
```

**加固方案**：
```python
# ✅ 安全：参数化查询 + 输入验证
import re

ALLOWED_COLUMNS = {"id", "name", "email"}

def safe_query(column, value):
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: {column}")
    if not re.match(r"^[\w@.-]+$", value):
        raise ValueError("Invalid value format")
    return db.execute(
        "SELECT * FROM users WHERE {} = %s".format(column),
        (value,)
    )
```

### P1-B：泛化错误信息

**危险模式**：
```python
# ❌ 危险：泄露内部路径
try:
    load_config("/etc/app/config.json")
except FileNotFoundError as e:
    return f"Config not found: {e.filename}"
```

**加固方案**：
```python
# ✅ 安全：泛化错误
try:
    load_config(config_path)
except FileNotFoundError:
    return "Configuration error: file not found"
except PermissionError:
    return "Configuration error: access denied"
except Exception:
    return "Configuration error: invalid format"
```

### P2-A：超时保护

**危险模式**：
```python
# ❌ 危险：无超时
def fetch_data(url):
    return requests.get(url)  # 可能永久阻塞
```

**加固方案**：
```python
# ✅ 安全：超时控制
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def fetch_data_with_timeout(url, timeout=30):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        return requests.get(url, timeout=timeout)
    finally:
        signal.alarm(0)
```

### P2-B：日志脱敏

**危险模式**：
```python
# ❌ 危险：敏感数据进日志
logger.info(f"User {user_id} logged in with token {token}")
```

**加固方案**：
```python
# ✅ 安全：脱敏日志
import re

def mask_sensitive(text):
    """脱敏邮箱、手机号、密钥"""
    text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', text)
    text = re.sub(r'\b\d{11}\b', '[PHONE]', text)
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[API_KEY]', text)
    return text

logger.info(f"User {user_id} logged in")  # 不含 token
```

---

## 3. 加固验证清单

```markdown
## 加固验证报告

Skill：<name>
版本：<version>
加固日期：<date>
审查者：CISO-001

### P0 加固验证

- [ ] P0-A 硬编码密钥：✅ 已移除 / ❌ 仍存在
- [ ] P0-B 文件权限：✅ 已收紧 / ❌ 仍宽松
- [ ] P0-C 依赖清理：✅ 已清理 / ❌ 仍冗余

### P1 加固验证

- [ ] P1-A 输入验证：✅ 已强化 / ❌ 仍薄弱
- [ ] P1-B 错误泛化：✅ 已泛化 / ❌ 仍详细

### P2 加固验证

- [ ] P2-A 超时保护：✅ 已添加 / ❌ 仍缺失
- [ ] P2-B 日志脱敏：✅ 已脱敏 / ❌ 仍明文

### 最终评估

| 指标 | 加固前 | 加固后 | 改善 |
|------|--------|--------|------|
| RED FLAGS | N | M | ⬇️ |
| CVSS 评分 | X.Y | Y.Z | ⬇️ |
| 攻击面 | 大 | 小 | ⬇️ |

**结论**：`[✅ 加固完成 / ⚠️ 部分加固 / 🚫 加固失败]`
```

---

## 附录：加固代码片段库

### 安全文件读取

```python
from pathlib import Path
import os

def safe_read_file(relative_path, base_dir="~/.qclaw/workspace"):
    base = Path(base_dir).expanduser().resolve()
    target = (base / relative_path).resolve()
    
    # 防止路径遍历
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal detected")
    
    # 防止 symlink 攻击
    if target.is_symlink():
        raise ValueError("Symlinks not allowed")
    
    return target.read_text(encoding="utf-8")
```

### 安全命令执行

```python
import subprocess
import shlex
import re

ALLOWED_COMMANDS = {"python", "node", "git", "npm"}

def safe_exec(command, args):
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {command}")
    
    # 验证参数（仅允许字母数字和常见符号）
    for arg in args:
        if not re.match(r'^[\w./-]+$', arg):
            raise ValueError(f"Invalid argument: {arg}")
    
    return subprocess.run(
        [command] + args,
        capture_output=True,
        timeout=30
    )
```
