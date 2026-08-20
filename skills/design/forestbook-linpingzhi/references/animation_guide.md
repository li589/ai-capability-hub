# ArkUI 动画开发完全指南

## 动画分类

| 类型 | API | 场景 | 复杂度 |
|------|-----|------|--------|
| 属性动画 | animation() | 简单属性过渡 | ⭐ |
| 显式动画 | animateTo() | 需要回调控制 | ⭐⭐ |
| 转场动画 | transition() | 组件出现/消失 | ⭐⭐ |
| 共享元素 | sharedTransition() | 页面切换 | ⭐⭐⭐ |
| 一镜到底 | geometryTransition() | 组件内共享元素 | ⭐⭐ |
| 路径动画 | motionPath() | 沿轨迹运动 | ⭐⭐⭐ |
| 关键帧 | keyframeAnimateTo() | 多段复杂动画 | ⭐⭐⭐ |
| 粒子动画 | Particle() | 特效(烟花/雨雪) | ⭐⭐⭐⭐ |

## 属性动画 animation()

**原理**：当@State变化时，自动对带animation的属性进行过渡

```typescript
@Entry
@Component
struct PropertyAnimation {
  @State width: number = 100
  @State rotate: number = 0
  
  build() {
    Column({ space: 20 }) {
      Row()
        .width(this.width)
        .height(50)
        .backgroundColor('#007AFF')
        .rotate({ angle: this.rotate })
        .animation({
          duration: 500,
          curve: Curve.EaseInOut,
          delay: 0,
          iterations: 1,
          playMode: PlayMode.Normal
        })
      
      Button('切换')
        .onClick(() => {
          this.width = this.width === 100 ? 200 : 100
          this.rotate = this.rotate === 0 ? 360 : 0
        })
    }
  }
}
```

## 显式动画 animateTo()

**原理**：主动触发动画，支持回调监听

```typescript
@Entry
@Component
struct ExplicitAnimation {
  @State scale: number = 1
  @State opacity: number = 1
  @State translateY: number = 0
  
  build() {
    Column({ space: 30 }) {
      Text('动画目标')
        .fontSize(24)
        .scale({ x: this.scale, y: this.scale })
        .opacity(this.opacity)
        .translate({ y: this.translateY })
      
      Button('触发动画')
        .onClick(() => {
          animateTo({
            duration: 800,
            curve: Curve.Spring,
            delay: 0,
            iterations: 1,
            playMode: PlayMode.Normal,
            onFinish: () => {
              console.log('动画完成')
            }
          }, () => {
            // 闭包内修改状态会产生动画
            this.scale = this.scale === 1 ? 1.5 : 1
            this.opacity = this.opacity === 1 ? 0.5 : 1
            this.translateY = this.translateY === 0 ? -50 : 0
          })
        })
    }
  }
}
```

## 动画曲线 Curve

```typescript
// 内置曲线
Curve.Linear        // 线性
Curve.Ease          // 缓入缓出
Curve.EaseIn        // 缓入
Curve.EaseOut       // 缓出
Curve.EaseInOut     // 缓入缓出
Curve.FastOutSlowIn // 快出慢入（Material风格）
Curve.Sharp         // 锐利
Curve.Smooth        // 平滑
Curve.Friction      // 摩擦（惯性滑动）
Curve.Spring        // 弹簧

// 自定义贝塞尔曲线
import { curves } from '@kit.ArkUI'
let customCurve = curves.cubicBezierCurve(0.42, 0, 0.58, 1)

// 弹簧曲线（物理动画）
// springMotion(response, dampingFraction, overlapDuration)
// response: 响应速度(0-1)，越小越快
// dampingFraction: 阻尼系数(0-1)，越小弹性越大
// overlapDuration: 过冲时间
let springCurve = curves.springMotion(0.5, 0.5, 0)
```

## 转场动画 transition()

**原理**：组件出现(if为true)/消失(if为false)时的动画

```typescript
@Entry
@Component
struct TransitionDemo {
  @State isShow: boolean = false
  
  build() {
    Column({ space: 20 }) {
      Button(this.isShow ? '隐藏' : '显示')
        .onClick(() => this.isShow = !this.isShow)
      
      if (this.isShow) {
        Column() {
          Text('弹出内容')
        }
        .width(200)
        .height(150)
        .backgroundColor('#4ECDC4')
        .borderRadius(12)
        .justifyContent(FlexAlign.Center)
        // 转场动画
        .transition(
          TransitionEffect.OPACITY
            .combine(TransitionEffect.scale({ x: 0.8, y: 0.8 }))
            .combine(TransitionEffect.translate({ y: 100 }))
            .animation({ duration: 400, curve: Curve.EaseOut })
        )
      }
    }
  }
}
```

