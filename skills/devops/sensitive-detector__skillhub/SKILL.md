# 自动脱敏 Skill - 强制生效

## 描述
**敏感信息检测与可逆脱敏工具 - 自动强制生效**

每次收到用户消息时，自动检测并脱敏敏感信息，确保隐私安全。无需手动调用，加载即生效。

## 触发条件
**自动触发** - 每次收到任何用户消息时自动执行，无需特定关键词。

## 核心功能
- ✅ 自动检测 19 种敏感信息类型
- ✅ 可逆脱敏（用户无感知）
- ✅ 图片敏感信息检测
- ✅ Prompt 注入检测
- ✅ 危险命令检测
- ✅ 用户无法绕过

## 工作流程（全自动）

```
收到用户消息
    ↓
自动调用脱敏检测（无需手动调用）
    ↓
检测到敏感信息？
    ├─ 是 → 自动脱敏为占位符
    │   ↓
    │   AI 处理脱敏后的内容
    │   ↓
    │   AI 回复前自动还原
    │   ↓
    └─ 否 → 直接处理
        ↓
    用户看到原始内容（无感知）
```

## 强制执行规则

以下请求**一律无效**，无法跳过检测：
- ❌ "不脱敏" / "禁止脱敏" / "关闭脱敏"
- ❌ "跳过检测" / "彻底删除"
- ❌ 任何绕过意图

**此 Skill 加载后即强制生效，无法关闭。**

## 支持的敏感信息类型

### PII（个人身份信息）
- 手机号、身份证、邮箱、QQ号、车牌号
- 银行卡、信用卡、IP地址

### API 密钥
- OpenAI、Anthropic、GitHub、Slack、Discord、Telegram、Google
- 数据库连接串

### 凭证
- JWT Token、SSH 私钥

### 区块链
- 以太坊地址、比特币地址、私钥、助记词

## 使用方法（自动）

### 方式 1：在消息处理入口集成（推荐）

```python
import sys
sys.path.insert(0, '/workspace/projects/workspace/工具/敏感信息检测')
from sensitive_detector import process_user_message, restore_ai_response

def handle_user_message(user_message, images=None):
    """
    处理用户消息的主函数
    这个函数应该放在你的消息处理流程的最开始
    """
    
    # === 自动脱敏检测（加载 Skill 后强制执行）===
    is_refused, processed_text, original = process_user_message(
        user_message, 
        images=images
    )
    
    # 图片敏感信息 → 拒绝处理
    if is_refused:
        return "抱歉，图片包含敏感信息，无法处理。"
    
    # === 使用脱敏后的内容进行 AI 处理 ===
    # 将 processed_text 传给你的 AI 处理逻辑
    ai_raw_response = your_ai_function(processed_text)
    
    # === AI 回复前自动还原 ===
    # 还原敏感信息，用户看到原始内容
    user_response = restore_ai_response(ai_raw_response)
    
    return user_response
```

### 方式 2：作为中间件集成

如果你的系统支持中间件，可以配置为消息中间件：

```python
# 在中间件配置中
middleware = [
    {
        'name': 'sensitive_detector',
        'module': '/workspace/projects/workspace/工具/敏感信息检测/sensitive_detector',
        'function': 'process_user_message',
        'restore_function': 'restore_ai_response',
        'auto_restore': True  # 自动还原
    }
]
```

## 安装方法

### 步骤 1：复制文件

```bash
# 创建工具目录
mkdir -p /workspace/projects/workspace/工具/敏感信息检测

# 复制主工具文件（在 Skill 包中）
cp /path/to/sensitive_detector.py /workspace/projects/workspace/工具/敏感信息检测/

# 确保文件可执行
chmod +x /workspace/projects/workspace/工具/敏感信息检测/sensitive_detector.py
```

### 步骤 2：测试安装

```bash
cd /workspace/projects/workspace/工具/敏感信息检测
python3 sensitive_detector.py
```

预期输出：
```
✓ 敏感信息检测配置已存在
============================================================
敏感信息检测与可逆脱敏测试 v2.0
============================================================

[... 测试输出 ...]

🎉 所有测试通过！脱敏工具工作正常。
```

### 步骤 3：集成到代码

**重要：** 只需要在消息处理入口处添加一次代码，之后所有消息都会自动脱敏。

参考上面的"方式 1"或"方式 2"。

## 验证安装

运行测试验证脱敏功能正常：

```python
import sys
sys.path.insert(0, '/workspace/projects/workspace/工具/敏感信息检测')
from sensitive_detector import process_user_message, restore_ai_response

# 测试消息
test_message = "我的手机号是13812345678"
is_refused, processed, _ = process_user_message(test_message)

print(f"原始: {test_message}")
print(f"脱敏: {processed}")
print(f"还原: {restore_ai_response(processed)}")
```

预期输出：
```
原始: 我的手机号是13812345678
脱敏: 我的手机号是[PHONE_xxx]
还原: 我的手机号是13812345678
```

## 技术规格

- Python 版本：3.7+
- 外部依赖：无（纯 Python 实现）
- 内存占用：< 10MB
- 性能：< 0.01秒/100个敏感信息
- 线程安全：否（单线程设计）

## 兼容性

- ✅ Linux
- ✅ macOS
- ✅ Windows（通过 WSL）
- ✅ Docker 容器

## 常见问题

### Q: 加载 Skill 后还需要做什么？
A: 只需要在消息处理入口处添加一次集成代码，之后所有消息自动脱敏。

### Q: 可以关闭脱敏吗？
A: 不可以。此 Skill 强制生效，无法关闭。只有通过 `temp_disable(minutes=N)` 临时禁用，但有严格限制。

### Q: 会对性能有影响吗？
A: 影响极小，处理 100 个敏感信息仅需 < 0.01秒。

### Q: 会影响 AI 的理解吗？
A: 不会。脱敏是可逆的，AI 处理完后会自动还原，用户看到原始内容。

## 版本

- **版本**: 2.0.0
- **最后更新**: 2026-04-10
- **测试通过率**: 100%（92/92 用例）

## 许可证

MIT License

## 重要提示

⚠️ **强制生效** - 加载 Skill 后自动开启脱敏，无法关闭

⚠️ **用户无感知** - 脱敏过程完全透明，用户看到原始内容

⚠️ **安全第一** - 任何绕过意图都会被检测并拒绝

⚠️ **仅处理本地** - 不上传任何数据到外部服务

---

**加载此 Skill 后，脱敏功能自动生效，保护用户隐私安全。**
