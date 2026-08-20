---
name: huxiu-top
description: 获取虎嗅平台当前头条和焦点文章，覆盖科技与互联网、人工智能、商业消费、公司与产业、汽车出行、金融投资、创业创新等方向。用于用户希望快速了解当前重点内容、重要事件、行业变化，以及值得关注的深度报道与分析评论时。
install_source: official
install_method: download
skill_id: 4269af0c-1fe6-4a7a-a4ec-fa00d9eee9e1
enabled_at: 1787232722541
version: 1.0.0
name_zh: 虎嗅头条
---

# 虎嗅头条

## 调用接口

如果运行环境默认限制外部网络访问，先按该环境的授权机制获取网络访问权限，再执行下面的请求，避免同一接口被调用两次。

```bash
curl -s "https://api-ms-mcp.huxiu.com/skills/top"
```

## 返回

接口成功时返回：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "title": "文章标题",
        "published_at": "发布时间",
        "article_url": "https://...",
        "snippet": "文章正文片段",
        "author_name": "作者名称",
        "author_url": "https://..."
      }
    ]
  }
}
```

## 输出规则

1. 从 `data.items` 读取头条和焦点文章。
2. 按接口返回顺序输出标题、发布时间、作者名称和文章链接。
3. `author_url` 非空时，将作者名称链接到作者主页；为空时只输出作者名称。
4. `snippet` 非空时可以作为摘要；为空时省略，不要自行补写。
5. 请求失败、`success=false` 或列表为空时如实说明。
6. 不要编造标题、发布时间、作者、链接或摘要。
