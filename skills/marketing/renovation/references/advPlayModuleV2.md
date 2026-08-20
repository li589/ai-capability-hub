# 轮播图组件字段速查表（moduleCode: `advPlayModuleV2`）

> 本文件是 `advPlayModuleV2` 组件**唯一合法的 fieldKey 来源**。设置 values 时 key 必须取自本文件，不得猜测、不得用 CSS 名。
> key 规则：非数组字段直接用叶子 key 名，**不要加 `style.`/`content.` 前缀**；图片列表用 `items[N].子字段`（N 从 0 计）；颜色用十六进制；枚举用整数。

---


## 组件整体效果 / 用途

顶部主视觉**横幅 banner**：一张或多张大图，自动或手动轮播。整屏宽、视觉最重，通常放页面**最顶部**作主视觉。`styleGroup` 决定整体形态：`1`=滚动播放（一张占满、左右轮播），`2`=滑动播放（卡片式、可露出两侧边缘、带间隔）。可设圆角、背景、轮播间隔、指示器。

> ⚠️ **"滚动播放"/"滑动播放"是 `styleGroup`，不是 `slidingStyle`**。`slidingStyle`（0平面/1立体）是 `styleGroup=2`（滑动播放）时的子效果，不能用来切换滚动↔滑动。用户说"改成滚动播放"→ `styleGroup:1`；说"改成滑动播放"→ `styleGroup:2`。

```
┌──────────────────────────┐
│                          │
│        大图 banner        │  ← 整屏宽，自动/手动轮播
│        ● ○ ○             │  ← 底部指示器
└──────────────────────────┘
```

适合：首屏主视觉、活动主图、品牌大图。改图/数量见图片列表字段（同 4-key 规则）。

---

## 一、用户描述 → 字段key 速查表

| 用户可能说的 | 字段key | 合法值 |
|---|---|---|
| 样式分组 / 滚动播放 / 滑动播放 | `styleGroup` | `1`(滚动播放) / `2`(滑动播放)。⚠️ "滚动播放"=`styleGroup:1`，不是 `slidingStyle`；`slidingStyle` 是 `styleGroup=2` 时的立体/平面效果，不能用来切换滚动/滑动 |
| 边角样式 / 圆角 | `borderRadius` | `0`(直角) / `1`(圆角) / `2`(大圆角) |
| 轮播间隔 / 自动播放速度 | `autoplaySpeed` | `1000000`(不自动) / `1000` / `2000` / `3000` / `4000` / `5000`(ms) |
| 轮播样式 | `advStyle` | `1` / `2` / `3` / `4` |
| 选中点颜色用默认色（跟随系统） | `selectColor` | `0`（单独传，不传 `color`） |
| 选中点颜色用自定义色（用户指定颜色时） | `selectColor` + `color` | `selectColor: 1` + `color: <十六进制色值>`（**两个字段同时传**） |
| 预览图片 / 点击放大 | `previewPic` | `0`(关) / `1`(开) |
| 图片间隔小（仅滑动 styleGroup=2） | `space` | `0` |
| 图片间隔中（仅滑动 styleGroup=2） | `space` | `16` |
| 图片间隔大（仅滑动 styleGroup=2） | `space` | `24` |
| 滑动样式（仅滑动 styleGroup=2） | `slidingStyle` | `0`(平面) / `1`(立体) |
| 页边距（仅滚动 styleGroup=1） | `pageMargin` | `0`(无,0px) / `1`(有,28px) |
| 是否有背景 | `haveBackground` | `0`(无) / `1`(有) |
| 背景类型（有背景时） | `backgroundType` | `0`(纯色) / `1`(图片) |
| 背景颜色 | `backgroundColor` | 十六进制色值 |
| 背景图片（backgroundType=1） | `backgroundImage` | 图片 URL |
| 上边距设置（系统/自定义） | `topMarginType` | `0`(系统) / `1`(自定义) |
| 上间距小（系统档位） | `topMargin` | `0` |
| 上间距中（系统档位） | `topMargin` | `16` |
| 上间距大（系统档位） | `topMargin` | `24` |
| 上边距设为自定义具体值（如 30px / 50px） | `topMarginType` + `customTopMargin` | `topMarginType: 1` + `customTopMargin: <0–600 偶数 px>`（**两个字段同时传**） |
| 下边距设置（系统/自定义） | `bottomMarginType` | `0`(系统) / `1`(自定义) |
| 下间距小（系统档位） | `bottomMargin` | `0` |
| 下间距中（系统档位） | `bottomMargin` | `16` |
| 下间距大（系统档位） | `bottomMargin` | `24` |
| 下边距设为自定义具体值（如 30px / 50px） | `bottomMarginType` + `customBottomMargin` | `bottomMarginType: 1` + `customBottomMargin: <0–600 偶数 px>`（**两个字段同时传**） |
| 换图 / 改第N张图 | `items[N].imageUrl` + `items[N].name` + `items[N].width` + `items[N].height`（4 个同传） | 见第四节 |
| 增加图片 / 添加图片 / 追加一张图 / 多加几张图 | **先 `getModuleVal` 读 `items`** 感知现有图片数量，N 接着现有末尾往后排（见第四节「增加图片」） | 见第四节 |

