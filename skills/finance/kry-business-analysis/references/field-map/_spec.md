# 字段取数契约格式规范

本目录下的每个 `.md` 文件对应一组业务域接口的字段取数契约。模型在提取接口返回数据时 **必须** 参照此契约，禁止自行推断字段含义。

---

## 文件编写规范

每个接口按以下结构编写：

```markdown
## <接口中文名>

**路径**：`<接口URI>`
**授权**：品牌授权 / 门店授权
**数据路径**：`<从response到目标数组/对象的完整JSON路径>`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|---------|
| 中文含义 | fieldName | string/number | 元/分/笔/% | 备注 |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|---------|
| fieldA vs fieldB | fieldA=含义A，fieldB=含义B |

### 校验规则

- 规则1
- 规则2
```

---

## 通用规则

### 金额单位

| 接口类别 | 金额单位 | 展示转换 |
|---------|---------|---------|
| 营收/收入/优惠/菜品销售类报表 | **元**（字符串） | 直接展示 |
| 团购对账 | **分**（字符串） | ÷100 转元 |
| 其他 | 参照具体接口标注 | — |

### 数据路径约定

- 所有报表类接口的数据均在 `response.result` 内
- 具体列表路径由各接口文档中 `数据提取路径` 标注
- 分页接口通常有 `totalSize` 字段表示总数
- ⚠️ **空数据容错**：部分接口数据为空时，`list`/`values` key 可能不存在（仅返回 `{"totalSize":0}`），取值时必须先判断 key 是否存在，不能直接访问

### 动态列结构

营收/收入构成/优惠构成等接口使用动态列结构：

```jsonc
{
  "itemList": [
    { "code": "编码", "name": "名称", "amount": "金额值" }
  ],
  "subTotal": "小计"
}
```

取数时应遍历 `itemList` 按 `code` 或 `name` 匹配目标项，取 `amount` 字段值。

---

## 请求参数常见错误与纠正

以下是真实调用中高频出现的入参错误，**调用前必须核对**：

### 1. 报表类接口通用必填参数

营收/收入/优惠/收款类报表接口（income/v3、constitute/v3、promo/v3、paid/income/v6）共享以下必填参数：

| 参数名                | 类型            | 必填 | 正确值示例                            | ❌ 常见错误                            |
| --------------------- | --------------- | ---- | ------------------------------------- | ------------------------------------- |
| shopIds               | Array\<String\> | 是   | `["80384673"]`                        | ❌ 用 `shopIdList`；❌ 用数字而非字符串 |
| periodType            | String          | 是   | `"BY_DAY"`                            | ❌ 缺失此参数                          |
| couponStatisticalType | String          | 是   | `"BY_NAME"`                           | ❌ 缺失此参数                          |
| storeStatisticalType  | String          | 是   | `"SEPARATE"`                          | ❌ 缺失此参数                          |
| pageBean              | Object          | 是   | `{"pageNum":1,"pageSize":1000}`       | ❌ 用 pageNo/pageSize 平铺             |
| dateRange             | Object          | 是   | `{"startDate":"...","endDate":"..."}` | ❌ 用 startDate/endDate 平铺           |

### 2. paid/income/v6 额外必填参数

| 参数名                | 类型    | 必填 | 正确值示例          | ❌ 常见错误   |
| --------------------- | ------- | ---- | ------------------- | ------------ |
| tabType               | String  | 是   | `"BUSINESS_INCOME"` | ❌ 缺失此参数 |
| statisticsByBusi      | Boolean | 是   | `true`              | ❌ 缺失此参数 |
| statisticsByOrderType | Boolean | 是   | `false`             | ❌ 缺失此参数 |

### 3. 菜品销售 orderItem/list 必填参数（全部为 Object 类型）

| 参数名               | 类型   | 必填 | 正确值示例                                               | ❌ 常见错误             |
| -------------------- | ------ | ---- | -------------------------------------------------------- | ---------------------- |
| countLatitude        | Object | 是   | `{"countCollectType":0,"countType":1}`                   | ❌ 传字符串 `"BY_DISH"` |
| sellLatitude         | Object | 是   | `{"sellCollectType":false,"countType":"SINGLE_PACKAGE"}` | ❌ 缺失                 |
| orderSourceCondition | Object | 是   | `{"operationFlag":0,"orderSources":[]}`                  | ❌ 缺失                 |
| orderTypeCondition   | Object | 是   | `{"operationFlag":0,"orderTypes":[]}`                    | ❌ 缺失                 |
| goodsTempFlag        | Long   | 是   | `0`                                                      | ❌ 缺失                 |

### 4. 员工接口参数易错

| 接口                     | 参数名 | 正确用法             | ❌ 常见错误        |
| ------------------------ | ------ | -------------------- | ----------------- |
| employee/brand/list      | orgId  | 必填，传品牌ID       | ❌ 缺失 orgId      |
| employee/brand/getDetail | id     | 传员工ID             | ❌ 用 `employeeId` |
| employee/shop/list       | —      | 门店授权，无需 orgId | —                 |
| employee/shop/getDetail  | id     | 传员工ID             | ❌ 用 `employeeId` |

### 5. 菜品分页查询参数

| 接口                        | 参数名    | 正确用法    | ❌ 常见错误    |
| --------------------------- | --------- | ----------- | ------------- |
| dish/shop/pageQueryBaseDish | pageIndex | 页码从1开始 | ❌ 用 `pageNo` |
| dish/shop/pageQueryBaseDish | pageSize  | 每页大小    | —             |

### 6. 报表类分页参数差异汇总

| 分页模式                | 适用接口                                                                                  | 参数格式                                   |
| ----------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------ |
| pageBean 嵌套对象       | income/v3、constitute/v3、promo/v3、paid/v6、orderItem/list、payment/reconciliation/v4、order/queryList（值为String） 等 | `"pageBean":{"pageNum":1,"pageSize":1000}` |
| 平铺 pageNo/pageSize    | employee/brand/list                                                      | `"pageNo":1,"pageSize":100`                |
| 平铺 pageIndex/pageSize | dish/shop/pageQueryBaseDish                                                               | `"pageIndex":1,"pageSize":20`              |
| pageBean with pageNo    | report/order/table-avg/page、dinner/*                                                     | `"pageBean":{"pageNo":1,"pageSize":100}`   |

### 7. 最佳实践

- **调用前先执行 `kry-cli view <接口路径>`** 获取完整参数列表和示例
- 报表接口默认使用：`periodType:"BY_DAY"`, `couponStatisticalType:"BY_NAME"`, `storeStatisticalType:"SEPARATE"`
- shopIds 传空数组 `[]` 表示查询全部门店（最多前1000家）
- 门店ID必须是**字符串数组**，不是数字数组

---

## 使用方式

模型在执行数据查询后：
1. 根据接口路径找到对应的 field-map 文件
2. 按「数据路径」定位到目标数组
3. 按「核心字段」表中的字段名提取数据
4. 检查「易混字段对照」避免取错
5. 执行「校验规则」验证数据合理性
