## POST 招中标合同数据搜索列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/searchProjectContactApi?key=***`

**说明：** 按关键词、地区、行业、时间和合同区间搜索合同数据列表。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| startDate | string | 是 | 2025-07-20 23:00:00 | 发布时间开始时间，格式 yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| endDate | string | 是 | 2025-07-25 23:59:59 | 发布时间结束时间，格式 yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| pageId | integer | 是 | 1 | 当前页码 |
| pageNumber | integer | 是 | 20 | 每页记录数，此值不要超过100,设为0时仅返回结果数量，即total值 |
| searchType | integer | 是 | 1 | 搜索类型：1=智能模糊，2=精准，3=高级 |
| keyword | string | 否 | 工程\|空调 | 搜索关键词： - 多个关键词”同时出现”用空格分隔 - 多个关键词”或关系”用竖线分隔。 -包含竖线，总长度不得超过300个字符 |
| excludeKW | string | 否 | - | 排除关键词，多个用竖线分隔。包含竖线，总长度不得超过50个字符 |
| inCludeKW | string | 否 | - | 结果必含关键词，多个用竖线分隔。 注意inCludeKW不要和keyword有相同的关键词，inCludeKW，长度较短。 -包含竖线，总长度不得超过50个字符 |
| searchMode | integer | 否 | 1 | 搜索字段模式：1=全部，2=仅标题，3=仅内容 |
| areaCode | object | 否 | - | 地区筛选条件，区域编码均为6位数字字符串；传递哪些编码，就查询哪些编码对应的数据；proviceCodeList 传 ["0"] 时表示查询全国 |
| areaCode.proviceCodeList | array | 否 | - | 省级地区编码列表，均为6位数字字符串；传入哪些省编码就查询哪些省；传 ["0"] 表示全国；多个使用 “，”拼接； |
| areaCode.cityCodeList | array | 否 | - | 市级地区编码列表，均为6位数字字符串；传入哪些市编码就查询哪些市；多个使用 “，”拼接； |
| areaCode.countyCodeList | array | 否 | - | 区县地区编码列表，均为6位数字字符串；传入哪些区县编码就查询哪些区县；多个使用 “，”拼接； |
| industryCode | object | 否 | - | 行业分类筛选条件 |
| industryCode.firstCodeList | array | 否 | - | 一级行业编码列表；示例：{"firstCodeList":["Q"]} |
| industryCode.secondCodeList | array | 否 | - | 二级行业编码列表；示例：{"secondCodeList":["Q83"]} |
| industryCode.thirdCodeList | array | 否 | - | 三级行业编码列表；示例：{"thirdCodeList":["Q831"]} |
| contractEndMin | string | 否 | 2025-07-20 | 合同截止日期最小值，格式 yyyy-MM-dd |
| contractEndMax | string | 否 | 2025-12-25 | 合同截止日期最大值，格式 yyyy-MM-dd |
| purchaseTypeID | string | 否 | -100 | 采购分类ID，参考枚举值-码表 (招中标信息采购分类)；默认值：“-100”，表示查询全部分类；多个类型使用","拼接； |
| partAName | string | 否 | - | 甲方（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| partBName | string | 否 | - | 乙方（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| agentName | string | 否 | - | 代理机构（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| companyName | string | 否 | 职业技术学院 | 公司名字，支持模搜索，多个以英文逗号分隔,适用于不确定公司的角色（甲方、乙方、代理机构） |
| projectMoneyMin | string | 否 | 100000 | 项目金额极小值，单位人民币：元；为空表示：不限； |
| projectMoneyMax | string | 否 | 1000000 | 项目金额极大值，单位人民币：元；为空表示：不限； |
| fileFlag | integer | 否 | -1 | 附件标识：-1=无要求，0=无附件，1=有附件 |

### 请求示例

