## POST 招中标信息结构化数据详情

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getZTBStructreDetail?key=***`

**说明：** 根据项目 ID 和发布时间获取招中标项目信息结构化项目详情与采集源网址。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | integer | 是 | 332023653 | 项目ID |
| publishTime | string | 是 | 2026-06-08 14:30:30 | 项目发布时间，yyyy-MM-dd HH:mm:ss； |

### 请求示例

```json
{
  "id": 332023653,
  "publishTime": "2026-06-08 14:30:30"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码 |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code |
| subMsg | string | 业务侧 msg |
| data | object | 业务数据结果 |
| data.projectID | integer | 项目ID |
| data.publishTime | string | 项目发布时间 格式：yyyy-MM-dd HH:mm:ss |
| data.sbkjBidUrl | string | 世舶科技项目信息地址 |
| data.collectUrl | string | 项目源网址 |
| data.projectName | string | 项目名称 |
| data.projectNumber | array | 项目编号（支持多编号） |
| data.projectSectionCode | array | 项目标段编号（支持多标段） |
| data.budgetMoney | array | 预算金额（支持多金额，如：[100, 200]）单位：元 |
| data.bidMoney | array | 中标金额（支持多金额，如：[100, 200]）单位：元 |
| data.siginUpStopDate | string | 报名截止日期（null表示无）格式：yyyy-MM-dd HH:mm:ss |
| data.bidStartDate | string | 开标日期（null表示无）格式：yyyy-MM-dd HH:mm:ss |
| data.bidStartAddress | array | 开标地点（支持多地点） |
| data.partyAInfo | array | 甲方信息列表 |
| data.partyAInfo[].name | string | 主体名称（甲方/乙方/代理机构） |
| data.partyAInfo[].contactName | array | 联系人列表（支持多人） |
| data.partyAInfo[].contactPhone | array | 联系电话列表（支持多号码） |
| data.partyAInfo[].address | array | 地址列表（支持多地址） |
| data.partyAInfo[].email | array | 邮箱列表（支持多邮箱，null表示无） |
| data.partyBInfo | array | 乙方信息列表 |
| data.agencyInfo | array | 代理机构信息列表 |
| data.bidCompany | array | 投标企业列表（支持多家） |

### 响应示例

```json
{
  "data": {
    "projectID": 332023653,
    "publishTime": "2026-06-08 14:30:30",
    "sbkjBidUrl": null,
    "collectUrl": "https://xvmec.com/lookzb?item=9c682b43-dd35-4978-98ad-16bbfee920fa&type=2",
    "projectName": "邵阳市中医医院棉织品采购项目",
    "projectNumber": [
      "HNXW-202605028"
    ],
    "projectSectionCode": [],
    "budgetMoney": [
      280000
    ],
    "bidMoney": [],
    "siginUpStopDate": "2026-05-28 17:00:00",
    "bidStartDate": "2026-06-03 14:30:00",
    "bidStartAddress": [
      "湖南鑫卫开标室"
    ],
    "partyAInfo": [
      {
        "name": "邵阳市中医医院",
        "contactName": [
          "胡女士"
        ],
        "contactPhone": [
          "07395227115"
        ],
        "address": [
          "邵阳市双坡岭"
        ],
        "email": []
      }
    ],
    "partyBInfo": [
      {
        "name": "项城市梦丽雅商贸有限公司",
        "contactName": [
          "邓新力"
        ],
        "contactPhone": [
          "13525785803"
        ],
        "address": [
          "项城市交通路与工业路交叉口东南角"
        ],
        "email": null
      }
    ],
    "agencyInfo": [
      {
        "name": "湖南先卫医药电子商务科技发展有限公司",
        "contactName": [
          "黄芝",
          "陈乾"
        ],
        "contactPhone": [
          "4006968998转94"
        ],
        "address": [
          "长沙市开福区英鞭中路一段88号天健当平方英里1栋8楼"
        ],
        "email": []
      }
    ],
    "bidCompany": [
      "项城市梦丽雅商贸有限公司",
      "河南梦欣兰服饰有限公司",
      "项城市梦风兰服饰有限公司"
    ]
  },
  "msg": "ok",
  "count": 0,
  "returnValue": null,
  "returnvalue": null,
  "subCode": "0000000000",
  "subMsg": "成功",
  "code": 200
}
```

---
