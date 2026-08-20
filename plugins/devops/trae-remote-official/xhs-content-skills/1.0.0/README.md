# 小红书内容创作技能包

这是一个纯 Skill 的 TRAE Plugin，覆盖小红书内容从选题到发布的完整工作流，不包含 MCP、Connector、外部命令或第三方运行时依赖。

## 能力列表

| Skill | 能力 |
| --- | --- |
| `content-strategy-engine` | 总控并协调完整内容工作流 |
| `xhs-topic-planner` | 选题、关键词与笔记简报 |
| `xhs-content-writer` | 标题与正文写作 |
| `xhs-cover-strategy` | 封面类型、文案与素材策略 |
| `xhs-title-analyzer` | 标题五维诊断与改写建议 |
| `xhs-compliance-check` | CTA、诱导互动与敏感内容检查 |
| `xhs-humanizer` | 去除常见 AI 写作痕迹 |
| `content-scorer` | 发布前质量评分与检查 |
| `xhs-publish-engine` | 发布前自查、冷启动与赛道速查 |

## 目录结构

```text
xhs-content-skills/
├── .trae-plugin/plugin.json
├── skills/
│   └── <skill-name>/SKILL.md
├── assets/icon.svg
├── README.md
└── LICENSE
```

## 使用方式

当用户提出小红书内容创作、选题策划、标题或正文写作、封面策略、合规审查、标题诊断、去 AI 痕迹、内容评分或发布运营需求时，加载对应 Skill。需要完整流程时，优先使用 `content-strategy-engine` 作为总控。

## 认证与依赖

本插件不调用小红书接口，不需要账号授权、API Key、MCP、Connector 或本地依赖。所有能力均由 Skill 文档提供。

## 已知限制

- Skill 中的平台规则、指标和运营经验会随平台策略变化，使用前应结合当前规则核验。
- 本插件不代表小红书官方，也不会替用户执行实际发布操作。
- 图标和内容由原包作者提供；提交市场前应由提交方确认其权利与授权状态。

## License

MIT
