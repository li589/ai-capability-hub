# References 索引

`cat-network-quality-analysis` skill 的参考文档。SKILL.md 已引用这些文档，按需查阅即可。

## 文档清单

| 文件 | 用途 | 何时查阅 |
|------|------|---------|
| `cli_schema.md` | CLI 参数完整约束与非法示例 | **每次**构造脚本命令前 |
| `query_text_templates.md` | `--query-text` 模板库与反模式 | 确定意图后选模板时 |
| `sse_events.md` | SSE 事件语义（辅助理解脚本内部行为） | 辅助理解 |
| `error_handling.md` | 脚本失败（JSON `code=1`）分类应对 | 出错时 |
| `branch_pcap.md` | 抓包分支（5a 候选提醒 / 5b 两入口） | 进入抓包场景时 |

## 最小执行路径

```
用户请求
  ├─ 多任务对比 ── SKILL.md §3-多任务对比（构造 <structured_json> → Step 4 交付）
  ├─ 抓包意图（直达/跟进）─── branch_pcap.md（5a/5b → Step 4 交付）
  └─ 错误/整体/性能分析
         ├─ query_text_templates.md 选模板
         ├─ cli_schema.md 校验参数
         ├─ SKILL.md Step 3 同步执行（300s 内置超时）
         │     ├─ code=0 → SKILL.md Step 4 交付 → 若 pcap_candidates 非空则 branch_pcap.md 5a
         │     └─ code=1 → error_handling.md
```

## 强制约束速查

1. **绝不发送 `.md` 文件附件** —— 解析 JSON 后把 `report` 字段作为消息正文
2. **时间戳一律毫秒（13 位）**，不是秒
3. **执行期间全程沉默**，脚本只输出一行 JSON，不转发中间输出
4. **抓包意图优先于错误/整体/性能**，不要先跑 error/overall/performance 再让用户选候选
5. **出错不自动重试**，必须先告知用户原因
6. **多任务对比触发条件**：用户要求做任务对比即触发；仅 1 个 task ID → 默认它为主任务并追问对比任务；无 task ID → 追问主任务和对比任务
7. **多任务对比数量上限**：最多 **1 个主任务 + 5 个对比任务**；超出 → 告知用户并让其重新选择
