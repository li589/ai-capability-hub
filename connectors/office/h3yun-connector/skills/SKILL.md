# 氚云Skill

本 Skill 提供氚云应用、表单、业务数据及待办审批的查询和操作能力。

## 可用工具

### listApps - 获取用户有权限访问的应用

直接获取用户所有有权限的应用时调用

**参数说明**：

| 参数      | 类型   | 必填 | 说明     |
| --------- | ------ | :--: | -------- |
| pageIndex | number |  ✅  | 页码     |
| pageSize  | number |  ✅  | 每页数量 |

**返回值**：{ errorCode: number; errorMessage: string; data: `{ total: number, data: AppDetail[] }` }

**使用示例**：

```json
{ "pageIndex": 1, "pageSize": 20 }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "total": 1,
    "data": [
      {
        "appCode": "APP_DEMO",
        "appName": "业务应用",
        "appState": "ENABLED",
        "createdTime": "2026-07-31T10:00:00+08:00",
        "createdBy": "user_001",
        "createdByObject": {
          "objectId": "user_001",
          "name": "张三",
          "entryId": "entry_001"
        }
      }
    ]
  }
}
```

**可能错误码**：`100304`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`

### searchApps - 根据应用名称关键字获取用户有权限访问的应用

根据指定关键字查询应用名称匹配的当前用户有权限访问的应用。

**参数说明**：

| 参数      | 类型   | 必填 | 说明     |
| --------- | ------ | :--: | -------- |
| pageIndex | number |  ✅  | 页码     |
| pageSize  | number |  ✅  | 每页数量 |
| keyword   | string |  ✅  | 应用名称 |

**返回值**：{ errorCode: number; errorMessage: string; data: `{ total: number, data: AppDetail[] }` }

**使用示例**：

```json
{ "pageIndex": 1, "pageSize": 20, "keyword": "CRM" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "total": 1,
    "data": [
      {
        "appCode": "APP_DEMO",
        "appName": "业务应用",
        "appState": "ENABLED",
        "createdTime": "2026-07-31T10:00:00+08:00",
        "createdBy": "user_001",
        "createdByObject": {
          "objectId": "user_001",
          "name": "张三",
          "entryId": "entry_001"
        }
      }
    ]
  }
}
```

**可能错误码**：`100304`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`

### searchFunctionNodes - 根据名称关键字获取用户有权限的表单列表

根据指定关键字查找匹配表单名称的当前用户有权限访问的表单。

**参数说明**：

| 参数      | 类型   | 必填 | 说明       |
| --------- | ------ | :--: | ---------- |
| pageIndex | number |  ✅  | 页码       |
| pageSize  | number |  ✅  | 每页数量   |
| keyword   | string |  ✅  | 名称关键字 |
| appCode   | string |  -   | 应用名称   |

**返回值**：{ errorCode: number; errorMessage: string; data: `{ total: number, data: FunctionNode[] }` }

**使用示例**：

```json
{ "pageIndex": 1, "pageSize": 20, "keyword": "跟进记录" }
```

指定应用查询：

```json
{ "pageIndex": 1, "pageSize": 20, "keyword": "跟进记录", "appCode": "APP_DEMO" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "total": 1,
    "data": [
      {
        "appCode": "APP_DEMO",
        "appName": "人事管理",
        "schemaCode": "D0000001",
        "schemaName": "请假申请",
        "description": "员工请假表单",
        "icon": "https://example.com/icons/leave.svg"
      }
    ]
  }
}
```

