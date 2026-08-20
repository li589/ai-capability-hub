---
name: lovstudio-wechat-article-operator
description: 自动读取、编辑、保存并重载验证微信公众号文章；适用于“读取当前公众号文章”“替换封面”“插入这段内容”、"edit this
  WeChat article" 等需要可靠操作现有文章的任务。
version: 0.1.0
author: lovstudio
source_type: git
git_url: https://github.com/lovstudio/wechat-article-operator-skill
disable-model-invocation: true
---

# 微信公众号文章操作器

可靠地读取、修改、保存并验证微信公众号文章。把浏览器、编辑器和草稿状态视为可替换的适配器细节，对上层提供稳定的文章数据与操作结果。

## Triggers

### Activate when

- 用户说“读取当前公众号文章”“替换这篇文章的封面”“把这段内容插到品牌介绍前”“检查草稿是否真的保存”。
- 用户提供微信公众号编辑页、文章页或当前已登录页面，要求提取或修改文章。
- The user asks to "read the current WeChat article", "edit this WeChat article", "replace its cover", or verify that an edit persisted.

### Do not activate when

- 用户只需要离线写作或修改 Markdown，不操作微信公众号。
- 用户要从文件创建并发布一篇全新文章，应使用公众号发布能力。
- 用户要整体完成内容智能、封面与品牌化，应使用 `lovstudio-wechat-article-branding`。

## Operating contract

- **Article first, adapter second.** `draft` 只是文章状态，ego lite 只是当前验证过的适配器；不要把二者写进用户结果。
- **Read before write.** 写入前必须取得真实页面中的标题、摘要、正文、封面和结构快照。
- **Minimum mutation.** 只修改用户授权的字段或区块，保留其他可见内容。
- **Persisted truth.** 页面提示、DOM 变化或上传成功都不是完成；保存并重新加载后的状态才是事实。
- **Control ownership.** 用户接管浏览空间时立即停止，获得用户明确确认后再恢复。

## Workflow (MANDATORY)

### Step 0: Resolve the runtime and adapter

1. 优先使用用户明确指定的浏览器自动化能力。
2. 默认选择能复用登录状态、隔离任务空间并支持真实页面交互的适配器。
3. 使用 ego lite 时，完整读取 [ego-lite 适配器](references/ego-lite-adapter.md) 后再操作。
4. 缺少已登录会话时，把控制权交给用户完成登录；不要用另一套浏览器绕开当前会话。

### Step 1: Acquire the real article

读取并记录：

- 页面 URL、文章状态与账号侧可见标识；
- 标题、摘要、作者或来源字段；
- 正文 HTML、纯文本、章节和图片；
- 封面 URL、比例与素材状态；
- 可见字数、保存状态和目标区块数量。

按 [文章状态契约](references/article-state-contract.md) 组织内部快照。正文和凭据只保留在当前任务边界内。

### Step 2: Define the mutation plan

在动手前明确：

1. 目标字段或内容块；
2. 插入或替换锚点；
3. 允许变化的状态路径；
4. 必须保持不变的字段；
5. 完成后应出现的唯一标识或可见文本。

用户要求“整体优化”时不要擅自扩大操作范围；先交给 Branding Skill 生成内容计划，再执行其明确变更。

### Step 3: Apply the smallest reliable edit

- 普通表单优先使用语义定位器。
- 富文本编辑器先做可撤销的小探针，并通过可见状态确认落点。
- 大段富文本使用编辑器真实支持的粘贴或键盘路径，避免只改 DOM。
- 为新增结构使用稳定、非用户可见的唯一标记；写入后检查数量和相对顺序。
- 上传封面后检查素材被选中、裁切确认和实际封面 URL 更新。

### Step 4: Inspect before saving

至少检查：

- 目标内容只出现一次；
- 没有测试文字、空壳区块或重复节点；
- 插入点与目标锚点顺序正确；
- 标题、摘要、正文、图片与封面只发生计划内变化；
- 平台预览中的关键比例或版式成立。

### Step 5: Save and reload

1. 执行平台保存动作。
2. 等待明确的已保存状态。
3. 重新加载同一篇文章。
4. 再次采集文章状态。
5. 使用 `scripts/verify_article_state.py` 或等价比对，验证允许变化和必需结果。

示例：

```bash
python3 "$SKILL_DIR/scripts/verify_article_state.py" before.json after.json \
  --allow 'word_count' \
  --allow 'blocks.cover_prompt*' \
  --expect 'blocks.cover_prompt.count=1'
```

### Step 6: Report the observed result

报告实际观察到的：

- 修改内容与位置；
- 保存和重载结果；
- 保持不变的关键字段；
- 仍需要用户处理的登录、预览或发布步骤。

不要把“已上传”“已选中”“页面提示成功”写成最终持久化结果。

## Failure recovery

- **重复或错位：** 按唯一标记定位错误区块，清理后重新同步编辑器选区。
- **重载丢失：** 说明写入未进入编辑器状态；改用真实输入、粘贴或编辑器命令路径。
- **封面仍是旧 URL：** 回到选择、裁切、确认链路，保存后再次检查 CDN URL。
- **用户接管控制：** 停止所有操作，等待明确继续指令。
- **非目标字段变化：** 停止交付；从原始快照恢复或让用户选择保留范围。

## Private boundary

不得打包、记录或公开登录 Cookie、编辑令牌、账号标识、未发布正文、私人浏览器路径与真实品牌凭据。Skill 只携带通用数据契约、适配器规则和验收逻辑。

## Dependencies

- 一个能操作用户已登录微信公众号页面的浏览器自动化适配器。
- Python 3.8+，仅用于可选的确定性状态验证脚本。
