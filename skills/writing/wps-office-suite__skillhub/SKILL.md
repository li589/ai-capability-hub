---
name: wps-office-suite
displayName: WPS Office 全家桶
slug: wps-office-suite
description: WPS Office 全家桶 - 四引擎（WPS/MS Office/LibreOffice/纯Python）智能识别用户已安装软件，纯Python模式支持排序/筛选/图表/公式/统计，含文档模板（代码生成）、最佳实践案例、故障排除大章（20+避坑+15 FAQ+15错误ID 统一索引）、自动重试、硬件自适应、环境自检、Skill更新提醒；v4.0新增：Word→PPT一键生成、Excel自然语言数据分析、Word合同条款审查、Excel发票OCR入账；v4.3新增：Excel深度分析（公式纠错/数据清洗/透视表/数据预测/NL2Formula）；v4.4新增：长文档排版自动化（目录/页眉页脚/标题编号/图表索引/交叉引用/格式统一）；v4.5新增：会议纪要生成（ASR转写→LLM摘要→Word）、COM健康检查（状态检测+残留进程+自动释放）；v4.6新增：Excel智能分析统一入口（6命令合并）、数据图表生成器（自动选图+生成）、文档翻译增强版（Word/Excel/PPT多格式翻译）；v4.7新增：公式解释器（反向NL2Formula，Excel公式→自然语言）、Markdown→Word/PPT转换、长文档排版统一入口（long-document --action）、长文档排版性能优化（分批处理+单次保存+进度回调）
version: 4.7.0
category: 办公协作与生产力工具
platforms:
  - windows
  - macos
  - linux
permission:
  - 文件系统访问
  - 应用程序控制（WPS / MS Office / LibreOffice / 纯Python）
dependency:
  - "Python 3.8+"
  - "pywin32（Windows COM 模式，可选）"
  - "python-docx / openpyxl / python-pptx（纯Python模式，可选）"
  - "WPS Office 2019+ 或 Microsoft Office（可选，增强模式）"
  - "LibreOffice（可选，跨平台兜底转换）"
pricing: 免费
tags:
  - WPS
  - MS-Office
  - LibreOffice
  - Office
  - Word
  - Excel
  - PPT
  - 四引擎
  - 智能识别
  - 纯Python
  - 跨平台
  - 自动重试
  - 硬件自适应
  - 自动化
  - 办公提效
  - AI助手
  - 文档模板
  - 最佳实践
  - 避坑指南
  建议反馈邮箱: njskills@agent.qq.com
disable-model-invocation: true
---

# WPS Office 全家桶 v4.7.0 ✅

> 🏗️ **四引擎智能识别**：自动检测用户电脑已安装的软件，按 WPS → MS Office → LibreOffice → 纯Python 顺序选择最合适的引擎
> ✨ **纯Python模式增强**：排序、筛选、图表、公式、统计 — 跨平台全部支持
> 🔄 **自动重试**：WPS 卡住时自动重试 3 次，不用手动重启
> ⚡ **硬件自适应**：自动检测 CPU 内存，动态调整超时和线程，不拖累电脑
> 📚 **文档模板 + 最佳实践 + 故障排除**：代码生成3个即用模板 + 10个最佳实践案例 + 统一故障排除大章
> 📬 **Skill 更新提醒**：自动检查新版本，7天提醒一次，保持最新
> 🆕 **文件大小明确限制**：单文件 < 50MB 直接处理，> 50MB 有分片建议
> 🔬 **Excel 智能分析 v4.6**：6命令合并为 1 个统一入口（--action 参数路由）
> 📊 **数据图表生成器 v4.6**：基于数据特征自动推荐图表类型 + 生成图表嵌入 Excel
> 🌐 **文档翻译 v4.6**：Word/Excel/PPT 专业翻译（支持多模型降级）
> 🎙️ **会议纪要 v4.5**：音频 → ASR 转写 → LLM 摘要 → Word（支持降级链）
> 🏥 **COM 健康检查 v4.5**：WPS/MS Office 状态检测 + 残留进程清理
> 🧮 **公式解释器 v4.7**：Excel 公式 → 自然语言解释（反向 NL2Formula，纯本地实现）
> 📝 **Markdown 转换 v4.7**：MD → Word/PPT（保留标题层级，纯本地实现）
> 📑 **长文档排版 v4.7**：统一入口 long-document --action（8命令合并），性能优化（分批+单次保存+进度回调）
> 📧 **建议反馈**：有更好建议？邮箱：[njskills@agent.qq.com](mailto:njskills@agent.qq.com)

---

## 🚀 分钟上手

### 1. 检查环境

```bash
python scripts/wps_test.py
```

### 2. 查看当前引擎 + 硬件

```bash
python scripts/wps_excel.py engine-info
```

### 3. 创建文件

```bash
python scripts/wps_word.py create --title "测试文档"
python scripts/wps_excel.py create --name "预算表" --sheets "收入,支出"
python scripts/wps_ppt.py create --title "推广方案"
```

### 4. 检查更新

```bash
python scripts/wps_excel.py check-update
```

### 5. 生成模板（代码生成，无二进制文件）

```bash
python templates/generate_templates.py --dir ./output
```

---

## ⚡ 硬件自适应

| 硬件等级 | CPU / 内存 | 超时 | 并行数 | 适用场景 |
|---------|-----------|------|-------|---------|
| 高性能 | 8核+ / 16G+ | 30s | 8线程 | 批量处理、大文件 |
| 中等 | 4核+ / 8G+ | 60s | 4线程 | 日常办公 |
| 低性能 | 2核 / 4G | 120s | 1线程 | 轻量任务 |

---

## 🔧 功能矩阵

