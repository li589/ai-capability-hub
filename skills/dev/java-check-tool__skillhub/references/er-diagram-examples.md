# ER 图示例集

本文档提供各种场景下的 ER 图示例，帮助快速生成标准化的数据库设计图。

## 1. 简化 ER 图示例

### 1.1 线索管理系统

```mermaid
erDiagram
    lead_source ||--o{ lead_main : "1:N 一个来源对应多条线索"
    lead_main ||--o{ lead_follow_record : "1:N 一条线索有多条跟进记录"
    lead_main ||--o{ lead_modify_log : "1:N 一条线索有多条修改记录"
    lead_main ||--|| lead_customer : "1:1 一条线索转化为一个客户"
    lead_main ||--o{ lead_todo : "1:N 一条线索有多个待办"
    lead_todo ||--|| lead_follow_record : "1:1 待办完成生成跟进记录"
    lead_assign_rule ||--o{ lead_assign_rule_user : "1:N 一个规则配置多个员工"
    lead_assign_rule ||--o{ lead_assign_log : "1:N 一个规则产生多条分配日志"
    lead_main ||--o{ lead_owner_change_log : "1:N 一条线索有多条归属变更记录"
```

### 1.2 订单管理系统

```mermaid
erDiagram
    user ||--o{ order : "1:N 一个用户多个订单"
    order ||--|{ order_item : "1:N 一个订单多个明细"
    product ||--o{ order_item : "1:N 一个产品多个订单明细"
    order ||--|| payment : "1:1 一个订单一个支付记录"
    order ||--o{ shipment : "1:N 一个订单多个发货记录"
```

## 2. 详细 ER 图示例

### 2.1 品牌客户关系管理

```mermaid
erDiagram
    lead_brand {
        bigint id PK "雪花算法"
        varchar brand_name "品牌名称(区分大小写)"
        varchar brand_country "品牌国家/地区编码"
        varchar brand_logo "品牌Logo文件URL"
        varchar business_format "品牌业态(字典:crm_business_format)"
        varchar brand_desc "品牌描述"
        varchar brand_status "品牌状态:NORMAL/REVIEWING/CHANGE_REVIEWING/REJECTED"
        bigint pending_customer_id "当前待生效变更对应客户ID"
        varchar pending_process_instance_id "审批流程实例ID"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    lead_brand_customer_rel {
        bigint id PK "雪花算法"
        bigint brand_id FK "品牌ID(lead_brand.id)"
        bigint customer_id FK "客户ID(lead_customer.id)"
        varchar link_status "关系状态:EFFECTIVE-生效,INVALID-失效"
        varchar source_type "关系来源:CUSTOMER_APPROVE/CUSTOMER_CHANGE_APPROVE/MANUAL"
        datetime effective_time "生效时间"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    lead_customer {
        bigint id PK "雪花算法"
        varchar customer_no UK "客户编号"
        varchar customer_name "客户名称"
        varchar customer_type "客户类型"
        varchar customer_grade "客户等级"
        bigint customer_source_id FK "客户来源ID"
        varchar customer_status "客户状态"
        varchar brand_name "品牌名称(快照)"
        varchar brand_country "品牌国家/地区(快照)"
        varchar business_format "品牌业态(快照)"
        bigint brand_id FK "主关联品牌ID"
        bigint owner_id FK "归属人ID"
        bigint owner_dept_id "归属人部门ID"
        bigint tenant_id "租户编号"
        tinyint deleted "是否删除:0-否,1-是"
    }

    lead_brand ||--o{ lead_brand_customer_rel : "1:N 一品牌关联多客户"
    lead_customer ||--o{ lead_brand_customer_rel : "1:N 一客户关联多品牌"
    lead_customer }o--o| lead_brand : "N:1 主关联品牌(brand_id)"
```

### 2.2 用户权限管理

```mermaid
erDiagram
    sys_user {
        bigint id PK "雪花算法"
        varchar username UK "用户名"
        varchar password "密码(加密)"
        varchar nickname "昵称"
        varchar email "邮箱"
        varchar mobile "手机号"
        tinyint sex "性别:0-未知,1-男,2-女"
        varchar avatar "头像URL"
        tinyint status "状态:0-停用,1-启用"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    sys_role {
        bigint id PK "雪花算法"
        varchar role_name "角色名称"
        varchar role_code UK "角色编码"
        tinyint role_sort "显示顺序"
        tinyint status "状态:0-停用,1-启用"
        varchar remark "备注"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    sys_user_role {
        bigint id PK "雪花算法"
        bigint user_id FK "用户ID(sys_user.id)"
        bigint role_id FK "角色ID(sys_role.id)"
        varchar creator "创建者"
        datetime create_time "创建时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    sys_menu {
        bigint id PK "雪花算法"
        varchar menu_name "菜单名称"
        bigint parent_id "父菜单ID"
        tinyint menu_type "菜单类型:1-目录,2-菜单,3-按钮"
        varchar permission "权限标识"
        varchar path "路由地址"
        varchar component "组件路径"
        tinyint visible "是否显示:0-隐藏,1-显示"
        tinyint status "状态:0-停用,1-启用"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
    }

    sys_role_menu {
        bigint id PK "雪花算法"
        bigint role_id FK "角色ID(sys_role.id)"
        bigint menu_id FK "菜单ID(sys_menu.id)"
        varchar creator "创建者"
        datetime create_time "创建时间"
        tinyint deleted "是否删除:0-否,1-是"
    }

    sys_user ||--o{ sys_user_role : "1:N 一个用户多个角色"
    sys_role ||--o{ sys_user_role : "1:N 一个角色多个用户"
    sys_role ||--o{ sys_role_menu : "1:N 一个角色多个菜单"
    sys_menu ||--o{ sys_role_menu : "1:N 一个菜单多个角色"
```

