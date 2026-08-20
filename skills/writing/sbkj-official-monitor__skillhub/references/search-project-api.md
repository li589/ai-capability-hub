## POST 招中标信息搜索列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/searchProjectApi?key=***`

**说明：** 按关键词、地区、行业、时间和金额、企业名字等条件搜索招标采购信息列表。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| startDate | string | 是 | 2025-07-20 23:00:00 | 招中标信息发布开始日期，精确到天，格式 yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| endDate | string | 是 | 2025-07-25 23:59:59 | 招中标信息发布结束日期，精确到天，格式yyyy-MM-dd或yyyy-MM-dd HH:mm:ss |
| pageId | integer | 是 | 1 | 当前页码 |
| pageNumber | integer | 是 | 20 | 每页记录数，此值不要超过50,设为0时仅返回结果数量，即total值 |
| searchType | integer | 是 | 1 | 搜索类型：1=智能模糊，2=精准，3=高级 |
| keyword | string | 否 | 工程\|空调 | 搜索关键词： - 多个关键词”同时出现”用空格分隔 - 多个关键词”或关系”用竖线分隔。 -包含竖线，总长度不得超过300个字符 |
| excludeKW | string | 否 | - | 排除关键词，多个用竖线分隔。包含竖线，总长度不得超过150个字符 |
| inCludeKW | string | 否 | - | 结果必含关键词，多个用竖线分隔。 注意inCludeKW不要和keyword有相同的关键词，inCludeKW，长度较短。 -包含竖线，总长度不得超过150个字符 |
| projectClassID | string | 否 | -100 | 招中标信息分类ID，参考枚举值-码表 (招中标信息14个信息分类)；多个以英文逗号分隔； |
| searchMode | integer | 否 | 1 | 搜索字段模式，1：全部（标题+内容），2：搜索标题，3：搜索内容；默认值：1 |
| areaCode | object | 否 | - | 地区筛选条件，区域编码均为6位数字字符串；传递哪些编码，就查询哪些编码对应的数据；proviceCodeList 传 ["0"] 时表示查询全国 |
| areaCode.proviceCodeList | array | 否 | - | 省级地区编码列表，均为6位数字字符串；传入哪些省编码就查询哪些省；传 0 表示全国；多个使用 “，”拼接； |
| areaCode.cityCodeList | array | 否 | - | 市级地区编码列表，均为6位数字字符串；传入哪些市编码就查询哪些市；多个使用 “，”拼接； |
| areaCode.countyCodeList | array | 否 | - | 区县地区编码列表，均为6位数字字符串；传入哪些区县编码就查询哪些区县；多个使用 “，”拼接； |
| industryCode | object | 否 | - | 行业分类筛选条件 |
| industryCode.firstCodeList | array | 否 | - | 一级行业编码列表；示例：{"firstCodeList":["Q"]} |
| industryCode.secondCodeList | array | 否 | - | 二级行业编码列表；示例：{"secondCodeList":["Q83"]} |
| industryCode.thirdCodeList | array | 否 | - | 三级行业编码列表；示例：{"thirdCodeList":["Q831"]} |
| contractEndMin | string | 否 | 2025-07-20 | 合同截至日期查询极小值，精确到天，格式 yyyy-MM-dd |
| contractEndMax | string | 否 | 2025-12-25 | 合同截至日期查询极大值，精确到天，格式 yyyy-MM-dd |
| purchaseTypeID | string | 否 | -100 | 采购分类ID，参考枚举值-码表 (招中标信息采购分类)；默认值：“-100”，表示查询全部分类；多个以英文逗号分隔; |
| partAName | string | 否 | - | 甲方（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| partBName | string | 否 | - | 乙方（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| agentName | string | 否 | - | 代理机构（公司）名字集合，支持模搜索，多个以英文逗号分隔 |
| projectMoneyMin | integer | 否 | 100000 | 项目金额最小值；单位人民币：元；为空则表示不限 |
| projectMoneyMax | integer | 否 | 1000000 | 项目金额最大值；单位人民币：元；为空则表示不限 |
| fileFlag | integer | 否 | -1 | 附件标识：-1=无要求，0=无附件，1=有附件 |
| companyName | string | 否 | 湖北会计师事务所 | 公司名字，支持模糊搜索，多个以英文逗号分隔,适用于不确定公司的角色（甲方、乙方、代理机构） |

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
  "projectClassID": "-100",
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
  "projectMoneyMin": "100000",
  "projectMoneyMax": "1000000",
  "fileFlag": -1,
  "companyName": "湖北会计师事务所"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code（0000000000=成功） |