| 功能 | WPS | MS Office | LibreOffice | 纯Python |
|------|-----|-----------|-------------|----------|
| **创建/编辑/格式 — Word** | ✅ | ✅ | ✅（回退） | ✅ |
| **表格/图片/目录 — Word** | ✅ | ✅ | ❌ | ✅ |
| **创建/编辑/公式/图表 — Excel** | ✅ | ✅（回退） | ✅（回退） | ✅ |
| **排序/筛选/统计 — Excel** | ✅ | ✅（回退） | ✅（回避） | ✅ |
| **幻灯片/主题/插入 — PPT** | ✅ | ❌ | ❌ | ❌ |
| **PPT 创建/多页 — PPT** | ✅ | ✅ | ✅（回退） | ✅ |

> ✅（回退）= 原生引擎不支持时，自动回退到纯 Python 实现

---

## 📂 文档模板（代码生成，零二进制文件）

| 模板 | 用途 | 生成命令 |
|------|------|---------|
| 工作报告 | 周报/月报/汇报 | `python templates/generate_templates.py --dir ./output` |
| 月度预算 | 收入/支出/汇总 | 同上 |
| 商务PPT | 项目汇报/方案 | 同上 |

> 模板通过纯 Python 代码动态生成，无需分发二进制文件。首次运行需安装 `python-docx`、`openpyxl`、`python-pptx`。

---

## ⚠️ 文件限制速查

| 限制项 | 阈值建议 | 超出后处理方式 |
|--------|---------|--------------|
| **单文件大小** | < 50MB 直接处理 | > 50MB 先分片（拆 Sheet/Section） |
| **批量文件数** | 建议 ≤ 50 个/批 | 超过时分批调用 |
| **Excel 行数** | < 100,000 行 | 超过时分 Sheet 存储 |
| **PPT 页数** | < 100 页 | 拆分为多个文件 |
| **并发操作** | 同一引擎 1 个实例 | 串行等待，避免并行写同一文件 |
| **文件名长度** | < 200 字符 | 过短路径避免中文 |

---

## 🔧 故障排除大章（v4.5 合并，统一索引）

### 统一索引表

| 类型 | 问题 | 快速解决 |
|------|------|---------|
| 🚫 避坑 | WPS 未安装就调用 | 运行 engine-info 检查引擎 |
| 🚫 避坑 | 公式写入显示 #NAME? | 按 Ctrl+Alt+F9 重新计算 |
| 🚫 避坑 | 中文路径编码错误 | 改用英文路径或 raw string |
| 🚫 避坑 | 大文件内存溢出 | >50MB 分片处理 |
| 🚫 避坑 | WPS 卡住无响应 | 已自动重试3次，不行就任务管理器结束 |
| 🚫 避坑 | COM 对象残留 | Worker 自动释放，或运行 com-health release-all |
| 🚫 避坑 | PPT 添加幻灯片失败 | 仅 WPS 支持，或一次性指定 slides_content |
| 🚫 避坑 | openpyxl 读取公式为 None | 先 WPS 打开保存一次 |
| 🚫 避坑 | 排序/筛选/图表错乱 | 确保第一行是表头，列名完全一致 |
| 🚫 避坑 | 筛选返回空结果 | 数值 value 必须是字符串 |
| ⚠️ FAQ | 该选哪个引擎？ | 自动检测，无需手动选择 |
| ⚠️ FAQ | WPS 版本有要求？ | 2019+ 或 WPS 365，安装后必须重启 |
| ⚠️ FAQ | 纯Python vs WPS 区别？ | 公式计算/图表/添加幻灯片不同 |
| ⚠️ FAQ | 文件太大怎么办？ | <50MB 直接处理，>50MB 分片 |
| ⚠️ FAQ | Linux 能用吗？ | 能，安装 LibreOffice |
| ⚠️ FAQ | WPS 卡住怎么办？ | 自动重试3次，不行结束进程 |
| ⚠️ FAQ | 纯Python 安装依赖？ | pip install python-docx openpyxl python-pptx |
| ⚠️ FAQ | 模板如何获取？ | 代码生成，运行 generate_templates.py |
| ⚠️ FAQ | 批量转换格式？ | format_converter.py batch |
| ⚠️ FAQ | 多 Sheet 处理？ | 逐 Sheet 调用或 add-sheet |
| ⚠️ FAQ | 排序/筛选总失败？ | 确保 openpyxl 安装、文件未占用 |
| ⚠️ FAQ | 如何提交反馈？ | wps_feedback.py email 或发邮件 |
| ⚠️ FAQ | 公式何时计算？ | 打开文件时由 Excel/WPS 计算 |
| ⚠️ FAQ | 文件被占用怎么办？ | 关闭程序，等待3-5秒重试 |
| ⚠️ FAQ | 纯Python 不可用功能？ | 添加幻灯片/插入/主题/VBA/条件格式 |
| 🚨 错误ID | E001 WPS 未安装或 COM 注册失败 | 安装 WPS 后重启电脑 |
| 🚨 错误ID | E002 python-docx 未安装 | pip install python-docx openpyxl python-pptx |
| 🚨 错误ID | E003 文件路径不存在 | 改用英文路径或以管理员运行 |
| 🚨 错误ID | E004 格式转换失败 | 安装 WPS 或 LibreOffice |
| 🚨 错误ID | E005 需要 WPS 模式 | 安装 WPS 或改用纯Python模式 |
| 🚨 错误ID | E006 WPS 卡住无响应 | 任务管理器结束进程；更新到最新版 |
| 🚨 错误ID | E007 权限不足 | 以管理员运行；检查文件只读属性 |
| 🚨 错误ID | E008 pywin32 导入失败 | pip uninstall pywin32 && pip install pywin32 |
| 🚨 错误ID | E009 Python 版本过低 | 升级到 Python 3.8+ |
| 🚨 错误ID | E010 引擎不支持此功能 | 安装 WPS 或改用 info 查看能力矩阵 |
| 🚨 错误ID | E011 LibreOffice 未安装 | 下载 LibreOffice 并添加到 PATH |
| 🚨 错误ID | E012 LibreOffice 转换失败 | 检查源文件是否损坏；避免中文路径 |
| 🚨 错误ID | E013 文件不存在 | 确认路径正确；未被删除或移动 |
| 🚨 错误ID | E014 未知运行时错误 | 运行环境自检 wps_test.py；联系反馈 |
| 🚨 错误ID | E015 不支持的操作或格式 | 输出格式改为 pdf/txt/html |

