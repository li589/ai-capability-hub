# 全域电商经营助手 / Omnichannel Commerce Assistant

`omnichannel-commerce-assistant` 是一个面向 TRAE 的全域电商分析与经营决策插件。它服务多平台、多渠道经营的品牌和商家，统一分析不同平台的商品结构、流量表现、转化效率、促销策略和用户运营，帮助经营者建立全域经营视角。

> 跨越平台看经营，统一视角做增长。  
> 让国内电商与跨境业务不再割裂，在一个应用中看清全域机会。

## 主要能力

- 店铺经营诊断与核心指标分析
- 商品、品类、爆款发现与孵化分析
- 流量、转化、定价、促销和利润评估
- 库存、供应链与留存/会员运营建议
- 中国国内与跨境市场研究、竞品对标和进入策略
- 面向管理决策的结构化报告与可视化输出指导

角色标签：全域电商、多平台运营、品牌电商、渠道运营、跨境电商、经营分析。

## 包内结构

```text
omnichannel-commerce-assistant/
├── .trae-plugin/
│   └── plugin.json
├── assets/
│   └── icon.png
├── skills/
│   └── omnichannel-commerce-assistant/
│       ├── SKILL.md
│       ├── assets/
│       ├── references/
│       └── scripts/
│           └── calculate_metrics.py
├── README.md
└── LICENSE
```

## 能力形态

- Skill：已包含，入口为 `./skills/omnichannel-commerce-assistant/SKILL.md`。
- MCP：未包含，不声明 `.mcp.json`。
- Connector：未包含，不需要 OAuth 或 Remote MCP 授权。

## 运行环境

- TRAE 负责加载插件清单和 Skill。
- Python 3 仅在执行可选的 `calculate_metrics.py` 时需要。
- Python 第三方依赖：无。

## 认证与敏感信息

当前版本不需要外部授权。包内不包含 token、secret、private key、账号、客户数据或真实凭据。

## 许可证

清单许可证标识为 `UNLICENSED`。详见 `LICENSE`。
