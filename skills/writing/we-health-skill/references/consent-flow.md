# 用户同意流程详细说明

> 本文件由 SKILL.md 主流程按需引用，不可独立执行。
> 条款链接：https://wy.guahao.com/agreement

---

## 未同意时的处理流程

1. **展示官方声明与条款确认**（必须原样输出，话术见 SKILL.md「同意确认」章节）
2. **用户输入「查看全文」**：浏览器打开 `https://wy.guahao.com/agreement`，完成后重新询问
3. **用户接受**（回复「同意」或直接提出健康问题）：执行 `consent.py accept`，继续查询
4. **用户拒绝**：执行 `consent.py decline`，告知无法使用服务，结束对话

---

## 状态管理命令

| 命令 | 作用 | 返回 `consented` |
|------|------|:---:|
| `consent.py check` | 检查是否已同意 | `true` / `false` |
| `consent.py accept` | 标记同意 | `true` |
| `consent.py decline` | 撤销同意 | `false` |
| `consent.py status` | 查看本地状态 | `true` / `false` |

同意状态持久化在 `~/.wy-health-skill/consent.json`，跨会话有效，文件权限 `0600`。