---

## 🚫 避坑详解（20+ 条）

### 🥇 高频问题（TOP 10）

#### ❌ 坑 1：WPS 没安装就调用 WPS 功能

```
症状：win32com.com_error 或 "WPS 未安装"
排查：
  1. 运行 python scripts/wps_excel.py engine-info 检查当前引擎
  2. 如果显示 PURE 或 LIBREOFFICE，说明 WPS 不可用
  3. 安装 WPS Office 2019+ 后重启电脑
```

#### ❌ 坑 2：纯 Python 模式下写公式，打开 Excel 显示 #NAME?

```
症状：公式写入后打开显示 #NAME? 错误
排查：
  1. openpyxl 写的是公式字符串，打开时需 Excel/WPS 重新计算
  2. 解决：按 Ctrl+Alt+F9 强制重新计算
  3. 或切换到 WPS 模式自动计算
```

#### ❌ 坑 3：中文路径编码错误

```
症状：UnicodeEncodeError 或 FileNotFoundError
排查：
  1. 避免中文路径：D:\docs\report.docx ✅
  2. 路径加引号："D:\中文\报告.docx" ✅
  3. 使用 raw string：r"D:\中文\报告.docx" ✅
```

#### ❌ 坑 4：大文件内存溢出

```
症状：MemoryError 或程序卡死
排查：
  1. 先运行 python scripts/wps_word.py info --file big.docx 查看大小
  2. < 50MB 直接处理
  3. > 50MB 拆分处理：分 Sheet/Section
  4. 硬件自适应会自动延长超时
```

#### ❌ 坑 5：WPS 卡住无响应

```
症状：操作超时（30s/60s/120s）
排查：
  1. Skill 已自动重试 3 次（等 1s → 2s → 4s）
  2. 仍失败则：任务管理器 → 结束 WPS 进程
  3. 反复出现：pip install --upgrade pywin32
```

#### ❌ 坑 6：COM 对象残留

```
症状：第二次调用报 "RPC 服务器不可用"
排查：
  1. Worker 已内置自动释放（每次操作后调用 release_wps）
  2. 手动清理：任务管理器 → 结束 kwps.exe
  3. 避免频繁创建/销毁 Worker，使用 stdin/stdout 协议
```

#### ❌ 坑 7：PPT 添加幻灯片失败

```
症状：纯Python模式不支持添加幻灯片
排查：
  1. 添加幻灯片、插入内容、主题应用仅 WPS 支持
  2. 替代方案：用 pure_create_ppt 创建时指定 slides_content 一次生成多页
  3. 或安装 WPS Office
```

#### ❌ 坑 8：openpyxl 读取公式为 None

```
症状：读取含公式的单元格返回 None
排查：
  1. openpyxl 默认读取缓存值（data_only=True）
  2. 如果从未在 Excel 中打开计算，缓存值为 None
  3. 解决：先在 WPS 中打开保存一次，或改用公式计算
```

#### ❌ 坑 9：sort 命令排序错乱

```
症状：排序结果不对
排查：
  1. 确保第一行是表头（不参与排序）
  2. 列名参数 column 需与表头完全一致（区分大小写）
  3. 多列排序时注意优先级顺序
```

#### ❌ 坑 10：filter 筛选返回空结果

```
症状：筛选条件正确但返回空
排查：
  1. 条件 column 值需与表头完全一致
  2. 数值比较时 value 必须是字符串（"--value": "5000"）
  3. 检查是否有隐藏空格，使用 trim
```

### 🥈 中频问题

#### ⚠️ 坑 11：LibreOffice 转换失败
```
症状：Word 转 PDF 报错
排查：先检查 LibreOffice 是否加入 PATH；避免中文路径；确保文件未损坏
```

#### ⚠️ 坑 12：generate_templates.py 报 ImportError
```
症状：缺少 python-docx / openpyxl / python-pptx
排查：pip install python-docx openpyxl python-pptx
```

#### ⚠️ 坑 13：_worker 启颈慢
```
症状：首次调用需2-3秒
排查：正常！Worker 启动时检测硬件和引擎
```

#### ⚠️ 坑 14：MS Office 模式下功能缺失
```
症状：纯Python能做的MS Office不行
排查：MS Office COM 接口并非全功能，部分自动回退到纯Python
```

#### ⚠️ 坑 15：多 Sheet 引用公式失效
```
症状：=SUM(1月:12月!B2) 不计算
排查：openpyxl 写公式不支持 3D 引用，改用 stats 命令或逐 Sheet 运算
```

### 🥉 低频但重要

#### ⚡ 坑 16：macOS 上 WPS 部分功能不可用
```
症状：Mac 版 WPS COM 不支持某些操作
排查：回退到纯Python模式（WPS_ENGINE=PURE）
```

#### ⚡ 坑 17：xlsm 文件宏丢失
```
症状：保存后宏功能失效
排查：openpyxl 不支持宏，xlsm 文件请用 WPS/MS Office 模式
```