**可能错误码**：`100304`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200104`、`200105`

###

### getSchema - 获取表单结构

获取指定表单的表结构、返回表中字段定义及子表定义。

**参数说明**：

| 参数       | 类型   | 必填 | 说明     |
| ---------- | ------ | :--: | -------- |
| schemaCode | string |  ✅  | 表单编码 |

**返回值**：{ errorCode: number; errorMessage: string; data: `BizObjectSchema` }

**使用示例**：

```json
{ "schemaCode": "D0000001" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "schemaCode": "D0000001",
    "displayName": "请假申请",
    "description": "员工请假表单",
    "fields": [
      {
        "name": "F0000001",
        "displayName": "申请人",
        "description": "人员单选",
        "controlType": 12,
        "options": {
          "defaultValue": "user_001"
        }
      },
      {
        "name": "F0000002",
        "displayName": "请假说明",
        "description": "多行文本",
        "controlType": 2,
        "options": {
          "defaultValue": ""
        }
      },
      {
        "name": "F0000003",
        "displayName": "请假天数",
        "description": "数字",
        "controlType": 4,
        "options": {
          "defaultValue": "0"
        }
      },
      {
        "name": "F0000004",
        "displayName": "开始日期",
        "description": "日期",
        "controlType": 3,
        "options": {
          "defaultValue": "2026-08-04"
        }
      },
      {
        "name": "F0000005",
        "displayName": "请假类型",
        "description": "下拉框",
        "controlType": 7,
        "options": {
          "defaultValue": "年假",
          "defaultItems": ["年假", "病假", "调休"]
        }
      },
      {
        "name": "F0000006",
        "displayName": "请假时段",
        "description": "单选框",
        "controlType": 5,
        "options": {
          "defaultValue": "全天",
          "defaultItems": ["上午", "下午", "全天"]
        }
      },
      {
        "name": "F0000007",
        "displayName": "附加原因",
        "description": "复选框",
        "controlType": 6,
        "options": {
          "defaultValue": "探亲;休假",
          "defaultItems": ["探亲", "休假", "其他"]
        }
      },
      {
        "name": "F0000008",
        "displayName": "是否紧急",
        "description": "是否控件",
        "controlType": 8,
        "options": {
          "defaultValue": "false"
        }
      },
      {
        "name": "F0000009",
        "displayName": "关联项目",
        "description": "关联表单",
        "controlType": 301,
        "options": {
          "defaultValue": "bo_001",
          "associationSchemaCode": "D0000002"
        }
      },
      {
        "name": "F0000010",
        "displayName": "参与人员",
        "description": "人员多选",
        "controlType": 11,
        "options": {
          "defaultValue": "user_001"
        }
      },
      {
        "name": "F0000011",
        "displayName": "所属部门",
        "description": "部门单选",
        "controlType": 13,
        "options": {
          "defaultValue": "dept_001"
        }
      },
      {
        "name": "F0000012",
        "displayName": "地址",
        "description": "地址控件",
        "controlType": 9,
        "options": {
          "defaultValue": "{\"adcode\":\"110108\",\"adname\":\"北京市海淀区\",\"Detail\":\"中关村大街\"}"
        }
      },
      {
        "name": "F0000013",
        "displayName": "定位位置",
        "description": "定位控件",
        "controlType": 10,
        "options": {
          "defaultValue": "{\"Address\":\"中关村\",\"CSType\":1,\"Point\":{\"lat\":39.983,\"lng\":116.316},\"WGS84Point\":{\"lat\":39.981,\"lng\":116.310}}"
        }
      },
      {
        "name": "F0000014",
        "displayName": "附件",
        "description": "附件控件",
        "controlType": 15,
        "options": {
          "defaultValue": "",
          "maxUploadSize": 10485760
        }
      },
      {
        "name": "F0000015",
        "displayName": "照片",
        "description": "图片控件",
        "controlType": 16,
        "options": {
          "defaultValue": "",
          "uploadMultiple": true
        }
      }
    ],
    "childSchemas": []
  }
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200204`、`200205`

### getSchemaAcl - 获取表单权限

获取当前用户对指定表单的操作权限和字段权限。

**参数说明**：

| 参数       | 类型   | 必填 | 说明     |
| ---------- | ------ | :--: | -------- |
| schemaCode | string |  ✅  | 表单编码 |

**返回值**：{ errorCode: number; errorMessage: string; data: `SchemaPermissionResult` }

**使用示例**：

```json
{ "schemaCode": "D0000001" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "schemaAcl": {
      "addable": true,
      "editable": true,
      "removable": false
    },
    "fieldPermissions": {
      "AddPermission": [
        {
          "visible": true,
          "editable": true,
          "required": true
        }
      ],
      "EditPermission": [
        {
          "visible": true,
          "editable": true,
          "required": true
        }
      ]
    }
  }
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200204`、`200205`

### createBizObject - 新增单条业务数据

在指定表单中新增一条业务数据。

**参数说明**：

| 参数       | 类型           | 必填 | 说明                                 |
| ---------- | -------------- | :--: | ------------------------------------ |
| schemaCode | string         |  ✅  | 表单编码                             |
| bizObject  | WriteBizObject |  ✅  | 业务数据对象；完整结构见文末类型定义 |

**返回值**：{ errorCode: number; errorMessage: string; data: `{bizObjectId: string}` }

**使用示例**：

`bizObject` 为业务数据对象，字段名应以 `getSchema` 返回的字段定义为准。下表按 `ControlValueTypeMap` 说明各控件字段值的构造方式。

| 控件类型                                                 | 字段值类型              | 值示例                          | 说明                                                            |
| -------------------------------------------------------- | ----------------------- | ------------------------------- | --------------------------------------------------------------- |
| 单行文本、多行文本、数字、日期、下拉框、单选框、关联表单 | `string`                | `"张三"`、`"2"`、`"2026-08-03"` | 数字和日期也按字符串传入                                        |
| 复选框                                                   | `string`                | `"选项A;选项B"`                 | 选项拼接字符串，多个选项以英文分号拼接                          |
| 是否控件                                                 | `boolean`               | `true`                          | 直接传入布尔值                                                  |
| 地址                                                     | `AddressFieldValueType` | `"{\"adcode\":\"110108\",...}"` | `AddressValue` 序列化后的 JSON 字符串                           |
| 定位                                                     | `MapFieldValueType`     | `"{\"Address\":\"...\",...}"`   | `MapValue` 序列化后的 JSON 字符串                               |
| 人员、部门、拥有者、所属部门                             | `string[]`              | `["user_001"]`                  | 人员或部门 ID 数组；单选也使用数组                              |
| 关联表单多选                                             | `string[]`              | `["bo_001", "bo_002"]`          | 关联业务数据 ID 数组                                            |
| 子表                                                     | `bizObject[]`           | `[{ "子表文本": "第一行" }]`    | 数组中的每一项是一行子表数据，字段值类型与 `bizObject` 完全一致 |

子表字段的值为行对象数组。每一行都使用与 `bizObject` 相同的字段值规则，并应按子表 schema 中的字段定义提供字段键和值。

```json
{
  "schemaCode": "D0000001",
  "bizObject": {
    "申请人": "张三",
    "请假说明": "年假申请",
    "请假天数": "2",
    "开始日期": "2026-08-03",
    "请假类型": "年假",
    "请假时段": "上午",
    "关联项目": "bo_project_001",
    "请假原因": "探亲;休假",
    "是否紧急": true,
    "地址": "{\"adcode\":\"110108\",\"adname\":\"北京市海淀区\",\"Detail\":\"中关村大街\"}",
    "定位位置": "{\"Address\":\"北京市海淀区中关村大街\",\"CSType\":1,\"Point\":{\"lat\":39.983,\"lng\":116.316},\"WGS84Point\":{\"lat\":39.981,\"lng\":116.31}}",
    "申请人员": ["user_001"],
    "抄送人员": ["user_002", "user_003"],
    "所属部门": ["dept_001"],
    "拥有者": ["user_001"],
    "关联业务数据": ["bo_001", "bo_002"],
    "费用明细": [
      {
        "费用名称": "交通费",
        "金额": "120",
        "是否报销": true,
        "经办人": ["user_001"],
        "关联单据": ["bo_cost_001"]
      },
      {
        "费用名称": "住宿费",
        "金额": "300",
        "是否报销": false,
        "经办人": ["user_002"],
        "关联单据": ["bo_cost_002", "bo_cost_003"]
      }
    ]
  }
}
```

**返回示例**：

```json
{ "bizObjectId": "*****" }
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100305`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200201`、`200204`、`200205`、`200207`、`200208`、`200209`

### createBizObjects - 批量新增业务数据

在指定表单中批量新增业务数据。

**参数说明**：

| 参数           | 类型             | 必填 | 说明                                       |
| -------------- | ---------------- | :--: | ------------------------------------------ |
| schemaCode     | string           |  ✅  | 表单编码                                   |
| bizObjectArray | WriteBizObject[] |  ✅  | 待新增业务数据列表；完整结构见文末类型定义 |

**返回值**：{ errorCode: number; errorMessage: string; data: `{ successBizObjectIds: string[], failedBizObjectIds: string[] }` }

**使用示例**：

`bizObjectArray` 的每个元素均为一个 `bizObject`，字段值类型、数组字段和子表数组均遵循 `createBizObject` 的完整规则。

```json
{
  "schemaCode": "D0000001",
  "bizObjectArray": [
    {
      "申请人": "张三",
      "申请人员": ["user_001"],
      "费用明细": [
        { "费用名称": "交通费", "金额": "120", "经办人": ["user_001"] }
      ]
    },
    {
      "申请人": "李四",
      "申请人员": ["user_002"],
      "费用明细": [
        { "费用名称": "住宿费", "金额": "300", "经办人": ["user_002"] }
      ]
    }
  ]
}
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "successBizObjectIds": ["bo_001"],
    "failedBizObjectIds": ["bo_002"]
  }
}
```

