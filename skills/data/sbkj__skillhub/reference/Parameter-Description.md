# 接口文档

## 服务地址
生产环境：[https://gate.gov-bid.com/outer-gateway](https://gate.gov-bid.com/outer-gateway)

## 枚举值-码表

## 1、客户端系统类别 systemType

| 操作系统名称      | 枚举名称 | 枚举值 |
|------------------|---------|------|
| 安卓系统          | android | 0    |
| 苹果系统          | ios | 1    |
| Windows Phone系统|wp | 2    |
| Windows系统      | win | 3    |
| H5浏览器         | h5 | 4    |
| 微信小程序       | wxapplet | 5    |
| 微信公众号       | wxoa | 6    |
| 百度小程序       | bdapplet | 7    |
| 抖音小程序       |douyinapplet  | 8    |
| 华为快应用       | hweiquickapp | 9    |
| IpadOS          | ipados | 10   |
| 鸿蒙OS          | harmonyos | 11   |

## 2、招中标信息14个信息分类

| ID | 分类名称            |
|----|-----------------|
| 1  | 公开招标        |
| 2  | 成交结果        |
| 3  | 合同公告        |
| 4  | 意向公开        |
| 5  | 答疑变更        |
| 6  | 候选人公示      |
| 7  | 开标公示        |
| 8  | 重新招标        |
| 11 | 流标废标        |
| 18 | 结果变更        |
| 26 | 拍租公告        |
| 28 | 竞争性谈判      |
| 29 | 竞争性磋商      |
| 30 | 单一来源采购    |
| 31 | 其它            |

## 3、招中标信息采购分类

| ID | 分类名称    |
|----|---------|
| 0  | 其它类  |
| 1  | 服务类  |
| 2  | 工程类  |
| 3  | 货物类  |

## 4、国家统计局企业行业码表
文件名：CompanyIndustry.csv
下载地址请复制整串到浏览器打开：
http://faq.zhvac.com/server/index.php?s=/api/attachment/visitFile&sign=ffc15fc5e747855791f33d0c48754b45

## 5、国家地理位置码表
文件名：Area.csv
下载地址请复制整串到浏览器打开：
http://faq.zhvac.com/server/index.php?s=/api/attachment/visitFile&sign=c40c87a3e4599cbff592c7facba690d9


---

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

## POST 招中标信息详情（不含结构化数据）

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getZTBProjectDetail?key=***`

**说明：** 根据项目 ID 和发布时间获取招中标项目信息正文详情，不包含结构化字段。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | integer | 是 | 337580128 | 项目ID |
| publishTime | string | 是 | 2026-07-06 18:11:40 | 项目发布时间，格式： yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss； |

### 请求示例

```json
{
  "id": 337580128,
  "publishTime": "2026-07-06 18:11:40"
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
| data.id | integer | 项目ID |
| data.newsTypeID | integer | 项目信息类别ID（老版分类）：1=招标信息，2=中标信息，3=采购合同，4=采购意向，5=拍卖信息 |
| data.title | string | 项目信息标题 |
| data.content | string | 项目信息内容，带html标签（标讯信息正文内容） |
| data.publishTime | string | 项目发布时间 格式：yyyy-MM-dd HH:mm:ss |
| data.proviceCode | string | 项目归属地code-省code |
| data.cityCode | string | 项目归属地code-市code |
| data.countyCode | string | 项目归属地code-区/县code |
| data.projectMoney | string | 项目金额（展示用，如”32.32万”），优先级：合同金额>中标金额>预算金额，默认0 |
| data.projectClassID | string | 2025版14个项目子分类ID ，详见码表 |
| data.projectClassName | string | 项目子分类名称（可能为null） |
| data.purchaseType | string | 采购类别ID：0=其它，1=服务类，2=工程类，3=货物类 |
| data.industryName | string | 信息行业分类名称，多个以英文逗号分隔 |
| data.partAName | string | 甲方名称，多个以英文逗号分隔 |
| data.partBName | string | 乙方名称，多个以英文逗号分隔 |
| data.agentName | string | 代理机构名称，多个以英文逗号分隔 |
| data.projectFiles | array | 项目附件列表 |
| data.projectFiles[].projectFileID | integer | 项目信息附件ID |
| data.projectFiles[].name | string | 信息附件名称 |
| data.projectFiles[].publishTime | string | 项目信息发布时间 格式：yyyy-MM-dd HH:mm:ss |
| returnValue | string | 单个值响应结果 |

### 响应示例

```json
{
  "data": {
    "id": 337580128,
    "newsTypeID": 1,
    "newsTypeName": "招标信息",
    "title": "聊城市茌平区非电网直供电小区供配电设施土建部分改造项目（2026年）答疑澄清公示",
    "content": "<div> <p><span><span>聊城市茌平区非电网直供电小区供配电设施土建部分改造项目（</span><span>2026年）答疑澄清公示</span></span></p><p><span><span>一、项目名称：聊城市茌平区非电网直供电小区供配电设施土建部分改造项目（</span><span>2026年）</span></span></p><p><span><span>二、招标编号：</span><span>XCPJSGC-2026-016</span></span></p><p><span><span>三</span> <span>、澄清答疑内容：</span></span><span><span>公告中标段划分：共分三个标段：标段一：中心街以西、孟秋路以北，中心街以东、振兴东路以北（其中包括：建工家属楼、造纸东厂家属楼、老交通局家属楼、信鸽面业家属楼、棉麻公司家属楼、三九味精家属楼、逸翠园、齐韩民心工程家属区、第四加油站家属院、恒达食品公司家属院小区、青年公寓小区、泰和广场小区、金帝家园、都市新村、信发步行街、水木清华（及</span><span>14号、.15.号、16号楼）、康安苑、教师新村小区、阳光时代小区）；标段二：南环路以南，中心街以东、振兴东路以南（其中包括：翡翠郡小区、技术监督局小区、翡翠园、翡翠龙城、安居康城、东方新天地小区、领秀苑、滨河花园、中心花园华府、工商银行家属楼、阳光嘉苑、林周小区、纸厂家属楼、天鹅湖小区）；标段三：中心街以西、新政西路以南，龙山街以西、孟秋路以南（其中包括：实验中学（职高）家属院、水岸豪庭、民政局小区、交通委馨祥嘉苑一期、交通委馨祥嘉苑二期、正泰集团26号楼、杏林小区、名居苑小区、美景家园、西关村村民安置房、金都花园一期、装饰公司家属楼、金都花园一期、金都花园、正泰家园1号小区、嘉丰家属院、东家后新区），其中标段一中少了水木清华的</span></span><span><span>14号、15号、16号楼）</span></span><span><span>。</span></span></p><p><span><span>四、请各投标人自行下载变更后的招标文件，如因未及时下载造成的一切后果，自行承担。变更后的招标文件详见答疑澄清文件。</span></span></p><p><span><span>五、联系方式</span></span></p><table width='606'><tbody><tr ><td width='101' valign='center' ><p><span><span><span>招</span> <span>标</span><span> </span><span>人</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span>聊城市茌平区宜居置业有限公司</span></span></p></td><td width='119' valign='center' ><p><span><span><span>招标代理机构</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>山东昌盛项目管理有限公司</span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span><span>地址</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span><span>山东省聊城市</span></span><span><span>茌平区</span></span></span></p></td><td width='119' valign='center' ><p><span><span><span>地址</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span><span>聊城市茌平区枣乡街</span></span><span><span>19-6</span><span>号</span></span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span><span>邮编</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span>252100</span></span></p></td><td width='119' valign='center' ><p><span><span><span>邮编</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>252100</span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span><span>联系人</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span>刘新，马庆波</span></span></p></td><td width='119' valign='center' ><p><span><span><span>项目负责人</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>杨山山</span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span><span>电话</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span><span>0635-</span></span><span><span>4229056</span></span></span></p></td><td width='119' valign='center' ><p><span><span><span>电话</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>18806354639</span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span><span>传真</span></span><span><span>：</span></span></span></p></td><td width='189' valign='center' ><p><span><span>/</span></span></p></td><td width='119' valign='center' ><p><span><span><span>传真</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>/</span></span></p></td></tr><tr ><td width='101' valign='center' ><p><span><span>电子邮件：</span></span></p></td><td width='189' valign='center' ><p><span><span>/</span></span></p></td><td width='119' valign='center' ><p><span><span><span>电子邮件</span></span><span><span>：</span></span></span></p></td><td width='198' valign='center' ><p><span><span>cpchangsheng@163.com</span></span></p></td></tr></tbody></table><p><span><span>山东昌盛项目管理有限公司</span></span></p><p><span><span>2026年07月0</span></span><span><span>6</span></span><span><span>日</span></span></p><p></p></div> <li>  答疑文件正文.pdf</li><li>  工程量清单.pdf</li><li>  答疑说明文件.pdf</li>",
    "publishTime": "2026-07-06 18:11:40",
    "proviceCode": "370000",
    "proviceName": "山东省",
    "cityCode": "371500",
    "cityName": "聊城市",
    "countyCode": null,
    "countyName": null,
    "projectMoney": null,
    "projectClassID": "5",
    "projectClassName": "答疑变更",
    "purchaseType": "工程类",
    "industryName": "输配电及控制设备制造,电力供应,电气安装,房地产开发经营,住宅房屋建筑",
    "partAName": "聊城市茌平区宜居置业有限公司",
    "partBName": "",
    "agentName": "山东昌盛项目管理有限公司",
    "projectFiles": [
      {
        "projectFileID": 186555422,
        "name": "答疑说明文件pdf",
        "publishTime": "2026-07-06 18:11:40"
      },
      {
        "projectFileID": 186555424,
        "name": "答疑文件正文pdf",
        "publishTime": "2026-07-06 18:11:40"
      },
      {
        "projectFileID": 186555426,
        "name": "工程量清单pdf",
        "publishTime": "2026-07-06 18:11:40"
      }
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

## POST 招中标信息附件列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getZTBProjectFiles?key=***`

**说明：** 根据项目 ID 和发布时间获取项目附件列表及下载地址。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| projectId | integer | 是 | 332064410 | 项目ID |
| publishTime | string | 是 | 2026-06-08 14:32:50 | 项目发布时间，格式：yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss；不传时按当前日期计算搜索日期窗口 |

### 请求示例

```json
{
  "projectId": 332064410,
  "publishTime": "2026-06-08 14:32:50"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码 |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code |
| subMsg | string | 业务侧 msg |
| data | array | 项目附件列表（数组形式，无附件时返回空数组） |
| data[].projectFileID | integer | 项目信息附件ID |
| data[].projectID | string | 项目ID |
| data[].name | string | 附件名称（可能含省略号，完整名称需结合实际场景展示） |
| data[].url | string | 附件下载地址（可直接跳转下载） |
| data[].proviceCode | string | 项目归属地省代码（修正原文档类型错误，实际为地区编码字符串） |
| data[].cityCode | string | 项目归属地市代码 |
| data[].suffix | string | 文件后缀（如docx、pdf、jpg等，用于识别文件类型） |
| data[].size | number | 附件大小（单位：KB），null表示未获取到大小信息 |
| data[].publishTime | string | 项目发布时间（附件关联的项目发布时间）格式 yyyy-MM-dd HH:mm:ss |
| data[].state | string | 附件处理状态： 0=未下载，1=下载正常，2=下载失败， 3=附件太大（超过20M不下载），4=文件已损坏，5=url已失效 |
| data[].createTime | string | 附件创建时间 格式 yyyy-MM-dd HH:mm:ss |

### 响应示例

```json
{
  "data": [
    {
      "projectFileID": 183550184,
      "projectID": "332064410",
      "name": "c2211df44339911ae669...",
      "url": "https://cos.woyaobid.com/ztb-collectfiles/2026/06/08/c2211df44339911ae669-183550184.pdf",
      "proviceCode": "230000",
      "cityCode": "230800",
      "suffix": "pdf",
      "size": 199.95,
      "publishTime": "2026-06-08 14:32:50",
      "state": "1",
      "createTime": "2026-06-08 17:41:43"
    }
  ],
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

## POST 招中标信息搜索列表（AI专用、Agent专用）

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/SearchProjectForAI?key=***`

**说明：** 面向第三方 AI 模型的招标采购搜索接口，使用自然语言友好的筛选参数。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| startDate | string | 是 | 2026-06-03 | 起始日期(格式:yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss) |
| endDate | string | 是 | 2026-06-05 | 结束日期(格式:yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss) |
| pageId | integer | 是 | 1 | 当前页码 |
| pageNumber | integer | 是 | 10 | 每页记录数，此值不要超过100,设为0时仅返回结果数量，即total值 |
| keyword | string | 否 | 工程\|空调 | 搜索关键词： - 多个关键词”同时出现”用空格分隔 - 多个关键词”或关系”用竖线分隔 |
| excludeKW | string | 否 | - | 排除关键词，多个用竖线分隔 |
| inCludeKW | string | 否 | - | 必须包含关键词： - 多个关键词”或关系”用竖线分隔 |
| className | string | 否 | 招标信息 | 项目信息类别： 全部信息，招标信息，中标信息，合同信息，采购意向，拍租信息 多个类别用英文逗号分隔 |
| areaName | string | 否 | 武汉 | 地区名称 |
| companyName | string | 否 | 华中科技大学 | 参与招投标活动的企业名字，可以是甲方、乙方、代理机构 |

### 请求示例

```json
{
  "startDate": "2026-06-03",
  "endDate": "2026-06-05",
  "pageId": 1,
  "pageNumber": 10,
  "keyword": "办公家具|空调",
  "excludeKW": "",
  "inCludeKW": "",
  "className": "招标信息",
  "areaName": "武汉",
  "companyName": "华中科技大学"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口统一响应码 |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧code |
| subMsg | string | 业务侧msg |
| data | object | 业务数据结果 |
| data.costtime | string | 搜索耗费时长，单位，毫秒 |
| data.total | integer | 搜索结果总数 |
| data.pageId | integer | 当前页码 |
| data.pageNumber | integer | 每页记录数量 |
| data.startdate | string | 搜索开始时间(格式：yyyy-MM-dd HH:mm:ss) |
| data.enddate | string | 搜索结束时间(格式：yyyy-MM-dd HH:mm:ss) |
| data.hasNext | boolean | 是否还有下一页 |
| data.seKeyWords | string | Ui标红用的关键词 |
| data.data | array | 记录集合 |
| data.data[].id | integer | 项目ID |
| data.data[].newsTypeName | string | 信息类别 |
| data.data[].title | string | 信息标题(包含HTML高亮标签) |
| data.data[].publishTime | string | 项目发布时间(格式:YYYY-MM-DD HH:mm:ss) |
| data.data[].content | string | 招中标信息内容 |
| data.data[].areaName | string | 项目信息归属地名称 |
| data.data[].score | number | 搜索引擎对文章相关度打分 |
| data.data[].projectMoney | string | 项目金额(带单位，如”54.38万”) |
| data.data[].projectClass | string | 项目子分类名称 |
| data.data[].purchaseType | string | 项目采购分类名称 |
| data.data[].partAInfo | array | 甲方信息 |
| data.data[].partBInfo | array | 乙方信息 |
| data.data[].agencyInfo | array | 代理机构信息 |
| data.data[].siginUpStopDate | string | 报名截止时间(格式：yyyy-MM-dd) |
| data.data[].bidStartAddress | string | 开标地点 |
| data.data[].bidStartDate | string | 开标时间(格式：yyyy-MM-dd) |
| data.data[].collectUrl | string | 内容采集原网址 |
| data.data[].sbkjBidUrl | string | 世舶科技内容地址 |

### 响应示例

```json
{
  "data": {
    "costTime": null,
    "total": 20,
    "pageId": 1,
    "pageNumber": 0,
    "startDate": "2026-06-03 00:00:00",
    "endDate": "2026-06-05 23:59:59",
    "hasNext": true,
    "data": [
      {
        "id": 331801147,
        "newsTypeName": "招标信息",
        "projectName": "硬质利器盒",
        "title": "华中科技大学同济医学院附属同济医院硬质利器盒更正公告",
        "publishTime": "2026-06-05 16:59:15",
        "content": "1.采购人信息 名 称:<span style='color:red;'>华中科技大学</span>同济医<span style='color:red;'>学</span>院附属同济医院,2.采购代理机构信息 名 称:湖北路港<span style='color:red;'>工程</span>咨询有限公司",
        "areaName": "省：湖北省 市：武汉市",
        "sbkjBidUrl": "http://static.project.woyaobid.cn/ProjectInfo/20260605/77718245DE449994370.html",
        "collectUrl": "http://www.ccgp.gov.cn/cggg/zygg/gzgg/202606/t20260605_26695810.htm",
        "score": 52.73697,
        "projectMoney": null,
        "projectClass": "答疑变更",
        "purchaseType": "货物类",
        "partAInfo": [
          {
            "name": "华中科技大学同济医学院附属同济医院",
            "contactPhone": "027-83662896",
            "email": null
          }
        ],
        "partBInfo": [],
        "agencyInfo": [
          {
            "name": "湖北路港工程咨询有限公司",
            "contactPhone": "18162620221",
            "email": null
          }
        ],
        "siginUpStopDate": null,
        "bidStartAddress": null,
        "bidStartDate": "2026-06-11 00:00:00"
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

## POST AI重写招中标信息搜索条件

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/aiSearchSubmitPolling?key=***`

**说明：** 提交自然语言搜索请求并返回 requestKey，供后续轮询搜索条件重写结果。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| userQuery | string | 是 | 湖北近30天物业服务，工程建筑中标结果，金额500万以上 | 用户输入的自然语言搜索语句 |

### 请求示例

```json
{
  "userQuery": "湖北近30天物业服务，工程建筑中标结果，金额500万以上"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 解析响应信息 |
| subCode | string | 业务侧 code（0000000000=成功） |
| subMsg | string | 业务侧 msg |
| data | object | 业务数据结果 |
| data.requestKey | string | 请求唯一标识（MD5） |
| data.status | string | 处理中->processing,搜索条件重写完成->search_rewrite_done,地区解析完成->area_code_done,行业推理完成->industry_done,全部完成->completed,处理失败->failed |
| data.searchCondition | object |  |
| data.searchCondition.searchStartTime | string | 搜索开始时间，格式：yyyy-MM-dd |
| data.searchCondition.searchEndTime | string | 搜索结束时间，格式：yyyy-MM-dd |
| data.searchCondition.enterpriseName | string | 企业名称 |
| data.searchCondition.enterpriseIndustry | string | 企业所属行业 |
| data.searchCondition.subjects | array | 标的物或搜索主题 |
| data.searchCondition.projectClassIds | string | 信息类型；参考枚举值-码表 (招中标信息14个信息分类)；多个以英文逗号分隔； |
| data.searchCondition.purchaseTypeId | string | 采购分类 `0`=其他、`1`=服务类、`2`=工程类、`3`=货物类 |
| data.searchCondition.projectMoneyMin | number | 项目金额最小值；单位人民币：元； |
| data.searchCondition.projectMoneyMax | number | 项目金额最大值；单位人民币：元； |
| data.searchCondition.subcontractFlag | boolean | 是否分包 |
| data.industryCodes | array | 行业信息列表 |
| data.industryCodes[].firstCodeList | array | 一级行业编码列表 |
| data.industryCodes[].secondCodeList | array | 二级行业编码列表 |
| data.industryCodes[].thirdCodeList | array | 三级行业编码列表 |
| data.industryCodes[].fullTitle | string | 全路径标题（如：一级-二级-三级） |
| data.industryCodes[].minTitle | string | 最下级路径标题 |
| data.areaCode | object |  |
| data.areaCode.proviceCodeList | array | 省级编码列表 |
| data.areaCode.cityCodeList | array | 市级编码列表 |
| data.areaCode.countyCodeList | array | 区县编码列表 |
| data.errorMsg | string | 错误信息 |

### 响应示例

```json
// 搜索条件重写正在处理中，通过定时周期请求查看任务处理状态
{
    "msg": "ok",
    "code": 200,
    "data": {
        "requestKey": "b9adfa20ed6f28c68428af6568ec6e48_17",
        "status": "processing",
        "searchCondition": null,
        "areaCode": null,
        "industryCodes": null,
        "errorMsg": null
    },
    "errorData": null,
    "subCode": "0000000000",
    "subMsg": "ok",
    "returnValue": null
}


// 搜索条件重写完成后响应
{
    "msg": "ok",
    "code": 200,
    "data": {
        "requestKey": "a4c9b476d555cd6e35402cd9241c4f47_17",
        "status": "completed",
        "searchCondition": {
            "enterpriseName": null,
            "enterpriseIndustry": "物业服务/工程建筑",
            "subjects": [
                "物业服务",
                "工程建筑"
            ],
            "searchStartTime": "2026-06-29",
            "searchEndTime": "2026-07-29",
            "projectClassIds": null,
            "purchaseTypeId": "2",
            "projectMoneyMin": 5000000.00,
            "projectMoneyMax": 1000000000.00,
            "subcontractFlag": null
        },
        "areaCode": {
            "proviceCodeList": [
                "420000"
            ],
            "cityCodeList": [],
            "countyCodeList": []
        },
        "industryCodes": [
            {
                "firstCodeList": [],
                "secondCodeList": [],
                "thirdCodeList": [
                    "K702"
                ],
                "fullTitle": "房地产业-房地产业-物业管理",
                "minTitle": "物业管理"
            },
            {
                "firstCodeList": [],
                "secondCodeList": [],
                "thirdCodeList": [
                    "E489"
                ],
                "fullTitle": "建筑业-土木工程建筑业-其他土木工程建筑",
                "minTitle": "其他土木工程建筑"
            },
            {
                "firstCodeList": [],
                "secondCodeList": [],
                "thirdCodeList": [
                    "K701"
                ],
                "fullTitle": "房地产业-房地产业-房地产开发经营",
                "minTitle": "房地产开发经营"
            }
        ],
        "errorMsg": null
    },
    "errorData": null,
    "subCode": "0000000000",
    "subMsg": "ok",
    "returnValue": null
}
```

---

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

## POST 获取招中标信息采集源网址

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getCollectUrl?key=***`

**说明：** 根据招标 ID 和发布时间获取招中标项目信息原始采集网址。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | integer | 是 | 332023653 | 项目ID |
| publishTime | string | 是 | 2026-06-08 23:59:59 | 项目发布时间（格式 yyyy-MM-dd HH:mm:ss） |

### 请求示例

```json
{
  "id": 332023653,
  "publishTime": "2026-06-08 23:59:59"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口统一响应码 |
| msg | string | 接口层级响应描述 |
| data | string | 额外业务数据，默认为空 |
| returnValue | string | 采集源地址 |

### 响应示例

```json
{
  "data": null,
  "msg": "ok",
  "count": 0,
  "returnValue": "https://xvmec.com/lookzb?item=9c682b43-dd35-4978-98ad-16bbfee920fa&type=2",
  "returnvalue": "https://xvmec.com/lookzb?item=9c682b43-dd35-4978-98ad-16bbfee920fa&type=2",
  "subCode": "0000000000",
  "subMsg": "成功",
  "code": 200
}
```

---

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

## POST 拟在建项目详情

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getNZJProjectDetail?key=***`

**说明：** 根据拟在建信息ID和发布时间获取拟在建项目信息详情。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | integer | 是 | 11748734 | 项目ID |
| publishtime | string | 是 | 2026-06-07 17:07:32 | 项目发布时间，格式 yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss，如：2024-03-04 14:39:56 |

### 请求示例

```json
{
  "id": 11748734,
  "publishtime": "2026-06-07 17:07:32"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 接口响应提示信息 |
| count | integer | 列表页记录数老参数，当前返回固定0 |
| returnValue | any | 通用返回值字段，当前为null无数据 |
| subCode | string | 业务侧编码（0000000000=业务成功） |
| subMsg | string | 业务侧响应提示信息 |
| data | object | 拟在建项目详情业务数据对象 |
| data.proposeProjectID | integer | 项目ID |
| data.title | string | 拟在建项目信息标题 |
| data.content | string | 拟在建项目信息内容，可能包含HTML结构 |
| data.constructionCompany | string | 建设单位，null表示未提供 |
| data.proviceCode | string | 省份行政区域编码 |
| data.cityCode | string | 地市行政区域编码 |
| data.countyCode | string | 区县行政区域编码 |
| data.proviceName | string | 项目信息归属地省名称 |
| data.cityName | string | 项目信息归属地市名称 |
| data.countyName | string | 项目信息归属地区/县名称 |
| data.publishTime | string | 项目发布时间，格式yyyy-MM-dd HH:mm:ss |
| data.projectFiles | array | 项目附件数组 |
| data.projectFiles[].projectFileID | integer | 附件ID |
| data.projectFiles[].name | string | 附件名称 |
| data.projectFiles[].publishTime | string | 附件对应的信息发布时间，格式yyyy-MM-dd HH:mm:ss |

### 响应示例

```json
{
  "data": {
    "proposeProjectID": 11748734,
    "title": "来宾同泰新能源有限公司来宾市武宣县（覃超垣）30kW交流侧户用光伏发电项目",
    "content": "<div><div>项目基本信息<div></div><table><tr><th width='10%'>项目代码</th><td>2606-451323-04-01-451872</td><th width='10%'>项目名称</th><td width='40%'>来宾同泰新能源有限公司来宾市武宣县（覃超垣）30kW交流侧户用光伏发电项目</td></tr><tr><th>审核备类型</th><td>备案类项目</td><th>项目法人单位</th><td>来宾同泰新能源有限公司</td></tr></table></div><div></div><div>审批事项公示信息<div></div><table><tr><th width='20%'>审批部门</th><th width='25%'>审批事项</th><th width='10%'>办理结果</th><th width='10%'>办理时间</th><th width='20%'>审批文号</th></tr><tr><td>武宣县发展和改革局</td><td>【企业投资项目备案】《政府核准的投资项目目录》以外的企业投资项目备案---企业投资境内项目备案</td><td>办结（准予许可）</td><td>2026-06-07</td><td></td></tr></table></div><div></div><div>相关办理结果<div></div><table><tr><th width='20%'>审批部门</th><th width='25%'>审批事项</th><th width='10%'>办理结果</th><th width='10%'>办理时间</th><th width='20%'>审批文号</th></tr><tr><td>武宣县发展和改革局</td><td>【企业投资项目备案】《政府核准的投资项目目录》以外的企业投资项目备案---企业投资境内项目备案</td><td>受理</td><td>2026-06-07</td><td></td></tr><tr><td>武宣县发展和改革局</td><td>【企业投资项目备案】《政府核准的投资项目目录》以外的企业投资项目备案---企业投资境内项目备案</td><td>接件</td><td>2026-06-07</td><td></td></tr></table><table><tr><td></td></tr></table></div></div>",
    "constructionCompany": null,
    "proviceCode": "450000",
    "cityCode": "451300",
    "countyCode": "451323000000",
    "publishTime": "2026-06-07 17:07:32",
    "folowUpStatus": 0,
    "projectFiles": []
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

## POST 【AI模型训练定制化】LLM招中标项目信息结构化

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/ztbAiStructureInfo?key=***`

**说明：** 调用大模型接口对招中标项目信息标题和内容进行结构化抽取，座机号码补全区号，金额转化为人民币元，评标专家角色提取为职业、职务、专业方向等。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| messages | array | 否 | - | 对话消息数组，兼容OpenAI Chat Completions格式，通常包含system结构化规则和user标讯标题及内容 |
| messages[].role | string | 是 | system | 消息角色：system、user、assistant等 |
| messages[].content | string | 是 | 工程 | 消息内容；system中填写结构化规则，user中填写待结构化的标讯标题和正文内容 |
| max_tokens | integer | 否 | 2048 | 模型最大输出token数量 |
| temperature | number | 否 | 0 | 采样温度，0表示稳定输出 |
| top_p | number | 否 | 1 | 核采样参数，1表示不限制累计概率采样范围 |

### 请求示例

```json
{
  "messages": [
    {
      "role": "system",
      "content": "标讯信息数据结构化，座机号码要补全区号，金额要转化为人民币元，评标专家角色为其职业、职务、专业方向等。"
    },
    {
      "role": "user",
      "content": "中标（成交）结果公告 采购项目名称： 新庙镇沙塘学校信息化设备采购项目 采购项目编号： EZYG-ZFCG-2023-017 项目行政主管地区： 鄂州市 采购项目子包编号： 1 中标（成交）供应商名称： 武汉市腾亚科技有限公司 中标（成交）供应商代码： 91420111751839827U 中标（成交）价格： 121.5 价格单位： 万元 价格币种： 人民币 公告名称： 鄂州市临空经济区新庙镇中心学校新庙镇沙塘学校信息化设备采购项目中标（成交）结果公告 首次公告时间： 2023-09-06 15:13:53 创建人： 公告内容： 一、项目编号 EZYG-ZFCG-2023-017 二、采购计划备案号 420706-2023-00292 三、项目名称 新庙镇沙塘学校信息化设备采购项目 四、中标（成交）信息 包1： 供应商名称：武汉市腾亚科技有限公司 供应商地址：武汉东湖新技术开发区东一产业园光谷大道金融后台服务中心基地建设项目二期2.7期B26幢2层1、2号 中标（成交）金额：¥121.5万元 五、主要标的信息 包1： 货物类 名称：详见响应文件 品牌（如有）：详见响应文件 规格型号：详见响应文件 数量：详见响应文件 单价：121.5 万元 六、 评审专家名单 廖良锋(包1采购人代表)、汪学斌(包1组长)、任红军(包1) 七、评审信息 1. 评审时间：2023-09-05 2. 评审地点：鄂州市文苑壹号34号门面，吴都中学东门对面（阳光造价招标代理部评标室） 八、代理服务收费标准及金额： 1. 代理服务收费标准：参照《招标代理服务收费管理暂行办法》计价格[2002]1980号文规定计取 2. 收费金额（万元）：1.74 九、公告期限 自本公告发布之日起1个工作日。 十、其他补充事宜 根据《鄂州市政府采购合同融资工作实施方案》的要求，有需求的中标的中小微企业可以向意向金融机构提出政府采购合同融资申请。中小微企业凭政府采购中标（成交）通知书、政府采购合同，即可'零担保、零抵押'自主选择金融机构申请融资。合作金融机构承诺为中标供应商提供融资绿色通道，采购人承诺及时做好政府采购合同公开和合同备案。具体融资事宜由中标供应商与合作金融机构进行洽谈、办理。 十一、凡对本次公告内容提出询问，请按以下方式联系 1、采购人信息 名 称：鄂州市临空经济区新庙镇中心学校 地 址：新庙镇文塘村 联系方式：13986403924 2、采购代理机构信息 名 称：鄂州阳光建设工程造价咨询有限责任公司 地 址：湖北省-鄂州市-市辖区 文苑1号9号楼1层34号门面及2层4-9号门面 联系方式：13554455605 3、项目联系方式： 项目联系人： 向哲文 电 话： 13554455605 鄂州阳光建设工程造价咨询有限责任公司 2023-09-06"
    }
  ],
  "temperature": 0,
  "top_p": 1
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 本次对话补全请求ID |
| object | string | 响应对象类型，通常为chat.completion |
| created | integer | 响应创建时间戳 |
| model | string | 实际调用的模型名称 |
| choices | array | 模型生成结果列表 |
| choices[].index | integer | 候选结果序号 |
| choices[].message | object | 模型返回的消息对象 |
| choices[].message.role | string | 模型消息角色，通常为assistant |
| choices[].message.content | string | 标讯信息结构化结果文本，通常为JSON字符串或结构化文本 |
| choices[].finish_reason | string | 模型停止原因，例如stop、length等 |
| usage | object | token用量统计对象 |
| usage.prompt_tokens | integer | 输入提示词token数量 |
| usage.completion_tokens | integer | 输出内容token数量 |
| usage.total_tokens | integer | 总token数量 |

### 响应示例

```json
{
  "id": "chatcmpl-d25b458a28244220b8d200442032927e",
  "object": "chat.completion",
  "created": 1780388222,
  "model": "/home/ubuntu/ZTB-Structure/model/qwen2.5-1.5b-ztbstructure-ch17400-20251101",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"项目名称\":\"安徽省低空科技建工水利AI飞巡网络区域建设三期人机机场及配套设施采购\",\"项目编号\":[\"ACEG-202604233001001\"],\"甲方信息\":[{\"甲方名称\":\"安徽省低空科技发展有限公司\",\"甲方联系人姓名\":[\"吴工\"],\"甲方联系电话\":[\"18656351508\"]}],\"报名截止时间\":\"2026-04-09 18:00:00\",\"开标时间\":\"2026-04-13\"}",
        "refusal": null,
        "annotations": null,
        "audio": null,
        "function_call": null,
        "tool_calls": [],
        "reasoning_content": null
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null,
      "token_ids": null
    }
  ],
  "service_tier": null,
  "system_fingerprint": null,
  "usage": {
    "prompt_tokens": 1493,
    "total_tokens": 1617,
    "completion_tokens": 124,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "prompt_token_ids": null,
  "kv_transfer_params": null
}
```

---

## POST 【AI模型训练定制化】招中标信息分类推理

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/categoryReasoning?key=***`

**说明：** 根据标讯标题和正文推理招中标信息14分类。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| title | string | 是 | 中共虎林市委统一战线工作部侨联宣传册采购履约验收公告 | 信息标题 |
| content | string | 是 | 一、合同编号：ZBJ-20260706095637-27244二、合同名称：侨联宣传册采购三、项目编号：9c5c93d41db6409d8720146010e43ed5四、项目名称：400本，单价9.5元五、合同主体 采购人(甲方)：中共虎林市委统一战线工作部 地址：解放西街1号市委大楼232 联系方式：13125975585 供应商(乙方)：虎林市海信印刷厂 地址：黑龙江省鸡西市虎林市曙光街道极兴委爱民西街 233号 联系方式：04675838394 六、合同主要信息 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 七、本次验收内容 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 八、验收日期：2026年07月06日九、验收组成员：王若礼，马叶彤十、验收意见：验收通过十一、其他补充事宜：无 中共虎林市委统一战线工作部 2026年07月06日 | 信息内容 |

### 请求示例

```json
{
  "title": "中共虎林市委统一战线工作部侨联宣传册采购履约验收公告",
  "content": "一、合同编号：ZBJ-20260706095637-27244二、合同名称：侨联宣传册采购三、项目编号：9c5c93d41db6409d8720146010e43ed5四、项目名称：400本，单价9.5元五、合同主体 采购人(甲方)：中共虎林市委统一战线工作部 地址：解放西街1号市委大楼232 联系方式：13125975585 供应商(乙方)：虎林市海信印刷厂 地址：黑龙江省鸡西市虎林市曙光街道极兴委爱民西街 233号 联系方式：04675838394 六、合同主要信息 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 七、本次验收内容 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 八、验收日期：2026年07月06日九、验收组成员：王若礼，马叶彤十、验收意见：验收通过十一、其他补充事宜：无 中共虎林市委统一战线工作部 2026年07月06日"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| msg | string | 响应信息 |
| code | integer | 接口响应状态码 |
| data | object | 业务数据 |
| data.response | string | 模型推理结果，返回14种分类结果 |
| data.status | integer | 模型接口响应状态码 |
| data.time | string | 模型接口执行时间 |
| errorData | object | 错误数据 |
| subCode | string | 业务侧编码 |
| subMsg | string | 业务侧响应提示信息 |
| returnValue | object | 通用返回值字段 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "response": "公开招标",
    "status": 200,
    "time": "2026-05-13 09:26:48"
  },
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---

## POST 拟在建项目信息附件列表

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/getNZJProjectFileList?key=***`

**说明：** 根据拟在建项目ID、项目类型和发布时间获取项目信息所有附件。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| projectId | integer | 是 | 183474014 | 项目ID |
| projectTypeID | integer | 是 | 2 | 项目类型，此处固定为2，2=拟在建信息 |
| publishTime | string | 是 | 2026-06-08 09:04:35 | 项目发布时间，格式 yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss |

### 请求示例

```json
{
  "projectId": 183474014,
  "projectTypeID": 2,
  "publishTime": "2026-06-08 09:04:35"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | 接口响应状态码（200=成功） |
| msg | string | 接口响应提示信息 |
| count | integer | 列表页记录数老参数，当前返回固定0 |
| returnValue | any | 通用返回值字段，当前为null无数据 |
| subCode | string | 业务侧编码（0000000000=业务成功） |
| subMsg | string | 业务侧响应提示信息 |
| data | array | 项目附件列表数组 |
| data[].projectTypeID | integer | 项目类型，2=拟在建信息 |
| data[].projectFileID | integer | 项目信息附件ID |
| data[].projectID | string | 项目ID |
| data[].name | string | 附件名称 |
| data[].url | string | 附件下载地址 |
| data[].proviceCode | string | 省份行政区域编码 |
| data[].cityCode | string | 地市行政区域编码 |
| data[].suffix | string | 文件后缀 |
| data[].size | number | 附件大小，单位KB，null表示未提供 |
| data[].publishTime | string | 项目发布时间，格式yyyy-MM-dd HH:mm:ss |
| data[].state | string | 附件处理状态 |
| data[].createTime | string | 附件创建时间，格式yyyy-MM-dd HH:mm:ss |

### 响应示例

```json
{
  "data": [
    {
      "projectFileID": 101770000,
      "projectID": "283390000",
      "name": "风险大脑企业版产品的订阅22002255...",
      "url": "https://file-open-doc.zcygov.cn/1014AN/openfcf2cb1ae5.docx",
      "proviceCode": "330000",
      "cityCode": "330100",
      "suffix": "docx",
      "size": null,
      "publishTime": "2025-09-03 14:28:17",
      "state": "0",
      "createTime": "2025-09-03 16:15:49"
    }
  ],
  "code": 200,
  "msg": "ok",
  "count": 0,
  "returnValue": null,
  "subCode": "0000000000",
  "subMsg": "成功"
}
```

---

## POST 【AI模型训练定制化】项目信息甄别

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/projectDiscrimination?key=***`

**说明：** 根据标题和正文判断文本属于标讯信息、拟在建信息、非项目信息或异常信息。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| title | string | 是 | 中共虎林市委统一战线工作部侨联宣传册采购履约验收公告 | 信息标题 |
| content | string | 是 | 一、合同编号：ZBJ-20260706095637-27244二、合同名称：侨联宣传册采购三、项目编号：9c5c93d41db6409d8720146010e43ed5四、项目名称：400本，单价9.5元五、合同主体 采购人(甲方)：中共虎林市委统一战线工作部 地址：解放西街1号市委大楼232 联系方式：13125975585 供应商(乙方)：虎林市海信印刷厂 地址：黑龙江省鸡西市虎林市曙光街道极兴委爱民西街 233号 联系方式：04675838394 六、合同主要信息 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 七、本次验收内容 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 八、验收日期：2026年07月06日九、验收组成员：王若礼，马叶彤十、验收意见：验收通过十一、其他补充事宜：无 中共虎林市委统一战线工作部 2026年07月06日 | 信息内容 |

### 请求示例

```json
{
  "title": "中共虎林市委统一战线工作部侨联宣传册采购履约验收公告",
  "content": "一、合同编号：ZBJ-20260706095637-27244二、合同名称：侨联宣传册采购三、项目编号：9c5c93d41db6409d8720146010e43ed5四、项目名称：400本，单价9.5元五、合同主体 采购人(甲方)：中共虎林市委统一战线工作部 地址：解放西街1号市委大楼232 联系方式：13125975585 供应商(乙方)：虎林市海信印刷厂 地址：黑龙江省鸡西市虎林市曙光街道极兴委爱民西街 233号 联系方式：04675838394 六、合同主要信息 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 七、本次验收内容 序号 名称 数量(单位) 单价(元) 合计(元) 1 400本，单价9.5元 1(3800) 3800.00 3800.00 合同金额： 3800.00元，大写(人民币)：叁仟捌佰元整 八、验收日期：2026年07月06日九、验收组成员：王若礼，马叶彤十、验收意见：验收通过十一、其他补充事宜：无 中共虎林市委统一战线工作部 2026年07月06日"
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| msg | string | 响应信息 |
| code | integer | 接口响应状态码 |
| data | object | 业务数据 |
| data.response | string | 模型甄别结果，可能为标讯信息、拟在建信息 |
| data.status | integer | 模型接口响应状态码 |
| data.time | string | 模型接口执行时间 |
| errorData | object | 错误数据 |
| subCode | string | 业务侧编码 |
| subMsg | string | 业务侧响应提示信息 |
| returnValue | object | 通用返回值字段 |

### 响应示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "response": "标讯信息",
    "status": 200,
    "time": "2026-05-13 09:25:07"
  },
  "errorData": null,
  "subCode": "0000000000",
  "subMsg": "ok",
  "returnValue": null
}
```

---

## 关于我们

# 主要产品与服务

## 1. 招投标数据 API
- 招投标数据接口已支持调用
- 拟在建、企业数据接口已经上线
- MCP、爱马仕、小龙虾等技能封装已完成，支持一键调用

## 2. 78个结构化高级字段数据导出
- 支持按行业、地区、关键词、时间范围等条件导出招投标数据
- 可用于销售线索、市场分析、客户挖掘等场景

## 3. 数据库定制
- 3亿+ 招投标数据支持定制化
- 数据日更 30 万+
- 年度新增数据 6000 万+
- 可按客户业务需求进行字段、范围、更新频率定制

## 4. 保标商机助手（仅企业微信使用）
- 适用于企业微信场景
- 面向老板、销售总监、销售团队使用
- 帮助企业发现商机、跟进项目、提升销售转化效率

## 5. 招投标小程序（含原码） + PC 网页定制开发
- 支持小程序开发
- 支持 PC 端网页系统开发
- 可结合招投标数据、企业数据、业务流程进行定制

## 6. 结构化模型训练
- 支持结构化数据模型训练
- 可根据私有数据和业务场景进行定制
- 适用于数据清洗、字段抽取、线索识别、商机推荐等场景
- 提供金融行业（银行、保险行业等）、智能制造、人工智能等垂直行业的数据结构化模型训练方法

## 7. 现有的招投标数据结构化模型（可直接售卖）

## 8. 字段优先结构化数据
支持优先结构化年卡客户消费的垂直行业。目前现有的78个结构化字段API支持定制，具体如下：

### 招标信息字段
- 项目名称
- 项目编号
- 项目标段编号
- 招标单位名称
- 招标单位联系人
- 招标单位联系电话
- 招标单位地址
- 招标单位邮箱
- 代理机构名称
- 代理机构联系人
- 代理机构联系电话
- 代理机构地址
- 代理机构联系邮箱
- 预算金额
- 报名截止时间
- 开标地点
- 开标时间
- 验收负责人
- 验收单位
- 验收交付时间
- 项目转包分包声明

### 中标信息字段
- 项目名称
- 项目编号
- 项目标段编号
- 中标单位名称
- 中标单位联系人
- 中标单位联系电话
- 中标单位联系地址
- 中标候选人
- 中标单位名称
- 中标金额
- 评标专家姓名
- 评标专家角色

### 合同信息字段
- 项目名称
- 项目编号
- 项目标段编号
- 中标单位名称
- 中标单位联系人
- 中标单位联系电话
- 中标单位联系地址
- 合同编号
- 合同金额
- 合同签订时间
- 合同开始时间
- 合同截止时间
- 项目周期

---

## 第二期结构化字段计划

### 投标记录
- 标段编号
- 投标单位名称
- 投标单位总报价
- 投标单位技术得分
- 投标单位商务得分
- 投标单位报价得分
- 投标单位总得分
- 投标单位报价系数
- 投标单位费率

### 其他字段
- 资金来源
- 标的物
- 资质

---

## 第三期结构化字段计划

- 合同编号
- 合同甲方
- 合同乙方
- 合同金额
- 付款条件
- 付款条件难度评级
- 验收条件
- 验收条件评级

### 标的物明细
- 标的物名称
- 标的物型号
- 标的物参数
- 标的物数量
- 标的物计量单位
- 标的物单价

### 其他字段
- 合同联系人
- 合同联系人联系方式

对产品有任何技术问题及项目开发合作等问题联系：
 张瑛18986107388
![zhangying](https://static.gov-bid.com/web-static/v2/prod/assets/install-shell/sbkj-zhangying.jpg "zhangying")

