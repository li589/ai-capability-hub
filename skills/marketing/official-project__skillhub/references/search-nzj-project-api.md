## POST 拟在建项目信息搜索列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/searchNZJProjectApi?key=***`

**说明：** 按关键词、地区和发布时间分页搜索拟在建项目信息

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| startDate | string | 是 | 2025-07-20 23:00:00 | 拟在建信息发布时间开始时间，格式 yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| endDate | string | 是 | 2025-07-25 23:59:59 | 拟在建信息发布时间结束时间，格式 yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| pageId | integer | 是 | 1 | 当前页码 |
| pageNumber | integer | 是 | 20 | 每页记录数，此值不要超过50,设为0时仅返回结果数量，即total值 |
| searchType | integer | 是 | 3 | 搜索类型：1=智能模糊，2=精准，3=高级 |
| keyword | string | 否 | 工程\|空调 | 搜索关键词： - 多个关键词”同时出现”用空格分隔 - 多个关键词”或关系”用竖线分隔。 -包含竖线，总长度不得超过300个字符 |
| excludeKW | string | 否 | - | 排除关键词，多个用竖线分隔。包含竖线，总长度不得超过150个字符 |
| inCludeKW | string | 否 | - | 结果必含关键词，多个用竖线分隔。 注意inCludeKW不要和keyword有相同的关键词，inCludeKW，长度较短。 -包含竖线，总长度不得超过150个字符 |
| searchMode | integer | 否 | 1 | 搜索字段模式：1=全部，2=仅标题，3=仅内容；默认值：1； |
| areaCode | object | 否 | - | 地区筛选条件，区域编码均为6位数字字符串；传递哪些编码，就查询哪些编码对应的数据；proviceCodeList 传 ["0"] 时表示查询全国 |
| areaCode.proviceCodeList | array | 否 | - | 省级地区编码列表，均为6位数字字符串；传入哪些省编码就查询哪些省；传 ["0"] 表示全国；多个使用 “，”拼接； |
| areaCode.cityCodeList | array | 否 | - | 市级地区编码列表，均为6位数字字符串；传入哪些市编码就查询哪些市；多个使用 “，”拼接； |
| areaCode.countyCodeList | array | 否 | - | 区县地区编码列表，均为6位数字字符串；传入哪些区县编码就查询哪些区县；多个使用 “，”拼接； |

### 请求示例

