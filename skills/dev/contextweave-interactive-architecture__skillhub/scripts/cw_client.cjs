const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { URL } = require("url");
const http = require("http");
const https = require("https");
const tls = require("tls");

function getProxyForUrl(targetUrl) {
  const protocol = targetUrl.protocol;
  if (protocol === "https:") {
    return process.env.HTTPS_PROXY || process.env.https_proxy;
  } else if (protocol === "http:") {
    return process.env.HTTP_PROXY || process.env.http_proxy;
  }
  return null;
}

function makeRequest(urlString, options, requestData = null, timeoutMs = 3000000) {
  return new Promise((resolve, reject) => {
    const targetUrl = new URL(urlString);
    const proxyStr = getProxyForUrl(targetUrl);
    
    const requestOptions = {
      ...options,
      hostname: targetUrl.hostname,
      port: targetUrl.port,
      path: targetUrl.pathname + targetUrl.search,
      protocol: targetUrl.protocol,
    };

    if (proxyStr) {
      const isTargetHttps = targetUrl.protocol === "https:";
      const AgentClass = isTargetHttps ? https.Agent : http.Agent;
      
      class ProxyAgent extends AgentClass {
        createConnection(opts, cb) {
          let proxyUrl;
          try {
            proxyUrl = new URL(proxyStr);
          } catch (e) {
            return cb(new Error(`Invalid proxy URL: ${proxyStr}`));
          }
          
          const isHttpsProxy = proxyUrl.protocol === "https:";
          const proxyRequestOptions = {
            method: "CONNECT",
            host: proxyUrl.hostname,
            port: proxyUrl.port || (isHttpsProxy ? 443 : 80),
            path: `${targetUrl.hostname}:${targetUrl.port || (isTargetHttps ? 443 : 80)}`,
            headers: {
              Host: targetUrl.hostname,
            },
          };

          if (proxyUrl.username || proxyUrl.password) {
            const auth = Buffer.from(`${proxyUrl.username}:${proxyUrl.password}`).toString("base64");
            proxyRequestOptions.headers["Proxy-Authorization"] = `Basic ${auth}`;
          }

          const proxyReq = (isHttpsProxy ? https : http).request(proxyRequestOptions);

          proxyReq.on("connect", (res, socket, head) => {
            if (res.statusCode === 200) {
              if (isTargetHttps) {
                const tlsSocket = tls.connect({
                  socket: socket,
                  servername: targetUrl.hostname,
                });
                tlsSocket.on('error', (err) => {
                  cb(err);
                });
                cb(null, tlsSocket);
              } else {
                cb(null, socket);
              }
            } else {
              cb(new Error(`Proxy connection failed: ${res.statusCode}`));
            }
          });

          proxyReq.on("error", (err) => {
            cb(err);
          });

          proxyReq.setTimeout(timeoutMs, () => {
            proxyReq.destroy(new Error("timeout"));
          });

          proxyReq.end();
        }
      }

      requestOptions.agent = new ProxyAgent();
    }

    const lib = targetUrl.protocol === "https:" ? https : http;
    const req = lib.request(requestOptions, (res) => {
      resolve(res);
    });

    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error("timeout"));
    });

    req.on("error", (err) => {
      if (err.message === "timeout" || err.code === "ECONNRESET") {
        reject(new Error("timeout"));
      } else {
        reject(err);
      }
    });

    if (requestData) {
      req.write(requestData);
    }
    req.end();
  });
}

function readBody(response) {
  return new Promise((resolve, reject) => {
    let data = '';
    response.setEncoding('utf8');
    response.on('data', (chunk) => {
      data += chunk;
    });
    response.on('end', () => {
      resolve(data);
    });
    response.on('error', (err) => {
      reject(err);
    });
  });
}

function getSkillVersion() {
  try {
    const skillMdPath = path.join(__dirname, '..', 'SKILL.md');
    if (fs.existsSync(skillMdPath)) {
      const content = fs.readFileSync(skillMdPath, 'utf-8');
      const match = content.match(/^version:\s*(.+)$/m);
      if (match) {
        return match[1].trim();
      }
    }
  } catch (e) {}
  return "unknown";
}

const SKILL_VERSION = getSkillVersion();

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isTransientNetworkError(error) {
  if (!error) return false;
  if (error.message === "timeout") return true;
  return ["ECONNRESET", "ECONNREFUSED", "EPIPE", "ETIMEDOUT"].includes(error.code);
}

