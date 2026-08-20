---
name: linpingzhi
description: HarmonyOS NEXT原生应用开发专家技能。当用户需要开发鸿蒙应用时触发，包括：(1)使用ArkTS/ArkUI编写代码 (2)实现UI界面和组件 (3)状态管理和数据绑定 (4)动画与转场效果 (5)网络请求和数据持久化 (6)多设备适配和分布式能力 (7)性能优化和最佳实践。生成符合华为官方规范的高质量鸿蒙原生代码。
install_source: official
install_method: download
skill_id: official_5B9Oi3Ld
enabled_at: 1787232392852
version: 1.0.0
name_zh: 代码生成
---

# Linpingzhi - HarmonyOS NEXT开发专家

专注于HarmonyOS NEXT（API 12+）原生应用开发，使用ArkTS语言和ArkUI声明式框架。

## 核心技术栈

- **语言**: ArkTS（TypeScript超集，严格类型）
- **框架**: ArkUI声明式UI
- **模型**: Stage应用模型
- **工具**: DevEco Studio

## ArkTS语法要点

### 严格约束
```typescript
// ✅ 正确
let name: string = '张三'
const age: number = 25

// ❌ 禁止
var x = 1           // 禁用var
let any_val: any    // 禁用any
obj["key"]          // 禁止动态属性
```

### 状态管理装饰器

| 装饰器 | 作用域 | 同步方式 | 使用场景 |
|--------|--------|----------|----------|
| @State | 组件内 | - | 组件私有状态 |
| @Prop | 父→子 | 单向(深拷贝) | 父传子，子不影响父 |
| @Link | 父↔子 | 双向(引用) | 父子数据同步 |
| @Provide/@Consume | 跨层级 | 双向 | 爷孙组件通信 |
| @ObjectLink | 嵌套对象 | 引用 | 配合@Observed监听嵌套属性 |
| @StorageLink | 全局 | 双向 | 应用级持久化状态 |

**传参语法**：@Prop直接传值，@Link用`$`符号传引用

```typescript
// 父组件
@State count: number = 0
Child({ propVal: this.count, linkVal: $count })

// 子组件
@Prop propVal: number      // 单向
@Link linkVal: number      // 双向
```

## 组件开发模板

### 基础页面结构
```typescript
@Entry
@Component
struct PageName {
  @State message: string = 'Hello'

  build() {
    Column() {
      Text(this.message)
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
      
      Button('点击')
        .onClick(() => this.message = '已点击')
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }
}
```

### 自定义组件
```typescript
@Component
struct CustomCard {
  @Prop title: string = ''
  @BuilderParam content: () => void = this.defaultContent

  @Builder defaultContent() { Text('默认内容') }

  build() {
    Column() {
      Text(this.title).fontSize(18).fontWeight(FontWeight.Bold)
      this.content()
    }
    .padding(16)
    .backgroundColor('#fff')
    .borderRadius(8)
  }
}
```

### 复用装饰器

```typescript
// @Builder - 轻量UI片段
@Builder function CardItem(title: string) {
  Text(title).fontSize(16).padding(12)
}

// @Styles - 通用样式复用（不支持参数）
@Styles function cardStyle() {
  .backgroundColor('#fff')
  .borderRadius(8)
  .padding(16)
}

// @Extend - 扩展特定组件（支持参数）
@Extend(Text) function titleText(size: number) {
  .fontSize(size)
  .fontWeight(FontWeight.Bold)
}
```

## 列表性能优化

