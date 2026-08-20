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