### TransitionEffect 类型

```typescript
// 基础效果
TransitionEffect.OPACITY                    // 透明度 0↔1
TransitionEffect.SLIDE                      // 滑动
TransitionEffect.SLIDE_SWITCH               // 滑动切换
TransitionEffect.translate({ x, y, z })     // 位移
TransitionEffect.rotate({ angle, x, y, z }) // 旋转
TransitionEffect.scale({ x, y, z })         // 缩放
TransitionEffect.move(TransitionEdge.TOP)   // 边缘移入
TransitionEffect.asymmetric(appear, disappear) // 非对称（出现和消失不同效果）

// 组合使用
TransitionEffect.OPACITY
  .combine(TransitionEffect.scale({ x: 0.5, y: 0.5 }))
  .combine(TransitionEffect.translate({ y: 100 }))
  .animation({ duration: 300, curve: Curve.EaseOut })
```

## 共享元素转场 sharedTransition()

**原理**：页面跳转时，相同id的元素平滑过渡

```typescript
// 列表页
@Entry
@Component
struct ListPage {
  build() {
    List() {
      ForEach(this.items, (item, index) => {
        ListItem() {
          Image(item.image)
            .width(100)
            .height(100)
            // 设置共享id
            .sharedTransition(`image_${index}`, {
              duration: 400,
              curve: Curve.EaseInOut,
              type: SharedTransitionEffectType.Exchange
            })
            .onClick(() => {
              router.pushUrl({ url: 'pages/DetailPage', params: { index } })
            })
        }
      })
    }
  }
}

// 详情页
@Entry
@Component
struct DetailPage {
  @State index: number = 0
  
  build() {
    Column() {
      Image(this.items[this.index].image)
        .width('100%')
        .height(300)
        // 相同的共享id
        .sharedTransition(`image_${this.index}`, {
          duration: 400,
          curve: Curve.EaseInOut
        })
    }
  }
}
```

## 一镜到底 geometryTransition()

**原理**：组件内的共享元素过渡，无需页面跳转

```typescript
@Entry
@Component
struct GeometryTransitionDemo {
  @State isExpanded: boolean = false
  
  build() {
    Column() {
      if (this.isExpanded) {
        // 展开状态
        Column() {
          Image($r('app.media.photo'))
            .width('100%')
            .height(300)
            .geometryTransition('photo')  // 相同id
            .onClick(() => this.isExpanded = false)
          
          Text('详情内容...')
            .transition(TransitionEffect.OPACITY.animation({ delay: 200 }))
        }
        .width('100%')
      } else {
        // 收起状态
        Image($r('app.media.photo'))
          .width(100)
          .height(100)
          .borderRadius(8)
          .geometryTransition('photo')  // 相同id
          .onClick(() => this.isExpanded = true)
      }
    }
    .width('100%')
  }
}
```

## 关键帧动画 keyframeAnimateTo()

**原理**：多段动画，每段可有不同配置

```typescript
import { keyframeAnimateTo } from '@kit.ArkUI'

@Entry
@Component
struct KeyframeDemo {
  @State scale: number = 1
  @State rotate: number = 0
  @State opacity: number = 1
  
  build() {
    Column() {
      Text('关键帧动画')
        .scale({ x: this.scale, y: this.scale })
        .rotate({ angle: this.rotate })
        .opacity(this.opacity)
      
      Button('播放')
        .onClick(() => {
          keyframeAnimateTo({ iterations: 1 }, [
            // 第一段: 0-300ms
            {
              duration: 300,
              curve: Curve.EaseIn,
              event: () => {
                this.scale = 1.5
                this.rotate = 180
              }
            },
            // 第二段: 300-600ms
            {
              duration: 300,
              curve: Curve.EaseOut,
              event: () => {
                this.opacity = 0.5
                this.rotate = 360
              }
            },
            // 第三段: 600-900ms 恢复
            {
              duration: 300,
              curve: Curve.Linear,
              event: () => {
                this.scale = 1
                this.opacity = 1
                this.rotate = 0
              }
            }
          ])
        })
    }
  }
}
```

## 路径动画 motionPath()

