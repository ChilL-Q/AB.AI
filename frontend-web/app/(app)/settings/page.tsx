"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save, User, Building2, MessageSquare, Shield, CreditCard } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { User as UserType, Team } from "@/types";

const TIMEZONES = [
  "Asia/Almaty",
  "Asia/Aqtau",
  "Asia/Aqtobe",
  "Asia/Atyrau",
  "Asia/Oral",
  "Europe/Moscow",
  "UTC",
];

const PLAN_LABELS: Record<string, string> = {
  start: "Start",
  pro: "Pro",
  business: "Business",
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  trialing: { label: "Пробный период", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  active: { label: "Активна", color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200" },
  past_due: { label: "Просрочена", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
  canceled: { label: "Отменена", color: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200" },
};

function BillingSection() {
  const qc = useQueryClient();

  const { data: plans } = useQuery({
    queryKey: ["billing-plans"],
    queryFn: async () => (await api.get<Record<string, PlanInfo>>("/billing/plans")).data,
  });

  const { data: sub } = useQuery({
    queryKey: ["billing-subscription"],
    queryFn: async () => (await api.get<SubscriptionInfo>("/billing/subscription")).data,
  });

  const checkoutMut = useMutation({
    mutationFn: async (plan: string) => {
      const { data } = await api.post("/billing/checkout", { plan });
      return data;
    },
    onSuccess: (data) => {
      if (data.url) {
        window.open(data.url, "_blank");
      } else {
        qc.invalidateQueries({ queryKey: ["billing-subscription"] });
      }
    },
  });

  const cancelMut = useMutation({
    mutationFn: async () => {
      await api.post("/billing/cancel");
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["billing-subscription"] });
    },
  });

  const currentPlan = sub?.plan ?? "start";
  const statusInfo = STATUS_LABELS[sub?.status ?? "trialing"];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">Тариф: {PLAN_LABELS[currentPlan] ?? currentPlan}</span>
            {statusInfo && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusInfo.color}`}>
                {statusInfo.label}
              </span>
            )}
          </div>
          {sub?.trial_ends_at && sub.status === "trialing" && (
            <p className="text-xs text-muted-foreground mt-1">
              Пробный период до {new Date(sub.trial_ends_at).toLocaleDateString("ru-RU")}
            </p>
          )}
          {sub?.current_period_end && sub.status === "active" && (
            <p className="text-xs text-muted-foreground mt-1">
              Оплачено до {new Date(sub.current_period_end).toLocaleDateString("ru-RU")}
            </p>
          )}
        </div>
        {sub?.cancel_at_period_end && (
          <span className="text-xs text-amber-600">Отменена в конце периода</span>
        )}
      </div>

      {plans && (
        <div className="grid gap-3 sm:grid-cols-3">
          {Object.entries(plans).map(([key, plan]) => {
            const isCurrent = key === currentPlan;
            return (
              <div
                key={key}
                className={`rounded-xl border p-4 transition-colors ${
                  isCurrent ? "border-primary bg-primary/5" : "hover:bg-muted/50"
                }`}
              >
                <div className="font-semibold">{plan.name}</div>
                <div className="text-lg font-bold text-primary mt-1">{plan.price_label}</div>
                <ul className="mt-2 space-y-1">
                  {plan.features.slice(0, 3).map((f: string, i: number) => (
                    <li key={i} className="text-xs text-muted-foreground">· {f}</li>
                  ))}
                </ul>
                <div className="mt-3">
                  {isCurrent ? (
                    <Button variant="outline" size="sm" className="w-full" disabled>
                      Текущий
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      className="w-full brand-gradient brand-gradient-text"
                      disabled={checkoutMut.isPending}
                      onClick={() => checkoutMut.mutate(key)}
                    >
                      {checkoutMut.isPending ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : null}
                      Выбрать
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {sub?.status === "active" && !sub?.cancel_at_period_end && currentPlan !== "start" && (
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            className="text-destructive hover:text-destructive"
            disabled={cancelMut.isPending}
            onClick={() => cancelMut.mutate()}
          >
            Отменить подписку
          </Button>
        </div>
      )}
    </div>
  );
}

interface PlanInfo {
  name: string;
  price_monthly: number;
  price_label: string;
  clients_limit: number | null;
  ai_messages_monthly: number | null;
  channels: string[];
  features: string[];
}

interface SubscriptionInfo {
  plan: string;
  status: string;
  trial_ends_at: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  payment_provider: string | null;
}

export default function SettingsPage() {
  const qc = useQueryClient();

  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<UserType>("/me")).data,
  });

  const { data: team, isLoading: teamLoading } = useQuery({
    queryKey: ["team"],
    queryFn: async () => {
      try {
        const { data } = await api.get<Team>("/team");
        return data;
      } catch {
        return null;
      }
    },
  });

  const { data: members } = useQuery({
    queryKey: ["team-members"],
    queryFn: async () => {
      try {
        const { data } = await api.get<UserType[]>("/me/team-members");
        return data;
      } catch {
        return [];
      }
    },
    enabled: !!me?.team_id,
  });

  // Profile form
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [profileSaved, setProfileSaved] = useState(false);

  const profileMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.patch<UserType>("/me", {
        full_name: fullName || undefined,
        phone: phone || undefined,
      });
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    },
  });

  // Team form
  const [teamName, setTeamName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Almaty");
  const [teamSaved, setTeamSaved] = useState(false);

  // Verify email
  const [, setVerifySent] = useState(false);
  const verifyMutation = useMutation({
    mutationFn: async () => {
      await api.post("/auth/verify-email/request");
    },
    onSuccess: () => {
      setVerifySent(true);
      setTimeout(() => setVerifySent(false), 3000);
    },
  });

  const teamMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.patch<Team>("/team", {
        name: teamName || undefined,
        timezone: timezone || undefined,
      });
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["team"] });
      setTeamSaved(true);
      setTimeout(() => setTeamSaved(false), 2000);
    },
  });

  // Init forms when data loads
  useEffect(() => {
    if (me && !fullName) {
      setFullName(me.full_name);
      setPhone(me.phone ?? "");
    }
  }, [me?.id]);

  useEffect(() => {
    if (team && !teamName) {
      setTeamName(team.name);
      setTimezone(team.timezone);
    }
  }, [team?.id]);

  if (meLoading || teamLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Настройки</h2>
        <p className="text-muted-foreground">Управление профилем и командой</p>
      </div>

      {/* ─── Profile ─── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="h-4 w-4 text-primary" /> Профиль
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              profileMutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="s-name">Имя</Label>
              <Input
                id="s-name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="s-email">Email</Label>
              <Input id="s-email" value={me?.email ?? ""} disabled className="bg-muted" />
              <p className="text-xs text-muted-foreground">Email нельзя изменить</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="s-phone">Телефон</Label>
              <Input
                id="s-phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+7 777 123 45 67"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={profileMutation.isPending}>
                {profileMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Сохранить
              </Button>
              {profileSaved && (
                <span className="text-sm text-emerald-600">Сохранено</span>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ─── Team ─── */}
      {team && (
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4 text-primary" /> Команда
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                teamMutation.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="t-name">Название</Label>
                <Input
                  id="t-name"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="t-tz">Часовой пояс</Label>
                <select
                  id="t-tz"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>

              {members && members.length > 0 && (
                <div className="space-y-2">
                  <Label>Участники</Label>
                  <div className="divide-y rounded-lg border">
                    {members.map((m) => (
                      <div key={m.id} className="flex items-center gap-3 px-3 py-2">
                        <div className="h-8 w-8 rounded-full brand-gradient text-white flex items-center justify-center text-xs font-bold shrink-0">
                          {m.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{m.full_name}</p>
                          <p className="text-xs text-muted-foreground truncate">{m.email}</p>
                        </div>
                        <span className="text-xs text-muted-foreground capitalize px-2 py-0.5 rounded-full bg-muted">
                          {m.role}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <Button type="submit" disabled={teamMutation.isPending}>
                  {teamMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Сохранить
                </Button>
                {teamSaved && (
                  <span className="text-sm text-emerald-600">Сохранено</span>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* ─── Channels (stubs) ─── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageSquare className="h-4 w-4 text-primary" /> Каналы связи
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <span className="text-lg">💬</span>
              </div>
              <div>
                <p className="text-sm font-medium">WhatsApp</p>
                <p className="text-xs text-muted-foreground">Подключите WhatsApp Business API</p>
              </div>
            </div>
            <Button variant="outline" size="sm" disabled>Скоро</Button>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <span className="text-lg">✈️</span>
              </div>
              <div>
                <p className="text-sm font-medium">Telegram</p>
                <p className="text-xs text-muted-foreground">Подключите Telegram Bot API</p>
              </div>
            </div>
            <Button variant="outline" size="sm" disabled>Скоро</Button>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                <span className="text-lg">📱</span>
              </div>
              <div>
                <p className="text-sm font-medium">SMS</p>
                <p className="text-xs text-muted-foreground">Отправка SMS через провайдера</p>
              </div>
            </div>
            <Button variant="outline" size="sm" disabled>Скоро</Button>
          </div>
        </CardContent>
      </Card>

      {/* ─── Billing ─── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <CreditCard className="h-4 w-4 text-primary" /> Подписка
          </CardTitle>
        </CardHeader>
        <CardContent>
          <BillingSection />
        </CardContent>
      </Card>

      {/* ─── Security (stub) ─── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-4 w-4 text-primary" /> Безопасность
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Подтверждение email</p>
              <p className="text-xs text-muted-foreground">
                {me?.email_verified_at ? "Подтверждён" : "Не подтверждён"}
              </p>
            </div>
            {!me?.email_verified_at && (
              <Button
                variant="outline"
                size="sm"
                disabled={verifyMutation.isPending}
                onClick={() => verifyMutation.mutate()}
              >
                {verifyMutation.isPending ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : null}
                Отправить письмо
              </Button>
            )}
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Сброс пароля</p>
              <p className="text-xs text-muted-foreground">Изменить текущий пароль</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => window.location.href = "/forgot-password"}>
              Сбросить
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Двухфакторная аутентификация</p>
              <p className="text-xs text-muted-foreground">Дополнительный уровень защиты</p>
            </div>
            <Button variant="outline" size="sm" disabled>Скоро</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}