### 2.3 商品订单管理

```mermaid
erDiagram
    product {
        bigint id PK "雪花算法"
        varchar product_code UK "商品编码"
        varchar product_name "商品名称"
        bigint category_id FK "分类ID(product_category.id)"
        decimal price "价格"
        int stock "库存数量"
        varchar unit "单位"
        varchar description "商品描述"
        tinyint status "状态:0-下架,1-上架"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    product_category {
        bigint id PK "雪花算法"
        varchar category_name "分类名称"
        bigint parent_id "父分类ID"
        int sort "排序"
        tinyint status "状态:0-停用,1-启用"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    order_main {
        bigint id PK "雪花算法"
        varchar order_no UK "订单编号"
        bigint user_id FK "用户ID"
        decimal total_amount "订单总金额"
        decimal pay_amount "实付金额"
        varchar order_status "订单状态:PENDING/PAID/SHIPPED/COMPLETED/CANCELLED"
        varchar pay_status "支付状态:UNPAID/PAID/REFUNDED"
        datetime pay_time "支付时间"
        varchar remark "订单备注"
        varchar creator "创建者"
        datetime create_time "创建时间"
        varchar updater "更新者"
        datetime update_time "更新时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    order_item {
        bigint id PK "雪花算法"
        bigint order_id FK "订单ID(order_main.id)"
        bigint product_id FK "商品ID(product.id)"
        varchar product_name "商品名称(快照)"
        decimal product_price "商品单价(快照)"
        int quantity "购买数量"
        decimal subtotal "小计金额"
        varchar creator "创建者"
        datetime create_time "创建时间"
        tinyint deleted "是否删除:0-否,1-是"
        bigint tenant_id "租户编号"
    }

    product_category ||--o{ product : "1:N 一个分类多个商品"
    order_main ||--|{ order_item : "1:N 一个订单多个明细"
    product ||--o{ order_item : "1:N 一个商品多个订单明细"
```

## 3. 使用指南

### 3.1 选择合适的格式

**重要：技术文档默认使用详细格式**

| 场景 | 推荐格式 | 原因 |
|------|----------|------|
| 技术方案文档（默认） | 详细 ER 图 | 完整展示表结构，便于开发实现 |
| 详细设计文档 | 详细 ER 图 | 完整展示表结构，便于开发实现 |
| 代码评审文档 | 详细 ER 图 | 便于评审字段设计和约束 |
| 数据库迁移文档 | 详细 ER 图 | 需要完整的字段信息 |
| 技术方案初稿 | 简化 ER 图 | 快速展示表关系，便于讨论架构 |
| 系统架构文档 | 简化 ER 图 | 关注表关系，不需要字段细节 |

### 3.2 详细 ER 图绘制规范

1. **字段顺序**：
   - 主键字段（id）放在最前面
   - 唯一键字段紧随其后
   - 业务字段按重要性排列
   - 标准字段放在最后（creator, create_time, updater, update_time, deleted, tenant_id）

2. **字段类型**：
   - 使用 MySQL 数据类型：bigint, varchar, datetime, tinyint, text, decimal, int
   - 保持与建表 SQL 一致

3. **约束标记**：
   - 主键必须标记 `PK`
   - 外键必须标记 `FK` 并在注释中说明关联表
   - 唯一键标记 `UK`

4. **字段注释规范**：
   - 使用双引号包裹
   - 枚举值格式：`"字段说明:值1/值2/值3"` 或 `"字段说明:值1-说明1,值2-说明2"`
   - 外键格式：`"关联表说明(表名.字段名)"`
   - 字典字段格式：`"字段说明(字典:字典编码)"`
   - 快照字段格式：`"字段说明(快照)"`

5. **关系定义**：
   - 在所有表定义之后统一定义关系
   - 关系描述格式：`"关系类型 关系说明"`
   - 示例：`"1:N 一品牌关联多客户"`

### 3.3 常见关系类型

| 关系符号 | 含义 | 示例 |
|----------|------|------|
| `\|\|--\|\|` | 一对一 (1:1) | 订单 → 支付记录 |
| `\|\|--o{` | 一对多 (1:N) | 用户 → 订单 |
| `}o--o{` | 多对多 (N:M) | 学生 ↔ 课程 |
| `}o--o\|` | 多对一 (N:1) | 订单 → 用户 |

### 3.4 标准字段说明

所有表必须包含以下标准字段（在详细 ER 图中必须展示）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | bigint | 主键ID（雪花算法） |
| creator | varchar | 创建者 |
| create_time | datetime | 创建时间 |
| updater | varchar | 更新者 |
| update_time | datetime | 更新时间 |
| deleted | tinyint | 逻辑删除标记:0-否,1-是 |
| tenant_id | bigint | 租户编号 |

