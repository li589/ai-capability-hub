import { type CSSProperties, memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type LocalizedTextBundle,
  Row,
  Stack,
  Text,
  useCanvasAction,
  useCanvasState,
  useHostTheme,
  useLocalizedText,
} from "qoder/canvas";

// --- Types ---

interface KanbanSession {
  id: string;
  taskId?: string;
  sessionId?: string;
  title: string;
  status: string;
  workspace: string;
  projectPath?: string;
  updatedAt: string;
  sessionFile: string;
  promptPreview?: string;
  source: string;
  messages?: number;
}

interface KanbanData {
  schemaVersion?: number;
  version?: number;
  updatedAt?: string;
  columns: {
    running: KanbanSession[];
    blocked: KanbanSession[];
    ready: KanbanSession[];
  };
  totalSessions: number;
}

interface QuestTask {
  id: string;
  name: string;
  title?: string;
  status: string;
  query?: string;
  executionSessionId?: string;
  filePath?: string;
  updatedAtTimestamp?: number;
  lastUserQueryAt?: number;
  createdAt?: number;
  planProgress?: { completedSteps: number; totalSteps: number };
}

interface QuestFolder {
  label: string;
  path: string;
  uri?: string;
}

interface QuestWorkspacesData {
  schemaVersion?: number;
  updatedAt?: string;
  folders: QuestFolder[];
  tasksByFolder: Record<string, QuestTask[]>;
}

interface QuestSessionsData {
  schemaVersion?: number;
  updatedAt?: string;
  sessions: KanbanSession[];
}

interface QuestKanbanDelta {
  schemaVersion?: number;
  version?: number | string;
  updatedAt?: string;
  upsert?: KanbanSession[];
  removeIds?: string[];
}

type ThemeTokens = ReturnType<typeof useHostTheme>["tokens"];
type KanbanColumnKey = keyof KanbanData["columns"];

interface KanbanText {
  allQuest: string;
  refresh: string;
  refreshing: string;
  searchPlaceholder: string;
  clear: string;
  workspace: string;
  all: string;
  less: string;
  more: (count: number) => string;
  showMore: (count: number) => string;
  running: string;
  waiting: string;
  completed: string;
  noSessions: string;
  actionRequired: string;
  error: string;
  stopped: string;
  pending: string;
  open: string;
  opening: string;
  messages: (count: number) => string;
  tasks: (count: number) => string;
}

function useKanbanText(): KanbanText {
  return useLocalizedText(KANBAN_TEXT);
}

// --- Defaults ---

const EMPTY_KANBAN: KanbanData = {
  columns: { running: [], blocked: [], ready: [] },
  totalSessions: 0,
};

const EMPTY_WS: QuestWorkspacesData = {
  folders: [],
  tasksByFolder: {},
};

const EMPTY_SESSIONS: QuestSessionsData = {
  sessions: [],
};

const EMPTY_KANBAN_DELTA: QuestKanbanDelta = {};
const EMPTY_FOLDERS: QuestFolder[] = [];
const EMPTY_TASKS_BY_FOLDER: Record<string, QuestTask[]> = {};
const KANBAN_COLUMN_KEYS: KanbanColumnKey[] = ["running", "blocked", "ready"];
const KANBAN_COLUMN_COLLAPSED_LIMIT = 10;

const QUEST_KANBAN_KEY = "aicoding.quest.kanban";
const QUEST_KANBAN_DELTA_KEY = "aicoding.quest.kanban.delta";
const QUEST_WORKSPACES_KEY = "aicoding.quest.workspaces";
const QUEST_SESSIONS_KEY = "aicoding.quest.sessions";
const LEGACY_KANBAN_KEY = "kanban.v1";
const LEGACY_QUEST_WORKSPACES_KEY = "system.quest.workspaces.v1";
const LEGACY_QUEST_SESSIONS_KEY = "system.quest.sessions.v1";

const KANBAN_TEXT: LocalizedTextBundle<KanbanText> = {
  default: {
    allQuest: "All Quests",
    refresh: "刷新",
    refreshing: "刷新中...",
    searchPlaceholder: "Search quests...",
    clear: "Clear",
    workspace: "Workspace",
    all: "All",
    less: "Less",
    more: (count) => `+${count} more`,
    showMore: (count) => `Show more (${count})`,
    running: "Running",
    waiting: "Waiting",
    completed: "Completed",
    noSessions: "No quests",
    actionRequired: "Action Required",
    error: "Error",
    stopped: "Stopped",
    pending: "Pending",
    open: "Open",
    opening: "Opening...",
    messages: (count) => `${count} msg${count === 1 ? "" : "s"}`,
    tasks: (count) => `${count} quest${count === 1 ? "" : "s"}`,
  },
  "zh-cn": {
    allQuest: "全部 Quest",
    refresh: "刷新",
    refreshing: "刷新中...",
    searchPlaceholder: "搜索 Quest...",
    clear: "清除",
    workspace: "工作区",
    all: "全部",
    less: "收起",
    more: (count) => `还有 ${count} 个`,
    showMore: (count) => `再显示 ${count} 个`,
    running: "运行中",
    waiting: "等待中",
    completed: "已完成",
    noSessions: "暂无 Quest",
    actionRequired: "等待操作",
    error: "错误",
    stopped: "已停止",
    pending: "待处理",
    open: "打开",
    opening: "打开中...",
    messages: (count) => `${count} 条消息`,
    tasks: (count) => `${count} 个 Quest`,
  },
};

