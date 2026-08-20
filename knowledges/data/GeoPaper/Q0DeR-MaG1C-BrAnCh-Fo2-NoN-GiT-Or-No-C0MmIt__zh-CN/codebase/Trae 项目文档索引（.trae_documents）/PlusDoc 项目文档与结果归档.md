---
description: "PlusDoc 项目文档与结果归档：收集并归档 PlusCode V8.0 分析链产出的实验说明、状态保存点、P1-P4 主线设计稿、论文主文段落以及数据集扩充阶段的 CSV 附件与演示材料。"
module_id: "atlas:a32811059632e22af108f6cf0c2e2f51"
updated_at: "2026-07-30T06:32:32Z"
---

# PlusDoc 项目文档与结果归档

## 概述 <!-- category:overview -->
收集并归档 PlusCode V8.0 分析链产出的实验说明、状态保存点、P1-P4 主线设计稿、论文主文段落以及数据集扩充阶段的 CSV 附件与演示材料。

## 架构设计 <!-- category:architecture_design -->
本模块为纯文档型叶子模块，按主题划分目录：`Notice/` 存放通知与 PDF；`PPT/` 存放演示文稿；`数据集扩充阶段汇报_附件/` 集中全球与意大利的统计 CSV 附件；`模型说明/` 预留模型文档位置；根目录下以 Markdown 为主，包含三类内容——(1) 实验设计与阅读稿（如 `P1_区域异质性分区字段设计与输出Schema_2026-06-29.md`、`P2_P3_P4综合阅读稿_正式LISA与空间级联版_2026-06-30.md`）；(2) 版本化状态保存点（`当前项目状态保存点_YYYY-MM-DD_*.md`），记录 V8.0 主链从环境修复到 P1-P4 逐步落地的演进；(3) 底表注册与口径固化文件（`base_table_registry_v8.csv` 与 `base_table_registry_v8.md`），定义 segment/file/threshold/soil-enriched 等统一表结构、阈值口径（全局 0.65、意大利 0.75）及 P1-P4 推荐用表分工。依赖方向单向向下指向 `PlusCode/Hyper-TCDF/V8.0` 产出的 `result_v8/...` 目录，本模块不产生代码，仅作为可追溯的论文级叙事与产物索引层。

## 技术栈 <!-- category:tech_stack -->
Markdown + CSV 为主的纯文本归档，无构建系统；PDF/PPTX 用于外部演示材料。

## 编码规范 <!-- category:coding_conventions -->
- 文件名采用“中文主题_版本号或日期”命名，日期统一使用 `YYYY-MM-DD` 格式，便于按时间排序回溯。
- 状态保存点文档以“当前项目状态保存点_YYYY-MM-DD_简述.md”形式记录每个里程碑的环境、运行产物与下一步计划。
- 底表清单同时提供机器可读的 CSV（`base_table_registry_v8.csv`）与人类可读的 Markdown（`base_table_registry_v8.md`），CSV 列固定为 table_name、file_path、granularity、row_count、key_fields、spatial_fields、group_fields、primary_usage、notes。
- V8.0 相关产物路径统一以 `result_v8/...` 前缀引用，确保文档与代码输出目录严格对齐。

## 配置与命令 <!-- category:unique_setup_and_commands -->
无需编译或安装；所有文档与 CSV 直接由 Git 管理。阅读主线建议按时间顺序浏览 `当前项目状态保存点_*.md`，并以 `base_table_registry_v8.md` 与 `base_table_registry_v8.csv` 作为后续 P1-P4 分析的入口规范。
