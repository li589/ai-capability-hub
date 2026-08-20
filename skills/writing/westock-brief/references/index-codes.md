# 指数代码速查

## A股

| 指数 | 代码 | 说明 |
|------|------|------|
| 上证指数 | sh000001 | 沪市大盘 |
| 深证成指 | sz399001 | 深市大盘 |
| 沪深300 | sh000300 | 蓝筹代表 |
| 创业板指 | sz399006 | 成长代表 |
| 科创50 | sh000688 | 科创代表 |

## 港股

| 指数 | 代码 | 说明 |
|------|------|------|
| 恒生指数 | hkHSI | 港股大盘 |
| 恒生科技 | hkHSTECH | 科技板块 |

## 美股（查不到代码时用 `westock search <名称> --type index` 查询）

| 指数 | 代码 / 查询方式 | 说明 |
|------|------|------|
| S&P 500 | usINX | 美股大盘 |
| Nasdaq Composite | usIXIC | 科技主导 |
| Dow Jones | usDJI | 工业蓝筹 |

## 外汇与大宗商品（盘前全球市场速览按需）

| 品种 | 代码 / 查询方式 | 说明 |
|------|------|------|
| 美元指数 | fxDINIW | 汇率风向 |
| 离岸人民币 | fxCNH | 美元兑离岸人民币 |
| 原油 WTI | fuCL | 原油期货 |
| 黄金 | fuGC | COMEX 黄金 |

## 批量查询命令

```bash
# A股指数
westock quote sh000001,sz399001,sh000300,sz399006,sh000688

# 港股指数
westock quote hkHSI,hkHSTECH

# A股 + 港股 + 美股主要指数一次查询
westock quote sh000001,sz399001,sh000300,sz399006,sh000688,hkHSI,hkHSTECH,usINX,usIXIC,usDJI

# 盘前全球市场速览按需补充
westock quote fxDINIW,fxCNH,fuCL,fuGC
```