```json
{
  "startDate": "2025-07-20 23:00:00",
  "endDate": "2025-07-25 23:59:59",
  "pageId": 1,
  "pageNumber": 20,
  "searchType": 3,
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
  }
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| state | integer | 接口响应状态码（1=成功） |
| msg | string | 接口响应提示信息 |
| count | integer | 统计数量标识，当前返回固定0 |
| returnValue | any | 通用返回值字段，当前为null无数据 |
| returnvalue | any | 小写别名返回值字段，当前为null无数据 |
| subCode | string | 业务侧编码（0000000000=业务成功） |
| subMsg | string | 业务侧响应提示信息 |
| data | object | 业务分页及列表总数据对象 |
| data.costTime | string | 搜索耗时（单位毫秒），null表示未统计耗时 |
| data.total | integer | 符合关键词条件的全部数据总条数 |
| data.pageId | integer | 当前请求页码ID |
| data.pageNumber | integer | 分页页码序号 |
| data.startDate | string | 实际搜索开始时间，格式 yyyy-MM-dd HH:mm:ss |
| data.endDate | string | 实际搜索结束时间，格式 yyyy-MM-dd HH:mm:ss |
| data.hasNext | boolean | 是否存在下一页：true=有下一页，false=无 |
| data.seKeyWords | string | 搜索关键词，用于页面关键词标红匹配 |
| data.data | array | 项目列表数据数组 |
| data.data[].id | integer | 项目ID |
| data.data[].title | string | 项目标题，包含HTML标红样式标签 |
| data.data[].summary | string | 项目摘要描述，含HTML关键词标红标签 |
| data.data[].publishTime | string | 项目发布时间，格式yyyy-MM-dd HH:mm:ss |
| data.data[].proviceCode | string | 省份行政区域编码 |
| data.data[].cityCode | string | 地市行政区域编码 |
| data.data[].countyCode | string | 区县行政区域编码，null表示无区县级别 |
| data.data[].collectWebID | integer | 采集来源站点ID，null表示无来源站点 |
| data.data[].hasFile | integer | 是否附带附件：0=无附件，1=有附件 |

### 响应示例

```json
{
  "data": {
    "costTime": null,
    "total": 2300,
    "pageId": 1,
    "pageNumber": 0,
    "startDate": "2026-05-01 00:00:00",
    "endDate": "2026-05-14 23:59:59",
    "hasNext": true,
    "data": [
      {
        "id": 10777554,
        "title": "中国电信新疆公司2026年5G七期室外分布系统项目工程、5803工程",
        "summary": "880MHz,天线架设方式简易支架;57、肿瘤<span style='color:red;'>医院</span>门口美化塔,,位于苏州路肿瘤<span style='color:red;'>医院</span>门口美化塔,经度87.567123",
        "publishTime": "2026-05-13 17:08:11",
        "proviceCode": "650000",
        "cityCode": "650100",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 1.1517801,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777542,
        "title": "湖北知美医疗美容项目",
        "summary": "中应当填报环境影响登记表的建设项目,属于第108 <span style='color:red;'>医院</span>",
        "publishTime": "2026-05-13 17:07:36",
        "proviceCode": "420000",
        "cityCode": "420300",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 2.7806609,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777506,
        "title": "四会卓盛专科门诊部口腔CT射线装置应用项目",
        "summary": "（平方米） 826 建设单位 四会卓盛<span style='color:red;'>医院</span>管理有限公司,承诺: 四会卓盛<span style='color:red;'>医院</span>管理有限公司 吴卓兴承诺所填写各项内容真实",
        "publishTime": "2026-05-13 17:05:03",
        "proviceCode": "440000",
        "cityCode": "441200",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 4.5084248,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777428,
        "title": "新建DR机房",
        "summary": "平方米） 24.8 建设单位 播州宁康精神病<span style='color:red;'>医院</span>,承诺: 播州宁康精神病<span style='color:red;'>医院</span> 杨鑫承诺所填写各项内容真实",
        "publishTime": "2026-05-13 17:02:15",
        "proviceCode": "520000",
        "cityCode": "520300",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 4.6287374,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777416,
        "title": "澄城木槿医疗美容有限公司医疗美容诊所",
        "summary": "中应当填报环境影响登记表的建设项目,属于第108 <span style='color:red;'>医院</span>",
        "publishTime": "2026-05-13 17:01:57",
        "proviceCode": "610000",
        "cityCode": "610500",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 3.0994017,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777413,
        "title": "镇雄县场坝镇卫生院新增一台便携式数字X射线装置",
        "summary": "一、污染防治措施1、防护用品和监测仪器:<span style='color:red;'>医院</span>已为放射工作人员配备个人剂量计",
        "publishTime": "2026-05-13 17:01:55",
        "proviceCode": "530000",
        "cityCode": "530600",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 2.644681,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777346,
        "title": "蕲春县赤东镇竹瓦卫生院新建射线装置（CT）应用项目",
        "summary": "建设内容及规模 一、建设内容<span style='color:red;'>医院</span>新增射线装置应用,5、防护用品和监测仪器:<span style='color:red;'>医院</span>已配备个人剂量计",
        "publishTime": "2026-05-13 16:59:21",
        "proviceCode": "420000",
        "cityCode": "421100",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 3.7633843,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777345,
        "title": "上海市奉贤区中心<span style='color:red;'>医院</span>新增1枚V类放射源Sr-90项目",
        "summary": "项目名称 上海市奉贤区中心<span style='color:red;'>医院</span>新增1枚V类放射源,平方米） 6 建设单位 上海市奉贤区中心<span style='color:red;'>医院</span>",
        "publishTime": "2026-05-13 16:59:20",
        "proviceCode": "310000",
        "cityCode": "310100",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 6.035365,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777314,
        "title": "辽宁中爱益友宠物<span style='color:red;'>医院</span>盘锦三部",
        "summary": "项目名称 建设地点 （平方米） 建设单位 ／ 法定代表人 联系人 联系电话 项目投资(万元) 环保投...",
        "publishTime": "2026-05-13 16:55:47",
        "proviceCode": "210000",
        "cityCode": "211100",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 4.584847,
        "browseStatus": 0,
        "folowUpStatus": 0
      },
      {
        "id": 10777211,
        "title": "原宜昌市夷陵区中医<span style='color:red;'>医院</span>(安康<span style='color:red;'>医院</span>)改造项目",
        "summary": "项目名称: 原宜昌市夷陵区中医<span style='color:red;'>医院</span>(安康<span style='color:red;'>医院</span>,(安康<span style='color:red;'>医院</span>)改造项目项目环境影响评价文件",
        "publishTime": "2026-05-13 16:54:02",
        "proviceCode": "420000",
        "cityCode": "420500",
        "countyCode": null,
        "collectWebID": null,
        "hasFile": 0,
        "score": 7.056516,
        "browseStatus": 0,
        "folowUpStatus": 0
      }
    ],
    "seKeyWords": "医院"
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