#### ⚡ 坑 18：批量操作时 WPS 弹出对话框
```
症状：WPS 弹窗阻断自动化
排查：弹窗需手动点击；建议在无人值守时关闭 WPS 弹窗
```

#### ⚡ 坑 19：文件被占用
```
症状：PermissionError
排查：关闭占用文件的程序（WPS/Excel/Word），等待 3-5 秒后重试
```

#### ⚡ 坑 20：Windows 长路径限制
```
症状：Windows 默认最大路径 260 字符
排查：启用 Windows 长路径支持，或使用短路径
```

---

## 📋 常见问题 FAQ（Q&A）

### Q1：我应该选择哪个引擎？

**不用选！Skill 自动检测**。运行 `python scripts/wps_excel.py engine-info` 查看。如果强行切换，可以设置环境变量 `WPS_ENGINE=PURE` 强制使用纯 Python。

### Q2：WPS 版本有要求吗？

- WPS Office 2019+ 或 WPS 365
- 安装后**必须重启电脑**
- 32/64 位均可

### Q3：纯 Python 模式和 WPS 模式有什么区别？

| | WPS 模式 | 纯 Python 模式 |
|--|---------|-------------|
| 公式计算 | ✅ 自动计算 | ⚠️ 写入公式，打开时计算 |
| 图表 | ✅ 实时预览 | ✅ 嵌入到 Excel |
| 添加幻灯片 | ✅ 支持 | ❌ 不支持 |
| 内存占用 | 高（几百 MB） | 低（几十 MB） |
| 速度 | 快（WPS 优化） | 较慢 |

### Q4：文件太大怎么办？

> Skill 硬件自适应会自动延长超时（最高 5 倍）。
> 建议：< 50MB 直接处理；> 50MB 先分片处理（拆分 Sheet/Section）。
> 批量操作时单次建议 ≤ 50 个文件。

### Q5：Linux 上能用吗？

> ✅ 能用！安装 LibreOffice 即可：
> ```bash
> sudo apt install libreoffice  # Ubuntu/Debian
> ```
> 支持格式转换（Word/Excel/PPT → PDF）；
> 公式、排序、筛选、图表也能用纯 Python 模式。

### Q6：WPS 卡住怎么办？

> Skill 会自动重试 3 次。如果仍然失败：
> 1. 打开任务管理器 → 结束 WPS 进程
> 2. 重新运行命令
> 3. 如果反复出现，尝试：`pip install --upgrade pywin32`

### Q7：纯 Python 模式如何安装依赖？

```bash
pip install python-docx openpyxl python-pptx
```

### Q8：模板文件在哪里？如何获取？

> 模板通过代码生成，不包含二进制文件。安装依赖后运行：
> ```bash
> python templates/generate_templates.py --dir ./output
> ```
> 即可生成 3 个模板：report_template.docx、budget_template.xlsx、business_ppt_template.pptx

### Q9：如何批量转换格式？

```bash
# 单个文件
python scripts/wps_word.py export --file report.docx --format pdf

# 批量转换（使用 format_converter.py）
python scripts/format_converter.py batch --input-dir ./docs --input-format docx --output-format pdf
```

### Q10：如何同时处理多个 Sheet？

```bash
# 查看所有 Sheet
python scripts/wps_excel.py info --file Sales.xlsx

# 为每个 Sheet 添加数据（逐 Sheet 调用）
python scripts/wps_excel.py input --file Sales.xlsx --sheet Q1 --data '[["A",100]]'
python scripts/wps_excel.py input --file Sales.xlsx --sheet Q2 --data '[["B",200]]'

# 添加新 Sheet
python scripts/wps_excel.py add-sheet --file Sales.xlsx --sheet Q4 --headers '["产品","价格"]' --data '[["X",300]]'
```

### Q11：排序/筛选/图表操作总是失败？

> 纯 Python 模式下这些功能 100% 支持。
> 1. 确保已安装：`pip install openpyxl`
> 2. 文件不能正在被占用（关闭 WPS/Excel）
> 3. 第一行必须是表头（列名）
> 4. 列名参数需与表头完全一致

### Q12：如何提交反馈？

```bash
python scripts/wps_feedback.py email  # 打开邮件客户端（自动附带系统信息）
```

或直接发邮件到：**njskills@agent.qq.com**

### Q13：纯 Python 模式下公式何时计算？

> openpyxl 写入公式字符串，**打开文件时**由 Excel/WPS 计算。
> 如果需要立即计算，请使用 WPS 模式或 MS Office 模式。

### Q14：文件被占用怎么办？

> 关闭占用文件的程序（WPS/Excel/Word），等待 3-5 秒后重试。
> 或使用自动重试（Skill 已内置 3 次重试）。

### Q15：哪些功能在纯 Python 模式下不可用？

> - 添加幻灯片（add-slide）
> - 幻灯片插入内容（insert）
> - 幻灯片主题（theme）
> - VBA/宏操作
> - 条件格式
> 
> 替代方案：安装 WPS Office 或 MS Office 获取完整功能。

---

## 🏆 最佳实践（10 个案例）

### BP-1：大文件处理策略

```
问题：50MB 的 Word 文档操作很慢
策略：
  1. 先运行 python scripts/wps_word.py info --file big.docx 查看大小
  2. 如果 > 50MB，分片处理
  3. 使用纯 Python 模式读取内容
  4. 避免频繁保存（每次保存触发全量写入）
```

### BP-2：周报自动化

```
问题：每周重复做相同格式的周报
策略：
  1. 生成模板：python templates/generate_templates.py --dir ./output
  2. 复制模板：copy output\report_template.docx 本周周报.docx
  3. 用 edit 命令追加内容
  4. 用 format 命令设置格式
  5. 用 export 生成 PDF
```

### BP-3：预算跟踪自动化

