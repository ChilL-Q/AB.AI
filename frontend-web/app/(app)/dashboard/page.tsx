"use client";

import {
  Users,
  MessageSquare,
  Car,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Phone,
  CheckCircle2,
  Clock,
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
import { cn } from "@/lib/utils";

type Stat = {
  label: string;
  value: string;
  delta: number;
  icon: React.ComponentType<{ className?: string }>;
  tone: "blue" | "violet" | "emerald" | "amber";
};

const STATS: Stat[] = [
  { label: "Активные клиенты", value: "1 284", delta: 12.4, icon: Users, tone: "blue" },
  { label: "Диалоги сегодня", value: "87", delta: 3.2, icon: MessageSquare, tone: "violet" },
  { label: "Автомобили в базе", value: "1 642", delta: 8.1, icon: Car, tone: "emerald" },
  { label: "Возвратность 60д", value: "42%", delta: -1.8, icon: TrendingUp, tone: "amber" },
];

const TONE: Record<Stat["tone"], string> = {
  blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  emerald: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

const CHART = [
  { d: "Пн", revenue: 240, visits: 18 },
  { d: "Вт", revenue: 320, visits: 22 },
  { d: "Ср", revenue: 280, visits: 20 },
  { d: "Чт", revenue: 410, visits: 29 },
  { d: "Пт", revenue: 520, visits: 34 },
  { d: "Сб", revenue: 680, visits: 41 },
  { d: "Вс", revenue: 390, visits: 25 },
];

const ACTIVITY = [
  { icon: MessageSquare, tone: "violet" as const, title: "AI-агент ответил Марату К.", meta: "WhatsApp · 2 мин назад" },
  { icon: CheckCircle2, tone: "emerald" as const, title: "Визит закрыт: Toyota Camry", meta: "Мастер — Саян · 12 мин назад" },
  { icon: Phone, tone: "blue" as const, title: "Новый клиент: Айжан Д.", meta: "Источник: 2GIS · 34 мин назад" },
  { icon: Clock, tone: "amber" as const, title: "Напоминание отправлено 18 клиентам", meta: "ТО через 30 дней · 1 ч назад" },
];

const TONE_SOFT: Record<"blue" | "violet" | "emerald" | "amber", string> = {
  blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  emerald: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

export default function DashboardPage() {
  const { data: me } = useMe();
  const firstName = me?.full_name?.split(" ")[0] ?? "";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Привет{firstName ? `, ${firstName}` : ""} 👋
          </h2>
          <p className="text-muted-foreground">Вот как идут дела в автосервисе на этой неделе</p>
        </div>
        <Button>
          <Sparkles className="h-4 w-4 mr-2" />
          Запустить AI-кампанию
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {STATS.map(({ label, value, delta, icon: Icon, tone }) => {
          const up = delta >= 0;
          return (
            <Card key={label} className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>{label}</CardDescription>
                  <div className={cn("p-2 rounded-lg", TONE[tone])}>
                    <Icon className="h-4 w-4" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold tracking-tight">{value}</div>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant={up ? "success" : "destructive"}>
                    {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {up ? "+" : ""}{delta.toFixed(1)}%
                  </Badge>
                  <span className="text-xs text-muted-foreground">vs прошлая неделя</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Выручка за неделю</CardTitle>
                <CardDescription>Динамика оборота и количество визитов</CardDescription>
              </div>
              <Badge variant="success">
                <ArrowUpRight className="h-3 w-3" /> +18.2%
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={CHART} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="d" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}K`} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    labelStyle={{ color: "hsl(var(--foreground))" }}
                    formatter={(value: number, name) => [
                      name === "revenue" ? `${value}K ₸` : `${value} визитов`,
                      name === "revenue" ? "Выручка" : "Визиты",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="url(#rev)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Последние события</CardTitle>
            <CardDescription>Автоматика и мастера</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {ACTIVITY.map(({ icon: Icon, tone, title, meta }, i) => (
              <div key={i} className="flex gap-3">
                <div className={cn("h-9 w-9 shrink-0 rounded-full flex items-center justify-center", TONE_SOFT[tone])}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{title}</p>
                  <p className="text-xs text-muted-foreground">{meta}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {!me?.team_id && (
        <Card className="border-dashed bg-muted/30">
          <CardContent className="py-6 flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">Демо-данные</p>
                <p className="text-sm text-muted-foreground">
                  Команда ещё не создана — на дашборде показаны примеры. Перейдите в Настройки, чтобы начать.
                </p>
              </div>
            </div>
            <Button variant="outline">Создать команду</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
