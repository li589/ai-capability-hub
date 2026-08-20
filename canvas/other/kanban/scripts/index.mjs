import { promises as fs } from "node:fs";
import path from "node:path";

const dataPath = process.env.QODER_CANVAS_DATA || path.resolve("index.canvas.data.json");
const existing = await readJson(dataPath);

// Primary source: workspace tasks from IDE-injected data
const wsData = readState(existing, "aicoding.quest.workspaces", "system.quest.workspaces.v1");
const folders = Array.isArray(wsData.folders) ? wsData.folders : [];
const tasksByFolder = isRecord(wsData.tasksByFolder) ? wsData.tasksByFolder : {};

// Secondary source: quest sessions for enrichment (messages count etc.)
const systemSessions = readSystemQuestSessions(existing);
const sessionIndex = new Map();
for (const s of systemSessions) {
  if (s.taskId) sessionIndex.set(s.taskId, s);
}

// Build kanban columns from workspace tasks
const running = [];
const blocked = [];
const ready = [];

for (const folder of folders) {
  const tasks = Array.isArray(tasksByFolder[folder.path]) ? tasksByFolder[folder.path] : [];
  for (const task of tasks) {
    const session = convertTaskToSession(task, folder, sessionIndex);
    const column = mapToColumn(session.status);
    if (column === "running") running.push(session);
    else if (column === "blocked") blocked.push(session);
    else ready.push(session);
  }
}

// Sort each column by updatedAt descending
const byDate = (a, b) => dateMillis(b.updatedAt) - dateMillis(a.updatedAt);
running.sort(byDate);
blocked.sort(byDate);
ready.sort(byDate);

// Build task report from workspace tasks
const allTasks = [...running, ...blocked, ...ready];
const taskReport = buildTaskReport(allTasks);

const kanbanData = {
  schemaVersion: 1,
  updatedAt: latestUpdatedAt(allTasks),
  columns: { running, blocked, ready },
  taskReport,
  totalSessions: allTasks.length,
};

existing["aicoding.quest.kanban"] = kanbanData;
existing["kanban.v1"] = kanbanData;

await writeJsonAtomic(dataPath, existing);

// --- Helpers ---

function convertTaskToSession(task, folder, sessionIndex) {
  const taskId = String(task.id || "");
  const enrichment = sessionIndex.get(taskId);

  const updatedAt = formatTimestamp(task.lastUserQueryAt || task.updatedAtTimestamp || task.createdAt) || enrichment?.updatedAt || "";

  return {
    id: taskId,
    taskId,
    sessionId: String(task.executionSessionId || enrichment?.sessionId || `${taskId}.session.execution`),
    title: compactTitle(task.name || task.title || enrichment?.title || "Untitled Quest", 96),
    status: normalizeStatus(task.status || enrichment?.status || "Pending"),
    workspace: folder.label,
    projectPath: String(task.filePath || folder.path || ""),
    updatedAt,
    sessionFile: enrichment?.sessionFile || `quest:${taskId}`,
    promptPreview: compactTitle(task.query || enrichment?.promptPreview || "", 160),
    source: "quest",
    messages: enrichment?.messages || 0,
  };
}

function readSystemQuestSessions(existing) {
  const system = readState(existing, "aicoding.quest.sessions", "system.quest.sessions.v1");
  const sessions = Array.isArray(system.sessions) ? system.sessions : [];
  return sessions.filter(isRecord).map(normalizeQuestSession);
}

function normalizeQuestSession(session) {
  return {
    taskId: typeof session.taskId === "string" ? session.taskId : typeof session.id === "string" ? session.id : undefined,
    sessionId: typeof session.sessionId === "string" ? session.sessionId : undefined,
    title: String(session.title || session.promptPreview || ""),
    status: String(session.status || "Pending"),
    updatedAt: String(session.updatedAt || ""),
    sessionFile: String(session.sessionFile || ""),
    promptPreview: String(session.promptPreview || ""),
    messages: typeof session.messages === "number" ? session.messages : 0,
  };
}

function mapToColumn(status) {
  const normalized = normalizeStatus(status);
  if (normalized === "Running") return "running";
  if (normalized === "ActionRequired" || normalized === "Error") return "blocked";
  return "ready";
}

function buildTaskReport(sessions) {
  const total = sessions.length;
  let running = 0;
  let blocked = 0;
  let completed = 0;
  let stopped = 0;
  let pending = 0;
  let last24h = 0;
  let last7d = 0;

  const now = Date.now();
  const ms24h = 24 * 60 * 60 * 1000;
  const ms7d = 7 * ms24h;

  for (const s of sessions) {
    const normalized = normalizeStatus(s.status);
    if (normalized === "Running") running++;
    else if (normalized === "ActionRequired" || normalized === "Error") blocked++;
    else if (normalized === "Completed") completed++;
    else if (normalized === "Stopped") stopped++;
    else if (normalized === "Pending") pending++;

    const time = dateMillis(s.updatedAt);
    if (time > 0) {
      const age = now - time;
      if (age < ms24h) last24h++;
      if (age < ms7d) last7d++;
    }
  }

  return { total, running, blocked, completed, stopped, pending, last24h, last7d };
}

function normalizeStatus(status) {
  const value = String(status || "").trim();
  const lower = value.toLowerCase();
  if (lower === "running" || lower === "inprogress" || lower === "in_progress") return "Running";
  if (lower === "actionrequired" || lower === "action_required" || lower === "blocked") return "ActionRequired";
  if (lower === "error" || lower === "failed") return "Error";
  if (lower === "stopped" || lower === "cancelled" || lower === "canceled") return "Stopped";
  if (lower === "completed" || lower === "done" || lower === "success" || lower === "end_turn" || lower === "endturn") return "Completed";
  if (lower === "pending" || lower === "waiting") return "Pending";
  return value || "Pending";
}

// --- IO Utilities ---

async function readJson(file) {
  try {
    const raw = await fs.readFile(file, "utf8");
    const parsed = JSON.parse(raw);
    return isRecord(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function isRecord(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function readState(existing, key, legacyKey) {
  if (isRecord(existing[key])) return existing[key];
  if (legacyKey && isRecord(existing[legacyKey])) return existing[legacyKey];
  return {};
}

function compactTitle(value, limit = 72) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 1)}...`;
}

function formatTimestamp(timestamp) {
  if (!timestamp) return "";
  const millis = timestamp < 10000000000 ? timestamp * 1000 : timestamp;
  const date = new Date(millis);
  return Number.isNaN(date.getTime()) ? "" : date.toISOString();
}

function latestUpdatedAt(sessions) {
  let latest = 0;
  for (const session of sessions) {
    const time = dateMillis(session.updatedAt);
    if (time > latest) {
      latest = time;
    }
  }
  return latest > 0 ? new Date(latest).toISOString() : undefined;
}

function dateMillis(iso) {
  if (!iso) return 0;
  const time = new Date(iso).getTime();
  return Number.isNaN(time) ? 0 : time;
}

async function writeJsonAtomic(file, data) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(tmp, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  await fs.rename(tmp, file);
}
