---
layout_version: "agent/v1"
store_schema_version: "v1alpha1"
title: "GeoPaper 代码库知识（codebase）"
description: "GeoPaper @ Q0DeR-MaG1C-BrAnCh-Fo2-NoN-GiT-Or-No-C0MmIt 的代码库知识；单向只读，自动重生。"
repo: "GeoPaper"
branch: "Q0DeR-MaG1C-BrAnCh-Fo2-NoN-GiT-Or-No-C0MmIt"
locale: "zh-CN"
workspace_path: "d:\\Workspace\\GeoPaper"
commit: "0000000000000000000000000000000000000000"
partition_id: "bfba9c24abae9ed9"
source: "codebase"
generated_at: "2026-07-30T07:36:55Z"
module_count: 5
---

# GeoPaper 代码库知识（codebase）
_只读投影 · 自动重生（改动会被覆盖） · 权威源在知识卡 DB · 仅供参考、非强制规则_

## 格式说明
- **目录层级 = 模块树**：子目录即子模块。含子模块的模块写成目录，其自身内容在该目录的 `README.md`；无子模块的模块是平铺的 `<名>.md`。
- **模块文件 frontmatter**：`description`（一句话摘要）、`module_id`（稳定身份，文件可改名而 id 不变）、`source_files`（该模块对应的仓库源文件，grep 用；无则省略）、`updated_at`（该模块最近更新）。partition 级公共信息（layout_version/store_schema_version/repo/branch/locale/commit/partition_id/source）见本文件顶部 frontmatter，不在每个模块文件重复。
- **正文**：`## 标题 <!-- category:x -->` 每段是一个知识维度；`## 关系` 段按 **依赖 / 被依赖 / 相关** 三向各一行列出邻居模块（父子关系不列，由目录层级表达），链接是指向其它模块文件的相对路径。

## 层级总览
- [Trae 项目文档索引（.trae/documents）](<Trae 项目文档索引（.trae_documents）/README.md>) — Trae 项目文档索引（.trae/documents）：为 Trae IDE 提供的项目级文档入口，集中存放 PlusCode 滑坡 TCDF 模型、学术论文与汇报材料等子模块的关联文档索引。
  - [学术论文与答辩材料文档库](<Trae 项目文档索引（.trae_documents）/学术论文与答辩材料文档库.md>) — 学术论文与答辩材料文档库：集中管理基于 Hyper-TCDF 模型的旱涝急转-滑坡灾害链研究相关的论文草稿、PPT 答辩材料、开题报告及中山大学毕业论文模板生成脚本。
  - [旱涝急转滑坡研究汇报幻灯片（Hyper-TCDF）](<Trae 项目文档索引（.trae_documents）/旱涝急转滑坡研究汇报幻灯片（Hyper-TCDF）.md>) — 旱涝急转滑坡研究汇报幻灯片（Hyper-TCDF）：基于单文件 HTML 的学术汇报演示文稿，展示 Hyper-TCDF 框架在旱涝急转诱发滑坡时滞因果机制识别中的意大利实证与全球扩展成果。
  - [滑坡 TCDF 模型与数据工程（PlusCode）](<Trae 项目文档索引（.trae_documents）/滑坡 TCDF 模型与数据工程（PlusCode）.md>) — 滑坡 TCDF 模型与数据工程（PlusCode）：基于 Hyper-TCDF 的滑坡时序预测项目，整合 GEE 原始缓存、TCDF 点级序列构建、区域训练与因果/空间异质性/级联效应等 V8.0 实验分析链。
  - [PlusDoc 项目文档与结果归档](<Trae 项目文档索引（.trae_documents）/PlusDoc 项目文档与结果归档.md>) — PlusDoc 项目文档与结果归档：收集并归档 PlusCode V8.0 分析链产出的实验说明、状态保存点、P1-P4 主线设计稿、论文主文段落以及数据集扩充阶段的 CSV 附件与演示材料。
