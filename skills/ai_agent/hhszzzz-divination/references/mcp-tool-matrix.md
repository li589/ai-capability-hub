# MCP Tool Matrix

## Core Tools

| Tool                   | Purpose             | Required Input                                               | Optional Input                                                                         | Key Output Fields                                                                                       | Handler Source                                           |
| ---------------------- | ------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `bazi_calculate`       | 八字命盘计算        | `gender`, `birthYear`, `birthMonth`, `birthDay`, `birthHour` | `birthMinute`, `calendarType`(solar/lunar), `isLeapMonth`, `birthPlace`                | `dayMaster`, `fourPillars`(含藏干/十神/纳音/地势/神煞/空亡), `relations`, `kongWang`                    | `packages/mcp-core/src/handlers/bazi.ts`                 |
| `bazi_pillars_resolve` | 四柱反查公/农历候选 | `yearPillar`, `monthPillar`, `dayPillar`, `hourPillar`       | —                                                                                      | `count`, `candidates[]`(含 solarText/lunarText/nextCall)                                                | `packages/mcp-core/src/handlers/bazi-pillars-resolve.ts` |
| `ziwei_calculate`      | 紫微斗数排盘        | `gender`, `birthYear`, `birthMonth`, `birthDay`, `birthHour` | `birthMinute`, `calendarType`(solar/lunar), `isLeapMonth`                              | `palaces[]`(含主星/辅星/四化/亮度), `decadalList[]`, `soul`, `body`, `fiveElement`                      | `packages/mcp-core/src/handlers/ziwei.ts`                |
| `liuyao_analyze`       | 六爻断卦分析        | `question`, `yongShenTargets`                                | `method`(auto/select), `hexagramName`, `changedHexagramName`, `date`, `seed`           | `fullYaos[]`, `yongShen[]`, `shenSystemByYongShen[]`, `fuShen[]`, `timeRecommendations[]`, `warnings[]` | `packages/mcp-core/src/handlers/liuyao.ts`               |
| `tarot_draw`           | 塔罗抽牌            | —                                                            | `spreadType`(single/three-card/love/celtic-cross), `question`, `allowReversed`, `seed` | `cards[]`(含 position/card/orientation/meaning), `spreadName`                                           | `packages/mcp-core/src/handlers/tarot.ts`                |
| `daily_fortune`        | 每日运势            | —                                                            | `dayMaster`, `birthYear`, `birthMonth`, `birthDay`, `birthHour`, `date`                | `dayInfo`(干支), `tenGod`, `almanac`(含宜忌/冲煞/节气/吉凶神)                                           | `packages/mcp-core/src/handlers/fortune.ts`              |
| `dayun_calculate`      | 大运计算            | `gender`, `birthYear`, `birthMonth`, `birthDay`, `birthHour` | `birthMinute`, `calendarType`(solar/lunar), `isLeapMonth`                              | `list[]`(含 startYear/ganZhi/stem/branch/tenGod/branchTenGod/hiddenStems/naYin/diShi/shenSha)           | `packages/mcp-core/src/handlers/liunian.ts`              |

## Practical Notes

- **Input Validation**: Always validate `gender` (male/female) and date ranges before calling tools.
- **Calendar Type**: 默认 `solar`（阳历）。用户给出农历时必须设置 `calendarType: 'lunar'`，若为闰月需同时设置 `isLeapMonth: true`。
- **Ambiguity Handling**: Prefer `bazi_pillars_resolve` first when user gives only four pillars and no calendar date. Use `nextCall` in response to chain into `bazi_calculate`.
- **Reproducibility**: Use `seed` in Liuyao/Tarot/Fortune when reproducible output is needed for debugging or consistent dialogue.
- **Error Handling**: 工具抛错时，根据错误信息判断：输入校验错误应提示用户补正；内部错误应告知"计算暂不可用"。
- **Tool Chaining**: `bazi_pillars_resolve` → `bazi_calculate` 是标准链式调用；`bazi_calculate` + `dayun_calculate` 覆盖完整八字+大运。
- **Schema Source**: All tool definitions in `packages/mcp-core/src/tools.ts`. When tool schema changes, update this matrix and workflows.
