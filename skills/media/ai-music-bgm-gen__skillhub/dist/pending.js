/**
 * 待支付订单的本地存储。
 *
 * SkillPay 没有登录、没有 API Key，`out_trade_no` 就是这台机器上唯一的身份凭证：
 * 402 时存下，支付完成后重试时回传，服务端凭它解析出用户身份。
 *
 * 它是 bearer 凭证——谁持有谁就能以该身份调用——故文件权限 0600。
 *
 * 所有读写都不抛异常：沙箱可能没有 HOME、或文件系统只读。写不进去时，402 的提示
 * 里仍会回显 out_trade_no，用户可以让 Agent 用 --order 显式带上。
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
const DIR_NAME = ".skillpay";
const FILE_NAME = "pending-order.json";
function getDir() {
    const override = process.env.SKILLPAY_CONFIG_DIR?.trim();
    return override ? path.resolve(override) : path.join(os.homedir(), DIR_NAME);
}
export function getStorePath() {
    return path.join(getDir(), FILE_NAME);
}
export function readOrderNo() {
    try {
        const raw = fs.readFileSync(getStorePath(), "utf8");
        const parsed = JSON.parse(raw);
        const value = typeof parsed.out_trade_no === "string" ? parsed.out_trade_no.trim() : "";
        return value || undefined;
    }
    catch {
        // 不存在、损坏、无权限——一律当作没存过，让流程走回 402 重新下单
        return undefined;
    }
}
export function saveOrderNo(outTradeNo) {
    try {
        const dir = getDir();
        fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
        const file = getStorePath();
        fs.writeFileSync(file, `${JSON.stringify({ out_trade_no: outTradeNo }, null, 2)}\n`, {
            encoding: "utf8",
            mode: 0o600,
        });
        fs.chmodSync(file, 0o600);
    }
    catch {
        // 只读文件系统 / 无 HOME：静默降级，调用方会在 402 提示里回显 out_trade_no
    }
}
export function clearOrderNo() {
    try {
        fs.rmSync(getStorePath());
    }
    catch {
        // 本就不存在
    }
}
//# sourceMappingURL=pending.js.map