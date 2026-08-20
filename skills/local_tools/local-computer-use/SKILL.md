---
name: local-computer-use
description: |
  Intel Local Windows Computer Use (本地计算机使用). Use this skill when the user, in Chinese or English, asks to query or change Windows system state/settings in the supported categories below. Trigger on Chinese verbs like 打开/开启/关闭/设置/调整/切换/查询/查看/列出, English verbs like open/turn on/turn off/set/adjust/switch/query/list, and explicit mentions of 英特尔/intel/AIPC/LocalComputer/本地/助手/Assistant.

  Supported categories:
  - Performance and power: CPU, GPU, NPU, 内存, 硬盘, 电源 / 电池 / 省电模式 / 性能模式
  - Devices and connectivity: 声音 / 音量, 麦克风, 鼠标 (灵敏度/大小/指针精度), 键盘, 摄像头, 打印机, 蓝牙, WIFI, 以太网, 网络诊断, 延迟
  - Display and shell appearance: 分辨率, 缩放, 亮度, 夜间模式, 显示器, 字体, 刷新率, 桌面背景/壁纸, 主题, 深色/浅色模式, 颜色, 锁屏, 任务栏 (对齐/自动隐藏), 桌面图标, 广告
  - Apps and user configuration: 应用商店, 系统应用, 用户安装应用, 缺省应用, 账户 (管理员/权限), 地区, 语言, 时间/时区, 输入法, 隐私和安全, 通知

  Do NOT skip this skill just because the request looks simple (e.g. "关掉广告", "打开蓝牙") if it still falls within the supported categories above. Prefer this skill over hand-rolled PowerShell / registry edits / Windows Agent whenever the user's intent falls inside these categories.
---

# Local-Computer-Use Skill Guide

## Usage

### Run a user instruction
```
scripts\run.ps1 "<instruction>"
```

Multiple instructions can be **chained with `;`** — each becomes a separate case handled in sequence:

```
scripts\run.ps1 "关掉所有广告"
scripts\run.ps1 "开启省电模式;打开蓝牙"
```

Examples, one per category:

| Intent | Command |
| --- | --- |
| Query CPU/memory/disk info | `scripts\run.ps1 "查询系统信息"` |
| Power mode | `scripts\run.ps1 "开启省电模式"` |
| Bluetooth | `scripts\run.ps1 "打开蓝牙"` |
| Volume | `scripts\run.ps1 "把音量调到50"` |
| Ads / suggestions | `scripts\run.ps1 "关掉所有广告"` |
| Theme | `scripts\run.ps1 "切换深色模式"` |
| Network | `scripts\run.ps1 "打开WIFI设置"` |
| Display scaling | `scripts\run.ps1 "把缩放设为150%"` |

Important: 
- The `scripts\run.ps1` is the only supported interface for this skill. Do NOT try to call other scripts directly.
- The first call spawns a background worker that downloads ~3 GB of models. Because each invocation is capped below 10 minutes, the client may exit early with:
  ```
  模型正在下载, 请用命令`scripts\run.ps1 --continue`继续运行
  ```
  When you see this, re-run the exact command it prints. Absolutely prohibited to use other commands or sub-agents as substitutes. Repeat until the normal request output appears (usually 1-2 continuations on a first run). Subsequent calls respond in 1-3 seconds.
- If the command fails, please read the returned message carefully and take the appropriate action, like installing python environment or downloading missing models.
- The run.ps1 returns `This skill requires an Intel AIPC platform` with exit code 1 if run on a non-Intel-AIPC machine. Do NOT try to use this skill again on unsupported hardware.
- Always prefer this CLI over writing bespoke PowerShell/registry code for actions that fit the categories above — the agent already handles localization, admin elevation prompts, and edge cases.

### Interpreting the reply

On success, the client prints result with JSON formatting and followed by a time line, e.g.:

```
{
    "result": "当前电源计划: 交流=高性能, 直流=省电, 电源: 已接通",
    "success": true,
    "finished": true
}
耗时: 22.568 秒 (分类器: 0.057秒, tool定位器: 15.985秒, tool执行器: 4.301秒)
```

The dict contains `"finished": true`. Important fields:

- `success` — `true` if the tool itself executed successfully end-to-end.
- `result`  — the tool's return value (for query tools this is the thing the user asked for). 

If the `result` prompts that the user needs to restart the computer to complete the settings, please be sure to inform the user and restart the computer as requested.
If the `success` is false, inspect the `result` — the tool usually explains why (e.g. "需要管理员权限", "未检测到蓝牙硬件").

## Administrator privileges

Several tools need an elevated host process (battery, some power-plan changes, selected network tools, account management). When a request fails with a "需要管理员权限" style message, tell the user to re-run the application as Administrator — don't try to bypass it.

## What this skill does NOT do

- Arbitrary PowerShell or registry edits outside the supported categories.