批量处理存在失败项时，接口仍通过 `failedBizObjectIds` 返回未成功添加的数据 ID；调用方应根据该数组处理失败项。

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100305`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200201`、`200204`、`200205`、`200207`、`200208`、`200209`

### removeBizObject - 删除单条业务数据

删除指定表单中的一条业务数据。

**参数说明**：

| 参数        | 类型   | 必填 | 说明        |
| ----------- | ------ | :--: | ----------- |
| schemaCode  | string |  ✅  | 表单编码    |
| bizObjectId | string |  ✅  | 业务数据 ID |

**返回值**：{ errorCode: number; errorMessage: string; data: 无 }

**使用示例**：

```json
{ "schemaCode": "D0000001", "bizObjectId": "bo_001" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {}
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200202`、`200204`、`200205`、`200206`

### removeBizObjects - 批量删除业务数据

批量删除指定表单中的业务数据。

**参数说明**：

| 参数         | 类型     | 必填 | 说明                     |
| ------------ | -------- | :--: | ------------------------ |
| schemaCode   | string   |  ✅  | 表单编码                 |
| bizObjectIds | string[] |  ✅  | 待删除的业务数据 ID 列表 |

**返回值**：{ errorCode: number; errorMessage: string; data: `{ successBizObjectIds: string[], failedBizObjectIds: string[] }` }

**使用示例**：

```json
{
  "schemaCode": "D0000001",
  "bizObjectIds": ["bo_001", "bo_002"]
}
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "successBizObjectIds": ["bo_001"],
    "failedBizObjectIds": ["bo_002"]
  }
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200202`、`200204`、`200205`、`200206`

### updateBizObject - 更新业务数据

更新指定表单中的一条业务数据。

**参数说明**：

| 参数        | 类型           | 必填 | 说明                                         |
| ----------- | -------------- | :--: | -------------------------------------------- |
| schemaCode  | string         |  ✅  | 表单编码                                     |
| bizObjectId | string         |  ✅  | 业务数据 ID                                  |
| bizObject   | WriteBizObject |  ✅  | 待更新的业务数据对象；完整结构见文末类型定义 |

bizObject字段值类型、数组字段和子表数组均遵循 createBizObject 的完整规则。

**返回值**：{ errorCode: number; errorMessage: string; data: 无 }

**使用示例**：

```json
{
  "schemaCode": "D0000001",
  "bizObjectId": "bo_001",
  "bizObject": "{\"姓名\":\"张三\",\"请假天数\":3}"
}
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {}
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100305`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200203`、`200204`、`200205`、`200206`、`200207`、`200208`

### getBizObject - 查询单条业务数据

根据表单编码和业务数据 ID 查询一条业务数据。

**参数说明**：

| 参数        | 类型   | 必填 | 说明        |
| ----------- | ------ | :--: | ----------- |
| schemaCode  | string |  ✅  | 表单编码    |
| bizObjectId | string |  ✅  | 业务数据 ID |

**返回值**：{ errorCode: number; errorMessage: string; data: `{schemaCode: string, valueTable: SingleQueryBizObject}` }

**BizObject 类型引用**：本接口返回的 valueTable 类型为 SingleQueryBizObject，完整结构见文末“BizObject 场景类型定义”。

**返回示例**：

```json
{
  "schemaCode": "D0000001",
  "valueTable": {
    "F0001": "张三",
    "F0002": "说明",
    "F0003": "2026-08-04",
    "F0004": 12.5,
    "F0005": "年假",
    "F0006": "A;B",
    "F0007": "高",
    "F0008": true,
    "F0009": [{ "fileId": "f1", "fileUrl": "https://example.com/a.pdf" }],
    "F0010": [{ "fileId": "p1", "fileUrl": "https://example.com/a.png" }],
    "F0011": "{\"adcode\":\"110108\",\"adname\":\"北京市海淀区\",\"Detail\":\"中关村大街\"}",
    "F0012": "{\"Address\":\"中关村\",\"CSType\":1,\"Point\":{\"lat\":39.983,\"lng\":116.316},\"WGS84Point\":{\"lat\":39.981,\"lng\":116.310}}",
    "F0013": "user_001",
    "F0014": ["user_001", "user_002"],
    "F0015": "dept_001",
    "F0016": ["dept_001"],
    "F0017": [
      { "ObjectId": "child_1", "Name": "明细1", "ParentObjectId": "bo_001" }
    ],
    "F0018": "NO-001",
    "F0019": "user_001",
    "F0020": "user_002",
    "F0021": "dept_001",
    "F0022": "2026-08-04T10:00:00+08:00",
    "F0023": "2026-08-04T11:00:00+08:00",
    "F0024": 2,
    "F0025": "bo_001",
    "F0026": ["bo_001"],
    "F0027": null,
    "F0028": 100,
    "F0029": null,
    "F0013Object": { "ObjectId": "user_001", "Name": "张三", "EntryId": "e1" },
    "F0014Object": [
      { "ObjectId": "user_001", "Name": "张三", "EntryId": "e1" }
    ],
    "F0015Object": {
      "ObjectId": "dept_001",
      "Name": "研发部",
      "EntryId": "e2"
    },
    "F0016Object": [
      { "ObjectId": "dept_001", "Name": "研发部", "EntryId": "e2" }
    ],
    "CreatedByObject": {
      "ObjectId": "user_001",
      "Name": "张三",
      "EntryId": "e1"
    },
    "OwnerIdObject": {
      "ObjectId": "user_002",
      "Name": "李四",
      "EntryId": "e3"
    },
    "OwnerDeptIdObject": {
      "ObjectId": "dept_001",
      "Name": "研发部",
      "EntryId": "e2"
    }
  }
}
```

### queryData - 筛选业务数据（只支持查单表）

根据sql查询表单业务数据

**参数说明**：

| 参数       | 类型   | 必填 | 说明     |
| ---------- | ------ | :--: | -------- |
| schemaCode | string |  ✅  | 表单编码 |
| sql        | string |  ✅  | 查询语句 |

**返回值**：{ errorCode: number; errorMessage: string; data: `BatchQueryBizObject[]`，完整结构见文末类型定义。 }

**使用示例**：

```json
{
  "schemaCode": "D0000001",
  "sql": "****"
}
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": [
    {
      "schemaCode": "D0000001",
      "valueTable": {
        "F0001": "张三",
        "F0002": "说明",
        "F0003": "2026-08-04",
        "F0004": 12.5,
        "F0005": "年假",
        "F0006": "A;B",
        "F0007": "高",
        "F0008": true,
        "F0009": [
          {
            "fileId": "f1",
            "fileUrl": "url"
          }
        ],
        "F0010": [
          {
            "fileId": "p1",
            "fileUrl": "url"
          }
        ],
        "F0011": "{\"adcode\":\"110108\"}",
        "F0012": "{\"Address\":\"中关村\",\"CSType\":1,\"Point\":{\"lat\":39.983,\"lng\":116.316},\"WGS84Point\":{\"lat\":39.981,\"lng\":116.310}}",
        "F0013": "user_001",
        "F0014": ["user_001"],
        "F0015": "dept_001",
        "F0016": ["dept_001"],
        "F0018": "NO-001",
        "F0019": "user_001",
        "F0020": "user_002",
        "F0021": "dept_001",
        "F0022": "2026-08-04T10:00:00+08:00",
        "F0023": "2026-08-04T11:00:00+08:00",
        "F0024": 2,
        "F0025": "bo_001",
        "F0026": ["bo_001"],
        "F0027": null,
        "F0028": 100,
        "F0029": null
      }
    }
  ]
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100306`、`100307`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200204`、`200205`、`200210`、`200211`

