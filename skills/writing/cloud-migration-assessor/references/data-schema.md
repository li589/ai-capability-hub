# 数据 Schema 参考

## 评估数据 JSON 格式

用于脚本输入和项目保存/加载的标准 JSON 格式：

```json
{
  "version": "4.1.0",
  "exportDate": "2026-04-01T12:00:00.000Z",
  "projectInfo": {
    "name": "项目名称",
    "client": "客户/单位名称",
    "code": "项目编号（可选）",
    "assessor": "评估人",
    "sourceType": "idc|private-cloud|other-cloud|hybrid",
    "sourceLocation": "源端位置描述",
    "targetCloud": "tencent|aliyun|huawei|aws|azure|gcp|other",
    "targetRegion": "目标区域"
  },
  "businessSystems": [
    {
      "name": "业务系统名称",
      "priority": "核心|重要|一般",
      "services": 8,
      "databases": 2
    }
  ],
  "resources": [
    {
      "id": 1,
      "category": "云服务器|云数据库|缓存|搜索服务|文档数据库|消息队列|容器产品|网络产品|安全产品|安全服务|CDN/存储|大数据|中间件|其他",
      "name": "资源名称",
      "spec": "规格描述",
      "qty": 10,
      "complexity": "low|medium|high",
      "usage": "用途说明"
    }
  ],
  "config": {
    "teamSize": 5,
    "hoursPerDay": 8,
    "aiBoost": 50,
    "parallel": 0.7,
    "riskBuffer": 15,
    "costPerDay": 1500
  }
}
```

---

## Excel 导入格式

支持的 Excel 列名及映射关系：

| 列名关键词 | 映射字段 | 说明 |
|-----------|----------|------|
| 类型, 类别, 资源类型, category | category | 资源分类 |
| 名称, 资源名, 资源名称, name | name | 资源名称 |
| 规格, 配置, 型号, spec | spec | 规格描述 |
| 数量, 数目, qty, count, 台数 | qty | 实例数量 |
| 用途, 说明, 备注, usage, description | usage | 用途说明 |
| 复杂度, complexity | complexity | low/medium/high |

### Excel 列名匹配规则
1. 忽略大小写
2. 去除首尾空格
3. 支持部分匹配（如列名包含"名称"即匹配为 name）
4. 第一行为表头，从第二行开始读取数据
5. 空行自动跳过

---

## 文字描述解析规则

用户可能用以下方式描述资源清单：

### 格式示例
```
有10台CVM（8C16G），3个MySQL主从（16C64G 1T），2套Redis集群（16G），
1个K8s集群（20节点），5台负载均衡，1个对象存储（2T）
```

### 解析策略
1. 识别数量词：数字 + 量词（台/个/套/组/节点/条）
2. 识别资源类型：匹配 resource-models.md 中的关键词
3. 提取规格：括号内容作为 spec
4. 无法识别的部分归入"其他"类型

---

## 输出报告数据结构

计算引擎输出的结果结构（用于报告生成）：

```json
{
  "resourceBreakdown": [
    {
      "category": "云数据库",
      "name": "MySQL主从集群",
      "qty": 3,
      "complexity": "high",
      "complexityLabel": "高",
      "complexityFactor": 1.5,
      "qtyEffectiveFactor": 2.4,
      "phaseBreakdown": {
        "planning": { "rawDays": 1.08, "aiDays": 1.00 },
        "infra": { "rawDays": 0.36, "aiDays": 0.33 },
        "provision": { "rawDays": 1.44, "aiDays": 1.30 },
        "migration": { "rawDays": 4.32, "aiDays": 4.10 },
        "deploy": { "rawDays": 1.80, "aiDays": 1.69 },
        "testing": { "rawDays": 1.80, "aiDays": 1.67 }
      },
      "totalRawDays": 10.8,
      "totalAiDays": 10.1
    }
  ],
  "phaseWorkload": [
    {
      "id": "planning",
      "name": "规划设计及方案确认",
      "resourceRaw": 5.0,
      "resourceAi": 4.2,
      "overheadRaw": 9.0,
      "overheadAi": 7.5,
      "rawTotal": 14.0,
      "aiTotal": 11.7
    }
  ],
  "rawTotal": 120.5,
  "aiTotal": 95.3,
  "buffered": 109.6,
  "calendarDays": 32,
  "aiSaveDays": 25.2,
  "aiSavePct": 21,
  "aiCostSave": 37800,
  "totalResources": 38,
  "teamSize": 5
}
```
