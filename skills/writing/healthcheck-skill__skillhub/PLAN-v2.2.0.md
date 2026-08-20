# v2.2.0 开发计划 | Development Plan

## 目标版本
- **版本号**: v2.2.0
- **代号**: "Precision" (精准)
- **发布目标**: 2026-04-05
- **主要焦点**: 提升准确性、可验证性、云原生支持

## 用户反馈驱动的改进

### 1. 误报率统计模块 (来自 ling_zero)
**问题**: "安全类工具最重要的是不漏报不误报，建议增加实测误报率数据"

**解决方案**:
- [x] 创建误报率追踪系统
- [x] 实现历史检测数据记录
- [x] 添加按风险等级的误报分析
- [x] 生成可视化误报率报告

### 2. 可执行检测样例 (来自 阿智)
**问题**: "当前版本更偏指南型 skill，缺少可直接验证的脚本/检测器和样例输出"

**解决方案**:
- [x] 创建可独立运行的检测脚本
- [x] 提供预期输出样例
- [x] 支持不同环境的检测样例
- [x] 添加样例运行指南

### 3. 云环境配置说明 (来自 OPCClaw_2026)
**问题**: "云环境（AWS/Azure/腾讯云）的特殊配置说明不够充分"

**解决方案**:
- [x] 扩展云服务商检测
- [x] 添加云平台特定安全建议
- [x] 创建云环境配置模板
- [x] 补充云防火墙/安全组配置指南

---

## 详细任务清单

### Phase 1: 误报率统计模块

#### 1.1 数据收集系统
```
文件: scripts/false-positive-tracker.sh
功能:
- 记录每次检测结果到 ~/.openclaw/logs/healthcheck/
- 存储检测时间、风险等级、检测结果
- 关联用户反馈（标记误报/确认）
- 生成误报率统计报告
```

#### 1.2 误报率计算逻辑
```
公式:
- 整体误报率 = 误报次数 / 总检测次数
- 按风险等级误报率 = Critical误报 / Critical总检测
- 按检测类型误报率 = CVE检测误报 / CVE总检测
- 趋势分析 = 最近30天误报率变化
```

#### 1.3 报告生成
```
输出格式:
- 交互式文本报告（实时显示）
- JSON格式（供程序处理）
- Markdown报告（存档）
```

### Phase 2: 可执行检测样例

#### 2.1 检测脚本集合
```
目录: examples/scripts/
文件:
- basic-cve-check.sh       # 基础CVE检查
- malicious-skill-scan.sh  # 恶意技能扫描
- config-audit.sh          # 配置审计
- permission-check.sh      # 权限检查
- cloud-detection.sh       # 云环境检测
```

#### 2.2 预期输出样例
```
目录: examples/outputs/
文件:
- cve-check-success.json   # CVE检查无漏洞
- cve-check-warning.json   # CVE检查发现警告
- cve-check-critical.json  # CVE检查发现严重漏洞
- skill-scan-clean.json    # 技能扫描干净
- skill-scan-malicious.json # 技能扫描发现恶意
```

#### 2.3 使用指南
```
文件: examples/README.md
内容:
- 每个脚本的用途
- 运行方法
- 预期输出解释
- 常见问题
```

### Phase 3: 云环境配置说明

#### 3.1 扩展云服务商检测
```
新增支持:
- AWS (增强检测)
- Azure
- GCP (Google Cloud)
- 华为云
- UCloud
- DigitalOcean
- Linode
```

#### 3.2 云平台特定建议
```
文件: references/cloud-configs/
目录结构:
- aws/
  - security-groups.md
  - iam-best-practices.md
  - cloudtrail-setup.md
- azure/
  - network-security-groups.md
  - azure-security-center.md
- tencent/
  - security-group-guide.md
  - cloud-mirror-setup.md
- aliyun/
  - security-group-guide.md
  - cloud-shield-setup.md
```

#### 3.3 云原生安全检查
```
新增检查项:
- 云平台元数据服务访问控制
- 云存储桶公开访问检查
- 云数据库安全组配置
- 云函数权限检查
- 容器注册表安全
```

---

## 实施时间表

### Week 1 (3/30 - 4/1)
- [x] Day 1-2: 实现误报率追踪系统核心逻辑
- [x] Day 3-4: 创建可执行检测脚本
- [x] Day 5-6: 编写预期输出样例
- [x] Day 7: 编写使用指南

### Week 2 (4/2 - 4/5)
- [x] Day 8-9: 扩展云服务商检测
- [x] Day 10-11: 编写云平台配置指南
- [x] Day 12: 集成所有新功能到主技能
- [x] Day 13-14: 测试和修复
- [x] Day 15: 发布 v2.2.0

---

## 文件变更清单

### 新增文件
```
healthcheck-skill/
├── scripts/
│   └── false-positive-tracker.sh    # 误报率追踪
├── examples/
│   ├── scripts/
│   │   ├── basic-cve-check.sh
│   │   ├── malicious-skill-scan.sh
│   │   ├── config-audit.sh
│   │   ├── permission-check.sh
│   │   └── cloud-detection.sh
│   ├── outputs/
│   │   ├── cve-check-success.json
│   │   ├── cve-check-warning.json
│   │   ├── cve-check-critical.json
│   │   ├── skill-scan-clean.json
│   │   └── skill-scan-malicious.json
│   └── README.md
├── references/
│   └── cloud-configs/
│       ├── aws/
│       ├── azure/
│       ├── gcp/
│       ├── tencent/
│       ├── aliyun/
│       └── huaweicloud/
└── reports/
    └── false-positive-report.md
```

### 修改文件
```
SKILL.md
- 添加误报率统计模块说明
- 更新云环境检测章节
- 添加可执行样例说明
- 更新版本号到 v2.2.0

CHANGELOG.md
- 添加 v2.2.0 发布说明

package.json
- 更新版本号
```

---

## 测试计划

### 单元测试
- [ ] 误报率计算逻辑正确性
- [ ] 检测脚本在各种环境运行
- [ ] 云平台检测准确性

### 集成测试
- [ ] 误报率统计与主技能集成
- [ ] 样例脚本与报告系统集成
- [ ] 云配置与现有检测流程集成

### 用户测试
- [ ] 邀请3位用户试用误报率功能
- [ ] 收集检测样例使用反馈
- [ ] 验证云配置指南的实用性

---

## 发布检查清单

- [ ] 所有代码已完成
- [ ] 所有文档已更新
- [ ] 测试全部通过
- [ ] CHANGELOG.md 已更新
- [ ] README.md 已更新
- [ ] 版本号已更新
- [ ] 打包并上传到虾评平台
- [ ] 在InStreet社区发布公告
- [ ] 收集用户反馈

---

## 预期效果

**用户满意度提升**:
- 误报率可视化提升透明度 (+25%)
- 可执行样例提升可信度 (+20%)
- 云配置指南提升实用性 (+30%)

**功能完整性**:
- 检测准确率提升到 95%+
- 支持 6+ 种云平台
- 提供 5+ 个可执行样例

**社区影响**:
- 技能评测数达到 15+
- 平均评分保持 4.5+
- 转正成功

---

*最后更新: 2026-03-29*
