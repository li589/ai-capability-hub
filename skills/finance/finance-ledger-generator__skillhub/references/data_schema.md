# 财务凭证生成器 - 数据结构参考

## 数据存储目录结构

```
~/.workbuddy/skills/finance-ledger-generator/data/
├── ledger_books.json       # 账簿清单
├── account_codes.json       # 科目档案
├── accounting_rules.json    # 核算规则
├── customers.json          # 客户清单
├── suppliers.json          # 供应商清单
├── employees.json          # 员工清单
├── exchange_rates.json      # 汇率表
├── auxiliary_data.json       # 其他辅助资料
└── meta.json               # 元数据
```

## 数据模型定义

### 1. 账簿清单 (ledger_books.json)

```json
[
  {
    "code": "001",
    "name": "主账簿",
    "start_date": "2024-01-01",
    "currency": "人民币",
    "status": "active",
    "description": "公司主账簿",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 账簿编码，唯一标识 |
| name | string | 是 | 账簿名称 |
| start_date | string | 是 | 账簿启用日期 (YYYY-MM-DD) |
| currency | string | 否 | 币别，默认"人民币" |
| status | string | 否 | 状态：active/inactive |
| description | string | 否 | 描述说明 |
| created_at | string | 否 | 创建时间 (ISO格式) |

### 2. 科目档案 (account_codes.json)

```json
[
  {
    "code": "1001",
    "name": "库存现金",
    "category": "资产",
    "is_auxiliary": false,
    "auxiliary_types": [],
    "direction": "借",
    "parent_code": "1000",
    "level": 1,
    "is_detail": true,
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "code": "1122",
    "name": "应收账款",
    "category": "资产",
    "is_auxiliary": true,
    "auxiliary_types": ["customer"],
    "direction": "借",
    "parent_code": "1120",
    "level": 2,
    "is_detail": true,
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 科目编码，支持多级（如1001、100101） |
| name | string | 是 | 科目名称 |
| category | string | 否 | 科目类别：资产/负债/权益/成本/损益 |
| is_auxiliary | boolean | 否 | 是否启用辅助核算，默认false |
| auxiliary_types | array | 否 | 辅助核算类型列表：customer/supplier/employee/project/department |
| direction | string | 否 | 余额方向：借/贷 |
| parent_code | string | 否 | 上级科目编码 |
| level | integer | 否 | 科目级次（1-6级） |
| is_detail | boolean | 否 | 是否明细科目 |
| status | string | 否 | 状态：active/inactive |

### 3. 核算规则 (accounting_rules.json)

```json
{
  "version": "1.0",
  "updated_at": "2024-01-01T00:00:00",
  "rules": [
    {
      "rule_id": "bank_in_1002_debit",
      "business_type": "银行收款",
      "source_field": "收款金额",
      "target_account_code": "1002",
      "target_account_name": "银行存款",
      "entry_type": "debit",
      "mapping_logic": "",
      "priority": 100,
      "confidence": 0.95,
      "is_auto_learned": false,
      "is_user_defined": true,
      "status": "active",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rule_id | string | 是 | 规则唯一标识 |
| business_type | string | 是 | 业务类型 |
| source_field | string | 是 | 源文件字段名 |
| target_account_code | string | 是 | 目标科目编码 |
| target_account_name | string | 否 | 目标科目名称 |
| entry_type | string | 是 | 分录类型：debit/credit |
| mapping_logic | string | 否 | 映射逻辑表达式 |
| priority | integer | 否 | 优先级（数字越小优先级越高） |
| confidence | float | 否 | 置信度（0-1，仅自动学习的规则） |
| is_auto_learned | boolean | 否 | 是否自动学习 |
| is_user_defined | boolean | 否 | 是否用户自定义 |
| status | string | 否 | 状态：active/inactive |

### 4. 客户清单 (customers.json)

```json
[
  {
    "code": "C001",
    "name": "测试客户有限公司",
    "short_name": "测试客户",
    "tax_id": "91110000XXXXXXXX",
    "bank_account": "1234567890123456",
    "bank_name": "中国工商银行北京分行",
    "contact": "张三",
    "phone": "010-12345678",
    "address": "北京市朝阳区XX路XX号",
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 客户编码，唯一标识 |
| name | string | 是 | 客户全称 |
| short_name | string | 否 | 客户简称 |
| tax_id | string | 否 | 纳税人识别号 |
| bank_account | string | 否 | 银行账号 |
| bank_name | string | 否 | 开户行名称 |
| contact | string | 否 | 联系人 |
| phone | string | 否 | 联系电话 |
| address | string | 否 | 地址 |
| status | string | 否 | 状态：active/inactive |

### 5. 供应商清单 (suppliers.json)

```json
[
  {
    "code": "S001",
    "name": "测试供应商有限公司",
    "short_name": "测试供应商",
    "tax_id": "91110000XXXXXXXX",
    "bank_account": "2345678901234567",
    "bank_name": "中国建设银行上海分行",
    "contact": "李四",
    "phone": "021-87654321",
    "address": "上海市浦东新区XX路XX号",
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 供应商编码，唯一标识 |
| name | string | 是 | 供应商全称 |
| short_name | string | 否 | 供应商简称 |
| tax_id | string | 否 | 纳税人识别号 |
| bank_account | string | 否 | 银行账号 |
| bank_name | string | 否 | 开户行名称 |
| contact | string | 否 | 联系人 |
| phone | string | 否 | 联系电话 |
| address | string | 否 | 地址 |
| status | string | 否 | 状态：active/inactive |

### 6. 员工清单 (employees.json)

```json
[
  {
    "code": "E001",
    "name": "王五",
    "department": "销售部",
    "position": "销售经理",
    "email": "wangwu@example.com",
    "phone": "13800138001",
    "id_card": "110101199001011234",
    "bank_account": "3456789012345678",
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 员工编码，唯一标识 |
| name | string | 是 | 员工姓名 |
| department | string | 否 | 所属部门 |
| position | string | 否 | 职位 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 电话 |
| id_card | string | 否 | 身份证号 |
| bank_account | string | 否 | 工资卡号 |
| status | string | 否 | 状态：active/inactive |

### 7. 汇率表 (exchange_rates.json)

```json
[
  {
    "currency_code": "USD",
    "currency_name": "美元",
    "rate_to_cny": 7.25,
    "effective_date": "2024-01-01",
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "currency_code": "EUR",
    "currency_name": "欧元",
    "rate_to_cny": 7.85,
    "effective_date": "2024-01-01",
    "status": "active",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| currency_code | string | 是 | 币种代码（ISO标准） |
| currency_name | string | 是 | 币种名称 |
| rate_to_cny | float | 是 | 兑人民币汇率 |
| effective_date | string | 是 | 生效日期 (YYYY-MM-DD) |
| status | string | 否 | 状态：active/inactive |

### 8. 辅助资料 (auxiliary_data.json)

```json
{
  "projects": [
    {
      "code": "P001",
      "name": "研发项目A",
      "category": "研发",
      "parent_code": "",
      "description": "新产品研发项目",
      "status": "active",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "departments": [
    {
      "code": "D001",
      "name": "销售部",
      "category": "业务部门",
      "parent_code": "",
      "description": "",
      "status": "active",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "contracts": [
    {
      "code": "CT001",
      "name": "采购合同-2024-001",
      "category": "采购",
      "parent_code": "",
      "description": "",
      "status": "active",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 编码，唯一标识 |
| name | string | 是 | 名称 |
| category | string | 否 | 类别 |
| parent_code | string | 否 | 上级编码 |
| description | string | 否 | 描述 |
| status | string | 否 | 状态：active/inactive |

## 支持的辅助核算类型

| 类型标识 | 说明 | 对应数据表 |
|----------|------|-----------|
| customer | 客户核算 | customers.json |
| supplier | 供应商核算 | suppliers.json |
| employee | 员工核算 | employees.json |
| project | 项目核算 | auxiliary_data.projects |
| department | 部门核算 | auxiliary_data.departments |
| contract | 合同核算 | auxiliary_data.contracts |

## 业务类型参考

| 业务类型 | 关键词 | 说明 |
|----------|--------|------|
| 银行收款 | 收款、收入、到账、回款 | 通过银行收到的款项 |
| 银行付款 | 付款、支出、汇出、支付 | 通过银行支付的款项 |
| 现金收款 | 现金收入、收现 | 以现金方式收到的款项 |
| 现金付款 | 现金支出、付现 | 以现金方式支付的款项 |
| 应收账款 | 应收、赊销、销售 | 客户欠款 |
| 应付账款 | 应付、赊购、采购 | 欠供应商款项 |
| 工资薪酬 | 工资、薪酬、奖金、补贴 | 员工工资相关 |
| 税费缴纳 | 税金、税费、纳税 | 各类税费 |
| 费用报销 | 报销、费用、开支 | 费用报销 |
| 资产购置 | 购入、购置、购买 | 购买资产 |
| 资产折旧 | 折旧、摊销、计提 | 资产折旧摊销 |
| 利息收支 | 利息、手续费 | 利息和手续费 |

## 常用科目编码参考

| 编码 | 名称 | 类别 |
|------|------|------|
| 1001 | 库存现金 | 资产 |
| 1002 | 银行存款 | 资产 |
| 1012 | 其他货币资金 | 资产 |
| 1122 | 应收账款 | 资产 |
| 1123 | 预付账款 | 资产 |
| 1221 | 其他应收款 | 资产 |
| 1405 | 库存商品 | 资产 |
| 1601 | 固定资产 | 资产 |
| 1602 | 累计折旧 | 资产（减） |
| 1701 | 无形资产 | 资产 |
| 2202 | 应付账款 | 负债 |
| 2211 | 应付职工薪酬 | 负债 |
| 2221 | 应交税费 | 负债 |
| 4001 | 实收资本 | 权益 |
| 5001 | 生产成本 | 成本 |
| 6001 | 主营业务收入 | 损益 |
| 6401 | 主营业务成本 | 损益 |
| 6601 | 销售费用 | 损益 |
| 6602 | 管理费用 | 损益 |
| 6603 | 财务费用 | 损益 |
