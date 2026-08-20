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
