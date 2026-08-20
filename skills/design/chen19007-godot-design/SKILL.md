---
name: godot-design
description: Godot GDScript 接口设计规范与指导，强调 TDD 友好、可测试、可维护的设计原则。
install_source: official
install_method: download
skill_id: official_e7LD7Nkg
enabled_at: 1787232387859
version: 1.0.0
name_zh: Godot开发
---

# Godot 接口设计 Skill

## 概述

本 Skill 提供 Godot GDScript 接口设计的规范和指导，确保代码符合 TDD 友好、可测试、可维护的设计原则。

## 适用场景

- 设计新的游戏逻辑类
- 定义模块间接口
- 编写供测试使用的 API
- 重构现有代码结构

## Godot 类系统基础规则

### 脚本 ≠ 类

在 Godot 中，脚本不是真正的类，而是附加到引擎内置类的资源：

```gdscript
# 脚本继承 Node，成为其扩展
class_name Player extends Node

# 也可以不写 extends，隐式继承 RefCounted
class_name MathUtils
```

**关键点**：
- 脚本通过 `class_name` 注册到 ClassDB
- 无 `extends` 时隐式继承 `RefCounted`
- 只能附加到对应类型的节点

### 场景 = 类

场景在 Godot 中扮演类的角色：

```gdscript
# 场景是可复用、可实例化、可继承的节点组
# Player.tscn (场景)
# ├─ Sprite2D (子节点)
# └─ CollisionShape2D (子节点)

# Player.gd (脚本根节点)
class_name Player extends Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D
```

**场景定义的内容**：
- 节点组成
- 组织方式
- 初始化顺序
- 信号连接

## 接口设计规则

### 1. 状态查询方法（必备）

测试需要能够验证对象状态，必须提供查询方法：

```gdscript
class_name Player extends Node

var _health: int = 100
var _speed: float = 300.0
var _is_moving: bool = false

# 状态查询方法（供测试断言使用）
func get_health() -> int:
    return _health

func get_speed() -> float:
    return _speed

func is_alive() -> bool:
    return _health > 0

func is_moving() -> bool:
    return _is_moving
```

### 2. 动作方法签名

```gdscript
# 好的例子：有明确的类型注解和返回值
func move_to(target: Vector2) -> void:
    ...

func take_damage(amount: int) -> void:
    ...

func heal(amount: int) -> int:  # 返回实际恢复的血量
    ...

# 避免：缺少类型注解
func move_to(target):  # 错误
    ...

func take_damage(amount: int):  # 缺少返回类型
    ...
```

### 3. 信号定义（解耦）

使用信号进行事件通知，避免直接耦合：

```gdscript
class_name Player extends Node

# 状态变化信号
signal health_changed(new_health: int, old_health: int)
signal died()
signal revived()

# 位置变化信号
signal position_changed(new_position: Vector2)

# 使用示例
func take_damage(amount: int) -> void:
    var old_health = _health
    _health = max(0, _health - amount)
    health_changed.emit(_health, old_health)

    if _health == 0:
        died.emit()
```

### 4. 错误处理

```gdscript
class_name FileManager extends Node

# 使用 Error 枚举作为返回值
func load_file(path: String) -> Error:
    var file = FileAccess.open(path, FileAccess.READ)
    if not file:
        return FileAccess.get_open_error()
    return OK

# 使用 Result 类型模式
func save_data(data: Dictionary) -> Variant:
    # 成功返回数据，失败返回 Error 信息
    if not is_valid_path(data.path):
        return error("Invalid path")
    ...
```

### 5. 异步操作

```gdscript
class_name AsyncLoader extends Node

# 使用 async/await + Signal
signal loading_completed(resource: Resource)
signal loading_progress(progress: float)

func load_resource(path: String) -> void:
    var loader = ResourceLoader.load_threaded_request(path)
    while true:
        var status = loader.poll_status()
        if status == ResourceLoader.STATUS_LOADED:
            var resource = loader.get_resource()
            loading_completed.emit(resource)
            break
        elif status == ResourceLoader.STATUS_IN_PROGRESS:
            loading_progress.emit(loader.get_progress())
            await get_tree().process_frame
        else:
            break

# 调用示例
func _ready() -> void:
    load_resource("res://player.tscn")
    await loading_completed
```

