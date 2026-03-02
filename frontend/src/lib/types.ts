/* YAI 前端类型定义，映射后端 Pydantic Schema */

export type ModelTier = "speed" | "pro" | "elite";

/* ========== User ========== */
export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  email_verified: boolean;
  credits: number;
  is_admin: boolean;
  avatar_url: string | null;
  created_at: string;
}

/* ========== Character ========== */
export interface CharacterDefinition {
  identity: { name: string; background: string; beliefs: string };
  personality: string[];
  speech_style: {
    tone: string;
    catchphrases: string[];
    punctuation_habits: string;
  };
  sample_dialogues: { user: string; character: string }[];
}

export interface CharacterResponse {
  id: string;
  name: string;
  avatar_url: string | null;
  avatar_source: string;
  tagline: string;
  definition: CharacterDefinition;
  tags: string[];
  is_public: boolean;
  chat_count: number;
  like_count: number;
  creator_id: string;
  creator_username: string;
  creator_display_name: string;
  created_at: string;
}

export interface CharacterPublicResponse {
  id: string;
  name: string;
  avatar_url: string | null;
  avatar_source: string;
  tagline: string;
  tags: string[];
  personality_summary: string[];
  is_public: boolean;
  chat_count: number;
  like_count: number;
  creator_id: string;
  creator_username: string;
  creator_display_name: string;
  created_at: string;
}

/* ========== Scene ========== */
export interface SceneResponse {
  id: string;
  name: string;
  description: string;
  cover_image_url: string | null;
  cover_source: string;
  genre: string;
  time_period: string;
  setting_location: string;
  mood: string;
  player_objective: string;
  greeting: string;
  allow_character_selection: boolean;
  tags: string[];
  is_public: boolean;
  play_count: number;
  creator_id: string;
  creator_username: string;
  creator_display_name: string;
  characters: CharacterPublicResponse[];
  created_at: string;
}

/* ========== Chat ========== */
export interface ChatDirective {
  mode: string;
  instruction: string;
}

export interface ChatRequest {
  character_id: string;
  scene_id?: string;
  message: string;
  model_tier: ModelTier;
  session_id?: string;
  directives: ChatDirective[];
}

export interface MessageResponse {
  id: string;
  role: "user" | "assistant";
  content: string;
  token_count: number;
  turn_number: number;
  feedback: string | null;
  is_pinned: boolean;
  created_at: string;
}

export interface SessionResponse {
  session_id: string;
  character_id: string;
  character_name: string;
  character_avatar_url: string | null;
  last_message_preview: string;
  last_message_at: string;
  message_count: number;
  created_at: string;
}

export interface ChatHistoryPage {
  session_id: string;
  items: MessageResponse[];
  has_more: boolean;
  next_before_message_id: string | null;
}

export interface RecentCharacterResponse {
  character_id: string;
  character_name: string;
  character_avatar_url: string | null;
  character_tagline: string;
  last_session_id: string;
  last_message_preview: string;
  last_message_at: string;
}

/* ========== Credits ========== */
export interface CreditBalanceResponse {
  credits: number;
  tier_pricing: Record<string, number>;
}

export interface TransactionResponse {
  id: string;
  amount: number;
  reason: string;
  created_at: string;
}

/* ========== Paginated ========== */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/* ========== Story Summary ========== */
export interface StorySummaryResponse {
  id: string;
  from_turn: number;
  to_turn: number;
  summary: string;
  key_dialogues: string;
  created_at: string;
}

/* ========== Admin ========== */
export interface UserDetailResponse extends User {
  can_create_character: boolean;
  can_create_scene: boolean;
  character_count: number;
  scene_count: number;
}

export interface AdminConsumptionDaily {
  date: string;
  consumed: number;
  refunded: number;
  net: number;
}

export interface AdminConsumptionResponse {
  user_id: string;
  window_days: number;
  total_consumed: number;
  total_refunded: number;
  net_consumed: number;
  daily: AdminConsumptionDaily[];
  recent_transactions: TransactionResponse[];
}

export interface ModelStatusResponse {
  speed: boolean;
  pro: boolean;
  elite: boolean;
}

/* ========== SSE Events ========== */
export interface SSEEvent {
  event: "speech" | "action" | "emotion" | "done" | "error";
  data: string;
}

export interface YamlResponse {
  speech: string;
  action: string;
  emotion: string;
  inner_thought: string;
}
