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
