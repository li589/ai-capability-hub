# 钟馗漏洞系统自进化 — 威胁情报管线

> 目标：将钟馗从"硬编码签名库"升级为"威胁情报驱动的自适应审查引擎"

## 整体架构

```
威胁情报摄入 -> 签名生成 -> 检查项扩展 -> 权重校准 -> 回归验证 -> 发布
```

## 1. 威胁情报摄入

### 1.1 自动化摄入源（仅保留 CVSS 客观评分的源）

筛选标准：情报项携带可量化的置信度/严重度指标（CVSS score），可直接映射到签名 `confidence` 字段。

#### 1.1.1 NVD（NIST 国家漏洞数据库）— CVSS v3.1

| 项目 | 端点 / 参数 | 置信度 |
|------|------------|--------|
| REST API 基地址 | `https://services.nvd.nist.gov/rest/json/cves/2.0` | — |
| 关键词搜索 | `?keywordSearch=prompt+injection&resultsPerPage=20` | CVSS v3.1 baseScore (0-10) |
| 精确匹配 | `?keywordSearch=LLM+agent+security&keywordExactMatch` | — |
| 严重度过滤 | `?cvssV3Severity=CRITICAL&keywordSearch=AI+agent` | CRITICAL/HIGH/MEDIUM/LOW |
| 日期范围 | `?pubStartDate=YYYY-MM-DDT00:00:00.000&pubEndDate=YYYY-MM-DDT23:59:59.999` (<=120天) | — |

LLM/Agent 相关 CWE 映射表：

| CWE | 名称 | 对应钟馗风险 |
|-----|------|-------------|
| CWE-94 | Code Injection | R1, R11 |
| CWE-74 | Improper Neutralization | R1/R11 |
| CWE-20 | Improper Input Validation | R1 |
| CWE-427 | Uncontrolled Search Path | R4 |
| CWE-494 | Download Without Integrity Check | R4 |
| CWE-918 | SSRF | R10 |
| CWE-200 | Exposure of Sensitive Info | R2 |
| CWE-668 | Exposure to Wrong Sphere | R7 |

#### 1.1.2 Snyk 漏洞数据库 — CVSS v3.1

| 项目 | 端点 | 置信度 |
|------|------|--------|
| Snyk V1 API | `GET https://api.snyk.io/v1/vulns`（需 Enterprise Token） | CVSS v3.1 score |

#### 1.1.3 Seebug 漏洞库

| 项目 | 端点 | 置信度 |
|------|------|--------|
| Seebug RSS | `https://www.seebug.org/rss/new` | severity 高/中/低 |

#### 1.1.4 跨源 Confidence 归一化

| 源 | 原始评分 | 归一化到 [0,1] |
|----|---------|---------------|
| NVD | CVSS v3.1 baseScore (0-10, 粒度 0.1) | `score / 10` |
| Snyk | CVSS v3.1 score (0-10, 粒度 0.1) | `score / 10` |
| Seebug | severity 高/中/低（3 级离散） | 高->0.8, 中->0.5, 低->0.2 |

Seebug 离散映射值收紧至 {0.8, 0.5, 0.2}，避免三档离散值过度挤压 NVD/Snyk 连续值区分空间。后续评分器可对 `source_type` 引入衰减因子（非 CVSS 源 *0.85）。

#### 1.1.5 摄入频率总表

| 源 | 频率 | 窗口 | 每次量 | 置信度类型 | 归一化 |
|----|------|------|--------|-----------|--------|
| NVD REST API | 每日 | 过去 7 天 | CRITICAL/HIGH CVE | CVSS v3.1 | score/10 -> [0,1] |
| Snyk V1 API | 每日 | 过去 1 天（增量） | 新增漏洞 | CVSS v3.1 | score/10 -> [0,1] |
| Seebug RSS | 每日 | 过去 1 天（增量） | 新条目 | severity 高/中/低 | {0.8, 0.5, 0.2} -> [0,1] |

#### 1.1.6 覆盖盲区与补救

CVSS 主要覆盖传统软件漏洞（CWE），以下 R3/R5/R6/R8/R9/R12 在三个自动化源中覆盖率接近零。补救路径：走"论文->模式提取"半自动链路——利用 HuggingFace/ArXiv/GitHub 作为人工情报源，分析员阅读最新攻击论文后手动将攻击模式编码为签名碎片注入 `patterns.json`。标记 `source_type: "manual"` 以区别于自动摄入，confidence 由分析员主观评定（0.5-0.9）。

#### 1.1.7 排除源清单

| 源 | 排除原因 |
|----|---------|
| OWASP LLM Top 10 | 分类列表，无 per-item 评分 |
| ArXiv/HuggingFace Papers | 论文无客观安全置信度 |
| GitHub Repos（garak/promptfoo 等） | Stars 是社区热度，非安全置信度 |
| AWS/Azure/GCP 安全公告 | 无严重度评分 |
| 腾讯科恩/玄武/CSA/奇安信 | 博客/报告级别无 per-item 置信度 |

## 2. 签名生成

### 2.1 流程

```
原始报告 -> LLM 提取攻击模式 -> 碎片化编码 -> 写入 patterns.json
```

1. **攻击模式提取**：报告正文喂入 LLM，输出结构化描述：攻击向量关键词、攻击目标层级（SKILL.md/scripts/deps）、对应风险类型（R1-R12）、置信度（0-1）
2. **碎片化编码**：关键词拆解为 pieces 格式，确保关键词本身不被安全引擎误判：
   ```json
   {"id": "CXX_NNN", "pieces": ["frag", "ment1"], "source": "OWASP-LLM-2026-03", "confidence": 0.85, "added": "2026-06-13"}
   ```
