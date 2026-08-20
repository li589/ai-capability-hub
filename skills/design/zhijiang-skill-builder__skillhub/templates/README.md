# 智匠：通用模板使用说明

## 这些文件是什么

本目录包含 3 个核心模板，智匠生成新专家时会自动填写它们。

| 文件 | 作用 | 谁改 |
|:--|:--|:--|
| `engine_skeleton.py` | 计算引擎骨架 | AI 自动填入你的公式；你通常不需要改 |
| `lookup_data_skeleton.py` | 查表数据结构 | AI 自动填入你的查表数据；规范更新时你维护 |
| `test_cases_skeleton.json` | 验证用例 | AI 自动填入标准算例；你核对结果 |

## AI 怎么填这些模板

智匠在 Step 2（案例验证）会做这件事：

```
复制 engine_skeleton.py  →  重命名为 engine.py
复制 lookup_data_skeleton.py →  重命名为 lookup_data.py
复制 test_cases_skeleton.json →  重命名为 test_cases.json

然后 AI 会：
1. 在 engine.py 的 TODO 区域写入你的计算公式
2. 在 lookup_data.py 的 TODO 区域写入查表数据
3. 在 test_cases.json 中写入标准算例的输入和期望输出
```

## 你需要关心什么

### 1. 核对 test_cases.json

打开 `test_cases.json`，重点看：
- `source`：算例来自哪本书、哪一页
- `params`：输入参数是否和你给的标准算例一致
- `expected`：期望结果是否和书上一样
- `tolerance_percent`：默认 3%，如果你要求更严格可以改

### 2. 本地跑通 engine.py

```bash
# 进入专家包目录
cd expert_<你的专家名>

# 安装依赖（如果没有 requirements.txt，一般只需要 Python 自带库）
python engine.py
```

如果看到 `NotImplementedError`，说明 AI 还没填好 TODO 区域，回到智匠对话里让它继续。

### 3. 验证差异 ≤ 3%

智匠会帮你跑验证。你自己也可以看输出：

```json
{
  "success": true,
  "mode": "mode_a",
  "result": {
    "K": 1.85
  }
}
```

对比 `test_cases.json` 里的 `expected.K`。如果差异 > 3%，必须回到 Step 2 调整。

## 通用部分 vs 专属部分

### 通用部分（不要改）

- `lookup_all()` 查表函数
- `build_html_report()` 报告生成
- `main()` 主入口
- 错误处理和参数校验

### 专属部分（AI 会填）

- `calc_mode_a()` / `calc_mode_b()` / `calc_mode_c()` / `calc_mode_d()`
- `LOOKUP_DATA` 里的具体表格
- `test_cases.json` 里的具体用例

## 常见错误

| 错误 | 原因 | 解决 |
|:--|:--|:--|
| `ModuleNotFoundError: No module named 'lookup_data'` | engine.py 和 lookup_data.py 不在同一文件夹 | 把它们放一起 |
| `NotImplementedError` | AI 还没填 TODO 区域 | 回到智匠对话继续 |
| `KeyError: 'xxx'` | 查表时用了不存在的键 | 检查 lookup_data.py 里的表名和键名 |
| 结果差异 > 3% | 公式理解有误或给定值被二次查表 | 回到 Step 2 检查公式链 |

## 给零基础用户的特别提醒

你不需要理解 `engine_skeleton.py` 里的每一行代码。
你只需要确认两件事：

1. `test_cases.json` 里的算例是你给的标准算例。
2. 跑出来的结果和书上的差异 ≤ 3%。

其他事情交给 AI 和部署脚本。
