---
name: kry-comment-query
version: 1.0.0
description: 评价查询与全局扫描。通过 kry-cli comment keruyun 查询门店在多渠道的顾客评价数据，支持单门店查询和批量全局扫描。
---

# 客如云评价查询分析

## 命令说明

通过 `kry-cli comment keruyun` 命令获取评价数据：

```bash
kry-cli comment keruyun --brandId 123 --shopIds 456,789 --start '2026-04-01' --end '2026-04-30'
```

| 参数              | 说明                                         | 必填  | 示例                                  |
| --------------- | ------------------------------------------ | --- | ----------------------------------- |
| `-b, --brandId` | 品牌ID                                       | 否   | `123`                               |
| `-s, --shopIds` | 门店ID，多个用逗号分隔。不传表示全部门店                      | 否   | `870606653` 或 `870606653,870606677` |
| `-o, --output`  | 把数据保存到文件，格式为 .csv                          | 否   | `/path/file.csv`                    |
| `--start`       | 开始时间，ISO 8601 格式 YYYY-MM-DD，最大查询范围为最近 31 天 | 否   | `2026-05-01`                        |
| `--end`         | 结束时间，ISO 8601 格式 YYYY-MM-DD，最大查询范围为最近 31 天 | 否   | `2026-05-31`                        |

**不传时间参数时默认查询最近 31 天的数据。**

---

## 返回格式

### 输出结构

命令将导出评价数据为 `csv` 文件到本地

### 表头字段

| 字段                         | 类型          | 说明                                        |
| -------------------------- | ----------- | ----------------------------------------- |
| `brandId`                  | Long        | 品牌ID                                      |
| `commentId`                | String      | 评价ID                                      |
| `commentSource`            | Long        | 评价来源：2=小程序点餐，16=饿了么外卖，18=美团外卖             |
| `commentTime`              | String      | 评价时间（毫秒时间戳）                               |
| `commentType`              | String      | 评价类型：GOOD=好评，MEDIUM=中评，BAD=差评，FOOD=食品安全问题 |
| `serviceScore`             | Long        | 商家总评分（1-5分）                               |
| `qualityScore`             | Long        | 口味评分（1-5分）                                |
| `environmentScore`         | Long        | 环境评分（1-5分）                                |
| `serviceSatisfactionScore` | Long        | 服务满意度评分（1-5分）                             |
| `commentContent`           | String      | 评价内容                                      |
| `replyStatus`              | Long        | 回复状态：0=未回复，1=已回复                          |
| `isKryReplied`             | Long        | 回复方式：0=未回复，1=手动回复，2=自动回复                  |
| `safetyLabel`              | Long/null   | 食品安全标签：1=安全，0=不安全                         |
| `upDishes`                 | String      | 点赞菜品（多个菜品用逗号分隔）                           |
| `downDishes`               | String      | 点踩菜品（多个菜品用逗号分隔）                           |
| `orderDishes`              | String      | 点单的菜品（多个菜品用逗号分隔）                          |
| `phoneNumber`              | String/null | 评论者电话（已脱敏，如 `130****9883`）                |
| `firstCommentTimeFormat`   | String      | 首评时间（格式化字符串，如 `2024-05-05 12:00:00`）      |
| `hasAddComment`            | Boolean     | 是否包含追评：true=有追评，false=无追评                 |

## 字段枚举

### 评价来源（commentSource）

| commentSource | 渠道名称   |
| ------------- | ---------- |
| 2             | 小程序点餐 |
| 16            | 饿了么外卖 |
| 18            | 美团外卖   |

### 评价类型（commentType）

| commentType | 类型名称     | 处理优先级 |
| ----------- | ------------ | ---------- |
| FOOD        | 食品安全问题 | 最高       |
| BAD         | 差评         | 高         |
| MEDIUM      | 中评         | 中         |
| GOOD        | 好评         | 低         |

### 敏感信息脱敏

| 字段          | 脱敏规则             |
| ------------- | -------------------- |
| `phoneNumber` | 显示为 `130****9883` |
| `userId`      | 显示为 `353569****`  |
