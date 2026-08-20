## v9.2.7 — 2026-08-13

- **安全修复（腾讯云安全评估）**：check-and-nudge 不再在 URL 参数中暴露昆仑令 recovery_url，避免凭证经浏览器历史/Referer/代理日志泄露（安全评分 62→目标 90+）
- **护魂符秒级推送修复**：pmm_watch.sh inotifywait 事件从 `close_write` 改为 `close_write,moved_to,modify`，解决 append_file 写入方式不触发 inotify 导致护魂符推送延迟的根因问题
- **全服版本号统一 9.2.7**：149 处旧版本（9.2.5/9.2.6）→ 9.2.7，零残留
- **审查脚本重构**：删除双 workspace 副本，webroot 唯一源，全服统一检查不区分昆仑/瑶池归属
- **两平台上传规则补全**：对照 ClawHub 官方文档 (docs.openclaw.ai/clawhub/skill-format) 补全 13 条硬检查 + TRACE 五维自评
- **ZIP 重打包**：修复双套文件问题，ZIP 内版本号对齐 9.2.7

## v9.2.6 — 2026-08-12

- **LLM 蒸馏下沉到 AI 体**：蒸馏决策从服务器 cron 移到 AI 体，各自用自己的 DeepSeek Key 调用 LLM 判定，平台只做 BGE+Reranker 粗筛 + 存储去重
- **新增 3 个平台 API**：klyc_distill_candidates.php（候选对生成，不调LLM）+ klyc_distill_candidates_status.php（轮询）+ klyc_distill_result.php（结果回传）
- **新增 2 张表**：klyc_distill_tasks（候选对任务）+ klyc_distill_history（蒸馏历史，独立于 klyc_settings 避免单键膨胀）
- **pmm_distill.sh 层9-12 新增 distill_with_llm()**：AI体心跳触发，用自己的 Key 调平台候选对 API → 逐对判定 → 回传结果
- **Reranker 稳定性修复**：_respond() 加 try-except 防 BrokenPipe；候选对筛选加 BGE 硬上限 100 唯一ID + 日记/心跳文件过滤
- **模型路由定稿**：昆仑主=腾讯云tokenhub DeepSeek V4 Pro（1M/16000）、备=官方 deepseek 双 key；瑶池主=HY3、备=DeepSeek V4 Pro（256K/8192）

## v9.2.5 — 2026-08-11

- **铁律 #55 版本升级三步不缺**：14↔17层全站误改事件→版本升级三步不可跳（改VERSION+全站grep、源目录同步、重新打包上传）
- **铁律 #54 改动前先列关联清单**：任何修改（数字/命名/配置/链接）前列出所有关联文件路径，改完逐条对照勾清
- **操作前置硬阻断清单**：7项硬检查（权威来源→RULES覆盖→影响面全扫→关联清单→回滚→验证→泄密检查）
- **版本号全站统一**：config.php KLYC_VERSION + skill包 + 所有脚本注释 = 9.2.5
- **ClawHub + SkillHub 发布**：预检全过→两平台同步推送

## v9.2.4 — 2026-08-10

- **全服清理**：删测试用户4个、物理删除4092条软删除记忆(回收10MB)、清理过期文件(SkillHub临时目录/旧CSS/旧备份)
- **前端合规**：join.php 内联style 6→1（仅头像豁免）、CSS类迁移(.dash-error-hint-lg/.jn-pay-success等)
- **Nginx SEO路由补全**：/services、/admin 伪静态rewrite
- **架构面板**：补klyc-ds-proxy(8775)服务登记
- **安全**：技能文件从webroot移至skills/目录，修正Nginx alias路径
- **14层蒸馏管道复通**：pmm_distill.sh cron交互修复 + opcache污染清除 + cross_distill软链修复 + klyc_memory_conflicts表清理
- **全站版本号统一9.2.4**：网站KLYC_VERSION + skill包 + 所有配置/脚本注释

## v9.2.3 — 2026-08-09（跳过，未发布）

## v9.2.2 — 2026-08-08