### getBizObjectNamesByIds - 按 ID 获取业务数据名称

根据表单编码和业务数据 ID 列表批量获取业务数据名称。

**参数说明**：

| 参数         | 类型     | 必填 | 说明             |
| ------------ | -------- | :--: | ---------------- |
| schemaCode   | string   |  ✅  | 表单编码         |
| bizObjectIds | string[] |  ✅  | 业务数据 ID 列表 |

**返回值**：{ errorCode: number; errorMessage: string; data: Array<{ name: string, id: string }> }

**使用示例**：

```json
{ "schemaCode": "D0000001", "bizObjectIds": ["bo_001", "bo_002"] }
```

**返回示例**：

```json
[
  { "name": "张三", "id": "bo_001" },
  { "name": "李四", "id": "bo_002" }
]
```

**可能错误码**：100300、100301、100302、100303、100400、100401、100402、100500、100501、100502、200204、200205、200206

### getOrgNamesByIds - 按 ID 获取人员或部门名称

根据组织对象 ID 列表批量获取人员或部门名称。

**参数说明**：

| 参数 | 类型     | 必填 | 说明               |
| ---- | -------- | :--: | ------------------ |
| ids  | string[] |  ✅  | 人员或部门 ID 列表 |

**返回值**：{ errorCode: number; errorMessage: string; data: Array<{ name: string, id: string, type: string }> }

**使用示例**：

```json
{ "ids": ["user_001", "dept_001"] }
```

**返回示例**：

```json
[
  { "name": "张三", "id": "user_001", "type": "user" },
  { "name": "研发部", "id": "dept_001", "type": "dept" }
]
```

**可能错误码**：100300、100301、100302、100303、100400、100401、100402、100500、100501、100502、200401

### getBizObjectIdsByNames - 按名称获取业务数据id

根据名称获取指定表单中业务数据的名称和 ID。

**参数说明**：

| 参数       | 类型     | 必填 | 说明         |
| ---------- | -------- | :--: | ------------ |
| schemaCode | string   |  ✅  | 表单编码     |
| names      | string[] |  ✅  | 业务数据名称 |

**返回值**：{ errorCode: number; errorMessage: string; data: `Array<{ name: string, bizObjectId: string }>` }

**使用示例**：

```json
{ "schemaCode": "D0000001", "name": "张三" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": [
    {
      "name": "张三",
      "bizObjectId": "bo_001"
    }
  ]
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200204`、`200205`、`200206`

### queryOrgIdsByNames - 按名称获取人员或部门

根据名称列表查询人员或部门的名称和组织单元 ID。

**参数说明**：

| 参数  | 类型     | 必填 | 说明                                           |
| ----- | -------- | :--: | ---------------------------------------------- |
| names | string[] |  ✅  | 人员或部门名称列表                             |
| type  | string   |  ✅  | 查询对象类型：`user` 表示人员，`dept` 表示部门 |

**返回值**：{ errorCode: number; errorMessage: string; data: `Array<{ name: string, id: string }>` }

**使用示例**：

查询人员：

```json
{ "names": ["张三", "李四"], "type": "user" }
```

查询部门：

```json
{ "names": ["人力资源部"], "type": "dept" }
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": [
    {
      "name": "人力资源部",
      "unitId": "dept_001"
    }
  ]
}
```

**可能错误码**：`100300`、`100301`、`100302`、`100303`、`100400`、`100401`、`100402`、`100500`、`100501`、`100502`、`200401`

### uploadFile - 转存附件

将指定 URL 的附件转存，返回上传文件的fileId, 用于方案回写表单等场景。

**参数说明**：

| 参数       | 类型   | 必填 | 说明                     |
| ---------- | ------ | :--: | ------------------------ |
| fileUrl    | string |  ✅  | 待转存文件的 URL         |
| schemaCode | string |  ✅  | 待上传附件所属的表单编码 |

**返回值**：{ errorCode: number; errorMessage: string; data: { fileId: string } }

**使用示例**：

```json
{
  "fileUrl": "https://example.com/files/contract.pdf",
  "schemaCode": "D0000001"
}
```

**返回示例**：

```json
{
  "errorCode": 0,
  "errorMessage": "",
  "data": {
    "fileId": "file_001"
  }
}
```

**可能错误码**：100300、100301、100302、100303、100400、100401、100402、100500、100501、100502、200601、200602

## 类型说明

### BizObject（业务数据）

| 字段       | 类型                      | 说明                                   |
| ---------- | ------------------------- | -------------------------------------- |
| schemaCode | string                    | 表单编码                               |
| valueTable | `Record<string, unknown>` | 业务字段值；支持的字段类型和字段值遵循 |

### BizObjectSchema（表单定义）

| 字段         | 类型              | 说明         |
| ------------ | ----------------- | ------------ |
| schemaCode   | string            | 表单编码     |
| displayName  | string            | 表单显示名称 |
| description  | string            | 表单描述     |
| fields       | FieldDefinition[] | 字段定义列表 |
| childSchemas | BizObjectSchema[] | 子表定义列表 |

### FieldDefinition（字段定义）

| 字段        | 类型         | 说明                     |
| ----------- | ------------ | ------------------------ |
| name        | string       | 字段编码                 |
| displayName | string       | 字段显示名称             |
| description | string       | 字段描述                 |
| controlType | FieldType    | 字段类型枚举             |
| options     | IFieldOption | 与控件类型对应的字段配置 |

