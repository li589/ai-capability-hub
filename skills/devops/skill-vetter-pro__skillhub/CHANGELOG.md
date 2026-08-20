# Changelog - skill-vetter-pro

## [1.0.0] - 2026-05-21

### 初始版本

基于 skill-vetter-optimized 的完整重构，新增：

- **子会话推送保障**：强制 sessions_yield 绑定，解决推送失败问题
- **六阶段 SOP**：接收 → 依赖检查 → 子会话审查 → 裁决 → 安装前校验 → 记录
- **分层执行策略**：基础审查必选，扩展维度按需启用
- **清单文件独立存储**：manifest 存放在 records/ 目录，与 skill 目录分离
- **全面工具集**：
  - skill_vet.py（AST 扫描器，21/21 自检通过）
  - skill_integrity_checker.py（SHA256 哈希链）
  - dependency_cve_checker.py（OSV API CVE 检查）
  - skill_behavior_monitor.py（strace 行为监控）
  - scanner_self_test.py（扫描器自检）

### 技术指标

| 指标 | 数值 |
|------|------|
| skill_vet.py 恶意样本检出率 | 13/13（100%） |
| skill_vet.py 良性样本误报率 | 0/8（0%） |
| 自检通过率 | 21/21（100%） |
| 支持依赖格式 | 6 种（requirements.txt / package.json / Gemfile / go.mod / composer.json / Cargo.toml） |
