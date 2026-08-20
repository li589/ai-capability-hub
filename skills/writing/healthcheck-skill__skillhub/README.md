# OpenClaw Healthcheck Skill v2.1.0

🛡️ **OpenClaw 主机安全加固与风险评估工具**

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/openclaw/skills/healthcheck)
[![Security](https://img.shields.io/badge/security-critical-red.svg)](https://security.openclaw.ai)
[![Language](https://img.shields.io/badge/language-zh--CN%20%7C%20en-green.svg)]()

---

## 🚨 紧急安全提醒（2026年3月）

> ⚠️ **当前威胁态势严峻**
> - 全球46.9万OpenClaw实例暴露，27%存在高危漏洞
> - CVE-2026-25253 (ClawJacked) 已发现在野大规模利用
> - ClawHub技能市场12%为恶意技能（超1,184个）
> - 朝鲜APT37、Kimsuky，俄罗斯APT28等正在积极攻击

**本技能覆盖**：
- ✅ 12个CVE高危漏洞专项检查
- ✅ 恶意技能自动扫描与清除
- ✅ 提示词注入防护检测
- ✅ MCP工具权限审计
- ✅ 敏感数据泄露防护

---

## ✨ 核心特性

### 🔴 CVE专项安全检查（2026年3月紧急更新）

覆盖12个已发现在野利用的CVE漏洞：

| CVE编号 | CVSS | 风险等级 | 在野利用 | 一键修复 |
|---------|------|---------|---------|---------|
| [CVE-2026-25253](https://nvd.nist.gov/vuln/detail/CVE-2026-25253) | 8.8 | 🔴 Critical | ✅ | ✅ |
| [CVE-2026-32302](https://nvd.nist.gov/vuln/detail/CVE-2026-32302) | 8.1 | 🔴 Critical | ⚠️ | ✅ |
| [CVE-2026-28466](https://nvd.nist.gov/vuln/detail/CVE-2026-28466) | 9.4 | 🔴 Critical | ✅ | ⚠️ |
| [CVE-2026-29610](https://nvd.nist.gov/vuln/detail/CVE-2026-29610) | 8.8 | 🔴 Critical | ✅ | ✅ |
| [CVE-2026-24763](https://nvd.nist.gov/vuln/detail/CVE-2026-24763) | 8.8 | 🔴 High | ⚠️ | ⚠️ |
| [CVE-2026-25157](https://nvd.nist.gov/vuln/detail/CVE-2026-25157) | 8.1 | 🔴 High | ⚠️ | ⚠️ |

### 🦠 恶意技能/插件供应链安全检查

- **恶意技能数据库**：1,184个已知恶意技能
- **自动扫描**：检测已安装技能中的威胁
- **可疑代码检测**：curl|bash、base64、反向shell等模式

### 💉 提示词注入防护检查

- HTML注释过滤检测
- 隐藏内容检测
- 系统指令保护检查

### 🛠️ MCP工具权限审计

- exec/browser/web_fetch 配置检查
- 最小权限配置建议

### 🔐 敏感数据保护检查

- 明文API密钥扫描
- SSH密钥权限检查
- MEMORY.md敏感信息检测

---

## 🚀 快速开始

### 安装

```bash
# 通过ClawHub安装
openclaw skills install healthcheck

# 或通过GitHub安装
openclaw skills install https://github.com/openclaw/skills/healthcheck
```

### 基础使用

```bash
# 完整安全检查（推荐）
healthcheck --deep

# CVE专项检查
healthcheck --cve-check

# 恶意技能扫描
healthcheck --skill-scan

# 一键修复高危问题
healthcheck --fix --severity=critical
```

---

## 📖 使用场景

### 场景1：CVE紧急响应
```bash
$ healthcheck --cve-check

🔴 CVE 专项安全报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ CVE-2026-25253 (ClawJacked) - 配置存在漏洞
❌ CVE-2026-28466 (Node审批绕过) - 需升级版本
✅ CVE-2026-32302 - 配置安全

修复命令：
$ openclaw security audit --fix --severity=critical
$ openclaw update
```

### 场景2：恶意技能排查
```bash
$ healthcheck --skill-scan

🦠 技能供应链安全报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
扫描技能总数: 15
🔴 发现恶意技能: 1个
   └─ youtube-summarize-pro (ClawHavoc木马)
⚠️  发现可疑技能: 2个

建议：立即删除恶意技能
$ openclaw skills remove youtube-summarize-pro
```

### 场景3：全面安全加固
```bash
$ healthcheck --deep

🔄 综合安全审计 [步骤 2/8]
[████████████████░░░░] 80%

已完成：
  ✅ 步骤 2.0: 基础安全审计
  ✅ 步骤 2.1: CVE专项检查 (6/6)
  ✅ 步骤 2.2: 恶意技能扫描
  ✅ 步骤 2.3: 提示词注入防护
  ✅ 步骤 2.4: MCP工具权限
  ⏳ 步骤 2.5: 敏感数据保护
```

---

## 📊 安全检查维度

| 检查项 | 覆盖范围 | 优先级 | 自动修复 |
|-------|---------|--------|---------|
| CVE-2026-25253 (ClawJacked) | 🔴 Critical | P0 | ✅ |
| CVE-2026-32302 (Proxy Bypass) | 🔴 Critical | P0 | ✅ |
| CVE-2026-28466 (Approval Bypass) | 🔴 Critical | P0 | ⚠️ |
| CVE-2026-29610 (PATH Hijack) | 🔴 Critical | P0 | ✅ |
| 恶意技能检测 | 🔴 Critical | P0 | ⚠️ |
| 提示词注入防护 | 🟠 High | P1 | ✅ |
| MCP工具权限 | 🟠 High | P1 | ✅ |
| 凭证存储安全 | 🟠 High | P1 | ⚠️ |
| 文件权限 | 🟡 Medium | P2 | ✅ |
| 网络暴露 | 🟡 Medium | P2 | ✅ |

---

## 🛡️ 威胁情报

### 当前威胁态势（2026年3月）

```
🔴 全球暴露实例：46.9万+（活跃20.3万）
🔴 存在漏洞实例：27.2%（约12.7万台）
🔴 与APT组织关联：40.7%（111,389台）
🔴 恶意技能数量：1,184个（占ClawHub的8-12%）
🔴 凭证泄露实例：37.2%
```

### APT组织威胁

| APT组织 | 国家 | 关联实例数 | 主要目标 |
|--------|------|-----------|---------|
| APT37 | 朝鲜 | 92,659 | 加密货币 |
| Kimsuky | 朝鲜 | 81,754 | 金融数据 |
| APT28 | 俄罗斯 | 79,422 | 政府机构 |
| Sandworm Team | 俄罗斯 | 74,456 | 基础设施 |

---

## 📋 报告格式

支持6种输出格式：

1. **交互式文本** - 实时进度显示
2. **Markdown格式** - 详细审计报告
3. **JSON格式** - 程序化处理
4. **对比报告** - 修复前后对比
5. **CVE专项报告** - 漏洞详细分析
6. **技能安全报告** - 供应链安全分析

---

## 🔧 系统要求

- OpenClaw >= 2026.1.29（建议 >= 2026.3.12）
- 支持环境：VPS/云服务器 | 本地工作站 | Docker | 沙盒
- 语言：中文 | English

---

## 🤝 贡献

欢迎提交Issue和PR！

### 待办事项

- [ ] 集成更多CVE漏洞检测
- [ ] 更新恶意技能数据库
- [ ] 添加更多云平台支持
- [ ] 优化检测性能

---

## 📄 许可

MIT License - OpenClaw Community

---

## 🙏 致谢

- 威胁情报来源：国家互联网应急中心(CNCERT)、工信部NVDB、GitHub Security Advisory
- 恶意技能数据：Koi Security、VirusTotal、ClawHub Security Team
- CVE信息：NVD、CNNVD

---

## 📞 联系

- **Issues**: https://github.com/openclaw/skills/healthcheck/issues
- **讨论**: https://github.com/openclaw/skills/healthcheck/discussions
- **安全报告**: security@openclaw.ai

---

**⚠️ 免责声明**：本技能仅用于安全加固和漏洞检测，不对因使用本技能造成的任何损失负责。请始终在测试环境验证后再应用于生产环境。

**建议**：所有OpenClaw用户应立即运行本技能进行全面安全检查！

