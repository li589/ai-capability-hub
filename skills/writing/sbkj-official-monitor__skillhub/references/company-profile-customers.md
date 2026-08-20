## POST 企业合作客户

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/companyProfileCustomers?key=***`

**说明：** 分页查询企业客户项目关系，pageSize 实际最大按 20 处理。

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
| data.records | array | 客户关系列表 |
| data.records[].partnerCompanyName | string | 合作方企业名称 |
| data.records[].relatedProjectId | string | 关联项目ID |
| data.records[].relatedProjectName | string | 关联项目名称 |
| data.records[].projectPublishTime | string | 项目发布时间， 格式 yyyy-MM-dd HH:mm:ss |
| data.records[].relationshipType | string | 关系类型，固定为客户 |

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
      "total": "46",
      "totalPages": 5,
      "hasNext": true
    },
    "records": [
      {
        "partnerCompanyName": "中江凯兴建材有限公司",
        "relatedProjectId": "249910165",
        "relatedProjectName": "中江县仓山污水处理厂及配套管网工程一标段施工运营总承包（PC+O）",
        "projectPublishTime": "2023-07-18 22:40:00",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "宜宾罗龙工业集中区投资集团有限责任公司",
        "relatedProjectId": "249866433",
        "relatedProjectName": "宜宾市南溪区长江沿线城市污水管网修复改造工程",
        "projectPublishTime": "2025-03-13 19:51:44",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "宜宾罗龙工业集中区投资集团有限责任公司",
        "relatedProjectId": "249856511",
        "relatedProjectName": "宜宾市南溪区长江沿线城市污水管网修复改造工程",
        "projectPublishTime": "2025-03-13 18:46:51",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "宜宾市三鼎建设工程有限责任公司",
        "relatedProjectId": "250119997",
        "relatedProjectName": "宜宾市翠屏区老城片区污水管网及相关附属设施治理工程",
        "projectPublishTime": "2025-03-14 17:41:03",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "宜宾市三鼎建设工程有限责任公司",
        "relatedProjectId": "250118353",
        "relatedProjectName": "宜宾市翠屏区老城片区污水管网及相关附属设施治理工程",
        "projectPublishTime": "2025-03-14 18:01:12",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "成都经开城市更新建设发展有限公司",
        "relatedProjectId": "250089393",
        "relatedProjectName": "大面东洪片区城中村改造配套道路-陵川路（玉竹路-洪惠路）改造工程、大面东洪片区城中村改造配套道路-洪惠路（陵川路-驿都大道）建设工程等4个项目设计-施工总承包",
        "projectPublishTime": "2025-01-13 16:44:06",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "内江市第二小学校",
        "relatedProjectId": "250309900",
        "relatedProjectName": "内江二小改扩建及附属幼儿园项目施工",
        "projectPublishTime": "2025-03-17 11:40:03",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "成都天府新区投资集团有限公司",
        "relatedProjectId": "250405643",
        "relatedProjectName": "福州路西段 (益州大道-滨江路)-两处老南干渠分洪工程施工",
        "projectPublishTime": "2025-03-17 17:06:14",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "五矿钢铁成都有限公司",
        "relatedProjectId": "250375922",
        "relatedProjectName": "中国五冶-金融岛站周边一体化开发项目投建运一体化项目C、D地块钢筋采购",
        "projectPublishTime": "2025-03-17 15:43:46",
        "relationshipType": "客户"
      },
      {
        "partnerCompanyName": "内江市第二小学校",
        "relatedProjectId": "250501952",
        "relatedProjectName": "内江二小改扩建及附属幼儿园项目施工",
        "projectPublishTime": "2025-03-17 09:30:54",
        "relationshipType": "客户"
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
