# SAP 数据查询 Skill

## 概述

**专供明辉集团SAP数据查询使用**

本Skill封装了明辉集团SAP系统的完整数据查询流程，支持企业微信认证、BAPI调用、表数据查询等功能。所有查询均符合明辉集团内部数据标准和格式要求。

## 功能特性

### 1. 企业微信认证
- 自动收集用户身份证后六位信息
- 获取SAP访问票据（Ticket）
- 安全认证管理

### 2. BAPI调用
- 支持标准SAP BAPI调用
- 自动参数格式化
- 物料条码补0到18位
- 生产订单号补0到12位

### 3. 表数据查询
- 支持SAP表和视图查询
- 智能查询构建
- 分页查询支持
- 复杂过滤条件

### 4. 智能查询
- 根据用户意图自动构建查询
- 自动选择返回字段
- 智能过滤条件生成

### 5. 结果处理
- 标准化输出格式
- 结果导出（JSON/Excel/CSV）
- 查询历史记录

## 执行步骤

### 步骤1：安装与配置

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件配置API端点
```

### 步骤2：用户认证

```python
from sap_data_query_skill import SAPDataQuerySkill

# 创建Skill实例
skill = SAPDataQuerySkill()

# 用户认证（交互式）
auth_result = skill.authenticate()
# 或指定参数
auth_result = skill.authenticate(
    work_code="MS00051286",
    identity="123456"  # 身份证后六位
)
```

### 步骤3：BAPI调用

```python
# 调用物料主数据BAPI
bapi_result = skill.query_bapi(
    rfc_name="BAPI_MATERIAL_GET_DETAIL",
    params={
        "MATERIAL": "000000000000001234"
    }
)

# 自动格式化物料条码
formatted_code = skill.format_material_code("1234")
# 返回: "000000000000001234"
```

### 步骤4：表数据查询

```python
# 查询物料主数据表
table_result = skill.query_table(
    table_name="MARA",
    fields=["MATNR", "MAKTX", "MEINS", "MATKL"],
    filters=[
        {
            "FieldName": "MATKL",
            "Calculation": "Equal",
            "Lower": "ROH"
        }
    ],
    orders=[
        {
            "FieldName": "MATNR",
            "Direction": "Ascend"
        }
    ],
    page_size=1000
)
```

### 步骤5：智能查询

```python
# 根据意图自动查询
intelligent_result = skill.intelligent_query(
    table_name="MARA",
    query_intent="查询2024年创建的原材料物料，按物料号排序",
    page_size=500
)
```

### 步骤6：结果处理

```python
# 导出结果
export_result = skill.export_results(
    result=table_result,
    format="excel",
    file_path="物料查询结果.xlsx"
)

# 查看查询历史
history = skill.get_query_history(limit=5)

# 获取Skill状态
status = skill.get_status()
```

## 输出标准

### 1. 认证输出格式

```json
{
    "success": true,
    "ticket": "xxxxx-xxxxx-xxxxx",
    "work_code": "MS00051286",
    "user_name": "张三",
    "expires_at": "2024-12-31 23:59:59",
    "error": null
}
```

### 2. BAPI调用输出格式

```json
{
    "success": true,
    "rfc_name": "BAPI_MATERIAL_GET_DETAIL",
    "execution_time": 1.23,
    "data": {
        "MATERIAL_GENERAL_DATA": {...},
        "PLANT_DATA": [...]
    },
    "statistics": {
        "rows_returned": 1,
        "fields_count": 15
    },
    "error": null
}
```

### 3. 表查询输出格式

```json
{
    "success": true,
    "table_name": "MARA",
    "query_config": {...},
    "data": [
        {
            "MATNR": "000000000000001234",
            "MAKTX": "原材料A",
            "MEINS": "KG",
            "MATKL": "ROH"
        }
    ],
    "statistics": {
        "row_count": 1250,
        "query_rows": 100,
        "page_size": 100,
        "current_page": 0,
        "total_pages": 13,
        "fields": [
            {
                "field_name": "MATNR",
                "display_name": "物料号",
                "data_type": "CHAR"
            }
        ]
    },
    "execution_time": 2.45,
    "error": null
}
```

### 4. 错误输出格式

```json
{
    "success": false,
    "error": "认证失败：身份证信息错误",
    "error_type": "authentication_failed",
    "error_code": "AUTH001",
    "suggestion": "请检查身份证后六位是否正确",
    "timestamp": "2024-04-22 12:30:45"
}
```

## 参数格式化规则

### 1. 物料条码格式化
- 输入：数字字符串
- 规则：左侧补0到18位
- 示例：`"1234"` → `"000000000000001234"`

### 2. 生产订单号格式化
- 输入：数字字符串
- 规则：左侧补0到12位
- 示例：`"5678"` → `"000000005678"`

### 3. 日期格式化
- SAP日期格式：YYYYMMDD
- 转换示例：`"2024-04-22"` → `"20240422"`

## 查询限制

### 1. 分页限制
- 最大每页数量：10000行
- 最大总页数：100页
- 默认每页数量：1000行

### 2. 字段限制
- 最大返回字段数：50个
- 建议字段数：≤20个

### 3. 性能限制
- 查询超时时间：60秒
- 最大数据量：100万行
- 建议数据量：≤10万行

## 安全要求

### 1. 认证信息
- 身份证后六位仅用于认证
- 认证票据（Ticket）有效期为24小时
- 不同用户需要重新认证

### 2. 数据保护
- 敏感数据自动脱敏
- 错误信息适当隐藏
- 查询日志加密存储

### 3. 访问控制
- 仅限明辉集团内部网络访问
- IP白名单限制
- 访问频率限制

## 维护与支持

### 1. 故障处理
- 认证失败：检查网络和身份证信息
- 查询超时：减少查询数据量
- 数据错误：验证参数格式

### 2. 性能优化
- 使用分页查询大数据
- 选择必要字段
- 添加合适过滤条件

### 3. 技术支持
- 问题反馈：it-support@minghuigroup.com
- 文档更新：每月第一个工作日
- 版本升级：季度发布

## 版本历史

### v1.0.0 (2024-04-22)
- 初始版本发布
- 支持企业微信认证
- 支持BAPI调用和表查询
- 标准化输出格式

---

**注意：本Skill仅限明辉集团内部使用，未经授权不得外传。**