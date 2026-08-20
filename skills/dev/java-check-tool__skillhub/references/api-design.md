# 接口设计规范

本文档定义 Controller、Service、Mapper 三层接口的设计规范和示例。

## 1. 三层架构说明

```
Controller 层 (控制器层)
    ↓ 调用
Service 层 (业务逻辑层)
    ↓ 调用
Mapper 层 (数据访问层)
```

- **Controller**: 处理 HTTP 请求，参数校验，权限控制
- **Service**: 实现业务逻辑，事务控制
- **Mapper**: 数据库操作，SQL 执行

### 1.1 当前模块范围约束（强制）

- 接口设计只展开**当前业务模块**的 Controller/Service/Mapper
- 禁止输出“跨模块依赖协作”“外部依赖对接”“协作边界”等非当前模块章节、表格或示例
- 不在当前方案中定义其他模块的数据库表、Mapper SQL、内部业务流程

## 2. Controller 接口设计

### 2.1 基本规范

```java
@RestController
@RequestMapping("/api/module")
@Tag(name = "模块名称")
public class ModuleController {

    @GetMapping("/page")
    @Operation(summary = "分页查询")
    @PreAuthorize("@ss.hasPermission('module:query')")
    public CommonResult<PageResult<ModuleRespVO>> getPage(
        @Valid ModulePageReqVO pageReqVO) {
        // 实现
    }
}
```

### 2.2 接口命名规范

| 操作类型 | HTTP 方法 | 路径 | 方法名 |
|----------|-----------|------|--------|
| 分页查询 | GET | /page | getPage |
| 列表查询 | GET | /list | getList |
| 详情查询 | GET | /get | get{Entity} |
| 新增 | POST | /create | create{Entity} |
| 修改 | PUT | /update | update{Entity} |
| 删除 | DELETE | /delete | delete{Entity} |

### 2.3 完整示例

#### 分页查询接口

```java
@GetMapping("/page")
@Operation(summary = "获取公海池线索分页")
@PreAuthorize("@ss.hasPermission('crm:lead-pool:query')")
public CommonResult<PageResult<LeadPoolRespVO>> getLeadPoolPage(
    @Valid LeadPoolPageReqVO pageReqVO) {

    PageResult<LeadPoolDO> pageResult = leadPoolService.getLeadPoolPage(pageReqVO);
    return success(LeadPoolConvert.INSTANCE.convertPage(pageResult));
}
```

**权限码**: `crm:lead-pool:query`

**请求参数** (LeadPoolPageReqVO):
- `brandName`: 品牌名（模糊搜索）
- `brandCountry`: 品牌国家/地区（多选）
- `contactName`: 联系人姓名（模糊搜索）
- `mobile`: 手机号（模糊搜索）
- `leadSourceIds`: 线索来源ID列表（多选）
- `leadStatus`: 线索状态（多选，默认UNASSIGNED）
- `referrerId`: 介绍人ID（多选）
- `createTime`: 创建时间范围
- `pageNo`: 页码
- `pageSize`: 每页大小

**响应数据**: 分页结果，包含线索列表

#### 详情查询接口

```java
@GetMapping("/get")
@Operation(summary = "获取公海池线索详情")
@PreAuthorize("@ss.hasPermission('crm:lead-pool:query')")
public CommonResult<LeadPoolRespVO> getLeadPool(
    @RequestParam("id") Long id) {

    LeadPoolDO leadPool = leadPoolService.getLeadPool(id);
    return success(LeadPoolConvert.INSTANCE.convert(leadPool));
}
```

**权限码**: `crm:lead-pool:query`

**请求参数**:
- `id`: 线索ID

**响应数据**: 线索详情对象

#### 保存接口（新增/修改）

```java
@PostMapping("/save")
@Operation(summary = "保存线索")
@PreAuthorize("@ss.hasPermission('crm:lead-pool:create')")
public CommonResult<Long> saveLeadPool(
    @Valid @RequestBody LeadPoolSaveReqVO saveReqVO) {

    Long id = leadPoolService.saveLeadPool(saveReqVO);
    return success(id);
}
```

**权限码**: `crm:lead-pool:create`

**请求参数** (LeadPoolSaveReqVO):
- `id`: 线索ID（修改时必填，新增时为空）
- `brandName`: 品牌名称
- `contactName`: 联系人姓名
- `mobile`: 手机号
- `leadSourceId`: 线索来源ID
- ...其他业务字段

**响应数据**: 保存后的线索ID

#### 删除接口

```java
@DeleteMapping("/delete")
@Operation(summary = "删除线索")
@PreAuthorize("@ss.hasPermission('crm:lead-pool:delete')")
public CommonResult<Boolean> deleteLeadPool(
    @RequestParam("id") Long id) {

    leadPoolService.deleteLeadPool(id);
    return success(true);
}
```

