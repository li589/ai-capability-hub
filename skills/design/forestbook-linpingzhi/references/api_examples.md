# ArkTS/ArkUI API 完整示例

## 基础组件

### Text 文本
```typescript
Text('Hello World')
  .fontSize(20)
  .fontColor('#333')
  .fontWeight(FontWeight.Bold)
  .fontFamily('HarmonyOS Sans')
  .textAlign(TextAlign.Center)
  .maxLines(2)
  .textOverflow({ overflow: TextOverflow.Ellipsis })
  .decoration({ type: TextDecorationType.Underline, color: '#007AFF' })
  .letterSpacing(2)
  .lineHeight(28)
```

### Image 图片
```typescript
// 本地资源
Image($r('app.media.icon'))
  .width(100)
  .height(100)
  .objectFit(ImageFit.Cover)
  .borderRadius(8)

// 网络图片
Image('https://example.com/image.png')
  .alt($r('app.media.placeholder'))  // 加载中占位图
  .onComplete((event) => console.log('加载完成'))
  .onError(() => console.log('加载失败'))

// PixelMap
Image(this.pixelMap)
  .interpolation(ImageInterpolation.High)
```

### Button 按钮
```typescript
Button('主要按钮', { type: ButtonType.Capsule })
  .width('80%')
  .height(44)
  .backgroundColor('#007AFF')
  .fontColor('#fff')
  .fontSize(16)
  .onClick(() => this.handleClick())

Button({ type: ButtonType.Circle }) {
  Image($r('app.media.add')).width(24).height(24)
}
.width(56)
.height(56)
```

### TextInput 输入框
```typescript
TextInput({ placeholder: '请输入用户名', text: this.username })
  .width('100%')
  .height(48)
  .type(InputType.Normal)
  .maxLength(20)
  .showPasswordIcon(true)
  .onChange((value: string) => this.username = value)
  .onSubmit((enterKey: EnterKeyType) => this.handleSubmit())

// 密码输入
TextInput({ placeholder: '请输入密码' })
  .type(InputType.Password)

// 数字输入
TextInput({ placeholder: '请输入金额' })
  .type(InputType.Number)
```

### TextArea 多行输入
```typescript
TextArea({ placeholder: '请输入内容...', text: this.content })
  .width('100%')
  .height(150)
  .maxLength(500)
  .showCounter(true)
  .onChange((value: string) => this.content = value)
```

## 容器组件

### List 列表
```typescript
List({ space: 10 }) {
  ForEach(this.items, (item: ItemType, index: number) => {
    ListItem() {
      Row() {
        Text(item.title)
        Blank()
        Text(item.value).fontColor('#999')
      }
      .width('100%')
      .padding(16)
    }
    .swipeAction({
      end: this.DeleteButton(index)  // 左滑删除
    })
  }, (item: ItemType) => item.id.toString())
}
.width('100%')
.height('100%')
.divider({ strokeWidth: 1, color: '#eee', startMargin: 16, endMargin: 16 })
.scrollBar(BarState.Auto)
.edgeEffect(EdgeEffect.Spring)
.onScrollIndex((start, end) => console.log(`可见范围: ${start}-${end}`))

@Builder DeleteButton(index: number) {
  Button('删除')
    .backgroundColor(Color.Red)
    .onClick(() => this.items.splice(index, 1))
}
```

### Grid 网格
```typescript
Grid() {
  ForEach(this.items, (item: ItemType) => {
    GridItem() {
      Column() {
        Image(item.image).width('100%').aspectRatio(1)
        Text(item.name).fontSize(14).margin({ top: 8 })
      }
    }
  })
}
.columnsTemplate('1fr 1fr 1fr')  // 3列等宽
.rowsGap(10)
.columnsGap(10)
.scrollBar(BarState.Off)
```

### Tabs 选项卡
```typescript
@State currentIndex: number = 0

Tabs({ barPosition: BarPosition.Start }) {
  TabContent() {
    HomeContent()
  }.tabBar(this.TabBuilder('首页', 0, $r('app.media.home')))
  
  TabContent() {
    MineContent()
  }.tabBar(this.TabBuilder('我的', 1, $r('app.media.mine')))
}
.barMode(BarMode.Fixed)
.onChange((index: number) => this.currentIndex = index)

@Builder TabBuilder(title: string, index: number, icon: Resource) {
  Column() {
    Image(icon)
      .width(24)
      .fillColor(this.currentIndex === index ? '#007AFF' : '#999')
    Text(title)
      .fontSize(12)
      .fontColor(this.currentIndex === index ? '#007AFF' : '#999')
  }
}
```

### Swiper 轮播
```typescript
Swiper() {
  ForEach(this.banners, (banner: BannerType) => {
    Image(banner.image)
      .width('100%')
      .height(200)
      .borderRadius(8)
      .onClick(() => this.handleBannerClick(banner))
  })
}
.autoPlay(true)
.interval(3000)
.loop(true)
.indicator(Indicator.dot()
  .color('#ccc')
  .selectedColor('#007AFF')
)
```

## 弹窗组件

### AlertDialog 警告弹窗
```typescript
AlertDialog.show({
  title: '提示',
  message: '确定要删除吗？',
  autoCancel: true,
  alignment: DialogAlignment.Center,
  primaryButton: {
    value: '取消',
    action: () => console.log('取消')
  },
  secondaryButton: {
    value: '确定',
    fontColor: Color.Red,
    action: () => this.handleDelete()
  }
})
```

