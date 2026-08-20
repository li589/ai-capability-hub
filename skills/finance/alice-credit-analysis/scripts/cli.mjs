#!/usr/bin/env node
import { createHash } from "node:crypto";
import { once } from "node:events";
import { mkdirSync, openSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { ensureWindowsUtf8Stdio, writeUtf8BomToFd } from "./encoding.js";
import { resolveDataDir } from "./dataDir.js";

// 稳定 CLI 入口：把参数转给 request.js（真正的请求 + SSE 解析在那边）。
// 必须 await 子进程退出，否则在某些 Windows / IDE 终端下父进程会先结束，
// 看到的只有 status/headers，后续流式正文被截断。

// 必须在所有 console 输出之前执行：在 Windows 沙箱 / 控制台中把代码页切到 UTF-8,
// 与 Node.js stdout 默认 UTF-8 写入对齐，避免中文提示文案被 GBK 等编码解码出现乱码。
ensureWindowsUtf8Stdio();

const requestEntrypoint = new URL("./request.js", import.meta.url);

// --- promptHash 计算 -------------------------------------------------------
// 必须与 request.js 的 computePromptHash 保持完全一致：
//   SHA256("信用分析::" + 标准化prompt)
// 这样 --detach 模式下 cli.mjs 算出的 hash 与 request.js 写入 ~/.wind-alice/tasks.json
// 的 promptHash 严格相等；调用方可以仅根据 prompt 推算出对应的日志文件名。
// 如果未来 request.js 改动 hash 算法，这里必须同步修改。
//
// 说明：本 CLI **不会**在 prompt 文本里拼接「使用「XX」技能：」前缀（直接透传用户原话），
// 但 promptHash 仍然按 namespace 前缀哈希，避免与其它 skill 的同 prompt 记录混淆。
const ALICE_SKILL_NAME_ZH = "信用分析";
function normalizePromptForHash(prompt) {
  return String(prompt ?? "").trim().replace(/\s+/g, " ");
}
function computePromptHash(prompt) {
  const normalized = normalizePromptForHash(prompt);
  const namespaced = `${ALICE_SKILL_NAME_ZH}::${normalized}`;
  return createHash("sha256").update(namespaced, "utf8").digest("hex");
}

// --- 参数解析 --------------------------------------------------------------
const rawArgs = process.argv.slice(2);
/** 部分 Agent 终端会把 JS undefined 字面量拼进 argv，过滤以免误解析。 */
const args = rawArgs.filter((a) => a !== "undefined" && a !== "null");

/**
 * 只读 / 配置类子命令清单：cli.mjs 透传给 request.js 即可，**不要**打"2-15 分钟"等
 * 暗示主路径的提示文案，避免误导用户以为子命令也会跑那么久。
 * 必须与 request.js 中的 SUBCOMMANDS 保持一致。
 */
const SUBCOMMANDS = new Set([
  "apikey-set",
  "apikey-get",
  "apikey-clear",
  "status",
  "check-conflict",
]);
const headArg = args[0];
const isSubcommand = typeof headArg === "string" && SUBCOMMANDS.has(headArg);

function readOptionValue(argv, longName, shortName) {
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === longName || a === shortName) {
      return argv[i + 1];
    }
    if (longName && a.startsWith(longName + "=")) {
      return a.slice(longName.length + 1);
    }
  }
  return undefined;
}

