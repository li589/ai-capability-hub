#!/usr/bin/env node
//
// chat.js — 通过妙问流式 API 进行 AI 问答（一站式脚本）
//
// 用法: node chat.js '<JSON_BODY>'
//
// 参数:
//   <JSON_BODY> — 完整的请求体 JSON 字符串，必须包含 "query" 字段，
//                 可选包含 "attachments" 字段（上传预审图片/素材时使用）。
//
// 示例:
//   普通问答:   node chat.js '{"query":"腾讯广告开户流程"}'
//   带附件预审: node chat.js '{"query":"帮我预审这张素材","attachments":[{"content_type":"IMAGE","url":"https://..."}]}'
//
// 功能:
//   - 自动检查 Token 文件是否存在
//   - 自动读取 Token 并发起流式 API 请求（SSE）
//   - 实时解析流式事件并输出执行进度
//   - 最终输出 Markdown 格式的完整回答
//   - 根据不同错误场景输出明确的提示信息
//
// Token 存储位置: ~/.MIAOWEN_ACCESS_TOKEN
//
// 退出码说明:
//   0 — 请求成功，结果已输出
//   1 — 参数错误（未提供 JSON 或 JSON 格式不合法）
//   2 — Token 文件不存在，需要用户首次获取 Token
//   3 — Token 文件为空，需要用户重新设置 Token
//   4 — API 返回错误（含 Token 失效、权限错误、版本过期等，由调用方根据输出内容判断）
//   5 — 网络请求失败（超时等）
//
// 输出格式:
//   脚本输出分为以下类型的行：
//   1. [PROGRESS]     — 实时进度信息（执行期间应同步给用户以缓解等待）
//   2. [RESULT]       — 紧随其后的所有内容为最终 Markdown 格式回答（内容未超阈值时）
//   3. [RESULT_FILE]  — 结果超长时，完整内容已写入本地文件；其后给出文件路径与预览，
//                       调用方须读取该文件获取完整内容（含全部超长媒体 URL）
//   4. [TASK_INFO]    — JSON 格式的任务元信息
//   5. [VERSION_EXPIRED] — SKILL 版本过期，需按提示更新后重试
//

const fs = require("fs");
const path = require("path");
const os = require("os");

const API_URL =
  process.env.MIAOWEN_CHAT_API_URL ||
  "https://ad.qq.com/ai/gw/ai_customer_service/v1/open_api/stream_chat";
const TOKEN_FILE = path.join(os.homedir(), ".MIAOWEN_ACCESS_TOKEN");
const REQUEST_TIMEOUT_MS = 10 * 60 * 1000; // 10 分钟超时（流式接口处理时间较长）
const SKILL_NAME = "tencent-ads-assistant";
const SKILL_VERSION = "1.2.0";
const VERSION_EXPIRED_CODE = 140209;

// 结果超长自动落盘阈值（字符数）。超过时把完整结果写入本地文件，stdout 仅输出摘要 + 文件路径，
// 避免创意灵感/素材审核等含大量超长媒体 URL 的结果被命令输出捕获层截断（导致素材链接丢失）。
// 可通过环境变量 MIAOWEN_RESULT_INLINE_LIMIT 覆盖。
const RESULT_INLINE_LIMIT = Number(
  process.env.MIAOWEN_RESULT_INLINE_LIMIT || 8000
);

// ============ 参数检查 ============

const jsonBody = process.argv[2];

if (!jsonBody) {
  console.error("[ERROR] 未提供请求体参数");
  console.error("用法: node chat.js '<JSON_BODY>'");
  console.error("示例: node chat.js '{\"query\":\"腾讯广告开户流程\"}'");
  process.exit(1);
}

// 校验 JSON 格式并确认包含 query 字段
let requestBody;
try {
  requestBody = JSON.parse(jsonBody);
} catch {
  console.error("[ERROR] 请求体不是合法的 JSON 格式");
  console.error("请检查 JSON 字符串是否正确。");
  process.exit(1);
}

if (!requestBody || typeof requestBody.query !== "string" || !requestBody.query) {
  console.error("[ERROR] 请求体缺少必填的 query 字段");
  process.exit(1);
}

// ============ Token 检查 ============

