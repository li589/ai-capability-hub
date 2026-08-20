# SAP 数据查询格式标准

## 概述

本文档定义了明辉集团SAP数据查询的输入输出格式标准，确保数据的一致性和可读性。

## 数据格式化规则

### 1. 物料条码格式化

**规则**: 左侧补0到18位

**示例**:
- 输入: `"1234"`
- 输出: `"000000000000001234"`

**处理逻辑**:
```python
def format_material_code(code):
    # 移除空格和特殊字符
    cleaned = str(code).strip()
    
    # 提取数字部分
    numbers = re.findall(r'\d+', cleaned)
    if numbers:
        # 取最长的数字序列
        longest = max(numbers, key=len)
        return longest.zfill(18)
    
    return cleaned
```

**适用字段**:
- `MATNR` (物料号)
- `MATERIAL` (物料)
- 其他物料相关字段

### 2. 生产订单号格式化

**规则**: 左侧补0到12位

**示例**:
- 输入: `"5678"`
- 输出: `"000000005678"`

**处理逻辑**:
```python
def format_production_order(order):
    cleaned = str(order).strip()
    
    if cleaned.isdigit():
        return cleaned.zfill(12)
    
    numbers = re.findall(r'\d+', cleaned)
    if numbers:
        longest = max(numbers, key=len)
        return longest.zfill(12)
    
    return cleaned
```

**适用字段**:
- `AUFNR` (生产订单)
- `ORDER_NUMBER` (订单号)

### 3. 日期格式化

**规则**: 统一为YYYYMMDD格式

**输入格式**:
- `"2024-04-22"`
- `"2024/04/22"`
- `"2024年04月22日"`

**输出格式**: `"20240422"`

**处理逻辑**:
```python
def format_date(date_str):
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue
    
    return date_str
```

**适用字段**:
- `ERSDA` (创建日期)
- `ERDAT` (创建日期)
- `AEDAT` (最后修改日期)
- `BUDAT` (过账日期)
- 其他日期字段

### 4. 金额格式化

**规则**: 保留2位小数，千分位分隔

**示例**:
- 输入: `1234567.89`
- 输出: `"1,234,567.89"`

**处理逻辑**:
```python
def format_amount(amount):
    try:
        value = float(amount)
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return str(amount)
```

**适用字段**:
- `NETWR` (净价值)
- `WRBTR` (金额)
- `DMBTR` (本币金额)

## 查询参数格式

### 1. 过滤条件格式

**基本格式**:
```json
{
    "Logic": "And",
    "FieldName": "MATKL",
    "Calculation": "Equal",
    "Lower": "ROH"
}
```

**计算符对照表**:

| 计算符 | 说明 | Lower | Hights |
|--------|------|-------|---------|
| `Empty` | 空字符 | 值 | - |
| `Equal` | 等于 | 值 | - |
| `Great` | 大于 | 值 | - |
| `Less` | 小于 | 值 | - |
| `NotEqual` | 不等于 | 值 | - |
| `GreatEqual` | 大于等于 | 值 | - |
| `LessEqual` | 小于等于 | 值 | - |
| `Between` | 介于 | 最小值 | 最大值 |
| `NotBetween` | 不介于 | 最小值 | 最大值 |
| `Like` | 相似 | 模式（支持%） | - |
| `NotLike` | 不相似 | 模式（支持%） | - |
| `In` | 在列表中 | - | 值数组 |
| `NotIn` | 不在列表中 | - | 值数组 |

**示例**:

1. 等于查询:
```json
{
    "FieldName": "MATKL",
    "Calculation": "Equal",
    "Lower": "ROH"
}
```

2. 范围查询:
```json
{
    "FieldName": "ERSDA",
    "Calculation": "Between",
    "Lower": "20240101",
    "Hights": "20241231"
}
```

3. 模糊查询:
```json
{
    "FieldName": "MAKTX",
    "Calculation": "Like",
    "Lower": "%原材料%"
}
```

4. 列表查询:
```json
{
    "FieldName": "WERKS",
    "Calculation": "In",
    "Hights": ["1000", "2000", "3000"]
}
```

### 2. 排序条件格式