// --- Main Component ---

export default function KanbanBoard() {
  const { tokens } = useHostTheme();
  const text = useKanbanText();
  const [questKanbanData] = useCanvasState<KanbanData>(QUEST_KANBAN_KEY, EMPTY_KANBAN);
  const [questKanbanDelta] = useCanvasState<QuestKanbanDelta>(QUEST_KANBAN_DELTA_KEY, EMPTY_KANBAN_DELTA);
  const [legacyKanbanData] = useCanvasState<KanbanData>(LEGACY_KANBAN_KEY, EMPTY_KANBAN);
  const [questWorkspaces] = useCanvasState<QuestWorkspacesData>(QUEST_WORKSPACES_KEY, EMPTY_WS);
  const [legacyQuestWorkspaces] = useCanvasState<QuestWorkspacesData>(LEGACY_QUEST_WORKSPACES_KEY, EMPTY_WS);
  const [questSessions] = useCanvasState<QuestSessionsData>(QUEST_SESSIONS_KEY, EMPTY_SESSIONS);
  const [legacyQuestSessions] = useCanvasState<QuestSessionsData>(LEGACY_QUEST_SESSIONS_KEY, EMPTY_SESSIONS);
  const [searchQuery, setSearchQuery] = useState("");
  const [questFilter, setQuestFilter] = useState<string>("all");
  const [showAllQuests, setShowAllQuests] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const dispatch = useCanvasAction();
  const appliedDeltaVersionRef = useRef<number | string | undefined>(undefined);
  const deltaOverlayRef = useRef<QuestKanbanDelta>(EMPTY_KANBAN_DELTA);

  const wsData = isCurrentQuestWorkspaceData(questWorkspaces) ? questWorkspaces : legacyQuestWorkspaces;
  const sessionData = isCurrentQuestSessionData(questSessions) ? questSessions : legacyQuestSessions;
  const baseData = useMemo(
    () => isCurrentKanbanData(questKanbanData) ? questKanbanData : buildKanbanData(wsData, sessionData, legacyKanbanData),
    [questKanbanData, wsData, sessionData, legacyKanbanData],
  );
  const [data, setData] = useState<KanbanData>(baseData);

  useEffect(() => {
    const deltaOverlay = deltaOverlayRef.current;
    if (!hasKanbanDeltaChanges(deltaOverlay)) {
      setData(baseData);
      return;
    }
    if (isKanbanDeltaOlderThanBase(deltaOverlay, baseData)) {
      deltaOverlayRef.current = EMPTY_KANBAN_DELTA;
      setData(baseData);
      return;
    }
    setData(applyKanbanDelta(baseData, deltaOverlay));
  }, [baseData]);

  useEffect(() => {
    const version = questKanbanDelta.version;
    if (version == null || appliedDeltaVersionRef.current === version) return;
    appliedDeltaVersionRef.current = version;
    if (!hasKanbanDeltaChanges(questKanbanDelta)) {
      deltaOverlayRef.current = EMPTY_KANBAN_DELTA;
      setData(baseData);
      return;
    }
    if (isKanbanDeltaOlderThanBase(questKanbanDelta, baseData)) {
      return;
    }
    deltaOverlayRef.current = mergeKanbanDeltaOverlay(deltaOverlayRef.current, questKanbanDelta);
    setData((current) => {
      return applyKanbanDelta(current, questKanbanDelta);
    });
  }, [questKanbanDelta, baseData]);

  const columns = data.columns || EMPTY_KANBAN.columns;

  const folders = wsData.folders || EMPTY_FOLDERS;
  const tasksByFolder = wsData.tasksByFolder || EMPTY_TASKS_BY_FOLDER;

  const handleRefresh = useCallback(() => {
    if (refreshing) return;
    setRefreshing(true);
    appliedDeltaVersionRef.current = undefined;
    deltaOverlayRef.current = EMPTY_KANBAN_DELTA;
    setData({
      ...EMPTY_KANBAN,
      schemaVersion: 1,
      updatedAt: new Date().toISOString(),
    });
    dispatch({ type: "aicoding.canvas.fetchQuestWorkspaces", force: true });
  }, [refreshing, dispatch]);

  useEffect(() => {
    if (!refreshing) return;
    const timer = window.setTimeout(() => setRefreshing(false), 120);
    return () => window.clearTimeout(timer);
  }, [refreshing, data.updatedAt, data.totalSessions]);

  // Build taskId -> folderLabel index and per-folder taskId sets
  const { taskIdToLabel, folderTaskSets } = useMemo(() => {
    const idToLabel = new Map<string, string>();
    const fSets = new Map<string, Set<string>>();

    for (const folder of folders) {
      const tasks = tasksByFolder[folder.path] || [];
      const idSet = new Set<string>();

      for (const t of tasks) {
        if (t.id) {
          idToLabel.set(t.id, folder.label);
          idSet.add(t.id);
        }
      }

      fSets.set(folder.path, idSet);
    }

    // Track already-assigned taskIds to avoid duplicate assignment for same-label folders
    const assignedIds = new Set<string>();
    for (const idSet of fSets.values()) {
      for (const id of idSet) assignedIds.add(id);
    }

    // Build label -> paths mapping (one label may map to multiple paths)
    const folderPathsByLabel = new Map<string, string[]>();
    for (const folder of folders) {
      const paths = folderPathsByLabel.get(folder.label) || [];
      paths.push(folder.path);
      folderPathsByLabel.set(folder.label, paths);
    }

    for (const key of KANBAN_COLUMN_KEYS) {
      for (const session of columns[key] || []) {
        const taskId = session.taskId || session.id;
        if (!taskId) continue;
        if (session.workspace && !idToLabel.has(taskId)) {
          idToLabel.set(taskId, session.workspace);
        }
        // Only assign unassigned sessions to a folder via workspace label
        if (!assignedIds.has(taskId) && session.workspace) {
          const paths = folderPathsByLabel.get(session.workspace);
          const folderPath = paths?.[0];
          if (folderPath) {
            const idSet = fSets.get(folderPath) || new Set<string>();
            idSet.add(taskId);
            fSets.set(folderPath, idSet);
            assignedIds.add(taskId);
          }
        }
      }
    }

    return { taskIdToLabel: idToLabel, folderTaskSets: fSets };
  }, [folders, tasksByFolder, columns]);

  // Filter sessions
  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const matchSearch = (s: KanbanSession) =>
      !q ||
      s.title.toLowerCase().includes(q) ||
      (s.workspace || "").toLowerCase().includes(q) ||
      (s.promptPreview || "").toLowerCase().includes(q);

    // Pre-compute the active idSet once, avoid per-session find()
    let activeIdSet: Set<string> | null = null;
    if (questFilter !== "all") {
      const folder = folders.find((f) => f.path === questFilter);
      if (folder) {
        activeIdSet = folderTaskSets.get(folder.path) || null;
      }
    }

    const matchQuest = (s: KanbanSession) => {
      if (questFilter === "all") return true;
      if (!activeIdSet) return false;
      return !!s.taskId && activeIdSet.has(s.taskId);
    };

    const match = (s: KanbanSession) => matchSearch(s) && matchQuest(s);

    const running = columns.running.filter(match);
    const allBlocked = columns.blocked.filter(match);
    const waiting = allBlocked.filter((s) => normalizeStatus(s.status) !== "Error");
    const errorItems = allBlocked.filter((s) => normalizeStatus(s.status) === "Error");
    const completed = [...columns.ready.filter(match), ...errorItems];
    return { running, waiting, completed };
  }, [columns, searchQuery, questFilter, folders, folderTaskSets]);

  return (
    <div
      style={{
        boxSizing: "border-box",
        height: "100vh",
        width: "calc(100% + 40px)",
        margin: "-16px -20px",
        overflow: "hidden",
        padding: "12px 14px",
        background: tokens.bg.elevated,
        color: tokens.text.primary,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      {/* Search bar */}
      <SearchBar value={searchQuery} onChange={setSearchQuery} text={text} />

      {/* Quest filter */}
      <QuestFilterBar
        folders={folders}
        tasksByFolder={tasksByFolder}
        questFilter={questFilter}
        onFilterChange={setQuestFilter}
        showAll={showAllQuests}
        onToggleShowAll={() => setShowAllQuests((v) => !v)}
        text={text}
      />

      {/* Kanban Columns */}
      <div style={{ flex: 1, minHeight: 0, display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
        <KanbanColumn title={text.running} count={filtered.running.length} sessions={filtered.running} tone="primary" taskIdToLabel={taskIdToLabel} text={text} collapsedLimit={KANBAN_COLUMN_COLLAPSED_LIMIT} />
        <KanbanColumn title={text.waiting} count={filtered.waiting.length} sessions={filtered.waiting} tone="warning" taskIdToLabel={taskIdToLabel} text={text} collapsedLimit={KANBAN_COLUMN_COLLAPSED_LIMIT} />
        <KanbanColumn title={text.completed} count={filtered.completed.length} sessions={filtered.completed} tone="success" taskIdToLabel={taskIdToLabel} text={text} collapsedLimit={KANBAN_COLUMN_COLLAPSED_LIMIT} />
      </div>
    </div>
  );
}

// --- Search & Filter ---

function SearchBar({ value, onChange, text }: { value: string; onChange: (v: string) => void; text: KanbanText }) {
  const { tokens } = useHostTheme();
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8, height: 30, padding: "0 8px",
      borderRadius: 6, border: `1px solid ${tokens.stroke.tertiary}`, background: tokens.bg.editor,
    }}>
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
        <path d="M7 1a6 6 0 1 0 3.71 10.71l3.29 3.29 1-1-3.29-3.29A6 6 0 0 0 7 1Zm0 1.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill={tokens.text.tertiary} />
      </svg>
      <input
        type="text" value={value} onChange={(e) => onChange(e.target.value)}
        placeholder={text.searchPlaceholder}
        style={{
          flex: 1, height: "100%", border: "none", background: "transparent",
          color: tokens.text.primary, fontSize: 12, outline: "none", font: "inherit",
        }}
      />
      {value && (
        <button type="button" onClick={() => onChange("")} style={{
          border: "none", background: "transparent", color: tokens.text.tertiary,
          cursor: "pointer", font: "inherit", fontSize: 12, padding: 0,
        }}>{text.clear}</button>
      )}
    </div>
  );
}

