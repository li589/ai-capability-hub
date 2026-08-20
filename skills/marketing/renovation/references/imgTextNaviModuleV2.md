# 图文导航组件字段速查表（moduleCode: `imgTextNaviModuleV2`）

> 本文件是 `imgTextNaviModuleV2` 组件**唯一合法的 fieldKey 来源**。设置 values 时 key 必须取自本文件，不得猜测、不得用 CSS 名。
> key 规则：非数组字段直接用叶子 key 名，**不要加 `style.`/`content.` 前缀**；导航项用 `items[N].子字段`（N 从 0 计）；颜色用十六进制；枚举用整数。
> ⚠️ 注意本组件 `topMargin`/`bottomMargin` 档位是 **`0`/`24`/`36`**，与其它组件的 `0`/`16`/`24` 不同。

---

## 组件整体效果 / 用途

**图标入口宫格**：每个入口 = 一张自定义图片 + 一行文字。`styleGroup`：`1`=单行滑动（一行图标，超出可左右滑，≥3 个），`2`=多行排列（按每行 3/4/5 个换行成宫格，≥6 个）。常用于分类/功能/活动入口聚合。

> ⛔ 每个**导航入口的跳转 `link` 固定为空对象 `{}`**（schema `const:{}`），**不支持配置跳转**。用户若要求"给导航入口配跳转"→ 告知"WAI 暂不支持当前操作，请在编辑器内操作"，不自造、不调工具。入口的图标/文字/颜色可改。

```
单行滑动(styleGroup=1)            多行排列(styleGroup=2, 每行4个)
┌──┬──┬──┬──┬─→             ┌──┬──┬──┬──┐
│◢ │◣ │◤ │◥ │ 滑           │◢ │◣ │◤ │◥ │
│文│文│文│文│              ├──┼──┼──┼──┤
└──┴──┴──┴──┘              │◢ │◣ │◤ │◥ │
                            └──┴──┴──┴──┘
```

适合：分类入口、功能导航、活动会场入口。各入口图标/文字/链接见导航项字段。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 样式分组 / 单行还是多行 | `styleGroup` | `1`(单行滑动) / `2`(多行排列) |
| 两行展示 / 两行排列 | `distributionType`（styleGroup=2 时有效，⚠️ 当前非 2 需同时传 `styleGroup: 2`） | `1`（固定两行，**不需要再传 `pictureDistribution`**） |
| 每行3个展示 / 每行4个展示 / 每行5个展示 | `distributionType` + `pictureDistribution`（styleGroup=2 时有效，⚠️ 当前非 2 需同时传 `styleGroup: 2`） | `distributionType: 2` 配合 `pictureDistribution: 3/4/5`（**两个字段同时传**） |
| 每行2个 / 每行6个及以上 | ❌ 不支持 | `pictureDistribution` 只接受 `3`/`4`/`5`，告知用户选最接近的一档 |
| 左右间距（styleGroup=2 时有效） | `pictureLRSpacing`（⚠️ 当前非 2 需同时传 `styleGroup: 2`） | 整数 0–100(rpx) |

> ⚠️ **`distributionType`/`pictureDistribution`/`pictureLRSpacing` 仅 `styleGroup=2`（多行排列）时生效。当前 `styleGroup` 未知时，禁止直接回复"无法操作"——必须先用 `getModuleVal` 读取 `styleGroup` 的当前值**（商户可能已手动切换为多行）：
> - 读到 `styleGroup=2` → 直接 `update` 设置目标字段。
> - 读到 `styleGroup=1` → 在同一个 `update` 里同时传 `styleGroup: 2` + 目标字段（如 `distributionType: 2, pictureDistribution: 4`），一步完成切换+设置。
| 边角类型设为系统预设 / 启用圆角档位 | `edgeCornerType` | `1`（需同时传 `borderRadius` 选择档位） |
| 边角类型设为自定义 / 像素级圆角 | `edgeCornerType` | `2`（需同时传 `pictureEdgeCornerSingle`/`Multiple`） |
| 边角改成直角（⚠️ 需同时传 `edgeCornerType: 1`） | `borderRadius` | `0`（**枚举整数，不是像素值**） |
| 边角改成圆角（⚠️ 需同时传 `edgeCornerType: 1`） | `borderRadius` | `1`（**枚举整数，不是像素值**） |
| 边角改成大圆角（⚠️ 需同时传 `edgeCornerType: 1`）（⚠️ 不是 `12`，枚举值是 `2`） | `borderRadius` | `2`（**枚举整数，不是像素值**） |
| 自定义边角圆角值（单行时，⚠️ 需同时传 `edgeCornerType: 2`） | `pictureEdgeCornerSingle` | 整数 0–60 |
| 自定义边角圆角值（多行时，⚠️ 需同时传 `edgeCornerType: 2`） | `pictureEdgeCornerMultiple` | 整数 0–60 |
| 文字颜色 | `color` | 十六进制色值 |
| 背景色 | `bgColor` | 十六进制色值 |
| 图片尺寸 | `imgSize` | `0`(小) / `1`(大) |
| 上间距小 / 上边距无 | `topMargin` | `0` |
| 上间距中 / 上边距中 | `topMargin` | `24` |
| 上间距大 / 上边距大 | `topMargin` | `36` |
| 下间距小 / 下边距无 | `bottomMargin` | `0` |
| 下间距中 / 下边距中 | `bottomMargin` | `24` |
| 下间距大 / 下边距大 | `bottomMargin` | `36` |
| 改导航项名称 / 图片 | `items[N].name` / `items[N].imgUrl` | 见第四节（可改；`link` 恒空不可配跳转） |

