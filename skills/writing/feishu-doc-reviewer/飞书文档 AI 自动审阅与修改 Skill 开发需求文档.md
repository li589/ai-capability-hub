# 飞书文档 AI 自动审阅与修改 Skill 开发需求文档

**版本**: V1.0  
**日期**: 2024  
**状态**: MVP 开发版  

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [功能需求](#3-功能需求)
4. [技术规格](#4-技术规格)
5. [API 接口清单](#5-api-接口清单)
6. [开发计划](#6-开发计划)
7. [风险与应对](#7-风险与应对)
8. [验收标准](#8-验收标准)
9. [附录](#9-附录)

---

## 1. 项目概述

### 1.1 背景
团队使用飞书文档进行协作，评审意见以"评论"形式存在。人工根据评论修改文档效率低且易遗漏。

### 1.2 核心目标
- ✅ 读取飞书文档的未处理评论
- ✅ 理解评论建议及选中的原文范围  
- ✅ 调用 AI 生成修改后的文本
- ✅ 直接写入飞书文档（通过 API）
- ✅ 反馈修改结果（回复评论）

### 1.3 核心决策
| 决策项   | 方案               | 理由                   |
| -------- | ------------------ | ---------------------- |
| 架构模式 | 直接 API 操作      | 抛弃本地 Markdown 中转 |
| 数据源   | 飞书为单一事实来源 | 无需双向同步，实时生效 |
| 格式处理 | 直接操作富文本块   | 保留加粗、链接等样式   |

---

## 2. 系统架构

```
数据流：
用户评论 → 获取评论列表 → 解析 block_id → 获取块内容 
→ AI 生成新文本 → 更新块 → 回复评论 → 完成
```

---

## 3. 功能需求 (P0)

### 3.1 认证与授权
- F-01: 通过 app_id/secret 获取 tenant_access_token
- F-02: 校验 docx:edit 和 comment:edit 权限

### 3.2 评论获取与解析
- F-03: GET /comment/v1/comments 获取评论列表
- F-04: 解析 target.block_id 和 target.quote 定位原文
- F-05: 过滤已处理评论（通过回复标签识别）

### 3.3 内容修改核心
- F-06: GET /docx/v1/documents/{token}/blocks/{id} 获取块
- F-07: AI 输入"原文+建议"，输出纯文本
- F-08: PUT 更新块，构造正确 text_elements 结构 ⭐
- F-09: API 失败时回滚，不破坏文档

### 3.4 状态反馈
- F-10: POST 回复评论，通知修改结果
- F-11: 回复中带 [AI-DONE] 标签，便于跳过

---

## 4. 技术规格

### 4.1 飞书块更新 Payload 示例
```json
{
  "fields": {
    "text_elements": [{
      "text": {
        "content": "修改后的文本",
        "style": {"bold": false, "italic": false}
      }
    }]
  }
}
```

### 4.2 原文定位策略（优先级）
1. 直接使用 comment.target.quote
2. block_id + range.offset 截取
3. 全块内容 + AI 模糊匹配

### 4.3 安全备份
- 每日定时调用 export_markdown 推送到 Git
- 增加 CONFIRM_MODE 开关，支持人工确认

---

## 5. API 接口清单

| 功能       | 端点                                       | 方法    | 权限             |
| ---------- | ------------------------------------------ | ------- | ---------------- |
| 获取令牌   | /auth/v3/tenant_access_token/internal      | POST    | -                |
| 获取评论   | /comment/v1/comments                       | GET     | comment:readonly |
| 回复评论   | /comment/v1/comments/{id}/replies          | POST    | comment:edit     |
| 获取块     | /docx/v1/documents/{token}/blocks/{id}     | GET     | docx:readonly    |
| **更新块** | /docx/v1/documents/{token}/blocks/{id}     | **PUT** | docx:edit ⭐      |
| 导出 MD    | /docx/v1/documents/{token}/export_markdown | GET     | docx:readonly    |

---

## 6. 开发计划

**Day 1**: 创建飞书应用，配置权限，测试 token  
**Day 2-3**: 实现 get_comments / get_block / update_block / reply_comment，验证 API 连通性 ⚠️  
**Day 4-5**: 接入 LLM，编写 Prompt，串联全流程  
**Day 6**: 测试格式保留、特殊字符、配置备份脚本

---

## 7. 风险与应对

| 风险           | 应对                               |
| -------------- | ---------------------------------- |
| API 结构变更   | 封装调用层，严格遵循官方文档       |
| 样式丢失       | MVP 优先保证文本正确，样式后续优化 |
| 误修改         | 开启 CONFIRM_MODE + 每日 Git 备份  |
| 私有化版本差异 | 预留 base_url 配置项               |

---

## 8. 验收标准

✅ 评论"改为 XXX" → 文档变"XXX" → 机器人回复"已修改"  
✅ API 报错时不修改文档，回复失败原因  
✅ 不重复处理已标记评论  
✅ 修改后保留原有加粗/斜体样式  

---

## 9. 附录

### 9.1 权限清单
```
docx:document:readonly
docx:document:edit  
comment:comment:readonly
comment:comment:edit
tenant_access_token
```

### 9.2 环境变量
```bash
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_BASE_URL=https://open.feishu.cn/open-apis
CONFIRM_MODE=true
```

### 9.3 Prompt 模板
```
你是一个文档编辑助手。请根据以下建议修改原文：
原文：{original_text}
修改建议：{suggestion}
要求：只输出修改后的文本，不要解释
修改后文本：
```

---

## 10. 参考资源
- 飞书开放平台：https://open.feishu.cn/document/
- DocX API: /document/ukTMukTMukTM/ucDOz4iNn4gMx4yNlcDN
- OpenHands: https://docs.all-hands.dev/

---
> **开发者提示**：优先验证 update_block 接口连通性，这是最大风险点。