"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Check, Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { slugify } from "@/lib/slug";
import { useMe } from "@/hooks/use-me";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Team } from "@/types";

const TIMEZONES = [
  "Asia/Almaty",
  "Asia/Tashkent",
  "Asia/Astana",
  "Asia/Bishkek",
  "Europe/Moscow",
];

const STEPS = [
  { icon: "🔧", title: "Создайте автосервис", desc: "Название и настройки" },
  { icon: "🤖", title: "AI-агент настроен", desc: "Автоматически" },
  { icon: "🚀", title: "Начните работу", desc: "Клиенты и визиты" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { data: me, isLoading, error: meError } = useMe();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [tz, setTz] = useState("Asia/Almaty");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slugEdited) setSlug(slugify(name));
  }, [name, slugEdited]);

  useEffect(() => {
    if (me?.team_id) router.replace("/dashboard");
  }, [me, router]);

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<Team>("/team", {
        name,
        slug,
        timezone: tz,
        locale: "ru",
      });
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      router.replace("/dashboard");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Не удалось создать команду");
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (slug.length < 2 || !/^[a-z0-9][a-z0-9-]*[a-z0-9]$/.test(slug)) {
      setError("Slug должен содержать только латиницу, цифры и дефисы (2+ символа)");
      return;
    }
    mutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (meError || !me) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <p className="text-sm text-destructive">
          Не удалось загрузить профиль. Проверьте, что бэкенд запущен.
        </p>
      </div>
    );
  }

  if (me.team_id) return null;

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-lg">
        {/* Logo + heading */}
        <div className="text-center mb-8">
          <div className="h-12 w-12 rounded-2xl brand-gradient flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Создаём ваш автосервис</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Одна команда — один автосервис. Пару минут — и можно начинать.
          </p>
        </div>

        {/* Steps preview */}
        <div className="flex items-center justify-center gap-6 mb-8">
          {STEPS.map((step, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="flex flex-col items-center gap-1">
                <span className="text-2xl">{step.icon}</span>
                <span className={cn(
                  "text-[11px] font-medium",
                  i === 0 ? "text-foreground" : "text-muted-foreground",
                )}>
                  {step.title}
                </span>
                <span className="text-[10px] text-muted-foreground/60">{step.desc}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="w-8 h-px bg-border mt-[-20px]" />
              )}
            </div>
          ))}
        </div>

        {/* Form card */}
        <div className="bg-card border border-border rounded-2xl shadow-lg p-6">
          <form onSubmit={onSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name">Название автосервиса</Label>
              <Input
                id="name"
                placeholder="Авто Мастер"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={2}
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Уникальный идентификатор</Label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground shrink-0 bg-muted px-3 py-2.5 rounded-l-lg border border-r-0 border-input">
                  ab-ai.kz/
                </span>
                <Input
                  id="slug"
                  placeholder="avto-master"
                  value={slug}
                  onChange={(e) => {
                    setSlugEdited(true);
                    setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""));
                  }}
                  required
                  pattern="^[a-z0-9][-a-z0-9]*[a-z0-9]$"
                  className="h-11 rounded-l-none"
                />
              </div>
              <p className="text-xs text-muted-foreground">Используется в URL-адресах и интеграциях</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tz">Часовой пояс</Label>
              <select
                id="tz"
                value={tz}
                onChange={(e) => setTz(e.target.value)}
                className="flex h-11 w-full rounded-xl border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {TIMEZONES.map((z) => (
                  <option key={z} value={z}>{z}</option>
                ))}
              </select>
            </div>

            {error && (
              <div className="rounded-xl bg-destructive/10 text-destructive text-sm px-4 py-3">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-11 brand-gradient brand-gradient-text brand-shadow-sm text-sm font-semibold rounded-xl"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Создаём...</>
              ) : (
                <><Check className="h-4 w-4 mr-2" /> Создать автосервис</>
              )}
            </Button>
          </form>
        </div>

        <p className="text-center text-[11px] text-muted-foreground/50 mt-4">
          AI-агент будет настроен автоматически после создания
        </p>
      </div>
    </div>
  );
}