# 输入数据模型

## 使用规则

- 一个输入文件只表示一个纳税主体；多个主体必须拆分。
- 金额单位由顶层 `unit` 指定，允许 `yuan` 或 `ten_thousand_yuan`。同一文件不得混用单位。
- 所有销售额均为不含税金额。含税金额应在税率明确后于输入前换算。
- 未知字段省略或设为 `null`；只有确认为无该事项时才填 `0`。
- 税额和销售额通常使用非负数。红字、冲销或更正造成负数时，在 `notes` 说明原因。

## JSON 结构

```json
{
  "entity": "示例企业",
  "unit": "yuan",
  "comparison": "previous_period",
  "periods": [
    {
      "period": "2026-01",
      "taxpayer_type": "general",
      "sales_general": "1000000",
      "output_tax": "130000",
      "input_tax_credit": "80000",
      "input_tax_transfer_out": "0",
      "opening_credit_balance": "10000",
      "closing_credit_balance": "0",
      "tax_general": "40000",
      "sales_simple": "100000",
      "tax_simple": "3000",
      "exempt_sales": "0",
      "tax_reduction": "0",
      "additional_credit": "0",
      "prepaid_tax": "0",
      "vat_payable": "43000",
      "vat_paid": "43000",
      "retained_tax_refund": "0",
      "notes": ""
    }
  ]
}
```

金额建议以字符串传入，避免二进制浮点误差。脚本也接受 JSON 数字。

## 字段定义

| 字段 | 含义 | 必需性 |
|---|---|---|
| `entity` | 纳税主体名称或匿名标识 | 必填 |
| `unit` | `yuan` 或 `ten_thousand_yuan` | 必填 |
| `periods` | 按时间升序排列的期间数组 | 必填，至少 1 项 |
| `period` | `YYYY-MM`、`YYYY-Qn` 或 `YYYY` | 必填且不可重复 |
| `taxpayer_type` | `general` 或 `small_scale` | 必填 |
| `sales_general` | 一般计税不含税销售额 | 按事项填写 |
| `output_tax` | 销项税额 | 一般计税分析填写 |
| `input_tax_credit` | 本期纳入计算的可抵扣进项税额 | 一般计税分析填写 |
| `input_tax_transfer_out` | 本期进项税额转出 | 无则填 0 |
| `opening_credit_balance` | 期初留抵税额 | 留抵分析填写 |
| `closing_credit_balance` | 期末留抵税额 | 留抵分析填写 |
| `tax_general` | 一般计税应纳税额 | 申报口径分析建议填写 |
| `sales_simple` | 简易计税不含税销售额 | 有简易计税时填写 |
| `tax_simple` | 简易计税应纳税额 | 有简易计税时填写 |
| `exempt_sales` | 免税销售额 | 有免税业务时填写 |
| `tax_reduction` | 税额减免 | 有则填写 |
| `additional_credit` | 加计抵减实际抵减额 | 有则填写 |
| `prepaid_tax` | 已预缴税额 | 有则填写，默认不直接冲减税负分子 |
| `vat_payable` | 申报应纳增值税额 | 综合申报税负的分子 |
| `vat_paid` | 当期实际缴纳增值税 | 计算实缴税负时填写 |
| `retained_tax_refund` | 本期收到的留抵退税 | 有则填写，单列披露 |
| `notes` | 业务变化、冲销、重分类等说明 | 异常值时填写 |

## 最低信息判断

- 只有 `vat_payable` 与至少一类应税销售额：可计算综合申报税负，不能完成组成勾稽。
- 具有销项、进项、留抵和一般计税应纳税额：可执行一般计税勾稽。
- 具有至少两个同口径期间：可执行期间比较。
- 缺少销售额或销售额为零：不得计算税负率，只报告金额和数据状态。