if (!fs.existsSync(TOKEN_FILE)) {
  console.log(`[TOKEN_NOT_FOUND] Token 文件不存在: ${TOKEN_FILE}`);
  console.log("");
  console.log("您需要先获取妙问 API KEY 才能使用问答服务。");
  console.log("");
  console.log("获取步骤：");
  console.log("  1. 打开妙问官网 https://miaowen.qq.com/ 并登录");
  console.log("  2. 左侧导航栏点击【Skill 社区】");
  console.log(
    "  3. 在弹出页面中可以看到「你的 API KEY」，格式为 sk-mw-xxxxx"
  );
  console.log(
    "  4. 点击 API KEY 右侧的「刷新」按钮获取 Token，点击「复制」按钮复制"
  );
  console.log("");
  console.log("获取 Token 后请粘贴给我，我会帮您自动保存。");
  process.exit(2);
}

const token = fs.readFileSync(TOKEN_FILE, "utf-8").trim();

if (!token) {
  console.log(`[TOKEN_EMPTY] Token 文件为空: ${TOKEN_FILE}`);
  console.log("");
  console.log("Token 文件存在但内容为空，请重新获取 Token。");
  console.log("");
  console.log("获取步骤：");
  console.log("  1. 打开妙问官网 https://miaowen.qq.com/ 并登录");
  console.log("  2. 左侧导航栏点击【Skill 社区】");
  console.log(
    "  3. 点击 API KEY 右侧的「刷新」按钮获取新 Token，点击「复制」按钮复制"
  );
  console.log("");
  console.log("获取 Token 后请粘贴给我，我会帮您重新保存。");
  process.exit(3);
}

// ============ SSE 事件解析器 ============

/**
 * 安全解析 JSON，失败时返回 null
 */