```
问题：每月记录收入支出，手动计算汇总
策略：
  1. 生成预算模板：python templates/generate_templates.py --dir ./output
  2. 每月用 input 命令录入数据
  3. 汇总 Sheet 含公式自动计算
  4. 用 stats 命令验证数据
```

### BP-4：商务PPT快速制作

```
问题：需要做项目汇报 PPT
策略：
  1. 生成模板：python templates/generate_templates.py --dir ./output
  2. 复制模板并修改标题
  3. 如有多页内容，创建时指定 --slides 参数
```

### BP-5：数据报表自动化

```
问题：每周重复做相同格式的报表
策略：
  1. 创建模板文件（含公式和图表位置）
  2. 每周用 input 命令录入新数据
  3. 公式和图表自动更新
  4. 导出 PDF 分发
```

### BP-6：多 Sheet 数据汇总

```
问题：12 个月的数据在 12 个 Sheet，需要年度汇总
策略：
  1. 用 add-sheet 创建"年度汇总"Sheet
  2. 用 stats 命令逐 Sheet 验证汇总结果
```

### BP-7：条件筛选导出

```
问题：从 1000 条记录中筛出"销售额>5000 且 地区=华东"
策略：
  python scripts/wps_excel.py filter --file data.xlsx --sheet Q1 \
    --conditions '[{"column":"销售额","op":">","value":"5000"},{"column":"地区","op":"=","value":"华东"}]' \
    --logic AND
  ✅ 筛出符合条件的记录
```

### BP-8：批量文件重命名

```
问题：20 个文件需要统一命名规范
策略：
  1. 用 document_manager.py 列出所有文件
  2. 批量重命名（加日期前缀）
  3. 用 format_converter.py 批量转换格式
```

### BP-9：跨平台文档转换

```
问题：Linux 服务器上需要把 Word 转 PDF
策略：
  1. 安装 LibreOffice：sudo apt install libreoffice
  2. 引擎自动检测为 LIBREOFFICE
  3. 直接 export --format pdf
```

### BP-10：定时自动化

```
问题：每天凌晨自动生成报表
策略：
  1. 编写自动化脚本（调用 wps_excel.py + wps_word.py）
  2. 使用 WorkBuddy automation 定时执行
  3. 输出到指定目录
```

---

## 🚨 错误速查手册 v3.1（15个错误ID）

### E001-E010：用户可自助解决

| ID | 错误 | 解决 |
|----|------|------|
| E001 | WPS 未安装或 COM 注册失败 | 安装 WPS 后重启电脑 |
| E002 | python-docx 未安装 | `pip install python-docx openpyxl python-pptx` |
| E003 | 文件路径不存在或无法访问 | 改用英文路径或以管理员运行 |
| E004 | 格式转换失败（纯Python不支持） | 安装 WPS 或 LibreOffice |
| E005 | 排序/筛选/图表需要 WPS 模式 | 安装 WPS 或改用纯Python模式 |
| E006 | WPS/LibreOffice 卡住无响应 | 任务管理器结束进程；更新到最新版 |
| E007 | 权限不足 | 或以管理员运行；检查文件只读属性 |
| E008 | pywin32 导入失败 | `pip uninstall pywin32 && pip install pywin32` |
| E009 | Python 版本过低 | 升级到 Python 3.8+ |
| E010 | 当前引擎不支持此功能 | 安装 WPS 或改用 info 查看能力矩阵 |

### E011-E015：需要进一步排查

| ID | 错误 | 解决 |
|----|------|------|
| E011 | LibreOffice 未安装 | 下载 LibreOffice 并添加到 PATH |
| E012 | LibreOffice 转换失败 | 检查源文件是否损坏；避免中文路径 |
| E013 | 文件不存在 | 确认路径正确；未被删除或移动 |
| E014 | 未知运行时错误 | 运行环境自检 `wps_test.py`；联系反馈 |
| E015 | 不支持的操作或格式 | 输出格式改为 pdf/txt/html |

---

## ⚠️ 能力边界说明

| 限制项 | 说明 | 解决方案 |
|--------|------|---------|
| **文件大小** | 单文件 < 50MB 直接处理 | 大文件先分片处理（硬件自适应自动延长超时） |
| **批量文件数** | 建议 ≤ 50 个/批 | 超过时分批调用 |
| **复杂度** | 透视表/VBA/ActiveX 不支持 | 使用 pandas 或手动处理 |
| **网络文件** | 不支持 HTTP/URL 下载 | 先手动下载到本地，再调用 Skill |
| **并发限制** | 同一时间只能操作同一引擎的一个实例 | 等待上次操作完成再发起 |
| **中文名文件路径** | 建议改用英文路径 | 路径中避免中文和特殊字符 |
| **实时协作** | 不支持多人同时编辑同一文件 | 通过手动分发和合并 |

---

## 🔗 CLI 参数速查

### Word

```bash
python scripts/wps_word.py create --title "report" --body "正文内容"
python scripts/wps_word.py edit --file "report.docx" --text "新增内容"
python scripts/wps_word.py format --file "report.docx" --font "微软雅黑" --size 14 --align center --bold --first-indent 0.74
python scripts/wps_word.py export --file "report.docx" --format pdf
python scripts/wps_word.py review --file "合同.docx" --output "合同_审查版.docx"
python scripts/wps_word.py info --file "report.docx"
python scripts/wps_word.py engine-info
python scripts/wps_word.py md-convert --file "README.md" --format docx --output "文档.docx"
python scripts/wps_word.py md-convert --file "README.md" --format pptx --output "演示.pptx"
python scripts/wps_word.py long-document --file "report.docx" --action all --preset thesis
```

### Excel

