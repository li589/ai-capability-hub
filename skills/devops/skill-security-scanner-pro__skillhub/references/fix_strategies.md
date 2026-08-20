# 安全修复策略指南

## 目录
- [概述](#概述)
- [本地命令执行修复](#本地命令执行修复)
- [命令注入修复](#命令注入修复)
- [敏感路径访问修复](#敏感路径访问修复)
- [外部下载与执行修复](#外部下载与执行修复)
- [动态导入修复](#动态导入修复)
- [硬编码凭证修复](#硬编码凭证修复)
- [路径遍历修复](#路径遍历修复)
- [不安全的反序列化修复](#不安全的反序列化修复)

## 概述
本文档提供了针对不同安全风险类型的修复策略和最佳实践。

## 本地命令执行修复

### 修复方法
使用工具调用或参数化命令替代直接命令执行。

### 修复策略

#### 1. 使用 exec_shell 工具（推荐）
```python
# 修复前
os.system(f"rm -rf {user_dir}")

# 修复后
# 通过智能体调用 exec_shell 工具，参数化执行
```

#### 2. 使用 subprocess 的安全参数
```python
# 修复前
os.system(f"cp {src} {dst}")

# 修复后
import subprocess
subprocess.run(["cp", src, dst], check=True)  # 列表形式，避免 shell 解析
```

#### 3. 移除不必要的命令执行
```python
# 修复前
os.system("mkdir -p output")

# 修复后
import os
os.makedirs("output", exist_ok=True)  # 使用 Python 原生函数
```

### 注意事项
- 避免使用 shell=True 参数
- 使用列表形式传递参数
- 验证和清理所有用户输入

## 命令注入修复

### 修复方法
移除或转义危险字符，使用参数化命令。

### 修复策略

#### 1. 移除危险字符
```python
# 修复前
command = f"cat {filename}; rm -rf /"

# 修复后
import re
safe_filename = re.sub(r'[;&|`$]', '', filename)
command = f"cat {safe_filename}"
```

#### 2. 使用参数化命令
```python
# 修复前
os.system(f"ls -l {user_path}")

# 修复后
import subprocess
subprocess.run(["ls", "-l", user_path], check=True)
```

#### 3. 输入验证
```python
# 修复前
os.system(f"cat {user_input}")

# 修复后
import os
# 验证文件名
if not re.match(r'^[a-zA-Z0-9_.-]+$', user_input):
    raise ValueError("Invalid filename")
with open(user_input, 'r') as f:
    print(f.read())
```

### 注意事项
- 永远不要信任用户输入
- 使用白名单验证
- 避免字符串拼接命令

## 敏感路径访问修复

### 修复方法
添加路径白名单检查，限制访问范围。

### 修复策略

#### 1. 路径白名单
```python
# 修复前
with open(user_path) as f:
    print(f.read())

# 修复后
import os
ALLOWED_DIRS = ['/workspace/projects', './data']

abs_path = os.path.abspath(user_path)
if not any(abs_path.startswith(d) for d in ALLOWED_DIRS):
    raise PermissionError("Access denied")

with open(abs_path) as f:
    print(f.read())
```

#### 2. 使用相对路径
```python
# 修复前
with open('/etc/passwd') as f:  # 系统文件
    print(f.read())

# 修复后
with open('./config/users.txt') as f:  # 相对路径
    print(f.read())
```

#### 3. 路径规范化
```python
# 修复前
filename = '../../etc/passwd'
with open(filename) as f:
    print(f.read())

# 修复后
from pathlib import Path
safe_path = Path(filename).resolve()
if not str(safe_path).startswith('/workspace'):
    raise PermissionError("Access denied")
with open(safe_path) as f:
    print(f.read())
```

### 注意事项
- 使用绝对路径进行验证
- 限制访问范围到项目目录
- 禁止访问系统敏感目录

## 外部下载与执行修复

### 修复方法
添加来源白名单和内容验证。

### 修复策略

#### 1. 来源白名单
```python
# 修复前
import urllib.request
content = urllib.request.urlopen(user_url).read()

# 修复后
import urllib.request

ALLOWED_DOMAINS = ['example.com', 'trusted.com']

from urllib.parse import urlparse
parsed = urlparse(user_url)
if parsed.netloc not in ALLOWED_DOMAINS:
    raise ValueError("Untrusted domain")

content = urllib.request.urlopen(user_url).read()
```

#### 2. 内容验证
```python
# 修复前
import requests
code = requests.get(url).text
exec(code)  # 直接执行

# 修复后
import requests
import ast

response = requests.get(url)
# 验证内容是否为安全格式
try:
    data = json.loads(response.text)  # 使用安全的 JSON
except json.JSONDecodeError:
    raise ValueError("Invalid content format")
```

#### 3. 使用安全的替代方案
```python
# 修复前
import urllib.request
urllib.request.urlopen('http://example.com/script.py').read()

# 修复后
# 使用包管理器或已验证的资源
import requests
from coze_workload_identity import requests  # 安全的请求库
```

### 注意事项
- 验证下载来源
- 检查文件类型和内容
- 避免直接执行下载的代码

## 动态导入修复

### 修复方法
使用静态导入替代动态导入。

### 修复策略

#### 1. 使用静态导入
```python
# 修复前
module = __import__(user_module_name)

# 修复后
import module1
import module2

# 使用条件导入
if condition:
    import module1
else:
    import module2
```

#### 2. 使用 importlib 的安全方法
```python
# 修复前
module = __import__(user_input)

# 修复后
import importlib
import importlib.util

# 白名单验证
ALLOWED_MODULES = ['module1', 'module2']
if user_input not in ALLOWED_MODULES:
    raise ValueError("Module not allowed")

module = importlib.import_module(user_input)
```

#### 3. 移除动态执行
```python
# 修复前
exec(f"import {user_module}")

# 修复后
# 使用配置文件或注册表
MODULES = {
    'option1': module1,
    'option2': module2,
}
module = MODULES.get(user_option)
```

### 注意事项
- 优先使用静态导入
- 如果必须动态导入，使用白名单
- 避免执行动态生成的代码

## 硬编码凭证修复

### 修复方法
使用环境变量或配置管理工具。

### 修复策略

#### 1. 使用环境变量
```python
# 修复前
API_KEY = "sk-1234567890abcdef"

# 修复后
import os
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not set")
```

#### 2. 使用配置文件
```python
# 修复前
PASSWORD = "admin123"

# 修复后
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
PASSWORD = config.get('credentials', 'password')
```

#### 3. 使用密钥管理服务
```python
# 修复前
SECRET_KEY = "my-secret-key"

# 修复后
from coze_workload_identity import get_credential
SECRET_KEY = get_credential("secret_key")
```

### 注意事项
- 永远不要在代码中硬编码凭证
- 使用环境变量或配置管理
- 定期轮换敏感凭证

## 路径遍历修复

### 修复方法
规范化路径，检查是否在允许范围内。

### 修复策略

#### 1. 路径规范化
```python
# 修复前
filename = user_input
with open(f'/data/{filename}') as f:
    print(f.read())

# 修复后
from pathlib import Path

base_dir = Path('/data').resolve()
user_path = (base_dir / user_input).resolve()

if not str(user_path).startswith(str(base_dir)):
    raise PermissionError("Path traversal detected")

with open(user_path) as f:
    print(f.read())
```

#### 2. 文件名验证
```python
# 修复前
filename = user_input
with open(filename) as f:
    print(f.read())

# 修复后
import re

if not re.match(r'^[a-zA-Z0-9_.-]+$', user_input):
    raise ValueError("Invalid filename")

filename = user_input
with open(filename) as f:
    print(f.read())
```

#### 3. 使用安全的文件操作
```python
# 修复前
open(user_path, 'w')

# 修复后
from pathlib import Path

safe_path = Path(user_path).resolve()
if not safe_path.is_relative_to('/workspace'):
    raise PermissionError("Invalid path")
```

### 注意事项
- 使用 Path.resolve() 规范化路径
- 验证路径是否在允许范围内
- 禁止使用相对路径

## 不安全的反序列化修复

### 修复方法
使用安全的序列化格式。

### 修复策略

#### 1. 使用 JSON 替代 pickle
```python
# 修复前
import pickle
data = pickle.loads(user_data)

# 修复后
import json
data = json.loads(user_data)  # JSON 是安全的
```

#### 2. 使用安全的 YAML 加载
```python
# 修复前
import yaml
data = yaml.unsafe_load(yaml_string)

# 修复后
import yaml
data = yaml.safe_load(yaml_string)  # 安全加载
```

#### 3. 数据验证
```python
# 修复前
import pickle
data = pickle.loads(user_data)

# 修复后
import pickle

# 验证数据结构
def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid data type")
    # 更多验证规则...

data = pickle.loads(user_data)
validate_data(data)
```

### 注意事项
- 优先使用 JSON
- 如果使用 YAML，使用 safe_load
- 验证反序列化的数据结构

## 附录：修复优先级

1. **Critical**: 立即修复
   - 命令注入
   - 远程代码执行

2. **High**: 优先修复
   - 本地命令执行
   - 路径遍历
   - 不安全的反序列化
   - 敏感路径访问

3. **Medium**: 计划修复
   - 外部下载与执行
   - 动态导入
   - 硬编码凭证

4. **Low**: 建议修复
   - 其他低风险问题
