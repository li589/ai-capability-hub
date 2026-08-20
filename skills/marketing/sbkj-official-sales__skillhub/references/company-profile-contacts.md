## POST 企业联系电话

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/companyProfileContacts?key=***`

**说明：** 分页查询企业联系人信息，pageSize 实际最大按 5 处理。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| companyName | string | 是 | 武汉览山科技有限公司 | 企业名称  |
| pageNo | integer | 是 | 1 | 页码，从 1 开始 |
| pageSize | integer | 是 | 5 | 每页条数，接口内部最大按 5 处理 |

### 请求示例

```json
{
  "companyName": "武汉览山科技有限公司",
  "pageNo": 1,
  "pageSize": 5
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码 |
| msg | string | 响应信息 |
| data | object | 业务数据 |
| data.companyName | string | 企业名称 |
| data.pagination | object | 分页信息 |
| data.pagination.pageNo | integer | 当前页码 |
| data.pagination.pageSize | integer | 每页条数 |
| data.pagination.total | integer | 总条数 |
| data.pagination.totalPages | integer | 总页数 |
| data.pagination.hasNext | boolean | 是否有下一页 |
| data.records | array | 联系人列表 |
| data.records[].contactName | string | 联系人姓名 |
| data.records[].contactPhones | array | 联系电话列表 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "companyName": "中国五冶集团有限公司",
    "pagination": {
      "pageNo": 1,
      "pageSize": 5,
      "total": "327",
      "totalPages": 66,
      "hasNext": true
    },
    "records": [
      {
        "contactName": "程文华",
        "contactPhones": [
          "17340513729"
        ]
      }
    ]
  },
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---