| subMsg | string | 业务侧 msg |
| data | object | 业务数据结果（分页配置+搜索结果数据） |
| data.costtime | string | 搜索耗费时长（单位：毫秒），null表示未统计 |
| data.total | integer | 搜索结果总数 |
| data.pageId | integer | 当前页码 |
| data.pageNumber | integer | 每页记录数 |
| data.startdate | string | 实际搜索开始时间（格式：yyyy-MM-dd HH:mm:ss） |
| data.enddate | string | 实际搜索结束时间（格式：yyyy-MM-dd HH:mm:ss） |
| data.hasNext | boolean | 是否还有下一页：true=有，false=无 |
| data.seKeyWords | string | UI标红用的关键词（匹配搜索关键词） |
| data.data | array | 搜索结果数据集合（数组形式，按dataSetType返回对应结构） |
| data.data[].id | integer | 项目ID |
| data.data[].newsTypeID | string | 已弃用，老版本分类ID，信息类别(1招标，2中标，3:合同，6：意向公开，5：拍租公告) |
| data.data[].title | string | 信息标题（含HTML高亮标签，用于关键词标红） |
| data.data[].publishTime | string | 项目发布时间（格式：yyyy-MM-dd HH:mm:ss） |
| data.data[].content | string | 命中高亮内容（含HTML高亮标签，非完整内容） |
| data.data[].proviceCode | string | 省代码 |
| data.data[].cityCode | string | 市代码 |
| data.data[].countyCode | string | 区/县代码（null表示无） |
| data.data[].hasFile | integer | 是否有附件：0=无，1=有 |
| data.data[].score | number | 文档得分 |
| data.data[].projectMoney | string | 项目金额（带单位，如”16.8万”） |
| data.data[].projectClassID | string | 2025版项目子分类ID |
| data.data[].purchaseTypeID | string | 采购类别ID |
| data.data[].industryCodeList | array | 行业分类code数组 |
| data.data[].partANameList | array | 甲方名称列表（多个用数组存储） |
| data.data[].partBNameList | array | 乙方名称列表（多个用数组存储） |

### 响应示例

```json
{
  "data": {
    "costTime": null,
    "total": 2,
    "pageId": 1,
    "pageNumber": 20,
    "startDate": "2025-07-20 23:00:00",
    "endDate": "2025-07-25 23:59:59",
    "hasNext": false,
    "data": [
      {
        "id": 304974237,
        "newsTypeID": 2,
        "title": "武汉经济技术开发区（汉南区）财政局武汉经开区财政局审计服务结果公告",
        "publishTime": "2025-07-25 23:42:15",
        "content": "武汉经开区财政局审计服务 四、中标（成交）信息 供应商名称:<span style='color:red;'>湖北</span>中定诚<span style='color:red;'>会计师事务</span><span style='color:red;'>所</span>,84852250 2、采购代理机构信息 名 称:<span style='color:red;'>湖北</span>大有<span style='color:red;'>工程</span>咨询有限公司",
        "proviceCode": "420000",
        "cityCode": "420100",
        "countyCode": "420107000000",
        "hasFile": 0,
        "score": 49.6299,
        "projectMoney": "49.77万",
        "projectClassID": "2",
        "purchaseTypeID": "1",
        "industryCodeList": [
          "S912",
          "L723"
        ],
        "partANameList": [
          "武汉经济技术开发区财政局"
        ],
        "partBNameList": [
          "湖北中定诚会计师事务所（普通合伙）"
        ],
        "contractEndDate": "2025-08-15 00:00:00"
      },
      {
        "id": 297885479,
        "newsTypeID": 2,
        "title": "武汉经济技术开发区（汉南区）财政局武汉经开区财政局审计服务结果公告",
        "publishTime": "2025-07-25 01:17:11",
        "content": "武汉经开区财政局审计服务 四、中标（成交）信息 供应商名称:<span style='color:red;'>湖北</span>中定诚<span style='color:red;'>会计师事务</span><span style='color:red;'>所</span>,84852250 2、采购代理机构信息 名 称:<span style='color:red;'>湖北</span>大有<span style='color:red;'>工程</span>咨询有限公司",
        "proviceCode": "420000",
        "cityCode": "420100",
        "countyCode": "420107000000",
        "hasFile": 0,
        "score": 49.650814,
        "projectMoney": "49.77万",
        "projectClassID": "2",
        "purchaseTypeID": "1",
        "industryCodeList": [
          "S912",
          "L723"
        ],
        "partANameList": [
          "武汉经济技术开发区财政局"
        ],
        "partBNameList": [
          "湖北中定诚会计师事务所（普通合伙）"
        ],
        "contractEndDate": "2025-08-15 00:00:00"
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
