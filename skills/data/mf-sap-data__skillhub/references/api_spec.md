# SAP 数据查询 API 规范

## 概述

本文档定义了明辉集团SAP数据查询Skill的API接口规范，包括认证接口、BAPI调用接口和表数据查询接口。

## 认证接口

### 1. 获取认证票据

**端点**: `POST https://info02.mingfaigroup.com/api/account/agent/getticket`

**请求参数**:
```json
{
    "WorkCode": "MS00051286",
    "Identity": "123456",
    "AppName": "mf.portal.agent",
    "AppVersion": "1.0"
}
```

**参数说明**:
- `WorkCode`: 用户工号
- `Identity`: 身份证后六位
- `AppName`: 应用名称，固定为 `mf.portal.agent`
- `AppVersion`: 应用版本，固定为 `1.0`

**成功响应**:
```json
{
    "Code": 0,
    "Message": "成功",
    "Data": {
        "Ticket": "xxxxx-xxxxx-xxxxx",
        "WorkCode": "MS00051286",
        "UserName": "张三",
        "Department": "IT部门"
    }
}
```

**错误响应**:
```json
{
    "Code": 1001,
    "Message": "身份证验证失败"
}
```

**错误码说明**:
- `0`: 成功
- `1001`: 身份证验证失败
- `1002`: 工号不存在
- `1003`: 应用未授权
- `1004`: 票据已过期
- `1005`: 系统内部错误

## BAPI调用接口

### 2. 调用SAP BAPI

**端点**: `POST https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke?ticket={Token}`

**请求参数**:
```json
{
    "RfcName": "BAPI_MATERIAL_GET_DETAIL",
    "Data": {
        "MATERIAL": "000000000000001234"
    }
}
```

**参数说明**:
- `RfcName`: BAPI名称
- `Data`: 调用参数，根据具体BAPI定义

**URL参数**:
- `ticket`: 认证票据，从认证接口获取

**成功响应**:
```json
{
    "Code": 0,
    "Message": "成功",
    "Data": {
        "MATERIAL_GENERAL_DATA": {
            "MATERIAL": "000000000000001234",
            "MAKTX": "原材料A",
            "MEINS": "KG"
        },
        "PLANT_DATA": [
            {
                "PLANT": "1000",
                "STPRS": "100.00"
            }
        ]
    }
}
```

**错误响应**:
```json
{
    "Code": 2001,
    "Message": "BAPI调用失败: 物料不存在"
}
```

**错误码说明**:
- `0`: 成功
- `2001`: BAPI调用失败
- `2002`: 参数验证失败
- `2003`: 权限不足
- `2004`: 系统繁忙
- `2005`: 超时错误

## 表结构查询接口

### 3. 获取表结构信息

**端点**: `GET https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns?ticket={Token}&tableName={TableName}`

**URL参数**:
- `ticket`: 认证票据
- `tableName`: 表名

**成功响应**:
```json
{
    "Code": 0,
    "Message": "成功",
    "Data": [
        {
            "ColumnName": "MATNR",
            "DisplayName": "物料号",
            "DataType": "CHAR",
            "Length": 18,
            "IsKey": true,
            "Description": "物料编号"
        },
        {
            "ColumnName": "MAKTX",
            "DisplayName": "物料描述",
            "DataType": "CHAR",
            "Length": 40,
            "IsKey": false,
            "Description": "物料描述"
        }
    ]
}
```

## 表数据查询接口

### 4. 查询表数据

**端点**: `POST https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata?ticket={Token}`

**请求参数**:
```json
{
    "TableName": "MARA",
    "CurrentPage": 0,
    "PageSize": 10000,
    "LanguageTable": "MAKT",
    "Fields": ["MATNR", "MAKTX", "MEINS"],
    "Orders": [
        {
            "FieldName": "MATNR",
            "Direction": "Ascend"
        }
    ],
    "Filters": [
        {
            "Logic": "And",
            "FieldName": "MATKL",
            "Calculation": "Equal",
            "Lower": "ROH"
        }
    ]
}
```

**参数说明**:

#### 4.1 基本参数
- `TableName`: 表名（必需）
- `CurrentPage`: 当前页码，从0开始（必需）
- `PageSize`: 每页数量，最大10000（必需）
- `LanguageTable`: 语言表，用于获取字段描述（可选）

#### 4.2 字段参数
- `Fields`: 返回字段列表（可选，默认返回所有字段）