### LazyForEach + @Reusable
```typescript
// 数据源实现
class MyDataSource implements IDataSource {
  private data: MyItem[] = []
  
  totalCount(): number { return this.data.length }
  getData(index: number): MyItem { return this.data[index] }
  
  registerDataChangeListener(listener: DataChangeListener) {}
  unregisterDataChangeListener(listener: DataChangeListener) {}
}

// 可复用组件
@Reusable
@Component
struct ReusableItem {
  @State item: MyItem = new MyItem()

  aboutToReuse(params: Record<string, Object>) {
    this.item = params.item as MyItem
  }

  build() {
    Row() {
      Text(this.item.name)
    }.padding(12)
  }
}

// 列表使用
List() {
  LazyForEach(this.dataSource, (item: MyItem) => {
    ListItem() {
      ReusableItem({ item: item })
    }
  }, (item: MyItem) => item.id.toString())
}
.cachedCount(5)
```

## 动画实现

### 显式动画
```typescript
animateTo({
  duration: 500,
  curve: Curve.EaseInOut,
  onFinish: () => console.log('完成')
}, () => {
  this.opacity = this.opacity === 1 ? 0 : 1
  this.scale = this.scale === 1 ? 1.2 : 1
})
```

### 转场动画
```typescript
if (this.isShow) {
  Column()
    .transition(
      TransitionEffect.OPACITY
        .combine(TransitionEffect.translate({ y: 100 }))
        .animation({ duration: 400, curve: Curve.EaseOut })
    )
}
```

### 一镜到底
```typescript
Image($r('app.media.photo'))
  .geometryTransition('shared_id')  // 相同id实现共享元素转场
```

## 路由导航

### Navigation（推荐）
```typescript
@Entry
@Component
struct MainPage {
  pageStack: NavPathStack = new NavPathStack()

  build() {
    Navigation(this.pageStack) {
      Button('跳转详情')
        .onClick(() => this.pageStack.pushPath({ name: 'DetailPage', param: { id: 1 } }))
    }
    .navDestination(this.PageBuilder)
  }

  @Builder PageBuilder(name: string, param: Object) {
    if (name === 'DetailPage') {
      DetailPage({ param: param })
    }
  }
}
```

### 路由配置 (module.json5)
```json
{
  "routerMap": "$profile:route_map"
}
```

## 网络请求

```typescript
import { http } from '@kit.NetworkKit'

async function fetchData<T>(url: string): Promise<T> {
  const httpRequest = http.createHttp()
  const response = await httpRequest.request(url, {
    method: http.RequestMethod.GET,
    header: { 'Content-Type': 'application/json' }
  })
  httpRequest.destroy()
  return JSON.parse(response.result as string) as T
}
```

## 数据持久化

### Preferences（键值对）
```typescript
import { preferences } from '@kit.ArkData'

const store = await preferences.getPreferences(context, 'settings')
await store.put('theme', 'dark')
await store.flush()
const theme = await store.get('theme', 'light')
```

## 生命周期

```typescript
@Entry
@Component
struct LifecyclePage {
  aboutToAppear() { /* 组件创建，初始化数据 */ }
  aboutToDisappear() { /* 组件销毁，清理资源 */ }
  onPageShow() { /* 页面显示 */ }
  onPageHide() { /* 页面隐藏 */ }
  onBackPress(): boolean { return false /* 返回true拦截返回 */ }
}
```

## 多设备适配

```typescript
GridRow({ columns: { sm: 4, md: 8, lg: 12 } }) {
  GridCol({ span: { sm: 4, md: 4, lg: 3 } }) {
    CardItem()
  }
}
.onBreakpointChange((bp) => this.breakpoint = bp)
```

## 代码规范

1. **类型安全**: 始终声明类型，禁用any
2. **状态管理**: 根据数据流向选择正确的装饰器
3. **性能优化**: 长列表用LazyForEach，复杂组件用@Reusable
4. **布局优先**: Row/Column > Flex，减少嵌套层级
5. **资源引用**: 使用$r('app.xxx')引用资源
6. **异步处理**: 耗时操作使用TaskPool/Worker

## 详细参考

- 状态管理详解: [references/state-management.md](references/state-management.md)
- 动画完全指南: [references/animation-guide.md](references/animation-guide.md)
- 性能优化手册: [references/performance.md](references/performance.md)