```bash
python scripts/wps_excel.py create --name "Sales" --sheets "Q1,Q2,Q3"
python scripts/wps_excel.py input --file "Sales.xlsx" --sheet "Q1" --data '[["A",100]]'
python scripts/wps_excel.py formula --file "Sales.xlsx" --sheet "Q1" --cell "C1" --formula "=SUM(A1:B1)"
python scripts/wps_excel.py chart --file "Sales.xlsx" --sheet "Q1" --type bar --data "A1:B10" --title "销售趋势"
python scripts/wps_excel.py sort --file "Sales.xlsx" --sheet "Q1" --sorts '[{"column":"Price","ascending":false}]'
python scripts/wps_excel.py filter --file "Sales.xlsx" --sheet "Q1" --conditions '[{"column":"Price","op":">","value":"50"}]' --logic AND
python scripts/wps_excel.py add-sheet --file "Sales.xlsx" --sheet "Q4" --headers '["Product","Price"]' --data '[["X",300]]'
python scripts/wps_excel.py nl-analyze --file "Sales.xlsx" --query "按月份统计销售额并画出趋势图"
python scripts/wps_excel.py invoice --input "发票.pdf" --output "进账台账.xlsx"
python scripts/wps_excel.py stats --file "Sales.xlsx" --sheet "Q1" --column "B" --type SUM
python scripts/wps_excel.py info --file "Sales.xlsx"
python scripts/wps_excel.py engine-info
python scripts/wps_excel.py check-update
python scripts/wps_excel.py formula-explain --formula "=SUM(A1:A10)"
python scripts/wps_excel.py formula-explain --file "data.xlsx" --cell "B2"
python scripts/wps_excel.py formula-explain --file "data.xlsx" --sheet "Sheet1"
```

### PPT

```bash
python scripts/wps_ppt.py create --title "Pitch"
python scripts/wps_ppt.py add-slide --file "Pitch.pptx" --title "Intro"
python scripts/wps_ppt.py insert --file "Pitch.pptx" --slide 2 --content "Key points"
python scripts/wps_ppt.py theme --file "Pitch.pptx" --name business_blue
python scripts/wps_ppt.py export --file "Pitch.pptx" --format pdf
python scripts/wps_ppt.py docx-to-ppt --input 报告.docx --output 演示.pptx --title "项目汇报" --theme business
python scripts/wps_ppt.py info --file "Pitch.pptx"
python scripts/wps_ppt.py engine-info
```

### 🆕 v4.0 新命令（详见下方各组件）

| 功能 | 命令 |
|------|------|
| Word→PPT | `python scripts/wps_ppt.py docx-to-ppt --input report.docx --output ppt.pptx` |
| NL分析 | `python scripts/wps_excel.py nl-analyze --file data.xlsx --query "按月份统计销售额画趋势图"` |
| 合同审查 | `python scripts/wps_word.py review --file contract.docx --output 审查版.docx` |
| 发票OCR | `python scripts/wps_excel.py invoice --input 发票.pdf --output 入账台账.xlsx` |
| 公式解释器 | `python scripts/wps_excel.py formula-explain --formula "=SUM(A1:A10)"` |
| MD→Word/PPT | `python scripts/wps_word.py md-convert --file README.md --format docx` |
| 长文档排版 | `python scripts/wps_word.py long-document --file report.docx --action all` |

### 🆕 v4.3 Excel 深度分析命令

```bash
python scripts/excel_analyzer.py profile --file data.xlsx --sheet Sheet1
python scripts/excel_analyzer.py fix-formulas --file data.xlsx --sheet Sheet1
python scripts/excel_analyzer.py pivot --file data.xlsx --sheet Sheet1
python scripts/excel_analyzer.py predict --file data.xlsx --sheet Sheet1 --column 销售额 --method auto --steps 3
python scripts/excel_analyzer.py nl2formula --query "同比增长率"
python scripts/excel_analyzer.py clean --file data.xlsx --sheet Sheet1
python scripts/excel_analyzer.py hardware
```

### 🆕 v4.4 长文档排版命令（已升级为 v4.7 统一入口）

> v4.7 起，长文档排版 8 个命令合并为 `wps_word.py long-document --action` 统一入口，降低记忆成本。

```bash
# 新统一入口（推荐）
python scripts/wps_word.py long-document --file report.docx --action all --preset thesis

# 旧命令仍可通过 long_document.py 调用（兼容）
python scripts/long_document.py all --file report.docx --preset thesis --output 排版后.docx
```

### 🆕 v4.5 会议纪要 + COM 健康命令

```bash
# 会议纪要生成
python scripts/meeting_minutes.py check                    # 检查可用 ASR 引擎
python scripts/meeting_minutes.py transcribe --file audio.wav --method auto
python scripts/meeting_minutes.py generate --file audio.wav --output 纪要.docx
python scripts/meeting_minutes.py batch --input-dir ./audio --output-dir ./docs

# COM 健康检查
python scripts/com_health.py wps-check                     # WPS COM 状态
python scripts/com_health.py ms-check                     # MS Office COM 状态
python scripts/com_health.py residuals                    # 检测残留进程
python scripts/com_health.py release-all --force           # 强制清理所有
python scripts/com_health.py full-check --json             # 完整健康报告

# 通过 wps_word.py 调用
python scripts/wps_word.py meeting-minutes --file audio.wav --output 纪要.docx
python scripts/wps_word.py com-health --check full
```

### 🆕 v4.6 Excel 智能分析 + 数据图表 + 文档翻译