const FilterButton = memo(function FilterButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  const { tokens } = useHostTheme();
  const [hovered, setHovered] = useState(false);
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        height: 24, padding: "0 9px", borderRadius: 6,
        border: `1px solid ${active ? tokens.stroke.secondary : tokens.stroke.tertiary}`,
        background: active ? tokens.fill.tertiary : hovered ? tokens.fill.tertiary : "transparent",
        color: active ? tokens.text.primary : tokens.text.secondary,
        cursor: "pointer", font: "inherit", fontSize: 12, fontWeight: 560,
        lineHeight: "22px", boxShadow: "none", whiteSpace: "nowrap",
      }}
    >
      {label}
    </button>
  );
});

const QUEST_FILTER_VISIBLE_COUNT = 5;

function QuestFilterBar({ folders, tasksByFolder, questFilter, onFilterChange, showAll, onToggleShowAll, text }: {
  folders: QuestFolder[];
  tasksByFolder: Record<string, QuestTask[]>;
  questFilter: string;
  onFilterChange: (v: string) => void;
  showAll: boolean;
  onToggleShowAll: () => void;
  text: KanbanText;
}) {
  const { tokens } = useHostTheme();
  const visibleFolders = showAll ? folders : folders.slice(0, QUEST_FILTER_VISIBLE_COUNT);
  const hiddenCount = folders.length - QUEST_FILTER_VISIBLE_COUNT;
  // If active filter is in hidden section, always show it
  const activeHiddenFolder = !showAll
    ? folders.find((f, i) => f.path === questFilter && i >= QUEST_FILTER_VISIBLE_COUNT)
    : undefined;

  return (
    <Row gap={6} align="center" wrap>
      <Text tone="tertiary" size="small" style={{ fontSize: 11, fontWeight: 600, flexShrink: 0 }}>{text.workspace}</Text>
      <FilterButton active={questFilter === "all"} onClick={() => onFilterChange("all")} label={text.all} />
      {visibleFolders.map((f) => {
        const tasks = tasksByFolder[f.path] || [];
        return (
          <FilterButton
            key={f.path}
            active={questFilter === f.path}
            onClick={() => onFilterChange(f.path)}
            label={`${f.label} (${tasks.length})`}
          />
        );
      })}
      {activeHiddenFolder && (
        <FilterButton
          key={activeHiddenFolder.path}
          active
          onClick={() => onFilterChange(activeHiddenFolder.path)}
          label={`${activeHiddenFolder.label} (${(tasksByFolder[activeHiddenFolder.path] || []).length})`}
        />
      )}
      {hiddenCount > 0 && (
        <button type="button" onClick={onToggleShowAll} style={{
          height: 24, padding: "0 9px", borderRadius: 6,
          border: `1px solid ${tokens.stroke.tertiary}`,
          background: "transparent",
          color: tokens.text.tertiary,
          cursor: "pointer", font: "inherit", fontSize: 11, fontWeight: 560,
          lineHeight: "22px", boxShadow: "none", whiteSpace: "nowrap",
        }}>
          {showAll ? text.less : text.more(hiddenCount)}
        </button>
      )}
    </Row>
  );
}

