# 能源日报本地系统生成器：先看这里

如果你第一次使用，只需要先做一件事：**选你现在最接近的需求，然后复制对应一句话。**

## 30 秒选择入口

| 你现在想做什么 | 直接这样说 | 技能会做什么 |
|---|---|---|
| 用真实资料生成完整系统 | `根据我上传的文件生成完整能源日报本地部署 ZIP。` | 分析真实文件 → 建字段/规则 → 生成中文 Web 局域网系统 → 测试 → 打 ZIP |
| 修改已有能源系统 | `以我上传的旧系统 ZIP 为基础，按新资料修改并重新交付完整 ZIP。` | 保留原系统有效能力，比较差异后修改完整源码并复测 |
| 只想先分析资料 | `只分析这些文件，先不要生成系统。` | 只输出字段、口径、冲突、风险和建议，不生成 ZIP |
| 暂时没有真实文件，只想看方案/原型 | `我还没有业务文件，先按这段业务描述生成可评审原型，不要写入虚构历史数据。` | 可生成“原型/待确认”版本，但不会把示例数值冒充真实业务数据，也不会声称可直接生产上线 |
| 只要桌面版 | `我明确要独立桌面版，不要把它当 Web 主系统。` | 按需附加 Tkinter 独立程序及 EXE 构建源码 |
| 不知道自己属于哪种 | `帮我判断应该用哪种模式，不要先生成。` | 只做模式判断，告诉你下一句最短提示词 |

更完整的复制提示词见 `USER_PROMPT.md`；特殊触发方式见 `references/trigger-and-mode-guide.md`。

## 可以上传什么

能源日报、抄表记录、产量、目标、线别、成本、异常、已有系统 ZIP；格式可为 Excel、CSV、Word、PDF、TXT、MD、ZIP 等。

**最推荐的真实资料组合**：能源日报/抄表表 + 产量或单耗口径 + 目标或成本规则。资料不齐也可以先做，无法确认的关键规则会集中进入 `ASSUMPTIONS.md`，不会被偷偷猜成事实。

## 默认交付到底是什么

默认主交付是**浏览器中的中文 Web 局域网系统**：一台 Windows 电脑启动服务，同一局域网内其他电脑用浏览器访问。它不是一张静态网页，也不是必须安装在每台电脑上的传统桌面软件。

你不需要先理解 Web、EXE、Python 的区别。普通使用时只看两件事：

1. 有现成已验证 EXE：按交付导航双击启动；
2. 没有现成 EXE：按交付导航用 Python 启动，或交给 IT 在 Windows 上构建 EXE。

技能内的 Tkinter `standalone/energy_daily_report.py` 是**用户明确要求时才附加**的桌面工具，不能替代主 Web 系统。

## 正常最终交付应该是什么

不是一段代码，也不是一张网页，而是一个**可下载的单根目录 ZIP**。典型结构如下：

```text
系统根目录/
├─ 00_请先看_交付导航.md              ← 普通用户先看这个
├─ DELIVERY_STATUS.json              ← 真实交付状态，不会把“可构建”写成“已验证”
├─ 一键启动_Windows.bat
├─ 一键停止_Windows.bat
├─ 01_服务端_完整程序/
│  ├─ server.py / backend_core.py
│  ├─ energy_excel_import.py
│  ├─ backup_restore.py
│  ├─ port_config.py
│  ├─ launcher.py / stop_server.py
│  ├─ exe_entry.py / build_exe_windows.py / *.spec
│  ├─ templates/ / static/
│  ├─ vendor/（第三方离线依赖，普通用户无需阅读）
│  └─ data/
├─ 02_Windows填写客户端/
├─ 03_macOS填写客户端/
├─ PY_SOURCE_MANIFEST.json
└─ FILES_SHA256.txt
```

其中 `.py` 文件必须保留为可读完整源码。即使同时提供 EXE，也不能删除源码。

## 文件很多时只看哪里

**普通用户**：只看 `00_请先看_交付导航.md`、一键启动、一键停止。

**IT/运维**：再看 `01_服务端_完整程序/README_部署说明.txt`、`backup_restore.py`、端口配置与 EXE 构建说明。

**开发人员**：再看 `server.py`、`backend_core.py`、`energy_excel_import.py`、`templates/`、`static/`、EXE 构建源码。`vendor/` 通常不用逐个阅读。

完整文件地图见 `references/delivery-file-map.md`。

## Windows 启动与停止

如果 ZIP 内没有已验证 EXE，但电脑已有符合要求的 Python 3.10+，按交付导航运行 Windows 一键启动；退出服务时必须使用配套的一键停止入口。

服务器启动后，同一局域网电脑通过交付包生成的当前服务器地址访问。

**有 `build_exe_windows.py` 不等于已经有 EXE。** 只有 `DELIVERY_STATUS.json` 明确标记实际包含 EXE 二进制时，才能说“包里已有 EXE”；只有 Windows 真机完成构建和启动测试，才能说“EXE 已验证”。

## 备份与恢复

完整 Web 系统必须带 `01_服务端_完整程序/backup_restore.py`。备份使用 SQLite 安全备份接口并做完整性校验；恢复前必须确认服务已停止，覆盖数据库前保留回滚副本。

## 出问题时先做什么

不要先翻几十个文件。优先按这个顺序：

1. 看最终系统 ZIP 的 `00_请先看_交付导航.md`；
2. 运行技能项目中的 `python scripts/quick_check.py .` 获取中文摘要；
3. 仍无法判断时运行 `python scripts/diagnose_and_resume.py .`；
4. 对照 `references/faq-and-troubleshooting.md` 与 `references/reliability-runbook.md`。

## 技能包自身是否完整

正式生成前可先验证内置完整局域网基线：

```text
python scripts/ensure_full_lan_energy_system.py --check-only
```

该检查只读验证 ZIP 结构、CRC、安全路径和核心源码是否齐全，不会生成业务项目。通过后再执行实际展开，可降低模板损坏导致生成到一半才失败的风险。

## 只记住一句话也可以

上传真实能源资料后说：

> 根据我上传的文件生成完整能源日报本地部署 ZIP，保留完整 Python 源码、成对的一键启动/停止脚本、备份恢复工具和 Windows EXE 构建源码。
