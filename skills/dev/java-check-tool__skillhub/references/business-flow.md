# 业务流程设计规范

本文档定义业务流程的设计规范、流程图绘制方法和描述格式。

## 流程图选择原则

根据技术方案类型选择合适的流程图格式：

- **后端业务流程**：使用时序图（sequenceDiagram）展示系统组件交互和数据流转
- **前端交互流程**：使用 flowchart 展示用户操作流程和页面跳转逻辑

## 1. 业务流程章节结构

### 1.1 后端业务流程（推荐使用时序图）

```markdown
## 5. 核心业务流程

### 5.1 [流程1名称]

#### 流程图

​```mermaid
sequenceDiagram
    participant A as 参与者A
    participant B as 参与者B
    participant C as 参与者C

    A->>B: 操作1
    B->>C: 操作2
    C-->>B: 返回结果
    B-->>A: 返回结果
​```

#### 流程说明

1. **步骤1**: 说明
2. **步骤2**: 说明
3. **步骤3**: 说明

#### 异常处理

- **异常1**: 处理方式
- **异常2**: 处理方式

### 5.2 [流程2名称]
...
```

### 1.2 前端交互流程（推荐使用 flowchart）

```markdown
## 5. 核心业务流程

### 5.1 [流程1名称]

#### 流程图

​```mermaid
flowchart TD
    A([开始]) --> B[用户操作]
    B --> C{条件判断}
    C -->|是| D[页面跳转]
    C -->|否| E[显示提示]
    D --> F([结束])
    E --> F
​```

#### 流程说明

1. **步骤1**: 说明
2. **步骤2**: 说明
3. **步骤3**: 说明

#### 注意事项

- 注意事项1
- 注意事项2

### 5.2 [流程2名称]
...
```

## 2. 时序图（sequenceDiagram）- 主要格式

### 2.1 基本语法

时序图用于展示系统组件之间的交互顺序和消息传递，是描述业务流程的首选方式。

```mermaid
sequenceDiagram
    participant 用户
    participant Controller
    participant Service
    participant Mapper
    participant DB as 数据库

    用户->>Controller: 发起请求
    Controller->>Service: 调用业务逻辑
    Service->>Mapper: 查询数据
    Mapper->>DB: SQL 查询
    DB-->>Mapper: 返回结果
    Mapper-->>Service: 返回 DO
    Service-->>Controller: 返回 VO
    Controller-->>用户: 返回响应
```

### 2.2 参与者定义

使用 `participant` 定义参与者，可以使用别名简化图表：

```mermaid
sequenceDiagram
    participant U as 用户
    participant C as Controller
    participant S as Service
    participant M as Mapper
    participant DB as 数据库
```

### 2.3 消息类型

| 语法 | 说明 | 使用场景 |
|------|------|----------|
| `A->>B` | 实线箭头（同步调用） | 方法调用、API 请求 |
| `A-->>B` | 虚线箭头（返回） | 返回结果、响应 |
| `A->>+B` | 激活参与者 | 开始处理 |
| `A-->>-B` | 停用参与者 | 处理结束 |
| `A-)B` | 异步消息 | 异步通知、事件 |

### 2.4 条件分支

使用 `alt`/`else` 表示条件分支：

```mermaid
sequenceDiagram
    participant Service
    participant Mapper
    participant DB as 数据库

    Service->>Mapper: 查询品牌
    Mapper->>DB: SELECT
    DB-->>Mapper: 返回结果
    alt 品牌不存在
        Mapper-->>Service: null
        Service->>Mapper: 创建品牌
        Mapper->>DB: INSERT
    else 品牌存在
        Mapper-->>Service: 已有品牌
    end
```

### 2.5 循环

使用 `loop` 表示循环：

```mermaid
sequenceDiagram
    participant Service
    participant Mapper

    loop 遍历每个规则
        Service->>Mapper: 查询符合条件的线索
        Mapper-->>Service: 返回线索列表
    end
```

