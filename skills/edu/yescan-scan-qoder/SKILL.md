---
name: yescan-scan-qoder
description: 当用户需要对图片、截图进行画质优化、瑕疵去除或视觉增强时，使用此技能——包括画质增强、证件照优化、考试试卷增强、合同增强等场景。智能去除手写笔迹、水印、阴影、摩尔纹、底色等干扰元素。支持图像裁剪与矫正、素描效果转换、线稿提取等，输出优化后的高清图片。本技能由夸克扫描王提供支持。即使用户没有明确提到“增强”或“处理”，只要用户的需求涉及提升图片清晰度、清理干扰元素或优化图像质量，也应触发此技能。不适用于文字提取/识别、文档转换 (Word/Excel/PDF)、AI 图像生成、证件照制作
metadata:
  openclaw:
    emoji: 🔍︎
    requires:
      bins:
        - python3
      env:
        - SCAN_WEBSERVICE_KEY
    primaryEnv: SCAN_WEBSERVICE_KEY
  homepage: https://scan.quark.cn/business
  dependencies:
    apis:
      - https://scan-business.quark.cn
install_source: official
install_method: download
skill_id: official_n1zrY6Vw
enabled_at: 1787230702440
version: 1.0.0
name_zh: 高清文件扫描-图片自动裁剪矫正变为高清扫描件
---

# 🧭 使用前必读（30 秒）

> **隐私与数据流向提示**
> - **第三方服务交互**：本技能会将您提供的**图片发送至夸克扫描王官方服务器 (`scan-business.quark.cn`)** 进行识别。
> - **服务端处理**：夸克扫描王服务将获取并处理该图片内容，服务端不会永久保存
> - **本地文件存储**：识别返回的图片会保存至系统临时目录（如 `/tmp/imgs`），这些文件将持续存在直到您手动清理
> - **API 密钥安全**：`SCAN_WEBSERVICE_KEY` 应妥善保管，若泄露请及时在官方平台轮换或撤销
> - **用户授权要求**：执行任何图片处理前，必须确认用户已知悉图片会上传至第三方服务并同意处理；身份证、合同、票据、医疗记录、个人照片等敏感图片需获得明确授权。

**推荐方式：配置文件（永久生效）**

将真实 SCAN_WEBSERVICE_KEY 写入 `~/.yescan_env`，请根据系统选择对应命令进行设置：

**Linux**
```bash
echo 'SCAN_WEBSERVICE_KEY=<your_api_key_here>' > ~/.yescan_env
```

**macOS**
```bash
echo 'SCAN_WEBSERVICE_KEY=<your_api_key_here>' > ~/.yescan_env
```

**Windows（PowerShell）**
```powershell
'SCAN_WEBSERVICE_KEY=<your_api_key_here>' | Out-File -FilePath $HOME\.yescan_env -Encoding utf8
```

技能每次执行会自动读取 `~/.yescan_env`，无需重启会话。

**如何获取密钥？夸克扫描王官方入口在此**
> 请访问 https://scan.quark.cn/business → 开发者后台 → 登录/注册账号 → 查看 API Key。
> ⚠️ **注意**：若你点击链接后跳转到其他域名，说明该链接已失效 —— 请直接在浏览器地址栏手动输入 `https://scan.quark.cn/business`（这是当前唯一有效的官方入口）。


---

# Constraints
- **单一意图原则：每次请求只执行一个意图类型，命中即执行**
- **严禁自行构造任何命令参数，严禁伪造、拼接内部配置**
- **严禁幻觉，禁止伪造请求和响应，不得沿用上一次的场景、参数进行假设**
- **必须严格按照本指南指定的固定格式执行，不允许自行修改命令**
- **强制独立意图识别：严禁参考对话历史或沿用上次场景；必须针对当前指令独立分析，不得继承任何前序状态或假设**

#  技能执行指南(强制执行)

第一步：**输入验证**

