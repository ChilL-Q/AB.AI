"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Loader2,
  Sparkles,
  Save,
  CheckCircle2,
  Power,
  Activity,
  Phone,
  Check,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatMoney, formatDateShort } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  AIAgentConfig,
  AIAgentMode,
  OutreachAction,
  OutreachMetrics,
} from "@/types";

const MODE_OPTIONS: { value: AIAgentMode; title: string; description: string }[] = [
  {
    value: "manual",
    title: "Ручной",
    description: "AI не вмешивается. Все ответы оператор пишет сам.",
  },
  {
    value: "semi_auto",
    title: "Полуавтомат",
    description:
      "На каждое входящее AI готовит черновик. Оператор принимает, правит или отклоняет.",
  },
  {
    value: "auto",
    title: "Авто",
    description:
      "AI отвечает сам без подтверждения. Оператор может перехватить в любой момент.",
  },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  sent: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  replied: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  escalated: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  failed: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает",
  sent: "Отправлено",
  replied: "Отвечено",
  escalated: "Эскалация",
  failed: "Ошибка",
};

export default function AIAgentPage() {
  const qc = useQueryClient();
  const configQ = useQuery({
    queryKey: ["ai-agent-config"],
    queryFn: async () => (await api.get<AIAgentConfig>("/ai-agent/config")).data,
  });

  const metricsQ = useQuery({
    queryKey: ["outreach-metrics"],
    queryFn: async () => (await api.get<OutreachMetrics>("/ai-agent/outreach/metrics")).data,
  });

  const actionsQ = useQuery({
    queryKey: ["outreach-actions"],
    queryFn: async () =>
      (await api.get<OutreachAction[]>("/ai-agent/outreach")).data,
  });

  const [mode, setMode] = useState<AIAgentMode>("semi_auto");
  const [isActive, setIsActive] = useState(true);
  const [tone, setTone] = useState("friendly");
  const [personality, setPersonality] = useState("");
  const [forbiddenCsv, setForbiddenCsv] = useState("");
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const configLoaded = !!configQ.data;
  useEffect(() => {
    if (!configQ.data) return;
    setMode(configQ.data.mode);
    setIsActive(configQ.data.is_active ?? true);
    setTone(configQ.data.tone ?? "friendly");
    setPersonality(configQ.data.personality ?? "");
    setForbiddenCsv((configQ.data.forbidden_topics ?? []).join(", "));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configLoaded]);

  const save = useMutation({
    mutationFn: async () => {
      const { data } = await api.patch<AIAgentConfig>("/ai-agent/config", {
        mode,
        is_active: isActive,
        tone: tone.trim() || "friendly",
        personality: personality.trim() || null,
        forbidden_topics: forbiddenCsv.split(",").map((s) => s.trim()).filter(Boolean),
      });
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["ai-agent-config"], data);
      setSavedAt(Date.now());
    },
  });

  const toggleActive = useMutation({
    mutationFn: async (active: boolean) => {
      const { data } = await api.patch<AIAgentConfig>("/ai-agent/config", {
        is_active: active,
      });
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["ai-agent-config"], data);
      setIsActive(data.is_active);
    },
  });

  const saveError = save.error
    ? (save.error as { response?: { data?: { detail?: string } }; message?: string })
        .response?.data?.detail ??
      (save.error as { message?: string }).message ??
      "Не удалось сохранить"
    : null;

  const metrics = metricsQ.data;
  const actions = actionsQ.data ?? [];

  const approveMut = useMutation({
    mutationFn: async ({ id, edited_message }: { id: string; edited_message?: string }) => {
      return (await api.post<OutreachAction>(`/ai-agent/outreach/${id}/approve`, { edited_message })).data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["outreach-actions"] });
      await qc.invalidateQueries({ queryKey: ["outreach-metrics"] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/ai-agent/outreach/${id}/reject`);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["outreach-actions"] });
      await qc.invalidateQueries({ queryKey: ["outreach-metrics"] });
    },
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl brand-gradient flex items-center justify-center shrink-0">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">AI-агент</h1>
            <p className="text-sm text-muted-foreground">
              Настройки автоответчика и проактивного обращения к клиентам
            </p>
          </div>
        </div>
        <Button
          variant={isActive ? "default" : "outline"}
          onClick={() => toggleActive.mutate(!isActive)}
          disabled={toggleActive.isPending}
          className={cn(
            isActive
              ? "bg-emerald-600 hover:bg-emerald-700"
              : "text-destructive hover:text-destructive",
          )}
        >
          {toggleActive.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Power className="h-4 w-4 mr-2" />
          )}
          {isActive ? "AI работает" : "AI остановлен"}
        </Button>
      </div>

      {configQ.isLoading ? (
        <div className="py-16 flex justify-center">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Режим работы</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {MODE_OPTIONS.map((opt) => {
                const active = mode === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setMode(opt.value)}
                    className={cn(
                      "text-left border rounded-lg p-4 transition-colors",
                      active
                        ? "border-primary bg-primary/5"
                        : "border-border hover:bg-accent/50",
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          "h-4 w-4 rounded-full border-2 mt-0.5 shrink-0",
                          active
                            ? "border-primary bg-primary"
                            : "border-muted-foreground/40",
                        )}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="font-medium">{opt.title}</div>
                        <div className="text-sm text-muted-foreground mt-0.5">
                          {opt.description}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Голос бренда</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="tone">Тон общения</Label>
                <Input
                  id="tone"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  placeholder="friendly, formal, playful..."
                />
                <p className="text-xs text-muted-foreground">
                  Короткое слово — стилистический модификатор для ответов
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="personality">Характер (подсказка для AI)</Label>
                <textarea
                  id="personality"
                  value={personality}
                  onChange={(e) => setPersonality(e.target.value)}
                  rows={4}
                  placeholder="Например: «Вежливый механик со стажем 20 лет. Не пересыпает техническими терминами, объясняет на пальцах.»"
                  className="w-full px-3 py-2 rounded-md border bg-background text-sm resize-y min-h-[96px] focus:outline-none focus:ring-2 focus:ring-ring"
                  maxLength={4000}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="forbidden">Запрещённые темы</Label>
                <Input
                  id="forbidden"
                  value={forbiddenCsv}
                  onChange={(e) => setForbiddenCsv(e.target.value)}
                  placeholder="политика, конкуренты, персональные данные"
                />
                <p className="text-xs text-muted-foreground">
                  Через запятую. AI вежливо уйдёт от этих тем.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex items-center gap-3">
            <Button onClick={() => save.mutate()} disabled={save.isPending}>
              {save.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Сохранить
            </Button>
            {savedAt && !save.isPending && !saveError && (
              <span className="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                Сохранено
              </span>
            )}
            {saveError && <span className="text-sm text-destructive">{saveError}</span>}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Метрики AI Outreach
              </CardTitle>
            </CardHeader>
            <CardContent>
              {metrics ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">
                      Всего обращений
                    </div>
                    <div className="mt-1 text-2xl font-bold">{metrics.total_outreach}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">
                      Ответили
                    </div>
                    <div className="mt-1 text-2xl font-bold">
                      {metrics.replied}{" "}
                      <span className="text-sm text-muted-foreground">
                        ({(metrics.reply_rate * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">
                      Вернулись на визит
                    </div>
                    <div className="mt-1 text-2xl font-bold">
                      {metrics.resulted_in_visit}{" "}
                      <span className="text-sm text-muted-foreground">
                        ({(metrics.retention_rate * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">
                      Выручка от AI
                    </div>
                    <div className="mt-1 text-2xl font-bold">
                      {formatMoney(metrics.total_revenue)}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">Загрузка метрик...</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Лента действий AI</CardTitle>
            </CardHeader>
            <CardContent>
              {actions.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  Пока нет действий AI
                </p>
              ) : (
                <div className="divide-y">
                  {actions.map((action) => (
                    <div key={action.id} className="flex items-center justify-between py-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{action.client_name}</span>
                          <Badge
                            variant="outline"
                            className={STATUS_COLORS[action.status] ?? ""}
                          >
                            {STATUS_LABELS[action.status] ?? action.status}
                          </Badge>
                        </div>
                        {action.message_text && (
                          <p className="text-sm text-muted-foreground mt-0.5 truncate">
                            {action.message_text}
                          </p>
                        )}
                        {action.status === "escalated" && (
                          <div className="mt-1 flex items-center gap-1 text-sm text-amber-600 dark:text-amber-400">
                            <Phone className="h-3 w-3" />
                            Рекомендуется позвонить клиенту
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-4">
                        {action.status === "pending" && (
                          <>
                            <Button
                              size="sm"
                              variant="default"
                              className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700"
                              disabled={approveMut.isPending}
                              onClick={() => approveMut.mutate({ id: action.id })}
                            >
                              <Check className="h-3 w-3 mr-1" />Одобрить
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs text-destructive hover:text-destructive"
                              disabled={rejectMut.isPending}
                              onClick={() => rejectMut.mutate(action.id)}
                            >
                              <X className="h-3 w-3 mr-1" />Отклонить
                            </Button>
                          </>
                        )}
                        <div className="text-sm text-muted-foreground">
                          {formatDateShort(action.created_at)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}