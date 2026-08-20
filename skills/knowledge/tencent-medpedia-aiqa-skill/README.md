# 腾讯医典知识库问答 Skill

WorkBuddy Skill —— 检索腾讯医典官方科普知识库，在严格"只引用、不编造"的约束下整合归纳，输出结构清晰、句句可溯源的健康答案。

## 这是什么

一个 WorkBuddy Skill，让 WorkBuddy 能回答医疗健康问题（疾病、症状、用药、检查、就医等），
答案全部来自腾讯医典官方知识库，每条附带 `baike.qq.com` 原文出处。

- **零配置、零密钥**：安装即用，用户无需填写任何 token

## 安装

把整个 `tencent-medpedia-aiqa-skill/` 目录放到 WorkBuddy 的 skills 目录：

- macOS / Linux：`~/.workbuddy/skills/tencent-medpedia-aiqa-skill/`
- Windows：`%USERPROFILE%\.workbuddy\skills\tencent-medpedia-aiqa-skill\`

放好后**完全重启 WorkBuddy**，开新会话即可使用。

## 使用示例

- "糖尿病早期有什么症状？"
- "布洛芬的用法用量和禁忌是什么？"
- "儿童发烧到多少度需要就医？"

预期：**结论前置**的分点回答 + 末尾附腾讯医典科普文章链接 + 医疗免责声明。

## 目录结构

```
tencent-medpedia-aiqa-skill/
├── SKILL.md                     主指令（触发、查询、状态映射、兜底文案）
├── README.md                    本文件
└── references/
    ├── answer-system-prompt.md  答案生成约束（只引用不编造）
    ├── safety-rules.md          安全红线、未成年人保护、免责声明
    ├── golden-cases.md          标杆问答示例
    └── api-spec.md              查询接口规格（入参/出参/错误码）
```

## 版本

v1.1.0（2026-07-09）

- 同步产品更新的描述文案（description_zh / 引用规则 / 免责声明措辞 / "结论前置"）
- 包名更新为 `tencent-medpedia-aiqa-skill`
- 修复"首次提问答案被折叠"：明确要求答案作为独立完整的最终回复输出、结论前置、不混入工具调用过程叙述（详见 SKILL.md §2.4.1）
