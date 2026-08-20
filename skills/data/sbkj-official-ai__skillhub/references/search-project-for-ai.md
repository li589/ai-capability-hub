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
