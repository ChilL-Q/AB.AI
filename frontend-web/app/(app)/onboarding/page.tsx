"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Car, Check, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { slugify } from "@/lib/slug";
import { useMe } from "@/hooks/use-me";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Team } from "@/types";

const TIMEZONES = [
  "Asia/Almaty",
  "Asia/Tashkent",
  "Asia/Astana",
  "Asia/Bishkek",
  "Europe/Moscow",
];

export default function OnboardingPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { data: me, isLoading } = useMe();

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

  if (isLoading || !me || me.team_id) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 pt-6">
      <div className="text-center space-y-2">
        <div className="mx-auto h-14 w-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
          <Car className="h-7 w-7" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Создаём ваш автосервис</h1>
        <p className="text-muted-foreground">
          Одна команда — один автосервис. Пара минут и можно начинать работу.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Данные автосервиса</CardTitle>
          <CardDescription>Эти данные будут видны вашей команде</CardDescription>
        </CardHeader>
        <CardContent>
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
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Уникальный идентификатор</Label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground shrink-0">ab.ai/</span>
                <Input
                  id="slug"
                  placeholder="avto-master"
                  value={slug}
                  onChange={(e) => {
                    setSlugEdited(true);
                    setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""));
                  }}
                  required
                  pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$"
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
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {TIMEZONES.map((z) => (
                  <option key={z} value={z}>{z}</option>
                ))}
              </select>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Создаём...</>
              ) : (
                <><Check className="h-4 w-4 mr-2" /> Создать автосервис</>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