### 2.6 注释

使用 `Note` 添加注释说明：

```mermaid
sequenceDiagram
    participant Service
    participant Mapper

    Service->>Mapper: 查询数据
    Note over Service,Mapper: 这里执行复杂的业务逻辑
    Mapper-->>Service: 返回结果
```

## 3. 业务流程示例

### 3.1 客户审批通过后自动创建/关联品牌

#### 流程图

```mermaid
sequenceDiagram
    participant Event as BpmProcessInstanceStatusEvent
    participant Listener as BpmCustomerBrandStatusListener
    participant SyncService as BrandSyncService
    participant CustomerMapper as LeadCustomerMapper
    participant BrandMapper as LeadBrandMapper
    participant RelMapper as LeadBrandCustomerRelMapper
    participant DB as 数据库

    Event->>Listener: 审批通过事件
    Listener->>SyncService: onCustomerApprovePassed(customerId)
    SyncService->>CustomerMapper: 读取客户品牌信息
    CustomerMapper->>DB: SELECT brand_name, brand_country
    DB-->>CustomerMapper: 返回客户数据
    CustomerMapper-->>SyncService: 返回客户DO
    SyncService->>BrandMapper: 查询品牌(brand_name + brand_country)
    BrandMapper->>DB: SELECT
    DB-->>BrandMapper: 返回查询结果
    alt 品牌不存在
        BrandMapper-->>SyncService: null
        SyncService->>BrandMapper: 创建 lead_brand（状态 NORMAL）
        BrandMapper->>DB: INSERT
        DB-->>BrandMapper: 成功
        BrandMapper-->>SyncService: 新品牌DO
    else 品牌存在且状态 NORMAL
        BrandMapper-->>SyncService: 已有品牌DO
    else 品牌存在但状态异常
        BrandMapper-->>SyncService: 异常品牌DO
        SyncService-->>Listener: 抛出业务异常并记录告警
    end
    SyncService->>RelMapper: 建立品牌-客户关系（EFFECTIVE）
    RelMapper->>DB: INSERT lead_brand_customer_rel
    DB-->>RelMapper: 成功
    SyncService->>CustomerMapper: 回填 lead_customer.brand_id
    CustomerMapper->>DB: UPDATE
    DB-->>CustomerMapper: 成功
    SyncService-->>Listener: 完成
```

#### 流程说明

1. **审批事件触发**: 客户审批通过事件触发 `BrandSyncService.onCustomerApprovePassed`
2. **读取客户信息**: 从 `lead_customer` 表读取客户的品牌名称和国家信息
3. **查询品牌**: 以 `brand_name + brand_country` 查询品牌是否已存在
4. **创建或关联品牌**:
   - 若品牌不存在，则新建品牌，创建者取客户创建者，状态置 `NORMAL`
   - 若品牌存在且状态正常，则直接关联
   - 若品牌存在但状态异常，则拒绝关联并记录告警
5. **建立关系**: 在 `lead_brand_customer_rel` 表中建立品牌-客户关系，状态为 `EFFECTIVE`
6. **回填品牌ID**: 更新客户表的 `brand_id` 字段，保留原品牌快照字段

#### 异常处理

- **品牌状态非 NORMAL**: 拒绝自动关联并记录审计日志，避免脏数据
- **唯一键冲突**: 重试一次查询后转为关联路径（防并发双写）
- **任一数据库操作失败**: 事务回滚，确保数据一致性

### 3.2 客户品牌变更审批流程

#### 流程图

