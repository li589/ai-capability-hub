# 故障排查

优先从这三步开始：

```bash
vefaas --version
vefaas doctor
vefaas --debug <command>
```

## 常见问题

| 问题 | 恢复动作 |
|---|---|
| CLI 不存在或版本太旧 | `npm i -g @volcengine/vefaas-cli@latest`；要求 0.2.7+ |
| 鉴权失败 | `vefaas login --check`，再 `vefaas login --sso` 或 AK/SK 登录 |
| SSO 登录后提示无权操作 APIG、CR | 建议切换 AK/SK 登录 |
| 不确定是账号、网络还是项目问题 | `vefaas doctor` |
| 框架检测错误 | `vefaas --debug inspect`，再覆盖 build/start/port |
| 本地构建失败 | 先本地复现构建命令，安装依赖，确认 Node >= 18 |
| 新应用部署找不到 gateway | `vefaas gateway list --first`；为空则让用户提供或创建网关 |
| 当前目录 link 到错误资源 | `vefaas config list`，再重新 link |
| 高阶命令不覆盖目标操作 | 查看 `vefaas api <Action> --help` |
