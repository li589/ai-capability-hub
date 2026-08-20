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