```json
{
  "startDate": "2025-07-20 23:00:00",
  "endDate": "2025-07-25 23:59:59",
  "pageId": 1,
  "pageNumber": 20,
  "searchType": 1,
  "keyword": "工程|空调",
  "excludeKW": "",
  "inCludeKW": "",
  "searchMode": 1,
  "areaCode": {
    "proviceCodeList": [
      "0"
    ],
    "cityCodeList": [],
    "countyCodeList": []
  },
  "industryCode": {
    "firstCodeList": [],
    "secondCodeList": [],
    "thirdCodeList": []
  },
  "contractEndMin": "2025-07-20",
  "contractEndMax": "2025-12-25",
  "purchaseTypeID": "-100",
  "partAName": "",
  "partBName": "",
  "agentName": "",
  "companyName": "职业技术学院",
  "projectMoneyMin": "100000",
  "projectMoneyMax": "1000000",
  "fileFlag": -1
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code（0000000000=成功） |
| subMsg | string | 业务侧 msg |
| data | object |  |
| data.costtime | string | 搜索耗费时长（单位：毫秒），null表示未统计 |
| data.total | integer | 符合条件的搜索结果总数 |
| data.pageID | integer | 当前页码（与请求参数一致） |
| data.pageNumber | integer | 每页记录数（与请求参数一致） |
| data.startdate | string | 实际搜索开始时间（格式：YYYY-MM-DD HH:mm:ss） |
| data.enddate | string | 实际搜索结束时间（格式：YYYY-MM-DD HH:mm:ss） |
| data.hasNext | boolean | 是否还有下一页：true=有，false=无 |
| data.seKeyWords | string | UI标红用的关键词（匹配搜索关键词） |
| data.data | array | 搜索结果数据集合（数组形式，按dataSetType返回对应结构） |
| data.data[].id | integer | 信息ID |
| data.data[].title | string | 信息标题（含HTML高亮标签，用于关键词标红） |
| data.data[].publishTime | string | 发布时间（格式：YYYY-MM-DD HH:mm:ss） |
| data.data[].content | string | 内容（含HTML高亮标签） |
| data.data[].proviceCode | string | 省代码 |
| data.data[].cityCode | string | 市代码 |
| data.data[].countyCode | string | 区/县代码（null表示无） |
| data.data[].hasFile | integer | 是否有附件：0=无，1=有 |
| data.data[].projectMoney | string | 项目金额（带单位，如”16.8万”） |
| data.data[].projectClassID | string | 项目子分类ID-新版 |
| data.data[].purchaseTypeID | string | 采购类别ID |
| data.data[].industryCodeList | array | 行业分类code数组 |
| data.data[].projectCycle | array | 项目周期，有多个标段时，可能会有多个项目周期，一般一个值 |
| data.data[].partAInfo | array | 甲方(公司)信息集合 |
| data.data[].partBInfo | array | 乙方(公司)信息集合 |
| data.data[].contractStartDate | string | 合同开始时间（格式：YYYY-MM-DD） |
| data.data[].contractEndDate | string | 合同到期时间（格式：YYYY-MM-DD） |

### 响应示例

```json
{
  "data": {
    "costTime": null,
    "total": 29,
    "pageId": 1,
    "pageNumber": 1,
    "startDate": "2025-07-20 23:00:00",
    "endDate": "2025-07-25 23:59:59",
    "hasNext": true,
    "data": [
      {
        "id": 275985695,
        "title": "云南农业职业技术学院新农电商直播实训室及茭菱校区体育训练区改造<span style='color:red;'>工程</span>项目合同",
        "publishTime": "2025-07-25 23:21:51",
        "content": "五、合同主体 采购人（甲方）: 云南农<span style='color:red;'>业</span><span style='color:red;'>职业</span><span style='color:red;'>技术学院</span>,25 九、其他补充事宜: 附件: 云南农<span style='color:red;'>业</span><span style='color:red;'>职业</span><span style='color:red;'>技术学院</span>新农电商直播实训室及茭菱校区体育训练区改造<span style='color:red;'>工程</span>项目合同",
        "proviceCode": "530000",
        "cityCode": "530100",
        "countyCode": null,
        "hasFile": 1,
        "score": 38.91352,
        "projectMoney": "54.68万",
        "projectClassID": "3",
        "purchaseTypeID": "2",
        "industryCodeList": [
          "E501",
          "I649",
          "R882"
        ],
        "projectCycle": [
          "30天"
        ],
        "partAInfo": [
          {
            "name": "云南农业职业技术学院",
            "contactPhone": [
              "0871-68875284"
            ],
            "email": []
          }
        ],
        "partBInfo": [
          {
            "name": "金狐建筑装饰工程有限公司",
            "contactPhone": [
              "15125247808"
            ],
            "email": null
          }
        ],
        "contractStartDate": "2025-07-25",
        "contractEndDate": "2025-08-25"
      }
    ],
    "seKeyWords": "工程,空调"
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