// --- Kanban Column & Cards ---

type ColumnTone = "primary" | "warning" | "success";

interface ToneVisual {
  accent: string;
  bg: string;
  border: string;
  text: string;
}

function columnVisual(tokens: ThemeTokens, tone: ColumnTone): ToneVisual {
  if (tone === "warning") {
    return {
      accent: tokens.status.warning,
      bg: tokens.status.warningBg,
      border: tokens.status.warningBorder,
      text: tokens.status.warning,
    };
  }
  if (tone === "success") {
    return {
      accent: tokens.status.success,
      bg: tokens.status.successBg,
      border: tokens.status.successBorder,
      text: tokens.status.success,
    };
  }
  return {
    accent: "rgb(116,173,223)",
    bg: "rgba(116,173,223,0.1)",
    border: "rgba(116,173,223,0.3)",
    text: "rgb(116,173,223)",
  };
}

function statusVisual(tokens: ThemeTokens, status: string): ToneVisual {
  const normalized = normalizeStatus(status);
  if (normalized === "Error") {
    return {
      accent: tokens.status.danger,
      bg: tokens.status.dangerBg,
      border: tokens.status.dangerBorder,
      text: tokens.status.danger,
    };
  }
  if (normalized === "ActionRequired") {
    return {
      accent: tokens.status.warning,
      bg: tokens.status.warningBg,
      border: tokens.status.warningBorder,
      text: tokens.status.warning,
    };
  }
  if (normalized === "Running") {
    return {
      accent: "rgb(116,173,223)",
      bg: "rgba(116,173,223,0.1)",
      border: "rgba(116,173,223,0.3)",
      text: "rgb(116,173,223)",
    };
  }
  if (normalized === "Completed") {
    return columnVisual(tokens, "success");
  }
  return {
    accent: tokens.text.quaternary,
    bg: tokens.fill.tertiary,
    border: tokens.stroke.tertiary,
    text: tokens.text.secondary,
  };
}

