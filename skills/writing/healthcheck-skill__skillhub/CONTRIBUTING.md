# 贡献指南 | Contributing Guide

感谢您对 OpenClaw Healthcheck Skill 的兴趣！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了Bug或有功能建议，请通过以下方式报告：

1. **GitHub Issues**: https://github.com/openclaw/skills/healthcheck/issues
2. **安全问题**: 请发送邮件至 security@openclaw.ai（不要公开披露安全漏洞）

**报告问题时请提供**：
- 问题描述
- 复现步骤
- 环境信息（OS、OpenClaw版本等）
- 错误日志（如果有）

### 提交代码

1. **Fork 本仓库**
   ```bash
   git clone https://github.com/openclaw/skills/healthcheck.git
   cd healthcheck
   ```

2. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/issue-description
   ```

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加CVE-2026-xxxxx检测"
   ```

4. **推送并创建PR**
   ```bash
   git push origin feature/your-feature-name
   ```

   然后在GitHub上创建Pull Request。

### 提交规范

#### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: 
- `feat`: 新功能
- `fix`: 修复Bug
- `docs`: 文档更新
- `style`: 格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```
feat(cve): 添加CVE-2026-25253检测

- 检测gateway.controlUi.allowCustomGatewayUrl配置
- 提供一键修复功能
- 更新安全基线检查

Closes #123
```

## 📝 开发指南

### 技能文件结构

```
healthcheck/
├── SKILL.md              # 主要技能文档
├── README.md             # 项目说明
├── CHANGELOG.md          # 更新日志
├── LICENSE               # 许可证
├── package.json          # 元数据
├── examples/             # 使用示例
└── docs/                 # 详细文档
```

### 添加新的CVE检测

1. 在 `SKILL.md` 的 **CVE 专项安全检查** 部分添加：

```markdown
##### CVE-YYYY-XXXXX - 🔴 Critical CVSS X.X

**漏洞描述**：简要描述

**检查命令**：
\`\`\`bash
# 检查配置
openclaw config get xxx.xxx
\`\`\`

**安全基线**：
| 配置项 | 安全值 | 危险值 |
|-------|-------|-------|
| xxx | `true` | `false` |

**一键修复**：
\`\`\`bash
openclaw config set xxx true
\`\`\`
```

2. 更新 **威胁情报数据库**
3. 更新 **更新日志**
4. 添加 **FAQ**

### 添加恶意技能检测

1. 在恶意技能数据库中添加：

```json
{
  "name": "skill-name",
  "risk": "风险描述",
  "campaign": "攻击活动名称"
}
```

2. 添加检测模式（如果需要）

### 代码风格

- 使用清晰的命令注释
- 提供中英文双语说明
- 包含错误处理
- 添加进度显示

## 🧪 测试要求

提交PR前请确保：

- [ ] 在至少2种不同环境类型测试
- [ ] 更新相关文档
- [ ] 确保向后兼容
- [ ] 添加/更新测试用例

### 测试环境

推荐测试环境：
1. **VPS/云服务器** - 完整功能测试
2. **本地工作站** - 日常使用场景
3. **Docker容器** - 隔离环境测试
4. **沙盒环境** - 权限限制测试

## 📋 待办事项

### 高优先级

- [ ] 集成更多CVE漏洞检测
- [ ] 优化恶意技能数据库更新机制
- [ ] 添加实时监控功能

### 中优先级

- [ ] 支持更多云平台（华为云、GCP、Azure）
- [ ] 添加可视化报告
- [ ] 优化检测性能

### 低优先级

- [ ] 添加更多语言支持
- [ ] 开发GUI界面
- [ ] 企业级功能

## 🏆 贡献者

感谢所有为这个项目做出贡献的人！

### 核心团队

- luck (AI Assistant) - 主要开发

### 特别感谢

- OpenClaw 社区
- 安全研究员
- 威胁情报提供者

## 📞 联系方式

- **一般问题**: GitHub Issues
- **安全问题**: security@openclaw.ai
- **讨论**: GitHub Discussions

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**再次感谢您的贡献！** 🙏