所有控件的 options 都可选填 defaultValue；默认值以字符串形式返回。其他属性取决于 controlType，未列出的控件仅支持基础选项。

| 控件类型              | options 结构      | 示例                                                         | 说明                                     |
| --------------------- | ----------------- | ------------------------------------------------------------ | ---------------------------------------- |
| FormTextBox           | IFieldOption      | {"defaultValue":"张三"}                                      | 单行文本默认值                           |
| FormTextArea          | IFieldOption      | {"defaultValue":"说明"}                                      | 多行文本默认值                           |
| FormDateTime          | IFieldOption      | {"defaultValue":"2026-08-04"}                                | 日期默认值                               |
| FormNumber            | IFieldOption      | {"defaultValue":"0"}                                         | 数字默认值以字符串表示                   |
| FormCheckbox          | IFieldOption      | {"defaultValue":"false"}                                     | 是否控件默认值                           |
| FormRadioButtonList   | ISelectOption     | {"defaultValue":"年假","defaultItems":["年假","病假"]}       | 单选项及默认值                           |
| FormCheckboxList      | ISelectOption     | {"defaultValue":"探亲;休假","defaultItems":["探亲","休假"]}  | 多选项及分号拼接的默认值                 |
| FormDropDownList      | ISelectOption     | {"defaultValue":"高","defaultItems":["高","中","低"]}        | 下拉选项及默认值                         |
| FormQuery             | IFormQueryOption  | {"defaultValue":"bo_001","associationSchemaCode":"D0000002"} | 关联单选目标表单                         |
| FormMultiQuery        | IFormQueryOption  | {"defaultValue":"bo_001","associationSchemaCode":"D0000002"} | 关联多选目标表单                         |
| FormAreaSelect        | IFieldOption      | {"defaultValue":"{"adcode":"110108"}"}                       | 地址 JSON 默认值                         |
| FormMap               | IFieldOption      | {"defaultValue":"{"Address":"中关村"}"}                      | 定位 JSON 默认值                         |
| FormUser              | IFieldOption      | {"defaultValue":"user_001"}                                  | 人员单选默认值                           |
| FormMultiUser         | IFieldOption      | {"defaultValue":"user_001"}                                  | 人员多选默认值                           |
| FormDepartment        | IFieldOption      | {"defaultValue":"dept_001"}                                  | 部门单选默认值                           |
| FormMultiDepartment   | IFieldOption      | {"defaultValue":"dept_001"}                                  | 部门多选默认值                           |
| FormAttachment        | IAttachmentOption | {"defaultValue":"","maxUploadSize":10485760}                 | 最大附件大小，单位字节                   |
| FormPhoto             | IFormPhotoOption  | {"defaultValue":"","uploadMultiple":true}                    | 是否允许多图上传                         |
| FormGridView          | IFieldOption      | {"defaultValue":""}                                          | 子表无专用 options                       |
| FormSeqNo             | IFieldOption      | {"defaultValue":""}                                          | 流水号只支持默认值                       |
| FormCreater           | IFieldOption      | {"defaultValue":"user_001"}                                  | 创建人默认值                             |
| FormOwner             | IFieldOption      | {"defaultValue":"user_001"}                                  | 拥有者默认值                             |
| FormOwnerDepartment   | IFieldOption      | {"defaultValue":"dept_001"}                                  | 所属部门默认值                           |
| FormCreatedTime       | IFieldOption      | {"defaultValue":"2026-08-04T10:00:00+08:00"}                 | 创建时间默认值                           |
| FormModifiedTime      | IFieldOption      | {"defaultValue":"2026-08-04T10:00:00+08:00"}                 | 修改时间默认值                           |
| FormStatus            | IFieldOption      | {"defaultValue":"0"}                                         | 流程状态默认值                           |
| FormAssociateProperty | IFieldOption      | {"defaultValue":""}                                          | 关联属性无专用 options                   |
| FormFormula           | IFieldOption      | {"defaultValue":"0"}                                         | 公式无专用 options                       |
| FormRollup            | IFieldOption      | {"defaultValue":"0"}                                         | 汇总无专用 options                       |
| FormAttachment        | IAttachmentOption | {"defaultValue":"","maxUploadSize":10485760}                 | maxUploadSize 为单个附件允许的最大字节数 |
| FormPhoto             | IFormPhotoOption  | {"defaultValue":"","uploadMultiple":true}                    | uploadMultiple 表示是否允许上传多张图片  |

`FieldType` 的取值如下：

| 分类           | 枚举值                | 数值 | 说明                                 |
| -------------- | --------------------- | :--: | ------------------------------------ |
| 基础字段       | Unspecific            |  0   | 未指定                               |
| 基础字段       | FormTextBox           |  1   | 单行文本                             |
| 基础字段       | FormTextArea          |  2   | 多行文本                             |
| 基础字段       | FormDateTime          |  3   | 日期                                 |
| 基础字段       | FormNumber            |  4   | 数字                                 |
| 基础字段       | FormRadioButtonList   |  5   | 单选框                               |
| 基础字段       | FormCheckboxList      |  6   | 复选框                               |
| 基础字段       | FormDropDownList      |  7   | 下拉框                               |
| 基础字段       | FormCheckbox          |  8   | 是/否                                |
| 基础字段       | FormAreaSelect        |  9   | 地址                                 |
| 基础字段       | FormMap               |  10  | 位置                                 |
| 基础字段       | FormMultiUser         |  11  | 人员多选                             |
| 基础字段       | FormUser              |  12  | 人员单选                             |
| 基础字段       | FormDepartment        |  13  | 部门单选                             |
| 基础字段       | FormMultiDepartment   |  14  | 部门多选                             |
| 基础字段       | FormAttachment        |  15  | 附件                                 |
| 基础字段       | FormPhoto             |  16  | 图片                                 |
| 布局字段       | FormGroupTitle        | 101  | 分组标题                             |
| 布局字段       | FormLayout            | 102  | 一行多列                             |
| 布局字段       | FormDescription       | 103  | 描述说明                             |
| 布局字段       | FormGridView          | 104  | 子表                                 |
| 布局字段       | FormTab               | 105  | 标签页                               |
| 系统字段       | FormSeqNo             | 201  | 流水号                               |
| 系统字段       | FormCreater           | 202  | 创建人                               |
| 系统字段       | FormOwner             | 203  | 拥有者                               |
| 系统字段       | FormOwnerDepartment   | 204  | 所属部门                             |
| 系统字段       | FormCreatedTime       | 205  | 创建时间                             |
| 系统字段       | FormModifiedTime      | 206  | 修改时间                             |
| 系统字段       | FormLabel             | 207  | 创建人、创建时间、修改时间等系统字段 |
| 系统字段       | FormStatus            | 208  | 流程状态                             |
| 系统字段       | FormActivityName      | 209  | 流程当前节点                         |
| 系统字段       | FormParticipant       | 210  | 流程当前处理人                       |
| 系统字段       | FormObjectId          | 256  | ObjectId                             |
| 关联与扩展字段 | FormQuery             | 301  | 关联表单                             |
| 关联与扩展字段 | FormMultiQuery        | 302  | 关联表单多选                         |
| 关联与扩展字段 | FormAssociateProperty | 303  | 关联属性                             |
| 关联与扩展字段 | FormFormula           | 304  | 公式型控件                           |
| 关联与扩展字段 | FormButton            | 305  | 按钮                                 |
| 关联与扩展字段 | FormHandSign          | 306  | 手写签名                             |
| 关联与扩展字段 | FormOcr               | 401  | 文字识别                             |
| 关联与扩展字段 | FormAdvancedButton    | 402  | 扩展按钮                             |
| 关联与扩展字段 | FormEsign             | 403  | 电子签章                             |
| 关联与扩展字段 | FormBatchScan         | 404  | 批量扫码                             |
| 关联与扩展字段 | FormFaceRecognition   | 405  | 人脸识别                             |
| 关联与扩展字段 | FormRollup            | 501  | 汇总控件                             |
| 关联与扩展字段 | FormDynamic           | 1001 | 自定义控件                           |
| 关联与扩展字段 | FormPlugin            | 2001 | 自定义插件                           |