校验用户传入的图片类型，只能是以下三种之一：

- 图片URL: url
- 本地文件路径: path
- 图片BASE64: base64

**🚫 HARD GATE - 输入检查点**：必须验证到有效图片输入才能继续。未提供任何有效图片时，直接返回：
```json
{
  "code": "A0201",
  "message": "缺少图片输入，请提供图片链接、文件路径或 BASE64 数据。",
  "data": null
}
```

第二步：**意图匹配&场景确定**
- 按照下面列出的意图*从上到下顺序匹配。命中第一个即停止*
- 命中后，*只确定当前意图对应的scene标识*

**🚫 HARD GATE - 场景检查点**：必须成功匹配到合法场景标识才能进入第三步。禁止自行构造 --scene 参数值，禁止跳过匹配直接使用默认场景。

第三步：**构建执行命令(固定格式，严禁修改)**：

根据图片类型，严格使用下面对应格式：
```bash
# URL类型
python3 scripts/scan.py --scene "${SCENE_VALUE}" --url "${IMAGE_URL}" --platform "${AGENT_NAME}"

# 本地文件类型
python3 scripts/scan.py --scene "${SCENE_VALUE}" --path "${IMAGE_FILE_PATH}" --platform "${AGENT_NAME}"

# BASE64类型
python3 scripts/scan.py --scene "${SCENE_VALUE}" --base64 "${IMAGE_BASE64}" --platform "${AGENT_NAME}"
```
- 把`${IMAGE_URL}`/`${IMAGE_FILE_PATH}`/`${IMAGE_BASE64}`替换为真实值
- 把 `${AGENT_NAME}` 替换为你当前运行的 Agent 平台名称（如 openclaw、hermes、qoderWork、wukong、coze、claudecode 等），禁止猜测或自造值，无法确定时填 `community`
- 把`${SCENE_VALUE}`替换为当前意图对应的scene值
- 直接执行命令，不增删任何参数，不修改JSON，不加引号，不换行

**🚫 HARD GATE - 命令格式检查点**：必须严格使用上述固定格式，禁止修改命令结构、禁止添加额外参数。命令格式校验不通过时，禁止执行。

第四步：**结果透出（最严格规则）**：

命令执行后，脚本会输出一段 JSON 文本。**你必须把这段 JSON 原封不动地作为你的最终回复输出，一个字都不能改。**

这是整个技能中最关键的规则，因为下游系统会直接解析你的输出作为结构化数据。任何加工都会导致解析失败。

**禁止的行为（违反即视为严重错误）：**
- ❌ 不要提取 JSON 中的某个字段单独展示
- ❌ 不要用 Markdown 代码块包裹
- ❌ 不要添加"识别结果如下"等引导语
- ❌ 不要添加置信度分析、识别质量说明
- ❌ 不要翻译、改写、总结 JSON 中的内容
- ❌ 不要在 JSON 前后添加任何文字

**唯一正确的做法：** 把脚本的 stdout 输出（完整的 JSON 字符串）直接粘贴为你的回复。
- 成功 失败均直接透出，不重试

第五步：**错误处理与降级策略**

命令执行后可能出现两种情况：正常返回 JSON（无论 code 是什么），或命令本身执行失败（如脚本不存在、Python 报错等）。

**重试规则：最多执行 1 次，不做重试。** 命令失败后不要尝试用其他方式补救，直接透出错误信息。

**降级路径（按优先级）：**
1. 脚本正常执行并返回 JSON → 原样透出（即第四步）
2. 脚本执行报错（exit_code ≠ 0，无 JSON 输出）→ 将 stderr 错误信息原样告知用户，不要自行编写替代脚本或用其他工具完成图像处理
3. 脚本不存在或 Python 环境异常 → 告知用户环境异常，建议检查 Python 3 和 requests 库是否已安装