```bash
# Excel 智能分析（6 命令合并为 1 个 --action 路由）
python scripts/wps_excel.py excel-smart --file data.xlsx --action profile
python scripts/wps_excel.py excel-smart --file data.xlsx --action fix-formulas
python scripts/wps_excel.py excel-smart --file data.xlsx --action pivot
python scripts/wps_excel.py excel-smart --file data.xlsx --action predict --column 销售额 --method auto --steps 3
python scripts/wps_excel.py excel-smart --file data.xlsx --action nl2formula --query "同比增长率"
python scripts/wps_excel.py excel-smart --file data.xlsx --action clean
python scripts/wps_excel.py excel-smart --file data.xlsx --action hardware

# 数据图表生成器
python scripts/wps_excel.py chart-gen --file data.xlsx --action auto        # 一键分析+推荐+生成
python scripts/wps_excel.py chart-gen --file data.xlsx --action analyze      # 仅分析数据特征
python scripts/wps_excel.py chart-gen --file data.xlsx --action recommend    # 仅推荐图表类型
python scripts/wps_excel.py chart-gen --file data.xlsx --action generate --type line  # 生成指定图表

# 文档翻译
python scripts/wps_word.py translate --file report.docx --output 报告_zh.docx --source en --target zh
python scripts/wps_word.py translate --input-dir ./docs --output-dir ./translated --source en --target zh
python scripts/document_translator.py translate --file report.docx --output 报告_zh.docx
python scripts/document_translator.py batch --input-dir ./docs --output-dir ./translated
python scripts/document_translator.py check                                  # 检查可用翻译引擎
```

### 🆕 v4.7 公式解释器 + Markdown 转换 + 长文档统一入口

```bash
# 公式解释器（反向 NL2Formula，纯本地实现）
python scripts/wps_excel.py formula-explain --formula "=SUM(A1:A10)"
python scripts/wps_excel.py formula-explain --file data.xlsx --cell B2
python scripts/wps_excel.py formula-explain --file data.xlsx --sheet Sheet1

# Markdown → Word/PPT
python scripts/wps_word.py md-convert --file README.md --format docx --output 文档.docx
python scripts/wps_word.py md-convert --file README.md --format pptx --output 演示.pptx
python scripts/wps_word.py md-convert --dir ./docs --format docx --output-dir ./output

# 长文档排版统一入口（8 命令合并为 1 个 --action 路由）
python scripts/wps_word.py long-document --file report.docx --action analyze
python scripts/wps_word.py long-document --file report.docx --action toc --max-level 3 --insert
python scripts/wps_word.py long-document --file report.docx --action header --chapter-in-header --page-number
python scripts/wps_word.py long-document --file report.docx --action numbering --style arabic --max-level 4
python scripts/wps_word.py long-document --file report.docx --action fig-index --insert
python scripts/wps_word.py long-document --file report.docx --action xref
python scripts/wps_word.py long-document --file report.docx --action format --preset thesis
python scripts/wps_word.py long-document --file report.docx --action all --preset thesis --output 排版后.docx
python scripts/wps_word.py long-document --file report.docx --action preview --preset thesis
```

### 其他工具

```bash
python scripts/wps_test.py                    # 环境自检（人类可读）
python scripts/wps_test.py --json             # 环境自检（JSON 格式）
python scripts/wps_feedback.py page           # 打开反馈页面
python scripts/wps_feedback.py email          # 打开邮件客户端
python scripts/wps_update.py --force          # 强制检查更新
python scripts/wps_toc.py insert --file "report.docx"  # 插入目录
python scripts/format_converter.py batch --input-dir "D:\Reports" --input-format docx --output-format pdf  # 批量转换
python templates/generate_templates.py --dir ./output  # 生成模板
```

---

## 📊 版本兼容矩阵

| Python | WPS Office | LibreOffice | Windows | macOS | Linux | 状态 |
|--------|-----------|-------------|---------|-------|-------|------|
| 3.8+ | 2019+ | - | ✅ | ⚠️ | ❌ | 基础 |
| 3.8+ | 365 | - | ✅ | ✅ | ❌ | 最佳 |
| 3.8+ | - | 7.0+ | ✅ | ✅ | ✅ | 跨平台推荐 |
| 3.8+ | - | - | ✅ | ✅ | ✅ | 纯Python |

> ⚠️ = 部分功能受限（纯Python模式），❌ = 对应引擎不可用

---

## ⚠️ 安全须知

**✅ 五道防线保障安全**：
1. **引擎自检**：启动时自动检测可用引擎，崩溃自动重启
2. **路径校验**：`safe_path()` 全面校验，拒绝非法路径和特殊字符
3. **错误中文化**：所有错误 ID 提供详细中文说明和操作步骤
4. **数据零上传**：所有处理在本地完成，不上传任何内容到互联网
5. **显式 Opt-in**（v4.6.1 引入）：外部服务（ASR/LLM）仅在用户显式指定 method 时调用，auto 模式仅使用本地引擎

**📝 注意事项**：
- 批量操作时，桌面会创建 `WPS_Backup` 文件夹保存副本
- macOS 上 WPS 不支持所有功能
- 纯 Python 模式下格式设置有限，复杂排版建议安装 WPS
- 所有文件操作在本地进行，不会联网
- LibreOffice Headless 模式下不支持实时预览
- Skill 每 7 天自动检查更新，不会频繁打扰
- **模板为纯代码生成，不包含二进制文件，更安全可靠**
- **v4.7 新增公式解释器、MD 转换均为纯本地实现，不读取外部凭证或 API Key**

---

## 更新日志

