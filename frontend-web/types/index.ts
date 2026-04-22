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
