# OpenClaw HealthCheck Skill

🛡️ **OpenClaw 主机安全加固与风险评估工具**

[![SkillHub](https://img.shields.io/badge/SkillHub-v4.6.8-success.svg)](https://skillhub.cn/skills/openclaw-healthcheck)
[![ClawHub](https://img.shields.io/badge/ClawHub-Coming%20Soon-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ 功能特性

### 🔴 CVE 漏洞扫描
- 12个高危 CVE 检查（CVE-2026-25253, CVE-2026-32302 等）
- 增量更新机制，扫描效率提升 5.6 倍
- 自动修复支持

### 🦠 恶意技能检测
- 1,184+ 已知恶意技能库
- 可疑代码模式识别
- 供应链安全检查

### 💉 提示词注入防护
- HTML 注释过滤检测
- 系统指令保护检查

### 🛠️ 工具权限审计
- MCP 工具配置审计
- 最小权限配置建议

### 🔐 敏感数据保护
- 明文密钥扫描
- SSH 密钥权限检查

---

## 🚀 快速开始

### 通过 SkillHub 安装

```bash
skillhub install openclaw-healthcheck
```

### 通过 ClawHub 安装（即将支持）

```bash
clawhub install openclaw-healthcheck
```

### 基础使用

```bash
# 完整安全检查
./scripts/quick-start.sh --deep

# CVE 专项检查（带增量更新）
./examples/scripts/basic-cve-check.sh --update

# 恶意技能扫描
./scripts/security-checks.sh --scan-skills

# 查看更新状态
./examples/scripts/basic-cve-check.sh --status
```

---

## 📖 使用场景

### CVE 增量更新

```bash
# 首次运行：全量下载
./examples/scripts/basic-cve-check.sh --update

# 后续运行：自动增量检查
./examples/scripts/basic-cve-check.sh
# 耗时：8秒（首次45秒）

# 强制完整更新
./examples/scripts/basic-cve-check.sh --force
```

### 批量服务器扫描

```bash
for server in server1 server2 server3; do
  ssh $server "cd /tmp/healthcheck-skill && ./scripts/quick-start.sh --mode=scan-only"
done
```

---

## 📁 项目结构

```
healthcheck-skill/
├── SKILL.md                 # 技能主文件
├── README.md               # 项目说明
├── scripts/                # 安全检查脚本
│   ├── quick-start.sh      # 快速启动
│   ├── security-checks.sh  # 安全检查
│   ├── env-leak-detector.sh # 环境变量检测
│   └── ...
├── examples/               # 使用示例
│   └── basic-cve-check.sh  # CVE 检查（v2.3.0）
├── memory/                 # 反馈与路线图
│   └── feedback-and-roadmap.md
└── CHANGELOG.md            # 变更日志
```

---

## 🔧 系统要求

- OpenClaw Agent Framework v2.0+
- Bash 4.0+
- curl, jq, openssl

---

## 📊 版本信息

| 平台 | 版本 | 状态 |
|------|------|------|
| SkillHub | 4.6.8 | ✅ 已发布 |
| ClawHub | 待发布 | 🔄 开发中 |
| 虾评平台 | 4.6.8 | ✅ 已发布 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

**项目链接**：
- [SkillHub](https://skillhub.cn/skills/openclaw-healthcheck)
- [虾评平台](https://xiaping.coze.site/skill/61c9999f-1794-4f55-a6b8-6e457376b51e)
- [GitHub Issues](https://github.com/luck-security/openclaw-healthcheck-skill/issues)