**权限码**: `crm:lead-pool:delete`

**请求参数**:
- `id`: 线索ID

**响应数据**: 删除成功返回 true

### 2.4 接口文档格式

每个接口需要说明以下内容：

```markdown
#### [接口名称]

​```java
[接口代码]
​```

**权限码**: `module:action`

**请求参数**:
- `param1`: 参数说明
- `param2`: 参数说明

**响应数据**: 响应说明
```

## 3. Service 接口设计

### 3.1 基本规范

```java
public interface ModuleService {

    // 分页查询
    PageResult<ModuleDO> getPage(ModulePageReqVO pageReqVO);

    // 详情查询
    ModuleDO get(Long id);

    // 保存（新增/修改）
    Long save(ModuleSaveReqVO saveReqVO);

    // 删除
    void delete(Long id);
}
```

### 3.2 注释要求（强制）

- Service 接口中，**每个方法签名前必须有 `//` 单行注释**
- 注释需描述“做什么”，不要只写“方法说明”
- 不允许输出无注释的方法签名

### 3.3 方法命名规范

| 操作类型 | 方法名 | 返回值 |
|----------|--------|--------|
| 分页查询 | getPage | PageResult<DO> |
| 列表查询 | getList | List<DO> |
| 详情查询 | get | DO |
| 统计查询 | count | Long/Integer |
| 保存 | save | Long (返回ID) |
| 删除 | delete | void |
| 批量操作 | batch{Action} | void/List |

### 3.4 完整示例

```java
public interface LeadPoolService {

    // 分页查询公海池线索
    PageResult<LeadPoolDO> getLeadPoolPage(LeadPoolPageReqVO pageReqVO);

    // 获取公海池统计卡片
    LeadPoolStatisticsRespVO getStatistics();

    // 获取线索详情
    LeadPoolDO getLeadPool(Long id);

    // 保存线索（新增/修改）
    Long saveLeadPool(LeadPoolSaveReqVO saveReqVO);

    // 删除线索
    void deleteLeadPool(Long id);

    // 批量分配线索
    void batchAssignLeads(List<Long> leadIds, Long ownerId);
}
```

## 4. Mapper 接口设计

### 4.1 基本规范

```java
@Mapper
public interface ModuleMapper extends BaseMapperX<ModuleDO> {

    default PageResult<ModuleDO> selectPage(ModulePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModuleDO>()
            .likeIfPresent(ModuleDO::getName, reqVO.getName())
            .eqIfPresent(ModuleDO::getStatus, reqVO.getStatus())
            .betweenIfPresent(ModuleDO::getCreateTime, reqVO.getCreateTime())
            .orderByDesc(ModuleDO::getId));
    }
}
```

### 4.2 注释要求（强制）

- Mapper 接口中，分页查询、统计查询、自定义查询等方法前必须添加 `//` 单行注释
- 对带有业务过滤逻辑的方法（如状态过滤、数据权限过滤、时间区间过滤），注释中应简要体现
- 不允许输出无注释的方法签名

### 4.3 方法命名规范

| 操作类型 | 方法名 | 说明 |
|----------|--------|------|
| 分页查询 | selectPage | 返回分页结果 |
| 列表查询 | selectList | 返回列表 |
| 单条查询 | selectOne | 返回单条记录 |
| 统计查询 | selectCount | 返回数量 |
| 插入 | insert | 插入记录 |
| 更新 | update | 更新记录 |
| 删除 | delete | 删除记录 |

### 4.4 完整示例

```java
@Mapper
public interface LeadPoolMapper extends BaseMapperX<LeadPoolDO> {

    // 分页查询公海池线索
    default PageResult<LeadPoolDO> selectPage(LeadPoolPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<LeadPoolDO>()
            .likeIfPresent(LeadPoolDO::getBrandName, reqVO.getBrandName())
            .inIfPresent(LeadPoolDO::getBrandCountry, reqVO.getBrandCountry())
            .likeIfPresent(LeadPoolDO::getContactName, reqVO.getContactName())
            .likeIfPresent(LeadPoolDO::getMobile, reqVO.getMobile())
            .inIfPresent(LeadPoolDO::getLeadSourceId, reqVO.getLeadSourceIds())
            .inIfPresent(LeadPoolDO::getLeadStatus, reqVO.getLeadStatus())
            .inIfPresent(LeadPoolDO::getReferrerId, reqVO.getReferrerId())
            .betweenIfPresent(LeadPoolDO::getCreateTime, reqVO.getCreateTime())
            .orderByDesc(LeadPoolDO::getId));
    }

    // 统计今日新增线索数
    default Long selectTodayNewCount() {
        LocalDateTime startOfDay = LocalDateTime.now().with(LocalTime.MIN);
        return selectCount(new LambdaQueryWrapperX<LeadPoolDO>()
            .ge(LeadPoolDO::getCreateTime, startOfDay));
    }

    // 统计未分配线索数
    default Long selectUnassignedCount() {
        return selectCount(new LambdaQueryWrapperX<LeadPoolDO>()
            .eq(LeadPoolDO::getLeadStatus, LeadStatusEnum.UNASSIGNED));
    }
}
```