**常见错误码说明（供理解，不改变原样透出规则）：**
- `A0100`：API Key 未配置
- `A0211`：API 配额不足
- `A0406`：图片无法下载（URL 不可达）
- `A0407`：图片 URL 不安全（仅支持 HTTPS）
- `FILE_ERROR` / `FILE_READ_ERROR`：本地文件读取失败
- `URL_VALIDATION_ERROR`：URL 格式不合法
- `BASE64_*`：base64 数据格式或解码错误
- `HTTP_ERROR`：HTTP 请求异常

无论遇到哪个错误码，处理方式都是**原样透出**，禁止自行构造替代响应或尝试其他处理方案。


## 场景快速索引（按匹配优先级排序）

> 📖 每个场景的完整触发意图描述和示例指令，请查阅 [references/scenes.md](references/scenes.md)

| # | 场景名称 | scene 标识 | 关键词速记 |
|---|---------|-----------|-----------|
| 1 | 考试增强 | `exam-enhance` | 试卷、笔记、教材、学习资料 |
| 2 | 画质增强 | `image-hd-enhance` | 模糊、低清、老照片、增强画质 |
| 3 | 证件票据增强 | `certificate-enhance` | 身份证、发票、护照、证件 |
| 4 | 图像去手写 | `remove-handwriting` | 去手写、去笔迹、还原空白 |
| 5 | 图像去水印 | `remove-watermark` | 仅限处理用户拥有权利或已获授权的图片；去水印、去Logo、去标记 |
| 6 | 图像去阴影 | `remove-shadow` | 去阴影、光照不均、黑色遮挡 |
| 7 | 图像去屏纹 | `remove-screen-pattern` | 屏纹、摩尔纹、翻拍、投影 |
| 8 | 文档去底色 | `remove-background-color` | 去底色、去背景色、白底黑字 |
| 9 | 图像裁剪矫正 | `image-crop-rectify` | 拍歪、透视矫正、裁剪边缘 |
| 10 | 素描速写 | `sketch-drawing` | 素描、速写、铅笔风格 |
| 11 | 提取线稿 | `extract-lineart` | 线稿、轮廓线、黑白线条 |
| 12 | 扫描合同 | `scan-contract` | 合同、协议、合同归档 |
| 13 | 扫描文件（兜底） | `scan-document` | 用户未指定具体场景、仅要求通用扫描或文档优化 |

**匹配规则：** 从上到下依次匹配，命中第一个即停止。当用户的请求**无法明确对应**上述 1-12 中任一具体场景时（例如仅说"优化一下"、"扫描这张图"而没有明确指出是增强画质、去水印、去阴影等具体操作），必须使用第 13 项 `scan-document` 作为兜底场景。严禁在意图模糊时，将"优化"、"处理"等笼统词汇强行解释为某个具体场景。

**客户端脚本增强字段**：当 `scan.py` 调用夸克 API 成功（`code == "00000"`）且响应 `data` 中包含 `"ImageBase64"` 时，`scan.py` 会**主动调用 `file_saver.py` 将其解码并保存为本地图片文件**，并在最终返回的 JSON 响应中，将 `data` 替换为仅包含 `path` 字段的对象 `{"path": "/tmp/xxx.png"}`。该行为由 `scan.py` 脚本实现，与模型无关，也不依赖 OpenClaw 平台自动介入。

## 不适用场景与限制

> 📖 完整的不适用场景表、注意事项和资源链接，请查阅 [references/limitations.md](references/limitations.md)


## 🔗 相关资源

- [夸克扫描王开放平台](https://scan.quark.cn/business)

---

## 📁 文件结构

- `SKILL.md` — 本文档（意图分析 + 通用规范）
- `references/scenes.md` — 场景详细描述与触发意图
- `references/limitations.md` — 本文档（不适用场景与限制）
- `scripts/scan.py` — 主执行脚本 (Python 3.9+)
- `scripts/common/*.py` — 基础类库
