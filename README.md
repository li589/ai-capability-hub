# AI 能力包 · 发布版

从 6 款 AI 编码工具里挑出下载量较高的能力包，按类型重新归拢，做成一个能直接翻找和取用的集合。

收录范围是 Trae、TraeCN、Qoder、QoderWork、QoderCN、WorkBuddy。不是这些工具的全部内容，只取其中用得多的通用能力，和个人项目绑定的没有收。

## 里面有多少

| | |
|---|---|
| 能力包 | 3,510 |
| 文件 | 46,725 |
| 能力类型 | 9 |
| 来源工具 | 6 |

按类型分：skills 3149 · plugins 201 · connectors 120 · design_libraries 16 · experts 12 · mcps 5 · canvas 4 · knowledges 2 · commands 1

按来源分：qoder-work 2012 · workbuddy 1371 · trae-cn 99 · trae 19 · qoder 6 · qoder-cn 3

## 怎么用

想找具体的包，用在线检索页最快：https://li589.github.io/ai-capability-hub/
支持按名称、简介、类别、来源搜索，点卡片直达对应的 GitHub 目录。

想整包拿走，用 git 拉 package 分支：

```bash
git clone --depth 1 --branch package https://github.com/li589/ai-capability-hub.git
```

仓库体积较大，GitHub 不提供整包 zip，所以走 git。

拿到本地后也可以用 `manifest.csv` 筛选：用 Excel 或任何 CSV 工具打开，按 `capability` 或 `category` 列过滤，就能挑出某一类。这个文件在仓库根目录，一份覆盖全部包，记录每个包的来源工具、类型、类别和原始路径。

## 目录怎么排的

顶层按能力类型分，不按来源工具分，这样同类的东西能挨在一起：

```
skills/           3149 包，下面再按 dev / design / writing / marketing / data 等子类分
plugins/          201 包
connectors/       120 包
design_libraries/ 16 包
experts/          12 包
mcps/             5 包
canvas/           4 包
knowledges/       2 包
commands/         1 包
manifest.csv      每个包的来源工具、类型、类别和原始路径（根目录一份）
```

跨工具重名的包加了工具后缀，比如 `_tr` 是 trae、`_qw` 是 qoder-work、`_wb` 是 workbuddy，免得互相覆盖。

## 收的是什么，不收什么

**收了：** 各工具里下载量较高的通用能力包、每个包的来源标注、以及用于溯源的 `manifest.csv`。

**没收：** 低频冷门或重复的内容、和具体个人项目绑定的能力。

## 两点说明

包里可能带可执行脚本，用之前翻一眼里面的代码，尤其是来路不明的。

发布前清理过一遍，密钥、Token、API Key、机器路径和个人项目能力都已移除，全量扫描结果写在 `检查报告.md` 里。`agent_created: true` 这字样只在模板说明文档里出现过，不是真正的自建标记。
