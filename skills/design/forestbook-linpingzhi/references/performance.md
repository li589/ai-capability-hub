# HarmonyOS NEXT 性能优化指南

## 性能指标标准

| 指标 | 优秀 | 良好 | 需优化 |
|------|------|------|--------|
| 冷启动时延 | <1s | 1-2s | >2s |
| 帧率 | 60fps | 45-60fps | <45fps |
| 丢帧率 | <5% | 5-15% | >15% |
| 内存占用 | <200MB | 200-400MB | >400MB |

## 列表优化三件套

### 1. LazyForEach 懒加载

```typescript
// IDataSource 完整实现
class BasicDataSource<T> implements IDataSource {
  private listeners: DataChangeListener[] = []
  private data: T[] = []
  
  totalCount(): number { return this.data.length }
  getData(index: number): T { return this.data[index] }
  
  registerDataChangeListener(listener: DataChangeListener): void {
    if (this.listeners.indexOf(listener) < 0) {
      this.listeners.push(listener)
    }
  }
  
  unregisterDataChangeListener(listener: DataChangeListener): void {
    const pos = this.listeners.indexOf(listener)
    if (pos >= 0) this.listeners.splice(pos, 1)
  }
  
  pushData(item: T): void {
    this.data.push(item)
    this.listeners.forEach(l => l.onDataAdd(this.data.length - 1))
  }
  
  reloadData(data: T[]): void {
    this.data = data
    this.listeners.forEach(l => l.onDataReloaded())
  }
}
```

### 2. @Reusable 组件复用

```typescript
@Reusable
@Component
struct ReusableItem {
  @State item: ItemModel = new ItemModel()
  
  aboutToReuse(params: Record<string, Object>): void {
    this.item = params.item as ItemModel  // 必须更新状态
  }
  
  aboutToRecycle(): void {
    // 可选：清理大对象
  }
  
  build() { /* UI */ }
}

// 使用
ReusableItem({ item }).reuseId(item.type)
```

### 3. cachedCount 配置

```typescript
List() {
  LazyForEach(this.dataSource, ...)
}
.cachedCount(5)  // 推荐：屏幕可见数 × 0.5~1.5
```

## 布局优化

### 减少嵌套

```typescript
// ✅ RelativeContainer 扁平化
RelativeContainer() {
  Text('标题').id('title')
    .alignRules({ top: { anchor: '__container__', align: VerticalAlign.Top } })
  Text('内容').id('content')
    .alignRules({ top: { anchor: 'title', align: VerticalAlign.Bottom } })
}
```

### 组件选择

| 场景 | 推荐 | 避免 |
|------|------|------|
| 简单排列 | Row/Column | Flex |
| 复杂定位 | RelativeContainer | 多层嵌套 |
| 列表 | List+LazyForEach | Scroll+ForEach |

## 启动优化

```typescript
// 异步初始化
onCreate() {
  taskpool.execute(this.initAsync.bind(this))
}

@Concurrent
async initAsync() {
  await this.initDatabase()
  await this.loadConfig()
}
```

## 内存管理

```typescript
// 清理资源
aboutToDisappear() {
  clearInterval(this.timer)
  this.subscription?.unsubscribe()
  this.largeObject = null
}

// LRU缓存
let cache = new LRUCache<string, Data>(100)
```

## 渲染优化

```typescript
// renderGroup：固定内容整体动画
Column() {
  Image($r('app.media.avatar'))
  Text('固定内容')
}
.renderGroup(true)
.translate({ x: this.offsetX })
```

## 异步处理

```typescript
// TaskPool（短任务）
@Concurrent
function task(data: string): string { return process(data) }
let result = await taskpool.execute(new taskpool.Task(task, 'input'))

// Worker（长任务）
let worker = new worker.ThreadWorker('workers/MyWorker.ts')
worker.postMessage(data)
```

## 检查清单

- [ ] LazyForEach + cachedCount + @Reusable
- [ ] 布局嵌套<10层
- [ ] 异步初始化非必要模块
- [ ] 清理定时器和订阅
- [ ] 图片异步加载+合适尺寸