## 设计检查清单

### 单一职责原则 (SRP)

```gdscript
# 好的例子：单一职责
class_name PlayerHealth extends Node

signal health_changed(new_health: int)

var _health: int = 100

func take_damage(amount: int) -> void:
    ...

func heal(amount: int) -> void:
    ...

# 避免：职责过多
class_name Player extends Node:
    # 血量管理
    var _health: int = 100
    # 移动控制
    var _velocity: Vector2
    # 动画管理
    var _animation: AnimationPlayer
    # 音效管理
    var _audio: AudioStreamPlayer
    # 太多职责！
```

### 类型注解完整性

```gdscript
# 变量类型注解
var health: int = 100
var speed: float = 300.0
var target: Vector2 = Vector2.ZERO

# 函数参数和返回值
func move_to(target: Vector2) -> void:
    ...

func get_damage_multiplier(attack_type: String) -> float:
    ...

# 导出变量
@export var max_health: int = 100
@export var move_speed: float = 300.0
```

### 可测试性

```gdscript
# 好的例子：依赖注入，易于测试
class_name DamageCalculator extends RefCounted

var _base_damage: float

func _init(base_damage: float = 10.0) -> void:
    _base_damage = base_damage

func calculate_damage(base: float, multiplier: float) -> float:
    return base * multiplier * _base_damage

# 测试时可以直接传入不同的 base_damage
```

### 避免 Godot 内置模式

| 场景 | 使用 | 避免 |
|-----|------|------|
| 事件通知 | Signal | 手动回调函数 |
| 节点引用 | @onready | find_node() / get_node() |
| 全局状态 | Autoload | 全局变量 |
| 编辑器配置 | @export | 硬编码 |

## 完整示例：可测试的接口设计

```gdscript
# Player.gd - 符合 TDD 设计的 Player 类
class_name Player extends CharacterBody2D

# 导出配置
@export var max_health: int = 100
@export var move_speed: float = 300.0
@export var invincibility_time: float = 0.5

# 状态变量（私有）
var _health: int = 100
var _is_invincible: bool = false
var _invincibility_timer: float = 0.0

# 状态查询方法（供测试使用）
func get_health() -> int:
    return _health

func get_max_health() -> int:
    return max_health

func is_alive() -> bool:
    return _health > 0

func is_invincible() -> bool:
    return _is_invincible

func get_velocity() -> Vector2:
    return velocity

# 动作方法
func take_damage(amount: int) -> bool:
    if _is_invincible or _health <= 0:
        return false

    _health = max(0, _health - amount)
    _start_invincibility()

    if _health == 0:
        died.emit()
    else:
        health_changed.emit(_health)

    return true

func heal(amount: int) -> int:
    var old_health = _health
    _health = min(max_health, _health + amount)
    health_changed.emit(_health)
    return _health - old_health

func move(direction: Vector2, delta: float) -> void:
    velocity = direction.normalized() * move_speed
    move_and_slide()

# 信号
signal health_changed(new_health: int)
signal died()
signal invincibility_started()
signal invincibility_ended()

# 内部方法
func _start_invincibility() -> void:
    _is_invincible = true
    _invincibility_timer = invincibility_time
    invincibility_started.emit()

func _process(delta: float) -> void:
    if _is_invincible:
        _invincibility_timer -= delta
        if _invincibility_timer <= 0:
            _is_invincible = false
            invincibility_ended.emit()
```

## 常见问题

### Q: 什么时候使用 `class_name`？

A: 当需要满足以下条件时使用：
- 其他脚本需要通过类名引用它
- 需要使用类型检查 `is`
- 需要在编辑器中快速找到它

### Q: 私有属性如何命名？

A: 使用下划线前缀：
```gdscript
var _health: int = 100
var _velocity: Vector2 = Vector2.ZERO
```

### Q: 常量如何命名？

A: 使用全大写加下划线：
```gdscript
const MAX_HEALTH := 100
const MOVE_SPEED := 300.0
const GRAVITY := 980.0
```

### Q: 何时使用 `RefCounted` 而非 `Node`？

A: 当该类不需要场景树功能时：
- 工具函数
- 数据模型
- 计算类

---

## 测试用例设计规范