> ⚠️ **上下边距：系统档位 vs 自定义值**（仅轮播图组件支持自定义，其它组件边距只支持系统档位 `0`/`16`/`24`）：
> - 用户说"上/下边距改小/中/大"或给系统档位值（0/16/24）→ 用系统档位：`topMarginType: 0` + `topMargin: 0/16/24`（`topMarginType: 0` 通常可省略，默认即系统）。
> - 用户说"上/下边距改成 30px / 50px"等**自定义具体值**（且不在 0/16/24 系统档位内）→ 用自定义：`topMarginType: 1` + `customTopMargin: <偶数>`（下边距同理用 `bottomMarginType: 1` + `customBottomMargin`），**只传 `customTopMargin`/`customBottomMargin`，不传 `customTopMargin1`/`customBottomMargin1`**。
> - `customTopMargin`/`customBottomMargin` 约束 **0–600 偶数 px**。用户给奇数（如 31）→ 取最近偶数（32）并告知"已调整为 32px"；超出 0–600 → 回复"WAI 暂不支持该值，请在编辑器内操作"。

---

## 二、顶层字段

| 字段key | 类型 | 枚举 | 默认 | 说明 |
|---|---|---|---|---|
| `styleGroup` | integer | `1` / `2` | `1` | 1=滚动播放，2=滑动播放 |

---

## 三、样式字段（style，用叶子 key，不要加 `style.` 前缀）

| 字段key | 类型 | 枚举/约束 | 默认 | 说明 |
|---|---|---|---|---|
| `borderRadius` | integer | `0` / `1` / `2` | `0` | 边角 |
| `autoplaySpeed` | integer | `1000000`/`1000`/`2000`/`3000`/`4000`/`5000` | `3000` | 轮播间隔(ms)，1000000=不自动 |
| `advStyle` | integer | `1`/`2`/`3`/`4` | `1` | 轮播样式 |
| `selectColor` | integer | `0` / `1` | `0` | **轮播指示器（底部小圆点）当前页选中点的颜色**：`0`=用默认色（跟随系统），`1`=自定义色（此时需配 `color` 字段指定具体颜色） |
| `previewPic` | integer | `0` / `1` | `1` | 预览图片 |
| `color` | string(color) | `#RRGGBB` | `#FFFFFF` | **仅 `selectColor=1` 时配传**：选中点的自定义颜色。用户指定选中点颜色时，必须 `selectColor:1` + `color:<色值>` 同时传 |
| `space` | integer | `0`(无) / `16`(中) / `24`(大) | `16` | **仅 styleGroup=2**：图片间隔；只能取这三个值 |
| `slidingStyle` | integer | `0` / `1` | `0` | **仅 styleGroup=2**：0平面 1立体。⚠️ 不是"滚动/滑动"切换字段——切换滚动/滑动用 `styleGroup`，`slidingStyle` 只决定 styleGroup=2 时的滚动效果（平面/立体） |
| `pageMargin` | integer | `0` / `1` | `0` | **仅 styleGroup=1**：0无(0px) 1有(28px) |
| `haveBackground` | integer | `0` / `1` | `0` | 是否有背景 |
| `backgroundType` | integer | `0` / `1` | `0` | 0纯色 1图片 |
| `backgroundColor` | string(color) | `#RRGGBB` | `#FFFFFF` | 背景纯色 |
| `backgroundImage` | string | URL | `""` | 背景图，backgroundType=1 时必填非空 |
| `slideArea` | integer | 180–1624 偶数 | `750` | 滑动区域宽 |
| `topMarginType` | integer | `0` / `1` | `0` | 上边距：0系统 1自定义；用户给自定义具体值时传 `1` |
| `topMargin` | integer | `0` / `16` / `24` | `0` | 系统上边距档位（`topMarginType=0` 时用）；只能取这三个值 |
| `bottomMarginType` | integer | `0` / `1` | `0` | 下边距：0系统 1自定义；用户给自定义具体值时传 `1` |
| `bottomMargin` | integer | `0` / `16` / `24` | `0` | 系统下边距档位（`bottomMarginType=0` 时用）；只能取这三个值 |
| `customTopMargin` | integer | 0–600 偶数 | `28` | **自定义上边距**（`topMarginType=1` 时用）；用户给自定义值就传这个，**不传 `customTopMargin1`**；奇数取最近偶数并告知 |
| `customBottomMargin` | integer | 0–600 偶数 | `28` | **自定义下边距**（`bottomMarginType=1` 时用）；用户给自定义值就传这个，**不传 `customBottomMargin1`**；奇数取最近偶数并告知 |

