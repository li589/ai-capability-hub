---
name: 1688-product-find
description: |
  1688智能找商品能力。理解用户找商品、找同款等需求，通过文本、图片或链接搜索匹配商品。
  触发词：找商品、找同款、搜商品、想要 XX、帮我找、图片找货、链接找货、以图搜图。
metadata:
  openclaw:
    emoji: 🔍
    requires:
      bins:
        - python3
    primaryEnv: ALI_1688_AK
install_source: official
install_method: download
skill_id: official_2oc0gw9W
enabled_at: 1785348274906
version: 1.0.0
name_zh: 1688 找商品
---

# 1688-product-find (1688找商品Skill)
统一入口：`python3 {baseDir}/cli.py <command> [options]`

## 严格禁止 (NEVER DO)
- 不要编造商品价格、链接、`productId`、规格或供货信息，所有商品内容必须来自工具返回
- 不要在用户明确要下单、支付、查物流、管库存时继续调用本技能，这些不属于推荐能力
- 不要把工具返回的完整长描述原样堆给用户，应提炼商品标题、价格、核心卖点和商品链接

## 命令速查

| 命令 | 说明 | 示例 |
|------|------|------|
| `text_search` | 文本搜索商品 | `python3 cli.py text_search --query "黑色连帽卫衣"` |
| `image_search` | 图片以图搜图 | `python3 cli.py image_search --image "/path/to/image.jpg"` |
| `link_search` | 链接找同款 | `python3 cli.py link_search --url "https://detail.1688.com/offer/xxx.html"` |
| `configure` | 配置 AK | `python3 cli.py configure YOUR_AK` |

所有命令输出 JSON：`{"success": bool, "markdown": str, "data": {...}}`

**展示时直接输出 `markdown` 字段，Agent 分析追加在后面，不得混入其中。**

## 使用流程

Agent 根据用户意图**直接执行对应命令**。
各命令在 AK 缺失等情况下会自行返回明确错误，Agent 按下方「异常处理」应对即可。

### text_search（文本搜索）

当用户通过自然语言描述想要的商品时使用。

```bash
python3 cli.py text_search --query "黑色连帽卫衣宽松款" --limit 10
```

**参数说明**：
- `--query, -q`（必填）：搜索关键词
- `--platform, -p`（可选）：目标平台，默认 `1688`
- `--limit, -l`（可选）：返回数量，默认 `10`

**❗ --query 构造规则（必须遵守）**：

`--query` 的值应完整保留用户意图中的所有要素，包括但不限于：商品描述、排序要求、筛选条件。禁止丢弃用户提及的排序/筛选信息。

| 用户输入 | ✅ 正确的 --query | ❌ 错误的 --query |
|---------|------------------|------------------|
| 帮我找一件深绿色的始祖鸟同款冲锋衣，按销量倒排 | "深绿色 始祖鸟同款 冲锋衣 销量排序" | "深绿色冲锋衣 始祖鸟同款"|
| 找价格100元以下的男士牛仔裤 | "男士牛仔裤 价格100元以下" | "男士牛仔裤" |

### image_search（图片搜索）

当用户上传图片找同款时使用。

```bash
python3 cli.py image_search --image "/path/to/product.jpg" --limit 10
```

**参数说明**：
- `--image, -i`（必填）：图片本地路径或 URL。**本地图片必须使用绝对路径**（如 `/home/user/image.png` 或 `C:\Users\user\image.png`），禁止使用相对路径（如 `./image.png`），否则在不同操作系统下可能因工作目录不一致导致找不到文件。
- `--platform, -p`（可选）：目标平台，默认 `1688`
- `--limit, -l`（可选）：返回数量，默认 `10`
- `--threshold, -t`（可选）：相似度阈值，默认 `0.7`

### link_search（链接搜索）

当用户提供商品链接找同款时使用。

```bash
# 自动提取主图（仅 1688 支持）
python3 cli.py link_search --url "https://detail.1688.com/offer/xxx.html"

# 手动指定图片 URL（淘宝/天猫需要）
python3 cli.py link_search --url "https://item.taobao.com/item.htm?id=xxx" --image "图片URL"
```

