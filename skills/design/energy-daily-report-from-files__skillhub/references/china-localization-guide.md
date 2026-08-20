# 国内环境与中国业务适配指南

本指南定义可验证的国内环境适配能力。国内部署准备度报告不构成法律、税务、会计或电子签名合规意见；涉及正式报税、电子签章、档案管理、个人信息处理或行业监管时，必须由用户提供现行制度和适用要求，并完成专业复核与真实验收。

## 一、无需联网的运行基线

- 生成系统默认采用中文界面、`zh-CN` 区域和 `Asia/Shanghai` 时区。
- CSV/TSV/TXT 支持 `UTF-8 BOM` 与 `GB18030` 读取，导出优先使用 Excel 可直接打开的 UTF-8 BOM 或 XLSX。
- 依赖安装优先使用带 SHA-256 清单的离线 wheels；强制离线且依赖不完整时明确停止，不修改业务数据库。
- 正式交付不得把 npm、CDN、Google Fonts、在线图标、在线地图或境外分析服务作为默认运行依赖。
- Python 安装引导只接受配置中的官方 HTTPS 地址、固定 SHA-256 和签名校验；模板占位符未替换时不得声称可自动安装。

## 二、个人信息保护配置

蓝图可声明：

```json
{
  "personal_info": {
    "enabled": true,
    "data_classification": true,
    "id_card_masking": true,
    "phone_masking": true,
    "bank_card_masking": true,
    "export_requires_permission": true,
    "retention_review_required": true
  }
}
```

实现时至少验证：

1. 列表、日志、导出和错误信息不会泄露完整证件号、手机号和银行卡号；
2. 未授权角色不能查看原值或批量导出；
3. 审计记录查看、导出和权限变更；
4. 数据保留期限来自用户制度，不由技能猜测；
5. 删除、匿名化与备份保留策略保持一致。

不得仅因启用脱敏开关就宣称“符合个人信息保护法”。

## 三、金额、税率和发票字段

蓝图可保存金额精度、币种、税率来源和发票类型，但正式计算必须满足：

- 金额使用 Decimal，不使用二进制浮点直接结算；
- 税率由用户确认并版本化，不把示例税率当作现行税法；
- 含税价、不含税价和税额的舍入口径必须配置并测试；
- 发票号码、代码、电子发票字段根据用户真实样本映射；
- 系统默认不自动开票、不自动报税、不自动付款。

示例：

```json
{
  "tax_config": {
    "enabled": false,
    "currency": "CNY",
    "rate_source": "pending_user_confirmation",
    "rounding": "ROUND_HALF_UP",
    "automatic_filing": false
  }
}
```

## 四、业务月、会计期间与节假日

- 支持自然月和用户定义的业务月起止日；
- 会计期间关闭后，普通用户不得静默修改；
- 跨月、跨年、闰年和月末日期必须测试；
- 法定节假日、调休和企业班次日历只有在用户提供有效日历时才启用；
- 不内置长期固定节假日表，不把过期日历当作当前规则。

## 五、审批和电子签名边界

可生成多级审批、会签、或签、退回、加签和超时提醒；但：

- 自动付款、自动采购下单、自动质量放行和绕过审批继续禁止；
- 电子签名仅作为接口或证据字段占位，未接入合法服务并完成真实验证前显示“未配置”；
- 审批人、组织范围、金额阈值和代理规则必须由用户确认；
- 所有审批动作记录操作者、时间、意见、前后状态和规则版本。

## 八、国内 Python 安装与包管理

### Python 解释器准备

- 技能运行时不访问下载站，也不提供镜像切换或在线回退。
- Python 安装包必须由用户或 IT 预先放入指定目录；模板只核验安全文件名、固定 SHA-256 和发布者签名。
- 核验完成后，用户或 IT 在系统标准界面中手动安装；技能不启动安装器、不申请管理员权限。
- 国内网络不可用不会影响已经准备完整的离线交付包。

### Python 依赖准备

`scripts/install_dependencies.py` 和 `scripts/prepare_offline_dependencies.py` 只处理本地文件：

1. IT 将与当前 Python、操作系统和架构匹配的 wheels 放入 `wheels` 目录；
2. `prepare_offline_dependencies.py` 为这些现有文件生成 SHA-256 清单，不执行下载；
3. `install_dependencies.py` 设置 `PIP_NO_INDEX=1`，只安装清单校验通过的本地 wheels；
4. 文件缺失、版本不匹配或哈希不一致时立即停止，不修改业务数据库。

### Python 版本兼容

- 最低要求：Python 3.10
- 推荐：Python 3.11+（更好的 asyncio 和性能）
- 不支持：Python 2.x、Python 3.9 及以下
- Windows：64 位优先；ARM64 Windows 需单独验证
- macOS：Apple Silicon 使用 universal2 或 arm64 包

## 九、国内办公环境

- 优先兼容 Microsoft Office 和 WPS 可打开的 XLSX/CSV；
- 中文文件名和路径使用 UTF-8，不假设英文目录；
- Windows 启动说明使用中文，并避免依赖 PowerShell 执行策略绕过；
- 局域网地址发生变化时由启动器显示当前候选地址，不在文档中写死某台电脑 IP；
- 所有外部接口默认 `enabled: false`，未配置时显示“未配置”。

## 十、国内适配验收证据

发布前至少保存以下真实证据：

- `chinese_locale_utf8_gb18030`：中文与两类常用编码读写；
- `offline_dependency_install`：断网环境使用离线依赖安装；
- `office_wps_export_roundtrip`：导出文件至少完成程序回读，若做 WPS 真机验证则单独记录环境；
- `personal_data_masking`：界面、日志和导出脱敏；
- `currency_decimal_rounding`：人民币金额精度与舍入；
- `business_calendar_boundary`：跨月、跨年与业务月边界；
- `external_resources_disabled`：默认运行不依赖 CDN 或境外资源。

未执行的项目必须保持 `pending` 或 `not_run`，不得预填通过。
