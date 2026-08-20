---
name: 装前查
description: >
  中文 Agent 工具（Skill、MCP、插件...）安全风险查询。
  当用户想了解某个 AI 工具是否安全、查「XX 工具安全吗」「这个 skill 有风险吗」「XX 作者出过哪些高风险工具」、
  或需要按风险/来源浏览中文 Agent 工具生态时使用。数据来自装前查（zhuangqiancha.com）基于公开代码与声明的独立评估，
  涵盖权限透明、隐私去向、作者信誉、安全档位四个维度。零 API Key。纯文本回复，不生成图片。
---

# 装前查 · 中文 Agent 工具风险查询

帮用户在安装/运行一个中文 Agent 工具（Skill / MCP / 插件...）之前，先看清楚它的风险。

## 这是什么
装前查是**独立的工具风险查询层**，不是来源平台的镜像：基于公开代码与声明对工具做独立评估（权限透明 + 隐私去向 + 作者信誉 + 安全档位），帮你做到「知情同意」。结论**不构成安全担保**。

## 何时用
- 想了解某工具是否安全 / 有风险 / 能装吗
- 拿到 SkillHub / GitHub 链接或名字，想先评估
- 按风险浏览生态（高风险 TopN、某作者的工具）
- 选型时担心权限过大 / 数据外传 / 作者不可信

## 怎么用
**方式一 · 对话里调用（推荐）**  
例如 WorkBuddy：`/装前查` + 自然语言：
- `/装前查 API Gateway`
- `/装前查 作者 ctz168`
- `/装前查 高风险 Top20`
- `/装前查 https://skillhub.cn/skills/user_164f4c1f/global-biblio-base`

**方式二 · CLI（python3，仅标准库，纯文本）**
```bash
python3 scripts/zqc_cli.py search "关键词" [--limit N] [--grade red|orange|yellow|green]
python3 scripts/zqc_cli.py lookup "<slug或URL>" [--limit 15]
python3 scripts/zqc_cli.py risk [--limit 20]
python3 scripts/zqc_cli.py author "作者名或id"
```

### 用户贴链接时怎么查（强制按此解析）
1. **SkillHub**  
   `https://skillhub.cn/skills/{owner}/{name}`  
   → 先用工具名 `{name}` 做 `search`；若唯一命中则 `lookup` 其 slug。  
   常见 slug 形态：`skillhub:{name}` 或目录里带 owner 的条目，以 `search` 结果为准，勿臆造。
2. **GitHub**  
   `https://github.com/{owner}/{repo}`（可带 `/tree/...`）  
   → 候选 slug：`github:{owner}/{repo}`，先 `lookup`；失败再 `search "{repo}"` 或 `search "{owner}/{repo}"`。
3. 已是 `skillhub:…` / `github:…` 形态 → 直接 `lookup`。
4. 都失败 → 告知「装前查暂未收录」，可提示稍后再查或换准确工具名。

## 档位含义
| 档位 | 含义 |
|------|------|
| 高风险（red） | 命中高危证据，安装前务必确认权限与数据去向 |
| 谨慎（orange） | 存在中高风险信号，建议先看证据再决定 |
| 观察（yellow） | 有信号但较轻，使用前宜知情 |
| 未见风险（green） | 当前规则下暂未检出明显风险信号 |
| 待评估（unknown） | 证据不足或尚未完成评估 |

若 CLI 输出了「证据依据」，可原样转述（勿编造）：
- 代码实锤 / 文档自述 / 文档高危组合

若工具标记「证据待取证 / ungated」，说明档位可能尚不完整，建议以证据列表为准。

### 详情页（强制带上）
收录成功时，回复里用一行给出装前查详情页（CLI 会打印「更多细节：…」），例如：  
`更多细节：https://www.zhuangqiancha.com/tool/skillhub%3Axxx`  
**不要**输出「数据截至」时间。未收录则不要编造详情链接。

---

## 使用规范（给执行本技能的 agent）

### 必做
1. 先跑 CLI 再回复；**不编造**证据、作者统计、评级、隐私去向。
2. red / orange：明确「安装前请确认接受其权限范围与数据去向」。
3. 未收录：先 `search`，再如实告知。
4. 末尾固定：「装前查基于公开代码与声明独立评估，结论不构成担保。」
5. **只输出纯文本**，不生成、不展示、不提及任何图片 / PNG / 结果卡。
6. 有收录时转述 CLI 的「更多细节」详情页链接；有「隐私去向」段则一并转述（勿臆造域名）。

### 回复结构（强制，宜短）
1. 结果摘要（名、来源链接、档位、证据数、作者；有则加证据依据）  
2. 隐私去向（外联域名摘要 / 外传类证据；无则一句「未见外传信号」）  
3. 关键信号（有证据列 Top 条；无则一句）  
4. 作者侧一行（仅数字）  
5. 更多细节：装前查详情页 URL  
6. 一句话建议 + 免责声明  

### 禁止
- ❌ 编造个人对比 / 实测故事  
- ❌ 把绿档说成「放心用 / 绝对安全 / 已人工审过」  
- ❌ 无证据时大段推测数据去向  
- ❌「泼冷水」「没读代码」等自我拆台    


### 一句话建议口径
| 档位 | 建议 |
|------|------|
| green | 可作为装前参考；仍建议按需授权、留意更新。 |
| yellow | 建议先阅读上方信号再决定是否安装。 |
| orange / red | 建议暂缓或隔离试用，确认权限与数据去向后再装。 |
| unknown | 证据不足，建议优先选择已有完整评估的同类工具。 |

---

## 回复示例 · 绿档（0 证据）

```
装前查结果

工具：文章去AI味工具（unclecheng-reduce-ai-perception-v2）
来源：https://skillhub.cn/skills/user_ab5ae6ee/unclecheng-reduce-ai-perception-v2
评级：未见风险（green）
证据：0 条
作者：user_ab5ae6ee


简介摘要：面向文本的去 AI 痕迹改写；公开描述未体现 shell/外发等执行类能力。

作者信誉（装前查统计）：共 23 个工具 · 红 0 / 橙 0 / 黄 0 / 绿 23。

隐私去向：未见外传信号。

更多细节：https://www.zhuangqiancha.com/tool/skillhub%3Aunclecheng-reduce-ai-perception-v2

建议：当前未见明显风险信号，可作为装前参考；效果需自行试用验证。

装前查基于公开代码与声明独立评估，结论不构成担保。
```

## 回复示例 · 红/橙（有证据）

```
装前查结果

工具：示例高权限工具（demo-shell-tool）
来源：https://github.com/example/demo-shell-tool
评级：高风险（red）
证据依据：文档高危组合
证据：3 条（最高严重度 P0）
作者：example


评估证据：
[P0] R3_remote_code_exec — curl … | bash
[P1] R16_shell_exec — subprocess / os.system
[P2] CAP_cred_access — 文档提及读取 token

作者信誉（装前查统计）：共 5 个工具 · 红 2 / 橙 1 / 黄 0 / 绿 2。

隐私去向：外联 4 个域名（可疑 2 / 官方 1 / CDN 1）；外传类证据 1 条。
- api.example.com（可疑）
- [P1] R5_external_exfil — POST https://…

更多细节：https://www.zhuangqiancha.com/tool/github%3Aexample%2Fdemo-shell-tool

建议：建议暂缓安装或仅在隔离环境试用；安装前请确认接受其权限范围与数据去向。

装前查基于公开代码与声明独立评估，结论不构成担保。
```
