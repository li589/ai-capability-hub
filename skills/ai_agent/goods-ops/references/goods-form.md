# 商品表单字段 Reference（web_client_tool）

本文件只描述创建商品时要准备的业务字段含义与基本规则。不定义创建流程、页面跳转顺序。
读取本文件时，默认已经完成入口信息判断和商品编辑页跳转。

## 前端工具调用规则

- 工具名从当前上下文的 `web_client_tool_call` 可用 web tool 列表获取，根据描述选择“商品表单填充/提交/更新”相关工具。
- 调用前必须先执行 `get_web_client_tool_schema(<工具名>)`，读取该工具当前的 `inputSchema`，最后以他的返回为准
- 前端工具参数必须严格匹配 `inputSchema`；不要假设外层字段一定叫 `formData`、`data`、`payload` 或其他名称。
- 如果当前上下文没有可用的商品表单工具，不要猜测工具名，先说明当前页面缺少可执行的前端工具或引导用户跳转到商品创建页。

## 字段说明

### 入口字段规则

- 商品名称或商品图片至少需要一个；缺失时的追问和页面跳转顺序由 `SKILL.md` 决定。
- 若只有商品名称，默认 `goodsImageUrl` 设为 `[]`，继续根据名称生成商品信息。不主动询问图片处理方式。
- 若用户主动要求生成商品图（例如”帮我生成图片””用 AI 生成主图”）时，**非主动说明不调用** 调用图片生成接口：
  woscli image generateImage --prompt "xxxxx" --size "1024x1024" --count 1
  将生成的图片 URL 填入 `goodsImageUrl`。
- 若只有商品图片，必须先根据图片内容生成 `title`，再继续补全表单字段。

### 顶层字段

| 字段 | 类型 | 创建时必填 | 说明 |
|------|------|------------|------|
| `title` | string | 条件必填 | 商品名称，最多 60 字。若用户未提供名称但提供了图片，必须根据图片内容自动生成 |
| `subTitle` | string | 是 | 副标题，最多 60 字。根据商品名称、图片和描述自动生成 |
| `goodsImageUrl` | string[] | 条件必填 | 商品图片 URL 数组，每项为 URI 格式。若用户已提供商品名称，可不强制要求图片 |
| `categoryId` | integer | 是 | 分类 ID。调用 `search_category` 取最匹配 `id`，无结果默认 `231` |
| `categoryType` | integer | 否 | 分类类型。调用 `search_category` 取最匹配结果的 `category_type`结果为 `null` 时不填写|
| `isOnline` | boolean | 是 | 是否上架。默认 `true`，除非用户强烈要求修改 |
| `isMultiSku` | boolean | 是 | 是否多 SKU。默认 `false`。用户要求多规格时回复"目前只能创建单规格商品，多规格功能还在学习中" |
| `skuList` | object[] | 是 | SKU 列表。猜测合理价格，确保 `costPrice` < `salePrice`；每个 SKU 包含 `stockNum`，未指定库存时默认 100 |
| `goodsClassifyList` | object[] | 否 | 商品分类列表。`search_groups` 返回结果时为 `[{"classifyId": ..., "name": ...}]` 数组；无值时省略该字段 |
| `tagInfo` | object | 否 | 标签信息。`search_tags` 返回结果时为 `{"tagId": ..., "name": ...}` 对象；无值时省略该字段 |
| `goodsDesc` | string | 是 | 商品描述（HTML 格式）。根据商品名称、图片和描述生成 |
| `sessionId` | string | 否 | 会话 ID，用于链路追踪，不写入商品数据 |

**关键词生成原则**：基于商品名称、商品图片和描述，生成 1-8 个关键词（每个 1-3 个字），尽量用 `xxx|xxx|xxx` 形式拼接后传入搜索命令，例如白色 T 恤图片 → `"短袖|纯棉|白色|夏季|衣"`。商品上架流程中，默认并行调用 `search_category`、`search_tags`、`search_groups` 三个 tool，各调用一次并分别择优写入类目、标签、分组字段；每个 tool 每个商品最多调用 2 次，不按单个关键词逐次调用。若某个 tool 仍无合适结果，则按默认值或省略规则处理。

### autoOnlineOfflineDTO 结构

| 字段 | 类型 | 创建时必填 | 说明 |
|------|------|------------|------|
| `isAutoOnline` | boolean | 是 | 是否自动上架 |
| `isAutoOffline` | boolean | 是 | 是否自动下架 |
| `offlineStartTime` | null | 是 | 下架开始时间，不支持填写、修改 |
| `onlineStartTime` | null | 是 | 上架开始时间，不支持填写、修改|

### skuList 元素结构

| 字段 | 类型 | 创建时必填 | 说明 |
|------|------|------------|------|
| `salePrice` | number | 是 | 销售价格 |
| `costPrice` | number | 是 | 成本价格 |
| `stockNum` | integer | 是 | 库存数量，用户未指定时默认 100 |

### goodsClassifyList 元素结构

`search_groups` 返回结果时，取最匹配的填入：

| 字段 | 类型 | 说明 |
|------|------|------|
| `classifyId` | integer | 分组 ID，取 `search_groups` 结果的 `id` |
| `name` | string | 分组名称，取 `search_groups` 结果的 `name` |

`search_groups` 返回空或没找到合适分组时，不写入 `goodsClassifyList` 字段。

### tagInfo 结构

`search_tags` 返回结果时，取最匹配的一个填入：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tagId` | integer | 标签 ID，取 `search_tags` 结果的 `id` |
| `name` | string | 标签名称，取 `search_tags` 结果的 `name` |

`search_tags` 返回空或没找到合适的 tag 时，不写入 `tagInfo` 字段。

## 示例

```json
{
  "title": "白色纯棉短袖T恤",
  "subTitle": "夏季新款透气舒适",
  "goodsImageUrl": [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg"
  ],
  "categoryId": 1001,
  "categoryType": 1,
  "isOnline": true,
  "autoOnlineOfflineDTO": {
    "isAutoOnline": false,
    "isAutoOffline": false,
    "offlineStartTime": null,
    "onlineStartTime": null
  },
  "isMultiSku": false,
  "skuList": [
    {
      "salePrice": 99.0,
      "costPrice": 50.0,
      "stockNum": 100
    }
  ],
  "goodsClassifyList": [
    {
      "classifyId": 2001,
      "name": "上衣"
    }
  ],
  "goodsDesc": "<p>商品详情描述</p>"
}
```

### 未保存状态下修改字段

商品未保存时，直接生成要更新的业务字段片段；实际调用时仍需重新读取当前商品表单工具 schema 后再组装前端工具参数。

```json
{
  "title": "修正后的标题",
  "skuList": [
    {
      "salePrice": 79.0,
      "costPrice": 50.0,
      "stockNum": 100
    }
  ]
}
```

## 字段片段更新

用户在未保存状态下要求修改字段时，基于用户输入重新生成对应字段值，并重新调用当前可用的商品表单工具。

```
Step 1: 识别修改意图
  - 用户在未保存状态下要求修改某个字段（如"标题改成这个""价格调低一点"）。
  - 基于用户输入重新生成对应字段值。

Step 2: 重新调用当前前端商品表单工具
  - 重新读取 `get_web_client_tool_schema(<工具名>)`。
  - 按最新 schema 组装参数，将新值推送给前端。
  - 等待前端执行结果返回。
```
