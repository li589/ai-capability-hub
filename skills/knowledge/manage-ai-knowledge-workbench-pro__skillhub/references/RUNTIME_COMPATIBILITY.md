# SkillHub 运行时兼容边界

## 两条运行路径

### Python 主路径

Python 3.10+ 主路径提供完整能力：

- 环境诊断；
- 聚合结构清单；
- 受状态锁保护的单次付费请求；
- 支付后同订单重试；
- 方案校验与本地应用；
- Metadata-only 知识索引和离线 HTML；
- 后续本地增量更新。

### SkillHub POSIX Shell 免费回退

`scripts/skillhub_compat.sh` 只用于 SkillHub 云端案例沙箱或其他没有 Python、但具备 POSIX Shell 的受控环境。它只开放：

- `doctor`：验证事实源、独立工作区、元数据扫描和 SHA-256 能力；
- `manifest`：经明确确认后，在事实源之外生成聚合结构清单。

该路径在结构化结果中标识为 `posix-shell-free-precheck`。

回退路径不读取笔记正文，只使用目录结构和文件元数据；不上传清单、不请求网络、不创建订单、不触发支付、不应用付费方案、不生成 HTML、不更新事实源。结构清单契约及 `manifest_digest` 必须与 Python 主路径一致。

## 结果口径

- `SKILLHUB_FREE_PRECHECK_OK`：只证明免费预检路径可用。
- `STRUCTURE_MANIFEST_READY`：只证明本地清单已生成，且 `uploaded=false`。
- `DOCTOR_OK`：Python 主路径的完整环境诊断通过。
- `SKILLPAY_APPLIED`：方案已经在 Python 主路径本地应用。

任何低层结果都不能代替付费交付、本地 HTML、平台审核、公开可发现或外部购买回执。

## 失败策略

- 两条免费预检路径都不可用：停止并报告运行环境不足。
- Shell 回退成功但 Python 3.10+ 缺失：允许保存免费预检案例；进入上传、支付或完整构建前停止。
- 不自动安装 Python，不下载远程脚本，不用临时 HTTP 请求绕过本地状态锁。

## 官方规则刷新入口

- SkillHub Pay Skill 改造：`https://skillhub.cn/tutorials#agent-pay-upgrade`
- SkillHub Pay Skill 发布与案例：`https://skillhub.cn/tutorials#agent-pay-publish`
- SkillHub 商户改造最佳实践：`https://skillhub.cn/tutorials#agent-pay-best-practice`

平台规则和沙箱能力会变化，每次提交前都需要重新核对官方页面与真实案例沙箱。
