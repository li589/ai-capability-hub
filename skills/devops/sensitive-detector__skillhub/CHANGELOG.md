# 变更日志

## [2.0.1] - 2026-04-10

### 🐛 问题修复

#### 映射持久化
- **修复**: 映射表持久化到 JSON 文件，解决进程重启后无法还原的问题
- **新增**: `sensitive_mappings.json` 自动保存敏感信息映射
- **改进**: `restore_ai_response()` 自动加载最新映射，确保跨进程还原

#### 集成改进
- **改进**: 初始化时自动设置映射文件路径
- **改进**: 每次脱敏自动保存，每次还原自动加载

### 📁 新增文件
- `sensitive_mappings.json` - 敏感信息映射存储（运行时生成）

---

## [2.0.0] - 2026-04-10

### 🎉 主要更新

#### 自动触发机制
- **新增**: Skill 定义为"自动触发"，无需关键词
- **新增**: 加载 Skill 后强制生效，无法关闭
- **新增**: 简化集成，只需在消息入口添加一次代码

#### 问题修复
- ✅ 修复 QQ 号误匹配问题
- ✅ 修复车牌号误匹配问题
- ✅ 优化 API Key 长度检测
- ✅ 修复区块链地址边界问题
- ✅ 修复信用卡号检测问题

#### 测试覆盖
- **新增**: 39 个互联网搜索测试用例
- **总计**: 92 个测试用例
- **通过率**: 100%

#### 性能优化
- **优化**: 100个敏感信息处理 < 0.01秒
- **优化**: 减少内存占用
- **优化**: 提高检测准确率

### 📋 支持的敏感信息类型（19种）

#### PII（个人身份信息）
- 手机号、身份证、邮箱、QQ号、车牌号
- 银行卡、信用卡、IP地址

#### API 密钥
- OpenAI、Anthropic、GitHub、Slack、Discord、Telegram、Google
- 数据库连接串

#### 凭证
- JWT Token、SSH 私钥

#### 区块链
- 以太坊地址、比特币地址、私钥、助记词

### 🔒 安全特性

- 强制生效，无法绕过
- 可逆脱敏，用户无感知
- 本地处理，不上传外部
- Prompt 注入检测
- 危险命令检测
- 风险评分机制（0-10分）

### 📖 文档更新

- 新增 `SKILL.md` - Skill 定义（自动触发）
- 新增 `README.md` - 快速开始指南
- 新增 `INSTALL.md` - 详细安装指南
- 更新 `CHANGELOG.md` - 版本变更日志

### 🚀 安装方法

```bash
# 1. 复制工具文件
mkdir -p /workspace/projects/workspace/工具/敏感信息检测
cp sensitive_detector.py /workspace/projects/workspace/工具/敏感信息检测/

# 2. 测试工具
python3 /workspace/projects/workspace/工具/敏感信息检测/sensitive_detector.py

# 3. 集成到代码
# 在消息处理入口添加：
from sensitive_detector import process_user_message, restore_ai_response

is_refused, processed, _ = process_user_message(message)
response = restore_ai_response(ai_function(processed))
```

### ⚠️ 重要提示

- **强制生效**: 加载 Skill 后自动开启，无法关闭
- **用户无感知**: 脱敏过程完全透明
- **本地处理**: 不上传任何数据到外部服务
- **Python 3.7+**: 需要的最低 Python 版本
- **无外部依赖**: 纯 Python 实现

---

## [1.0.0] - 2026-04-09

### 初始版本

#### 核心功能
- ✅ 可逆脱敏功能
- ✅ 图片敏感信息检测
- ✅ 支持 19 种敏感信息类型
- ✅ 安全防护功能

#### 基础特性
- 文本脱敏
- 图片脱敏
- 绕过检测
- 注入检测
- 危险命令检测

#### 技术规格
- Python 3.7+
- 无外部依赖
- 性能：优秀

---

## 版本说明

### 版本号规则

采用语义化版本号：`主版本.次版本.修订版本`

- **主版本**: 重大更新，不兼容旧版本
- **次版本**: 新增功能，向后兼容
- **修订版本**: 问题修复，向后兼容

### 更新类型

- 🎉 新增功能
- ✅ 问题修复
- 🔧 优化改进
- 📋 功能调整
- 🔒 安全更新
- 📖 文档更新

---

## 升级指南

### 从 v1.0.0 升级到 v2.0.0

#### 变更内容
- 从"手动调用"改为"自动触发"
- 简化集成方式
- 修复 5 个检测准确性问题
- 新增 39 个测试用例

#### 升级步骤

1. **备份旧版本**
```bash
cp -r /workspace/projects/workspace/工具/敏感信息检测 \
      /workspace/projects/workspace/工具/敏感信息检测.bak
```

2. **安装新版本**
```bash
cp sensitive_detector.py /workspace/projects/workspace/工具/敏感信息检测/
```

3. **更新集成代码**

**旧代码（v1.0.0）**:
```python
# 可能需要手动调用
from sensitive_detector import process_user_message
processed = process_user_message(message)
```

**新代码（v2.0.0）**:
```python
# 自动触发，在消息入口添加一次
from sensitive_detector import process_user_message, restore_ai_response
is_refused, processed, _ = process_user_message(message)
response = restore_ai_response(ai_function(processed))
```

4. **验证升级**
```bash
python3 /workspace/projects/workspace/工具/敏感信息检测/sensitive_detector.py
```

5. **删除备份**
```bash
rm -rf /workspace/projects/workspace/工具/敏感信息检测.bak
```

---

## 未来计划

### v2.1.0（计划中）
- [ ] 支持更多敏感信息类型
- [ ] 提供更多配置选项
- [ ] 优化性能

### v3.0.0（长期规划）
- [ ] 多语言支持
- [ ] 可视化配置界面
- [ ] 分布式处理支持

---

## 贡献者

- AI助手

## 许可证

MIT License

---

**更新时间**: 2026-04-10
**当前版本**: 2.0.0
**测试状态**: ✅ 所有测试通过（92/92）
