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