function KanbanColumn({ title, count, sessions, tone, taskIdToLabel, text, collapsedLimit }: {
  title: string; count: number; sessions: KanbanSession[]; tone: ColumnTone;
  taskIdToLabel: Map<string, string>;
  text: KanbanText;
  collapsedLimit?: number;
}) {
  const { tokens } = useHostTheme();
  const visual = columnVisual(tokens, tone);
  const [visibleCount, setVisibleCount] = useState(collapsedLimit || sessions.length);

  useEffect(() => {
    setVisibleCount(collapsedLimit || sessions.length);
  }, [collapsedLimit, sessions]);

  const canPage = collapsedLimit != null && sessions.length > collapsedLimit;
  const visibleSessions = canPage ? sessions.slice(0, visibleCount) : sessions;
  const hiddenCount = canPage ? Math.max(sessions.length - visibleCount, 0) : 0;
  const nextCount = collapsedLimit ? Math.min(hiddenCount, collapsedLimit) : hiddenCount;

  return (
    <Stack gap={6} style={{
      minWidth: 0, minHeight: 0, border: "none",
      borderRadius: 8, padding: 8, overflow: "hidden", display: "flex", flexDirection: "column",
      background: tokens.bg.chrome,
    }}>
      <Row justify="space-between" align="center" style={{ padding: "6px 4px" }}>
        <Row gap={6} align="center">
          <span style={{ width: 8, height: 8, borderRadius: 99, background: visual.accent, flexShrink: 0 }} />
          <Text style={{ fontSize: 13, fontWeight: 650, letterSpacing: 0 }}>{title}</Text>
        </Row>
        <span
          style={{
            minWidth: 22,
            height: 18,
            padding: "0 6px",
            borderRadius: 99,
            background: "transparent",
            border: `1px solid ${visual.border}`,
            color: visual.text,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            lineHeight: "16px",
            fontWeight: 560,
            boxSizing: "border-box",
          }}
        >
          {count}
        </span>
      </Row>
      <Stack gap={10} style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {sessions.length === 0 && (
          <Text tone="tertiary" size="small" style={{ padding: "8px 0" }}>{text.noSessions}</Text>
        )}
        {visibleSessions.map((session) => (
          <SessionCard key={session.id} session={session} tokens={tokens} taskIdToLabel={taskIdToLabel} text={text} />
        ))}
        {canPage && (
          <button
            type="button"
            onClick={() => {
              if (hiddenCount > 0 && collapsedLimit) {
                setVisibleCount((count) => Math.min(count + collapsedLimit, sessions.length));
              } else {
                setVisibleCount(collapsedLimit || sessions.length);
              }
            }}
            style={{
              height: 28,
              border: `1px solid ${tokens.stroke.tertiary}`,
              borderRadius: 6,
              background: tokens.bg.elevated,
              color: tokens.text.primary,
              cursor: "pointer",
              font: "inherit",
              fontSize: 11,
              fontWeight: 560,
              flexShrink: 0,
            }}
          >
            {hiddenCount > 0 ? text.showMore(nextCount) : text.less}
          </button>
        )}
      </Stack>
    </Stack>
  );
}

