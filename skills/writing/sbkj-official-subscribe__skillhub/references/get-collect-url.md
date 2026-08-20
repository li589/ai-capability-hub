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
