# 电脑清理 · 安全扫描清单（按系统适配）

本文件供「昆仑增长电脑清理助手」在**阶段 2 只读扫描**时调用。所有命令均为**只读**，禁止写入/删除。

## 0. 系统识别（先执行）
- macOS / Linux：`uname -s` → `Darwin` / `Linux`
- Windows(PowerShell)：`$env:OS` → `Windows_NT`

---

## 1. macOS 安全扫描路径

### 可扫描（绿/黄）
- `~/Library/Caches` — 各 App 缓存（只读统计体积，不删）
- `~/Library/Logs` — 日志
- `~/Library/Developer/Xcode/DerivedData` — Xcode 派生数据
- `~/Library/Application Support/com.tencent.xinWeChat` — 微信缓存/接收文件
- `~/Downloads` — 旧安装包、压缩包（>180 天未访问）
- `~/Desktop` / `~/Documents` / `~/Movies` / `~/Pictures` — 仅**扫描报告**，默认不动

### 只读统计命令示例
```bash
# 目录体积排行（前20）
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -20
# 大文件 Top50（>500MB）
find ~ -type f -size +500M -print0 2>/dev/null | xargs -0 du -h 2>/dev/null | sort -rh | head -50
# 重复文件（按内容哈希聚类，仅输出，不删）
find ~/Downloads -type f -print0 2>/dev/null | xargs -0 md5 -r 2>/dev/null | sort | awk '{print $1}' | uniq -d
# 旧文件（>180天未访问）
find ~/Downloads -type f -atime +180 -print0 2>/dev/null | xargs -0 du -h 2>/dev/null | sort -rh
```

### 回收方式（仅移入废纸篓，不 rm）
```bash
mv "/path/to/file" ~/.Trash/
# 或 Finder 删除（进废纸篓）
osascript -e 'tell application "Finder" to delete POSIX file "/path/to/file"'
```

### 危险禁区（红，默认不碰）
- `/System`、`/Library`、`/usr`、`/private`
- `~/Library/Keychains`、`~/Library/Saved Application State`
- 照片原图 `~/Pictures/Photos Library.photoslibrary`（整库勿动）

---

## 2. Windows 安全扫描路径

### 可扫描（绿/黄）
- `%TEMP%`（`C:\Users\<用户>\AppData\Local\Temp`）
- `C:\Users\<用户>\AppData\Local\Microsoft\Edge\User Data\Default\Cache`
- `C:\Users\<用户>\AppData\Local\Tencent\WeChat`（微信文件）
- `C:\Users\<用户>\Downloads`
- `C:\Users\<用户>\Desktop` / `Documents` / `Videos` / `Pictures`（仅报告）

### 只读统计命令（PowerShell）
```powershell
# 目录体积（前20）
Get-ChildItem "$env:LOCALAPPDATA\Temp" | ForEach-Object { $_.Length } | Measure-Object -Sum
# 大文件 Top50（>500MB）
Get-ChildItem C:\Users\$env:USERNAME -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 500MB } | Sort-Object Length -Descending | Select-Object -First 50 FullName, @{N='MB';E={$_.Length/1MB}}
# 重复文件（哈希聚类，仅输出）
Get-ChildItem $env:USERPROFILE\Downloads -File -Recurse -ErrorAction SilentlyContinue |
  Get-FileHash -Algorithm MD5 | Group-Object Hash | Where-Object { $_.Count -gt 1 }
```

### 回收方式（进回收站，切勿 Remove-Item -Force）
```powershell
# 进回收站
$shell = New-Object -ComObject Shell.Application
$shell.NameSpace(0).ParseName("C:\path\to\file").InvokeVerb("delete")
```

### 危险禁区（红）
- `C:\Windows`、`C:\Program Files`、`C:\Program Files (x86)`
- `C:\Users\<用户>\AppData\Roaming\Microsoft\Windows\Start Menu`
- 系统还原点目录、页面文件

---

## 3. Linux 安全扫描路径

### 可扫描
- `~/.cache`、`~/.local/share/Trash`
- `~/Downloads`、`~/Videos`
- 构建缓存：`~/.npm/_cacache`、`~/.cargo`、`~/.m2`

### 只读统计
```bash
du -sh ~/.cache/* 2>/dev/null | sort -rh | head -20
find ~ -type f -size +500M 2>/dev/null -printf '%s %p\n' | sort -rn | head -50
```

### 回收方式
```bash
gio trash /path/to/file
# 或 trash-put（若已装 trash-cli）
```

### 危险禁区（红）
- `/`、`/etc`、`/boot`、`/usr`、`/var`
- 任何系统账户 home 以外目录

---

## 4. 通用红线（任何系统）
- ❌ `rm -rf` / `del /S /Q` / `format` / `truncate`
- ❌ 通配符批量删 `rm -rf *.tmp`、递归删桌面/文档/下载
- ❌ `sudo` 强行扫描系统目录
- ❌ 未确认就移动文件
- ✅ 只统计、只报告、只移回收站、分批、留撤销日志