class CWClient {
  constructor() {
    const baseUrl = process.env.CW_API_BASE_URL || "https://pptx.chenxitech.site";
    this.baseUrl = baseUrl ? baseUrl.replace(/\/+$/, "") : "";
    this.timeoutMs = 3000000;
    this.maxRequestRetries = parseInt(process.env.CW_REQUEST_MAX_RETRIES || "3", 10);
    this.retryBaseMs = parseInt(process.env.CW_REQUEST_RETRY_BASE_MS || "2000", 10);
    this.apiKey = this.loadApiKey();
    this.editorProtocol = process.env.CONTEXTWEAVE_EDITOR_PROTOCOL || "trae";
  }

  loadApiKey() {
    return process.env.CONTEXTWEAVE_MCP_API_KEY || "";
  }

  validateBaseUrl() {
    try {
      const url = new URL(this.baseUrl);
      if (url.hostname !== "pptx.chenxitech.site") {
        return this.error("INVALID_DOMAIN", "Only pptx.chenxitech.site domain is allowed");
      }
    } catch (e) {
      return this.error("INVALID_DOMAIN", "Invalid base URL");
    }
    return null;
  }

  headers() {
    const headers = { 
      "X-Request-ID": this.createRequestId(), 
      "Content-Type": "application/json",
      "X-Skill-Version": SKILL_VERSION
    };
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }
    return headers;
  }

  createRequestId() {
    return crypto.randomBytes(16).toString("hex");
  }

  validateSafePath(targetPath) {
    if (!targetPath || typeof targetPath !== "string") {
      return this.error("INVALID_PATH", "Path is empty or invalid");
    }
    if (!path.isAbsolute(targetPath)) {
      return this.error("INPUT_FILE_NOT_ABSOLUTE", `Path must be absolute: ${targetPath}`);
    }
    const normalized = path.resolve(targetPath);
    const cwd = process.cwd();
    const relative = path.relative(cwd, normalized);
    if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) {
      return this.error("PATH_TRAVERSAL_DETECTED", "Path must be strictly within the current working directory");
    }
    return null;
  }

  error(code, message, recoverable = false, recoveryHint = null) {
    const result = { status: "error", error: { code, message } };
    if (recoverable) {
      result.error.recoverable = true;
    }
    if (recoveryHint) {
      result.error.recovery_hint = recoveryHint;
    }
    return result;
  }

  async request(endpoint, payload) {
    const baseUrlError = this.validateBaseUrl();
    if (baseUrlError) {
      return baseUrlError;
    }
    const body = { ...payload };
    if (this.editorProtocol) {
      body.editor_protocol = this.editorProtocol;
    }

    for (let attempt = 1; attempt <= this.maxRequestRetries; attempt += 1) {
      try {
        const response = await this.postJson(`${this.baseUrl}${endpoint}`, body);
        if (response.statusCode >= 500) {
          // 5xx 视为瞬时故障，指数退避后重试
          if (attempt < this.maxRequestRetries) {
            const waitMs = this.retryBaseMs * Math.pow(2, attempt - 1);
            process.stderr.write(`[retry ${attempt}/${this.maxRequestRetries}] 服务端 ${response.statusCode}，${waitMs / 1000}s 后重试...\n`);
            await sleep(waitMs);
            continue;
          }
          return this.error("API_ERROR", `${response.statusCode} ${response.statusMessage || "Server Error"}（已自动重试 ${this.maxRequestRetries} 次）`, true, "后端服务暂时不可用，请稍后重试；若持续失败请走 submit_feedback 兜底");
        }
        return this.handleResponse(response);
      } catch (error) {
        if (isTransientNetworkError(error) && attempt < this.maxRequestRetries) {
          const waitMs = this.retryBaseMs * Math.pow(2, attempt - 1);
          process.stderr.write(`[retry ${attempt}/${this.maxRequestRetries}] 网络瞬时故障（${error.message || error.code}），${waitMs / 1000}s 后重试...\n`);
          await sleep(waitMs);
          continue;
        }
        return this.error("API_ERROR", String(error.message || error), true, "请检查网络或后端服务状态后重试");
      }
    }
  }

  handleResponse(response) {
    try {
      if (response.statusCode === 402) {
        return this.error("PAYMENT_REQUIRED", "Insufficient credits", true, "额度不足。可引导用户免费领取：询问用户邮箱 → 运行 request_quota_code.cjs --email <邮箱> 发送验证码 → 询问验证码 → 运行 redeem_quota_code.cjs --email <邮箱> --code <验证码> → 用户查收邮件按指引配置 CONTEXTWEAVE_MCP_API_KEY 后重试。");
      }
      if (response.statusCode === 403) {
        return this.error("AUTH_ERROR", "Invalid API key or missing key", true, "请检查 CONTEXTWEAVE_MCP_API_KEY");
      }
      if (response.statusCode === 426) {
        let parsed = {};
        try { parsed = JSON.parse(response.body); } catch(e) {}
        const detail = parsed.detail || {};
        return this.error(
          detail.code || "OUTDATED_SKILL",
          detail.message || "Skill版本已过期",
          true,
          detail.recovery_hint || "请下载最新版本"
        );
      }
      if (response.statusCode === 429) {
        let errorMsg = "Too Many Requests";
        try {
          const parsed = JSON.parse(response.body);
          errorMsg = parsed.detail || parsed.error || errorMsg;
        } catch (e) {}
        return this.error("RATE_LIMIT_EXCEEDED", errorMsg, true, "免费体验额度已用完或请求过于频繁。可稍后重试，或引导用户免费领取专属 API Key：询问用户邮箱 → 运行 request_quota_code.cjs --email <邮箱> 发送验证码 → 询问验证码 → 运行 redeem_quota_code.cjs --email <邮箱> --code <验证码> → 用户查收邮件按指引配置 CONTEXTWEAVE_MCP_API_KEY 后重试。");
      }
      if (response.statusCode === 400 || response.statusCode === 409) {
        let errorMsg = `${response.statusCode} ${response.statusMessage || "Request failed"}`;
        try {
          const parsed = JSON.parse(response.body);
          const detail = parsed.detail || parsed.error;
          if (detail) {
            errorMsg += `: ${typeof detail === 'object' ? JSON.stringify(detail) : detail}`;
          }
        } catch (e) {}
        return this.error(
          response.statusCode === 400 ? "BAD_REQUEST" : "CONFLICT",
          errorMsg,
          true,
          "请根据提示修正输入后重试"
        );
      }
      if (response.statusCode < 200 || response.statusCode >= 300) {
        let errorMsg = `${response.statusCode} ${response.statusMessage || "Request failed"}`;
        try {
          const parsed = JSON.parse(response.body);
          const detail = parsed.detail || parsed.error;
          if (detail) {
            errorMsg += `: ${typeof detail === 'object' ? JSON.stringify(detail) : detail}`;
          }
        } catch (e) {}
        throw new Error(errorMsg);
      }
      return JSON.parse(response.body || "{}");
    } catch (error) {
      return this.error("API_ERROR", String(error.message || error), true, "请检查网络或后端服务状态后重试");
    }
  }

  async postJson(urlString, body) {
    const requestData = JSON.stringify(body);
    const requestOptions = {
      method: "POST",
      headers: {
        ...this.headers(),
        "Content-Length": Buffer.byteLength(requestData),
      },
    };

    try {
      const response = await makeRequest(urlString, requestOptions, requestData, this.timeoutMs);
      const responseBody = await readBody(response);

      return {
        statusCode: response.statusCode,
        statusMessage: response.statusMessage,
        body: responseBody,
      };
    } catch (error) {
      if (error.message === "timeout") {
        throw new Error("timeout");
      }
      throw error;
    }
  }

  async runGeneration({ userRequest, inputFile = null, sessionId = null, inputSequence = null, validateRequestLength = false, diagramStyle = null, morphology = null, accentTargets = null, basePalette = null, enablePlan = false, n = 1, topK = 1 }) {
    const payload = {
      input_sequence: inputSequence,
      export_svg: true,
      export_pptx: false,
      session_id: sessionId,
      test_file: null,
      n: n,
      top_k: topK,
    };
    if (diagramStyle) {
      payload.diagram_style = diagramStyle;
    }
    if (morphology) {
      payload.morphology = morphology;
    }
    if (accentTargets) {
      payload.accent_targets = accentTargets;
    }
    if (basePalette) {
      payload.base_palette = basePalette;
    }

    // Add use_unified_bot flag if explicitly set via environment variable
    if (process.env.CONTEXTWEAVE_USE_UNIFIED_BOT === "true") {
      payload.use_unified_bot = true;
    }
    // Add enable_plan flag if explicitly set via environment variable or passed as argument
    if (enablePlan || process.env.CONTEXTWEAVE_ENABLE_PLAN === "true") {
      payload.enable_plan = true;
    }
    if (inputFile) {
      const pathError = this.validateSafePath(inputFile);
      if (pathError) {
        return pathError;
      }
      if (!fs.existsSync(inputFile)) {
        return this.error("FILE_NOT_FOUND", `File not found: ${inputFile}`);
      }
      try {
        const content = fs.readFileSync(inputFile, "utf8");
        let reqText = content.trim();
        let cwText = "";
        if (content.includes("# CW")) {
          const parts = content.split("# CW");
          const reqPart = parts[0];
          const cwPart = parts.slice(1).join("# CW");
          const afterFenceIndex = cwPart.indexOf("```cw");
          if (afterFenceIndex !== -1) {
            const afterFence = cwPart.substring(afterFenceIndex + 5);
            const lastFenceIndex = afterFence.lastIndexOf("```");
            if (lastFenceIndex !== -1) {
              cwText = afterFence.substring(0, lastFenceIndex).trim();
            } else {
              cwText = afterFence.trim();
            }
          } else {
            cwText = cwPart.trim();
          }
          if (reqPart.includes("# Request")) {
            reqText = reqPart.split("# Request")[1].trim();
          } else {
            reqText = reqPart.trim();
          }
        }
        payload.user_request = reqText;
        payload.initial_cw_code = cwText;

        // Try to parse user_request as JSON to extract base_path if present
        try {
          let jsonText = reqText;
          // Extract JSON block if enclosed in markdown
          const jsonMatch = reqText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
          if (jsonMatch) {
            jsonText = jsonMatch[1];
          }
          const parsedReq = JSON.parse(jsonText);
          if (parsedReq && parsedReq.base_path) {
            payload.base_path = parsedReq.base_path;
          }
        } catch (e) {
          // Not a valid JSON or no base_path, which is fine for normal text requests
        }

      } catch (error) {
        return this.error("READ_ERROR", `Failed to read input file: ${String(error.message || error)}`);
      }
    } else {
      payload.user_request = userRequest;
    }

    if (validateRequestLength) {
      const minLength = parseInt(process.env.CONTEXTWEAVE_MIN_REQUEST_LENGTH || "50", 10);
      const maxLength = parseInt(process.env.CONTEXTWEAVE_MAX_REQUEST_LENGTH || "5000", 10);
      const reqLength = payload.user_request ? payload.user_request.length : 0;
      if (reqLength < minLength || reqLength > maxLength) {
        return this.error(
          "INVALID_REQUEST_LENGTH",
          `生成请求的长度必须在 ${minLength} 到 ${maxLength} 字符之间，当前长度: ${reqLength}。`,
          true,
          `请调整请求文本的详细程度，确保字数在 ${minLength}-${maxLength} 之间。`
        );
      }
    }

    const result = await this.request("/run", payload);
    // 打印服务端透传的 lint 软警告（仅提示，不影响成功判定与返回值）
    if (result && Array.isArray(result.warnings) && result.warnings.length > 0) {
      for (const warning of result.warnings) {
        console.error(`[generation warnings] ${warning}`);
      }
    }
    return result;
  }

  async exportSessionAsset(sessionId, formatName) {
    return this.request("/export-session", { session_id: sessionId, format: formatName });
  }

  async recompileSession(sessionId) {
    return this.request("/session/recompile", { session_id: sessionId });
  }

  async importCode(target = "ContextWeave") {
    const pathError = this.validateSafePath(target);
    if (pathError) {
      return pathError;
    }
    const targetPath = path.resolve(target);
    if (!fs.existsSync(targetPath)) {
      return this.error("PATH_NOT_FOUND", `Path not found: ${targetPath}`);
    }
    
    let cwFile = targetPath;
    const stats = fs.statSync(targetPath);
    if (stats.isDirectory()) {
      cwFile = path.join(targetPath, "diagram.cw");
      if (!fs.existsSync(cwFile)) {
        return this.error("FILE_NOT_FOUND", `diagram.cw not found in directory: ${targetPath}`);
      }
    }
    
    let content;
    try {
      content = fs.readFileSync(cwFile, "utf8");
    } catch (error) {
      return this.error("READ_ERROR", String(error.message || error));
    }
    return this.request("/session/import", { cw_code: content, source_name: cwFile });
  }

  async exportCode(sessionId, target = "ContextWeave") {
    const pathError = this.validateSafePath(target);
    if (pathError) {
      return pathError;
    }
    const result = await this.request("/session/export", { session_id: sessionId });
    if (result.status === "error") {
      return result;
    }
    const cwCode = result.cw_code;
    const targetPath = path.resolve(target);
    try {
      fs.mkdirSync(targetPath, { recursive: true });
    } catch (error) {
      return this.error("CREATE_DIR_ERROR", String(error.message || error));
    }
    const targetFile = path.join(targetPath, "diagram.cw");
    try {
      fs.writeFileSync(targetFile, cwCode || "", "utf8");
    } catch (error) {
      return this.error("WRITE_ERROR", String(error.message || error));
    }
    return { status: "ok", file_path: targetFile, session_id: sessionId };
  }
}

