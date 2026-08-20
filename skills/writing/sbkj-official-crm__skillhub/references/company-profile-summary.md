## POST 企业基本信息

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/companyProfileSummary?key=***`

**说明：** 根据企业名称查询企业画像汇总信息。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| companyName | string | 是 | 武汉览山科技有限公司 | 企业名称  |

### 请求示例

```json
{
  "companyName": "武汉览山科技有限公司"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码 |
| msg | string | 响应信息 |
| data | object | 业务数据 |
| data.companyName | string | 企业名称 |
| data.baseInfo | object | 企业基础信息 |
| data.baseInfo.enterpriseProfile | object | 企业概况 |
| data.baseInfo.enterpriseProfile.companyId | integer | 企业ID |
| data.baseInfo.enterpriseProfile.companyTypeName | string | 企业类型名称 |
| data.baseInfo.enterpriseProfile.companyTypeCode | string | 企业类型编码 |
| data.baseInfo.enterpriseProfile.industryName | string | 所属行业名称 |
| data.baseInfo.enterpriseProfile.industryCode | string | 所属行业编码 |
| data.baseInfo.enterpriseProfile.registeredRegion | object | 注册地区信息 |
| data.baseInfo.enterpriseProfile.registeredRegion.areaId | integer | 地区ID |
| data.baseInfo.enterpriseProfile.registeredRegion.provinceCode | string | 省编码 |
| data.baseInfo.enterpriseProfile.registeredRegion.cityCode | string | 市编码 |
| data.baseInfo.enterpriseProfile.legalRepresentative | string | 法定代表人 |
| data.baseInfo.enterpriseProfile.establishmentDate | string | 成立日期 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.enterpriseProfile.operatingStatus | object | 经营状态 |
| data.baseInfo.enterpriseProfile.operatingStatus.statusCode | string | 经营状态编码 |
| data.baseInfo.enterpriseProfile.operatingStatus.statusName | string | 经营状态名称 |
| data.baseInfo.enterpriseProfile.historicalNames | string | 历史名称 |
| data.baseInfo.registrationInfo | object | 注册信息 |
| data.baseInfo.registrationInfo.creditCode | string | 统一社会信用代码 |
| data.baseInfo.registrationInfo.registrationNumber | string | 注册号 |
| data.baseInfo.registrationInfo.organizationCode | string | 组织机构代码 |
| data.baseInfo.registrationInfo.registrationAuthority | string | 登记机关 |
| data.baseInfo.registrationInfo.registeredCapital | object | 注册资本 |
| data.baseInfo.registrationInfo.registeredCapital.amount | number | 注册资本金额 |
| data.baseInfo.registrationInfo.registeredCapital.unitCode | string | 注册资本单位编码 |
| data.baseInfo.registrationInfo.registeredCapital.unitName | string | 注册资本单位名称 |
| data.baseInfo.registrationInfo.paidInCapital | object | 实缴资本 |
| data.baseInfo.registrationInfo.paidInCapital.amount | number | 实缴资本金额 |
| data.baseInfo.registrationInfo.paidInCapital.unitCode | string | 实缴资本单位编码 |
| data.baseInfo.registrationInfo.paidInCapital.unitName | string | 实缴资本单位名称 |
| data.baseInfo.operationInfo | object | 经营信息 |
| data.baseInfo.operationInfo.businessScope | string | 经营范围 |
| data.baseInfo.operationInfo.businessTerm | string | 营业期限 |
| data.baseInfo.operationInfo.businessTermStart | string | 营业期限开始时间 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.operationInfo.businessTermEnd | string | 营业期限结束时间 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.operationInfo.approvalDate | string | 核准日期 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.operationInfo.revocationDate | string | 吊销日期 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.operationInfo.cancellationDate | string | 注销日期 格式 yyyy-MM-dd HH:mm:ss |
| data.baseInfo.operationInfo.insuredPersonCount | string | 参保人数 |
| data.baseInfo.contactInfo | object | 联系信息 |
| data.baseInfo.contactInfo.registeredAddress | string | 注册地址 |
| data.baseInfo.contactInfo.latestAddress | string | 最新地址 |
| data.baseInfo.contactInfo.website | string | 官网地址 |
| data.baseInfo.contactInfo.contactPhones | array | 联系电话列表 |
| data.baseInfo.contactInfo.contactEmails | array | 联系邮箱列表 |
| data.projectInsights | object | 项目统计信息 |
| data.projectInsights.bidStatistics | array | 投标项目统计列表 |
| data.projectInsights.bidStatistics[].industryName | string | 行业名称 |
| data.projectInsights.bidStatistics[].projectCount | integer | 项目数量 |
| data.projectInsights.bidStatistics[].projectShare | string | 项目占比 |
| data.projectInsights.bidStatistics[].budgetAmountWan | string | 预算金额，单位万元 |
| data.projectInsights.winStatistics | array | 中标项目统计列表 |
| data.projectInsights.winStatistics[].industryName | string | 行业名称 |
| data.projectInsights.winStatistics[].projectCount | integer | 项目数量 |
| data.projectInsights.winStatistics[].projectShare | string | 项目占比 |
| data.projectInsights.winStatistics[].budgetAmountWan | string | 预算金额，单位万元 |
| data.relationshipSummary | object | 关系汇总 |
| data.relationshipSummary.contactPersonCount | integer | 联系人数量 |
| data.relationshipSummary.customerProjectCount | integer | 客户项目数量 |
| data.relationshipSummary.supplierProjectCount | integer | 供应商项目数量 |
| data.dataStatus | object | 数据命中状态 |
| data.dataStatus.baseInfoAvailable | boolean | 是否命中企业基础信息 |
| data.dataStatus.projectStatisticsAvailable | boolean | 是否命中项目统计信息 |
| data.dataStatus.contactsAvailable | boolean | 是否命中联系人数据 |
| data.dataStatus.customersAvailable | boolean | 是否命中客户数据 |
| data.dataStatus.suppliersAvailable | boolean | 是否命中供应商数据 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "companyName": "中国五冶集团有限公司",
    "baseInfo": {
      "enterpriseProfile": {
        "companyId": "21227579",
        "companyTypeName": "有限责任公司（国有控股）",
        "companyTypeCode": "1140",
        "industryName": "场地准备活动",
        "industryCode": "E5022",
        "registeredRegion": {
          "areaId": null,
          "provinceCode": "510000",
          "cityCode": "510100"
        },
        "legalRepresentative": "朱永繁",
        "establishmentDate": "1980-09-22 00:00:00",
        "operatingStatus": {
          "statusCode": "1",
          "statusName": "在营（开业）"
        },
        "historicalNames": null
      },
      "registrationInfo": {
        "creditCode": "91510100201906490X",
        "registrationNumber": "510100000073686",
        "organizationCode": "201906490",
        "registrationAuthority": "510100",
        "registeredCapital": {
          "amount": 532334.3,
          "unitCode": "156",
          "unitName": "156"
        },
        "paidInCapital": {
          "amount": 500417.82,
          "unitCode": null,
          "unitName": "156"
        }
      },
      "operationInfo": {
        "businessScope": "工程总承包、施工总承包；",
        "businessTerm": "2008/10/8 00:00:00-",
        "businessTermStart": "2008-10-08 00:00:00",
        "businessTermEnd": null,
        "approvalDate": "2025-03-07 00:00:00",
        "revocationDate": null,
        "cancellationDate": null,
        "insuredPersonCount": "0"
      },
      "contactInfo": {
        "registeredAddress": "成都市锦江区五冶路9号",
        "latestAddress": "成都市锦江区五冶路9号",
        "website": "http://www.mcc5.com.cn/",
        "contactPhones": [
          "028-12121212"
        ],
        "contactEmails": [
          "12121212@qq.com",
          "12121212@mcc5.com.cn"
        ]
      }
    },
    "projectInsights": {
      "bidStatistics": [
        {
          "industryName": "其他房屋建筑业",
          "projectCount": 1996,
          "projectShare": "30.83%",
          "budgetAmountWan": "7955058.35万元"
        },
        {
          "industryName": "其他土木工程建筑",
          "projectCount": 1929,
          "projectShare": "29.80%",
          "budgetAmountWan": "7590320.82万元"
        },
        {
          "industryName": "管道和设备安装",
          "projectCount": 1001,
          "projectShare": "15.46%",
          "budgetAmountWan": "597994.15万元"
        },
        {
          "industryName": "工程准备活动",
          "projectCount": 638,
          "projectShare": "9.85%",
          "budgetAmountWan": "7237780.99万元"
        },
        {
          "industryName": "电气安装",
          "projectCount": 624,
          "projectShare": "9.64%",
          "budgetAmountWan": "289932万元"
        },
        {
          "industryName": "架线和管道工程建筑",
          "projectCount": 224,
          "projectShare": "3.46%",
          "budgetAmountWan": "99260.4万元"
        },
        {
          "industryName": "其他",
          "projectCount": 62,
          "projectShare": "0.96%",
          "budgetAmountWan": "34531.93万元"
        }
      ],
      "winStatistics": []
    },
    "relationshipSummary": {
      "contactPersonCount": "327",
      "customerProjectCount": "47",
      "supplierProjectCount": "662"
    },
    "dataStatus": {
      "baseInfoAvailable": true,
      "projectStatisticsAvailable": true,
      "contactsAvailable": true,
      "customersAvailable": true,
      "suppliersAvailable": true
    }
  },
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---
