export interface Client {
  id: string;
  team_id: string;
  full_name: string;
  phone: string;
  email: string | null;
  total_visits: number;
  total_spent: string;
  last_visit_at: string | null;
  do_not_contact: boolean;
  tags: string[];
}

export interface Conversation {
  id: string;
  client_id: string;
  channel: "whatsapp" | "telegram" | "sms";
  status: "active" | "resolved" | "escalated";
  last_message_at: string | null;
  client: { id: string; full_name: string; phone: string } | null;
  last_message_preview: string | null;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  direction: "inbound" | "outbound";
  text: string | null;
  sent_by: "ai" | "human" | "system";
  sent_at: string | null;
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