3. **去重与归并**：语义相似度比对（embedding cosine > 0.9 归并），仅追加新碎片

### 2.2 质量门禁

| 门禁 | 规则 | 阻断条件 |
|------|------|----------|
| 碎片格式校验 | JSON schema 严格匹配 | 格式不符 -> 丢弃 |
| 自匹配测试 | 碎片串接后对钟馗自身 SKILL.md 做匹配 | 误报 -> 标记 false_positive |
| 回归测试 | 对已知干净 Skill 跑全量审查 | 新增误报 > 0 -> 阻断 |

## 3. 检查项扩展

触发条件：威胁情报识别出当前 54 项未覆盖的攻击面（新风险类别/已知类别新攻击向量/新文件类型）。

扩展流程：人工审核确认 -> 定义检查项编号/检测逻辑 -> 实现 `_check_*()` 代码 -> 更新 `static-audit.md` -> `checks_total` 自动 +1。

## 4. 权重校准

### 4.1 数据来源
- 误报反馈 / 漏报反馈 / 基准测试（干净 *50 + 恶意 *50 标注数据集）

### 4.2 校准公式

使用加权 Fβ 分数驱动权重调整。默认 beta=2（漏报权重为误报的 4 倍）：

| beta | 漏报:误报权重比 | 适用场景 |
|------|-----------------|----------|
| 0.5 | 1:4 | 误报成本极高（阻断型系统） |
| 1.0 | 1:1 | 漏报与误报等成本 |
| 2.0 | 4:1 | 漏报成本显著高于误报（安全审查场景，默认） |
| 3.0 | 9:1 | 漏报不可接受（入侵检测） |

```
F2 = (1+2^2) * precision * recall / (2^2 * precision + recall)
```

每季度基于反馈数据跑网格搜索，在权重空间中找到 F2 最优解。

## 5. 回归验证

每次签名/权重更新后自动执行：
1. 干净 Skill 集（>=10 个已知安全 Skill）— 确保无误报引入
2. 恶意 Skill 集（>=10 个已知恶意 Skill）— 确保检出率不下降
3. 对照 Skill 集（>=5 个边界案例）— 确保裁定不漂移

目标扩展至干净集 >=50、恶意集 >=50、对照集 >=20，F2-score 95% 置信区间收窄至 +/-0.05。

## 6. 发布策略

| 模式 | 触发条件 | 动作 |
|------|----------|------|
| 静默更新 | 仅新增碎片，回归全绿 | 自动合并到 patterns.json |
| 审查更新 | 新增检查项/修改权重 | 生成 PR，人工 Review 后合并 |
| 阻断 | 回归失败/门禁未通过 | 回滚，生成失败报告 |

## 7. 当前状态与待办

| 环节 | 状态 | 备注 |
|------|------|------|
| 威胁情报摄入 | ✅ 已实现 `core/intel/updater.py` | NVD + Seebug 双源，三层过滤，碎片化，去重注入 |
| 签名生成 | ✅ 已实现 `generate_patterns()` | 滑动窗口短语提取 + 碎片化编码，每 CVE 最多 1 条 |
| 检查项扩展 | 人工 | 按需（由情报触发） |
| 权重校准 | 未实现 | 缺乏 >=200 条反馈数据 |
| 回归验证 | 未实现 | 缺乏标准测试集 |
| 发布策略 | ✅ 已实现 `zhongkui.py --update` | 交互确认后注入，自动备份 |

### 7.1 更新标准与准入规范

| 维度 | 标准 |
|------|------|
| **更新频率** | 无硬性周期，按需执行 `--update` |
| **摄入源** | NVD API（CVSS v3.1 CRITICAL/HIGH，7 天窗口）+ Seebug RSS |
| **关键词过滤** | CVE 描述命中 `INTAKE_KEYWORDS`（26 词），排除 `EXCLUDE_KEYWORDS`（17 词） |
| **安全精确过滤** | 候选 CVE 必须命中 `AGENT_SAFETY_KEYWORDS`（21 项 Agent/Skill 特有安全术语） |
| **文本剥离** | 跳过产品介绍句，剥离 "Prior to version X, " 前缀，跳过纯修复/版本/致谢句 |
| **CWE 路由** | 9 个 CWE->钟馗分区映射（CWE-94->C1_injection，CWE-918->S2_network 等） |
| **去重** | `label` 唯一性：跨基础库 + 当前增量去重 |
| **碎片化** | 单片段 <=6 字符；词间 `[\\s\\S]{0,20}?` 弹性分隔 |
| **置信度** | CVSS/10 归一化到 0-1；Seebug {高->0.8, 中->0.5, 低->0.2} |
| **基础库保护** | `source: "manual"` 签名永不触碰，`--update` 仅替换 auto 增量 |
| **幂等性** | 每次 `--update` 先清旧增量再注入最新 |
| **回滚** | 注入前自动备份 `patterns.json.bak` |

## 8. 最小可行启动方案

1. **情报摄入**（已自动化）：`python zhongkui.py --update` 从 NVD + Seebug 自动拉取、过滤、生成碎片化签名。盲区类别（见 1.1.6）仍须人工覆盖。
2. **签名注入**（已自动化）：`update_patterns_json()` 按 CWE 分区路由注入，自动去重、备份、版本号递增。
3. **自审回归**（人工）：每次更新后跑 `python zhongkui.py . --quick` 确认无自审崩溃。