function safeJsonParse(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

/**
 * 处理单个 SSE 事件的 JSON 数据
 */
function handleEvent(jsonData, state) {
  const parsed = safeJsonParse(jsonData);
  if (!parsed) return;

  const eventType = parsed.event_type;
  const data = parsed.data;
  const thinkSeconds = parsed.think_seconds;

  // 版本过期检测：部分事件可能携带 code 字段
  if (parsed.code === VERSION_EXPIRED_CODE) {
    state.versionExpired = true;
    state.versionMessage = parsed.message || "";
  }

  switch (eventType) {
    case "STREAM_BEGIN":
      state.streamStarted = true;
      console.log("[PROGRESS] 🚀 已连接妙问智能营销助手，正在分析您的问题...");
      break;

    case "LOADING":
      // LOADING 会在每个步骤前重复推送，仅首次展示，避免刷屏
      if (!state.loadingShown) {
        state.loadingShown = true;
        console.log("[PROGRESS] ⏳ 正在加载分析引擎...");
      }
      break;

    case "THINK": {
      // THINK 事件有两种格式：
      // 1. data 是结构化对象（含 data_type）：步骤指令、步骤结果等
      // 2. data 是纯字符串：流式思考文本片段，逐字/逐词推送
      if (data && typeof data === "object") {
        const dataType = data.data_type;

        switch (dataType) {
          case "QUESTION_EVALUATION": {
            const evalQuestion = data.question || "";
            if (evalQuestion) {
              console.log(`[PROGRESS] 🔍 问题理解完成：${evalQuestion}`);
            } else {
              console.log("[PROGRESS] 🔍 已完成问题理解与分析规划");
            }
            if (thinkSeconds)
              console.log(`[PROGRESS] ⏱️  已用时 ${thinkSeconds} 秒`);
            break;
          }

          case "STEP_INSTRUCT": {
            const round = data.round;
            const instruct = data.instruct || "";
            if (round !== undefined) {
              state.totalSteps = Math.max(state.totalSteps, round);
            }
            // 去重：同一步骤指令可能被重复推送（实测 round 相同、instruct 相同），仅展示一次
            const instructKey = `${round}::${instruct}`;
            if (state.printedInstructs.has(instructKey)) break;
            state.printedInstructs.add(instructKey);

            if (instruct) {
              console.log(`[PROGRESS] 📋 步骤${round}：${instruct}`);
            } else if (round !== undefined) {
              console.log(`[PROGRESS] 📋 正在执行分析步骤 ${round}...`);
            }
            if (thinkSeconds)
              console.log(`[PROGRESS] ⏱️  已用时 ${thinkSeconds} 秒`);
            break;
          }

          case "STEP_RESULT": {
            const round = data.round;
            const result = (data.result || "").trim();
            const tools = data.tools || [];

            // 同一 round 的结果可能被重复推送（先 result-only，后补 tools，或反之）。
            // 记录该轮最完整的一版结果（取最长），用于流中断兜底与去重展示。
            if (result && round !== undefined) {
              const prev = state.roundResults[round] || "";
              if (result.length >= prev.length) state.roundResults[round] = result;
            }

            // 仅在该 round 首次完成时计入进度并展示，避免重复推送导致进度虚高（如 4/3 步）
            const firstTime =
              round === undefined ? true : !state.completedRounds.has(round);
            if (round !== undefined) state.completedRounds.add(round);
            state.completedSteps = round === undefined
              ? state.completedSteps + 1
              : state.completedRounds.size;

            if (!firstTime) break;

            if (round !== undefined) {
              // 工具名去重（实测同一步骤可能重复列出同名工具）
              const toolNames = [
                ...new Set(tools.map((t) => t.tool_name).filter(Boolean)),
              ].join("、");
              if (toolNames) {
                console.log(
                  `[PROGRESS] ✅ 步骤${round}已完成（调用：${toolNames}）`
                );
              } else {
                console.log(`[PROGRESS] ✅ 步骤${round}已完成`);
              }
            }

            if (result) {
              const oneLine = result.replace(/\s*\n\s*/g, " ");
              const summary =
                oneLine.length > 70 ? oneLine.slice(0, 70) + "..." : oneLine;
              console.log(`[PROGRESS] 💡 阶段结论：${summary}`);
            }

            if (state.totalSteps > 0) {
              const done = Math.min(state.completedSteps, state.totalSteps);
              console.log(
                `[PROGRESS] 📊 总进度：${done}/${state.totalSteps} 步完成`
              );
            }
            if (thinkSeconds)
              console.log(`[PROGRESS] ⏱️  已用时 ${thinkSeconds} 秒`);
            break;
          }

          case "SUMMARY":
            console.log(
              "[PROGRESS] 📝 所有分析步骤已完成，正在整合生成最终回答..."
            );
            if (thinkSeconds)
              console.log(`[PROGRESS] ⏱️  总用时 ${thinkSeconds} 秒`);
            break;
        }
      } else if (typeof data === "string") {
        // V2 协议：通用智能助手多轮迭代时逐字/逐词推送的思考文本片段。
        // 累积到 thinkBuffer，仅在首次出现时打一条进度，避免逐 token 刷屏。
        if (!state.thinking) {
          state.thinking = true;
          console.log("[PROGRESS] 🤔 正在推理分析中...");
        }
        state.thinkBuffer = (state.thinkBuffer || "") + data;
      }
      break;
    }

    case "MARKDOWN_DATA":
      // V2 协议：最终 Markdown 回答。可能分多段「穿插」推送（loading + markdown 交替），
      // 因此按段累积拼接（而非覆盖），既兼容单段整片，也兼容多段输出。
      if (typeof data === "string" && data) {
        state.markdownContent += data;
      }
      if (!state.answering) {
        state.answering = true;
        console.log("[PROGRESS] 📝 正在生成回答...");
      } else {
        // 长回答会被拆成数百至数千个字符片段逐字推送，仅靠一句"正在生成"会长时间静默。
        // 按字数里程碑（每 ~800 字）披露一次生成进度，缓解等待焦虑又不至于刷屏。
        const len = state.markdownContent.length;
        if (len - state.mdMilestone >= 800) {
          state.mdMilestone = len;
          console.log(`[PROGRESS] ✍️  回答持续输出中，已生成约 ${len} 字...`);
        }
      }
      break;

    case "MARKDOWN_OF_HTML":
      // V2 协议：HTML 卡片内嵌的流式 Markdown 片段，data.content 为增量文本。
      if (data && typeof data === "object" && typeof data.content === "string") {
        state.markdownContent += data.content;
      }
      break;

    case "HTML_DATA": {
      // V2 协议：结构化 HTML 卡片（诊断/账户分析/营销提案等）。CLI 无法渲染 HTML，
      // 这里尽力抽取关键文本（提示语、报告标题、报告正文、在线链接）拼入结果。
      if (data && typeof data === "object") {
        const tpl = parsed.html_template || data.html_template || "";
        const pieces = [
          data.tip,
          data.report_preface,
          data.report_title ? `### ${data.report_title}` : "",
          data.reply_content,
          data.report_content,
          data.report_content_stream,
          data.html_content,
          data.html_url ? `\n[在线查看完整内容](${data.html_url})` : "",
        ].filter((s) => typeof s === "string" && s.trim());
        if (pieces.length) {
          state.markdownContent += (state.markdownContent ? "\n\n" : "") + pieces.join("\n\n");
        }
        if (tpl) console.log(`[PROGRESS] 🧩 收到结构化卡片：${tpl}`);
      }
      break;
    }

    case "SEARCH": {
      // V2 协议：联网检索结果列表，转为 Markdown 引用列表追加到结果。
      if (Array.isArray(data) && data.length) {
        const refs = data
          .map((it) =>
            it && it.title
              ? `- [${it.title}](${it.url || ""})${it.site_name ? ` _(${it.site_name})_` : ""}`
              : ""
          )
          .filter(Boolean)
          .join("\n");
        if (refs) {
          state.markdownContent += `${state.markdownContent ? "\n\n" : ""}**参考来源：**\n${refs}`;
        }
        console.log("[PROGRESS] 🔎 已检索到相关资料");
      }
      break;
    }

    case "GUI": {
      // V2 协议：Agent 需要用户补充表单参数。CLI 场景把提示语作为结果透出，
      // 引导用户在下一轮 query 中以自然语言补充。
      let answerMsg = "";
      if (data && typeof data === "object") answerMsg = data.answer_msg || "";
      else if (typeof data === "string") answerMsg = data;
      if (answerMsg) {
        state.markdownContent += (state.markdownContent ? "\n\n" : "") + answerMsg;
      }
      state.needMoreInput = true;
      console.log("[PROGRESS] 📝 需要补充信息以继续");
      break;
    }

    case "SECURITY_TAG":
      // V2 协议：内容安全标签。需要撤回并替换时，用安全文案覆盖最终结果。
      if (data && typeof data === "object" && data.is_need_replace_content) {
        state.markdownContent = data.content_replace || state.markdownContent;
        state.securityReplaced = true;
        console.log("[PROGRESS] 🛡️ 内容安全校验已触发");
      }
      break;

    case "STREAM_END": {
      const agentInfo = parsed.agent_info;
      if (agentInfo) {
        state.taskInfo = JSON.stringify(agentInfo);
      }
      // STREAM_END 可能重复推送，仅展示一次
      if (!state.streamEnded) {
        state.streamEnded = true;
        console.log("[PROGRESS] ✨ 流式会话结束");
      }
      break;
    }

    // ERROR / ERROR_TIP：V2 中鉴权、业务等错误以 ERROR_TIP（Markdown 文案）返回。
    case "ERROR_TIP":
    case "ERROR": {
      state.hasError = true;
      let errorMsg = "未知错误";
      let errorCode;
      if (data && typeof data === "object") {
        errorMsg = data.message || data.tip || errorMsg;
        errorCode = data.code;
      } else if (typeof data === "string" && data) {
        errorMsg = data;
      }
      if (errorCode === VERSION_EXPIRED_CODE || parsed.code === VERSION_EXPIRED_CODE) {
        state.versionExpired = true;
        state.versionMessage = errorMsg;
      }
      state.errorMessage = errorMsg;
      console.log(`[PROGRESS] ❌ 服务返回提示: ${errorMsg}`);
      break;
    }
  }
}

/**
 * 流意外中断且未拿到最终 MARKDOWN_DATA 时，用已收到的步骤结果兜底降级。
 * 取最后一轮（通常最完整）的阶段结果作为主体。
 * 无任何可用内容时返回空字符串。
 */
function buildFallbackContent(state) {
  const rounds = Object.keys(state.roundResults)
    .map(Number)
    .sort((a, b) => a - b);
  if (rounds.length === 0) return "";
  const last = (state.roundResults[rounds[rounds.length - 1]] || "").trim();
  if (!last) return "";
  let md = `> ⚠️ 注意：本次回答在生成最终整合结论前连接中断，以下为已完成分析步骤的阶段性结果（供参考，可能不完整）。\n\n`;
  md += last;
  return md;
}

/**
 * 输出最终结果，自动处理「超长落盘」：
 *   - 内容未超阈值：直接 stdout 全量输出 [RESULT]（保持原有行为，向后兼容）。
 *   - 内容超阈值：完整写入本地文件，stdout 仅输出 [RESULT_FILE]（含预览片段 + 文件路径），
 *     由调用方读取该文件获取完整内容（含全部超长媒体 URL），规避命令输出被截断。
 * 写文件失败时降级为直接 stdout 输出，保证不丢内容。
 */
function emitResult(content, taskInfo) {
  const byteLen = Buffer.byteLength(content, "utf-8");

  if (content.length <= RESULT_INLINE_LIMIT) {
    console.log("");
    console.log("[RESULT]");
    console.log(content);
    if (taskInfo) {
      console.log("");
      console.log(`[TASK_INFO] ${taskInfo}`);
    }
    return;
  }

  // 超长：落盘
  const dir = path.join(os.tmpdir(), "miaowen_results");
  const ts = new Date()
    .toISOString()
    .replace(/[:.]/g, "-")
    .replace("T", "_")
    .slice(0, 19);
  const filePath = path.join(dir, `chat_result_${ts}_${process.pid}.md`);

  try {
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filePath, content, "utf-8");
  } catch (err) {
    // 落盘失败：降级为直接全量输出，宁可冒截断风险也不丢内容
    console.log("");
    console.log(
      `[PROGRESS] ⚠️ 结果超长且落盘失败（${err.message}），降级为直接输出`
    );
    console.log("[RESULT]");
    console.log(content);
    if (taskInfo) {
      console.log("");
      console.log(`[TASK_INFO] ${taskInfo}`);
    }
    return;
  }

  const preview = content.slice(0, 600);
  console.log("");
  console.log("[RESULT_FILE]");
  console.log(
    `本次结果较长（约 ${content.length} 字符 / ${byteLen} 字节），已完整写入本地文件以避免输出被截断、确保媒体链接完整。`
  );
  console.log(`完整结果文件：${filePath}`);
  console.log("");
  console.log("--- 结果预览（前 600 字符，完整内容请读取上述文件）---");
  console.log(preview);
  console.log("--- 预览结束 ---");
  if (taskInfo) {
    console.log("");
    console.log(`[TASK_INFO] ${taskInfo}`);
  }
}