### AddressValue（地址信息）

| 字段   | 类型   | 说明         |
| ------ | ------ | ------------ |
| adcode | string | 行政区划编码 |
| adname | string | 行政区划名称 |
| Detail | string | 详细地址     |

### 特殊字段值类型

`JsonString<T>` 表示内容符合 `T` 结构的 JSON 字符串。创建或更新业务数据时，复杂字段应按下表结构序列化后传入。

| 类型                  | 结构或值                                            | 说明               |
| --------------------- | --------------------------------------------------- | ------------------ |
| AddressFieldValueType | `JsonString<AddressValue>`                          | 地址字段值         |
| MapFieldValueType     | `JsonString<MapValue>`                              | 定位字段值         |
| OrganizationValueType | `string[]`                                          | 人员或部门值列表   |
| MultiQueryValueType   | `string[]`                                          | 关联表单多选值列表 |
| AttachmentValueType   | `{ AttachmentIds, DelAttachmentsIds, Attachments }` | 附件字段值         |
| HandSignValueType     | `{ AttachmentIds, DelAttachmentsIds, Attachments }` | 手写签名字段值     |

`MapValue` 包含 `Address`（地址）、`CSType`（坐标系类型）、`Point` 和 `WGS84Point`；后两者均为 `{ lat: number, lng: number }`。

`AttachmentValueType` 和 `HandSignValueType` 的 `AttachmentIds`、`DelAttachmentsIds` 为以分号拼接的字符串；`Attachments` 为 `JsonString<AttachementItem[]>`，其中每个 `AttachementItem` 包含必填的 `AttachmentId` 和可选的 `Desc`。

### SchemaAcl（表单操作权限）

| 字段      | 类型    | 说明         |
| --------- | ------- | ------------ |
| addable   | boolean | 是否允许新增 |
| editable  | boolean | 是否允许编辑 |
| removable | boolean | 是否允许删除 |

### SchemaPermissionResult（表单权限结果）

| 字段             | 类型                                | 说明                           |
| ---------------- | ----------------------------------- | ------------------------------ |
| schemaAcl        | SchemaAcl                           | 表单级新增、编辑和删除权限     |
| fieldPermissions | `Record<string, FieldPermission[]>` | 按权限上下文返回的字段权限列表 |

### FieldPermission（字段权限）

| 字段     | 类型    | 说明       |
| -------- | ------- | ---------- |
| visible  | boolean | 是否可见   |
| editable | boolean | 是否可编辑 |
| required | boolean | 是否必填   |

### WorkItem（工作项）

| 字段                | 类型                  | 说明             |
| ------------------- | --------------------- | ---------------- |
| name                | string                | 工作项名称       |
| activityName        | string                | 当前活动节点名称 |
| workItemId          | string                | 工作项 ID        |
| schemaCode          | string                | 表单编码         |
| bizObjectId         | string                | 业务数据 ID      |
| instanceId          | string                | 流程实例 ID      |
| instanceState       | WorkflowInstanceState | 流程实例状态     |
| summary             | string                | 摘要             |
| workItemType        | WorkItemType          | 工作项类型       |
| workflowDisplayName | string                | 流程显示名称     |
| taskState           | WorkItemState         | 工作项状态       |
| receiveTime         | string                | 接收时间         |
| originator          | string                | 发起人 ID        |
| originatorName      | string                | 发起人名称       |

`WorkItemType`：`Fill`（0，普通工作项）、`Approve`（2，审批）、`Circulate`（3，传阅）。

`WorkItemState`：`Waiting`（0，等待）、`Working`（1，处理中）、`Finished`（2，完成）、`Canceled`（3，已取消）、`Forwarded`（6，已转交）、`Revoked`（7，撤回）、`ForBack`（201，退回）等。

`WorkflowInstanceState`：`Initiated`（0，已初始化）、`Starting`（1，启动中）、`Running`（2，运行中）、`Finishing`（3，结束中）、`Finished`（4，已完成）、`Canceled`（5，已取消）等。

### FunctionNode（功能节点）

| 字段        | 类型   | 说明     |
| ----------- | ------ | -------- |
| appCode     | string | 应用编码 |
| appName     | string | 应用名称 |
| schemaCode  | string | 表单编码 |
| schemaName  | string | 表单名称 |
| description | string | 描述     |
| icon        | string | 图标     |

## BizObject 场景类型定义

三种场景分别使用 SingleQueryBizObject、BatchQueryBizObject 和 WriteBizObject。它们都是字段编码到字段值的 key:value 对象，但子表值类型使用对应场景的 BizObject。

### SingleQueryBizObject：单条数据控件类型和值结构

单条查询返回运行时值，并为组织机构类型字段(FormUser,FormDepartment,FormMultiUser,FormMultiDepartment,FormCreater,FormOwner,FormOwnerDepartment)返回额外的扩展字段，字段编码格式为`${字段编码}Object`,内容为{ObjectId:string,Name:string,EntryId:string}。

