# Windows 数据布局与分级参考（扩展版）

分析 Windows 扫描结果时读这份。讲"东西存在哪、怎么辨认、归哪一级"。
在原版基础上新增了盲区目录的说明。

## 多盘符

Windows 通常多个盘（C:、D:…）。磁盘总览列出所有盘，但**分析和清理聚焦系统盘 C:**——缓存、AppData、临时文件几乎都在 C:。其他盘（D: 等）一般是用户自存的资料/游戏，归 🟡 让用户自己判断，不要自动给删除按钮。

## 关键目录

### 用户目录

| 目录（环境变量） | 装什么 | 典型分级 |
|---|---|---|
| `%LOCALAPPDATA%`（`C:\Users\<u>\AppData\Local`） | 浏览器缓存、应用数据、Temp，最大头 | 缓存 🟢 / 应用数据 🟡 |
| `%LOCALAPPDATA%\Temp`、`%TEMP%` | 临时文件 | 🟢 |
| `%APPDATA%`（Roaming） | 应用配置/数据 | 🟡 |
| 浏览器缓存 `%LOCALAPPDATA%\Google\Chrome\User Data\*\Cache`、Edge 同构 | 浏览器缓存 | 🟢 |
| 浏览器 `User Data\<Profile>`（非 Cache 部分） | 书签/登录态/扩展 | 🟡 |
| `%USERPROFILE%\Downloads` 的安装包 | exe/msi 残留 | 🟢 |

### 应用本体

| 目录 | 装什么 | 典型分级 |
|---|---|---|
| `C:\Program Files` | 64位应用本体 | 🔴 仅重复/想卸时上灯，否则归蓝色 |
| `C:\Program Files (x86)` | 32位应用本体 | 🔴 同上 |
| `%LOCALAPPDATA%\Programs` | 用户级安装的应用 | 🔴 想卸时上灯 |

### 📦 NEW: 系统级目录（原版盲区，新增覆盖）

| 目录 | 装什么 | 典型分级 | 安全清理方法 |
|---|---|---|---|
| `C:\Windows\Installer` | MSI/MSP 安装补丁缓存，355+ 个文件，通常 10-30GB | 🟢 可通过 DISM 安全清理 | `DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase` |
| `C:\ProgramData` | 所有用户的共享应用数据 | 🟡 逐一判断 | 子目录指南见下方 |
| `C:\$Recycle.Bin` | 回收站（各盘独立） | 🟢 右键清空即可 | 桌面回收站右键→清空 |
| `C:\Windows\Temp` | 系统临时文件 | 🟢 可安全清 | 管理员 PowerShell: `del /s /q C:\Windows\Temp\*` |
| `C:\Windows\SoftwareDistribution` | Windows Update 下载缓存 | 🟢 可安全清（需先停 wuauserv） | `net stop wuauserv & del /s /q Download & net start wuauserv` |
| `C:\Windows\WinSxS` | 组件存储 (Component Store) | 🔴 绝不能手删 | DISM 可释放部分: `DISM /Online /Cleanup-Image /StartComponentCleanup` |
| `C:\hiberfil.sys` | 休眠文件（大小=内存容量） | 🔴 不要手删 | 关闭休眠: `powercfg /hibernate off` |
| `C:\pagefile.sys` | 虚拟内存页面文件 | 🔴 不要手删 | 系统自动管理，可通过系统属性调整大小 |

### 📦 NEW: ProgramData 子目录指南

| 子目录 | 大小参考 | 分级 | 说明 |
|---|---|---|---|
| `Comms` | 1-2 GB | 🟡 | 华为通讯服务（BasicService/Hiview/PCManager），用华为设备则保留 |
| `Package Cache` | 0.5-2 GB | 🟢 | Visual Studio/VC++ 安装缓存，可安全清 |
| `Intel Package Cache {*}` | 0.5-1 GB | 🟢 | Intel 驱动安装缓存，安装后无用 |
| `Autodesk` | 1-2 GB | 🟡 | 如已卸载 Autodesk 软件，可删；否则保留 |
| `Microsoft` | 0.5-5 GB | 🟡🔴 | Windows 系统组件，不建议手动碰 |
| `SogouInput` | 0.3-0.5 GB | 🟡 | 搜狗输入法语料库，在 App 内管理 |
| `USOPrivate` | 50-200 MB | 🟢 | Windows Update 会话数据，可安全清 |

### 开发缓存

| 目录 | 装什么 | 典型分级 |
|---|---|---|
| `%USERPROFILE%\.cache`、`.npm`、`.gradle`、`.m2`、`.nuget\packages` | 包管理器缓存 | 🟢 |
| `%LOCALAPPDATA%\pip\Cache` | pip 下载缓存 | 🟢 |
| `%LOCALAPPDATA%\uv` | uv 虚拟环境缓存 | 🟢 |
| `%LOCALAPPDATA%\Yarn` | Yarn 包缓存 | 🟢 |
| `%LOCALAPPDATA%\ms-playwright` | Playwright 浏览器二进制（~500MB） | 🟢 可再生 |
| `%LOCALAPPDATA%\go-build` | Go 构建缓存 | 🟢 |
| `%USERPROFILE%\.cargo` | Rust 工具链 | 🟡 重装耗时 |
| `%USERPROFILE%\.pnpm-store` | pnpm 全局存储 | 🟡 |

## 系统占用（不上灯，归蓝色"系统及其他"，间接释放写 long_term）

- `C:\Windows\WinSxS`：组件存储，**绝不能手删**，用 `DISM /StartComponentCleanup`
- `C:\Windows\System32`：核心系统文件
- `C:\Windows\SysWOW64`：32位系统文件
- `hiberfil.sys`（休眠）、`pagefile.sys`（虚拟内存）：系统管理，别手动删
- 间接释放：设置 > 系统 > 存储 > 存储感知；`cleanmgr`（磁盘清理）；扩展磁盘清理选 Windows 更新清理

## 更新器缓存（常见 🟢 项）

| 路径模式 | 应用 | 安全删除 |
|---|---|---|
| `%LOCALAPPDATA%\*updater` | 各种应用的更新缓存 | ✅ |
| `%LOCALAPPDATA%\Temp\*-update-*` | 更新临时文件 | ✅ |
| `%LOCALAPPDATA%\@*-updater` | Electron 应用更新器 | ✅ |

## 删除机制

`server.py` 在 Windows 用 ctypes 调 `SHFileOperationW`(FOF_ALLOWUNDO) 送进回收站；纯标准库。🟢 项的 `trash_paths` 应在用户配置文件（`%USERPROFILE%`）或允许的系统目录（`C:\ProgramData`、`C:\Windows\Temp`）内，便于白名单与越界校验通过。

## Windows 扫描 VS 原版 storage-analyzer 差异

| 原版扫描 | Windows 版新增 |
|---|---|
| user_profile | 同 |
| appdata_local | 同 |
| appdata_roaming | 同 |
| temp | windows_temp 补充 |
| downloads | 同 |
| program_files | 同 |
| program_files_x86 | 同 |
| ❌ | program_data |
| ❌ | windows_installer |
| ❌ | recycle_bin |
| ❌ | windows_update |
| ❌ | hiberfil.sys / pagefile.sys 检测 |
| dev_caches (7项) | dev_caches (12项，新增 nuget/playwright/go-build/pnpm) |