**基本格式**:
```json
{
    "FieldName": "MATNR",
    "Direction": "Ascend"
}
```

**方向说明**:
- `"Ascend"`: 升序（默认）
- `"Descend"`: 降序
- `""`: 默认排序

**多字段排序**:
```json
[
    {
        "FieldName": "MATKL",
        "Direction": "Ascend"
    },
    {
        "FieldName": "MATNR",
        "Direction": "Descend"
    }
]
```

### 3. 分页参数格式

**参数**:
- `CurrentPage`: 当前页码，从0开始
- `PageSize`: 每页数量，最大10000

**示例**:
```json
{
    "CurrentPage": 0,
    "PageSize": 1000
}
```

**计算总页数**:
```python
total_pages = (row_count + page_size - 1) // page_size
```

## 输出格式标准

### 1. 认证输出格式

**成功响应**:
```json
{
    "success": true,
    "ticket": "xxxxx-xxxxx-xxxxx",
    "work_code": "MS00051286",
    "user_name": "张三",
    "expires_at": "2024-12-31 23:59:59",
    "department": "IT部门",
    "message": "认证成功"
}
```

**错误响应**:
```json
{
    "success": false,
    "error": "身份证验证失败",
    "error_type": "authentication_failed",
    "error_code": "AUTH001",
    "suggestion": "请检查身份证后六位是否正确",
    "timestamp": "2024-04-22 12:30:45"
}
```

### 2. BAPI调用输出格式

**成功响应**:
```json
{
    "success": true,
    "rfc_name": "BAPI_MATERIAL_GET_DETAIL",
    "bapi_name": "获取物料详细信息",
    "execution_time": 1.23,
    "data": {
        "MATERIAL_GENERAL_DATA": {
            "MATERIAL": "000000000000001234",
            "MAKTX": "原材料A",
            "MEINS": "KG"
        }
    },
    "structure": {
        "tables": [
            {
                "name": "PLANT_DATA",
                "row_count": 5,
                "columns": ["PLANT", "STPRS"]
            }
        ],
        "structures": [
            {
                "name": "MATERIAL_GENERAL_DATA",
                "fields": ["MATERIAL", "MAKTX", "MEINS"]
            }
        ]
    },
    "statistics": {
        "tables_count": 1,
        "structures_count": 1,
        "total_rows": 5,
        "fields_count": 5
    },
    "timestamp": "2024-04-22 12:30:45"
}
```

### 3. 表查询输出格式

**成功响应**:
```json
{
    "success": true,
    "table_name": "MARA",
    "execution_time": 2.45,
    "query_config": {
        "fields": ["MATNR", "MAKTX", "MEINS"],
        "filters": [
            {
                "FieldName": "MATKL",
                "Calculation": "Equal",
                "Lower": "ROH"
            }
        ],
        "page_size": 1000,
        "current_page": 0
    },
    "data": [
        {
            "MATNR": "000000000000001234",
            "MAKTX": "原材料A",
            "MEINS": "KG"
        }
    ],
    "statistics": {
        "row_count": 1250,
        "query_rows": 100,
        "page_size": 1000,
        "current_page": 0,
        "total_pages": 2,
        "has_more": true,
        "fields_count": 3
    },
    "structure": {
        "total_rows": 1250,
        "returned_rows": 100,
        "fields_count": 3,
        "columns_info": [
            {
                "field_name": "MATNR",
                "display_name": "物料号",
                "data_type": "CHAR",
                "length": 18,
                "description": "物料编号"
            }
        ]
    },
    "field_mapping": [
        {
            "field_name": "MATNR",
            "display_name": "物料号",
            "data_type": "CHAR",
            "is_key": true,
            "description": "物料编号"
        }
    ],
    "timestamp": "2024-04-22 12:30:45"
}
```

### 4. 错误输出格式

**通用错误格式**:
```json
{
    "success": false,
    "error": "错误描述",
    "error_type": "错误类型",
    "error_code": "错误代码",
    "suggestion": "解决建议",
    "timestamp": "错误时间",
    "context": {
        "table_name": "表名",
        "query_intent": "查询意图"
    }
}
```

**错误类型对照表**:

| 错误类型 | 说明 | 错误代码范围 |
|----------|------|-------------|
| `authentication_failed` | 认证失败 | AUTH001-AUTH999 |
| `bapi_invoke_failed` | BAPI调用失败 | BAPI001-BAPI999 |
| `table_query_failed` | 表查询失败 | TABLE001-TABLE999 |
| `parameter_validation_failed` | 参数验证失败 | PARAM001-PARAM999 |
| `connection_error` | 连接错误 | CONN001-CONN999 |
| `timeout_error` | 超时错误 | TIME001-TIME999 |
| `system_error` | 系统错误 | SYS001-SYS999 |

## 数据导出格式

### 1. JSON导出格式

**文件格式**: `.json`

**内容格式**:
```json
{
    "export_info": {
        "skill_version": "1.0.0",
        "export_time": "2024-04-22 12:30:45",
        "table_name": "MARA",
        "total_rows": 1250,
        "exported_rows": 100
    },
    "query_config": {
        "fields": ["MATNR", "MAKTX", "MEINS"],
        "filters": [],
        "orders": []
    },
    "data": [
        {
            "MATNR": "000000000000001234",
            "MAKTX": "原材料A",
            "MEINS": "KG"
        }
    ],
    "field_mapping": [
        {
            "field_name": "MATNR",
            "display_name": "物料号"
        }
    ]
}
```

### 2. Excel导出格式

**文件格式**: `.xlsx`

**工作表结构**:
1. **数据**工作表: 包含查询数据
2. **字段说明**工作表: 包含字段映射信息
3. **查询信息**工作表: 包含查询配置和统计信息

**列格式**:
- 使用字段显示名作为列标题
- 数据格式化显示
- 冻结首行

### 3. CSV导出格式

**文件格式**: `.csv`

**编码**: UTF-8 with BOM

**分隔符**: 逗号（,）

**内容格式**:
```csv
物料号,物料描述,基本单位
000000000000001234,原材料A,KG
000000000000001235,原材料B,KG
```

## 日志格式标准

### 1. 查询日志格式

**日志级别**: INFO

**格式**:
```
[2024-04-22 12:30:45] INFO - 查询执行 - table=MARA, rows=100, time=2.45s
[2024-04-22 12:30:45] INFO - 查询配置 - fields=3, filters=1, page=0
[2024-04-22 12:30:45] INFO - 查询结果 - total=1250, returned=100
```

### 2. 错误日志格式

**日志级别**: ERROR

**格式**:
```
[2024-04-22 12:30:45] ERROR - 认证失败 - error_type=authentication_failed, error_code=AUTH001
[2024-04-22 12:30:45] ERROR - 错误详情 - message=身份证验证失败, suggestion=请检查身份证后六位
```

### 3. 性能日志格式

**日志级别**: DEBUG

**格式**:
```
[2024-04-22 12:30:45] DEBUG - 性能统计 - total_queries=10, avg_time=1.23s, success_rate=90%
[2024-04-22 12:30:45] DEBUG - 缓存统计 - cache_hits=85, cache_misses=15, hit_rate=85%
```

## 编码规范

### 1. 字符编码
- 所有文本数据使用UTF-8编码
- 文件导出使用UTF-8 with BOM
- API请求和响应使用UTF-8

### 2. 日期时间格式
- 日期: YYYY-MM-DD
- 时间: HH:MM:SS
- 日期时间: YYYY-MM-DD HH:MM:SS
- SAP日期: YYYYMMDD

### 3. 数字格式
- 整数: 无千分位分隔
- 小数: 保留2位小数
- 金额: 千分位分隔，保留2位小数

### 4. 布尔值格式
- JSON: `true`/`false`
- 字符串: `"true"`/`"false"`
- 数字: `1`/`0`

## 兼容性说明

### 1. 向后兼容
- 新增字段不影响现有功能
- 字段改名提供别名支持
- 格式变更提供转换函数

### 2. 向前兼容
- 支持旧版本数据格式
- 提供格式升级工具
- 维护转换文档

### 3. 版本管理
- 主版本号: 重大变更
- 次版本号: 功能增强
- 修订号: 问题修复

---

**注意：本格式标准仅限明辉集团内部使用，未经授权不得外传。**