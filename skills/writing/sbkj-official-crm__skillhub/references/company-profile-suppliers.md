## POST 企业供应商

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/companyProfileSuppliers?key=***`

**说明：** 分页查询企业供应商项目关系，pageSize 实际最大按 20 处理。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| companyName | string | 是 | 武汉览山科技有限公司 | 企业名称 |
| pageNo | integer | 是 | 1 | 页码，从 1 开始 |
| pageSize | integer | 是 | 20 | 每页条数，接口内部最大按 20 处理 |

### 请求示例

```json
{
  "companyName": "武汉览山科技有限公司",
  "pageNo": 1,
  "pageSize": 20
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
| data.records | array | 供应商关系列表 |
| data.records[].partnerCompanyName | string | 合作方企业名称 |
| data.records[].relatedProjectId | string | 关联项目ID |
| data.records[].relatedProjectName | string | 关联项目名称 |
| data.records[].projectPublishTime | string | 项目发布时间 |
| data.records[].relationshipType | string | 关系类型，固定为供应商 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "companyName": "中国五冶集团有限公司",
    "pagination": {
      "pageNo": 1,
      "pageSize": 10,
      "total": "662",
      "totalPages": 67,
      "hasNext": true
    },
    "records": [
      {
        "partnerCompanyName": "四川晖古建材有限公司",
        "relatedProjectId": "249386549",
        "relatedProjectName": "中国五冶内江职业技术学院新校区产教融合建设项目一标段安全文明物资",
        "projectPublishTime": "2025-03-11 17:08:05",
        "relationshipType": "供应商"
      },
      {
        "partnerCompanyName": "徐州市勋祈机电设备贸易有限公司",
        "relatedProjectId": "249469545",
        "relatedProjectName": "五冶工程技术服务分公司日照作业部山东日照LNG及煤气净化作业区年修项目气动调节阀采购一批次",
        "projectPublishTime": "2025-03-12 09:31:39",
        "relationshipType": "供应商"
      },
      {
        "partnerCompanyName": "四川晨景园林工程有限公司",
        "relatedProjectId": "249225327",
        "relatedProjectName": "中国五冶德阳老年病医院住院病区项目成本控制",
        "projectPublishTime": "2025-03-11 08:19:47",
        "relationshipType": "供应商"
      },
      {
        "partnerCompanyName": "四川建川兴蓉建设工程有限公司",
        "relatedProjectId": "249225316",
        "relatedProjectName": "中国五冶航空与燃机配套产业园基础设施建设项目(一期)A区总坪及景观工程",
        "projectPublishTime": "2025-03-11 08:19:36",
        "relationshipType": "供应商"
      },
      {
        "partnerCompanyName": "徐州市勋祈机电设备贸易有限公司",
        "relatedProjectId": "249478739",
        "relatedProjectName": "五冶工程技术服务分公司日照作业部山东日照LNG及煤气净化作业区年修项目气动快切阀采购一批次",
        "projectPublishTime": "2025-03-12 09:50:11",
        "relationshipType": "供应商"
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
