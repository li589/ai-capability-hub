/**
 * SkillPay HTTP 客户端。
 *
 * 零登录：不带 API Key。身份完全由 `X-SkillPay-Order`（本地存的 out_trade_no）承载，
 * 由本模块自动附带——Agent 只管重试原命令，不必理解支付细节。
 *
 * 用 Node 18+ 内置 fetch，无第三方依赖。
 */
import { readOrderNo, saveOrderNo } from "./pending.js";
const DEFAULT_BASE_URL = "https://music.68zysm.cn/api/v3/skillpay";
function getBaseUrl() {
    return (process.env.SKILLPAY_API_BASE_URL?.trim() || DEFAULT_BASE_URL).replace(/\/+$/, "");
}
function buildHeaders(explicitOrderNo) {
    const headers = { "Content-Type": "application/json" };
    // --order 优先于本地存储：沙箱写不了盘时，Agent 会显式带上
    const orderNo = explicitOrderNo?.trim() || readOrderNo();
    if (orderNo) {
        headers["X-SkillPay-Order"] = orderNo;
    }
    return headers;
}
/** 402 响应：把 out_trade_no 存下来供重试，并取出 payment_code。 */
function handlePaymentRequired(body, headerCode) {
    // Header 优先（标准化识别），Body 兜底（兼容只读正文的 Agent）
    const paymentCode = headerCode || body?.WeixinPay?.["WeixinPay-Required"] || "";
    const outTradeNo = body?.data?.out_trade_no || "";
    saveOrderNo(outTradeNo);
    // 存不进去（只读文件系统 / 无 HOME）时，要让 Agent 显式回传，故此处校验实际结果
    const stored = readOrderNo() === outTradeNo;
    return { kind: "payment_required", paymentCode, outTradeNo, stored };
}
async function post(path, payload, orderNo) {
    const response = await fetch(`${getBaseUrl()}${path}`, {
        method: "POST",
        headers: buildHeaders(orderNo),
        body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 402) {
        return handlePaymentRequired(body, response.headers.get("WeixinPay-Required"));
    }
    if (response.status >= 400) {
        return {
            kind: "error",
            code: String(body?.code || response.status),
            message: String(body?.message || "请求失败"),
        };
    }
    return { kind: "ok", data: body?.data ?? body };
}
export async function createSong(input, orderNo) {
    return post("/songs", { brief: input.brief, title: input.title, style_tags: input.styleTags ?? [] }, orderNo);
}
export async function createFromLyrics(input, orderNo) {
    return post("/songs/from-lyrics", { lyrics: input.lyrics, title: input.title, style_tags: input.styleTags ?? [] }, orderNo);
}
export async function createInstrumental(input, orderNo) {
    return post("/instrumentals", { brief: input.brief, title: input.title, style_tags: input.styleTags ?? [] }, orderNo);
}
/** 免费查询订单的生成结果（幂等）。生成是异步的，创建后靠它轮询取歌。 */
export async function getResult(orderNo) {
    const effective = orderNo?.trim() || readOrderNo();
    if (!effective) {
        return {
            kind: "error",
            code: "usage_error",
            message: "本机没有已保存的订单号，请用 --order <订单号> 指定",
        };
    }
    const response = await fetch(`${getBaseUrl()}/orders/${effective}/result`);
    const body = await response.json().catch(() => ({}));
    if (response.status >= 400) {
        return {
            kind: "error",
            code: String(body?.code || response.status),
            message: String(body?.message || "请求失败"),
        };
    }
    return { kind: "ok", data: body?.data ?? body };
}
//# sourceMappingURL=client.js.map