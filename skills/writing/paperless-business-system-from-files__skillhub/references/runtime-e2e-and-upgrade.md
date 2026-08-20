# 2.7.0 运行 E2E 与安全升级契约

## 1. 真实运行测试

统一入口：

```bash
python scripts/run_skill.py test --project <项目目录>
```

测试必须在隔离副本中执行，禁止直接拿用户真实数据库做新增、修改、删除或恢复演练。测试器会创建全新 `data/`，覆盖：

1. 启动服务并访问 `/health`；
2. 读取随机首次管理员凭据并完成登录；
3. 对第一个可用业务对象做新增、修改、删除；
4. 如果存在数字字段，验证非法文本不能写入；
5. CSV 导入必须先逐行校验和预览，再确认提交；
6. XLSX 导出必须生成有效 Office ZIP；
7. 使用本项目 shutdown token 安全停止服务；
8. 执行 SQLite 备份、恢复与 `PRAGMA integrity_check`。

测试通过后更新：

- `TEST_REPORT.md`；
- `DELIVERY_STATUS.json.tests_executed`；
- `DELIVERY_STATUS.json.runtime_e2e_verified=true`；
- `runtime_e2e_test_environment`、`runtime_e2e_last_run`；
- `project_scoped_safe_stop_verified=true`。

如果当前 Python 环境没有 Flask/openpyxl，测试器返回 `PB802`。这属于“运行环境未就绪”，不能把测试标记为已通过。应先按项目 `requirements.txt` 准备运行环境，或使用 `--python` 指向已经安装依赖的项目虚拟环境。

## 2. strict 验收语义

2.7.0 起：

```bash
python scripts/run_skill.py validate --project <项目目录> --strict
```

除了静态交付结构外，还要求：

- `tests_executed` 非空；
- `runtime_e2e_verified=true`；
- 已记录运行测试环境；
- `TEST_REPORT.md` 不再是“未执行”。

因此“文件结构完整”与“系统真正可用”被明确分开。

## 3. 安全升级

统一入口：

```bash
python scripts/run_skill.py upgrade \
  --project <旧项目目录> \
  --spec <新system-spec.json> \
  --output <升级副本目录>
```

输出变化分三类：

- `safe_additive`：新增业务对象、新增字段；
- `review_required`：标签、required、唯一键、公式、权限、工作流、候选关系变化；
- `breaking`：删除对象、删除字段、字段改类型。

默认发现 `breaking` 就停止自动升级。`--allow-breaking` 仅表示允许创建待人工处理的升级副本，不表示破坏性迁移已经安全完成。

升级永远创建副本，保留 `system-spec.before-upgrade.json`，并输出 `UPGRADE_DIFF_REPORT.md` / `upgrade-diff.json`。运行时迁移只自动补齐新增表和新增字段；删除/改类型需要显式迁移设计。

升级后必须重新执行 `test` 和 `validate --strict`，之前版本的运行测试证据不可直接继承。
