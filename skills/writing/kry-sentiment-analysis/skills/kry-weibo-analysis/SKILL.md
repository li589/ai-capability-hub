---
name: kry-weibo-analysis
version: 1.1.0
description: 微博舆情数据获取与分析。需要品牌关键词作为搜索条件。
---

# 数据获取

```bash
kry-cli comment weibo -k <brandKey>
```

| 参数                   | 说明       | 必填 | 示例     |
| ---------------------- | ---------- | ---- | -------- |
| `-k, --brandKey <key>` | 品牌关键词 | 是   | `星巴克` |

> 品牌关键词由主 SKILL 步骤三获取，本子 SKILL 无需重复获取。

---

# 分析报告

- 报告内容：基于参考模版，并按照用户的需求补充章节、段落、内容
- 参考模版：[template_weibo.md](../../references/template_weibo.md)
- 格式要求：生成单文件、交互式 HTML
