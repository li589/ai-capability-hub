# 战略增长罗盘

面向创业者、产品负责人和企业战略人员的一站式战略分析与规划应用，覆盖公司定位、商业模式、竞争格局、收入与成本结构、战略分析及产品路线规划，帮助团队明确方向并形成可执行的战略选择。

## 目录

```text
company-strategy-trae-plugin/
├── .trae-plugin/
│   └── plugin.json
├── skills/
│   └── company-strategy/
│       ├── SKILL.md
│       └── references/
├── icon.svg
├── README.md
└── LICENSE
```

## 能力

- 公司定位、产品定位、生态位与目标市场分析
- 商业模式、收入结构、成本驱动与单位经济分析
- 竞品战略、生态策略及跨产品线影响评估
- SWOT、PESTEL 与波特五力行业结构分析
- 产品组合、资源配置与战略选项比较
- 季度战略及 Must/Should/Could 路线规划
- 用户数据、官方原文与第三方资料的分层核验

## 包内关系

- `skills/company-strategy/`：插件的核心 Skill，负责事实核验、战略分析、选项比较和路线规划。
- MCP：本插件不包含 MCP 服务。
- Connector：本插件不包含 Remote MCP 或 OAuth Connector。
- `html-report`：由 TRAE 运行环境按需提供，用于将已经完成的战略正文渲染为 HTML；不属于本插件包。

## 认证、运行环境与依赖

本插件本身不要求配置账号、密钥、环境变量或本地运行时，也不包含安装脚本。外部资料获取能力取决于 TRAE 运行环境可用的 `WebSearch`、`WebFetch` 等工具；HTML 交付取决于运行环境是否提供 `html-report`。

## 配置与验证

`.trae-plugin/plugin.json` 中的所有路径均以插件根目录为基准：

- `logo` 指向 `./icon.svg`
- `skills` 指向 `./skills/`

安装或提交前，确认上述路径存在，并确认 `skills/company-strategy/SKILL.md` 可以被 TRAE 识别。

## 已知边界

- 不负责详细需求拆解、具体 PRD、交互原型、研发排期、项目协同与进度管理。
- 不用于没有明确决策问题的纯资讯监测。
- 无法核验的事实保持未知，不为满足格式制造数据、指标或图表。

## 来源与许可证

本插件基于内部整理的公司与产品战略方法开发，不捆绑第三方代码、品牌图标或外部运行文件。使用和再分发条件见根目录 `LICENSE`。
