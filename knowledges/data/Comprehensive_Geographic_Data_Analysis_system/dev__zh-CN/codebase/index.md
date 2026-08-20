---
layout_version: "agent/v1"
store_schema_version: "v1alpha1"
title: "Comprehensive Geographic Data Analysis system 代码库知识（codebase）"
description: "Comprehensive Geographic Data Analysis system @ dev 的代码库知识；单向只读，自动重生。"
repo: "Comprehensive Geographic Data Analysis system"
branch: "dev"
locale: "zh-CN"
workspace_path: "d:\\temp_desktop\\Proj\\Comprehensive Geographic Data Analysis system"
commit: "3a3acce1521cbcd62ca4ad657ea59269e02cfbf6"
partition_id: "61fec3d2dbd01490"
source: "codebase"
generated_at: "2026-07-29T19:56:37Z"
module_count: 4
---

# Comprehensive Geographic Data Analysis system 代码库知识（codebase）
_只读投影 · 自动重生（改动会被覆盖） · 权威源在知识卡 DB · 仅供参考、非强制规则_

## 格式说明
- **目录层级 = 模块树**：子目录即子模块。含子模块的模块写成目录，其自身内容在该目录的 `README.md`；无子模块的模块是平铺的 `<名>.md`。
- **模块文件 frontmatter**：`description`（一句话摘要）、`module_id`（稳定身份，文件可改名而 id 不变）、`source_files`（该模块对应的仓库源文件，grep 用；无则省略）、`updated_at`（该模块最近更新）。partition 级公共信息（layout_version/store_schema_version/repo/branch/locale/commit/partition_id/source）见本文件顶部 frontmatter，不在每个模块文件重复。
- **正文**：`## 标题 <!-- category:x -->` 每段是一个知识维度；`## 关系` 段按 **依赖 / 被依赖 / 相关** 三向各一行列出邻居模块（父子关系不列，由目录层级表达），链接是指向其它模块文件的相对路径。

## 层级总览
- [CGDA 综合地理数据分析平台根目录](<CGDA 综合地理数据分析平台根目录/README.md>) — CGDA 综合地理数据分析平台根目录：CGDA 平台的仓库根，提供跨平台一键启动器、后端辅助脚本与文档/工具/环境等子模块的统一入口与编排约定。
  - [CGDA 跨平台一键启动器（CLI Launcher）](<CGDA 综合地理数据分析平台根目录/CGDA 跨平台一键启动器（CLI Launcher）.md>) — CGDA 跨平台一键启动器（CLI Launcher）：CGDA 项目的跨平台 CLI 启动器，提供 start/stop/status/restart/logs/sync/flush/reset-db 等子命令，统一管理 Docker 基础设施、Celery Worker/Beat…
  - [项目文档与架构设计](<CGDA 综合地理数据分析平台根目录/项目文档与架构设计.md>) — 项目文档与架构设计：综合地理数据平台的文档集合，涵盖技术栈、后端架构、工作流编排、部署说明及各类工程决策纪要。
  - [地理数据工具与运维脚本集](<CGDA 综合地理数据分析平台根目录/地理数据工具与运维脚本集.md>) — 地理数据工具与运维脚本集：面向地理空间数据的下载、同步、扫描、校验与一次性分析脚本集合，支撑多源遥感数据集的远程发现、本地组织与质量验证。