#### 4.3 排序参数
- `Orders`: 排序条件列表（可选）
  - `FieldName`: 排序字段
  - `Direction`: 排序方向，可选值：`"Ascend"`（升序）、`"Descend"`（降序）、`""`（默认）

#### 4.4 过滤参数
- `Filters`: 过滤条件列表（可选）
  - `Logic`: 逻辑运算符，可选值：`"And"`、`"Or"`、`""`（默认）
  - `FieldName`: 过滤字段
  - `Calculation`: 计算符（见下文）
  - `Lower`: 低值
  - `Hights`: 高值（数组，用于IN/BETWEEN操作）

**计算符说明**:
- `"Empty"`: 空字符（仅使用Lower）
- `"Equal"`: 等于（仅使用Lower）
- `"Great"`: 大于（仅使用Lower）
- `"Less"`: 小于（仅使用Lower）
- `"NotEqual"`: 不等于（仅使用Lower）
- `"GreatEqual"`: 大于等于（仅使用Lower）
- `"LessEqual"`: 小于等于（仅使用Lower）
- `"Between"`: 介于（使用Lower和Hights）
- `"NotBetween"`: 不介于（使用Lower和Hights）
- `"Like"`: 相似（仅使用Lower，支持%通配符）
- `"NotLike"`: 不相似（仅使用Lower，支持%通配符）
- `"In"`: 在列表中（Hights为数组）
- `"NotIn"`: 不在列表中（Hights为数组）

**成功响应**:
```json
{
    "Code": 0,
    "Message": "成功",
    "Data": {
        "RowCount": 1250,
        "Fields": [
            {
                "FieldName": "MATNR",
                "DisplayName": "物料号"
            },
            {
                "FieldName": "MAKTX",
                "DisplayName": "物料描述"
            }
        ],
        "Data": [
            {
                "MATNR": "000000000000001234",
                "MAKTX": "原材料A",
                "MEINS": "KG"
            },
            {
                "MATNR": "000000000000001235",
                "MAKTX": "原材料B",
                "MEINS": "KG"
            }
        ]
    }
}
```

**响应说明**:
- `RowCount`: 总行数
- `Fields`: 字段信息列表，包含字段名和显示名
- `Data`: 查询到的数据列表

**错误响应**:
```json
{
    "Code": 3001,
    "Message": "表不存在"
}
```

**错误码说明**:
- `0`: 成功
- `3001`: 表不存在
- `3002`: 字段不存在
- `3003`: 过滤条件错误
- `3004`: 排序条件错误
- `3005`: 分页参数错误
- `3006`: 数据量过大
- `3007`: 查询超时

## 通用规范

### 1. 请求头
所有请求必须包含以下请求头：
```http
Content-Type: application/json
User-Agent: {AppName}/{AppVersion}
```

### 2. 响应格式
所有响应使用统一格式：
```json
{
    "Code": 0,
    "Message": "描述信息",
    "Data": {}
}
```

### 3. 错误处理
- HTTP状态码200表示请求已接收
- API错误通过`Code`字段表示
- 客户端应根据`Code`进行相应处理

### 4. 超时设置
- 认证接口：30秒
- BAPI调用：60秒
- 表查询：60秒

### 5. 重试机制
- 网络错误：自动重试2次
- 服务器错误：根据错误码决定是否重试
- 超时错误：自动重试1次

## 安全规范

### 1. 认证要求
- 所有接口必须提供有效的`ticket`
- `ticket`有效期为24小时
- 过期后需要重新认证

### 2. 数据保护
- 敏感数据在传输中加密
- 错误信息适当隐藏
- 查询日志脱敏存储

### 3. 访问控制
- IP白名单限制
- 访问频率限制：每分钟100次
- 并发连接限制：每用户10个

## 性能规范

### 1. 查询限制
- 最大返回行数：10000行/页
- 最大总数据量：100万行
- 建议数据量：≤10万行

### 2. 字段限制
- 最大返回字段数：50个
- 建议字段数：≤20个

### 3. 过滤优化
- 使用索引字段过滤
- 避免全表扫描
- 合理使用分页

## 版本管理

### 当前版本
- API版本：v1.0
- 发布日期：2024-04-22
- 兼容性：向后兼容

### 版本更新
- 每月第一个工作日更新文档
- 重大变更提前30天通知
- 版本号遵循语义化版本规范

## 支持与反馈

- 技术支持：it-support@minghuigroup.com
- 问题反馈：通过工单系统
- 文档更新：内部Wiki

---

**注意：本API仅限明辉集团内部使用，未经授权不得外传。**