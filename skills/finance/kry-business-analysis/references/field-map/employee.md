# 员工 字段取数契约

---

## 总部员工列表

**路径**：`/open/standard/employee/brand/list`
**授权**：品牌授权
**数据路径**：`response.result.data.page.list`

### 请求参数要点

必填：`pageNo` + `pageSize` + **`orgId`**（传品牌ID，❌ 不能缺失）
分页模式：平铺 `pageNo`/`pageSize`（不是 pageBean 嵌套）

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 员工ID | id | Long | — | ⚠️ 字段名是 id 不是 employeeId |
| 员工姓名 | name | String | — | — |
| 手机号 | mobilePhone | String | — | ⚠️ 不是 mobile |
| 工号 | workId | String | — | ⚠️ 不是 jobNumber |
| 性别 | sex | String | — | MALE/FEMALE |
| 邮箱 | email | String | — | — |
| 头像 | avatarUrl | String | — | URL |
| 员工状态 | status | String | — | NORMAL=在职 |
| 入职时间 | hiredDate | String | — | 可能为 null |
| 账号类型 | accountType | String | — | — |
| 归属机构名称 | orgName | String | — | — |
| 归属机构类型 | orgType | String | — | BRAND/STORE |
| 归属机构ID | kryOrgId | Long | — | — |

### 分页字段

| 业务含义 | 字段名 | 类型 |
|---------|--------|------|
| 总数 | totalCount | Long |
| 页码 | pageNo | Long |
| 页大小 | pageSize | Long |
| 总页数 | totalPage | Long |

### ⚠️ 易混字段对照

| 容易混淆的字段     | 正确区分                                   |
| ------------------ | ------------------------------------------ |
| id vs kryOrgId     | id=员工ID，kryOrgId=员工所属机构ID         |
| mobilePhone vs tel | mobilePhone=手机号，tel=座机（可能为null） |

---

## 总部员工详情

**路径**：`/open/standard/employee/brand/getDetail`
**授权**：品牌授权
**请求参数**：`{"id": <员工ID>}` 或 `{"mobile": "<手机号>"}`（二选一）
**数据路径**：`response.result.data`

### 核心字段

| 业务含义 | 字段名 | 类型 | 单位 | 易错说明 |
|---------|--------|------|------|--------|
| 员工ID | id | Long | — | ⚠️ 不是 employeeId |
| 员工姓名 | name | String | — | — |
| 手机号 | mobilePhone | String | — | — |
| 工号 | workId | String | — | — |
| 账号ID | accountId | Long | — | ≠ id |
| 归属机构ID | orgId | Long | — | — |
| 归属机构类型 | orgType | String | — | BRAND/STORE |
| 角色/权限 | authList | Array | — | 含 roleId/roleName/roleType/authRange |
| 管辖范围 | adminScopeList | Array | — | 含 scopeType/scopeId/scopeName |

### authList[] 子结构

| 业务含义 | 字段名    | 类型   |
| -------- | --------- | ------ |
| 角色ID   | roleId    | Long   |
| 角色名称 | roleName  | String |
| 角色类型 | roleType  | String |
| 授权范围 | authRange | Array  |

### ⚠️ 易混字段对照

| 容易混淆的字段 | 正确区分 |
|--------------|--------|
| id vs accountId | id=员工业务ID，accountId=账号系统ID |
| orgId vs kryOrgId | 同一字段，详情用 orgId，列表用 kryOrgId |

---

## 门店员工列表

**路径**：`/open/standard/employee/shop/list`
**授权**：门店授权
**数据路径**：`response.result.data.page.list`

### 请求参数要点

必填：`pageNo` + `pageSize`（门店授权不需要 orgId）

### 核心字段

与「总部员工列表」结构一致，额外可能包含：

| 业务含义 | 字段名       | 类型   | 单位 | 易错说明       |
| -------- | ------------ | ------ | ---- | -------------- |
| 岗位ID   | positionId   | Long   | —    | —              |
| 岗位名称 | positionName | String | —    | 如"门店大经理" |
| 工作类型 | workType     | String | —    | FIXED=固定     |

---

## 门店员工详情

**路径**：`/open/standard/employee/shop/getDetail`
**授权**：门店授权
**数据路径**：`response.result.data`

### 核心字段

与「总部员工详情」结构一致，区别仅在授权方式为门店授权。

### ⚠️ 注意

- 品牌授权接口可查所有门店员工，门店授权仅能查本店员工
- 两套接口返回字段一致，选择取决于授权方式
- 请求参数字段为 `id`（非 employeeId）
