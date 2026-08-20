# 爆款内容API接口规范

## 接口信息

**接口地址**: `https://onetotenvip.com/skill/cozeSkill/getWxLowFanExplosiveArticle`

**请求方式**: POST

**内容类型**: application/json

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| originWord | String | 是 | 原词（用户输入的原始内容） |
| spitWords | Array[String] | 是 | 分词组（对原词进行合理分词后的结果） |
| expansionWords | Array[String] | 是 | 拓展词组（对原词进行合理拓展，10个词以内） |

## 参数示例

### 示例1：AI编程
```json
{
  "originWord": "AI编程",
  "spitWords": ["AI", "编程"],
  "expansionWords": ["AI科技", "人工智能", "大模型", "机器学习", "智能编程"]
}
```

### 示例2：健康饮食
```json
{
  "originWord": "健康饮食",
  "spitWords": ["健康", "饮食"],
  "expansionWords": ["养生", "营养", "减肥", "健康生活", "饮食搭配", "健康食谱"]
}
```

## 返回数据

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "title": "文章标题",
      "accountName": "公众号名称",
      "readCount": 10000,
      "likeCount": 500,
      "publishTime": "2024-01-01",
      "url": "https://mp.weixin.qq.com/..."
    }
  ]
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| title | String | 文章标题 |
| accountName | String | 公众号名称 |
| readCount | Integer | 阅读量 |
| likeCount | Integer | 点赞数 |
| publishTime | String | 发布时间 |
| url | String | 文章链接 |

## 注意事项

1. **分词原则**：
   - 保持语义完整性
   - 避免过度拆分导致语义丢失
   - 示例："AI编程" → ["AI", "编程"]（合理） vs ["A", "I", "编", "程"]（不合理）

2. **拓展词原则**：
   - 围绕核心主题拓展
   - 保持相关性和实用性
   - 数量控制在10个以内
   - 示例："AI编程" → ["AI科技", "人工智能", "大模型"]（相关） vs ["美食", "旅游"]（不相关）

3. **排序规则**：
   - 默认按互动数（阅读量+点赞数*10）降序排序
   - 返回TOP30数据

4. **错误处理**：
   - 网络超时：30秒
   - HTTP错误：显示状态码和响应内容
   - API错误：显示错误信息

## 使用建议

1. 关键词选择应具有代表性，避免过于宽泛或过于狭窄
2. 分词应考虑用户搜索习惯和语义关联
3. 拓展词应覆盖相关热门话题和长尾关键词
