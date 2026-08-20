# Capability: image_search (图片找同款)

## 功能说明
基于用户上传的商品图片，通过图像识别和特征匹配，在 1688 平台搜索同款或相似商品。支持本地图片路径和图片 URL。

## 触发方式
**Skill 级触发词**: 图片找货、找同款、搜相似

**Capability 识别特征**:
- 用户输入包含图片附件
- 或消息中包含图片 URL
- 配合文字："找同款"、"有类似的吗"、"搜这个"

## 前置条件
- 已配置 AK（未配置时会提示运行 `cli.py configure YOUR_AK`）

## CLI 调用
```bash
python3 {baseDir}/capabilities/image_search/cmd.py --image "图片路径或URL" [--platform 1688] [--limit 6] [--threshold 0.7]
```

### 命令行参数
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--image` | `-i` | 图片本地路径或 URL | 必需 |
| `--platform` | `-p` | 目标平台 | 1688 |
| `--limit` | `-l` | 返回数量 | 6 |
| `--threshold` | `-t` | 相似度阈值 | 0.7 |

### 使用示例
```bash
# 基本用法
python3 cmd.py -i /path/to/image.jpg

# 指定返回数量
python3 cmd.py -i /path/to/image.jpg -l 10

# 完整参数
python3 cmd.py -i /path/to/image.jpg -p 1688 -l 5 -t 0.8
```

## 输入参数
```json
{
  "image_path": "string (required) - 本地图片路径或 URL",
  "platform": "string (optional) - 目标平台，默认 1688",
  "limit": "int (optional) - 返回数量，默认 6",
  "similarity_threshold": "float (optional) - 相似度阈值，默认 0.7"
}
```

## 处理流程
### 1. 图片预处理 (ImagePreprocessor)
```python
步骤：
1. 判断输入类型（本地路径 / URL）
2. 本地图片：检查文件存在性和大小
3. 返回处理后的图片信息
```

### 2. API 搜索 (_search_via_api)
**主要流程**:
1. 将图片通过 base64 编码转换成字符串
2. 拼装请求并调用 `/api/findProduct/1.0.0` 接口
3. 解析返回的商品数据

**API 请求格式**:
```json
{
  "request": {
    "imgBase64": "base64编码的图片字符串",
    "imageUrl": "图片URL（可选）",
    "pageSize": 10
  }
}
```

**API 响应格式**:
```json
{
  "data": {
    "data": [
      {
        "itemId": 987622522091,
        "title": "商品标题",
        "imageUrl": "商品主图URL",
        "detailUrl": "商品详情页URL",
        "score": 0.99786893,
        "source": "1688",
        "cateId": 201382421,
        "industryName": "消费品"
      }
    ],
    "count": 3
  }
}
```

### 3. 浏览器降级方案 (_search_via_browser)
当 API 不可用时，返回结构化信号，由 Agent 接管：
```python
return [{
    "action": "browser_render",
    "url": "https://s.1688.com/selloffer/offer_search.htm",
    "upload_image": image_path,
    "message": "正在上传图片并搜索同款..."
}]
```

## 输出格式
```json
{
  "success": true,
  "source_image": "/path/to/uploaded.jpg",
  "similar_products": [
    {
      "product_id": "987622522091",
      "title": "跨境创意五彩公鸡动物摆件2D平面亚克力家居办公桌面装饰摆件",
      "image_url": "https://img.alicdn.com/...",
      "detail_url": "https://detail.1688.com/offer/987622522091.html",
      "similarity_score": 0.9979,
      "source": "1688",
      "category_id": 201382421,
      "industry_name": "未定义产业名称"
    }
  ],
  "search_type": "image_similarity",
  "total_results": 3
}
```

## 代码结构
```
scripts/capabilities/image_search/
├── __init__.py      # 模块初始化
├── cmd.py           # CLI 入口
└── service.py       # 核心服务实现
    ├── ImagePreprocessor    # 图片预处理器
    ├── ImageSearchExecutor  # 搜索执行器
    ├── format_similar_product()  # 格式化输出
    └── image_search()       # 主入口函数
```

## 错误处理
- **图片路径无效**: 抛出 `ServiceError("图片路径无效")`
- **图片不存在**: 抛出 `FileNotFoundError`
- **图片太大**: 抛出 `ValueError`（超过 5MB）
- **API 格式异常**: 抛出 `ServiceError("格式异常，请稍后重试")`
- **AK 未配置**: 提示用户运行 `cli.py configure YOUR_AK`

## 测试用例
```python
# 本地图片路径
image_search(image_path="/workspace/product.jpg")

# 图片 URL
image_search(image_path="https://example.com/product.png")

# 指定返回数量
image_search(image_path="xxx.jpg", limit=10)

# 调整相似度阈值
image_search(image_path="xxx.jpg", similarity_threshold=0.8)
```

## 依赖关系
- `_http.api_post`: HTTP 请求封装
- `_auth.get_ak_from_env`: AK 认证
- `_errors.ServiceError`: 错误处理
- `_output.print_output/print_error`: 输出格式化

## 注意事项
1. 图片上传需考虑隐私和安全，临时文件会自动清理
2. API 调用需要有效的 AK 配置
3. 浏览器降级方案需要 Agent 接管处理