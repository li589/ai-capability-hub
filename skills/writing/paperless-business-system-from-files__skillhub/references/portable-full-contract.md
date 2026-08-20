# portable_full 完整部署包契约（V1.5.11 级）

`portable_full` 用于用户明确要求“完整部署包、局域网完整包、类似现有 V1.5.11 的交付、服务器端+填写客户端、一键启停、给普通电脑用户使用”等场景。

它不是“把源码多压一次 ZIP”，而是**交付包装与运行生命周期模式**。

## 1. 触发与 system-spec

用户明确要求完整部署包时，将：

```json
system.deployment_mode = "portable_full"
portable_full.enabled = true
```

如果用户明确要求局域网多人访问，再将 `system.network_mode = "lan"`。不要因为 `portable_full` 自动把所有系统暴露到局域网。

推荐初始化命令：

```bash
python scripts/bootstrap_generation.py <材料> --output <工作区> --deployment-mode portable_full --network-mode lan
```

## 2. V1.5.11 级目录标准

最终 ZIP 根目录至少包含：

- `01_服务端_完整程序/`：完整第一方源码、templates/static、SQLite/迁移、数据目录、日志目录、备份恢复、诊断、验收、EXE 构建源码、服务端一键启停；
- `02_Windows填写客户端/`：`server_url.txt`、打开系统、设置服务器地址、测试服务器连接、使用说明；
- `03_macOS填写客户端/`：仅当用户要求 macOS 或现有系统已有该能力时生成；
- `04_业务原始资料参考/`：保留“参考资料区”能力。默认只放说明，不自动复制敏感原件；用户明确要求随包带资料时再复制；
- `05_电子档模板/`：保留正式导入/申请/业务模板区域；没有证据时只放说明，不伪造正式模板；
- `06_说明与版本记录/00_当前版本/`：VERSION、当前版本说明、更新摘要和交付能力说明；
- 根目录 Windows 一键启动/停止入口；若启用 macOS 支持，根目录同时提供 macOS 启停入口；
- `00_请先看_交付导航.md`、`DELIVERY_STATUS.json`、测试/验收/哈希等交付证据。

目录名可以按业务名称微调，但能力不得缩水。

## 3. 运行时策略

`portable_full.runtime_strategy` 必须显式记录，允许：

1. `self_bootstrap_venv`：像 V1.5.11 一样，优先使用已有虚拟环境；没有时由系统 Python 创建项目专属 venv 并安装依赖；
2. `bundled_python`：随包提供可再分发的便携 Python + 本地依赖；
3. `windows_exe`：随包提供已构建 Windows EXE；
4. `inherit_existing`：升级现有完整包时保留并验证既有运行时/虚拟环境/客户端；
5. `source_only`：只能作为开发交付，**不得**宣称 portable_full 完整运行交付。

### “解压即用、免 Python”声明门禁

只有满足以下任一条件且完成目标 Windows 真机验证时，才允许 `no_python_required_verified = true`：

- 已包含并验证 Windows EXE；或
- 已包含并验证可再分发的便携 Python 运行时及全部本地依赖。

`self_bootstrap_venv` 仍可属于 V1.5.11 级完整部署模式，但目标机必须已有可用 Python；如果依赖需要联网安装，就不能宣称“完全离线首次安装”。

### “完全离线首次安装”声明门禁

必须有本地 wheelhouse/依赖缓存、便携运行时或已验证 EXE，不得只凭 `requirements.txt` 声明。

## 4. 局域网能力

当 `system.network_mode = "lan"` 时：

- 服务端允许显式绑定 `0.0.0.0`；
- 仍需显示实际内网访问地址；
- 提供查看服务器内网地址、连接测试和当前端口/地址说明；
- Windows 客户端的服务器地址可配置，不得把某台机器的固定 `192.168.x.x` 写死为所有用户默认值；
- Windows 防火墙开放动作必须由用户主动执行，并只开放本项目当前端口，不能静默修改系统安全设置。

## 5. 继承升级

如果附件中存在 V1.5.11 一类完整系统 ZIP：

- 优先保留原目录、SQLite、历史备份、迁移、运行时、客户端、启停工具、端口配置、日志、模板和版本资料；
- 不得只抽取 `app.py` 后重新生成一个简化包；
- 原有 `.venv/.venv_windows/portable_runtime/dist` 只在来源可信、与目标 OS 匹配且用户要求保留时进入最终包；
- 不复制真实密码、会话、secret key、shutdown token、私人日志等运行态敏感文件到“新建系统”模板。

## 6. 验收

除常规 `validate_local_bundle.py --strict` 外，`portable_full` 必须额外运行：

```bash
python scripts/validate_portable_full.py <项目目录> --strict
```

最终 `finalize_delivery.py` 会根据 `system-spec.json` 自动执行该门禁，并在候选 ZIP、最终 ZIP 两次独立解包后重复验证。

以下任一情况不得标记为完整 `portable_full`：

- 缺少服务端完整程序目录；
- 缺少 Windows 填写客户端；
- 根目录没有一键启停；
- 客户端不能配置/测试服务器地址；
- 缺少版本记录区；
- `runtime_strategy=source_only`；
- 声称免 Python/完全离线，但没有对应运行时证据和真机验证。
