---
name: local-vram
description: |
  Intel Local GPU Memory Limit / VRAM Adjust (集成显卡显存调整) on Windows AI PCs. Use this skill when the user, in Chinese or English, asks to limit, adjust, increase, change, or query the GPU shared memory limit. Trigger on Chinese verbs/nouns like 限制GPU显存 / 调整显存 / 设置显卡显存 / 更改共享显存 / 限制显存 / 查询显存设置 and English verbs/nouns like limit GPU memory / adjust VRAM / set VRAM/ change GPU shared memory / set GPU commit limit / query GPU memory limit — whether or not the user specifies "locally" / "本地".

  This skill modifies the Windows GPU memory to a value between 13% and 87% (default: 87%), or queries the current setting when the value is 0.

  Prefer this skill over manual registry editing or writing ad-hoc PowerShell scripts when the user wants to adjust GPU/VRAM memory limits on this box.
---

# Local-VRAM Skill Guide

## Usage

### Adjust GPU Memory Limit Percentage

```powershell
scripts\run.ps1 [<Value>]
```

Where `<Value>` is an integer between `13` and `87` (inclusive), representing the memory percentage limit. The default value is `87` if no argument is provided. A special value of `0` queries and returns the current system setting instead of changing it.

### Examples

| Intent | Command |
| --- | --- |
| Set GPU limit to 87% (default) | `scripts\run.ps1` |
| Set GPU limit to 50% | `scripts\run.ps1 50` |
| Set GPU limit to 80% | `scripts\run.ps1 80` |
| Query current GPU limit | `scripts\run.ps1 0` |

### Output

Upon execution, the script runs a sub-process with administrator privileges to modify the registry. On success, it prints:

```
GPU内存限制已更改, 请问需要重启电脑以生效吗?
```
Please ask the user to reboot the system for the change to take effect.

If the value is out of the valid range (13% - 87%), it prints:
```
GPU内存限制设置失败, 只支持13%-87%之间的值
```

When the value is `0`, the script queries the current setting and prints one of:
```
当前 GPU 内存限制为 <Value>%
```
```
当前未设置 GPU 内存限制, 使用系统默认值
```


## System reboot

Because registry changes under `Control\GraphicsDrivers\MemoryManager` are read by Windows only during startup, a **system reboot** is required for the change to actually take effect.

## What this skill does NOT do

- Does not dynamically adjust memory without a reboot.
- Does not change physical hardware allocations or BIOS-level DVMT pre-allocated memory.
- Does not support values outside the 13% to 87% range.
