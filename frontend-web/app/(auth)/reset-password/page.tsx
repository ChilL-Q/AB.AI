"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function ResetPasswordInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError("Отсутствует токен сброса пароля");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.post("/auth/password-reset/confirm", { token, new_password: password });
      setSuccess(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Ошибка сброса пароля");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-amber-500/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-amber-500/5 blur-3xl" />
      </div>
      <div className="w-full max-w-md px-4 relative">
        <div className="text-center mb-8">
          <Link href="/login" className="font-bold tracking-tight text-3xl leading-none">
            <span className="text-primary">AB-</span>
            <span className="text-muted-foreground">AI.kz</span>
          </Link>
        </div>
        <div className="bg-card border border-border rounded-2xl shadow-lg p-8">
          {success ? (
            <>
              <h1 className="text-xl font-semibold text-center mb-2">Пароль сброшен</h1>
              <p className="text-sm text-muted-foreground text-center mb-6">
                Вы можете войти с новым паролем.
              </p>
              <Link href="/login">
                <Button className="w-full h-11 brand-gradient font-semibold">Войти</Button>
              </Link>
            </>
          ) : !token ? (
            <>
              <h1 className="text-xl font-semibold text-center mb-2">Неверная ссылка</h1>
              <p className="text-sm text-muted-foreground text-center mb-6">
                Ссылка для сброса пароля недействительна или устарела.
              </p>
              <Link href="/forgot-password">
                <Button variant="outline" className="w-full h-11">Запросить новую ссылку</Button>
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-xl font-semibold text-center mb-1">Новый пароль</h1>
              <p className="text-sm text-muted-foreground text-center mb-6">
                Введите новый пароль для вашего аккаунта
              </p>
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="password">Новый пароль</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    className="h-11"
                  />
                </div>
                {error && (
                  <div className="rounded-lg bg-destructive/10 text-destructive text-sm px-4 py-3">
                    {error}
                  </div>
                )}
                <Button type="submit" className="w-full h-11 brand-gradient font-semibold" disabled={loading}>
                  {loading ? "Сохраняем..." : "Сбросить пароль"}
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordInner />
    </Suspense>
  );
}