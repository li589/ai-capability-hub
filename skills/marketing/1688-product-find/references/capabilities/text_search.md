# Capability: text_search (文本搜索)

## 功能说明
通过用户输入的关键词或自然语言描述，在 1688 平台搜索匹配的商品列表。与 image_search 和 link_search 共用同一 API 接口。

## 触发方式
**Skill 级触发词**: 找商品、搜商品、想要 XX、帮我找 XX

**Capability 识别特征**:
- 用户输入包含商品描述性语言
- 不包含图片附件
- 不包含完整 URL 链接

## 前置条件
- 已配置 AK（未配置时会提示运行 `cli.py configure YOUR_AK`）

## CLI 调用
```bash
python3 {baseDir}/capabilities/text_search/cmd.py --query "搜索关键词" [--platform 1688] [--limit 6]
```

### 命令行参数
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--query` | `-q` | 搜索关键词 | 必需 |
| `--platform` | `-p` | 目标平台 | 1688 |
| `--limit` | `-l` | 返回数量 | 6 |

### 使用示例
```bash
# 基本用法
python3 cmd.py -q "黑色连帽卫衣"

# 指定返回数量
python3 cmd.py -q "手机壳" -l 10

# 完整参数
python3 cmd.py -q "男士牛仔裤 修身" -p 1688 -l 5
```

## 输入参数
```json
{
  "query": "string (required) - 搜索关键词",
  "platform": "string (optional) - 目标平台，默认 1688",
  "limit": "int (optional) - 返回数量，默认 6"
}
```

## 处理流程
### 1. 查询处理
直接使用用户输入的关键词作为搜索条件。

### 2. API 搜索 (_search_via_api)
**主要流程**:
1. 拼装请求并调用 `/api/findProduct/1.0.0` 接口
2. 解析返回的商品数据

**API 请求格式**:
```json
{
  "request": {
    "query": "搜索关键词",
    "pageSize": 10
  }
}
```

**API 响应格式**:
```json
{
  "data": [
    {
      "industryName": "消费品",
      "score": "0.97332934",
      "itemId": 984731164094,
      "cateId": 122698013,
      "imageUrl": "https://img.alicdn.com/imgextra/O1CN018RgEjT1KiHAGIt18W_!!2212920081197-0-cib.jpg",
      "source": "1688",
      "detailUrl": "https://detail.1688.com/offer/984731164094.html",
      "recallSource": "same_product_recall",
      "title": "按摩垫按摩靠垫电动热敷按摩仪长导轨家用按摩仪揉捏腰部按摩器",
      "class": "com.alibaba.china.shared.tagspider.client.Model.aifindproduct.AiFindProductItem"
    }
  ],
  "__msgCode__": "OK",
  "__success__": true,
  "count": 1,
  "intent": {
    "intentType": "IMAGE_SEARCH",
    "imageUrl": "https://img.alicdn.com/imgextra/O1CN01Mx7Qyb24jADQmO25X_!!2217083847426-0-cib.jpg",
    "findSame": true,
    "class": "com.alibaba.china.shared.tagspider.client.Model.aifindproduct.AiFindProductIntent"
  }
}
```

## 输出格式
```json
{
  "success": true,
  "query": "黑色连帽卫衣",
  "similar_products": [
    {
      "product_id": "987622522091",
      "title": "2024新款黑色连帽卫衣男宽松加绒加厚秋冬季外套",
      "image_url": "https://img.alicdn.com/...",
      "detail_url": "https://detail.1688.com/offer/987622522091.html",
      "similarity_score": 0.95,
      "source": "1688",
      "category_id": 201382421,
      "industry_name": "消费品"
    }
  ],
  "search_type": "text_search",
  "total_results": 6
}
```

## 代码结构
```
scripts/capabilities/text_search/
├── __init__.py      # 模块初始化
├── cmd.py           # CLI 入口
└── service.py       # 核心服务实现
    ├── TextSearchExecutor   # 搜索执行器
    ├── format_product_card()  # 格式化输出
    └── text_search()        # 主入口函数
```

## 错误处理
- **AK 未配置**: 提示用户运行 `cli.py configure YOUR_AK`
- **API 格式异常**: 抛出 `ServiceError("格式异常，请稍后重试")`
- **无搜索结果**: 返回空数组

## 测试用例
```python
# 基础搜索
text_search(query="黑色连帽卫衣")

# 多关键词搜索
text_search(query="黑色连帽卫衣 宽松 加绒")

# 限定数量
text_search(query="手机壳", limit=10)
```

## 依赖关系
- `_http.api_post`: HTTP 请求封装
- `_auth.get_ak_from_env`: AK 认证
- `_errors.ServiceError`: 错误处理
- `_output.print_output/print_error`: 输出格式化

## 与其他能力的关系
- **共用 API**: 与 `image_search`、`link_search` 使用同一 API path (`/api/findProduct/1.0.0`)
- **区别**: text_search 通过 `query` 参数传递搜索词，而非图片

## 注意事项
1. 搜索关键词应尽量准确，避免过于宽泛
2. API 调用需要有效的 AK 配置
3. 返回的商品数据结构与 image_search 一致
4. **--query 必须完整保留用户意图**：禁止丢弃用户提及的排序要求（如“按销量倒排”）、价格筛选（如“100元以下”）、品牌限定等信息，这些要素必须一并携带到 query 参数中