function printJson(data) {
  process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
}

function normalizeAssetResult(result) {
  if (!result || typeof result !== "object") {
    return result;
  }

  // We don't need to do anything complex anymore, because the backend (mcp_server) 
  // now sets the "svg_url" to the primary HTML wrapper link if HTML is enabled.
  // It also returns "raw_svg_url" if we ever need the actual SVG link.

  // Clean up excessive fields to keep the output clean
  delete result.html_url;
  delete result.primary_asset_url;
  delete result.preferred_asset_url;
  delete result.url;

  return result;
}

async function downloadFile(urlString, dest) {
  try {
    new URL(urlString);
  } catch (e) {
    throw new Error("Invalid URL");
  }

  try {
    const response = await makeRequest(urlString, { method: "GET" }, null, 3000000);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw new Error(`Failed to download file, status code: ${response.statusCode}`);
    }

    const file = fs.createWriteStream(dest);

    return new Promise((resolve, reject) => {
      response.pipe(file);
      
      file.on("finish", () => {
        file.close(() => resolve(dest));
      });

      response.on("error", (err) => {
        file.close();
        fs.unlink(dest, () => {});
        reject(err);
      });

      file.on("error", (err) => {
        file.close();
        fs.unlink(dest, () => {});
        reject(err);
      });
    });
  } catch (err) {
    fs.unlink(dest, () => {});
    throw err;
  }
}

