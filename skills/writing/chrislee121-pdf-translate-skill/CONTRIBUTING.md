# 贡献指南

感谢你有兴趣为pdf-translate skill做出贡献！

## 🤝 如何贡献

### 报告Bug

如果你发现了bug，请：

1. 检查 [Issues](https://github.com/yourusername/pdf-translate-skill/issues) 确保bug未被报告
2. 创建新Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（OS、Python版本、依赖版本）
   - 截图或错误日志

### 提出新功能

1. 先检查Issues确保功能未被建议
2. 创建新Issue，描述：
   - 功能描述和使用场景
   - 为什么这个功能有用
   - 可能的实现方案

### 提交代码

#### 准备工作

1. Fork本仓库
2. 克隆到本地：
   ```bash
   git clone https://github.com/yourusername/pdf-translate-skill.git
   cd pdf-translate-skill
   ```

3. 安装开发依赖：
   ```bash
   pip3 install -r requirements.txt
   ```

4. 创建特性分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### 开发规范

**代码风格**：
- 遵循PEP 8规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串

**测试**：
- 确保代码能正常运行
- 测试不同类型的PDF文件
- 验证字体配置在不同系统上的表现

**提交信息**：
- 使用清晰的commit message
- 遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：
  ```
  feat: 添加新功能
  fix: 修复bug
  docs: 更新文档
  refactor: 重构代码
  test: 添加测试
  chore: 构建/工具链更新
  ```

#### 提交流程

1. 提交代码：
   ```bash
   git add .
   git commit -m "feat: 添加你的新功能"
   ```

2. 推送到GitHub：
   ```bash
   git push origin feature/your-feature-name
   ```

3. 创建Pull Request：
   - 访问原仓库
   - 点击"New Pull Request"
   - 填写PR描述模板
   - 等待review

## 📋 PR审查流程

所有PR需要通过以下检查：

- [ ] 代码符合项目规范
- [ ] 新功能有相应文档
- [ ] 测试通过
- [ ] 没有引入新的警告或错误
- [ ] Commit message清晰

## 🎯 开发优先级

当前我们特别欢迎以下方面的贡献：

### 高优先级
- [ ] 支持更多PDF格式（扫描版、加密版）
- [ ] 添加单元测试
- [ ] 支持更多语言对的翻译

### 中优先级
- [ ] 性能优化（大文件处理）
- [ ] 更好的错误处理
- [ ] 命令行工具改进

### 低优先级
- [ ] GUI界面
- [ ] 云端翻译服务集成
- [ ] 批量处理工具

## 📖 文档贡献

改进文档也是非常重要的贡献方式！

你可以：
- 修正错别字和语法错误
- 改进示例代码
- 添加更多使用场景
- 翻译文档到其他语言

文档修改的PR通常会被快速合并。

## 🎨 代码风格示例

```python
# 好的代码
def translate_pdf_content(content: str) -> str:
    """
    翻译PDF内容

    Args:
        content: 原始PDF文本内容

    Returns:
        翻译后的文本
    """
    # 实现逻辑
    pass

# 不好的代码
def t(c):
    # 处理c
    pass
```

## 🔍 测试指南

### 本地测试

```bash
# 测试基础翻译
python3 scripts/translate_pdf.py test.pdf -o test_output.pdf

# 测试完整工作流
python3 scripts/generate_complete_pdf.py
```

### 测试检查清单

- [ ] 在macOS上测试
- [ ] 在Windows上测试
- [ ] 在Linux上测试
- [ ] 测试不同字号的PDF
- [ ] 测试包含图片的PDF
- [ ] 测试特殊字符和格式

## 💬 讨论和问题

在开始大型功能开发前，建议先创建Issue讨论：

- 描述你的想法和计划
- 等待维护者反馈
- 达成共识后再开始开发

这样可以避免浪费时间在不会被合并的功能上。

## 📜 行为准则

- 尊重所有贡献者
- 欢迎不同观点和建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 🏆 贡献者

所有贡献者将被列在项目的[贡献者](CONTRIBUTORS.md)文件中。

---

再次感谢你的贡献！🎉