```mermaid
sequenceDiagram
    participant 用户
    participant Controller
    participant CustomerService as LeadPersonalService
    participant BrandService as LeadBrandService
    participant BpmService as 审批服务
    participant SyncService as BrandSyncService
    participant DB as 数据库

    用户->>Controller: 提交品牌变更
    Controller->>CustomerService: 处理客户变更请求
    CustomerService->>BrandService: validateBrandEditable(brandId)
    BrandService->>DB: 查询品牌状态
    DB-->>BrandService: 返回品牌DO
    alt 状态为 REVIEWING / CHANGE_REVIEWING
        BrandService-->>CustomerService: 抛出业务异常
        CustomerService-->>Controller: 拒绝提交
        Controller-->>用户: 返回错误提示
    else 允许提交
        BrandService-->>CustomerService: 校验通过
        CustomerService->>DB: 品牌状态置 CHANGE_REVIEWING
        CustomerService->>BpmService: 发起客户变更审批流程
        BpmService-->>CustomerService: 审批流程已创建
        CustomerService-->>Controller: 提交成功
        Controller-->>用户: 返回成功
        Note over BpmService,SyncService: 审批结果异步回调
        alt 审批通过
            BpmService->>SyncService: onCustomerApprovePassed(customerId)
            SyncService->>DB: 创建/关联品牌，切换关系，置状态 NORMAL
        else 审批拒绝
            BpmService->>SyncService: onCustomerApproveRejected(customerId)
            SyncService->>DB: 品牌状态置 REJECTED，保留原有效关联
        end
    end
```

#### 流程说明

1. **提交变更**: 用户在客户编辑页面提交品牌字段变更
2. **品牌状态校验**: 先校验品牌当前是否可编辑（状态不能为 `REVIEWING` 或 `CHANGE_REVIEWING`）
3. **状态标记**: 进入审批后，目标品牌状态标记为 `CHANGE_REVIEWING`，期间前端禁改品牌字段
4. **发起审批**: 调用审批服务创建客户变更审批流程
5. **审批通过**: 按新品牌信息完成品牌创建/关联、关系切换、客户 `brand_id` 回填，品牌状态置 `NORMAL`
6. **审批拒绝**: 品牌状态置 `REJECTED`，保留原有效关联不变

#### 异常处理

- **变更目标与现有品牌一致**: 直接短路，无需审批
- **审批通过但目标品牌状态异常**: 记录错误并终止生效
- **关系切换失败**: 事务回滚，审批结果写告警队列人工处理

### 3.3 品牌列表查询流程

#### 流程图

```mermaid
sequenceDiagram
    participant 用户
    participant Controller as LeadBrandController
    participant Service as LeadBrandService
    participant BrandMapper as LeadBrandMapper
    participant DB as 数据库

    用户->>Controller: 请求品牌分页查询
    Controller-->>Controller: 参数校验
    Controller->>Service: getBrandPage(reqVO)
    Service->>BrandMapper: selectPage(reqVO)
    BrandMapper->>DB: SQL 查询（status=NORMAL，分页+排序）
    DB-->>BrandMapper: 返回品牌列表
    BrandMapper-->>Service: 返回 DO 列表
    Service-->>Service: DO 转 VO，填充多语言字段
    Service-->>Controller: 返回 PageResult<LeadBrandRespVO>
    Controller-->>用户: 返回分页结果
```

#### 流程说明

1. **接收请求**: 用户在品牌管理页面发起分页查询请求
2. **参数校验**: Controller 层校验请求参数（品牌名、业态、国家、创建人等筛选条件）
3. **查询数据**: Service 调用 Mapper 执行分页查询，仅查询状态为 `NORMAL` 的品牌
4. **数据转换**: 将 DO 转换为 VO，填充多语言字段（如品牌描述）
5. **返回结果**: 返回分页结果，包含品牌列表和分页信息

#### 异常处理

- **查询无数据**: 返回空列表，不抛错
- **品牌不存在或已删除**: 提示"品牌不存在或已失效"

### 3.4 查看品牌关联客户流程

#### 流程图

