# SAP 数据查询 Skill

## 快速开始

### 安装

```bash
# 1. 下载Skill包
# 2. 解压文件
unzip sap_data_query_skill_v1.0.0.zip

# 3. 进入目录
cd sap_data_query_skill

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境
cp .env.example .env
# 编辑.env文件配置API端点
```

### 基本使用

```python
from sap_data_query_skill import SAPDataQuerySkill

# 1. 创建Skill实例
skill = SAPDataQuerySkill()

# 2. 用户认证
auth_result = skill.authenticate()
if auth_result["success"]:
    print("认证成功！")
else:
    print(f"认证失败: {auth_result['error']}")

# 3. 查询表数据
result = skill.query_table(
    table_name="MARA",
    fields=["MATNR", "MAKTX", "MEINS"],
    page_size=100
)

# 4. 处理结果
if result["success"]:
    print(f"查询到 {result['statistics']['query_rows']} 行数据")
    for row in result["data"]:
        print(f"物料: {row['MATNR']} - {row['MAKTX']}")
else:
    print(f"查询失败: {result['error']}")
```

## 功能示例

### 示例1：物料查询

```python
# 查询原材料物料
result = skill.query_table(
    table_name="MARA",
    fields=["MATNR", "MAKTX", "MATKL", "ERSDA"],
    filters=[
        {
            "FieldName": "MATKL",
            "Calculation": "Equal",
            "Lower": "ROH"
        },
        {
            "Logic": "And",
            "FieldName": "ERSDA",
            "Calculation": "GreatEqual",
            "Lower": "20240101"
        }
    ],
    orders=[
        {
            "FieldName": "MATNR",
            "Direction": "Ascend"
        }
    ]
)
```

### 示例2：BAPI调用

```python
# 调用物料BAPI
bapi_result = skill.query_bapi(
    rfc_name="BAPI_MATERIAL_GET_DETAIL",
    params={
        "MATERIAL": skill.format_material_code("123456")
    }
)
```

### 示例3：智能查询

```python
# 根据意图自动查询
result = skill.intelligent_query(
    table_name="AUFK",
    query_intent="查询2024年1月的生产订单，按订单号降序排列，显示前50条",
    page_size=50
)
```

### 示例4：导出结果

```python
# 导出为Excel
export_result = skill.export_results(
    result=result,
    format="excel",
    file_path="生产订单查询结果.xlsx"
)

if export_result["success"]:
    print(f"导出成功: {export_result['file_path']}")
```

## 目录结构

```
sap_data_query_skill/
├── __init__.py              # Skill主模块
├── SKILL.md                 # 详细功能说明
├── README.md                # 快速开始指南
├── requirements.txt         # 依赖包列表
├── install.py              # 安装脚本
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── auth.py            # 认证模块
│   ├── bapi_client.py     # BAPI客户端
│   ├── table_client.py    # 表查询客户端
│   └── query_builder.py   # 查询构建器
├── config/                 # 配置模块
│   ├── __init__.py
│   ├── settings.py        # 配置管理
│   ├── bapi_mapping.py    # BAPI映射
│   └── table_mapping.py   # 表映射
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── formatter.py       # 数据格式化
│   ├── validator.py       # 参数验证
│   └── exporter.py        # 结果导出
├── templates/              # 查询模板
│   ├── __init__.py
│   ├── material.py        # 物料查询模板
│   ├── production.py      # 生产查询模板
│   └── sales.py           # 销售查询模板
├── scripts/                # 自动化脚本
│   ├── setup.py           # 环境设置
│   ├── test_connection.py # 连接测试
│   └── benchmark.py       # 性能测试
├── assets/                 # 资源文件
│   └── query_templates.json # 查询模板
├── references/             # 参考文档
│   ├── api_spec.md        # API规范
│   └── format_standards.md # 格式标准
├── examples/               # 使用示例
│   ├── quickstart.py      # 快速开始
│   ├── material_query.py  # 物料查询示例
│   └── production_query.py # 生产查询示例
├── tests/                  # 测试文件
│   ├── test_auth.py       # 认证测试
│   ├── test_bapi.py       # BAPI测试
│   └── test_table.py      # 表查询测试
└── logs/                   # 日志目录
```

## 配置说明

### 环境变量配置 (.env)

```bash
# API端点配置
SAP_AUTH_ENDPOINT=https://info02.mingfaigroup.com/api/account/agent/getticket
SAP_BAPI_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke
SAP_TABLE_COLUMNS_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns
SAP_TABLE_DATA_ENDPOINT=https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata

# 应用信息
SAP_APP_NAME=mf.portal.agent
SAP_APP_VERSION=1.0

# 性能配置
SAP_TIMEOUT=60
SAP_MAX_PAGE_SIZE=10000
SAP_DEFAULT_PAGE_SIZE=1000
SAP_MAX_PAGES=100

# 日志配置
SAP_LOG_LEVEL=INFO
SAP_LOG_FILE=logs/sap_query.log
```

### 配置文件 (config/settings.json)

```json
{
    "api_endpoints": {
        "auth": "https://info02.mingfaigroup.com/api/account/agent/getticket",
        "bapi": "https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke",
        "table_columns": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns",
        "table_data": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata"
    },
    "app_info": {
        "app_name": "mf.portal.agent",
        "app_version": "1.0"
    },
    "performance": {
        "timeout": 60,
        "max_page_size": 10000,
        "default_page_size": 1000,
        "max_pages": 100
    }
}
```

## 常见问题

### Q1: 认证失败怎么办？
A: 检查以下内容：
1. 网络连接是否正常
2. 身份证后六位是否正确
3. 工号是否有权限

### Q2: 查询速度慢怎么办？
A: 优化建议：
1. 减少返回字段数量
2. 添加合适的过滤条件
3. 使用分页查询

### Q3: 数据格式错误怎么办？
A: 检查参数格式：
1. 物料条码是否已格式化（18位）
2. 生产订单号是否已格式化（12位）
3. 日期格式是否为YYYYMMDD

### Q4: 如何导出大量数据？
A: 使用分页导出：
```python
all_data = []
current_page = 0

while True:
    result = skill.query_table(
        table_name="MARA",
        current_page=current_page,
        page_size=1000
    )
    
    if not result["success"] or not result["data"]:
        break
    
    all_data.extend(result["data"])
    current_page += 1
    
    if current_page >= 100:  # 限制最大页数
        break
```

## 技术支持

- 问题反馈：it-support@minghuigroup.com
- 文档更新：每月第一个工作日
- 版本发布：季度更新

## 许可证

本Skill仅供明辉集团内部使用，未经授权不得外传。

---

**开始使用：**
```bash
python examples/quickstart.py
```