// ============ 发起流式 API 请求 ============

async function main() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const state = {
    streamStarted: false,
    markdownContent: "",
    taskInfo: "",
    hasError: false,
    errorMessage: "",
    versionExpired: false,
    versionMessage: "",
    totalSteps: 0,
    completedSteps: 0,
    completedRounds: new Set(), // 已完成的步骤 round，用于去重计数
    printedInstructs: new Set(), // 已展示过的步骤指令，去重防刷屏
    roundResults: {}, // round -> 该轮最完整的阶段结果文本（兜底用）
    mdMilestone: 0, // 回答生成阶段已披露进度对应的字数
    loadingShown: false, // LOADING 是否已展示（去重）
    streamEnded: false, // STREAM_END 是否已展示（去重）
    thinkBuffer: "",
    thinking: false,
    answering: false,
    needMoreInput: false,
    securityReplaced: false,
  };

  let response;

  try {
    response = await fetch(API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "skill-name": SKILL_NAME,
        "skill-version": SKILL_VERSION,
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    printNetworkError(err);
    process.exit(5);
  }

  // 检查非流式错误响应
  if (!response.ok) {
    clearTimeout(timeout);
    const body = await response.text();
    const parsed = safeJsonParse(body);
    if (parsed && parsed.code === VERSION_EXPIRED_CODE) {
      console.log(`[VERSION_EXPIRED] ${parsed.message || "SKILL 版本过期，请按提示更新后重试"}`);
      process.exit(0);
    }
    console.error(`[API_ERROR] API 请求失败 (HTTP ${response.status})`);
    console.error("");
    if (body && body.trim()) {
      console.error(body);
    } else {
      // 流式接口出错时常返回空 body（如 HTTP 400/401/403），给出可操作的排查提示
      console.error("（服务端未返回错误详情）");
      console.error("");
      console.error("常见原因：");
      console.error("  - Token 失效或已过期 → 引导用户重新获取并保存 Token");
      console.error("  - Token 非「妙问开放 API」类型 → 确认 Token 来自妙问 Skill 社区页面");
      console.error("  - 账户无该能力权限 → 提示用户检查开通情况");
    }
    process.exit(4);
  }

  // ============ 流式读取与解析 ============

  try {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按行切分处理 SSE 数据
      const lines = buffer.split("\n");
      // 最后一个元素可能是不完整的行，保留在 buffer 中
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // SSE 格式：以 "data:" 开头
        if (trimmed.startsWith("data:")) {
          const jsonStr = trimmed.slice(5);
          if (jsonStr) {
            handleEvent(jsonStr, state);
          }
        }
      }
    }

    // 处理 buffer 中可能残留的最后一行
    if (buffer.trim()) {
      const trimmed = buffer.trim();
      if (trimmed.startsWith("data:")) {
        const jsonStr = trimmed.slice(5);
        if (jsonStr) {
          handleEvent(jsonStr, state);
        }
      }
    }

    clearTimeout(timeout);
  } catch (err) {
    clearTimeout(timeout);

    // 即使连接中断：已有 Markdown 或可兜底的步骤结果时，继续走结果输出（兜底降级）
    if (!state.markdownContent && buildFallbackContent(state) === "") {
      printNetworkError(err);
      process.exit(5);
    }
    state.streamInterrupted = true;
  }

  // ============ 输出最终结果 ============

  // 版本过期优先处理
  if (state.versionExpired) {
    console.log(
      `[VERSION_EXPIRED] ${state.versionMessage || "SKILL 版本过期，请按提示更新后重试"}`
    );
    process.exit(0);
  }

  // 拿到了完整最终答案：正常输出（超长自动落盘）
  if (state.markdownContent) {
    emitResult(state.markdownContent, state.taskInfo);
    process.exit(0);
  }

  // 未拿到最终答案，但已有步骤结果：兜底降级输出（同样支持超长落盘）
  const fallback = buildFallbackContent(state);
  if (fallback) {
    console.log("");
    console.log("[PROGRESS] ⚠️ 最终整合回答未完整返回，已用阶段性步骤结果兜底");
    emitResult(fallback, state.taskInfo);
    process.exit(0);
  }

  // 既无最终答案也无可兜底内容
  if (state.hasError) {
    console.error("");
    console.error(`[API_ERROR] 流式问答过程中出现错误: ${state.errorMessage}`);
    process.exit(4);
  }

  console.error("");
  console.error("[API_ERROR] 未获取到完整的回答内容");
  console.error("");
  console.error("可能原因：");
  console.error("  - 网络连接在传输过程中中断");
  console.error("  - 服务端处理超时");
  console.error("  - 请求被中断");
  process.exit(4);
}

