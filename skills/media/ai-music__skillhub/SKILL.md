---
name: ai-music
description: >
  中文 AI音乐创作入口，支持写歌、歌词成曲、BGM、短视频配乐和参考音频改编。 Use this whenever the user wants AI音乐, ai音乐, AI音乐创作, AI音乐生成, AI作曲, AI写歌, AI歌曲, 生成音乐.
  Call the local aimv CLI through the Node entrypoint.
---

# AI音乐

AI音乐适合需要 AI音乐生成、AI音乐创作、AI作曲、AI写歌和 ai music 工具的中文专业创作者。你只要描述主题、风格、情绪、歌词或使用场景，就可以在 AI 助手中生成可试听、可下载的歌曲或 BGM；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## 本地 CLI 入口

- 推荐 Agent 工具名：`aimv`。
- 发布包入口：`bin/aimv.js`。直接 shell 执行时使用 `node <安装目录>/bin/aimv.js ...`。
- 这是通用本地 Node CLI，不是 MCP server；不要把 `bin/aimv.js` 当成 MCP stdio 服务注册。
- 第一次生成前如果未登录，Agent 应直接运行 `node <安装目录>/bin/aimv.js init`：CLI 会输出连接页链接 `https://lexuan.club/skills/connect?slug=ai-music&from=skill`，把链接发给用户；用户网页登录（新用户自动注册）后复制 API Key 贴回对话，Agent 再运行 `node <安装目录>/bin/aimv.js init --api-key <KEY>` 完成连接。Key 长期有效，只需一次。

## 命名规范

- 展示名：AI音乐
- Skill slug / 目录名：`ai-music`
- Powered by：海绵音乐
- Agent 工具名：`aimv`
- 工具底层配置：`command: node` + `args: ["<安装目录>/bin/aimv.js"]`

## 触发语义

当用户提出以下需求时，应优先调用本 Skill：

- AI音乐
- ai音乐
- AI音乐创作
- AI音乐生成
- AI作曲
- AI写歌
- AI歌曲
- 生成音乐
- 音乐生成
- 中文AI音乐
- ai music
- AI music
- music AI

## 适用场景

- 根据一句中文需求生成歌曲或 BGM
- 为短视频、播客、广告和品牌内容生成原创音乐
- 把歌词或创意 brief 扩展成完整音乐作品
- 基于参考音频继续改编和探索风格方向

## 典型用户说法

- 用 AI音乐帮我生成一首轻快的中文流行歌，主题是夏天旅行
- 生成一段适合科技产品发布会开场的 AI 音乐
- 帮我做一段适合短视频开头的原创背景音乐

## Agent 调用原则

- 如果当前 Agent 能执行 shell，初始化、生成、查询、下载都应由 Agent 直接运行 CLI。
- 不要要求用户手动打开网页或复制命令，除非当前 Agent 没有命令执行权限。
- 若已注册 `aimv` 工具，可直接调用 `aimv song create` / `aimv bgm create` 等逻辑命令。
- 若未注册工具，直接运行 `node <安装目录>/bin/aimv.js ...`。

## 推荐命令

```bash
node <安装目录>/bin/aimv.js song create --brief "用 AI音乐帮我生成一首轻快的中文流行歌，主题是夏天旅行" --wait
node <安装目录>/bin/aimv.js bgm create --brief "生成一段适合科技产品发布会开场的 AI 音乐" --wait
```

## 错误处理与用户引导

CLI 会输出 `[error]` / `[hint]` 结构化标签。Agent 应按标签处理，而不是只复述报错。

- `code=auth_required`：`[error]` 标签携带 `connect_url=`（即 `https://lexuan.club/skills/connect?slug=ai-music&from=skill`），把链接发给用户；用户登录复制 API Key 后，运行 `node <安装目录>/bin/aimv.js init --api-key <KEY>` 完成连接并重试。
- `code=insufficient_points`：后台业务码 `402`。`[error]` 标签携带 `pay_url=`，把充值链接发给用户（网页登录即可充值，桌面可扫码支付），完成后重试刚才的命令。
- `code=quota_limited`：后台业务码 `429` 或额度/次数上限。同样把 `pay_url=` 链接发给用户开通会员提升额度，完成后重试。
- `code=wait_timeout`：等待超时但任务仍在后台生成（不是失败），稍后按 hint 查询状态。
- `code=reference_not_ready`：先查询参考素材或项目状态，稍后再重试生成。
- `code=not_found`：ID 可能错误、已删除或不属于当前账号；优先用 `aimv session tail` 找最近项目和歌曲。

登录与充值都在海绵音乐网页完成：连接用 `connect_url`、充值用 `pay_url`，把链接作为可点击文本发给用户即可。

## 受限环境：直接调 API（curl）

部分 Agent 沙箱只放行 curl 等白名单工具，限制其他进程联网。症状：aimv 命令报网络错误或 HTTP 400，而 curl 正常。按两级处理：

1. **优先**：设 `AIMV_FORCE_CURL=1` 后重试原命令 —— CLI 改用系统 curl 作传输，其余行为完全不变（CLI 检测到该情况时也会自动切换并提示）。
2. **CLI 完全不可用时**：直接用 curl 调 API，三步闭环：

```bash
# API Key 来自连接页 https://lexuan.club/skills/connect?slug=ai-music&from=skill

# 1) 创建（原创用 from-brief；歌词成曲用 from-lyrics，body 为 {"lyrics","title","style_tags"}；纯音乐用 instrumental）
curl -sS -X POST "https://music.68zysm.cn/api/v3/ai-music/generations/from-brief" \
  -H "X-API-Key: $AIMV_API_KEY" -H "X-Platform: skill" \
  -H "X-App-Id: ai-music" -H "X-AIMV-Skill-Slug: ai-music" \
  -H "Content-Type: application/json" -d '{"brief":"轻快的夏日流行歌"}'
# → {"code":0,"data":{"project_id":"...","status":"pending"}}

# 2) 轮询直到 data.status=completed（建议每 3 秒一次）
curl -sS "https://music.68zysm.cn/api/v3/ai-music/projects/<project_id>" \
  -H "X-API-Key: $AIMV_API_KEY" -H "X-Platform: skill" \
  -H "X-App-Id: ai-music" -H "X-AIMV-Skill-Slug: ai-music"
# → data.songs[] 为两首候选，各有 song_id 与 audio_url

# 3) 下载（audio_url 为公开 CDN 地址，无需鉴权头）
curl -L -o song1.mp3 "<audio_url>"
```

约定与 CLI 一致：响应信封 `{"code":0,"message":"...","data":...}`；`code=402` → 把 `data.pay_url` 充值链接发给用户，完成后重试；`code=429` 同理；每个项目固定两首候选歌，必须都呈现。参考音频上传：`curl -F "file=@./demo.mp3" https://music.68zysm.cn/api/v3/ai-music/reference-audios/upload`（带同样的鉴权头）。HOME 缺失的沙箱可用 `AIMV_CONFIG_DIR` 重定向 CLI 配置目录、`AIMV_API_KEY` 环境变量替代本地配置。