const SessionCard = memo(function SessionCard({ session, tokens, taskIdToLabel, text }: {
  session: KanbanSession;
  tokens: ThemeTokens;
  taskIdToLabel: Map<string, string>;
  text: KanbanText;
}) {
  // Resolve workspace label from taskId -> folder mapping, fallback to raw workspace
  const wsLabel = (session.taskId && taskIdToLabel.get(session.taskId)) || session.workspace;
  const visual = statusVisual(tokens, session.status);
  const dispatch = useCanvasAction();
  const [hovered, setHovered] = useState(false);

  const handleClick = useCallback(() => {
    dispatch({
      type: "aicoding.canvas.openQuestSession",
      taskId: session.taskId || session.id,
      sessionId: session.sessionId,
    });
  }, [dispatch, session.taskId, session.id, session.sessionId]);

  return (
    <Stack
      gap={7}
      onClick={handleClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        borderRadius: 8,
        background: tokens.bg.elevated,
        border: `1px solid ${tokens.stroke.tertiary}`,
        padding: "12px 14px",
        minWidth: 0,
        boxSizing: "border-box",
        cursor: "pointer",
        boxShadow: hovered ? "0 2px 8px rgba(0,0,0,0.08)" : "none",
        transition: "box-shadow 0.15s ease",
      }}
    >
      <Text style={{ fontSize: 13, fontWeight: 590, lineHeight: "18px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", letterSpacing: 0 }}>
        {session.title}
      </Text>
      {session.promptPreview && session.promptPreview !== session.title && (
        <Text tone="tertiary" size="small" style={{ fontSize: 11, lineHeight: "14px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {session.promptPreview}
        </Text>
      )}
      <Row justify="space-between" align="center" gap={4}>
        <Row gap={4} align="center" style={{ minWidth: 0, flex: 1 }}>
          <Text tone="tertiary" size="small" style={{ fontSize: 10, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {wsLabel}
          </Text>
          {session.messages ? (
            <Text tone="tertiary" size="small" style={{ fontSize: 10, flexShrink: 0 }}>{text.messages(session.messages)}</Text>
          ) : null}
        </Row>
      </Row>
      <Row align="center" gap={4}>
        <SessionStatusBadge status={session.status} visual={visual} text={text} />
      </Row>
    </Stack>
  );
});

const SessionStatusBadge = memo(function SessionStatusBadge({ status, visual, text }: {
  status: string;
  visual: ToneVisual;
  text: KanbanText;
}) {
  const label = statusLabel(status, text);

  return (
    <span style={{
      display: "inline-flex", alignItems: "center", height: 18, maxWidth: 120, padding: "0 7px",
      borderRadius: 999, background: visual.bg, color: visual.text, border: `1px solid ${visual.border}`,
      fontSize: 10, lineHeight: "16px",
      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", flexShrink: 0,
    }}>
      {label}
    </span>
  );
});

const SessionAction = memo(function SessionAction({ session, tokens, text, style }: {
  session: KanbanSession;
  tokens: ThemeTokens;
  text: KanbanText;
  style?: CSSProperties;
}) {
  const dispatch = useCanvasAction();
  const [pending, setPending] = useState(false);

  const handleOpen = useCallback(() => {
    if (pending) return;
    setPending(true);
    dispatch({
      type: "aicoding.canvas.openQuestSession",
      taskId: session.taskId || session.id,
      sessionId: session.sessionId,
    });
    window.setTimeout(() => setPending(false), 900);
  }, [pending, dispatch, session.taskId, session.id, session.sessionId]);

  return (
    <button type="button" disabled={pending} onClick={handleOpen} style={{
      height: 22, padding: "0 8px", border: "1px solid transparent", borderRadius: 5,
      background: "transparent", color: tokens.primary.text,
      cursor: pending ? "default" : "pointer", opacity: pending ? 0.62 : 1,
      font: "inherit", fontSize: 11, fontWeight: 650, whiteSpace: "nowrap", flexShrink: 0,
      ...style,
    }}>
      {pending ? text.opening : text.open}
    </button>
  );
});

// --- Utils ---

function hasQuestWorkspaceData(data: QuestWorkspacesData): boolean {
  return (data.folders?.length || 0) > 0 || Object.keys(data.tasksByFolder || {}).length > 0;
}

function hasQuestSessionData(data: QuestSessionsData): boolean {
  return (data.sessions?.length || 0) > 0;
}

function hasKanbanData(data: KanbanData): boolean {
  const columns = data.columns || EMPTY_KANBAN.columns;
  return (data.totalSessions || 0) > 0 ||
    columns.running.length > 0 ||
    columns.blocked.length > 0 ||
    columns.ready.length > 0;
}

function isCurrentQuestWorkspaceData(data: QuestWorkspacesData): boolean {
  return data.schemaVersion != null || hasQuestWorkspaceData(data);
}

function isCurrentQuestSessionData(data: QuestSessionsData): boolean {
  return data.schemaVersion != null || hasQuestSessionData(data);
}

function isCurrentKanbanData(data: KanbanData): boolean {
  return data.schemaVersion != null || hasKanbanData(data);
}

function applyKanbanDelta(current: KanbanData, delta: QuestKanbanDelta): KanbanData {
  const byId = new Map<string, KanbanSession>();
  const currentColumns = current.columns || EMPTY_KANBAN.columns;

  for (const key of KANBAN_COLUMN_KEYS) {
    for (const session of currentColumns[key] || []) {
      const id = sessionIdentity(session);
      if (id) {
        byId.set(id, normalizeKanbanSession(session, id));
      }
    }
  }

  for (const id of delta.removeIds || []) {
    if (id) {
      removeSessionByIdentity(byId, id);
    }
  }

  for (const session of delta.upsert || []) {
    const id = sessionIdentity(session);
    if (!id) continue;
    byId.set(id, normalizeKanbanSession(session, id));
  }

  const columns: KanbanData["columns"] = { running: [], blocked: [], ready: [] };
  for (const session of byId.values()) {
    columns[mapToColumn(session.status)].push(session);
  }
  sortKanbanColumns(columns);

  return {
    ...current,
    schemaVersion: current.schemaVersion || 1,
    version: typeof delta.version === "number" ? delta.version : current.version,
    updatedAt: latestUpdatedAt(columns.running, columns.blocked, columns.ready) || delta.updatedAt || current.updatedAt,
    columns,
    totalSessions: byId.size,
  };
}

function normalizeKanbanSession(session: KanbanSession, id: string): KanbanSession {
  return {
    ...session,
    id,
    taskId: session.taskId || id,
    sessionId: session.sessionId || `${id}.session.execution`,
    title: compactTitle(session.title || "Untitled Quest", 96),
    status: normalizeStatus(session.status || "Pending"),
    workspace: session.workspace || "",
    projectPath: session.projectPath || "",
    updatedAt: session.updatedAt || new Date().toISOString(),
    sessionFile: session.sessionFile || `quest:${id}`,
    promptPreview: compactTitle(session.promptPreview || "", 160),
    source: session.source || "quest",
    messages: session.messages || 0,
  };
}

function sessionIdentity(session: KanbanSession): string {
  return String(session.taskId || session.id || "");
}

function hasKanbanDeltaChanges(delta: QuestKanbanDelta): boolean {
  return (delta.upsert?.length || 0) > 0 || (delta.removeIds?.length || 0) > 0;
}

function isKanbanDeltaOlderThanBase(delta: QuestKanbanDelta, baseData: KanbanData): boolean {
  const deltaTime = dateMillis(delta.updatedAt);
  const baseTime = dateMillis(baseData.updatedAt);
  return deltaTime > 0 && baseTime > 0 && deltaTime < baseTime;
}

function mergeKanbanDeltaOverlay(current: QuestKanbanDelta, next: QuestKanbanDelta): QuestKanbanDelta {
  const upsertById = new Map<string, KanbanSession>();
  for (const session of current.upsert || []) {
    const id = sessionIdentity(session);
    if (id) {
      upsertById.set(id, session);
    }
  }

  const removeIds = new Set(current.removeIds || []);
  for (const id of next.removeIds || []) {
    if (!id) {
      continue;
    }
    removeSessionByIdentity(upsertById, id);
    removeIds.add(id);
  }

  for (const session of next.upsert || []) {
    const id = sessionIdentity(session);
    if (!id) {
      continue;
    }
    upsertById.set(id, session);
    removeIds.delete(id);
    removeIds.delete(String(session.id || ""));
    removeIds.delete(String(session.sessionId || ""));
  }

  return {
    schemaVersion: next.schemaVersion ?? current.schemaVersion,
    version: next.version ?? current.version,
    updatedAt: next.updatedAt ?? current.updatedAt,
    upsert: Array.from(upsertById.values()),
    removeIds: Array.from(removeIds),
  };
}

function removeSessionByIdentity(sessions: Map<string, KanbanSession>, rawId: string): void {
  const id = String(rawId || "");
  if (!id) return;

  sessions.delete(id);
  for (const [key, session] of sessions) {
    if (session.id === id || session.taskId === id || session.sessionId === id) {
      sessions.delete(key);
    }
  }
}

function sortKanbanColumns(columns: KanbanData["columns"]): void {
  const byDate = (a: KanbanSession, b: KanbanSession) =>
    dateMillis(b.updatedAt) - dateMillis(a.updatedAt);
  for (const key of KANBAN_COLUMN_KEYS) {
    columns[key].sort(byDate);
  }
}

function buildKanbanData(
  wsData: QuestWorkspacesData,
  sessionData: QuestSessionsData,
  legacyKanbanData: KanbanData,
): KanbanData {
  if (!hasQuestWorkspaceData(wsData)) {
    if (wsData.schemaVersion != null) {
      return {
        ...EMPTY_KANBAN,
        schemaVersion: 1,
        updatedAt: wsData.updatedAt,
      };
    }
    return hasKanbanData(legacyKanbanData) ? legacyKanbanData : EMPTY_KANBAN;
  }

  const sessionIndex = new Map<string, KanbanSession>();
  for (const session of sessionData.sessions || []) {
    const taskId = session.taskId || session.id;
    if (taskId) {
      sessionIndex.set(taskId, session);
    }
  }

  const running: KanbanSession[] = [];
  const blocked: KanbanSession[] = [];
  const ready: KanbanSession[] = [];

  for (const folder of wsData.folders || []) {
    const tasks = wsData.tasksByFolder?.[folder.path] || [];
    for (const task of tasks) {
      const session = convertTaskToSession(task, folder, sessionIndex);
      const column = mapToColumn(session.status);
      if (column === "running") running.push(session);
      else if (column === "blocked") blocked.push(session);
      else ready.push(session);
    }
  }

  sortKanbanColumns({ running, blocked, ready });

  const totalSessions = running.length + blocked.length + ready.length;
  return {
    schemaVersion: 1,
    updatedAt: latestUpdatedAt(running, blocked, ready),
    columns: { running, blocked, ready },
    totalSessions,
  };
}

function convertTaskToSession(
  task: QuestTask,
  folder: QuestFolder,
  sessionIndex: Map<string, KanbanSession>,
): KanbanSession {
  const taskId = String(task.id || "");
  const enrichment = sessionIndex.get(taskId);
  const updatedAt = formatTimestamp(task.lastUserQueryAt || task.updatedAtTimestamp || task.createdAt) || enrichment?.updatedAt || "";

  return {
    id: taskId,
    taskId,
    sessionId: String(task.executionSessionId || enrichment?.sessionId || `${taskId}.session.execution`),
    title: compactTitle(task.title || task.name || enrichment?.title || "Untitled Quest", 96),
    status: normalizeStatus(String(task.status || enrichment?.status || "Pending")),
    workspace: folder.label,
    projectPath: String(task.filePath || folder.path || ""),
    updatedAt,
    sessionFile: enrichment?.sessionFile || `quest:${taskId}`,
    promptPreview: compactTitle(task.query || enrichment?.promptPreview || "", 160),
    source: "quest",
    messages: enrichment?.messages || 0,
  };
}

function mapToColumn(status: string): "running" | "blocked" | "ready" {
  const normalized = normalizeStatus(status);
  if (normalized === "Running") return "running";
  if (normalized === "ActionRequired" || normalized === "Error") return "blocked";
  return "ready";
}

function statusLabel(status: string, text: KanbanText): string {
  const normalized = normalizeStatus(status);
  if (normalized === "ActionRequired") return text.actionRequired;
  if (normalized === "Error") return text.error;
  if (normalized === "Running") return text.running;
  if (normalized === "Stopped") return text.stopped;
  if (normalized === "Pending") return text.pending;
  if (normalized === "Completed") return text.completed;
  return normalized;
}

function normalizeStatus(status: string): string {
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

function compactTitle(value: string | undefined, limit = 72): string {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 1)}...`;
}

function formatTimestamp(timestamp: number | undefined): string {
  if (!timestamp) return "";
  const millis = timestamp < 10_000_000_000 ? timestamp * 1000 : timestamp;
  const date = new Date(millis);
  return Number.isNaN(date.getTime()) ? "" : date.toISOString();
}

function latestUpdatedAt(...groups: KanbanSession[][]): string | undefined {
  let latest = 0;
  for (const sessions of groups) {
    for (const session of sessions) {
      const time = dateMillis(session.updatedAt);
      if (time > latest) {
        latest = time;
      }
    }
  }
  return latest > 0 ? new Date(latest).toISOString() : undefined;
}

function dateMillis(iso: string | undefined): number {
  if (!iso) return 0;
  const time = new Date(iso).getTime();
  return Number.isNaN(time) ? 0 : time;
}
