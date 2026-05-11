"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Users,
  MessageSquare,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Loader2,
  Bot,
  CheckCircle2,
  Phone,
  Clock,
  UserPlus,
  Wallet,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMe } from "@/hooks/use-me";
import { formatMoney, formatTimeAgo } from "@/lib/formatters";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DashboardData {
  active_clients: number;
  conversations_today: number;
  total_cars: number;
  retention_rate: number;
  revenue_week: number;
  revenue_delta: number;
  outreach_returned: number;
  outreach_total: number;
  outreach_revenue: number;
  chart: { d: string; revenue: number; visits: number }[];
  activity: { type: string; title: string; meta: string; time: string }[];
}

const ACTIVITY_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  outreach: Bot,
  visit: CheckCircle2,
  client: UserPlus,
  escalation: Phone,
};

const ACTIVITY_STYLE: Record<string, { bg: string; icon: string }> = {
  outreach: { bg: "bg-amber-50 dark:bg-amber-500/10", icon: "text-amber-500" },
  visit: { bg: "bg-emerald-50 dark:bg-emerald-500/10", icon: "text-emerald-500" },
  client: { bg: "bg-sky-50 dark:bg-sky-500/10", icon: "text-sky-500" },
  escalation: { bg: "bg-rose-50 dark:bg-rose-500/10", icon: "text-rose-500" },
};

export default function DashboardPage() {
  const { data: me } = useMe();
  const firstName = me?.full_name?.split(" ")[0] ?? "";

  const { data: dash, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardData>("/analytics/dashboard")).data,
    enabled: !!me?.team_id,
  });

  const stats = [
    { label: "Активные клиенты", value: dash?.active_clients, icon: Users, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-500/10" },
    { label: "Диалоги сегодня", value: dash?.conversations_today, icon: MessageSquare, color: "text-sky-500", bg: "bg-sky-50 dark:bg-sky-500/10" },
    { label: "Возвратность", value: dash ? `${Math.round(dash.retention_rate * 100)}%` : null, icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-500/10" },
    { label: "Выручка / нед", value: dash ? formatMoney(dash.revenue_week) : null, icon: Wallet, color: "text-violet-500", bg: "bg-violet-50 dark:bg-violet-500/10" },
  ];

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Greeting */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Привет{firstName ? `, ${firstName}` : ""} 👋
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">Вот как идут дела на этой неделе</p>
        </div>
        <Button className="brand-gradient brand-gradient-text brand-shadow-sm h-9 text-sm font-semibold rounded-xl">
          <Sparkles className="h-4 w-4 mr-2" />
          Запустить AI-кампанию
        </Button>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map(({ label, value, icon: Icon, color, bg }) => (
              <Card key={label} className="border-0 shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className={cn("h-9 w-9 rounded-xl flex items-center justify-center", bg)}>
                      <Icon className={cn("h-4 w-4", color)} />
                    </div>
                  </div>
                  <div className="text-2xl font-bold tracking-tight">{value ?? "—"}</div>
                  <p className="text-xs text-muted-foreground mt-1">{label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* AI Outreach row */}
          {dash && dash.outreach_total > 0 && (
            <div className="grid gap-4 sm:grid-cols-3">
              <Card className="border-0 shadow-sm overflow-hidden">
                <div className="h-1 brand-gradient" />
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Bot className="h-4 w-4 text-primary" />
                    <span className="text-xs font-semibold text-muted-foreground">AI обратился</span>
                  </div>
                  <div className="text-2xl font-bold">{dash.outreach_total}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Вернулись: <span className="text-emerald-600 dark:text-emerald-400 font-medium">{dash.outreach_returned}</span>
                  </p>
                </CardContent>
              </Card>
              <Card className="border-0 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Wallet className="h-4 w-4 text-emerald-500" />
                    <span className="text-xs font-semibold text-muted-foreground">Выручка от AI</span>
                  </div>
                  <div className="text-2xl font-bold">{formatMoney(dash.outreach_revenue)}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Визитов: {dash.outreach_returned}
                  </p>
                </CardContent>
              </Card>
              <Card className="border-0 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-violet-500" />
                    <span className="text-xs font-semibold text-muted-foreground">Выручка / нед</span>
                  </div>
                  <div className="text-2xl font-bold">{formatMoney(dash.revenue_week)}</div>
                  {dash.revenue_delta !== 0 && (
                    <div className="flex items-center gap-1 mt-1">
                      <Badge variant={dash.revenue_delta >= 0 ? "success" : "destructive"} className="text-[10px] px-1.5 py-0">
                        {dash.revenue_delta >= 0 ? <ArrowUpRight className="h-2.5 w-2.5" /> : <ArrowDownRight className="h-2.5 w-2.5" />}
                        {Math.abs(dash.revenue_delta).toFixed(1)}%
                      </Badge>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Chart + Activity */}
          <div className="grid gap-4 lg:grid-cols-5">
            {/* Chart */}
            <Card className="lg:col-span-3 border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Выручка за неделю</CardTitle>
                <CardDescription className="text-xs">Динамика оборота</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[260px]">
                  {(dash?.chart ?? []).length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={dash?.chart ?? []} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.2} />
                            <stop offset="100%" stopColor="#F59E0B" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                        <XAxis dataKey="d" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}K`} />
                        <Tooltip
                          contentStyle={{
                            background: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: 12,
                            fontSize: 12,
                            boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                          }}
                          formatter={(value: number, name) => [
                            name === "revenue" ? `${value}K ₸` : `${value} визитов`,
                            name === "revenue" ? "Выручка" : "Визиты",
                          ]}
                        />
                        <Area type="monotone" dataKey="revenue" stroke="#F59E0B" strokeWidth={2} fill="url(#rev)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                      Данных за неделю пока нет
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Activity feed */}
            <Card className="lg:col-span-2 border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Последние события</CardTitle>
                <CardDescription className="text-xs">AI-агент и автосервис</CardDescription>
              </CardHeader>
              <CardContent>
                {(dash?.activity ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-10">Событий пока нет</p>
                ) : (
                  <div className="space-y-3">
                    {(dash?.activity ?? []).map((act, i) => {
                      const Icon = ACTIVITY_ICON[act.type] ?? Clock;
                      const style = ACTIVITY_STYLE[act.type] ?? { bg: "bg-muted", icon: "text-muted-foreground" };
                      return (
                        <div key={i} className="flex gap-3">
                          <div className={cn("h-8 w-8 shrink-0 rounded-lg flex items-center justify-center", style.bg)}>
                            <Icon className={cn("h-3.5 w-3.5", style.icon)} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate leading-tight">{act.title}</p>
                            <p className="text-[11px] text-muted-foreground mt-0.5 truncate">
                              {act.meta}
                              {act.time && ` · ${formatTimeAgo(act.time)}`}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}