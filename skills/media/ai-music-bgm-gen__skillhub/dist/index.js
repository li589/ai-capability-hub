/**
 * SkillPay CLI 入口。
 *
 * 极简手写参数解析，零第三方依赖——这个 CLI 只有三个命令，引入 commander 不划算。
 */
import { createFromLyrics, createInstrumental, createSong, getResult, } from "./client.js";
import { formatError, formatOkHint, formatPaymentRequired } from "./output.js";
const USAGE = `AI 音乐生成 Pay Skill（¥1/次，每次出 2 首候选歌，无需注册登录）

用法:
  skillpay song --brief "写一首轻快的夏日流行歌" [--title "夏天"] [--style 流行,轻快]
  skillpay lyrics --lyrics "<歌词>" --title "标题" [--style 民谣]
  skillpay bgm --brief "适合产品发布会开场的电子 BGM" [--title "开场"]
  skillpay status              查询生成结果（免费，创建后约 1-3 分钟轮询）

选项:
  --order <out_trade_no>   显式指定订单号（仅当本机无法保存订单号时需要）
`;
function parseArgs(argv) {
    const out = {};
    for (let i = 0; i < argv.length; i += 1) {
        const token = argv[i];
        if (!token?.startsWith("--"))
            continue;
        const key = token.slice(2);
        const next = argv[i + 1];
        if (next && !next.startsWith("--")) {
            out[key] = next;
            i += 1;
        }
        else {
            out[key] = "true";
        }
    }
    return out;
}
function splitStyles(value) {
    if (!value)
        return [];
    return value
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean);
}
function report(result) {
    if (result.kind === "payment_required") {
        console.log(formatPaymentRequired({
            paymentCode: result.paymentCode,
            outTradeNo: result.outTradeNo,
            stored: result.stored,
        }));
        return 2;
    }
    if (result.kind === "error") {
        console.error(formatError(result.code, result.message));
        return 1;
    }
    console.log(JSON.stringify(result.data, null, 2));
    const hint = formatOkHint(result.data);
    if (hint)
        console.log(hint);
    return 0;
}
async function run() {
    const [command, ...rest] = process.argv.slice(2);
    const args = parseArgs(rest);
    const order = args["order"];
    try {
        switch (command) {
            case "song": {
                if (!args["brief"]) {
                    console.error(formatError("usage_error", "缺少 --brief"));
                    return 1;
                }
                return report(await createSong({ brief: args["brief"], title: args["title"], styleTags: splitStyles(args["style"]) }, order));
            }
            case "lyrics": {
                if (!args["lyrics"] || !args["title"]) {
                    console.error(formatError("usage_error", "缺少 --lyrics 或 --title"));
                    return 1;
                }
                return report(await createFromLyrics({ lyrics: args["lyrics"], title: args["title"], styleTags: splitStyles(args["style"]) }, order));
            }
            case "bgm": {
                if (!args["brief"]) {
                    console.error(formatError("usage_error", "缺少 --brief"));
                    return 1;
                }
                return report(await createInstrumental({ brief: args["brief"], title: args["title"], styleTags: splitStyles(args["style"]) }, order));
            }
            case "status": {
                return report(await getResult(order));
            }
            default:
                console.log(USAGE);
                return command ? 1 : 0;
        }
    }
    catch (error) {
        console.error(formatError("network_error", error instanceof Error ? error.message : String(error)));
        return 1;
    }
}
process.exitCode = await run();
//# sourceMappingURL=index.js.map