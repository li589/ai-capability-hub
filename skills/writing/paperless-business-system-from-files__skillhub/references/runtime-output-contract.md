# 运行时输出契约

本文件规定“哪些文件应该由技能调用时生成”，避免把一次任务的结果、评审材料或示例成品永久放进技能安装包。

## 一、调用初始化阶段动态生成

`bootstrap_generation.py` 应在本次任务工作目录生成：

| 文件 | 作用 | 是否属于技能安装包固定文件 |
|---|---|---|
| `input-profile.json` | 全部输入文件只读盘点、哈希、格式、错误/警告 | 否 |
| `business-model.json` | 从结构化资料提取的业务对象、字段、公式、候选关系、证据与待确认项 | 否 |
| `BUSINESS_MODEL_REPORT.md` | 面向用户解释业务对象/字段/公式如何从资料中提取 | 否 |
| `business-profile.json` | 结合深度业务模型后的业务候选、置信度、证据 | 否 |
| `BUSINESS_RECOGNITION_REPORT.md` | 面向用户解释为何选择某业务域 | 否 |
| `INPUT_COMPLETENESS_REPORT.md` | A/B/C/D 完整度和未覆盖主题 | 否 |
| `source-file-mapping.json` | 来源文件、哈希、状态、后续字段映射入口 | 否 |
| `data-quality-report.md` | 文件级质量问题与恢复动作 | 否 |
| `BUSINESS_CONFLICTS.md` | 跨资料业务冲突；没有可靠冲突证据时保持“待比对” | 否 |
| `ASSUMPTIONS.md` | 安全假设与待确认事项；不得把缺证据项写成正式规则 | 否 |
| `system-spec.json` | 本次系统规格 | 否 |
| `DELIVERY_STATUS.json` | 本次交付验证状态 | 否 |

## 二、系统实现/验收阶段动态生成

正常完整交付还应根据真实实现生成或更新：

- `AUTO_GENERATION_REPORT.md`
- `business/generated_schema.json` 与 `business/generated_migrations.py`（使用 `generate` 时）
- `VALUE_REPORT.md`
- `TEST_REPORT.md`
- `PY_SOURCE_MANIFEST.json`
- `FILES_SHA256.txt`
- `RUNTIME_ACCEPTANCE.md` / `.json`
- `delivery-manifest.json`（使用时）
- `00_请先看_交付导航.md`
- `portable_full` 模式下的客户端、局域网辅助、版本区和完整部署包装文件
- 最终系统 ZIP

这些文件都描述“本次系统”，不属于技能本体的固定内容。

## 三、可以固定放在技能安装包中的内容

只保留真正需要复用的能力：

- `SKILL.md`：流程与约束；
- `scripts/`：只读分析、初始化、脚手架、诊断、验收、打包代码；
- `references/`：按需读取的领域规则和交付标准；
- `assets/scaffold/`：通用工程骨架；
- `assets/templates/`：空白 JSON 模板；
- `assets/icon.svg` 与必要界面元数据。

## 四、不应进入生产分发包

以下内容属于作者维护或一次性评审，不应让普通调用长期携带：

- CHANGELOG / UPGRADE_REPORT；
- 发布自测结果、质量证据截图、发布验证日志；
- 固定演示输出报告；
- 为回归测试准备的大量样例 CSV/截图；
- 平台安装后自动生成的 `_meta.json`、`_skillhub_meta.json`；
- 仅用于打“技能发布 ZIP”的构建脚本、哈希清单和发布清单。

如作者需要这些内容，应放在源码仓库或发布流水线，而不是生产技能 ZIP。
