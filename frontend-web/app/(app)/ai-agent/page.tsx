"use client";

/**
 * AI-agent configuration screen.
 *
 * A compact form over the team's single `AIAgentConfig` row. We commit on
 * explicit "Save" (not onChange) to avoid partial writes while the owner
 * is still tweaking the personality text.
 *
 * Modes:
 *   - manual:    AI never replies or suggests. Operator drives.
 *   - semi_auto: AI drafts a reply on every inbound; operator accepts/edits.
 *   - auto:      AI replies directly (sent_by="ai"). Safety net for off-hours.
 */

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Sparkles, Save, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { AIAgentConfig, AIAgentMode } from "@/types";

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

export default function AIAgentPage() {
  const qc = useQueryClient();
  const configQ = useQuery({
    queryKey: ["ai-agent-config"],
    queryFn: async () => (await api.get<AIAgentConfig>("/ai-agent/config")).data,
  });

  const [mode, setMode] = useState<AIAgentMode>("semi_auto");
  const [tone, setTone] = useState("friendly");
  const [personality, setPersonality] = useState("");
  const [forbiddenCsv, setForbiddenCsv] = useState("");
  const [savedAt, setSavedAt] = useState<number | null>(null);

  // Seed local form state once the config loads. We don't re-seed on every
  // query refetch — that would clobber the user's in-progress edits.
  const configLoaded = !!configQ.data;
  useEffect(() => {
    if (!configQ.data) return;
    setMode(configQ.data.mode);
    setTone(configQ.data.tone ?? "friendly");
    setPersonality(configQ.data.personality ?? "");
    setForbiddenCsv((configQ.data.forbidden_topics ?? []).join(", "));
    // Only seed once — react-query will refetch on focus, but we treat
    // the first successful fetch as the source-of-truth baseline.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configLoaded]);

  const save = useMutation({
    mutationFn: async () => {
      const { data } = await api.patch<AIAgentConfig>("/ai-agent/config", {
        mode,
        tone: tone.trim() || "friendly",
        personality: personality.trim() || null,
        forbidden_topics: forbiddenCsv
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["ai-agent-config"], data);
      setSavedAt(Date.now());
    },
  });

  const saveError = save.error
    ? (save.error as { response?: { data?: { detail?: string } }; message?: string })
        .response?.data?.detail ??
      (save.error as { message?: string }).message ??
      "Не удалось сохранить"
    : null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">AI-агент</h1>
          <p className="text-sm text-muted-foreground">
            Настройки автоответчика для входящих сообщений
          </p>
        </div>
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
                  placeholder={
                    "Например: «Вежливый механик со стажем 20 лет. Не пересыпает техническими терминами, объясняет на пальцах.»"
                  }
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
        </>
      )}
    </div>
  );
}
