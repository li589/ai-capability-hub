# HealthCheck 可执行检测样例

本目录包含可独立运行的检测脚本和预期输出样例，用于演示 HealthCheck 技能的核心功能。

## 📁 目录结构

```
examples/
├── scripts/           # 可执行检测脚本
│   ├── basic-cve-check.sh       # 基础CVE漏洞检查
│   ├── malicious-skill-scan.sh  # 恶意技能扫描
│   ├── config-audit.sh          # 配置审计
│   ├── permission-check.sh      # 权限检查
│   └── cloud-detection.sh       # 云环境检测
├── outputs/           # 预期输出样例
│   ├── cve-check-success.json   # CVE检查无漏洞
│   ├── cve-check-warning.json   # CVE检查发现警告
│   ├── cve-check-critical.json  # CVE检查发现严重漏洞
│   ├── skill-scan-clean.json    # 技能扫描干净
│   └── skill-scan-malicious.json # 技能扫描发现恶意
└── README.md          # 本文件
```

## 🚀 快速开始

### 运行基础CVE检查

```bash
# 赋予执行权限
chmod +x scripts/basic-cve-check.sh

# 运行脚本
./scripts/basic-cve-check.sh
```

**预期输出**:
- 交互式文本报告（终端显示）
- JSON格式输出（脚本末尾）

### 运行恶意技能扫描

```bash
# 赋予执行权限
chmod +x scripts/malicious-skill-scan.sh

# 运行脚本
./scripts/malicious-skill-scan.sh
```

**输出说明**:
- 扫描每个已安装技能
- 标记已知恶意技能（红色警告）
- 标记可疑技能（黄色警告）
- 最后输出JSON格式结果

## 📊 预期输出样例

### CVE检查结果样例

**无漏洞** (`cve-check-success.json`):
- OpenClaw版本最新
- 所有CVE配置安全
- 风险评分为0
- 建议：继续保持

**有警告** (`cve-check-warning.json`):
- 发现2个可修复的CVE配置问题
- 1个需要升级版本
- 风险评分65（High）
- 建议：运行自动修复

**严重漏洞** (`cve-check-critical.json`):
- 发现多个高危漏洞
- 系统可能已被入侵
- 风险评分95（Critical）
- 建议：立即断开网络，重建环境

### 技能扫描结果样例

**干净** (`skill-scan-clean.json`):
- 所有技能来自官方ClawHub
- 无已知恶意技能
- 无可疑代码模式
- 安全状态良好

**发现恶意** (`skill-scan-malicious.json`):
- 发现1个恶意技能（youtube-summarize-pro）
- 发现2个可疑技能
- 可能已泄露浏览器密码和加密货币钱包
- 需要立即采取行动

## 🔧 脚本详解

### basic-cve-check.sh

**功能**: 检查4个关键CVE漏洞的配置状态

**检查的CVE**:
1. CVE-2026-25253 (ClawJacked) - CVSS 8.8
2. CVE-2026-32302 (反向代理绕过) - CVSS 8.1
3. CVE-2026-29610 (命令劫持) - CVSS 8.8
4. CVE-2026-28466 (审批绕过) - CVSS 9.4

**输出格式**:
- 交互式报告（人类可读）
- JSON格式（程序处理）

**使用场景**:
```bash
# 作为独立安全检查
./basic-cve-check.sh

# 保存JSON结果
./basic-cve-check.sh > cve-report.json
```

### malicious-skill-scan.sh

**功能**: 扫描已安装技能，检测恶意软件和可疑代码

**检测能力**:
- 1,184个已知恶意技能数据库
- 可疑代码模式（curl|bash、base64、反向shell）
- 高危关键词（crypto、wallet、steal）

**输出信息**:
- 技能名称和状态
- 恶意软件来源活动
- 可疑代码模式详情
- 修复建议

**使用场景**:
```bash
# 定期检查
./malicious-skill-scan.sh

# 在CI/CD中使用（仅输出JSON）
./malicious-skill-scan.sh 2>/dev/null | tail -20
```

## 📖 如何使用这些样例

### 场景1：验证HealthCheck技能

1. 运行样例脚本
2. 对比实际输出和预期输出
3. 验证检测逻辑的正确性

### 场景2：集成到CI/CD

```bash
# 在部署前运行检查
./scripts/basic-cve-check.sh > /tmp/cve-report.json

# 检查是否有严重漏洞
CRITICAL_COUNT=$(cat /tmp/cve-report.json | jq '.summary.critical_count')
if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo "❌ 发现严重CVE漏洞，阻止部署"
    exit 1
fi
```

### 场景3：自定义检测脚本

基于提供的样例，创建自己的检测脚本：

```bash
#!/bin/bash
# 自定义检测脚本模板

# 引入健康检查函数
source /path/to/healthcheck-skill/scripts/lib/healthcheck-utils.sh

# 添加自定义检查
my_custom_check() {
    # 你的检测逻辑
    if [ "$condition" ]; then
        echo "✅ 通过"
    else
        echo "❌ 失败"
    fi
}

# 运行检查
my_custom_check
```

### 场景4：教育和培训

使用样例输出教授安全概念：

```bash
# 展示不同严重程度的检查结果
cat outputs/cve-check-success.json | jq '.summary'
cat outputs/cve-check-warning.json | jq '.summary'
cat outputs/cve-check-critical.json | jq '.summary'
```

## 🔍 技术细节

### 误报率统计集成

脚本会自动记录检测历史，用于计算误报率：

```bash
# 记录检测事件
../scripts/false-positive-tracker.sh log cve critical fail '{"cve":"CVE-2026-25253"}'

# 用户确认后为误报时标记
../scripts/false-positive-tracker.sh mark 5 true "实际为正常配置"

# 查看误报率
../scripts/false-positive-tracker.sh rate all 30
```

### 环境检测

脚本会自动检测运行环境：
- VPS/云服务器
- 本地工作站
- Docker容器
- 沙盒环境

根据环境类型调整检测策略。

## ⚠️ 注意事项

1. **权限要求**: 部分检查需要读取OpenClaw配置目录的权限
2. **版本兼容**: 脚本需要OpenClaw >= 2026.3.0
3. **网络访问**: CVE检查不需要网络，恶意技能扫描需要读取本地文件
4. **安全建议**: 不要在生产环境直接修改脚本，先在测试环境验证

## 🤝 贡献

欢迎提交新的检测脚本或改进现有脚本：

1. Fork本仓库
2. 在 `examples/scripts/` 目录添加新脚本
3. 在 `examples/outputs/` 添加预期输出样例
4. 更新本README.md
5. 提交Pull Request

## 📚 相关文档

- [SKILL.md](../SKILL.md) - 完整的技能文档
- [CHANGELOG.md](../CHANGELOG.md) - 版本更新日志
- [PLAN-v2.2.0.md](../PLAN-v2.2.0.md) - v2.2.0开发计划

## 📄 许可证

MIT License - OpenClaw Community
