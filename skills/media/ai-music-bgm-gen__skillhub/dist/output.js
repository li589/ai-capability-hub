/**
 * 面向 Agent 的结构化输出。
 *
 * 支付触发输出必须是 SkillHub「升级为 Pay Skill」规定的标准 CLI 格式
 * （`{"WeixinPay-Required": ..., "prompt": ...}`）——平台审核按这个标识判定
 * Skill 是否接入了支付服务，自定义格式会被判「缺少必要的支付服务」拒审。
 * 普通错误仍用 `[error] code=xxx` 标签，让 Agent 按标签决策。
 */
const PAY_PROMPT_BASE = "本次使用微信支付，请将 WeixinPay-Required 的值作为 paymentCode 交给 " +
    "weixinpay_pay，以向用户申请支付授权。";
/**
 * 402 支付触发。
 *
 * 刻意【不输出二维码】：对话内出二维码在多数 Agent 环境渲染不出来（本项目早期的
 * 扫码登录会话成功率只有 18%）。SkillPay 只面向支持 weixinpay_pay 的环境——
 * 环境不支持时用免费版 Skill，而不是在这里退回扫码。
 */
export function formatPaymentRequired(info) {
    const block = {
        "WeixinPay-Required": info.paymentCode,
    };
    if (info.stored) {
        // 订单号已在本地，Agent 重试原命令即可，不必理解支付细节
        block["prompt"] = PAY_PROMPT_BASE + "支付完成后重试刚才的命令即可（无需附加参数）。";
    }
    else {
        // 写盘失败（只读文件系统 / 无 HOME）：降级为让 Agent 自己记住并回传
        block["prompt"] =
            PAY_PROMPT_BASE +
                `支付完成后重试命令并附加 --order ${info.outTradeNo}（本机无法保存订单号，需显式带上）。`;
        block["out_trade_no"] = info.outTradeNo;
    }
    return JSON.stringify(block, null, 2);
}
export function formatError(code, message) {
    return `[error] code=${code} ${message}`;
}
/**
 * 成功输出后的行动指引。生成是异步的（创建立即返回，歌 1-3 分钟后才好），
 * 不给指引 Agent 就会重跑创建命令「查状态」——那会撞额度不足甚至二次付款。
 */
export function formatOkHint(data) {
    // 创建响应：{project_id, status}
    if (data?.project_id && data?.status && data.status !== "completed") {
        return ("[hint] 已开始生成，通常需 1-3 分钟。请记住 project_id 与本机订单号；" +
            "稍后运行 status 命令免费查询结果（node <安装目录>/bin/skillpay.js status）。" +
            "生成完成前【不要】重复运行创建命令——那会开启新的付费生成。");
    }
    // status 查询响应：{order_status, project}
    if (data?.order_status) {
        const project = data.project;
        if (!project)
            return null; // data.message 已带指引
        if (project.status === "completed") {
            return "[hint] 生成完成：songs[].audio_url 为音频直链。请把两首候选都呈现给用户。";
        }
        if (project.status === "failed") {
            return "[hint] 生成失败，额度已自动退回。可直接重试创建命令（不重复扣费）。";
        }
        return "[hint] 仍在生成中（通常 1-3 分钟），请约 30 秒后再次运行 status 命令。";
    }
    return null;
}
//# sourceMappingURL=output.js.map