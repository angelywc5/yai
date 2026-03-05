/* YAI API 客户端 — 所有后端调用封装 */

const BASE = "/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    public body: Record<string, unknown>,
  ) {
    super(body?.message as string || body?.detail as string || `HTTP ${status}`);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

/* ========== Auth ========== */
export const auth = {
  register: (data: { email: string; password: string; username: string; display_name: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { email: string; password: string }) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request<import("./types").User>("/auth/me"),
  refresh: () => request("/auth/refresh", { method: "POST" }),
  resendVerification: (email: string) =>
    request("/auth/resend-verification", { method: "POST", body: JSON.stringify({ email }) }),
};

/* ========== Characters ========== */
export const characters = {
  get: (id: string) => request<import("./types").CharacterResponse>(`/characters/${id}`),
  publicList: (page = 1, size = 20, sort = "popular") =>
    request<import("./types").PaginatedResponse<import("./types").CharacterPublicResponse>>(
      `/characters/public/list?page=${page}&size=${size}&sort=${sort}`,
    ),
  myList: (page = 1, size = 20) =>
    request<import("./types").PaginatedResponse<import("./types").CharacterPublicResponse>>(
      `/characters/me/list?page=${page}&size=${size}`,
    ),
  search: (q: string, page = 1, size = 20, tag?: string) =>
    request<import("./types").PaginatedResponse<import("./types").CharacterPublicResponse>>(
      `/characters/search?q=${encodeURIComponent(q)}&page=${page}&size=${size}${tag ? `&tag=${encodeURIComponent(tag)}` : ""}`,
    ),
  create: (data: Record<string, unknown>) =>
    request<import("./types").CharacterResponse>("/characters/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Record<string, unknown>) =>
    request<import("./types").CharacterResponse>(`/characters/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/characters/${id}`, { method: "DELETE" }),
};

/* ========== Scenes ========== */
export const scenes = {
  get: (id: string) => request<import("./types").SceneResponse>(`/scenes/${id}`),
  publicList: (page = 1, size = 20, sort = "popular") =>
    request<import("./types").PaginatedResponse<import("./types").SceneResponse>>(
      `/scenes/public/list?page=${page}&size=${size}&sort=${sort}`,
    ),
  myList: (page = 1, size = 20) =>
    request<import("./types").PaginatedResponse<import("./types").SceneResponse>>(
      `/scenes/me/list?page=${page}&size=${size}`,
    ),
  search: (q: string, page = 1, size = 20, tag?: string) =>
    request<import("./types").PaginatedResponse<import("./types").SceneResponse>>(
      `/scenes/search?q=${encodeURIComponent(q)}&page=${page}&size=${size}${tag ? `&tag=${encodeURIComponent(tag)}` : ""}`,
    ),
  create: (data: Record<string, unknown>) =>
    request<import("./types").SceneResponse>("/scenes/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Record<string, unknown>) =>
    request<import("./types").SceneResponse>(`/scenes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/scenes/${id}`, { method: "DELETE" }),
  addCharacter: (sceneId: string, data: { character_id: string; role_in_scene?: string; is_recommended?: boolean }) =>
    request(`/scenes/${sceneId}/characters`, { method: "POST", body: JSON.stringify(data) }),
  removeCharacter: (sceneId: string, charId: string) =>
    request(`/scenes/${sceneId}/characters/${charId}`, { method: "DELETE" }),
};

/* ========== Chat ========== */
export const chat = {
  history: (characterId: string, sessionId?: string, beforeMessageId?: string, limitRounds = 20) => {
    const params = new URLSearchParams();
    if (sessionId) params.set("session_id", sessionId);
    if (beforeMessageId) params.set("before_message_id", beforeMessageId);
    params.set("limit_rounds", String(limitRounds));
    return request<import("./types").ChatHistoryPage>(`/chat/history/${characterId}?${params}`);
  },
  sessions: (characterId: string) =>
    request<import("./types").SessionResponse[]>(`/chat/sessions/${characterId}`),
  deleteSession: (sessionId: string) =>
    request(`/chat/sessions/${sessionId}`, { method: "DELETE" }),
  summaries: (sessionId: string) =>
    request<import("./types").StorySummaryResponse[]>(`/chat/summaries/${sessionId}`),
  recentCharacters: (limit = 10) =>
    request<import("./types").RecentCharacterResponse[]>(`/chat/recent-characters?limit=${limit}`),
  editMessage: (messageId: string, data: { content: string; model_tier: string }) =>
    request(`/chat/messages/${messageId}/edit`, { method: "PUT", body: JSON.stringify(data) }),
  regenerate: (messageId: string, data: { model_tier: string }) =>
    request(`/chat/messages/${messageId}/regenerate`, { method: "POST", body: JSON.stringify(data) }),
  deleteMessage: (messageId: string) =>
    request(`/chat/messages/${messageId}`, { method: "DELETE" }),
  feedback: (messageId: string, data: { feedback: string }) =>
    request(`/chat/messages/${messageId}/feedback`, { method: "PUT", body: JSON.stringify(data) }),
  pin: (messageId: string) =>
    request(`/chat/messages/${messageId}/pin`, { method: "PUT" }),
};

/* SSE stream — returns a ReadableStream reader */
export function streamChat(body: import("./types").ChatRequest): {
  reader: Promise<ReadableStreamDefaultReader<Uint8Array>>;
  abort: () => void;
} {
  const controller = new AbortController();
  const reader = fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
    signal: controller.signal,
  }).then((res) => {
    if (!res.ok) throw new Error(`SSE failed: ${res.status}`);
    return res.body!.getReader();
  });
  return { reader, abort: () => controller.abort() };
}

/* ========== Credits ========== */
export const credits = {
  balance: () => request<import("./types").CreditBalanceResponse>("/credits/balance"),
  transactions: (page = 1, size = 20) =>
    request<import("./types").PaginatedResponse<import("./types").TransactionResponse>>(
      `/credits/transactions?page=${page}&size=${size}`,
    ),
  pricing: () => request<Record<string, number>>("/credits/pricing"),
};

/* ========== Admin ========== */
export const admin = {
  users: (page = 1, size = 20, q?: string) =>
    request<import("./types").PaginatedResponse<import("./types").UserDetailResponse>>(
      `/admin/users?page=${page}&size=${size}${q ? `&q=${encodeURIComponent(q)}` : ""}`,
    ),
  userDetail: (userId: string) =>
    request<import("./types").UserDetailResponse>(`/admin/users/${userId}`),
  adjustCredits: (userId: string, data: { user_id: string; amount: number; reason: string }) =>
    request(`/admin/users/${userId}/credits`, { method: "PUT", body: JSON.stringify(data) }),
  updatePermissions: (userId: string, data: { can_create_character?: boolean; can_create_scene?: boolean }) =>
    request(`/admin/users/${userId}/permissions`, { method: "PUT", body: JSON.stringify(data) }),
  consumption: (userId: string, days = 7) =>
    request<import("./types").AdminConsumptionResponse>(`/admin/users/${userId}/consumption?window_days=${days}`),
  userCharacters: (userId: string) =>
    request<import("./types").PaginatedResponse<import("./types").CharacterPublicResponse>>(
      `/admin/users/${userId}/characters`,
    ),
  deleteUserCharacter: (userId: string, charId: string) =>
    request(`/admin/users/${userId}/characters/${charId}`, { method: "DELETE" }),
  userScenes: (userId: string) =>
    request<import("./types").PaginatedResponse<import("./types").SceneResponse>>(
      `/admin/users/${userId}/scenes`,
    ),
  deleteUserScene: (userId: string, sceneId: string) =>
    request(`/admin/users/${userId}/scenes/${sceneId}`, { method: "DELETE" }),
  models: () => request<import("./types").ModelStatusResponse>("/admin/models"),
  toggleModel: (tier: string, enabled: boolean) =>
    request(`/admin/models/${tier}/toggle`, { method: "PUT", body: JSON.stringify({ enabled }) }),
};

export { ApiError };
