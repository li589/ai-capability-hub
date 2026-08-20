# 小红书 / 朋友圈 通用接口入参

本文件记录两个 skill 共用的 `smart-content save` 工具的入参与返回。本文件是事实层，若与 CLI `--help` 不一致，以 CLI 为准。

## 工具调用方式

所有工具通过 `woscli` 命令行方式调用。每条命令都由**固定命令头 + 参数**组成：

```bash
woscli 固定分类 固定命令名 --参数名 参数值
```

> **全局格式铁律：**
>
> 1. 第 1 个词固定是 `woscli`
> 2. 第 2 个词固定是命令分类
> 3. 第 3 个词固定是命令名
> 4. 只有第 4 个词开始才允许出现 `--参数名`
> 5. 命令分类和命令名绝对不能写成 `--category`、`--command`、`--cmd`
> 6. 所有业务参数必须以 `--<name> <value>` 的独立 flag 形式逐一传入

**遇到报错或不理解出入参时**，执行对应命令的 `--help` 获取参数规则，例如：

```bash
woscli smart-content save --help
```

---

## `get_goods_detail`
- **分类**：`mall-goods`
- **功能**：批量查询商品详情
- **参数说明**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | `goods_ids` | array\<long\> | 是 | 商品 ID 数组，**必须传 JSON 数组格式**，元素为 long 类型，不能传字符串 |
- **格式要求（严格遵守）**：
  - `goods_ids` 必须是 JSON 数组，如 `[102781115999837, 102787313999837]`
  - **禁止**传字符串形式，如 `"102781115999837"` 或 `["102781115999837"]`（字符串数组会导致反序列化失败）
  - **禁止**传逗号分隔字符串，如 `"102781115999837,102787313999837"`
  - 每个元素必须是数字（long），不是带引号的字符串
- **调用示例**：
  ```bash
  woscli mall-goods get_goods_detail --goods_ids [102781115999837,102787313999837]
  ```
- **返回示例**：
  ```json
  {
    "results": [
      {
        "id": 102781115999837,
        "title": "2026年 用心之选，让生活更美好",
        "description": null,
        "image_url": "https://image-c-dev.weimobwmc.com/qa-5W/b7da56ae93af4f11803d913c35f018ce.jpg",
        "category_full_url": "服饰>女装",
        "classify_full_url": null,
        "tag": "小王标签",
        "max_sale_price": null,
        "real_sale_num": 99,
        "stock_num": "0"
      }
    ],
    "total": 1
  }
  ```
- **创作使用字段**：`title`、`description`、`image_url`、`tag`
- **补充规则**：`description` 为 null 时，结合 `title`、`category_full_url`、`tag` 进行创作，但禁止捏造价格、活动、库存、时效等信息

---

## `editImage`
- **分类**：`image`
- **功能**：根据商品首图生成渠道风格商品图片
- **参数说明**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | `imageUrl` | string | 是 | 原始图片 URL（商品首图） |
  | `prompt` | string | 是 | 图片生成提示词 |
  | `size` | string | 否 | 图片尺寸，默认 `2048x2048` |
  | `count` | number | 否 | 生成数量，默认 `1` |

---

## `save`
- **分类**：`smart-content`
- **功能**：保存并发布图文内容
- **请求结构**：顶层字段直接传入，其中 `content` 作为一个 JSON 对象整体传入
- **参数说明**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | `title` | string | **按渠道决定** | 小红书必填；朋友圈**完全不传** |
  | `content` | json | 是 | 内容对象 |
  | `content.title` | string | **按渠道决定** | 小红书必填；朋友圈**完全不传** |
  | `content.image_url_list` | array | 是 | 图片 URL 列表，按商品顺序存放每个商品生成的 1 张图片 |
  | `content.content_info` | string | 是 | 正文内容 |
  | `content.content_tags` | array | **按渠道决定** | 小红书必填 3~5 个；朋友圈**完全不传** |
  | `contentType` | number | 是 | 内容类型：小红书传 `1`；朋友圈传 `2` |
  | `source` | number | 是 | 内容来源，当前示例为 `1` |
  | `creator` | string | 是 | 创建人，当前示例为 `system` |

> **渠道差异详见：`xhs-note-params.md` 与 `moments-note-params.md`**

- **请求示例（小红书）**：
  ```json
  {
    "cmd": "save",
    "title": "自然风光合集",
    "content": {
      "title": "自然风光合集",
      "image_url_list": [
        "https://example.com/image-1.jpg",
        "https://example.com/image-2.jpg"
      ],
      "content_info": "高山湖泊、森林海岸等高清风景图，可直接访问。",
      "content_tags": ["风景", "自然", "高清"]
    },
    "contentType": 1,
    "source": 1,
    "creator": "system"
  }
  ```
- **请求示例（朋友圈）**：
  ```json
  {
    "cmd": "save",
    "content": {
      "image_url_list": [
        "https://example.com/image-1.jpg",
        "https://example.com/image-2.jpg"
      ],
      "content_info": "今天新到的好物，推荐一下。"
    },
    "contentType": 1,
    "source": 1,
    "creator": "system"
  }
  ```
