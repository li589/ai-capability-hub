# BookWriter 3.0 能力边界

> 这是 3.0 的薄适配层。目标不是重写 2.1.2，而是在不删老能力的前提下，把报告驱动的 P0/P1 和 API2 后台约束落到更短的入口文档。

## 1. 兼容升级原则

- 保留 2.1.2 的生命周期、场景包、恢复卡、离线降级、乐包、会员和 Skill+脚本+CLI 实现方式。
- 3.0 的“精简”仅指入口重排、上下文分层和渐进披露，不代表删除旧能力。
- 书稿正文继续保存在本地磁盘；API2、连接器和事件账本只接收元数据、阶段、摘要、权益状态和授权引用。

## 2. 3.0 优先级

- P0-A：成稿后处理。
  证据：排版/导出返工 8.5%，去 AI 味返工 7.8%，改写返工 10.4%。
  对应入口：[`../02-workflows/post-draft-pack.md`](../02-workflows/post-draft-pack.md)
- P0-B：续写感知与进度卡。
  证据：85.9% 用户只活跃 1 天，89% 会话只有 1 轮，多轮产出率高于单轮。
  对应入口：[`../01-lifecycle/resume-progress-card.md`](../01-lifecycle/resume-progress-card.md)
- P1：长文档通用生产与素材整理。
  对应入口：[`../02-workflows/material-activation.md`](../02-workflows/material-activation.md)
- P2：Windows CLI/JSON 稳定性与标杆域 playbook。
  对应入口：[`../05-playbooks/academic-playbook.md`](../05-playbooks/academic-playbook.md)

## 3. 宿主与后台分工

| 层 | 3.0 职责 | 不负责 |
| --- | --- | --- |
| Skill | 路由、新建/继续/后处理、脚本说明、文件真值、恢复卡 | 专家人设、完整商业状态机 |
| API2 | 在线后台主通道：身份、会员层级、乐包/权益状态、事件账本、offer | 持有书稿正文 |
| 现行连接器 | API2 不可直达或宿主需兼容时的补充通道 | 重写乐包/会员规则 |
| 本地账本 / `.fbs` | 离线累计、恢复、质检、导出、事件兜底 | 伪造服务端确认 |

## 4. 继续阅读

- 完整规范：[`../01-core/skill-full-spec.md`](../01-core/skill-full-spec.md)
- 快速路由：[`../01-core/intake-and-routing.md`](../01-core/intake-and-routing.md)
- 乐包说明：[`../05-ops/credits-guide.md`](../05-ops/credits-guide.md)
- WorkBuddy 宿主集成：[`../06-plugin/workbuddy-host-integration.md`](../06-plugin/workbuddy-host-integration.md)
