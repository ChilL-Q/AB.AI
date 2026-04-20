// Shared types used by both frontend-web and mobile

export type UserRole = "owner" | "admin" | "manager" | "mechanic";
export type SubscriptionPlan = "start" | "pro" | "business" | "enterprise";
export type SubscriptionStatus = "trialing" | "active" | "past_due" | "canceled";
export type ConversationChannel = "whatsapp" | "telegram" | "sms";
export type CampaignType = "one_time" | "recurring" | "triggered";
export type CampaignStatus = "draft" | "running" | "paused" | "completed" | "archived";
export type AgentMode = "auto" | "semi_auto" | "manual";

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    has_next: boolean;
  };
}