async function downloadAssetsLocally(result) {
  if (!result || result.status !== "ok") {
    return result;
  }
  
  const sessionId = result.session_id || "diagram";
  const outputName = result.output_name || `diagram_${sessionId}`;
  
  let targetDir = process.cwd();
  if (result.output_dir) {
    targetDir = path.resolve(result.output_dir);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
  }

  // Handle svg_url or raw_svg_url
  const svgUrl = result.raw_svg_url || result.svg_url;
  if (svgUrl && svgUrl !== "WAITING_FOR_EXPERT_PROCESSING") {
    // If it's HTML wrapper, the download might get HTML. It's better to fetch raw_svg_url if available, or just download what's there.
    const ext = svgUrl.includes(".html") ? ".html" : ".svg";
    const dest = path.join(targetDir, `${outputName}${ext}`);
    try {
      await downloadFile(svgUrl, dest);
      result.saved_svg_file = dest;
      result.message = (result.message ? result.message + "\n" : "") + `资源已自动下载到本地：${dest}`;
    } catch (err) {
      // Silently fail or log error
    }
  }

  // Handle pptx_url
  if (result.pptx_url) {
    const dest = path.join(targetDir, `${outputName}.pptx`);
    try {
      await downloadFile(result.pptx_url, dest);
      result.saved_pptx_file = dest;
      result.message = (result.message ? result.message + "\n" : "") + `PPTX 资源已自动下载到本地：${dest}`;
    } catch (err) {
      // Silently fail or log error
    }
  }

  return result;
}

module.exports = {
  CWClient,
  normalizeAssetResult,
  downloadAssetsLocally,
  printJson,
};
