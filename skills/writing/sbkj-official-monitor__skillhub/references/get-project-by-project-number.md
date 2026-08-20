## POST 根据项目编号查询招中标信息列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getProjectByProjectNumber?key=***`

**说明：** 根据项目编号/项目标号和可选发布时间搜索招中标项目信息列表

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| projectNumber | string | 是 | HNXW-202605028 | 项目编号 |
| publishTime | string | 否 | 2026-06-08 14:30:30 | 项目发布时间，格式： yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss；不传时按当前日期计算搜索日期窗口 |

### 请求示例

```json
{
  "projectNumber": "HNXW-202605028",
  "publishTime": "2026-06-08 14:30:30"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码 |
| msg | string | 响应信息 |
| subCode | string | 子错误码 |
| subMsg | string | 子错误信息 |
| data | array | 项目列表 |
| data[].id | integer | 项目ID |
| data[].newsTypeID | integer | 资讯类型ID |
| data[].title | string | 标题 |
| data[].publishTime | string | 项目发布时间 |
| data[].content | string | 内容摘要 |
| data[].proviceCode | string | 省级编码 |
| data[].cityCode | string | 市级编码 |
| data[].countyCode | string | 区县编码 |
| data[].collectWebID | integer | 来源站点ID |
| data[].hasFile | integer | 附件标识，0=无附件，1=有附件 |
| data[].score | number | 匹配得分 |
| data[].projectMoney | string | 项目金额；例如：10万 |
| data[].projectClassID | string | 项目分类ID |
| data[].purchaseTypeID | string | 采购类型ID |
| data[].industryCodeList | array | 行业编码集合 |
| data[].partANameList | array | 甲方列表 |
| data[].partBNameList | array | 乙方列表 |
| data[].contractEndDate | string | 合同截止日期 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": [
    {
      "id": "332023653",
      "newsTypeID": 2,
      "title": "邵阳市中医医院棉织品采购项目竞争性磋商成交结果公告",
      "publishTime": "2026-06-08 14:30:30",
      "content": null,
      "proviceCode": "430000",
      "cityCode": "430500",
      "countyCode": null,
      "collectWebID": "99557",
      "hasFile": 1,
      "score": null,
      "projectMoney": "28万",
      "projectClassID": "2",
      "purchaseTypeID": "3",
      "industryCodeList": [
        "Q831",
        "C177"
      ],
      "partANameList": null,
      "partBNameList": null,
      "contractEndDate": null
    },
    {
      "id": "328860041",
      "newsTypeID": 1,
      "title": "邵阳市中医医院棉织品采购项目招标公告",
      "publishTime": "2026-05-21 17:18:51",
      "content": null,
      "proviceCode": "430000",
      "cityCode": "430500",
      "countyCode": null,
      "collectWebID": "99557",
      "hasFile": 0,
      "score": null,
      "projectMoney": null,
      "projectClassID": "1",
      "purchaseTypeID": "3",
      "industryCodeList": [
        "Q831",
        "C177"
      ],
      "partANameList": null,
      "partBNameList": null,
      "contractEndDate": null
    }
  ],
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---