```typescript
@Entry
@Component
struct PathAnimation {
  @State progress: number = 0
  
  build() {
    Column() {
      // 可视化路径（可选）
      Path()
        .commands('M100 100 Q200 50 300 100 T500 100')
        .stroke('#ccc')
        .strokeWidth(2)
        .fill('none')
      
      // 沿路径运动的元素
      Row()
        .width(30)
        .height(30)
        .backgroundColor('#FF6B6B')
        .borderRadius(15)
        .motionPath({
          path: 'M100 100 Q200 50 300 100 T500 100',
          from: this.progress,
          to: this.progress === 0 ? 1 : 0,
          rotatable: true  // 是否跟随路径旋转
        })
        .animation({ duration: 2000, curve: Curve.EaseInOut })
      
      Button('移动')
        .onClick(() => {
          this.progress = this.progress === 0 ? 1 : 0
        })
    }
  }
}
```

## 粒子动画 Particle()

```typescript
@Entry
@Component
struct ParticleDemo {
  build() {
    Stack() {
      Particle({
        particles: [{
          emitter: {
            particle: {
              type: ParticleType.IMAGE,
              config: {
                src: $r('app.media.star'),
                size: [20, 20]
              },
              count: 100,
              lifetime: 2000
            },
            emitRate: 10,
            position: [180, 400],
            shape: ParticleEmitterShape.CIRCLE
          },
          color: {
            range: [Color.Red, Color.Yellow],
            updater: {
              type: ParticleUpdater.CURVE,
              config: [{
                from: Color.Red,
                to: Color.Yellow,
                startMillis: 0,
                endMillis: 1000
              }]
            }
          },
          opacity: {
            range: [1, 0],
            updater: {
              type: ParticleUpdater.CURVE,
              config: [{
                from: 1,
                to: 0,
                startMillis: 0,
                endMillis: 2000
              }]
            }
          },
          acceleration: {
            speed: { range: [5, 10] },
            angle: { range: [0, 360] }
          }
        }]
      })
    }
  }
}
```

## 实战：点赞按钮动画

```typescript
@Entry
@Component
struct LikeButton {
  @State isLiked: boolean = false
  @State scale: number = 1
  @State heartY: number = 0
  @State heartOpacity: number = 0
  
  build() {
    Stack() {
      // 飘心
      Text('❤️')
        .fontSize(24)
        .translate({ y: this.heartY })
        .opacity(this.heartOpacity)
      
      // 点赞按钮
      Row({ space: 4 }) {
        Text(this.isLiked ? '❤️' : '🤍').fontSize(20)
        Text(this.isLiked ? '已点赞' : '点赞').fontSize(14)
      }
      .padding({ left: 12, right: 16, top: 8, bottom: 8 })
      .backgroundColor(this.isLiked ? '#FFE8E8' : '#F5F5F5')
      .borderRadius(20)
      .scale({ x: this.scale, y: this.scale })
      .onClick(() => this.handleLike())
    }
  }
  
  handleLike() {
    // 按钮缩放
    animateTo({ duration: 100, curve: Curve.Sharp }, () => {
      this.scale = 0.9
    })
    animateTo({ duration: 100, delay: 100, curve: Curve.Sharp }, () => {
      this.scale = 1
    })
    
    // 点赞时飘心
    if (!this.isLiked) {
      this.heartOpacity = 1
      this.heartY = 0
      animateTo({
        duration: 600,
        curve: Curve.EaseOut,
        onFinish: () => {
          this.heartOpacity = 0
          this.heartY = 0
        }
      }, () => {
        this.heartY = -60
        this.heartOpacity = 0
      })
    }
    
    this.isLiked = !this.isLiked
  }
}
```

## 动画选型决策树

```
需要动画？
├─ 简单属性变化 → animation()
├─ 需要回调/精确控制 → animateTo()
├─ 组件出现/消失 → transition()
├─ 页面跳转元素共享 → sharedTransition()
├─ 组件内元素共享 → geometryTransition()
├─ 多段复杂动画 → keyframeAnimateTo()
├─ 沿轨迹运动 → motionPath()
└─ 特效(粒子) → Particle()
```

## 性能优化建议

1. **使用renderGroup**：对固定内容的动画容器启用离屏缓存
2. **避免嵌套动画**：子组件不应有独立动效，统一由父组件控制
3. **控制动画元素数量**：大量元素使用LazyForEach按需创建
4. **使用合适的曲线**：Spring曲线比自定义贝塞尔性能更好
5. **避免动画期间布局变化**：使用transform而非改变width/height