const isHelp = args.length === 0 || args.includes("--help") || args.includes("-h");
if (isHelp) {
  console.log(
    [
      'alice-credit-analysis — 调用万得 Alice Agent「信用分析」，对各类企业 / 机构主体（城投 / 国企 / 民企 / 上市公司 / 金融机构 / 房地产 / 债券发行人 等）做系统化信用研究（主体信用、行业风险、财务健康度、现金流质量、评级对标、违约概率建模），用户原话直接透传给服务端',
      "",
      "Usage:",
      "  alice-credit-analysis --prompt <QUESTION> [--download-dir <DIR>] [--new]",
      "  alice-credit-analysis --prompt <QUESTION> --detach                        # 后台跑：立刻返回 PID 与日志路径，进程脱离当前会话",
      "  alice-credit-analysis --prompt <QUESTION> --no-wait                       # 沙箱推荐：CLI 内部自旋直到完成（默认）",
      "  alice-credit-analysis --prompt <QUESTION> --no-wait --once                # 单次探针：几秒内返回（脚本/调试）",
      "  alice-credit-analysis --prompt <QUESTION> --no-wait \\",
      "      --watch-interval 60 --watch-absolute-max 3600                       # 自定义轮询节奏",
      "  alice-credit-analysis status --prompt <QUESTION>                        # 查询落盘路径（不访问服务端）",
      "  alice-credit-analysis check-conflict --prompt <QUESTION>                # [已废弃] 主调用 --no-wait 已内置去重，无需预检",
      "  alice-credit-analysis apikey-set <KEY>",
      "  alice-credit-analysis apikey-get",
      "  alice-credit-analysis apikey-clear",
      "  alice-credit-analysis --help",
      "",
      "Windows UTF-8:",
      "  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/aca.ps1 --prompt <Q> --no-wait",
      "  管道捕获 live 中文乱码时，读 stdout 的 ALICE_SESSION_LOG= 路径（UTF-8 BOM 会话日志）。",
      "",
      "Options:",
      '  --prompt,       -p <QUESTION>   用户提问，例如"帮我分析一下宁德时代的信用资质？万科有没有短线机会？"（必填）',
      "  --download-dir, -d <DIR>        指定下载文件保存目录；不传则保存到用户 Downloads 文件夹。仅影响报告附件落盘，不影响 tasks.json 等状态（状态固定走 ~/.wind-alice/）",
      "  --new                     用户明确要求并行新建：清除该 prompt 全部本地记录后新建（须先经用户确认）",
      "  --context-id <ID>         【推荐续接】从上一轮 DONE 行的 contextId= 取值原样传回，CLI 直接复用该",
      "                                  contextId、不读不写共享文件，同宿主多会话各自带 ID、物理上不串号。",
      "                                  第一轮或切话题时不传。",
      "  --continue-session              （兼容，已不推荐）旧式：读共享 current-session[.<scope>].json 复用上次",
      "                                  contextId；共享文件按宿主（非按会话）切分，同宿主多会话会串号。改用 --context-id。",
      "  --new-session                   显式强制新建会话上下文（不复用上次 contextId）；",
      "                                  完全无关的新话题 / 用户明说「换个话题」时加，避免无关上文污染。",
      "  --session-scope <ID>            会话隔离标识（宿主 Agent 传入自己的会话标识，如 \"cursor\" / \"trae:chat-abc\"）；",
      "                                  未传则走默认全局 current-session.json（多宿主共享）。传入后按宿主隔离：",
      "                                  Cursor 里的续接不会误复用 Trae 的 contextId，反之亦然。可用环境变量",
      "                                  WIND_ALICE_SESSION_SCOPE 统一设置（命令行 --session-scope 优先）。",
      "  --detach                        启动后台子进程跑完整任务，stdout/stderr 重定向到独立日志文件，",
      "                                  父进程立即退出（PID 与日志路径打印到 stdout）。专为 Trae /",
      "                                  Cursor 等会强制结束长任务进程的 IDE 环境设计；启动后用 --no-wait",
      "                                  轮询服务端状态、或直接 tail 日志文件查看进度即可。",
      "  --no-wait                       CLI 内部自旋 tasks/get 直到完成（沙箱 / Trae 推荐）；全程默认 60min，",
      "                                  每轮 30min 自动续轮，Agent 禁止外层连发多条 CLI",
      "  --once                          （需配合 --no-wait）单次探针；禁止 Agent 用此模式手工循环",
      "  --watch,        -w              已废弃：--no-wait 默认即内部自旋",
      "  --watch-interval <SEC>          两次 probe 间隔（默认 60s）",
      "  --watch-timeout  <SEC>          每轮自旋上限（默认 1800s）；到点 CLI 自动续下一轮",
      "  --watch-absolute-max <SEC>      单次进程全程上限（默认 3600s）；仅触顶才 exit=4",
      "  --no-strict                     关闭 strict 模式（默认开启）；未输出 ALICE_CREDIT_ANALYSIS_DONE 时",
      "                                  不会把 exitCode=0 强制改成 6（仅脚本 / 调试场景使用）",
      "  --help,         -h              查看帮助",
      "",
      "API Key 子命令（KEY 是裸值不要加引号；只支持写入 ~/.wind-alice/config.env）:",
      "  apikey-set <KEY>            写入 / 覆盖 API Key（自动迁移历史版本的无后缀 config）",
      "  apikey-get                  查看当前 Key 状态（脱敏回显）",
      "  apikey-clear                清除当前 Key（同时清理历史版本的无后缀 config）",
      "",
      "下载目录解析顺序（优先级从高到低）:",
      "  ① --download-dir / -d 传入的目录（不存在则自动创建）",
      "  ② 未指定时，回落到用户 Downloads 文件夹（Windows: %USERPROFILE%\\Downloads；macOS/Linux: ~/Downloads，不存在则自动创建）",
      "",
      "任务调度（默认不新建并行任务）:",
      "  默认：同 prompt 有 running → 自动续接；本地 completed → 自动提交新分析；无记录 → 新建。",
      "  --new：用户明确要求并行新建时清除本地记录后新建（须先经用户确认）。",
      "",
      "多轮会话上下文（contextId 复用，--context-id 显式续接）:",
      "  默认：每次 CLI 调用视为全新会话，contextId 每次新生成；避免跨 Agent / 跨话题 / 跨用户的 context 污染。",
      "        每次 taskId 始终新生成，一条 prompt = 一个新任务。",
      "  --context-id <ID>：【推荐】从上一轮 DONE 行的 contextId= 取值原样传回，CLI 直接复用、不读不写共享",
      "                    文件，同宿主多会话各自带 ID、物理上不串号。第一轮或切话题时不传。",
      "  --continue-session：（兼容，已不推荐）旧式读共享 current-session[.<scope>].json 复用 contextId；",
      "                      同宿主多会话会串号。改用 --context-id。",
      "  --new-session：显式强制新建会话上下文（不复用上次 contextId）；完全无关新话题时加。",
      "  --session-scope <ID>：（兼容，已不推荐）旧式宿主隔离标识；--context-id 已按会话隔离，通常无需传。",
      "                       亦可用环境变量 WIND_ALICE_SESSION_SCOPE 统一设置（命令行优先）。",
      "  会话状态文件：",
      "    默认（未传 scope）：%USERPROFILE%\\.wind-alice\\current-session.json（Windows）/ ~/.wind-alice/current-session.json（*nix）",
      "    传入 --session-scope <id>：同目录下 current-session.<id>.json（按宿主隔离）",
      "",
      "--detach 模式日志位置（按 promptHash 独立、同 prompt 重跑会覆盖、不累积）:",
      "  Windows：     %USERPROFILE%\\.wind-alice\\logs\\<promptHash[:12]>.log / .err",
      "  macOS / Linux：~/.wind-alice/logs/<promptHash[:12]>.log / .err",
      "",
      "退出码:",
      "  0   成功：必定伴随 stdout 含 ALICE_CREDIT_ANALYSIS_DONE 行（含 promptHash= / reportFullFile=；Agent 判定任务完成的唯一确定信号）",
      "  1   一般失败 / 任务终态为 failed",
      "  2   参数错误 / Key 缺失（含 --watch 与 --no-wait 未同时给等不合法组合）",
      "  4   --no-wait 专用：已达全程自旋上限（默认 60min）仍未完成；Agent 再执行**一次**相同 --no-wait 续接",
      "  5   --no-wait 专用：--once 模式下本地无任务记录（默认内部自旋会自动提交）",
      "  6   strict 模式兜底：进程退出但未输出 ALICE_CREDIT_ANALYSIS_DONE（通常表示进程被沙箱终止），",
      "      任务可能仍在服务端跑，请用相同 prompt 加 --no-wait 续接；不要当成失败也不要当成功",
      "  11  [已废弃] check-conflict 子命令专用：检测到同/相似 prompt 的 running 任务",
      "  12  [已废弃] check-conflict 子命令专用：24h 内已有相似 completed 可重放",
      "  77  status 子命令专用：无此 prompt 本地记录但存在相似已完成任务；禁止扫 download/ 误读",
      "  75  服务端临时拒绝（并发上限 / 服务繁忙 / 积分不足）；禁止立即重试",
      "  76  重复提交防护命中（10 分钟内已有相似 prompt 的 running 任务），疑似 Agent 换 prompt 重试；",
      "      请改用相同 prompt 加 --no-wait 续接，或在用户明确需要时加 --new",
      "  78  环境受限，无法保存任务状态（未开启完全访问权限）；未向服务端发请求、不扣积分；",
      "      请在工具中开启完全访问权限后重试",
      "",
      "Examples (PowerShell):",
      "  # 注意：PowerShell 5.x 不支持 bash 的 &&；用分号 ; 或 node 绝对路径",
      '  Set-Location "D:\\path\\to\\alice-credit-analysis"; node scripts/cli.mjs --prompt "帮我分析一下宁德时代的信用资质？万科有没有短线机会？"',
      '  node "D:\\path\\to\\alice-credit-analysis\\scripts\\cli.mjs" --prompt "万科的违约概率和财务健康度怎么样？"',
      '  alice-credit-analysis -p "某城投平台的信用风险如何评估？"',
      '  alice-credit-analysis -p "对比 A 公司和 B 公司的信用资质" --download-dir "D:\\reports\\credit"',
      '  alice-credit-analysis -p "重新分析宁德时代信用资质" --new',
      '  alice-credit-analysis -p "这家公司的现金流质量和偿债能力如何？" --no-wait              # 沙箱：CLI 内部自旋直到完成',
      '  alice-credit-analysis -p "某房地产企业的违约风险有多大？" --no-wait --once     # 脚本：单次探针',
      '  alice-credit-analysis -p "帮我分析一下宁德时代的信用资质" --detach           # 后台跑，立即返回，IDE 杀终端也不影响',
      "",
      "API Key 配置位置（仅此路径，不支持环境变量 / skill 目录内 config.json）:",
      "  macOS / Linux：~/.wind-alice/config.env",
      "  Windows：     %USERPROFILE%\\.wind-alice\\config.env",
      "  内容（dotenv）：WIND_API_KEY=<你的KEY>",
      "  历史版本的无后缀 config 仍可读取，apikey-set 会自动迁移到 config.env 并删除老文件。",
      "",
      "获取 API Key：https://alice.wind.com.cn/settings?tab=account",
      "（万得 Alice → 左下角头像 → 「设置」→「账户」标签页 → 复制 API Key）",
    ].join("\n"),
  );
  process.exitCode = args.length === 0 ? 2 : 0;
} else {
  const nodePath = process.execPath;
  const { spawn } = await import("node:child_process");

  const isNoWait = args.includes("--no-wait");
  const isOnce = args.includes("--once");
  const isDetach = args.includes("--detach");

  // --detach 与 --no-wait 互斥：detach 是"丢出去后台跑"，no-wait 是"单次探针查"，
  // 两者并用语义不明确。
  if (isDetach && isNoWait) {
    console.error("[CLI] --detach 与 --no-wait 互斥：detach 是后台跑完整任务，no-wait 是单次探针。");
    process.exitCode = 2;
  } else if (isDetach) {
    const prompt = readOptionValue(args, "--prompt", "-p");
    if (!prompt || typeof prompt !== "string" || !prompt.trim()) {
      console.error("[CLI] --detach 模式必须显式提供 --prompt / -p（非空字符串）。");
      process.exitCode = 2;
    } else {
      // 透传给 request.js 的参数：去掉 --detach（其它选项原样保留）
      const childArgs = args.filter((a) => a !== "--detach");

      // 日志目录：resolveDataDir("logs") -> ~/.wind-alice/logs/<promptHash[:12]>.log / .err
      // （跨会话稳定，与 tasks.json / results 同一根目录，便于一次性清理）。
      // 文件名只取 hash 前 12 位：足够避免不同 prompt 碰撞，又便于人眼比对。
      const logDir = resolveDataDir("logs");
      const dataRoot = resolveDataDir();
      try {
        mkdirSync(logDir, { recursive: true });
      } catch (err) {
        console.error(`[CLI] 无法创建日志目录 ${logDir}: ${err.message}`);
        process.exitCode = 1;
        process.exit();
      }

      const hashShort = computePromptHash(prompt).slice(0, 12);
      const promptHash = computePromptHash(prompt);
      const logFile = join(logDir, `${hashShort}.log`);
      const errFile = join(logDir, `${hashShort}.err`);

      // 用 'w' 而非 'a'：同一 prompt 重跑直接覆盖旧日志，避免无限累积；
      // 历史输出本来就由服务端 tasks.json + ~/.wind-alice/results/<hash>.md 兜底，
      // 不依赖日志做归档。
      let outFd;
      let errFd;
      try {
        outFd = openSync(logFile, "w");
        errFd = openSync(errFile, "w");
        // PowerShell Get-Content 默认按 GBK 读无 BOM 的 UTF-8 会乱码；写入 BOM 便于识别
        writeUtf8BomToFd(outFd);
        writeUtf8BomToFd(errFd);
      } catch (err) {
        console.error(`[CLI] 无法打开日志文件: ${err.message}`);
        process.exitCode = 1;
        process.exit();
      }

      // detached: true + stdio: ['ignore', fd, fd] + child.unref()
      // 在 Windows / *nix 上都能让父进程立即退出而子进程继续在后台跑。
      // windowsHide: true 避免在 Windows 上闪一下控制台窗口。
      const child = spawn(
        nodePath,
        [fileURLToPath(requestEntrypoint), ...childArgs],
        {
          detached: true,
          stdio: ["ignore", outFd, errFd],
          windowsHide: true,
          env: { ...process.env, ALICE_DETACH_LOG: logFile },
        },
      );

      child.once("error", (err) => {
        console.error(`[CLI] 后台子进程启动失败: ${err.message}`);
        process.exitCode = 1;
      });

      // 让父进程不再持有子进程引用，从而可以立即退出
      child.unref();

      console.log(
        [
          "[CLI] --detach 已启动后台子进程，可立即关闭本终端 / 切换会话。",
          "[CLI] 分析在后台进行中；可用 --no-wait 续接查看进度。",
          `  pid       = ${child.pid ?? "(unknown)"}`,
          `  prompt    = ${prompt}`,
          `  PROMPT_HASH=${promptHash}`,
          `  hash[:12] = ${hashShort}`,
          `  stdout    = ${logFile}`,
          `  stderr    = ${errFile}`,
          "",
          "查看进度（任选其一）：",
          `  · PowerShell:  Get-Content -Path "${logFile}" -Encoding UTF8 -Tail 200 -Wait`,
          `  · *nix:        tail -n 200 -f "${logFile}"`,
          `  · 轮询结果:    alice-credit-analysis -p "${prompt}" --no-wait`,
          `  · 查落盘路径:  alice-credit-analysis status -p "${prompt}"`,
          "",
          "完成后报告位置：",
          `  · 兜底摘要:    ${join(dataRoot, "results", `${promptHash}.md`)}`,
          `  · 任务状态:    ${join(dataRoot, "tasks.json")}`,
          "  · 本地附件:    CLI 输出的 REPORT_FULL_FILE=（静默落盘，Agent 不要展示给用户）",
        ].join("\n"),
      );
      // 不 await child；进程会在控制权返回事件循环后自然退出（child 已 unref）。
    }
  } else {
    // 子命令（apikey-* / status / check-conflict）只是只读 / 配置操作，几秒内返回；
    // 不应套用主路径的"2-15 分钟"提示文案，否则会误导用户。
    if (isSubcommand) {
      // 静默透传，子命令本身的输出已经足够清晰。
    } else if (isNoWait && !isOnce) {
      console.error(
        "[CLI] --no-wait 内部自旋：默认每 60s 探针、每轮最长 30min、全程最长 60min；到轮次上限 CLI 自动续轮，Agent 勿外层连发。",
      );
    } else if (isNoWait && isOnce) {
      console.error(
        "[CLI] --no-wait --once 单次探针：几秒内返回；禁止 Agent 用此模式在外层循环。",
      );
    } else {
      console.error(
        "[CLI] 子进程即将启动；父进程将阻塞等待直至任务完成（通常 2-15 分钟），请勿提前结束本命令。",
      );
      console.error(
        "[CLI] 若在 Trae / 沙箱终端被强制结束，请 `--detach` 后台跑，再用 `--no-wait` 轮询（CLI 内部自旋，无需 --watch）。",
      );
    }
    const child = spawn(
      nodePath,
      [fileURLToPath(requestEntrypoint), ...args],
      { stdio: "inherit" },
    );
    child.once("error", (err) => {
      console.error("spawn failed:", err.message);
      process.exitCode = 1;
    });
    const [code, signal] = await once(child, "exit");
    process.exitCode = signal ? 1 : (code ?? 1);
  }
}
