## POST AI行业搜索

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/industryReasoning?key=***`

**说明：** 根据行业关键词短语推理并返回匹配的行业编码候选列表。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| keyword | string | 是 | 工程 | 行业关键词或短语 |

### 请求示例

```json
{
  "keyword": "工程"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code（0000000000=成功） |
| subMsg | string | 业务侧 msg |
| data | array | 业务数据结果 |
| data[].firstCodeList | array | 一级行业编码列表 |
| data[].secondCodeList | array | 二级行业编码列表 |
| data[].thirdCodeList | array | 三级行业编码列表 |
| data[].fullTitle | string | 全路径标题（如：一级-二级-三级） |
| data[].minTitle | string | 最下级路径标题 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": [
    {
      "firstCodeList": [],
      "secondCodeList": [],
      "thirdCodeList": [
        "P824"
      ],
      "fullTitle": "教育-教育-高等教育",
      "minTitle": "高等教育"
    },
    {
      "firstCodeList": [],
      "secondCodeList": [],
      "thirdCodeList": [
        "P823"
      ],
      "fullTitle": "教育-教育-中等教育",
      "minTitle": "中等教育"
    },
    {
      "firstCodeList": [],
      "secondCodeList": [],
      "thirdCodeList": [
        "P822"
      ],
      "fullTitle": "教育-教育-初等教育",
      "minTitle": "初等教育"
    }
  ],
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---
