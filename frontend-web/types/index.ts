export type UserRole = "owner" | "admin" | "manager" | "mechanic";

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  avatar_url: string | null;
  role: UserRole;
  team_id: string | null;
  email_verified_at: string | null;
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  timezone: string;
  locale: string;
  onboarding_completed: boolean;
  created_at: string;
}

export interface Client {
  id: string;
  team_id: string;
  full_name: string;
  phone: string;
  email: string | null;
  birth_date: string | null;
  telegram_username: string | null;
  whatsapp_opted_in: boolean;
  do_not_contact: boolean;
  total_visits: number;
  total_spent: string;
  last_visit_at: string | null;
  source: string;
  tags: string[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    has_next: boolean;
  };
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type ConversationChannel = "whatsapp" | "telegram" | "sms";
export type ConversationStatus = "active" | "resolved" | "escalated";

export interface ConversationClientMini {
  id: string;
  full_name: string;
  phone: string;
  email: string | null;
}

export interface Conversation {
  id: string;
  team_id: string;
  client_id: string;
  channel: ConversationChannel;
  status: ConversationStatus;
  last_message_at: string | null;
  created_at: string;
  client: ConversationClientMini | null;
  last_message_preview: string | null;
  unread_count: number;
}

export type MessageDirection = "inbound" | "outbound";
export type MessageStatus = "pending" | "sent" | "delivered" | "read" | "failed";
export type MessageSentBy = "ai" | "human" | "system";

export interface Message {
  id: string;
  conversation_id: string;
  direction: MessageDirection;
  text: string | null;
  media_url: string | null;
  status: MessageStatus;
  sent_by: MessageSentBy;
  user_id: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  created_at: string;
}

/**
 * Cursor page returned by `GET /conversations/{id}/messages`.
 * `data` is ordered oldest→newest within the page; pass `next_cursor`
 * as `?before=` to fetch the previous (older) slice.
 */
export interface MessagePage {
  data: Message[];
  next_cursor: string | null;
  has_more: boolean;
}

export type AIAgentMode = "auto" | "semi_auto" | "manual";

export interface AIAgentConfig {
  id: string;
  team_id: string;
  mode: AIAgentMode;
  is_active: boolean;
  personality: string | null;
  tone: string;
  knowledge_base: Record<string, string>;
  forbidden_topics: string[];
  escalation_rules: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AISuggestion {
  conversation_id: string;
  text: string;
}

export type OutreachStatus = "pending" | "sent" | "replied" | "escalated" | "failed";

export interface OutreachAction {
  id: string;
  client_id: string;
  client_name: string;
  status: OutreachStatus;
  reason: Record<string, string>;
  message_text: string | null;
  sent_at: string | null;
  replied_at: string | null;
  resulted_in_visit: boolean;
  resulted_in_revenue: string;
  created_at: string;
}

export interface OutreachMetrics {
  total_outreach: number;
  replied: number;
  reply_rate: number;
  resulted_in_visit: number;
  retention_rate: number;
  total_revenue: number;
  escalated: number;
}

export interface Car {
  id: string;
  client_id: string;
  brand: string;
  model: string;
  year: number | null;
  color: string | null;
  license_plate: string | null;
  vin: string | null;
  mileage: number | null;
  last_service_mileage: number | null;
  last_service_at: string | null;
  created_at: string;
}

export interface VisitServiceItem {
  name: string;
  price: string;
}

export interface Visit {
  id: string;
  team_id: string;
  client_id: string;
  car_id: string | null;
  mechanic_id: string | null;
  visited_at: string;
  total_amount: string;
  services: VisitServiceItem[];
  notes: string | null;
  source: string;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  channels: string[];
  read_at: string | null;
  created_at: string;
}

export interface Template {
  id: string;
  team_id: string | null;
  name: string;
  category: string;
  content: string;
  channels: string[];
  whatsapp_template_id: string | null;
  whatsapp_status: string | null;
  created_at: string;
  updated_at: string | null;
}

export type CampaignType = "one_time" | "recurring" | "triggered";
export type CampaignStatus = "draft" | "running" | "paused" | "completed" | "archived";

export interface ImportLog {
  id: string;
  team_id: string;
  user_id: string;
  source: string;
  filename: string | null;
  file_url: string | null;
  rows_total: number;
  rows_imported: number;
  rows_failed: number;
  rows_skipped: number;
  errors: ImportErrorRow[];
  status: "processing" | "completed" | "failed" | "rolled_back";
  completed_at: string | null;
  created_at: string;
}

export interface ImportErrorRow {
  row: number;
  phone: string;
  reason: string;
}

export interface Campaign {
  id: string;
  team_id: string;
  created_by: string;
  name: string;
  description: string | null;
  type: CampaignType;
  status: CampaignStatus;
  trigger: Record<string, unknown>;
  channels: string[];
  schedule: Record<string, unknown>;
  template_id: string | null;
  stats: Record<string, unknown>;
  ab_test_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}

export type ServiceIntervalUnit = "km" | "days" | "months";

export interface ServiceInterval {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  interval_value: number;
  interval_unit: ServiceIntervalUnit;
  is_active: boolean;
}

export interface DueService {
  client_id: string;
  client_name: string;
  car_id: string;
  car_name: string;
  service_name: string;
  reason: string;
}
