# 商户与门店查询参考（query-merchants / query-stores）

## 命令

| 命令 | 能力 |
|---|---|
| `woscli admin-api query-merchants` | 查询可访问商户列表 |
| `woscli admin-api query-stores` | 查询商户下门店/组织节点 |

## query-merchants

用途：当用户要“查商户”“确认可选商户”时，使用该命令获取商户列表。

### 参数

| 参数 | 说明 |
|---|---|
| `--name` | 商户名称关键词，可模糊搜索 |

### 返回字段

| 字段 | 说明 |
|---|---|
| `bosId` | 商户 ID |
| `merchantName` | 商户名称 |
| `migrated` | 是否已迁移 |

### 示例

```bash
woscli admin-api query-merchants --name '华东'
woscli admin-api query-merchants --name '连锁'
```

## query-stores

用途：当用户要“查门店”“看某商户下有哪些门店”时使用。

### 参数

| 参数 | 说明 |
|---|---|
| `--vidName` | 门店/组织节点名称关键词 |

### 返回字段

| 字段 | 说明 |
|---|---|
| `vid` | 门店/节点 ID |
| `vidType` | 门店/节点类型 |
| `vidName` | 门店名称 |
| `vidTypeName` | 门店类型名称 |

### 示例

```bash
woscli admin-api query-stores --vidName '上海'
woscli admin-api query-stores --vidName '旗舰店'
```

## 注意

- 返回的是候选列表，不代表已切换上下文；切换商户或门店由上层负责。
- `vidType` / `vidTypeName` 可能表示区域或分组节点，不一定是实体门店。
- 不要在自然语言回复中暴露 `bosId`、`vid` 等内部标识。
