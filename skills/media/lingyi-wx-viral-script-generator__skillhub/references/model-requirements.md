# 模型要求

## 模型中立

- 本 skill **不内置 LLM**，脚本生成完全由 agent 当前配置的模型完成。
- **纯文本生成，不依赖视觉能力**（区别于拆解（体验版）的看图需求）——任意支持中文的文本模型均可。
- 推荐中档及以上模型以保证口语化与结构完整；低档模型可能在时间轴自洽、枚举值上出错，需更多轮质检回炉。

## 写入防丢参

- 最终 Markdown 由 `render_script.py` 一次性渲染并覆写到 `--out`，agent **不要**手动分节追加输出文件（会造成多次生成内容叠加）。如需调整，改 JSON 后重跑 render。
- 生成 JSON 时若内容较长，可在思考里只列字段要点、不复述整份脚本，避免超大 content 丢参；JSON 文件每次覆写，不追加。

## 降级策略

- 模型若反复产出 schema 不合规的 JSON（退出码 2）：把 [output-schema.md](output-schema.md) 的字段细则直接贴进上下文，逐字段对照重生成。
- 口语化不达标：回炉时把 [compliance-rules.md](compliance-rules.md) 第 4 节铁律贴进上下文重写该段。
- 模型无法稳定输出干净 JSON：可让模型先输出 Markdown 脚本，再手工整理为 JSON 交 render_script.py 校验。
