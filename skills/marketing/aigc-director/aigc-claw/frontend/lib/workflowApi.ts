/**
 * 工作流 API 客户端
 */

/**
 * Streaming endpoints must bypass the Next.js rewrite proxy because it buffers
 * the entire upstream response before forwarding, which breaks SSE real-time delivery.
 * Non-streaming endpoints can still go through the proxy (relative URL).
 */
const STREAM_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface StageInfo {
  id: string;
  name: string;
  order: number;
  description: string;
}

export interface ProjectStatus {
  session_id: string;
  current_stage: string;
  status: string;
  error: string | null;
  stages_completed: string[];
}

export interface StreamEvent {
  type: 'progress' | 'heartbeat' | 'stage_complete' | 'error' | 'content';
  message?: string;
  phase?: string;
  step_desc?: string;
  percent?: number;
  stage?: string;
  status?: string;
  requires_intervention?: boolean;
  payload_summary?: any;
  content?: string;
  time?: number;
  data?: any;
}

export async function fetchStages(): Promise<StageInfo[]> {
  const resp = await fetch('/api/stages');
  const data = await resp.json();
  return data.stages;
}

export async function fetchSessions(): Promise<any[]> {
  const resp = await fetch('/api/sessions');
  const data = await resp.json();
  return data.sessions || [];
}

export async function startProject(params: {
  idea: string;
  style?: string;
  video_ratio?: string;
  llm_model?: string;
  vlm_model?: string;
  image_t2i_model?: string;
  image_it2i_model?: string;
  video_model?: string;
  scene_number?: number;
  enable_concurrency?: boolean;
}): Promise<{ session_id: string; status: string; params: any }> {
  const resp = await fetch('/api/project/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return resp.json();
}

export async function getProjectStatus(sessionId: string): Promise<ProjectStatus> {
  const resp = await fetch(`/api/project/${sessionId}/status`);
  if (!resp.ok) throw new Error('Failed to get project status');
  return resp.json();
}

// 从 sessions json 文件读取状态（供前端轮询使用，即使后端重启也能获取状态）
export async function getProjectStatusFromDisk(sessionId: string): Promise<any> {
  const resp = await fetch(`/api/project/${sessionId}/status/from_disk`);
  if (!resp.ok) throw new Error('Failed to get project status from disk');
  return resp.json();
}

export async function getArtifact(sessionId: string, stage: string): Promise<any> {
  const resp = await fetch(`/api/project/${sessionId}/artifact/${stage}`);
  if (!resp.ok) throw new Error(`Artifact for stage '${stage}' not found`);
  return resp.json();
}

export async function checkSceneAssets(sessionId: string, sceneNumber: number): Promise<{
  scene_number: number;
  reference_images: number;
  videos: number;
  shot_count: number;
}> {
  const resp = await fetch(`/api/project/${sessionId}/scene/${sceneNumber}/assets`);
  if (!resp.ok) return { scene_number: sceneNumber, reference_images: 0, videos: 0, shot_count: 0 };
  return resp.json();
}

export async function executeStage(
  sessionId: string,
  stage: string,
  inputData: Record<string, any> = {},
  signal?: AbortSignal,
): Promise<Response> {
  return fetch(`${STREAM_API_BASE}/api/project/${sessionId}/execute/${stage}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputData),
    signal,
  });
}

export async function intervene(
  sessionId: string,
  stage: string,
  modifications: Record<string, any>,
): Promise<Response> {
  // Use STREAM_API_BASE to bypass Next.js proxy (SSE endpoint)
  return fetch(`${STREAM_API_BASE}/api/project/${sessionId}/intervene`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stage, modifications }),
  });
}

export async function stopProject(sessionId: string): Promise<{ status: string }> {
  const resp = await fetch(`/api/project/${sessionId}/stop`, {
    method: 'POST',
  });
  return resp.json();
}

export async function updateModels(
  sessionId: string,
  models: Partial<Record<string, string>>,
): Promise<{ status: string }> {
  const resp = await fetch(`/api/project/${sessionId}/models`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(models),
  });
  return resp.json();
}

export async function deleteSession(
  sessionId: string,
  password: string,
): Promise<{ status: string }> {
  const resp = await fetch(`/api/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: '删除失败' }));
    throw new Error(err.detail || '删除失败');
  }
  return resp.json();
}

export async function saveSelections(
  sessionId: string,
  stage: string,
  selections: Record<string, any>,
): Promise<{ status: string }> {
  const resp = await fetch(`/api/project/${sessionId}/artifact/${stage}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(selections),
  });
  if (!resp.ok) throw new Error('保存选项失败');
  return resp.json();
}

export async function continueWorkflow(sessionId: string): Promise<{ status: string; next_stage?: string }> {
  const resp = await fetch(`/api/project/${sessionId}/continue`, {
    method: 'POST',
  });
  return resp.json();
}

export async function* parseStreamEvents(response: Response): AsyncGenerator<StreamEvent> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // keep incomplete trailing line in buffer
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event: StreamEvent = JSON.parse(line);
        if (event.type !== 'heartbeat') yield event;
      } catch { /* skip malformed */ }
    }
  }
  // Process any remaining data in buffer after stream ends
  if (buffer.trim()) {
    try {
      const event: StreamEvent = JSON.parse(buffer);
      if (event.type !== 'heartbeat') yield event;
    } catch { /* skip malformed */ }
  }
}
