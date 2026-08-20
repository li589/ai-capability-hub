# 搜索组件字段速查表（moduleCode: `searchModuleV2`）

> 本文件是 `searchModuleV2` 组件**唯一合法的 fieldKey 来源**。设置 values 时 key 必须取自本文件，不得猜测、不得用 CSS 名。
> key 规则：非数组字段直接用叶子 key 名，**不要加 `style.`/`content.` 前缀**；颜色用十六进制 `#RRGGBB`；枚举用整数。

---

## 组件整体效果 / 用途

**顶部搜索栏**：一条搜索框，点击进入商品搜索。可选附带门店切换、扫一扫、搜索热词；可设置滚动到顶部时**吸顶**固定。框体可描边/填充、直角/圆角。通常放页面**最顶部**，用于导购型首页。

```
┌──────────────────────────┐
│ 🔍 搜索想要的商品      [扫]│  ← 一条搜索栏，可吸顶
└──────────────────────────┘
```

适合：导购型店铺首页顶部搜索入口。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 默认搜索词 / 搜索框文字 | `searchKey` | 字符串，≤9 字 |
| 预设轮播搜索词列表 | `searchKeyList` | 数组，≤5 项，每项 1–9 字 |
| 门店切换 | `switchStore` | `0`(关) / `1`(开) |
| 扫一扫 / 扫码（⚠️ 不是 `scanCode`） | `showScan` | `0`(关) / `1`(开) |
| 搜索热词 / 显示热词（⚠️ 不是 `hotWords`） | `showHotWord` | `0`(不显示) / `1`(显示) |
| 吸顶 / 滚动吸顶 / 悬浮固定（⚠️ 不是 `stickyType`） | `switchCeiling` | `0`(不吸顶) / `1`(吸顶) |
| 搜索类型 / 自定义搜索 / 商品文章筛选 / 搜索过滤 | ❌ 不支持 WAI 操作 | 告知"暂不支持，请在编辑器操作" |
| 搜索栏样式 / 描边或填充 | `searchColorType` | `0`(描边) / `1`(填充) |
| 描边颜色 | `searchColor` | 十六进制色值 |
| 框体样式 / 默认或自定义 | `selectedBorderType` | `1`(默认跟随店铺) / `2`(自定义) |
| 框体圆角（自定义框体时） | `borderStyle` | `0`(直角) / `1`(圆角) / `2`(大圆角) |
| 文本位置 | `keyLocation` | `1`(居左) / `2`(居中) |
| 填充样式内容色 | `contentColor` | 十六进制色值 |
| 组件背景色 | `bgColor` | 十六进制色值 |
| 热词样式 / 描边或填充 | `hotwordsStyleType` | `0`(描边) / `1`(填充) |
| 热词描边色 | `hotwordsOutlineColor` | 十六进制色值 |
| 热词填充色 | `hotwordsFillColor` | 十六进制色值 |
| 热词文字色 | `hotwordsColor` | 十六进制色值 |
| 上间距小 / 上边距无 | `topMargin` | `0` |
| 上间距中 / 上边距中 | `topMargin` | `16` |
| 上间距大 / 上边距大 | `topMargin` | `24` |
| 下间距小 / 下边距无 | `bottomMargin` | `0` |
| 下间距中 / 下边距中 | `bottomMargin` | `16` |
| 下间距大 / 下边距大 | `bottomMargin` | `24` |

---

## 二、顶层字段

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `styleGroup` | integer | 固定 `1` | `1` | 只有一种样式 |

---

## 三、内容字段（content，用叶子 key）

| 字段key | 类型 | 枚举/约束 | 默认 | 说明 |
|---|---|---|---|---|
| `searchKey` | string | ≤9 字 | `""` | 搜索框默认文字 |
| `searchKeyList` | array | ≤5 项，每项 1–9 字 | `[""]` | 预设轮播搜索词 |
| `switchStore` | integer | `0`(关) / `1`(开) | `0` | 门店切换 |
| `showScan` | integer | `0`(关) / `1`(开) | `0` | 扫一扫 |
| `showHotWord` | integer | `0`(不显示) / `1`(显示) | `0` | 搜索热词 |
| `switchCeiling` | integer | `0`(不吸顶) / `1`(吸顶) | `0` | 吸顶规则 |
| `searchProductType` | integer | 固定 `0` | `0` | 搜索类型，固定不可改 |

> ⛔ 字段名禁用对照：`scanCode` 不存在→用 `showScan`；`hotWords`/`hotWord` 不存在→用 `showHotWord`；`stickyType`/`sticky` 不存在→用 `switchCeiling`；`searchType`/`goodsArticleFilter` 不存在且不支持。
> ⛔ 开关字段（`switchStore`/`showScan`/`showHotWord`/`switchCeiling`）传整数 `0`/`1`，不传 boolean `true`/`false`。

## 四、样式字段（style，用叶子 key，不要加 `style.` 前缀）

| 字段key | 类型 | 枚举/约束 | 默认 | 说明 |
|---|---|---|---|---|
| `searchColorType` | integer | `0` / `1` | `0` | 0描边 1填充 |
| `searchColor` | string(color) | `#RRGGBB` | `#212121` | 描边颜色 |
| `selectedBorderType` | integer | `1` / `2` | `1` | 1默认 2自定义 |
| `borderStyle` | integer | `0` / `1` / `2` | `0` | 自定义框体圆角 |
| `keyLocation` | integer | `1` / `2` | `1` | 文本位置：1左 2中 |
| `contentColor` | string(color) | `#RRGGBB` | `#212121` | 填充样式内容色 |
| `bgColor` | string(color) | `#RRGGBB` | `#FFFFFF` | 组件背景色 |
| `hotwordsStyleType` | integer | `0` / `1` | `1` | 热词：0描边 1填充 |
| `hotwordsOutlineColor` | string(color) | `#RRGGBB` | `#212121` | 热词描边色 |
| `hotwordsFillColor` | string(color) | `#RRGGBB` | `#F5F5F5` | 热词填充色 |
| `hotwordsColor` | string(color) | `#RRGGBB` | `#212121` | 热词文字色 |
| `topMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 上边距；只能取这三个值，不得传其他数字 |
| `bottomMargin` | integer | `0`(无/小) / `16`(中) / `24`(大) | `0` | 下边距；只能取这三个值，不得传其他数字 |