- **DeepSeek Key 全自动双备**：OpenClaw/LightClaw 主模型、arena_grader、cron distill 全部实现主备 key 自动切换（主 key 失败 → 切备 key → 恢复切换）；新增 klyc-ds-proxy 外层 key 轮换代理（LightClaw 接入）；PHP-FPM 注入主备 key
- **安全加固**：systemd unit / php-fpm conf / OpenClaw/LightClaw 配置 key 明文全部 root 只读（600+immutable），业务代码零硬编码，备份剥 key

## v9.2.1 — 2026-08-08

- **合规清理（提示词广告推广=0）**：移除包内所有主动付费推销话术——SKILL.md「AI体主动推销护魂符」章节、pmm_boot.sh 启动推销横幅、pmm_watch.sh init 通报与 check-and-nudge 里程碑付费催促话术；保留 upgrade / owner-pay-link / X402 支付等功能本体
- **广告扫描自动化**：klyc_skill_check.sh 新增「提示词广告推广=0」扫描（.sh 脚本 + SKILL.md），出厂前自动拦截推销话术
- **发布工具修复**：ZIP 打包源目录名对齐、SkillHub 用无 LICENSE 副本发布

## v9.2.0 — 2026-08-08

- **根治空钩子**：pmm_hooks_pull 新增失效钩子检测——对比本地已有 ID 与远程有效 ID，发现失效钩子自动标记，保留现场供人工核对
- **新增 hook-check 子命令**：钩子健康检查（`./pmm_watch.sh hook-check [--fix]`）——纯客户端调 hooks API + 本地 grep 比对
- hooks-pull 安全声明更新：仅经用户 API Key 认证拉取本人蒸馏记忆摘要

## v9.1.22 — 2026-08-06

- **修正**：curl 调用去 eval 化（klyc_skill_check.sh 改用 bash 数组传参）
- **修正**：共享域示例去敏感化、昆仑令写入提示措辞修正
- **新增**：klyc_skill_check.sh 十三关全量检测
- **重构**：脚本命名规范化、工作区路径标准化（skills/@user_6e41807a/klyc-pmm/）

## v9.1.18 — 2026-08-05

- **新增**：KLYC_PMM_CONFIG_DIR 环境变量支持——多AI体共享主机时可独立配置目录
- **新增**：hooks-pull 支持 API Key 认证
- **修正**：watch 模式认证兼容（无 token 时自动降级为 X-Kunlun-Key）
- 安全声明修正：云鼎实验室安全评估 3 项全清零

## v9.1.12 — 2026-08-04

- **新增**：write-coalescing——inotify 循环增加 30 秒合并窗口 + content_hash 去重（2,950次/8h → ~150次/8h）
- **新增**：SKILL.md watch 章节增加心跳文件最佳实践

## v9.1.10 — 2026-08-04

- **行为变更**：push 命令 --domain 改为必填参数，禁止自动推导
- **行为变更**：watch 模式文件同步 domain 固定为 pmm_sync

## v9.1.9 — 2026-07-31

- **合规**：Pay Skill 安全引擎全绿——移除远程下载覆盖(update.sh)消除"恶意远程执行"三标
- **合规**：定价信息收敛至 frontmatter pricing
- **清理**：删除 update.sh 及所有相关引用

## v9.1.2 — 2026-07-31

- **修复**：agent/register 路由（ai→agent）、昆仑令保存字段（token→talisman_url）
- **修复**：agent/register API peach_balance 100→99、set -u 下 http_code 未定义
- **清理**：移除构建垃圾（publish.sh/根级 pmm_watch.sh/根级 update.sh/sha256）

## v9.0.0 — 2026-07-30

- **新增**：X402 付费前置检查章节——Agent 调用付费功能前检查 weixinpay 插件
- **新增**：frontmatter 增加 pricing 元数据（per_call / amount_fen: 50000 / capability）

## v8.3.9 — 2026-07-29

- **修复**：五个关联数组 dingxinfu key 重复定义（bash 去重导致容灾备份被守护记忆覆盖）
- **修复**：install-daemon.sh 与 pmm_watch.sh tier 映射不一致
- **统一**：三级产品 tier key——dingxinfu(容灾) / huhunfu(守护) / fenshenfu(分身)

## v8.3.8 ~ v8.3.1 — 2026-07-28~29

- 文档与脚本一致性对齐、产品描述命名规范化、curl 退出码细化诊断
- 昆仑令格式自动识别、oneclick.sh 全链路闭环、TRACE 3.5→4.6