## 5. VO 对象设计

### 5.1 请求对象（ReqVO）

```java
@Data
public class ModulePageReqVO extends PageParam {

    @Schema(description = "名称", example = "张三")
    private String name;

    @Schema(description = "状态", example = "1")
    private Integer status;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;
}
```

### 5.2 响应对象（RespVO）

```java
@Data
public class ModuleRespVO {

    @Schema(description = "ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "张三")
    private String name;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Integer status;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createTime;
}
```

## 6. 权限码规范

权限码格式：`模块:操作`

常用操作：
- `query`: 查询
- `create`: 新增
- `update`: 修改
- `delete`: 删除
- `export`: 导出
- `import`: 导入

示例：
- `crm:lead-pool:query`
- `crm:lead-pool:create`
- `crm:lead-pool:update`
- `crm:lead-pool:delete`

## 7. 多语言字段设计

### 7.1 多语言注解说明

项目使用 `@Translate` 和 `@TranslateDomain` 注解实现业务数据的多语言支持。

#### @TranslateDomain（类级注解）

标记在 VO 类上，声明所属业务模块：

```java
@TranslateDomain(module = "crm-lead")
public class LeadPoolRespVO {
    // ...
}
```

**参数说明**:
- `module`: 模块编码（如：product、system、crm-lead）
- `recursive`: 是否递归处理嵌套对象（默认 false）

#### @Translate（字段级/方法级注解）

**字段级使用**：标记需要多语言处理的业务字段

```java
@Translate(domain = "leadPool", name = "brandName", id = "id")
private String brandName;
@Schema(description = "品牌名称多语言")
private Map<String, String> brandNameML;
```

**方法级使用**：标记在 Controller 方法上，启用多语言处理

```java
@GetMapping("/page")
@Translate  // 启用多语言处理
public CommonResult<PageResult<LeadPoolRespVO>> getPage(@Valid LeadPoolPageReqVO pageReqVO) {
    // ...
}
```

**参数说明**:
- `domain`: 业务域（如：product、leadPool、leadSource）
- `name`: 字段名（如：productName、brandName）
- `id`: ID 字段名（默认 "id"）
- `idMethod`: ID 获取方法名（适用于组合 ID）
- `module`: 模块编码（优先级高于 @TranslateDomain）
- `suffix`: 多语言 Map 字段后缀（默认 "ML"）
- `scope`: 作用域（TENANT-租户维度，GLOBAL-全局维度）
- `client`: 客户端类型（AUTO-自动从请求头获取）

### 7.2 多语言字段命名规范

| 原字段名 | 多语言 Map 字段名 | 说明 |
|---------|-----------------|------|
| brandName | brandNameML | 品牌名称多语言 |
| companyName | companyNameML | 公司名称多语言 |
| address | addressML | 地址多语言 |
| remark | remarkML | 备注多语言 |

**命名规则**: `{原字段名} + ML`（ML = MultiLanguage）

### 7.3 多语言字段设计示例

#### 响应对象（RespVO）

```java
@Schema(description = "管理后台 - 品牌信息 Response VO")
@Data
@TranslateDomain(module = "crm-lead")
public class BrandRespVO {

    @Schema(description = "品牌ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "品牌名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "海底捞")
    private String brandName;
    // 注意：brandName 不需要 @Translate，因为需求明确"无需多语言"

    @Schema(description = "品牌描述", example = "知名火锅品牌")
    @Translate(domain = "brand", name = "brandDesc", id = "id")
    private String brandDesc;
    @Schema(description = "品牌描述多语言")
    private Map<String, String> brandDescML;

    @Schema(description = "品牌国家/地区", example = "CN")
    private String brandCountry;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createTime;
}
```

#### 保存对象（SaveReqVO）

```java
@Schema(description = "管理后台 - 品牌保存 Request VO")
@Data
@TranslateDomain(module = "crm-lead")
public class BrandSaveReqVO {

    @Schema(description = "品牌ID", example = "1")
    private Long id;

    @Schema(description = "品牌名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "海底捞")
    @NotBlank(message = "品牌名称不能为空")
    private String brandName;

    @Schema(description = "品牌描述", example = "知名火锅品牌")
    @Translate(domain = "brand", name = "brandDesc", id = "id")
    private String brandDesc;
    @Schema(description = "品牌描述多语言")
    private Map<String, String> brandDescML;

    @Schema(description = "品牌国家/地区", requiredMode = Schema.RequiredMode.REQUIRED, example = "CN")
    @NotBlank(message = "品牌国家/地区不能为空")
    private String brandCountry;
}
```

