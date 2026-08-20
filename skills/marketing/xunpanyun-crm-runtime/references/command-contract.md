# 命令与凭证约定

- 凭证仅从 `CODEBUDDY_PLUGIN_OPTION_XUNPANYUN_CLIENT_ID` 和 `CODEBUDDY_PLUGIN_OPTION_XUNPANYUN_CLIENT_SECRET` 读取。
- 标准输出使用JSON；密钥和Token不得输出。
- `AUTH_REQUIRED` 表示需要用户进入插件配置，不得在对话中索取密钥。
- 查询覆盖：`fields <object>`、`query <object>`，支持dataId、可重复filter、and/or、expression、排序、分组、公私海标识和分页。
- 通用写入覆盖：lead、customer、contact、opportunity、followUpRecord的objFieldData create/update。
- 专用写入覆盖：公私海pool assign/transfer/return、商机salesStageStatus、订单及明细orderData；全部强制`--dry-run`、明确确认和`--confirm`。商机/订单同步回查，公私海等待系统通知。
- 公私海接口code=10000只表示“已受理，待系统通知确认”；不得输出“已完成”。
- private transfer不暴露transferRelatedObj及关联对象保留参数，直至官方枚举明确。
- 第一版复用现有询盘云Python客户端；正式发布前验证WorkBuddy运行环境提供Python 3与HTTPS网络访问。
