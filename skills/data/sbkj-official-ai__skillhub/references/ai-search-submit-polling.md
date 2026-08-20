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