### CustomDialog 自定义弹窗
```typescript
@CustomDialog
struct MyDialog {
  controller: CustomDialogController
  onConfirm: () => void = () => {}
  
  build() {
    Column() {
      Text('自定义内容')
      Row() {
        Button('取消').onClick(() => this.controller.close())
        Button('确定').onClick(() => {
          this.onConfirm()
          this.controller.close()
        })
      }
    }
    .padding(20)
  }
}

// 使用
dialogController: CustomDialogController = new CustomDialogController({
  builder: MyDialog({ onConfirm: () => this.handleConfirm() }),
  alignment: DialogAlignment.Center,
  customStyle: true
})

// 打开
this.dialogController.open()
```

### ActionSheet 操作菜单
```typescript
ActionSheet.show({
  title: '选择操作',
  sheets: [
    { title: '拍照', action: () => this.takePhoto() },
    { title: '从相册选择', action: () => this.pickFromAlbum() },
    { title: '取消', action: () => {} }
  ]
})
```

## 手势处理

### 点击手势
```typescript
Text('点击我')
  .onClick((event: ClickEvent) => {
    console.log(`点击位置: ${event.x}, ${event.y}`)
  })
```

### 长按手势
```typescript
Text('长按我')
  .gesture(
    LongPressGesture({ repeat: true })
      .onAction((event: GestureEvent) => console.log('长按中'))
      .onActionEnd(() => console.log('长按结束'))
  )
```

### 拖拽手势
```typescript
@State offsetX: number = 0
@State offsetY: number = 0

Text('拖拽我')
  .translate({ x: this.offsetX, y: this.offsetY })
  .gesture(
    PanGesture()
      .onActionUpdate((event: GestureEvent) => {
        this.offsetX += event.offsetX
        this.offsetY += event.offsetY
      })
  )
```

### 捏合缩放
```typescript
@State scale: number = 1

Image($r('app.media.photo'))
  .scale({ x: this.scale, y: this.scale })
  .gesture(
    PinchGesture()
      .onActionUpdate((event: GestureEvent) => {
        this.scale = event.scale
      })
  )
```

## 数据持久化

### Preferences 轻量存储
```typescript
import dataPreferences from '@ohos.data.preferences'

// 获取实例
let preferences = await dataPreferences.getPreferences(context, 'mystore')

// 写入
await preferences.put('username', 'zhangsan')
await preferences.put('age', 25)
await preferences.flush()

// 读取
let username = await preferences.get('username', '')
let age = await preferences.get('age', 0)

// 删除
await preferences.delete('username')
```

### 关系型数据库
```typescript
import relationalStore from '@ohos.data.relationalStore'

// 配置
const STORE_CONFIG: relationalStore.StoreConfig = {
  name: 'mydb.db',
  securityLevel: relationalStore.SecurityLevel.S1
}

// 建表SQL
const SQL_CREATE_TABLE = `
  CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER
  )
`

// 获取数据库
let rdbStore = await relationalStore.getRdbStore(context, STORE_CONFIG)
await rdbStore.executeSql(SQL_CREATE_TABLE)

// 插入
let valueBucket: relationalStore.ValuesBucket = { name: '张三', age: 25 }
let rowId = await rdbStore.insert('user', valueBucket)

// 查询
let predicates = new relationalStore.RdbPredicates('user')
predicates.equalTo('name', '张三')
let resultSet = await rdbStore.query(predicates, ['id', 'name', 'age'])

while (resultSet.goToNextRow()) {
  let id = resultSet.getLong(resultSet.getColumnIndex('id'))
  let name = resultSet.getString(resultSet.getColumnIndex('name'))
}
resultSet.close()
```

## 权限申请

```typescript
import abilityAccessCtrl from '@ohos.abilityAccessCtrl'
import bundleManager from '@ohos.bundle.bundleManager'

async function requestPermission(permission: string): Promise<boolean> {
  let atManager = abilityAccessCtrl.createAtManager()
  let bundleInfo = await bundleManager.getBundleInfoForSelf(bundleManager.BundleFlag.GET_BUNDLE_INFO_WITH_APPLICATION)
  let tokenId = bundleInfo.appInfo.accessTokenId
  
  // 检查权限
  let grantStatus = await atManager.checkAccessToken(tokenId, permission)
  if (grantStatus === abilityAccessCtrl.GrantStatus.PERMISSION_GRANTED) {
    return true
  }
  
  // 申请权限
  let result = await atManager.requestPermissionsFromUser(context, [permission])
  return result.authResults[0] === 0
}

// 使用
let granted = await requestPermission('ohos.permission.CAMERA')
if (granted) {
  // 有权限，执行操作
}
```

## 文件操作

```typescript
import fs from '@ohos.file.fs'

// 写文件
let filePath = context.filesDir + '/test.txt'
let file = fs.openSync(filePath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE)
fs.writeSync(file.fd, 'Hello World')
fs.closeSync(file)

// 读文件
let file2 = fs.openSync(filePath, fs.OpenMode.READ_ONLY)
let buffer = new ArrayBuffer(1024)
let readLen = fs.readSync(file2.fd, buffer)
let content = String.fromCharCode(...new Uint8Array(buffer.slice(0, readLen)))
fs.closeSync(file2)

// 删除文件
fs.unlinkSync(filePath)
```
