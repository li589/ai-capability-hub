# 语音智能报工助手 — MES 语音报工 Skill

工人在 WorkBuddy 对话中通过文字/语音输入产品、工序、数量（及可选的报废、设备），自动匹配派工清单并执行开工/报工。

## 目录结构

```
语音智能报工助手/
├── SKILL.md           # Skill 定义（入口）
├── scripts/
│   ├── report_tool.py # 参数化 CLI 执行工具
│   └── config.json    # ★ 服务器配置（IP 在这里改）
└── README.md          # 本说明
```

## ★ IP 在哪里配置？

**`scripts/config.json`** 文件：

```json
{
  "server": {
    "host": "",   // ← 改这里：服务器 IP（首次使用填写，不预制）
    "port": 20201             // ← 改这里：端口
  },
  "apis": {
    "queryMoList": "/open-api/bp/AIGetMoList",
    "startProduction": "/open-api/bp/AI_start_processing",
    "endProduction": "/open-api/bp/AI_end_processing",
    "queryReasonList": "/open-api/bp/AIGetCollData"
  }
}
```

只改 `host` / `port` 即可，其他不用动。`report_tool.py` 会自动读取同目录的 `config.json`。

## 使用

```bash
# 开工
python scripts/report_tool.py --action start  --product 产品 --process 工序 --qty 数量 --operator 工号

# 报工（可带报废）
python scripts/report_tool.py --action report --product 产品 --process 工序 --qty 数量 --operator 工号 [--scrap 报废数 --reason 原因名]
```

详细规则见 `SKILL.md`。

## 部署要求

- Python 3.8+（只需标准库，无需 pip 安装）
- 能访问 `config.json` 中配置的 MES 服务器 IP:端口
- Skill 目录放到 WorkBuddy 的 `skills/` 目录下（用户级 `~/.workbuddy/skills/` 或项目级 `.workbuddy/skills/`）