---

## 二、顶层字段

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `styleGroup` | integer | `1` / `2` | `1` | 1=单行滑动，2=多行排列 |

---

## 三、内容字段（content，用叶子 key）

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `type` | integer | `0`(系统图标) / `1`(自定义图片) | `1` | 本组件不支持系统图标，固定为 `1`（自定义图片）；**不允许修改，不传此字段** |

## 四、导航项字段（content.items，数组，最多 10 项）

styleGroup=1 至少 3 项，styleGroup=2 至少 6 项。各项必须传 `imgUrl`（自定义图片 URL）。

> ⚠️ **导航项字段必须用 `items[N].子字段` 平铺写法，N 从 0 计，不要传嵌套数组。**
> 正确：`"items[0].name": "手机配件", "items[0].imgUrl": "https://..."`
> 错误：`"items": [{"name": "手机配件", "imgUrl": "..."}]`

> ⚠️ **导航图标字段是 `items[N].imgUrl`（不是 `imageUrl`）**——与轮播图（`advPlayModuleV2`）、图片组件（`imgModuleV2`）的 `items[N].imageUrl` **字段名不同**，build 时严禁混用。导航图标是小方图（宫格入口），不是大 banner；搭建风格页时必须按用途单独生成，不能把轮播大图 URL 填到这里。

| 字段key | 类型 | 约束 | 说明 |
|---|---|---|---|
| `items[N].name` | string | 1–5 字，必填 | 导航文字 |
| `items[N].imgUrl` | string | 必填（⚠️ 是 `imgUrl` 不是 `imageUrl`） | 自定义图片 URL（导航图标，小方图） |
| `items[N].type` | integer | `0`(系统图标，不支持) / `1`(自定义图片) | 固定 `1`；**不允许修改，不传此字段** |
| `items[N].imgName` | string | — | 图片名 |
| `items[N].link` | object | **恒为空对象 `{}`**（schema `const:{}`） | **不支持配置跳转** |

## 五、样式字段（style，用叶子 key，不要加 `style.` 前缀）

| 字段key | 类型 | 枚举/约束 | 默认 | 说明 |
|---|---|---|---|---|
| `distributionType` | integer | `1`(两行排列) / `2`(更多分布) | `1` | 多行排列时有效（需 styleGroup=2）；`1`=固定两行不需要 `pictureDistribution`；`2`=自定义每行个数需同时传 `pictureDistribution` |
| `pictureDistribution` | integer | `3` / `4` / `5` | `4` | 仅 `distributionType=2` 时有效；指定每行展示几个，只接受 3/4/5，不得传其他数字 |
| `pictureLRSpacing` | integer | 0–100 | `0` | 多行排列时有效（需 styleGroup=2）：左右间距(rpx) |
| `edgeCornerType` | integer | `1`(系统) / `2`(自定义) | `2` | `1`=系统预设圆角（需搭配 `borderRadius`），`2`=自定义像素圆角（需搭配 `pictureEdgeCornerSingle`/`Multiple`） |
| `borderRadius` | integer | `0`(直角) / `1`(圆角) / `2`(大圆角) | `0` | **仅 `edgeCornerType=1` 时有效**；枚举值 `0`/`1`/`2`，**不是 CSS 像素**（大圆角=`2`，⚠️ 不是 `12` 或其他数字）；只能取这三个值 |
| `pictureEdgeCornerSingle` | integer | 0–60 | `0` | 单行滑动时有效（需 styleGroup=1）；**仅 `edgeCornerType=2` 时有效**：自定义边角像素值 |
| `pictureEdgeCornerMultiple` | integer | 0–60 | `0` | 多行排列时有效（需 styleGroup=2）；**仅 `edgeCornerType=2` 时有效**：自定义边角像素值 |
| `iconColor` | string(color) | `#RRGGBB` | `#212121` | 图标颜色（系统图标模式 type=0 使用；本组件固定 type=1，此字段通常无需修改） |
| `color` | string(color) | `#RRGGBB` | `#212121` | 文字颜色 |
| `bgColor` | string(color) | `#RRGGBB` | `#FFFFFF` | 背景色 |
| `imgSize` | integer | `0` / `1` | `1` | 图片尺寸：0小 1大 |
| `topMargin` | integer | `0`(无) / `24`(中) / `36`(大) | `36` | 上边距；只能取这三个值，不得传其他数字 |
| `bottomMargin` | integer | `0`(无) / `24`(中) / `36`(大) | `36` | 下边距；只能取这三个值，不得传其他数字 |

> ⛔ 表中"需 styleGroup=X"是**前提条件**（该字段仅在满足该 styleGroup 时有效），**不是要你同时传 `styleGroup` 字段**。若组件当前已满足条件，直接传目标字段即可；若不满足，需先确认或同时传 `styleGroup`，但不要把"需 styleGroup=2"误读为"在 values 里加 `styleGroup: 2`"。

---

## 六、styleGroup 约束

| styleGroup | 含义 | 必填/约束 |
|---|---|---|
| `1` | 单行滑动 | 导航项 ≥3；必传 `pictureEdgeCornerSingle`；不传 `distributionType`/`pictureDistribution`/`pictureLRSpacing`/`pictureEdgeCornerMultiple` |
| `2` | 多行排列 | 导航项 ≥6；必传 `distributionType`/`pictureLRSpacing`/`pictureEdgeCornerMultiple`；不传 `pictureEdgeCornerSingle`；**`distributionType=1`（两行）不需要传 `pictureDistribution`；`distributionType=2`（自定义每行个数）必须同时传 `pictureDistribution: 3/4/5`** |