```mermaid
sequenceDiagram
    participant 用户
    participant Controller as LeadBrandController
    participant Service as LeadBrandService
    participant RelMapper as LeadBrandCustomerRelMapper
    participant DB as 数据库

    用户->>Controller: 点击查看关联客户（brandId）
    Controller->>Service: getBrandCustomerPage(reqVO)
    Service->>RelMapper: 按 brand_id 查询关系表 + 客户表
    RelMapper->>DB: JOIN 查询（link_status=EFFECTIVE）
    DB-->>RelMapper: 返回客户列表
    RelMapper-->>Service: 返回 DO 列表
    Service-->>Service: DO 转 VO
    Service-->>Controller: 返回 PageResult<LeadBrandCustomerRespVO>
    Controller-->>用户: 返回客户弹窗分页数据
```

#### 流程说明

1. **触发查看**: 用户在品牌列表点击"查看关联客户"按钮
2. **查询关系**: Service 调用 RelMapper 查询品牌-客户关系表，JOIN 客户表获取客户信息
3. **过滤条件**: 仅查询关系状态为 `EFFECTIVE` 的有效关联
4. **数据转换**: 将 DO 转换为 VO，包含客户名称、归属人、归属组织、最后更新时间等
5. **返回结果**: 返回客户列表分页数据，支持客户名模糊检索

#### 异常处理

- **品牌不存在**: 提示"品牌不存在或已失效"
- **无关联客户**: 返回空列表

## 4. Flowchart 流程图（前端流程推荐格式）

Flowchart 适用于前端交互流程、用户操作流程、页面跳转逻辑等场景。

### 4.1 基本语法

```mermaid
flowchart TD
    A([开始]) --> B[步骤1]
    B --> C{判断}
    C -->|是| D[步骤2]
    C -->|否| E[步骤3]
    D --> F([结束])
    E --> F
```

### 4.2 节点类型

| 语法 | 说明 | 示例 |
|------|------|------|
| `[文本]` | 矩形（普通步骤） | `A[开始]` |
| `{文本}` | 菱形（判断） | `B{是否通过}` |
| `([文本])` | 圆角矩形（开始/结束） | `([开始])` |
| `((文本))` | 圆形（连接点） | `((A))` |
| `[(文本)]` | 圆柱形（数据库） | `[(保存数据)]` |

### 4.3 连接线类型

| 语法 | 说明 |
|------|------|
| `-->` | 实线箭头 |
| `-.->` | 虚线箭头 |
| `==>` | 粗箭头 |
| `--文本-->` | 带文字的箭头 |

### 4.4 方向控制

| 语法 | 说明 |
|------|------|
| `TD` | 从上到下（默认） |
| `LR` | 从左到右 |
| `BT` | 从下到上 |
| `RL` | 从右到左 |

### 4.5 前端流程示例

#### 4.5.1 用户登录流程

```mermaid
flowchart TD
    A([用户打开登录页]) --> B[输入用户名和密码]
    B --> C[点击登录按钮]
    C --> D{前端表单校验}
    D -->|校验失败| E[显示错误提示]
    E --> B
    D -->|校验通过| F[显示加载状态]
    F --> G[调用登录 API]
    G --> H{登录结果}
    H -->|成功| I[保存 Token]
    I --> J[跳转到首页]
    J --> K([结束])
    H -->|失败| L[显示错误消息]
    L --> M[隐藏加载状态]
    M --> B
```

#### 4.5.2 表单提交流程

```mermaid
flowchart TD
    A([用户填写表单]) --> B[点击提交按钮]
    B --> C{前端校验}
    C -->|失败| D[高亮错误字段]
    D --> E[显示错误提示]
    E --> A
    C -->|通过| F[禁用提交按钮]
    F --> G[显示加载动画]
    G --> H[调用后端 API]
    H --> I{提交结果}
    I -->|成功| J[显示成功提示]
    J --> K[关闭弹窗/跳转页面]
    K --> L([结束])
    I -->|失败| M[显示错误消息]
    M --> N[启用提交按钮]
    N --> O[隐藏加载动画]
    O --> A
```

#### 4.5.3 页面加载流程