| 版本 | 日期 | 本次更新 |
|------|------|---------|
| v4.7.0 | 2026-08-17 | 增加：公式解释器 formula_explainer.py（反向 NL2Formula，Excel 公式→自然语言解释，纯本地实现，80+ 函数映射）；增加：Markdown→Word/PPT 转换器 md_converter.py（保留标题层级/表格/列表/加粗，纯本地实现）；合并：长文档排版 8 命令为 long-document 统一入口（--action 参数路由）；优化：长文档排版性能（分批处理 + 单次保存 + 进度回调，大文档不卡顿）；增加：公式解释器 CLI 子命令（formula-explain）；增加：MD 转换 CLI 子命令（md-convert）；增加：长文档排版 CLI 子命令（long-document） |
| v4.6.1 | 2026-08-16 | 修复：ASR 引擎改为显式 Opt-in 模式（auto 仅使用本地 whisper-local，不读取外部凭证）；修复：Azure/Google STT 仅在 method 显式指定时调用，首次使用显示凭证读取范围警告；修复：LLM 翻译改为显式 Opt-in 模式（auto 仅使用 local-rule，不读取 API Key）；修复：外部 SDK 依赖（google-cloud-speech / azure-cognitiveservices-speech）补充声明至 requirements.txt |
| v4.6.0 | 2026-08-16 | 增加：Excel 智能分析统一入口 excel-smart（6 命令合并为 1 个 --action 路由）；增加：数据图表生成器 chart_recommender.py（数据特征分析 + 智能图表推荐 + 图表嵌入 Excel）；增加：文档翻译模块 document_translator.py（Word/Excel/PPT 多格式翻译 + 多模型降级链）；增加：翻译引擎降级链（cn-llm-router → local-rule → pure-template）；增加：图表推荐规则引擎（时间序列/类别对比/相关性/多变量）；增加：硬件自适应（低配禁用复杂图表渲染）；增加：术语表支持（JSON 格式可配置） |
| v4.5.0 | 2026-08-05 | 增加：会议纪要生成模块 meeting_minutes.py（ASR 转写 → LLM 摘要 → Word 生成）；增加：ASR 降级链（whisper-local → azure-speech → google-stt → template）；增加：LLM 降级链（rule-engine → external-llm → pure-template）；增加：COM 健康检查模块 com_health.py（WPS/MS COM 状态检测 + 残留进程检测 + 自动释放）；增加：6 个 CLI 子命令（transcribe/summarize/generate/batch/wps-check/ms-check/residuals/release-all/full-check）；合并：避坑指南 20+ 条 + FAQ 15 个 + 错误 ID 15 个 → 统一故障排除大章（含统一索引表）；增加：音频分段处理（默认 5 分钟/段）+ 进度回调；增加：硬件自适应（低配禁用并行转写） |
| v4.4.0 | 2026-07-30 | 增加：长文档排版自动化模块 long_document.py（自动目录生成/页眉页脚自动化/标题编号自动化/图表索引自动化/交叉引用自动化/格式统一/批量排版）；增加：8 个 CLI 子命令（analyze/toc/header/numbering/fig-index/xref/format/all/preview）；增加：多级标题编号引擎（支持中文/阿拉伯/罗马数字三种样式）；增加：图表索引自动生成（图 1-1 xxx / 表 1-1 xxx）；增加：交叉引用验证与自动修复；增加：格式统一预设模板（论文/标书/报告三种风格）；增加：性能优化（分批处理 + 进度回调 + 单次保存） |
| v4.3.0 | 2026-07-23 | 增加：Excel 智能分析模块 excel_analyzer.py（公式自动纠错/数据清洗辅助/透视表自动生成/数据预测/NL2Formula 自然语言转公式/硬件自适应降级）；增加：6 个 CLI 子命令（profile/fix-formulas/pivot/predict/nl2formula/clean/hardware）；优化：数据类型探测算法（数值/日期/文本自动识别）；优化：透视表智能字段推荐（基于唯一值比例+数据类型）；增加：数据质量评分体系（0-100分） |
| v4.1.0 | 2026-07-17 | 增加：PPT智能生成深度增强模块 ppt_generator.py（多源输入/演讲者备注/动画建议/配色适配/图表推荐/排练辅助）；增加：4 大工具 CLI 子命令扩展（docx-to-ppt/generate/nl-analyze/invoice/review）；增加：配色方案自动生成引擎；增加：演讲者备注双模式（模板引擎 + 外部 LLM 可选）；优化：PPT 生成流程重构为分层架构 |
| v4.0.0 | 2026-07-13 | 增加：Word→PPT一键生成；增加：Excel自然语言数据分析；增加：Word合同条款审查标注；增加：Excel发票OCR入账；增加：4 个专用脚本（wps_docx_to_ppt/wps_nl_analysis/wps_contract_review/wps_invoice_ocr）；增加：Worker 路由扩展至 28 个命令 |
| v3.1.0 | 2026-07-07 | 修复：模板安全问题（删除二进制文件，改为纯Python代码生成）；增加：20+避坑指南；增加：FAQ扩展到15个；增加：文件限制速查表 |
| v3.0.0 | 2026-07-07 | 增加：自动重试机制（3次指数退避）；增加：硬件自适应（CPU/内存动态调整）；增加：Skill更新检查（7天提醒）；增加：常见问题FAQ（8个Q&A）；增加：CLI参数说明+返回结果示例；增加：反馈邮箱；增加：反模式FAQ（8个常见错误）；增加：最佳实践（10个案例）；增加：wps_performance.py 性能管理 |
| v2.5.0 | 2026-07-03 | 增加：纯Python模式增强（排序/筛选/图表/公式/统计）；增加：文档模板目录；增加：10个最佳实践案例；增加：反模式FAQ |
| v2.2.0 | 2026-06-30 | 增加：四引擎智能识别；增加：LibreOffice Headless 跨平台兜底；增加：纯Python格式设置/表格/图片插入 |
| v2.1.0 | 2026-06-28 | 增加：目录生成；增加：环境自检；增加：反馈入口；增加：错误速查手册 |
| v1.0.0 | 2026-06-28 | 初始版本，三大组件 + 格式转换 |
