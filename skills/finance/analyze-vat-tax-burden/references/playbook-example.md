# Playbook 案例

## 场景

一般纳税人希望分析 2026 年 1—2 月增值税税负为什么上升。用户提供两个月的不含税销售额、销项、进项、留抵、一般计税应纳税额和申报应纳税额。

## 示例输入

```json
{
  "entity": "示例制造企业",
  "unit": "yuan",
  "periods": [
    {
      "period": "2026-01",
      "taxpayer_type": "general",
      "sales_general": "1000000",
      "output_tax": "130000",
      "input_tax_credit": "100000",
      "input_tax_transfer_out": "0",
      "opening_credit_balance": "0",
      "closing_credit_balance": "0",
      "tax_general": "30000",
      "sales_simple": "0",
      "tax_simple": "0",
      "tax_reduction": "0",
      "additional_credit": "0",
      "vat_payable": "30000",
      "vat_paid": "30000"
    },
    {
      "period": "2026-02",
      "taxpayer_type": "general",
      "sales_general": "1100000",
      "output_tax": "143000",
      "input_tax_credit": "85000",
      "input_tax_transfer_out": "0",
      "opening_credit_balance": "0",
      "closing_credit_balance": "0",
      "tax_general": "58000",
      "sales_simple": "0",
      "tax_simple": "0",
      "tax_reduction": "0",
      "additional_credit": "0",
      "vat_payable": "58000",
      "vat_paid": "58000"
    }
  ]
}
```

## 预期分析

- 1 月综合申报税负率为 `3.00%`，2 月为 `5.27%`，上升 `2.27` 个百分点。
- 销售额增长 10%，销项税额增长 10%，但进项抵扣额下降 15%，应纳税额增加 28,000 元。
- 数据显示进项抵扣变化是重要数值因素，但不能仅据此认定原因。应核查采购规模、发票取得和勾选确认时点、不可抵扣项目及是否存在跨期抵扣。
- 若销项、进项、应纳税额勾稽一致，可将结论状态标记为“波动需要解释”；不得写成税务违法风险结论。