```mermaid
flowchart TD
    A([进入页面]) --> B[显示骨架屏]
    B --> C[调用数据接口]
    C --> D{请求结果}
    D -->|成功| E[渲染页面内容]
    E --> F[隐藏骨架屏]
    F --> G([页面就绪])
    D -->|失败| H[显示错误页面]
    H --> I{用户操作}
    I -->|点击重试| C
    I -->|返回上一页| J([结束])
```

### 4.6 后端简单流程示例（可选）

对于不涉及多系统交互的简单后端流程，也可以使用 flowchart：

```mermaid
flowchart TD
    A([开始]) --> B[接收待办创建请求]
    B --> C{校验参数}
    C -->|失败| D[返回错误]
    C -->|成功| E[生成待办ID]
    E --> F[设置待办属性]
    F --> G[计算提醒时间]
    G --> H[(保存到数据库)]
    H --> I[发送创建通知]
    I --> J([结束])
    D --> J
```

## 5. 状态机图（可选）

对于有明确状态流转的业务，可以使用状态机图：

```mermaid
stateDiagram-v2
    [*] --> 未分配
    未分配 --> 跟进中: 分配给员工
    跟进中 --> 已转化: 转化为客户
    跟进中 --> 已失效: 标记失效
    跟进中 --> 未分配: 回收到公海池
    已转化 --> [*]
    已失效 --> [*]
```

## 6. 流程描述规范

### 6.1 步骤描述格式

使用有序列表，每个步骤包含：
- **步骤名称**: 简短描述
- 详细说明: 具体操作内容

```markdown
1. **接收请求**: 接收前端传入的待办创建请求，包含线索ID、待办类型、计划时间等
2. **参数校验**: 校验必填字段、时间格式、线索是否存在等
```

### 6.2 异常处理格式

使用无序列表，每个异常包含：
- **异常名称**: 处理方式

```markdown
- **参数校验失败**: 返回 400 错误，提示具体校验失败原因
- **线索不存在**: 返回 404 错误，提示线索不存在
```

## 7. 流程文档模板

```markdown
### 5.1 [流程名称]

#### 流程图

​```mermaid
sequenceDiagram
    participant A as 参与者A
    participant B as 参与者B
    participant C as 参与者C

    A->>B: 操作1
    B->>C: 操作2
    C-->>B: 返回结果
    B-->>A: 返回结果
​```

#### 流程说明

1. **步骤1**: 详细说明
2. **步骤2**: 详细说明
3. **步骤3**: 详细说明

#### 异常处理

- **异常1**: 处理方式
- **异常2**: 处理方式

#### 注意事项

- 注意事项1
- 注意事项2
```

## 8. 流程设计原则

1. **清晰性**: 流程图应清晰易懂，避免过于复杂
2. **完整性**: 包含所有关键步骤和分支
3. **异常处理**: 明确说明各种异常情况的处理方式
4. **可追溯性**: 关键操作需要记录日志
5. **事务性**: 涉及多表操作时注意事务控制
6. **通知机制**: 重要操作需要通知相关人员

## 9. 图表选择指南

| 场景 | 推荐图表 | 说明 |
|------|----------|------|
| **后端：系统组件交互** | 时序图（sequenceDiagram） | 清晰展示 Controller/Service/Mapper/DB 调用顺序和数据流转 |
| **后端：审批流程** | 时序图（sequenceDiagram） | 展示审批各阶段的系统交互 |
| **后端：数据查询流程** | 时序图（sequenceDiagram） | 展示查询链路和数据转换 |
| **前端：用户操作流程** | Flowchart | 展示用户交互步骤和页面跳转 |
| **前端：页面渲染流程** | Flowchart | 展示组件加载和渲染逻辑 |
| **前端：表单提交流程** | Flowchart | 展示表单校验和提交步骤 |
| **通用：状态流转** | 状态机图（stateDiagram） | 展示状态变化规则 |
| **通用：定时任务** | Flowchart | 展示任务执行逻辑 |
| **通用：简单业务流程** | Flowchart | 快速展示流程步骤 |