// ============ 网络错误处理 ============

function printNetworkError(err) {
  if (err.name === "AbortError") {
    console.error("[NETWORK_ERROR] 网络请求失败 (请求超时)");
    console.error("");
    console.error(
      "原因：请求超时（超过 10 分钟），妙问服务响应较慢，请稍后重试。"
    );
  } else if (
    err.cause &&
    (err.cause.code === "ENOTFOUND" || err.cause.code === "EAI_AGAIN")
  ) {
    console.error("[NETWORK_ERROR] 网络请求失败 (DNS 解析失败)");
    console.error("");
    console.error("原因：无法解析域名，请检查网络连接和 DNS 设置。");
  } else if (err.cause && err.cause.code === "ECONNREFUSED") {
    console.error("[NETWORK_ERROR] 网络请求失败 (连接被拒绝)");
    console.error("");
    console.error("原因：无法连接到服务器，请检查网络连接。");
  } else if (err.cause && err.cause.code === "ECONNRESET") {
    console.error("[NETWORK_ERROR] 网络请求失败 (连接被重置)");
    console.error("");
    console.error("原因：接收数据失败，网络连接中断。");
  } else if (
    err.cause &&
    (err.cause.code === "UNABLE_TO_VERIFY_LEAF_SIGNATURE" ||
      err.cause.code === "ERR_TLS_CERT_ALTNAME_INVALID")
  ) {
    console.error("[NETWORK_ERROR] 网络请求失败 (TLS/SSL 错误)");
    console.error("");
    console.error("原因：SSL/TLS 连接错误，请检查网络环境。");
  } else {
    console.error("[NETWORK_ERROR] 网络请求失败");
    console.error("");
    console.error(
      `原因：网络异常 (${err.message})，请检查网络连接后重试。`
    );
  }

  console.error("");
  console.error("如果问题持续存在，请检查：");
  console.error("  - 网络是否正常连接");
  console.error("  - 是否需要配置代理（如在公司内网环境）");
  console.error("  - 妙问服务是否可用: https://miaowen.qq.com/");
}

main();
