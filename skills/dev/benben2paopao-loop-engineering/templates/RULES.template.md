# RULES.md — {{TASK_TITLE}} 项目规范与约束

> 这是 LOOP 的「技能(Skills)」要素的精简版。
> 任何对 `{{PROJECT_PATH}}` 的修改都必须遵守这里的规则。

---

## 一、技术栈

{{PROJECT_LANG}}

项目根目录:`{{PROJECT_PATH}}`

---

## 二、命令清单(LOOP 在每轮中可以使用)

```bash
# 安装依赖(初次或更新依赖后才跑)
{{INSTALL_CMD}}

# 核心验收命令 ← LOOP 的成功信号源
{{VERIFY_CMD}}

{{EXTRA_COMMANDS}}
```

> ⚠️ 不要执行未在此列出的命令。如果 LOOP 觉得需要新命令,先在 STATE.md 写出意图,等用户批准。

---

## 三、核心约定(LOOP 改代码必须遵守)

{{CORE_CONVENTIONS}}

---

## 四、禁止事项(触碰即写 `[BLOCKED]` 等人工授权)

{{FORBIDDEN_DETAILS}}

通用禁区(无论项目类型都适用):
- 🚫 不得提交/推送 Git(除非用户明确允许)
- 🚫 不得发布到 npm / PyPI / Docker Hub 等公开仓库
- 🚫 不得调用外部网络 API(除非任务要求且用户批准)
- 🚫 不得在源码中硬编码 API key、密码、token
- 🚫 不得为了让验收命令通过而修改验收命令本身或测试断言
- 🚫 不得删除已有的测试文件(可以新增、可以修复,不能删)
- 🚫 不得用 `try/except: pass` 或 `try { } catch { }` 吞异常蒙混过关

---

## 五、需要"问我一下"的灰色地带

> 这些不是禁止,但 LOOP 必须先在 STATE.md 写出意图、停下来等用户批准。

- 🤔 新增任何依赖包
- 🤔 修改公共接口签名(影响调用方)
- 🤔 修改超过 200 行的文件
- 🤔 重命名/移动文件
- 🤔 修改配置文件(`.eslintrc`、`tsconfig.json`、`pyproject.toml` 等)

{{EXTRA_GRAY_AREA}}

---

## 六、项目特有的"踩过的坑"(口口相传的知识)

{{CRITICAL_NOTES}}

> 这一节是 LOOP 产出代码"像不像你团队写的"的关键。
> 跑通后再想到的坑,继续往这里加。