## 四、图片列表字段（content.items，数组）

1–10 张。换图同 imgModuleV2 规则：**`items[N].` 是 key 组成部分，改图必传 4 个 key**（`width`/`height` 默认 750 正方形）。

### 增加图片 / 追加图片（必读，避免覆盖已有图）

用户说"增加一张图 / 添加图片 / 追加几张图 / 再多放几张"时，**不能直接用 `items[0]`/`items[1]` 写图——那样会覆盖现有图片**。必须：

1. **先 `getModuleVal` 读 `items`**（key 就传 `items`），拿到现有图片数组，得知当前有几张（`count`）。
2. 新图从 `N = count` 开始往后排（现有末尾的下一张）。如现有 1 张（`items[0]`）→ 新图写 `items[1]`、`items[2]`…；现有 2 张 → 新图写 `items[2]`、`items[3]`…
3. 每张新图仍按 4-key 规则传齐（`imageUrl`/`name`/`width`/`height`）。
4. **数量上限 10 张**（轮播图不分 styleGroup，统一 ≤10）。追加后超上限 → 告知"轮播图最多 10 张，已达上限，请先减少现有图"，不强行覆盖。

> ⛔ **禁止凭空假设现有图片数量**。不读 `items` 就直接写 `items[0]` = 覆盖第一张原图，是典型错误。增加图片场景下，`getModuleVal` 读 `items` 是必做前置步骤。

| 字段key | 类型 | 约束 | 默认 | 说明 |
|---|---|---|---|---|
| `items[N].name` | string | — | `默认图片` | 图片名，改图必填 |
| `items[N].imageUrl` | string(uri) | URL | — | 图片地址，改图必填 |
| `items[N].width` | number | >0 | `750` | 宽(px)，改图必填 |
| `items[N].height` | number | >0 | `750` | 高(px)，改图必填 |
| `items[N].imgType` | integer | `0`(链接)/`1`(热区) | `0` | 交互类型 |
| `items[N].link` | object | — | `{}` | 跳转链接 |
| `items[N].hotZoneList` | array | — | `[]` | 热区列表 |

---

## 五、styleGroup 约束

| styleGroup | 含义 | 必填/约束 |
|---|---|---|
| `1` | 滚动播放 | 必传 `pageMargin`；**不传** `space`、`slidingStyle` |
| `2` | 滑动播放 | 必传 `space`、`slidingStyle`；**不传** `pageMargin` |

- `haveBackground=0` → `backgroundType` 必为 `0`、`backgroundImage` 必为 `""`。
- `haveBackground=1` 且 `backgroundType=1` → `backgroundImage` 必须为非空 URL。
