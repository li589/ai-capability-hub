# API2 权益后台

## 1. 原则

- API2 是 3.0 在线后台主通道。
- 现行连接器是补充/兼容通道。
- 本地账本和 `.fbs` 是离线兜底，不上传书稿正文。

## 2. 最小字段

```json
{
  "bindingId": "wb-xxx",
  "traceId": "trace-xxx",
  "skillVersion": "3.0.0",
  "connectorPackageVersion": "1.3.x",
  "benefitSource": "api2|connector|local_cache|offline_default",
  "memberTier": "T0|T1|T2|T3|unknown",
  "creditsState": "available|insufficient|offline_cache|unverified",
  "scenePackId": "whitepaper",
  "localLedgerBalance": 180
}
```

## 3. 优先级

1. `api2`
2. `connector`
3. `local_cache`
4. `offline_default`

只要不是 `api2`，都必须在结果卡或事件里显式标注来源。

## 4. 现有脚本映射

- `scripts/wecom/verify-member.mjs`
- `scripts/wecom/lib/entitlement.mjs`
- `scripts/event-writer.mjs`
- `scripts/fbs-connector-bridge.mjs`

## 5. 脚本模式互通

- 不把 `wecom-cli` 当作 3.0 提审联调的唯一前提。
- Skill 脚本与服务侧通讯默认优先直连 API2；连接器只是补充/兼容通道。
- 同 binding 的在线互通优先走：
  1. `skill_whoami`
  2. `fbs_scene_pack_query`
  3. `skill_consume`
- 推荐入口：

```bash
node scripts/fbs-service-bridge.mjs flow --with-consume --json
```

连接器兼容路径：

```bash
node scripts/fbs-connector-bridge.mjs --transport connector-config flow --with-consume --json
```

服务侧直连适合真机联调、提审证据采集和服务侧排障；连接器路径适合复用宿主现有配置做兼容验证。

## 6. 不上传内容

- 书稿正文
- 完整个人资料
- 未授权腾讯文档正文