设计接口时同时规划测试用例，确保接口可测试。

### 1. 等价类划分 (Equivalence Partitioning)

将输入分成有效和无效的等价类：

```gdscript
# 设计时考虑：
# - 有效类：level 1-100
# - 无效类：level < 1, level > 100

class_name Player extends Node

# 对应的测试接口
func set_level(level: int) -> bool:
    if level < 1 or level > 100:
        return false
    _level = level
    return true

func get_level() -> int:
    return _level
```

**对应的测试用例设计**：
```gdscript
# 测试代码
func test_level_valid():
    assert_true(player.set_level(50))

func test_level_below_min():
    assert_false(player.set_level(0))

func test_level_above_max():
    assert_false(player.set_level(101))
```

### 2. 边界值分析 (Boundary Value Analysis)

在边界值处设计测试用例：

```gdscript
# 设计时考虑边界：damage 的 0, 1, 99, 100
class_name DamageCalculator extends RefCounted

const MIN_DAMAGE := 0
const MAX_DAMAGE := 100

func calculate(damage: int) -> int:
    return clamp(damage, MIN_DAMAGE, MAX_DAMAGE)
```

**对应的测试用例设计**：
```gdscript
func test_damage_zero():
    assert_eq(calc.calculate(0), 0)

func test_damage_min():
    assert_eq(calc.calculate(1), 1)

func test_damage_max_minus_one():
    assert_eq(calc.calculate(99), 99)

func test_damage_max():
    assert_eq(calc.calculate(100), 100)
```

### 3. 状态转换测试 (State Transition)

设计状态查询方法支持状态测试：

```gdscript
# 设计时考虑状态：IDLE → WALKING → JUMPING → DEAD
class_name Player extends Node

var _state: String = "IDLE"

func get_state() -> String:
    return _state

func start_walk() -> void:
    _state = "WALKING"

func jump() -> void:
    _state = "JUMPING"

func land() -> void:
    _state = "IDLE"

func take_damage(amount: int) -> void:
    if amount >= _health:
        _state = "DEAD"
```

**对应的测试用例设计**：
```gdscript
func test_idle_to_walking():
    assert_eq(player.get_state(), "IDLE")
    player.start_walk()
    assert_eq(player.get_state(), "WALKING")

func test_any_state_to_dead():
    player.take_damage(1000)
    assert_eq(player.get_state(), "DEAD")
```

### 4. 决策表测试 (Decision Table)

设计接口支持多条件组合测试：

```gdscript
# 设计时考虑：is_critical, has_weapon, target_armor
class_name AttackCalculator extends RefCounted

func calculate_damage(is_critical: bool, has_weapon: bool, has_armor: bool) -> int:
    var base = 10 if has_weapon else 5
    var multiplier = 2.0 if is_critical else 1.0
    var reduction = 0.5 if has_armor else 0.0
    return int(base * multiplier * (1.0 - reduction))
```

**对应的测试用例设计**：
```gdscript
func test_critical_with_weapon_no_armor():
    assert_eq(calc.calculate_damage(true, true, false), 20)

func test_critical_with_weapon_with_armor():
    assert_eq(calc.calculate_damage(true, true, true), 10)
```

### 5. 错误场景设计

设计接口时考虑错误情况：

```gdscript
class_name FileLoader extends Node

func load_file(path: String) -> Variant:
    # 返回值设计：成功返回数据，失败返回 Error
    if not path.begins_with("res://"):
        return error("Invalid path format")

    var file = FileAccess.open(path, FileAccess.READ)
    if not file:
        return FileAccess.get_open_error()

    return file.get_as_text()

func is_valid_path(path: String) -> bool:
    return path.begins_with("res://") and FileAccess.file_exists(path)
```

**对应的测试用例设计**：
```gdscript
func test_invalid_path():
    assert_true(loader.load_file("invalid") is Error)

func test_nonexistent_file():
    var result = loader.load_file("res://nonexistent.gd")
    assert_true(result is Error)
```

### 设计检查清单

设计接口时确保：

- [ ] 定义有效的等价类范围
- [ ] 识别所有边界值
- [ ] 设计状态查询方法
- [ ] 规划状态转换路径
- [ ] 支持多条件组合测试
- [ ] 定义错误返回值类型