### 7.4 Controller 多语言处理

在 Controller 方法上添加 `@Translate` 注解启用多语言处理：

```java
@RestController
@RequestMapping("/api/crm/brand")
@Tag(name = "品牌管理")
public class BrandController {

    @GetMapping("/page")
    @Operation(summary = "获取品牌分页")
    @PreAuthorize("@ss.hasPermission('crm:brand:query')")
    @Translate  // 处理响应数据的多语言字段填充
    public CommonResult<PageResult<BrandRespVO>> getBrandPage(
        @Valid BrandPageReqVO pageReqVO) {

        PageResult<BrandDO> pageResult = brandService.getBrandPage(pageReqVO);
        return success(BrandConvert.INSTANCE.convertPage(pageResult));
    }

    @GetMapping("/get")
    @Operation(summary = "获取品牌详情")
    @PreAuthorize("@ss.hasPermission('crm:brand:query')")
    @Translate  // 处理响应数据的多语言字段填充
    public CommonResult<BrandRespVO> getBrand(@RequestParam("id") Long id) {
        BrandDO brand = brandService.getBrand(id);
        return success(BrandConvert.INSTANCE.convert(brand));
    }

    @PostMapping("/save")
    @Operation(summary = "保存品牌")
    @PreAuthorize("@ss.hasPermission('crm:brand:create')")
    @Translate  // 处理请求数据的多语言字段保存
    public CommonResult<Long> saveBrand(@Valid @RequestBody BrandSaveReqVO saveReqVO) {
        Long id = brandService.saveBrand(saveReqVO);
        return success(id);
    }
}
```

### 7.5 多语言字段使用场景

#### 需要多语言的场景

- 用户输入的业务数据（品牌描述、公司名称、地址、备注等）
- 需要在不同语言环境下展示不同内容的字段
- 跨国业务场景下的关键信息字段

#### 不需要多语言的场景

- 系统生成的编号（如：leadNo、brandNo）
- 枚举值和字典码（如：status、type）
- 数值类型（如：金额、数量、百分比）
- 日期时间（如：createTime、updateTime）
- 标识符（如：id、userId、tenantId）
- 品牌名称等专有名词（根据业务需求决定）

### 7.6 多语言数据存储

多语言数据存储在独立的多语言表中，通过 AOP 自动处理：

- **读取时**: 根据当前语言环境自动填充 `xxxML` Map 字段
- **保存时**: 自动将 `xxxML` Map 数据保存到多语言表
- **更新时**: 自动更新多语言表中的对应记录

**多语言表结构示例**:

```sql
CREATE TABLE `system_i18n_data` (
  `id` BIGINT NOT NULL COMMENT '主键ID',
  `module` VARCHAR(64) NOT NULL COMMENT '模块编码',
  `domain` VARCHAR(64) NOT NULL COMMENT '业务域',
  `name` VARCHAR(64) NOT NULL COMMENT '字段名',
  `ref_id` BIGINT NOT NULL COMMENT '关联业务ID',
  `lang_code` VARCHAR(16) NOT NULL COMMENT '语言编码(如:zh-CN,en-US)',
  `content` TEXT COMMENT '翻译内容',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_module_domain_name_ref_lang` (`module`, `domain`, `name`, `ref_id`, `lang_code`, `tenant_id`)
) COMMENT='多语言数据表';
```

## 8. 接口文档模板

```markdown
### 4.1 Controller 接口

#### 4.1.1 分页查询接口

​```java
[接口代码]
​```

**权限码**: `module:query`

**请求参数**:
- `param1`: 参数说明
- `param2`: 参数说明

**响应数据**: 响应说明

### 4.2 Service 接口

​```java
public interface LeadPoolService {

    // 分页查询公海池线索
    PageResult<LeadMainDO> getLeadPoolPage(LeadPoolPageReqVO pageReqVO);

    // 统计卡片
    LeadPoolStatisticsRespVO getStatistics();

    // 详情查询
    LeadMainDO getLeadPool(Long id);
}
​```

### 4.3 Mapper 接口

​```java
@Mapper
public interface LeadMainMapper extends BaseMapperX<LeadMainDO> {

    // 分页查询公海池线索（带数据权限过滤）
    default PageResult<LeadMainDO> selectPage(LeadPoolPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<LeadMainDO>()
            .eq(LeadMainDO::getPoolType, "PUBLIC")
            .likeIfPresent(LeadMainDO::getBrandName, reqVO.getBrandName())
            .orderByDesc(LeadMainDO::getUpdateTime));
    }
}
​```
```
