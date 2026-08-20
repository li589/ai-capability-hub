---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '3acb4dd3-3ece-40b6-8374-df07251b939a'
  PropagateID: '3acb4dd3-3ece-40b6-8374-df07251b939a'
  ReservedCode1: '2a3d1154-a8af-453c-91bb-21a672588d0b'
  ReservedCode2: '2a3d1154-a8af-453c-91bb-21a672588d0b'
---

# 招标文件解析字段映射指南

## 目录

1. [PROJECT 项目基本信息](#1-project-项目基本信息)
2. [EVAL_SCORES 评标评分项](#2-eval_scores-评标评分项)
3. [STRATEGIES 评分策略建议](#3-strategies-评分策略建议)
4. [TECH_REQS 技术要求](#4-tech_reqs-技术要求)
5. [HARDWARE_REQS 硬件要求](#5-hardware_reqs-硬件要求)
6. [BIZ_REQS 商务要求](#6-biz_reqs-商务要求)
7. [DARK_MARK_RULES 暗标格式规范](#7-dark_mark_rules-暗标格式规范)
8. [RISKS 风险清单](#8-risks-风险清单)
9. [QUALIFICATIONS 资质准备清单](#9-qualifications-资质准备清单)
10. [PERSONNEL 人员配置](#10-personnel-人员配置)
11. [SOP_PHASES 投标SOP阶段](#11-sop_phases-投标sop阶段)
12. [解析要点](#12-解析要点)
13. [Word报告标准产出9张表](#13-word报告标准产出9张表)

---

## 1. PROJECT 项目基本信息

```javascript
const PROJECT = {
  name: '项目名称',
  bidNo: '招标编号（如HBGH-2025-036）',
  purchaser: '采购人/招标人名称',
  agent: '招标代理机构名称（无则空字符串）',
  budget: '项目预算金额（含单位，如"365.88万元"）',
  softwareLimit: '软件最高限价（如"184.93万元"）',
  hardwareLimit: '硬件最高限价（如"180.95万元"）',
  deadline: '投标截止时间（ISO格式：YYYY-MM-DDTHH:MM:SS，用于倒计时计算）',
  location: '项目实施地点',
  platform: '电子招投标平台名称（如"招标通电子招投标交易平台"）',
  delivery: '交付周期（如"合同签订后60日历天"）',
  validity: '投标有效期（如"90日历天"）',
  warranty: '质保期（如"三年"）',
  quality: '质量标准',
  evalMethod: '评标办法类型（如"综合评估法"）',
  jointBid: '是否允许联合体投标（如"不允许"/"允许"）',
  subcontract: '分包要求（如"不允许"/"允许"）',
  deposit: '投标保证金（金额+方式，如"承诺书方式，违约赔付7.5万元"）'
};
```

**解析要点**：在"投标人须知"和"招标公告"中查找。deadline必须能被 `new Date()` 解析。

---

## 2. EVAL_SCORES 评标评分项

```javascript
const EVAL_SCORES = [
  { category: "商务部分(明标)", item: "评分项名称", score: 15, detail: "评分细则描述", target: "12-15", strategy: "一句话策略" },
  // ...每项一个对象
];
```

**字段说明**：
- `category`：分类，固定三个值 `"商务部分(明标)"` / `"项目实施方案(暗标)"` / `"投标报价"`
- `item`：评分项名称
- `score`：该项满分（整数）
- `detail`：评分细则原文或精简描述
- `target`：建议目标得分范围（如"12-15"）或单值（如"6"）
- `strategy`：一句话策略建议

**解析要点**：在"评标办法"章节逐项提取。暗标部分通常占比最高（60-70分）。

---

## 3. STRATEGIES 评分策略建议

```javascript
const STRATEGIES = [
  {
    item: "与EVAL_SCORES中的item对应",
    tips: [
      "策略建议1",
      "策略建议2",
      // ...每条具体可执行的建议
    ]
  }
];
```

**生成规则**：根据评标细则逐项分析，生成5-6条具体可执行建议。暗标高分项（如技术方案15分）需更多建议。

---

## 4. TECH_REQS 技术要求

```javascript
const TECH_REQS = [
  { module: "功能模块名", item: "功能项名称", detail: "需求描述", importance: "核心" }
];
```

**字段说明**：
- `module`：所属功能模块
- `item`：具体功能项
- `detail`：需求详情描述
- `importance`：`"核心"` 或 `"一般"`

**解析要点**：在"采购需求"或"技术规范"章节提取。按模块归类。

---

## 5. HARDWARE_REQS 硬件要求

```javascript
const HARDWARE_REQS = [
  { name: "设备名称", qty: "数量", params: "主要参数" }
];
```

---

## 6. BIZ_REQS 商务要求

```javascript
const BIZ_REQS = [
  { name: "条款名称", value: "条款内容" }
];
```

**必须提取的条款**：交付周期、验收标准、质保期、付款方式、培训要求、售后服务、保证金、递交方式、电子招投标要求、联合体投标、分包要求。

---

## 7. DARK_MARK_RULES 暗标格式规范

```javascript
const DARK_MARK_RULES = [
  { item: "检查项名称", rule: "具体格式要求", consequence: "违规后果（默认"否决投标"）" }
];
```

**解析要点**：暗标规范是废标红线，每条都是否决条件。通常包含：纸张/A4、字体/宋体四号、颜色/黑色、对齐/左对齐、行距/30磅、无目录、无页眉页脚、无身份信息等。

---

## 8. RISKS 风险清单

```javascript
const RISKS = [
  { type: "废标风险/评分风险/合规风险/流程陷阱", desc: "风险描述", level: "高/中/低", suggestion: "应对建议" }
];
```

---

## 9. QUALIFICATIONS 资质准备清单

```javascript
const QUALIFICATIONS = [
  { name: "资质材料名称", necessity: "必须/建议", deadline: "建议完成日期（如07-08）" }
];
```

**典型资质项**：营业执照副本、资质证书、业绩证明、财务审计报告、社保证明、税收证明、信用记录、投标保证金承诺书、不参与涉黑涉恶承诺书、授权委托书、法定代表人身份证明、人员证书、大模型备案/RAG认证等。

---

## 10. PERSONNEL 人员配置

```javascript
const PERSONNEL = [
  { role: "岗位名称", requirements: "资质要求描述", certs: "需准备的证书", score: "该项满分" }
];
```

---

## 11. SOP_PHASES 投标SOP阶段

```javascript
const SOP_PHASES = [
  {
    name: "阶段名称",
    period: "时间范围（如Day 1-2（07-02 ~ 07-03））",
    color: "phase-1", // phase-1~5 对应不同颜色
    tasks: [
      { id: "1.1", name: "任务名称", detail: "详细说明", responsible: "负责人/角色", deadline: "截止日期（如07-02）", necessity: "必须/建议", priority: "高/中/低" }
    ]
  }
];
```

**5个标准阶段**：

| 阶段 | 名称 | 时间 | color | 典型任务数 |
|:---|:---|:---|:---|:---|
| 1 | 投标启动与研读 | Day1-2 | phase-1 | 6-8项 |
| 2 | 商务资信准备 | Day3-7 | phase-2 | 8-12项 |
| 3 | 技术方案编写 | Day3-10 | phase-3 | 8-12项 |
| 4 | 商务文件编制与报价 | Day8-12 | phase-4 | 6-10项 |
| 5 | 审核校验与封装上传 | Day13-14 | phase-5 | 6-10项 |

**生成规则**：根据开标日期倒推。阶段3与阶段2可并行。deadline必须为可解析的日期格式。

---

## 12. 解析要点

### PDF提取
- 优先用pdfplumber，扫描件用PaddleOCR
- 注意AIGC水印（"AI生成"等）可能干扰文本，需识别并过滤
- 表格数据提取后需验证列对齐

### 关键章节定位
1. **招标公告**：项目编号、预算、截止时间、平台
2. **投标人须知**：投标有效期、保证金、联合体、分包
3. **评标办法**：评分构成、评分细则、价格分计算公式
4. **采购需求/技术规范**：技术要求、硬件参数
5. **合同条款**：付款方式、质保期、验收标准
6. **附件**：投标函格式、报价表格式、人员简历表格式

### 暗标检测
- 招标文件中出现"暗标""匿名""不得出现身份信息"等表述
- 暗标评分项通常单独列出，与明标分开评审
- 暗标格式要求通常是硬性约束，违反即废标

### 评标办法分析
- 综合评估法：商务+技术+报价，各部分有明确权重
- 最低评标价法：满足技术条件后按报价排序
- 识别评分基准价计算方式（算术平均/去掉最高最低）

---

## 13. Word报告标准产出9张表

| 序号 | 表格 | 内容 |
|:---|:---|:---|
| 1 | 控标项/修订项/问题项清单 | 从招标文件中识别的强制性要求、需澄清项、存疑项 |
| 2 | 澄清申请清单 | 需要向招标人提出澄清的问题列表 |
| 3 | 商务要求一览表 | 所有商务条款的结构化列表 |
| 4 | 技术要求一览表 | 技术参数+功能的结构化列表 |
| 5 | 评分细则表 | 评分项+分值+评分标准的详细表 |
| 6 | 附件要求一览表 | 需要准备的文件/证书/证明清单 |
| 7 | 资质材料清单 | 每项资质+必要性+负责人+截止日 |
| 8 | 投资估算与收益表 | 软硬件预算分解+人员成本估算 |
| 9 | 格式底稿 | 投标函、授权书等需按格式填写的底稿 |

> AI生成