**参数说明**：
- `--url, -u`（必填）：商品链接或商品 ID
- `--image, -i`（可选）：商品图片 URL（当自动获取失败时使用）
- `--platform, -p`（可选）：目标平台，默认 `1688`
- `--limit, -l`（可选）：返回数量，默认 `10`

**平台支持**：
| 平台 | 自动提取主图 | 说明 |
|------|-------------|------|
| **1688** | ✅ 支持 | 自动从商品页面提取主图 |
| **淘宝** | ❌ 不支持 | 需要用户手动提供图片 URL |
| **天猫** | ❌ 不支持 | 需要用户手动提供图片 URL |

**降级流程**：当 `link_search` 返回 `action: "need_image_url"` 时：
1. 提示用户无法自动获取商品主图
2. 引导用户手动复制商品图片 URL
3. 使用 `--image` 参数重新执行搜索

## 统一返回结构

所有搜索能力返回相同的商品数据结构：

```json
{
  "success": true,
  "query": "搜索词（仅 text_search）",
  "source_image": "图片 URL（image_search/link_search）",
  "source_url": "原始链接（仅 link_search）",
  "similar_products": [
    {
      "product_id": "商品 ID",
      "title": "商品标题",
      "image_url": "商品主图",
      "detail_url": "商品详情页链接",
      "similarity_score": 0.95,
      "source": "1688",
      "category_id": "类目 ID",
      "industry_name": "行业名称"
    }
  ],
  "search_type": "text_search|image_similarity|link_search",
  "total_results": 6
}
```

## 安全声明

| 风险级别 | 命令 | Agent 行为 |
|---------|------|-----------|
| **只读** | text_search | 参数明确时直接执行 |
| **只读** | image_search | 图片路径有效时直接执行 |
| **只读** | link_search | URL 有效时直接执行；提取失败时引导用户提供图片 URL |

## 执行前置（首次命中能力时必须）

- 首次执行 `configure` 前：先完整阅读 `references/capabilities/configure.md`
- 首次执行 `text_search` 前：先完整阅读 `references/capabilities/text_search.md`
- 首次执行 `image_search` 前：先完整阅读 `references/capabilities/image_search.md`
- 首次执行 `link_search` 前：先完整阅读 `references/capabilities/link_search.md`

## 异常处理

任何命令输出 `success: false` 时：

1. **先输出 `markdown` 字段**（已包含用户可读的错误描述）
2. **再根据关键词追加引导**：

| markdown 关键词 | Agent 额外动作 |
|----------------|--------------|
| “AK 未配置” | 提示用户运行 `python3 cli.py configure YOUR_AK` 配置认证信息，如果用户还没有 API_KEY，引导前往 https://clawhub.1688.com/ 获取 |
| "签名无效" 或 "401" | 提示用户检查 AK 是否正确或已过期 |
| "图片路径无效" | 提示用户检查图片路径是否存在 |
| "无法自动获取商品主图" | 引导用户手动提供商品图片 URL，使用 `--image` 参数 |
| "限流" 或 "429" | 建议用户等待 1-2 分钟后重试 |
| "格式异常" | 提示用户稍后重试，可能是 API 返回异常 |
| 其他 | 仅输出 markdown 即可 |

## 参数补齐引导话术

> **文本搜索**：请描述您想要的商品，例如："帮我找一件黑色连帽卫衣，宽松款的"

> **图片搜索**：请上传商品图片，我会帮您找到同款或相似商品。

> **链接搜索**：请提供商品链接。1688 链接可自动提取主图；淘宝/天猫链接需要您同时提供商品图片 URL。

## 技术说明

- **统一 API**：三个搜索能力共用 `/api/findProduct/1.0.0` 接口
- **认证方式**：通过环境变量 `ALI_1688_AK` 配置
- **依赖项**：Python 3.9+、requests、Pillow

## 更新日志

- v1.1.0 (2026-03-27): 新增 `cli.py` 统一 CLI 入口，简化命令调用方式
- v1.0.0 (2026-03-27): 初始版本，包含三大核心搜索能力（text_search、image_search、link_search）