| 控件类型                  | 控件名称     | 值类型                  | 示例                                                                           | 描述                     |
| ------------------------- | ------------ | ----------------------- | ------------------------------------------------------------------------------ | ------------------------ |
| FormTextBox               | 单行文本     | string                  | 张三                                                                           | 文本                     |
| FormTextArea              | 多行文本     | string                  | 第一行                                                                         | 多行文本                 |
| FormDateTime              | 日期         | string                  | 2026-08-04                                                                     | 日期                     |
| FormNumber                | 数字         | number                  | 12.5                                                                           | 数值                     |
| FormRadioButtonList       | 单选框       | string                  | 同意                                                                           | 选中项                   |
| FormCheckboxList          | 复选框       | string                  | A;B                                                                            | 分号拼接                 |
| FormDropDownList          | 下拉框       | string                  | 高                                                                             | 选中项                   |
| FormCheckbox              | 是/否        | boolean                 | true                                                                           | 布尔值                   |
| FormAttachment            | 附件         | AttachmenFieldValue[]   | [{fileId:f1,fileUrl:[https://example.com/a.pdf}]](https://example.com/a.pdf}]) | 附件数组                 |
| FormPhoto                 | 图片         | AttachmenFieldValue[]   | [{fileId:p1,fileUrl:[https://example.com/a.png}]](https://example.com/a.png}]) | 图片数组                 |
| FormAreaSelect            | 地址         | AddressFieldValueType   | {adcode:110108,adname:海淀区}                                                  | 地址 JSON 字符串         |
| FormMap                   | 位置         | MapFieldValueType       | {Address:中关村,Point:{lat:39.98,lng:116.31}}                                  | 定位 JSON 字符串         |
| FormUser                  | 人员单选     | string                  | user_001                                                                       | 人员 ID                  |
| FormMultiUser             | 人员多选     | string[]                | [user_001,user_002]                                                            | 人员 ID 数组             |
| FormDepartment            | 部门单选     | string                  | dept_001                                                                       | 部门 ID                  |
| FormMultiDepartment       | 部门多选     | string[]                | [dept_001,dept_002]                                                            | 部门 ID 数组             |
| FormGridView              | 子表         | SingleQueryBizObject[]  | [{ObjectId:child_1,Name:第1行,ParentObjectId:bo_1}]                            | 单条查询返回的子表行数组 |
| FormSeqNo                 | 流水号       | string                  | NO-001                                                                         | 自动编号                 |
| FormCreater               | 创建人       | string                  | user_001                                                                       | 创建人 ID                |
| FormOwner                 | 拥有者       | string                  | user_002                                                                       | 拥有者 ID                |
| FormOwnerDepartment       | 所属部门     | string                  | dept_001                                                                       | 所属部门 ID              |
| FormCreatedTime           | 创建时间     | string                  | 2026-08-04T10:00:00+08:00                                                      | 创建时间                 |
| FormModifiedTime          | 修改时间     | string                  | 2026-08-04T11:00:00+08:00                                                      | 修改时间                 |
| FormStatus                | 流程状态     | number                  | 2                                                                              | 状态值                   |
| FormQuery                 | 关联表单     | string                  | bo_001                                                                         | 关联数据 ID              |
| FormMultiQuery            | 关联表单多选 | string[]                | [bo_001,bo_002]                                                                | 关联数据 ID 数组         |
| FormAssociateProperty     | 关联属性     | unknown                 | null                                                                           | null                     |
| FormFormula               | 公式         | number                  | 100                                                                            | 公式结果                 |
| FormRollup                | 汇总         | unknown                 | null                                                                           | null                     |
| FormUserObject            | 人员单选扩展 | LoadedReferenceObject   | {ObjectId:user_001,Name:张三,EntryId:e1}                                       | 字段编码Object           |
| FormMultiUserObject       | 人员多选扩展 | LoadedReferenceObject[] | [{ObjectId:user_001,Name:张三,EntryId:e1}]                                     | 字段编码Object           |
| FormDepartmentObject      | 部门单选扩展 | LoadedReferenceObject   | {ObjectId:dept_001,Name:研发部,EntryId:e2}                                     | 字段编码Object           |
| FormMultiDepartmentObject | 部门多选扩展 | LoadedReferenceObject[] | [{ObjectId:dept_001,Name:研发部,EntryId:e2}]                                   | 字段编码Object           |
| FormCreaterObject         | 创建人扩展   | LoadedReferenceObject   | {ObjectId:user_001,Name:张三,EntryId:e1}                                       | CreatedByObject          |
| FormOwnerObject           | 拥有者扩展   | LoadedReferenceObject   | {ObjectId:user_002,Name:李四,EntryId:e3}                                       | OwnerIdObject            |
| FormOwnerDepartmentObject | 所属部门扩展 | LoadedReferenceObject   | {ObjectId:dept_001,Name:研发部,EntryId:e2}                                     | OwnerDeptIdObject        |

### BatchQueryBizObject：批量查询时控件值类型和结构

BatchQueryBizObject 的直接值与 SingleQueryBizObject 一致，不支持子表字段，同时并不会为组织机构类型字段返回扩展字段；

| 控件类型              | 控件名称     | 值类型                | 示例                      | 描述             |
| --------------------- | ------------ | --------------------- | ------------------------- | ---------------- |
| FormTextBox           | 单行文本     | string                | 张三                      | 文本             |
| FormTextArea          | 多行文本     | string                | 说明                      | 多行文本         |
| FormDateTime          | 日期         | string                | 2026-08-04                | 日期             |
| FormNumber            | 数字         | number                | 12.5                      | 数值             |
| FormRadioButtonList   | 单选框       | string                | 同意                      | 选中项           |
| FormCheckboxList      | 复选框       | string                | A;B                       | 分号拼接         |
| FormDropDownList      | 下拉框       | string                | 高                        | 选中项           |
| FormCheckbox          | 是/否        | boolean               | true                      | 布尔值           |
| FormAttachment        | 附件         | AttachmenFieldValue[] | [{fileId:f1,fileUrl:url}] | 附件数组         |
| FormPhoto             | 图片         | AttachmenFieldValue[] | [{fileId:p1,fileUrl:url}] | 图片数组         |
| FormAreaSelect        | 地址         | AddressFieldValueType | {adcode:110108}           | 地址 JSON 字符串 |
| FormMap               | 位置         | MapFieldValueType     | {Address:中关村}          | 定位 JSON 字符串 |
| FormUser              | 人员单选     | string                | user_001                  | 无               |
| FormMultiUser         | 人员多选     | string[]              | [user_001]                | 无               |
| FormDepartment        | 部门单选     | string                | dept_001                  | 无               |
| FormMultiDepartment   | 部门多选     | string[]              | [dept_001]                | 无               |
| FormSeqNo             | 流水号       | string                | NO-001                    | 自动编号         |
| FormCreater           | 创建人       | string                | user_001                  | 无               |
| FormOwner             | 拥有者       | string                | user_002                  | 无               |
| FormOwnerDepartment   | 所属部门     | string                | dept_001                  | 无               |
| FormCreatedTime       | 创建时间     | string                | 2026-08-04T10:00:00+08:00 | 创建时间         |
| FormModifiedTime      | 修改时间     | string                | 2026-08-04T11:00:00+08:00 | 修改时间         |
| FormStatus            | 流程状态     | number                | 2                         | 状态值           |
| FormQuery             | 关联表单     | string                | bo_001                    | 关联数据 ID      |
| FormMultiQuery        | 关联表单多选 | string[]              | [bo_001]                  | 关联数据 ID 数组 |
| FormAssociateProperty | 关联属性     | unknown               | null                      | null             |
| FormFormula           | 公式         | number                | 100                       | 公式结果         |
| FormRollup            | 汇总         | unknown               | null                      | null             |

### WriteBizObject：新增、编辑时控件值结构

WriteBizObject 是新增和编辑使用的字段编码到字段值对象。

| 控件类型            | 控件名称     | 值类型                         | 示例                                                                                                                 | 描述                                                                      |
| ------------------- | ------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| FormTextBox         | 单行文本     | CommonValueType/string         | 张三                                                                                                                 | 文本                                                                      |
| FormTextArea        | 多行文本     | CommonValueType/string         | 说明                                                                                                                 | 多行文本                                                                  |
| FormNumber          | 数字         | CommonValueType/string         | 12.5                                                                                                                 | 数字按字符串传入                                                          |
| FormDateTime        | 日期         | CommonValueType/string         | 2026-08-04                                                                                                           | 日期字符串                                                                |
| FormDropDownList    | 下拉框       | CommonValueType/string         | 高                                                                                                                   | 选中项                                                                    |
| FormRadioButtonList | 单选框       | CommonValueType/string         | 同意                                                                                                                 | 选中项                                                                    |
| FormQuery           | 关联表单     | CommonValueType/string         | bo_001                                                                                                               | 关联数据 ID                                                               |
| FormCheckboxList    | 复选框       | CheckboxListValueType/string   | A;B                                                                                                                  | 分号拼接                                                                  |
| FormCheckbox        | 是/否        | BooleanValueType/boolean       | true                                                                                                                 | 布尔值                                                                    |
| FormMap             | 位置         | MapFieldValueType              | "{"Address":"中关村","CSType":1,"Point":{"lat":39.9834,"lng":116.3162},"WGS84Point":{"lat":39.9828,"lng":116.3221}}" | MapValue 序列化后的 JSON 字符串，包含地址、坐标系类型及 GCJ-02/WGS84 坐标 |
| FormAreaSelect      | 地址         | AddressFieldValueType          | "{"adcode":"110108","adname":"北京市海淀区","Detail":"中关村大街 1 号"}"                                             | AddressValue 序列化后的 JSON 字符串，包含行政区划编码、地址名称和详细地址 |
| FormUser            | 人员单选     | OrganizationValueType/string[] | [user_001]                                                                                                           | 单选也传数组                                                              |
| FormMultiUser       | 人员多选     | OrganizationValueType/string[] | [user_001,user_002]                                                                                                  | 人员 ID 数组                                                              |
| FormDepartment      | 部门单选     | OrganizationValueType/string[] | [dept_001]                                                                                                           | 单选也传数组                                                              |
| FormMultiDepartment | 部门多选     | OrganizationValueType/string[] | [dept_001,dept_002]                                                                                                  | 部门 ID 数组                                                              |
| FormOwner           | 拥有者       | OrganizationValueType/string[] | [user_002]                                                                                                           | 拥有者 ID 数组                                                            |
| FormOwnerDepartment | 所属部门     | OrganizationValueType/string[] | [dept_001]                                                                                                           | 所属部门 ID 数组                                                          |
| FormMultiQuery      | 关联表单多选 | MultiQueryValueType/string[]   | [bo_001,bo_002]                                                                                                      | 关联数据 ID 数组                                                          |
| FormGridView        | 子表         | WriteBizObject[]               | [{F0001:第一行},{F0001:第二行}]                                                                                      | 每一行都是 WriteBizObject 的写入规则                                      |

## 错误码与提示信息

接口调用失败时，返回结构为 { errorCode, errorMessage, data: null }；errorMessage 使用下表中的可读提示。

| 错误码 | 提示信息                   |
| -----: | -------------------------- |
| 100100 | 网络错误，请检查网络后重试 |
| 100200 | 请求过于频繁，请稍后重试   |
| 100300 | 请求参数不合法             |
| 100301 | 缺少必填参数               |
| 100302 | 参数类型不正确             |
| 100303 | 参数值不合法               |
| 100304 | 分页参数不合法             |
| 100305 | 业务数据结构不合法         |
| 100306 | 筛选条件不合法             |
| 100307 | 排序条件不合法             |
| 100400 | 未登录或登录状态已失效     |
| 100401 | 登录凭证已过期，请重新登录 |
| 100402 | 无权执行此操作             |
| 100500 | 服务内部异常，请稍后重试   |
| 100501 | 上游服务异常，请稍后重试   |
| 100502 | 服务暂不可用，请稍后重试   |
| 200104 | 未找到指定的应用           |
| 200105 | 无权访问指定的应用         |
| 200201 | 缺少必填字段               |
| 200202 | 当前业务数据不允许删除     |
| 200203 | 字段不允许修改             |
| 200204 | 未找到指定的表单           |
| 200205 | 无权访问指定的表单         |
| 200206 | 未找到指定的业务数据       |
| 200207 | 字段值不合法               |
| 200208 | 业务数据校验失败           |
| 200209 | 业务数据已存在             |
| 200210 | 业务数据筛选条件不合法     |
| 200211 | 业务数据排序条件不合法     |
| 200302 | 未找到指定的待办工作项     |
| 200303 | 无权处理指定的待办工作项   |
| 200304 | 当前待办工作项不可处理     |
| 200305 | 审批动作不合法             |
| 200306 | 部分待办工作项审批失败     |
| 200401 | 未找到指定的人员或部门     |
| 200501 | 未找到匹配的地址信息       |
| 200601 | 文件地址不合法或无法访问   |
| 200602 | 文件转存失败，请稍后重试   |
