# Excel 凭证模板格式说明

本目录不包含预制的 Excel 文件。模板会在运行时由脚本动态生成。

## 模板生成方式

运行 `scripts/voucher_generator.py` 中的 `generate_template()` 方法生成 Excel 模板：

```python
from scripts.voucher_generator import VoucherGenerator

generator = VoucherGenerator()
# 生成金蝶模板
generator.generate_template('kingdee', 'output_kingdee.xlsx')
# 生成用友模板
generator.generate_template('yonyou', 'output_yonyou.xlsx')
# 生成 SAP 模板
generator.generate_template('sap', 'output_sap.xlsx')
# 生成 Oracle 模板
generator.generate_template('oracle', 'output_oracle.xlsx')
```

## 各财务软件模板字段

### 通用字段（所有软件）

| 字段名 | 说明 | 数据类型 |
|--------|------|----------|
| 凭证字 | 如"记"、"收"、"付"、"转" | 文本 |
| 凭证号 | 凭证序号（按月重置） | 整数 |
| 凭证日期 | 业务日期（YYYY-MM-DD） | 日期 |
| 附单据数 | 原始单据数量 | 整数 |

### 凭证分录字段

| 字段名 | 说明 | 数据类型 |
|--------|------|----------|
| 行号 | 分录序号 | 整数 |
| 摘要 | 业务描述 | 文本 |
| 科目编码 | 会计科目代码 | 文本 |
| 科目名称 | 会计科目名称 | 文本 |
| 借方金额 | 借方发生额 | 小数 |
| 贷方金额 | 贷方发生额 | 小数 |
| 币别 | 币种代码（如 RMB、USD） | 文本 |
| 汇率 | 外汇汇率 | 小数 |

### 辅助核算字段（可选）

| 字段名 | 说明 |
|--------|------|
| 辅助核算-客户编码 | 客户编码 |
| 辅助核算-客户名称 | 客户名称 |
| 辅助核算-供应商编码 | 供应商编码 |
| 辅助核算-供应商名称 | 供应商名称 |
| 辅助核算-员工编码 | 员工编码 |
| 辅助核算-员工姓名 | 员工姓名 |
| 辅助核算-项目编码 | 项目编码 |
| 辅助核算-项目名称 | 项目名称 |
| 辅助核算-部门编码 | 部门编码 |
| 辅助核算-部门名称 | 部门名称 |

## 金蝶 K/3 Cloud 格式

凭证表头字段：
- FBrNo: 账簿编码
- VchGroup: 凭证字
- VchNo: 凭证号
- Date: 凭证日期
- AccID: 科目编码
- Explanation: 摘要
- DR: 借方金额
- CR: 贷方金额
- Rate: 汇率
- ExRate: 折算汇率

## 用友 U8/U9 格式

凭证表头字段：
- 凭证字
- 凭证号
- 凭证日期
- 附单据数
- 制单人

凭证分录字段：
- 摘要
- 科目编码
- 科目名称
- 借方金额
- 贷方金额
- 数量
- 单价

## SAP 格式

使用 FBV0 事务码导入格式：
- BUKRS: 公司代码
- BLART: 凭证类型
- BLDAT: 凭证日期
- BUDAT: 过账日期
- WAERS: 货币代码
- KUNNR: 客户编码
- LIFNR: 供应商编码
- HKONT: 科目编码
- DMBTR: 本位币金额
- WRBTR: 外币金额

## Oracle Fusion 格式

使用电子表格导入：
- Ledger: 账簿名称
- Accounting Date: 会计日期
- Category: 凭证类别
- Currency: 币种
- Account: 科目编码
- Debit: 借方金额
- Credit: 贷方金额
- Description: 描述
- Reference: 参考信息

## 样式规范

生成 Excel 时应用以下样式：
- 表头行：加粗、灰色背景 (#CCCCCC)
- 数据行：白色背景
- 金额列：右对齐、保留2位小数
- 日期列：YYYY-MM-DD 格式
- 边框：细线边框

## 示例数据结构

```json
{
  "software": "kingdee",
  "header": {
    "ledger_code": "001",
    "voucher_word": "记",
    "voucher_number": 1,
    "date": "2024-01-15",
    "attachments": 2
  },
  "entries": [
    {
      "line_number": 1,
      "summary": "收到客户货款",
      "account_code": "1122",
      "account_name": "应收账款",
      "debit_amount": 10000.00,
      "credit_amount": 0,
      "currency": "RMB",
      "exchange_rate": 1.0,
      "auxiliary": {
        "customer_code": "C001",
        "customer_name": "XX公司"
      }
    },
    {
      "line_number": 2,
      "summary": "收到客户货款",
      "account_code": "1002",
      "account_name": "银行存款",
      "debit_amount": 0,
      "credit_amount": 10000.00,
      "currency": "RMB",
      "exchange_rate": 1.0,
      "auxiliary": {
        "bank_account": "基本户"
      }
    }
  ]
}
```
